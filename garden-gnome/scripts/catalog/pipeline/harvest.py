"""harvest2.py RUN_DIR [RUN_DIR ...] -- pull completed research records and audit verdicts out of stalled batch runs.

Writes cache.json (merged with any existing cache.json): {"research": {latin: record}, "audits": {latin: findings}}.
Research records are keyed by scientific_name_given; audits are matched to a species by the auditor prompt in the
agent transcript. Works for any session's run directory."""
import json, os, re, sys
sp = os.path.dirname(os.path.abspath(__file__))
cache_path = os.path.join(sp, 'cache.json')
cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {'research': {}, 'audits': {}}
for W in sys.argv[1:]:
    species_of = {}
    for fn in os.listdir(W):
        if not fn.endswith('.jsonl') or fn == 'journal.jsonl':
            continue
        aid = fn[len('agent-'):-len('.jsonl')]
        head = open(os.path.join(W, fn), errors='replace').read(6000)
        # The parenthetical is the species' latin name as template-research.js
        # wrote it, hybrid marker included: "(Nepeta × faassenii)",
        # "(Nepeta ×faassenii)" and "(Nepeta x faassenii)" all key their
        # audit verdict, and the shape stays tight so a second parenthesised
        # name further along the prompt cannot be captured instead.
        m = re.search(r'reviewing a researched plant-care record for .{0,160}?'
                      r'\(([A-Z][a-z]+ (?:[\u00d7x] )?\u00d7?[a-z\-]+)\)', head, re.S)
        if m:
            species_of[aid] = m.group(1)
    n_r = n_a = 0
    for line in open(os.path.join(W, 'journal.jsonl')):
        j = json.loads(line)
        if j.get('type') != 'result':
            continue
        r, aid = j.get('result'), j.get('agentId')
        if isinstance(r, dict) and 'scientific_name_given' in r:
            cache['research'][r['scientific_name_given']] = r; n_r += 1
        elif isinstance(r, dict) and 'findings' in r and aid in species_of:
            cache['audits'][species_of[aid]] = r['findings']; n_a += 1
    print(os.path.basename(W), 'research', n_r, 'audits', n_a)
json.dump(cache, open(cache_path, 'w'), indent=1, ensure_ascii=False)
print('cache now: research', len(cache['research']), 'audits', len(cache['audits']))
