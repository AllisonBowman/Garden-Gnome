"""b133_qc.py URL [-q QUOTE ...] [pat ...] -- collapsed-whitespace context windows plus verify_quotes.present()
for each -q quote (read-only; same fetch+extract path as verify_quotes)."""
import re, sys
sys.path.insert(0, 'scripts/catalog')
import verify_quotes as vq
url, args = sys.argv[1], sys.argv[2:]
st, raw = vq.fetch(url)
print('## status', st, '| <title>:', re.sub(r'\s+', ' ', (re.search(r'<title>(.*?)</title>', raw, re.S) or [None, ''])[1]))
m = re.search(r'<h1[^>]*>(.*?)</h1>', raw, re.S)
print('## H1:', m and re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', m.group(1))))
t = re.sub(r'[ \t]+', ' ', re.sub(r'\s*\n\s*', '\n', vq.extract(raw)))
nt = vq.norm(vq.extract(raw))
i = 0
while i < len(args):
    if args[i] == '-q':
        q = args[i + 1].replace('\\n', '\n')
        print('## PRESENT' if vq.present(q, nt) else '## MISSING', repr(q[:120]))
        i += 2
        continue
    pat = args[i]
    hits = list(re.finditer(pat, t))
    print(f'## {pat!r}: {len(hits)} hit(s)')
    for h in hits[:2]:
        print('   ', repr(t[max(0, h.start() - 150):h.start() + 450]))
    i += 1
