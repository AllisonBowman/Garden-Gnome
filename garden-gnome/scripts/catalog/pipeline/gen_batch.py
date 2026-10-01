"""gen_batch.py batches.json -- write bNN-catalog-research.js for each batch, from the b80 template.

Substitutes meta name/description, SPECIES, the batch slug, and the auditor's sibling clause (computed from the
corpus), and applies the null-verdict guard the resume scripts carry. Run from garden-gnome/."""
import glob, json, os, re, sys
sp = os.path.dirname(os.path.abspath(__file__))
SP = sp
batches = json.load(open(sys.argv[1]))
tpl = open(f'{sp}/template-research.js').read()

corpus = {}  # genus -> [(latin, common)]
for f in glob.glob('app/data/verified/b*.json'):
    for r in json.load(open(f))['records']:
        latin = r.get('scientific_name_accepted') or r['scientific_name_given']
        corpus.setdefault(latin.split()[0], []).append((latin, r['common_name']))
        if r.get('scientific_name_accepted') and r['scientific_name_given'] != r['scientific_name_accepted']:
            corpus.setdefault(r['scientific_name_given'].split()[0], []).append((r['scientific_name_given'], r['common_name']))

def sibling_clause(species):
    genera = {}
    for s in species:
        genera.setdefault(s['latin'].split()[0], []).append(s['latin'])
    shared = [g for g, ls in genera.items() if len(ls) > 1]
    in_batch = ('no two species here share a genus' if not shared else
                'shared genera in this batch: ' + '; '.join(f"{g}: {', '.join(genera[g])}" for g in shared))
    parts = []
    for s in species:
        g = s['latin'].split()[0]
        cong = [(l, c) for l, c in corpus.get(g, []) if l != s['latin']]
        parts.append(f"{s['latin']} is new to this catalog" if not cong else
                     f"{s['latin']} vs. " + ', '.join(f'{l} ({c})' for l, c in sorted(set(cong))))
    return in_batch, '; '.join(parts)

OLD_SIB = re.search(r"Watch for content bled in from a same-genus sibling in this batch \(.*?\), and for values read off", tpl, re.S).group(0)
guard_old = """    .then(verdict => {
      const refuted"""
guard_new = """    .then(verdict => {
      if (!verdict || !Array.isArray(verdict.findings)) return { species: s.latin, record, unverified: true, fields_removed: 0 }
      const refuted"""
ok_old = "const ok = results.filter(Boolean)"
ok_new = "const ok = results.filter(Boolean).filter(r => !r.unverified)\nconst unverifiedItems = results.filter(Boolean).filter(r => r.unverified).map(r => r.species)\nif (unverifiedItems.length) log(`UNVERIFIED (audit missing or failed): ${unverifiedItems.join(', ')}`)"
for b in batches:
    n, slug, title, species = b['n'], b['slug'], b['title'], b['species']
    js = tpl
    js = js.replace("name: 'b80-catalog-research'", f"name: 'b{n}-catalog-research'")
    js = js.replace("Research + adversarially verify 8 species for the plant-care claim catalog (b80, native coastal dune and salt-marsh plants)",
                    f"Research + adversarially verify {len(species)} species for the plant-care claim catalog (b{n}, {title})")
    start, end = js.index('const SPECIES = ['), js.index('\n]\n', js.index('const SPECIES = [')) + 3
    arr = 'const SPECIES = [\n' + ''.join('  ' + json.dumps({'common': s['common'], 'latin': s['latin'], 'note': s['note']}, ensure_ascii=False) + ',\n' for s in species) + ']\n'
    js = js[:start] + arr + js[end:]
    in_batch, cong = sibling_clause(species)
    js = js.replace(OLD_SIB, f"Watch for content bled in from a same-genus sibling in this batch ({in_batch}) or already in this catalog ({cong}), and for values read off")
    js = js.replace("batch: 'b80-native-coastal'", f"batch: 'b{n}-{slug}'")
    assert guard_old in js and ok_old in js
    js = js.replace(guard_old, guard_new).replace(ok_old, ok_new)
    ret_start = js.index('return {\n  unverified:')
    ret_end = js.index('}\n', ret_start) + 2
    compact = (
        "const payload = {\n"
        "  unverified: SPECIES.filter(sp => !ok.some(r => r.species === sp.latin)).map(sp => sp.latin),\n"
        f"  batch: 'b{n}-{slug}',\n"
        "  agents_failed: failed,\n"
        "  records: ok.map(r => r.record),\n"
        "  audit_summary: ok.map(r => ({ species: r.species, fields_removed: r.fields_removed })),\n"
        "}\n"
        "// Summary first so a truncated notification preview shows it; full records follow for extract_batch.py.\n"
        "return { summary: { batch: payload.batch, records: payload.records.length, unverified: payload.unverified, agents_failed: failed,\n"
        "  species: payload.records.map(r => r.common_name + ' (' + r.scientific_name_given + ') toxic=' + r.toxic_to_pets), audit: payload.audit_summary.map(a => a.species + ':' + a.fields_removed).join(', ') }, ...payload }\n")
    js = js[:ret_start] + compact + js[ret_end:]
    assert "b80" not in js.replace('b80-catalog', ''), 'stale b80 reference'
    open(f'{sp}/b{n}-catalog-research.js', 'w').write(js)
    print(f'b{n}: {len(species)} species -> b{n}-catalog-research.js ({title})')
