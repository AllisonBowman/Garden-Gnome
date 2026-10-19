"""b133_nodecheck.py -- run b130_qcheck's present/strict/body tests over every citation in the b133 landed file.

Read-only (verify_quotes' fetch path; never edits the shared cache). Prints only citations failing a test.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, 'scripts/catalog')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_quotes as vq  # noqa: E402
from b130_qcheck import body_nodes, nodes, strict  # noqa: E402

data = json.load(open('app/data/verified/b133-mixed.json'))
cache = {}
bad = 0
for r in data['records']:
    for c in r['citations']:
        u = c['url']
        if u not in cache:
            st, raw = vq.fetch(u)
            cache[u] = (st, raw and vq.norm(vq.extract(raw)), raw and nodes(raw), raw and body_nodes(raw))
        st, text, ns, bs = cache[u]
        if st != 'ok':
            print(f'SKIP[{st}] {r["common_name"]}: {c["claim"][:70]}')
            continue
        p, s, b = vq.present(c['quote'], text), strict(c['quote'], ns), strict(c['quote'], bs)
        if not (p and s and b):
            bad += 1
            print(f'present={p} strict={s} body={b} | {r["common_name"]}: {c["claim"][:80]}\n     {c["quote"][:110]!r}')
print('failing:', bad)
