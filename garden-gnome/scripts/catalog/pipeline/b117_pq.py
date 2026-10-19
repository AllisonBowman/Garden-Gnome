"""b117_pq.py URL QUOTE [QUOTE...] -- b117 helper: does verify_quotes.present() accept each quote? (\\n in args = newline)"""
import sys
sys.path.insert(0, 'scripts/catalog')
import verify_quotes as vq

url = sys.argv[1]
status, raw = vq.fetch(url)
print('## fetch', status)
text = vq.norm(vq.extract(raw)) if raw else ''
for q in sys.argv[2:]:
    q = q.replace('\\n', '\n')
    print(vq.present(q, text), "whole=%s" % vq._fragment_present(vq.norm(q), text), repr(q[:110]))
