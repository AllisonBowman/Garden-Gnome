"""b125_qc.py URL pat [pat...] -- like qc.py but collapses whitespace runs to single newlines/spaces (read-only)."""
import re, sys
sys.path.insert(0, 'scripts/catalog')
import verify_quotes as vq
st, raw = vq.fetch(sys.argv[1])
print('## status', st, '| <title>:', re.sub(r'\s+', ' ', (re.search(r'<title>(.*?)</title>', raw, re.S) or [None, ''])[1]))
m = re.search(r'<h1[^>]*>(.*?)</h1>', raw, re.S)
print('## H1:', m and re.sub(r'\s+', ' ', re.sub('<[^>]+>', '', m.group(1))))
t = re.sub(r'[ \t]+', ' ', re.sub(r'\s*\n\s*', '\n', vq.extract(raw)))
for pat in sys.argv[2:]:
    hits = list(re.finditer(pat, t))
    print(f'## {pat!r}: {len(hits)} hit(s)')
    for h in hits[:2]:
        print('   ', repr(t[max(0, h.start() - 120):h.start() + 450]))
