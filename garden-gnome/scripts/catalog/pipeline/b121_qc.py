"""b121_qc.py URL [-p "quote"]... [pattern]... -- compact qc.py for the b121 landing.

Same fetch+extract path as verify_quotes (via qc.py's import), but each rendered node is collapsed onto one
'⏎'-separated line so context windows stay short. `-p QUOTE` runs verify_quotes.present() on QUOTE.
"""
import re
import sys

sys.path.insert(0, 'scripts/catalog')
import verify_quotes as vq  # noqa: E402

url, args = sys.argv[1], sys.argv[2:]
status, raw = vq.fetch(url)
print('## fetch status:', status, '| bytes:', len(raw))
if not raw:
    sys.exit(1)
text = vq.extract(raw)
flat = '⏎'.join(s.strip() for s in re.split(r'\n', text) if s.strip())
ntext = vq.norm(text)
i = 0
while i < len(args):
    a = args[i]
    if a == '-p':
        q = args[i + 1].replace('\\n', '\n')
        print(f'## present={vq.present(q, ntext)}  {q[:90]!r}')
        i += 2
        continue
    hits = [m.start() for m in re.finditer(a, flat, re.I)]
    print(f'## {a!r}: {len(hits)} hit(s)')
    for h in hits[:4]:
        print('   ...' + flat[max(0, h - 150):h + 350] + '...')
    i += 1
