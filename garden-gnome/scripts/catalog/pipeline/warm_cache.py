"""warm_cache.py FILE [FILE ...] -- fetch every page these batch files cite that the quote cache lacks.

Run from garden-gnome/ OUTSIDE the sandbox (its proxy denies the extension sites to this machine). A cache entry
that exists is never re-fetched by verify_quotes, so an entry recording a failed fetch hides a page for good: this
deletes such entries and fetches again. Missouri Botanical Garden and Clemson refuse this machine outright and are
left alone. Prints what is still missing afterwards -- a citation to one of those pages cannot be verified here.
"""
import collections
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verify_quotes as vq  # noqa: E402

REFUSE = ('plantfinder.mobot.org', 'www.missouribotanicalgarden.org', 'hgic.clemson.edu')


def entry(url):
    return vq.CACHE / (hashlib.sha1(url.encode()).hexdigest() + '.json')


def ok(url):
    p = entry(url)
    return p.exists() and json.loads(p.read_text()).get('status') == 'ok'


urls = set()
for f in sys.argv[1:]:
    for r in json.loads(Path(f).read_text())['records']:
        urls |= {c['url'] for c in r.get('citations') or []}
todo = sorted(u for u in urls if not u.lower().endswith('.pdf') and not ok(u) and u.split('/')[2] not in REFUSE)
got = collections.Counter()
for u in todo:
    entry(u).unlink(missing_ok=True)
    status, _ = vq.fetch(u)
    got[status] += 1
    if status != 'ok':
        entry(u).unlink(missing_ok=True)
still = sorted(u for u in urls if not u.lower().endswith('.pdf') and not ok(u))
print(f'{len(urls)} cited pages; fetched {len(todo)}: {dict(got)}; still not cached: {len(still)}')
for u in still:
    print('   ', u)
