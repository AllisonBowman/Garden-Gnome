"""b131_scan.py -- run b131_repair.py's blocks (without finish) and test every quote: present / strict / body (read-only)."""
import re
import runpy
import sys

sys.path.insert(0, 'scripts/catalog')
sys.path.insert(0, 'scripts/catalog/pipeline')
import verify_quotes as vq  # noqa: E402
from b131_qcheck import body_nodes, nodes, strict  # noqa: E402

g = runpy.run_path('scripts/catalog/pipeline/b131_repair.py', run_name='scan')
pages = {}
for r in g['res']['records']:
    for i, c in enumerate(r['citations']):
        u, q = c['url'], c['quote']
        flags = []
        if ' | ' in q:
            flags.append('PIPE')
        if re.search(r'^[A-Z][^\n:]{2,40}:\n', q) and not q.startswith('Poison Severity:'):
            flags.append('LABEL')
        if re.search(r'#[a-z][^\n#]* #', q):
            flags.append('TAGRUN')
        if q.strip() == 'Correct' and c['claim'] != g['CORR']:
            flags.append('BARECORRECT')
        if 'mobot' in u or 'ifas' in u:
            st = 'skip'
        else:
            if u not in pages:
                s, raw = vq.fetch(u)
                pages[u] = (vq.norm(vq.extract(raw)), nodes(raw), body_nodes(raw)) if raw else None
            p = pages[u]
            if p is None:
                st = 'FETCHFAIL'
            else:
                pr, sn, bd = vq.present(q, p[0]), strict(q, p[1]), strict(q, p[2])
                st = f'present={pr} strict={sn} body={bd}'
                if not pr:
                    flags.append('MISS')
                elif not bd:
                    flags.append('nobody')
        if flags:
            print(f"{r['common_name'][:16]:16s} [{i}] {flags} {st} :: {q[:70]!r} || {c['claim'][:60]}")
