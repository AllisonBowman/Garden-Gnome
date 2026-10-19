"""b104-only helper (kept at a b104 path so no other landing overwrites it).

  b104_peek.py URL regex [regex...]        compact context windows (blank-line runs collapsed, newline shown as ⏎)
  b104_peek.py --q URL 'quote'             verify_quotes.present() for one candidate quote

Run from garden-gnome/ with .venv/bin/python. Same fetch+extract path as verify_quotes; reads the shared cache only.
"""
import re
import sys

sys.path.insert(0, 'scripts/catalog')
import verify_quotes as vq  # noqa: E402

if sys.argv[1] == '--q':
    url, q = sys.argv[2], sys.argv[3]
    st, raw = vq.fetch(url)
    print('fetch', st, '| present:', st == 'ok' and vq.present(q, vq.norm(vq.extract(raw))))
    sys.exit(0)

url = sys.argv[1]
st, raw = vq.fetch(url)
print('## fetch', st, len(raw))
if not raw:
    sys.exit(1)
text = vq.extract(raw)
text = re.sub(r'[ \t]+', ' ', text)
text = re.sub(r'\s*\n\s*', '\n', text)
for pat in sys.argv[2:]:
    hits = [m.start() for m in re.finditer(pat, text, re.I)]
    print(f'## {pat!r}: {len(hits)} hit(s)')
    for h in hits[:3]:
        print('   ...' + text[max(0, h - 150):h + 450].replace('\n', '⏎') + '...')
