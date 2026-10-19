"""b131_nodes.py URL PATTERN [N] -- print the rendered <body> text nodes around each regex hit (read-only, b131 only)."""
import re
import sys

sys.path.insert(0, 'scripts/catalog')
sys.path.insert(0, 'scripts/catalog/pipeline')
import verify_quotes as vq  # noqa: E402
from b131_qcheck import body_nodes  # noqa: E402

st, raw = vq.fetch(sys.argv[1])
print('## status', st)
bs = body_nodes(raw)
n = int(sys.argv[3]) if len(sys.argv) > 3 else 6
for i, x in enumerate(bs):
    if re.search(sys.argv[2], x, re.I):
        print(f'--- hit at node {i}')
        for j in range(max(0, i - n), min(len(bs), i + n + 1)):
            print(f'  {j}: {bs[j][:160]!r}')
