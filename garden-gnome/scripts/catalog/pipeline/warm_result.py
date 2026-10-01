"""warm_result.py RESULT.json [...] -- fetch every page a backfill RESULT cites that the quote cache lacks.

warm_cache.py warms what a batch file already cites; a round-5 result can cite a page no batch file has carried
yet (the species' own page on a registered authority, found by the researcher). Run from garden-gnome/ OUTSIDE the
sandbox, before landing, so commit_backfill's cache-only check can actually test those quotes. Also reports any
citation whose domain is not a registered authority -- such a citation resolves to nothing at load.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import verify_quotes as vq  # noqa: E402
from app.data.claims.authorities import REGISTRY, domain_of  # noqa: E402
import hashlib  # noqa: E402

# Same rules as warm_cache.py (which runs on import, so it is not imported):
# these hosts refuse this machine outright and are left alone.
REFUSE = ('plantfinder.mobot.org', 'www.missouribotanicalgarden.org', 'hgic.clemson.edu')


def entry(url):
    return vq.CACHE / (hashlib.sha1(url.encode()).hexdigest() + '.json')


def ok(url):
    p = entry(url)
    return p.exists() and json.loads(p.read_text()).get('status') == 'ok'

urls = set()
for f in sys.argv[1:]:
    for e in json.loads(Path(f).read_text())["landed"]:
        urls |= {c["url"] for c in e["record"].get("citations", [])}
unregistered = sorted(u for u in urls if domain_of(u) not in REGISTRY)
todo = sorted(u for u in urls if not u.lower().endswith(".pdf") and not ok(u) and u.split("/")[2] not in REFUSE)
for u in todo:
    entry(u).unlink(missing_ok=True)
    status, _ = vq.fetch(u)
    print(f"  {status:10} {u}")
still = sorted(u for u in urls if not u.lower().endswith(".pdf") and not ok(u))
print(f"{len(urls)} cited pages; fetched {len(todo)}; still not cached: {len(still)}; unregistered: {len(unregistered)}")
for u in still:
    print("  NOT CACHED", u)
for u in unregistered:
    print("  UNREGISTERED", u)
