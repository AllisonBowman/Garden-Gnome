"""b112_qc.py URL pattern... -- like qc.py but collapses whitespace runs so context is readable,
and reports whether each literal quote given with -q is present (verify_quotes' own normalisation)."""
import re, sys
sys.path.insert(0, 'scripts/catalog')
import verify_quotes as vq

url = sys.argv[1]
status, raw = vq.fetch(url)
print('## fetch status:', status, '| bytes:', len(raw or ''))
if not raw:
    sys.exit(1)
text = vq.extract(raw)
args = sys.argv[2:]
i = 0
while i < len(args):
    if args[i] == '-q':
        q = args[i + 1]; i += 2
        try:
            ok = vq.present(q, vq.norm(text))
        except Exception as e:
            ok = f'ERR {e}'
        print(f'## QUOTE {q[:70]!r}: {ok}')
        continue
    pat = args[i]; i += 1
    hits = [mm.start() for mm in re.finditer(pat, text, re.I)]
    print(f'## {pat!r}: {len(hits)} hit(s)')
    for h in hits[:4]:
        w = text[max(0, h - 150):h + 350]
        w = re.sub(r'[ \t]*\n[\s]*', ' ⏎ ', w)
        w = re.sub(r'[ \t]+', ' ', w)
        print('   ...' + w + '...')
