"""b124-only: list every landed b124 quote that fails the rendered-body strict test (reads the shared cache only)."""
import json
import sys
sys.path.insert(0, 'scripts/catalog')
sys.path.insert(0, 'scripts/catalog/pipeline')
import verify_quotes as vq  # noqa: E402
import b124_qcheck as qq  # noqa: E402

pages = {}
for r in json.load(open('app/data/verified/b124-mixed.json'))['records']:
    for c in r['citations']:
        u = c['url']
        if u not in pages:
            st, raw = vq.fetch(u)
            pages[u] = (qq.nodes(raw), qq.body_nodes(raw)) if raw else None
        if pages[u] is None:
            print('NOFETCH', r['common_name'], u)
            continue
        ns, bs = pages[u]
        if not qq.strict(c['quote'], bs):
            print(f"{r['common_name']:18s} strict={qq.strict(c['quote'], ns)} :: {c['claim'][:70]!r} :: {c['quote'][:70]!r}")
