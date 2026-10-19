"""b132_qc.py URL pat [pat...] -- read-only: shows <title>, H1, and context with each rendered text node
on its own line (node boundaries shown as U+23CE), using verify_quotes' fetch+extract parser."""
import re
import sys

sys.path.insert(0, 'scripts/catalog')
import verify_quotes as vq  # noqa: E402

st, raw = vq.fetch(sys.argv[1])
print('## status', st, '| bytes', len(raw))
if not raw:
    sys.exit(1)
print('## <title>:', re.sub(r'\s+', ' ', (re.search(r'<title>(.*?)</title>', raw, re.S) or [None, ''])[1]))
m = re.search(r'<h1[^>]*>(.*?)</h1>', raw, re.S)
print('## H1:', m and re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', m.group(1))).strip())
p = vq._Text()
p.feed(raw)
nodes = [re.sub(r'\s+', ' ', x).strip() for x in p.parts]
t = '⏎'.join(x for x in nodes if x)
for pat in sys.argv[2:]:
    hits = list(re.finditer(pat, t, re.I))
    print(f'## {pat!r}: {len(hits)} hit(s)')
    for h in hits[:3]:
        print('   ', t[max(0, h.start() - 150):h.start() + 400])
