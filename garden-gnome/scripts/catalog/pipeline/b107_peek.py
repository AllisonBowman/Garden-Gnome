"""b107-only: print original research values from b107-resume.js CACHE.research."""
import json, sys
s = open('scripts/catalog/pipeline/b107-resume.js').read()
line = [l for l in s.split('\n') if l.startswith('const CACHE =')][0]
c = json.loads(line[len('const CACHE ='):].strip().rstrip(';'))
R = c['research']
if len(sys.argv) == 1:
    print(c.keys(), R.keys())
for a in sys.argv[1:]:
    k, f = a.split(':')
    print('\n##', k, f, '\n', json.dumps(R[k].get(f), ensure_ascii=False, indent=1))
