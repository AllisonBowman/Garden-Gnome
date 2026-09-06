"""Mechanical citation-liveness check: does each cited quote actually appear on
the cited page?

    python scripts/catalog/verify_quotes.py path/to/batch.json [more.json ...]

Run from garden-gnome/ with the project venv (needs httpx). Exit 1 on any MISS.
The raw-HTML cache lives beside this file in .quote_cache/ (gitignored).

For every citation, fetch the URL (raw HTML disk-cached, throttled per host,
browser UA), reduce the page to rendered text, and test whether the quote is
present after normalization on both sides. Prints HIT / MISS / INCONCLUSIVE /
SKIP per citation and a summary.

  MISS          the quote is not on the page although other quotes from the
                same page ARE -- the real candidate for a fabricated or
                paraphrased quote. Look at every one of these.
  INCONCLUSIVE  every quote citing this page misses. That is a page-level
                signal (JS-rendered content, a redirect to a shell), not
                evidence against any single quote.
  SKIP          PDF, non-200, or connection error (plantfinder.mobot.org and
                ask.ifas.ufl.edu refuse non-browser clients from here).

Composite quotes -- fragments the researcher joined with ' ... ', ' | ' or
' / ' (common in b1-b35) -- are split first and each fragment is checked on
its own; the citation is present if at least 80% of its fragments are.

The auditor's live-fetch judgement stays the final word; this just makes sure
every load-bearing quote gets looked at instead of only "when in doubt".

Politeness: one request per URL ever (raw HTML cached, so parser improvements
apply retroactively), >= 1.5 s between requests to the same host, and PDFs are
skipped rather than downloaded.
"""
import hashlib
import html
import json
import re
import sys
import time
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import httpx

CACHE = Path(__file__).parent / ".quote_cache"
CACHE.mkdir(exist_ok=True)
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
HOST_GAP = 1.5
_last: dict[str, float] = {}

VOID = {"img", "br", "hr", "input", "meta", "link", "source", "wbr", "area", "col"}
# separators researchers used to stitch non-adjacent page fragments
COMPOSITE_SEP = re.compile(r"\s*(?:\.\.\.|…|\s\|\s|\s/\s)\s*")


class _Text(HTMLParser):
    """Rendered text only. Skips script/style and anything aria-hidden -- RHS
    hangs a glossary definition off each glossed term inside an aria-hidden
    tooltip span, and a bare text dump splices that definition into the
    middle of the sentence being quoted."""
    SKIP_TAGS = {"script", "style", "noscript", "svg", "template"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.SKIP_TAGS or a.get("aria-hidden") == "true" or a.get("hidden") is not None:
            if tag not in VOID:
                self._skip_stack.append(tag)
            return
        if self._skip_stack:
            return
        for k in ("alt", "title"):
            if a.get(k):
                self.parts.append(a[k])

    def handle_endtag(self, tag):
        if self._skip_stack and self._skip_stack[-1] == tag:
            self._skip_stack.pop()

    def handle_data(self, data):
        if not self._skip_stack:
            self.parts.append(data)


def extract(raw_html: str) -> str:
    p = _Text()
    p.feed(raw_html)
    return " ".join(p.parts)


def norm(s: str) -> str:
    """Reduce to lower-case word tokens; punctuation dropped, units unified."""
    s = html.unescape(s or "")
    s = s.replace("–", "-").replace("—", "-")
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace(" ", " ").replace("°", " degrees ").replace("_", " ")  # nbsp, degree, markdown emphasis
    s = re.sub(r"(?<=\d)\s*(?:degrees)?\s*([CcFf])\b", r" degrees \1", s)
    s = re.sub(r"(?<=\d)\s*-\s*(?=\d)", "\x00", s)
    s = re.sub(r"[^\w\s%/\x00]", " ", s)
    s = s.replace("\x00", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def fetch(url: str) -> tuple[str, str]:
    """Return (status, raw_html). status: ok | http-NNN | error:X | pdf."""
    if url.lower().endswith(".pdf"):
        return "pdf", ""
    key = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".json")
    if key.exists():
        d = json.loads(key.read_text())
        return d["status"], d["text"]
    host = urlparse(url).netloc
    wait = HOST_GAP - (time.time() - _last.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    try:
        r = httpx.get(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"},
                      follow_redirects=True, timeout=30)
        _last[host] = time.time()
        if r.status_code != 200:
            status, text = f"http-{r.status_code}", ""
        elif "pdf" in r.headers.get("content-type", ""):
            status, text = "pdf", ""
        else:
            status, text = "ok", r.text
    except Exception as e:  # noqa: BLE001
        _last[host] = time.time()
        status, text = f"error:{type(e).__name__}", ""
    key.write_text(json.dumps({"status": status, "text": text}))
    return status, text


def _fragment_present(q: str, text: str) -> bool:
    if q and q in text:
        return True
    words = q.split()
    if len(words) < 4:
        return bool(words) and " ".join(words) in text
    runs = [" ".join(words[i:i + 4]) for i in range(len(words) - 3)]
    return sum(run in text for run in runs) / len(runs) >= 0.8


def present(raw_quote: str, text: str) -> bool:
    """Whole quote, or -- for a composite -- >= 80% of its fragments."""
    if _fragment_present(norm(raw_quote), text):
        return True
    frags = [f for f in COMPOSITE_SEP.split(raw_quote) if f.strip()]
    if len(frags) < 2:
        return False
    ok = sum(_fragment_present(norm(f), text) for f in frags)
    return ok / len(frags) >= 0.8


def check(paths: list[str]) -> int:
    rows = []  # (batch, name, claim, url, quote, status, present)
    page_text: dict[str, str] = {}
    for path in paths:
        data = json.loads(Path(path).read_text())
        batch = data.get("batch", Path(path).stem)
        for r in data["records"]:
            name = r.get("common_name") or r.get("scientific_name_given")
            for c in r.get("citations", []):
                status, raw = fetch(c["url"])
                if status == "ok" and c["url"] not in page_text:
                    page_text[c["url"]] = norm(extract(raw))
                ok = status == "ok" and present(c["quote"], page_text[c["url"]])
                rows.append((batch, name, c["claim"], c["url"], c["quote"], status, ok))

    per_url = defaultdict(list)
    for row in rows:
        per_url[row[3]].append(row)

    hit = miss = inconclusive = skip = 0
    for batch, name, claim, url, quote, status, ok in rows:
        if status != "ok":
            skip += 1
            print(f"SKIP [{status}] [{batch}] {name}: {claim[:60]}")
            continue
        if ok:
            hit += 1
            continue
        siblings = per_url[url]
        if len(siblings) >= 2 and not any(s[6] for s in siblings):
            inconclusive += 1
            print(f"INCONCLUSIVE [{batch}] {name}: {claim[:60]}\n      {url}")
            continue
        miss += 1
        print(f"MISS [{batch}] {name}: {claim[:70]}\n      {url}\n      quote: {quote[:200]!r}")

    print(f"\n{hit} hit, {miss} MISS, {inconclusive} inconclusive, {skip} skipped (pdf/http/error)")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(check(sys.argv[1:]))
