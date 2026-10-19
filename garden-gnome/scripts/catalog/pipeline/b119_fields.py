"""b119_fields.py URL [LABEL...] -- b119-only helper: print each NC State <dt> label's rendered value nodes.

Uses verify_quotes' fetch path and the same node splitter as b119_qcheck.py; reads the shared cache, never edits it.
"""
import sys
sys.path.insert(0, 'scripts/catalog/pipeline')
sys.path.insert(0, 'scripts/catalog')
import verify_quotes as vq  # noqa: E402
from b119_qcheck import nodes  # noqa: E402

status, raw = vq.fetch(sys.argv[1])
ns = nodes(raw)
labels = sys.argv[2:]
for i, n in enumerate(ns):
    if any(n.startswith(l) for l in labels) and n.endswith(':'):
        vals = []
        for m in ns[i + 1:i + 30]:
            if m.endswith(':') and len(m) < 45:
                break
            vals.append(m)
        print(n, '=>', vals)
