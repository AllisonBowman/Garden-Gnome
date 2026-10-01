"""qc.py URL pattern [pattern...] -- print context windows from the cached/fetched page text.

Run from garden-gnome/ with .venv/bin/python. Uses verify_quotes' fetch+extract so
the page text seen here is exactly the text verify_quotes checks quotes against.
"""
import re, sys
sys.path.insert(0, 'scripts/catalog')
import verify_quotes as vq

url = sys.argv[1]
status, raw = vq.fetch(url)
print('## fetch status:', status, '| bytes:', len(raw))
if not raw:
    sys.exit(1)
text = vq.extract(raw)
m = re.search(r'<title>(.*?)</title>', raw, re.S | re.I)
print('## <title>:', (m.group(1).strip() if m else None))
for pat in sys.argv[2:]:
    hits = [mm.start() for mm in re.finditer(pat, text, re.I)]
    print(f'## {pat!r}: {len(hits)} hit(s)')
    for h in hits[:3]:
        print('   ...' + text[max(0, h - 200):h + 500].replace('\n', '⏎') + '...')
