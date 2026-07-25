"""Wikipedia catalog triage — free, deterministic enrichment of needs_review species.

Companion to research_review.py. That script asks an LLM to verify care numbers
against horticultural sources and costs real money per record, which is why the
1,688-record backlog has not moved. This one uses the MediaWiki API: free,
deterministic, and rate-limited only by politeness.

WHAT THIS IS GOOD AT (and it is deliberately narrow):

  Wikipedia is a taxonomic source, not a houseplant-care source. It will not
  tell you to water every 7-10 days or that a plant wants 60% humidity. It is
  excellent at the OTHER half of the catalog problem — the half that actually
  breaks identification:

  * Synonyms / near-duplicates. `Anthurium scherzerianum` and a row calling
    itself something that redirects to it are the same plant. Redirect
    resolution finds these deterministically. Near-duplicate rows are precisely
    what make identification ambiguous, so removing them is an ID fix, not just
    tidying.
  * Names that are not accepted species at all (misspellings, cultivar strings,
    genus-only rows).
  * Correcting a scientific name to the accepted binomial.
  * Toxicity, where an article states it outright.

  Care numbers are left alone and reported as `uncertain`. The point is to
  SHRINK and DEDUPLICATE the backlog so the expensive research pass runs over a
  smaller, cleaner set.

SAFETY (mirrors research_review.py — the rules live in that module's sanitize,
imported here so the two cannot drift):

  * Never writes to the catalog. It drafts verdicts into the same file
    apply_review.py already consumes, for a human to read first.
  * Every entry is stamped machine-drafted.
  * A verdict without a citation URL is downgraded to `uncertain`.
  * Corrections outside CORRECTABLE are stripped.
  * Toxicity is only ever proposed non-toxic -> toxic. Clearing a toxicity
    warning because an article failed to mention it would be an unsafe
    inference, so that direction is refused outright.

LICENSING: Wikipedia prose is CC BY-SA. This tool extracts *facts* (a canonical
title, a boolean, a redirect target) and cites the article URL; it never copies
article prose into care_notes, so nothing ships that would carry a share-alike
obligation.

Usage:
    python -m app.data.expansion.wiki_enrich --limit 25      # start small
    python -m app.data.expansion.wiki_enrich --all           # whole backlog (free)
    python -m app.data.expansion.wiki_enrich --mock-dir fixtures/wiki   # offline
    python -m app.data.expansion.apply_review output/wiki_review.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from sqlmodel import Session, select

from app.db.database import engine
from app.models.models import Species
from app.data.expansion.research_review import CORRECTABLE, sanitize as _sanitize

OUT_DIR = Path(__file__).parent / "output"
CHECKPOINT = OUT_DIR / "wiki_records.jsonl"
REVIEW_FILE = OUT_DIR / "wiki_review.json"

WIKI_API = "https://en.wikipedia.org/w/api.php"
ARTICLE_BASE = "https://en.wikipedia.org/wiki/"
# Wikimedia's policy requires a descriptive User-Agent with contact info;
# generic agents get rate-limited or blocked.
USER_AGENT = (
    "PlantAdvocate-catalog-triage/1.0 "
    "(https://plantadvocate.ai; support@plantadvocate.ai)"
)
# Courtesy pause between requests. Wikimedia asks for serial, unhurried access
# from batch tools; the backlog is not urgent enough to justify hammering them.
REQUEST_PAUSE_S = 0.3
DEFAULT_LIMIT = 25

RESEARCHED_BY = "wikipedia triage (unverified — needs human review)"

# Phrases that constitute an explicit toxicity statement. Deliberately narrow:
# a hit must pair a toxicity word with an ingestion/animal context.
_TOX_PATTERNS = [
    r"toxic\s+to\s+(?:cats|dogs|pets|animals|humans)",
    r"poisonous\s+to\s+(?:cats|dogs|pets|animals|humans)",
    r"toxic\s+if\s+(?:ingested|eaten|consumed)",
    r"poisonous\s+if\s+(?:ingested|eaten|consumed)",
    r"causes?\s+(?:severe\s+)?(?:irritation|burning|swelling)[^.]{0,40}(?:mouth|throat|ingest)",
    r"calcium\s+oxalate[^.]{0,60}(?:irritat|toxic|poison)",
]


def sanitize(review: dict) -> dict:
    """Same contract and downgrade rules as research_review, different stamp."""
    out = _sanitize(review)
    out["researched_by"] = RESEARCHED_BY
    return out


# --- pure helpers (no network; unit-tested) ---------------------------------

def article_url(title: str) -> str:
    return ARTICLE_BASE + title.replace(" ", "_")


def looks_like_binomial(name: str) -> bool:
    """A genus + species pair, optionally with a subspecies/variety.

    Guards against 'correcting' a name to a genus-only page or an article like
    'List of Anthurium species'."""
    return bool(re.fullmatch(r"[A-Z][a-z-]+ [a-z][a-z-]+(?: [a-z.\- ]+)?", name.strip()))


def detect_toxicity(text: str) -> bool:
    """True only when the text states toxicity outright. Absence proves nothing,
    so there is no False return — the caller treats not-True as 'unknown'."""
    low = (text or "").lower()
    return any(re.search(p, low) for p in _TOX_PATTERNS)


def is_unusable_page(wiki: dict) -> str | None:
    """Reason this page can't support a verdict, or None if it's usable."""
    if not wiki or wiki.get("missing"):
        return "no Wikipedia article found"
    if wiki.get("is_disambiguation"):
        return "Wikipedia title is a disambiguation page"
    return None


def derive_verdict(
    record: dict,
    wiki: dict,
    other_names: set[str],
) -> dict:
    """Turn a catalog record + its Wikipedia lookup into a draft verdict.

    `other_names` is every OTHER scientific name in the catalog, lowercased —
    used to tell a synonym that duplicates an existing row (reject) from one
    that merely needs its name corrected.

    Pure: no network, no DB, no clock. This is the whole decision surface."""
    name = (record.get("scientific_name") or "").strip()

    unusable = is_unusable_page(wiki)
    if unusable:
        return sanitize({
            "verdict": "uncertain",
            "notes": f"{unusable} for {name!r}; care data not checked.",
        })

    canonical = (wiki.get("title") or "").strip()
    url = wiki.get("url") or article_url(canonical)
    extract = wiki.get("extract") or ""
    redirected = wiki.get("redirected_from") is not None or (
        canonical.lower() != name.lower()
    )

    # 1. A redirect landing on a title another row already holds means these two
    #    rows are the same plant. That ambiguity is what breaks identification.
    if redirected and canonical.lower() in other_names:
        return sanitize({
            "verdict": "rejected",
            "citation_source": "Wikipedia",
            "citation_url": url,
            "notes": (
                f"{name!r} redirects to {canonical!r}, which the catalog already "
                f"holds as a separate row — these are the same plant. Duplicate "
                f"rows make identification ambiguous; keep the other row."
            ),
        })

    # 2. A redirect to an accepted binomial no other row holds: the name is a
    #    synonym and should be corrected rather than deleted.
    if redirected and looks_like_binomial(canonical):
        return sanitize({
            "verdict": "corrected",
            "citation_source": "Wikipedia",
            "citation_url": url,
            "corrections": {"scientific_name": canonical},
            "notes": (
                f"{name!r} is a synonym of the accepted name {canonical!r}. "
                f"Care values were not checked."
            ),
        })

    # 3. Redirect to something that isn't a species page (genus, list, cultivar
    #    group). Not actionable automatically — hand it to a human.
    if redirected:
        return sanitize({
            "verdict": "uncertain",
            "citation_source": "Wikipedia",
            "citation_url": url,
            "notes": (
                f"{name!r} resolves to {canonical!r}, which does not look like an "
                f"accepted species name — possibly a genus or cultivar row."
            ),
        })

    # 4. Title matches. Wikipedia confirms the species is real, but says nothing
    #    about watering intervals or humidity, so the care record stays
    #    unverified. The one fact worth lifting is an explicit toxicity
    #    statement, and only in the safe direction.
    if detect_toxicity(extract) and record.get("toxic_to_pets") is False:
        return sanitize({
            "verdict": "corrected",
            "citation_source": "Wikipedia",
            "citation_url": url,
            "corrections": {"toxic_to_pets": True},
            "notes": (
                "Article states this plant is toxic, but the record says it is "
                "pet-safe. Care values were not checked."
            ),
        })

    return sanitize({
        "verdict": "uncertain",
        "citation_source": "Wikipedia",
        "citation_url": url,
        "notes": (
            f"{canonical!r} is an accepted species and not a duplicate, but "
            f"Wikipedia carries no indoor care data — light/humidity/temp/soil "
            f"still need a horticultural source."
        ),
    })


# --- network layer (thin on purpose) ----------------------------------------

def fetch_wiki(name: str, client) -> dict:
    """Look a species up, following redirects. Returns {} shaped for the pure
    helpers above; never raises — a failed lookup is just 'uncertain'."""
    try:
        resp = client.get(
            WIKI_API,
            params={
                "action": "query",
                "titles": name,
                "redirects": 1,
                "prop": "extracts|pageprops",
                "exintro": 1,
                "explaintext": 1,
                "format": "json",
                "formatversion": 2,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=20.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # network, HTTP, or JSON — all mean "unverified"
        return {"missing": True, "error": f"{type(exc).__name__}: {exc}"}

    query = data.get("query") or {}
    pages = query.get("pages") or []
    if not pages:
        return {"missing": True}
    page = pages[0]
    if page.get("missing"):
        return {"missing": True}

    redirects = query.get("redirects") or []
    props = page.get("pageprops") or {}
    return {
        "title": page.get("title", ""),
        "extract": page.get("extract", ""),
        "url": article_url(page.get("title", "")),
        "redirected_from": redirects[0]["from"] if redirects else None,
        "is_disambiguation": "disambiguation" in props,
    }


def load_checkpoint() -> dict[str, dict]:
    done: dict[str, dict] = {}
    if CHECKPOINT.exists():
        for line in CHECKPOINT.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                done[entry["record"]["scientific_name"]] = entry
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def main() -> int:
    ap = argparse.ArgumentParser(description="Wikipedia triage of needs_review species")
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                    help=f"triage at most N records (default {DEFAULT_LIMIT})")
    ap.add_argument("--all", action="store_true",
                    help="triage the entire backlog (free, but slow and polite)")
    ap.add_argument("--status", default="needs_review",
                    help="which review_status to work through")
    ap.add_argument("--mock-dir", default=None,
                    help="read canned Wikipedia payloads from a fixture dir")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    done = load_checkpoint()

    with Session(engine) as session:
        pending = session.exec(
            select(Species).where(Species.review_status == args.status)
        ).all()
        # Every name in the catalog, for duplicate detection — not just the
        # pending ones, since a synonym usually duplicates an *approved* row.
        all_names = {
            (n or "").strip().lower()
            for n in session.exec(select(Species.scientific_name)).all()
        }
        targets = [sp for sp in pending if sp.scientific_name not in done]
        records = [{f: getattr(sp, f, None) for f in CORRECTABLE} | {
            "review_status": sp.review_status, "review_note": sp.review_note or "",
        } for sp in targets]

    total_pending = len(targets)
    if not args.all:
        targets, records = targets[:max(0, args.limit)], records[:max(0, args.limit)]

    print(f"  {args.status}: {total_pending} untriaged, {len(done)} already checkpointed")
    print(f"  triaging {len(targets)} this run (Wikipedia — free)")
    if not targets:
        print("  nothing to do")

    mock_dir = Path(args.mock_dir) if args.mock_dir else None
    client = None
    if targets and mock_dir is None:
        import httpx
        client = httpx.Client(follow_redirects=True)

    try:
        with CHECKPOINT.open("a", encoding="utf-8") as ckpt:
            for sp, record in zip(targets, records):
                name = sp.scientific_name or ""
                if mock_dir is not None:
                    fixture = mock_dir / f"{name.replace(' ', '_')}.json"
                    wiki = json.loads(fixture.read_text(encoding="utf-8")) if fixture.exists() else {}
                else:
                    wiki = fetch_wiki(name, client)
                    time.sleep(REQUEST_PAUSE_S)

                others = all_names - {name.strip().lower()}
                review = derive_verdict(record, wiki, others)

                entry = {"record": record, "review": review}
                done[name] = entry
                ckpt.write(json.dumps(entry, ensure_ascii=False) + "\n")
                ckpt.flush()
                print(f"  {review['verdict']:<10} {name}")
    finally:
        if client is not None:
            client.close()

    entries = list(done.values())
    REVIEW_FILE.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")

    tally: dict[str, int] = {}
    for e in entries:
        v = e["review"]["verdict"]
        tally[v] = tally.get(v, 0) + 1
    print(f"\n  wrote {REVIEW_FILE} ({len(entries)} entries)")
    print(f"  verdicts: {tally}")
    print("\n  'rejected' = duplicate/synonym rows worth removing — that is the")
    print("  identification fix. 'uncertain' still needs a horticultural source")
    print("  for care numbers; run research_review.py over what survives.")
    print(f"\n  Next: read the file, then")
    print(f"  python -m app.data.expansion.apply_review {REVIEW_FILE}")
    print("  Nothing has been written to the catalog by this script.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
