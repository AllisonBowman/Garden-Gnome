"""make_resume.py bNN -- write bNN-resume.js from bNN-catalog-research.js, skipping agents whose results are in cache.json."""
import json, os, re, sys
sp = os.path.dirname(os.path.abspath(__file__))
b = sys.argv[1]
cache = json.load(open(f'{sp}/cache.json'))
js = open(f'{sp}/{b}-catalog-research.js').read()
latins = re.findall(r'"latin": "([^"]+)"', js) or re.findall(r'latin: "([^"]+)"', js)
sub = {'research': {k: v for k, v in cache['research'].items() if k in latins},
       'audits': {k: v for k, v in cache['audits'].items() if k in latins}}
old_head = """  s => agent(researchPrompt(s), { label: `research:${s.common}`, phase: 'Research', schema: RECORD_SCHEMA, model: 'sonnet', effort: 'medium' }),
  (record, s) => agent(verifyPrompt(record, s), { label: `verify:${s.common}`, phase: 'Verify', schema: VERDICT_SCHEMA, model: 'opus' })
    .then(verdict => {"""
new_head = """  s => CACHE.research[s.latin]
    ? Promise.resolve(CACHE.research[s.latin])
    : agent(researchPrompt(s), { label: `research:${s.common}`, phase: 'Research', schema: RECORD_SCHEMA, model: 'sonnet', effort: 'medium' }),
  (record, s) => {
    if (!record) return { species: s.latin, record: null, unverified: true, fields_removed: 0 }
    const audited = CACHE.audits[s.latin]
      ? Promise.resolve({ findings: CACHE.audits[s.latin] })
      : agent(verifyPrompt(record, s), { label: `verify:${s.common}`, phase: 'Verify', schema: VERDICT_SCHEMA, model: 'opus' })
    return audited.then(verdict => {"""
old_tail = "      return { species: s.latin, record, fields_removed: removed.length }\n    })\n)"
new_tail = "      return { species: s.latin, record, fields_removed: removed.length }\n    })\n  }\n)"
assert old_head in js and old_tail in js, 'template shape changed'
js = js.replace(old_head, new_head).replace(old_tail, new_tail)
js = js.replace("const FIELD_LIST = [", "const CACHE = " + json.dumps(sub, ensure_ascii=False) + "\n\nconst FIELD_LIST = [", 1)
js = re.sub(r"name: '(b\d+-catalog-research)'", r"name: '\1-resumed'", js, count=1)
open(f'{sp}/{b}-resume.js', 'w').write(js)
need_r = [l for l in latins if l not in sub['research']]; need_a = [l for l in latins if l not in sub['audits']]
print(f'{b}: {len(latins)} species; cached research {len(sub["research"])}, cached audits {len(sub["audits"])}; to run: research {need_r}, audits {len(need_a)}')
