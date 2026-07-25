"""One command to populate the catalog as far as free sources allow.

Runs the cheap passes in the order that makes the expensive one smaller, merges
their verdicts per species, and reports precisely what is left:

    1. genus_fill   — offline, free. Fills defaulted care data from approved
                      siblings in the same genus.
    2. wiki_enrich  — free (MediaWiki). Finds synonym/duplicate rows and
                      corrects names to accepted binomials.
    3. research_review — COSTS MONEY. Not run here. This script tells you how
                      many records still need it, which is the point: dedup and
                      infer first so the paid pass runs over a smaller set.

Merge precedence, and why:

    * A `rejected` verdict from any source wins. If a row is a duplicate of one
      we already hold, filling in its care data is wasted effort — it should be
      removed, not improved.
    * Otherwise corrections are unioned. The two sources answer different
      questions (wiki: what is this plant called; genus: what care does it
      want), so they compose rather than conflict. Where they do overlap, the
      taxonomic source wins on names and the genus source wins on care.

Nothing here writes to the catalog. It drafts into the file apply_review.py
consumes, for a human to read first.

Usage:
    python -m app.data.expansion.populate_catalog --dry-run     # report only
    python -m app.data.expansion.populate_catalog               # write merged file
    python -m app.data.expansion.apply_review output/populate_review.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).parent / "output"
MERGED_FILE = OUT_DIR / "populate_review.json"

# Which source wins for a given field when both propose one.
NAME_FIELDS = {"scientific_name", "common_name"}

RESEARCHED_BY = "merged free passes: genus inference + wikipedia (unverified — needs human review)"


def _key(entry: dict) -> str:
    return (entry.get("record", {}).get("scientific_name") or "").strip().lower()


def merge_one(record: dict, reviews: list[dict]) -> dict:
    """Combine several draft verdicts for one species into one.

    Pure: takes verdict dicts, returns a verdict dict. `reviews` is ordered
    least- to most-authoritative on names (genus first, taxonomy last)."""
    reviews = [r for r in reviews if r]
    if not reviews:
        return {
            "verdict": "uncertain", "citation_source": "", "citation_url": "",
            "corrections": {}, "notes": "no source produced a verdict.",
            "researched_by": RESEARCHED_BY,
        }

    # A duplicate row is not worth improving — removal beats enrichment.
    for r in reviews:
        if r.get("verdict") == "rejected":
            return {**r, "researched_by": RESEARCHED_BY}

    corrections: dict = {}
    notes: list[str] = []
    sources: list[str] = []
    urls: list[str] = []
    for r in reviews:
        for field, value in (r.get("corrections") or {}).items():
            # Later reviews win on names; earlier (genus) keeps care fields it
            # already claimed, since the taxonomic source has no opinion there.
            if field in NAME_FIELDS or field not in corrections:
                corrections[field] = value
        if r.get("notes"):
            notes.append(r["notes"])
        if r.get("citation_source"):
            sources.append(r["citation_source"])
        if r.get("citation_url"):
            urls.append(r["citation_url"])

    return {
        "verdict": "corrected" if corrections else "uncertain",
        "citation_source": " + ".join(dict.fromkeys(sources)),
        "citation_url": urls[0] if urls else "",
        "corrections": corrections,
        "notes": " ".join(notes),
        "researched_by": RESEARCHED_BY,
    }


def merge_reports(*reports: list[dict]) -> list[dict]:
    """Merge per-source review files into one list, keyed by scientific name.

    Argument order is precedence order for names: pass genus_fill first,
    wiki_enrich last."""
    order: list[str] = []
    records: dict[str, dict] = {}
    buckets: dict[str, list[dict]] = {}

    for report in reports:
        for entry in report or []:
            k = _key(entry)
            if not k:
                continue
            if k not in buckets:
                buckets[k] = []
                order.append(k)
                records[k] = entry.get("record", {})
            buckets[k].append(entry.get("review", {}))

    return [{"record": records[k], "review": merge_one(records[k], buckets[k])} for k in order]


def coverage(entries: list[dict], care_fields: list[str]) -> dict:
    """How much of the backlog the free passes actually resolved."""
    stats = {"total": len(entries), "duplicates": 0, "filled": 0,
             "partial": 0, "still_needs_research": 0}
    for e in entries:
        review = e.get("review", {})
        record = e.get("record", {})
        if review.get("verdict") == "rejected":
            stats["duplicates"] += 1
            continue
        corrections = review.get("corrections") or {}
        merged = {**record, **corrections}
        missing = [f for f in care_fields
                   if merged.get(f) is None
                   or (isinstance(merged.get(f), str) and not merged[f].strip())]
        if not missing and corrections:
            stats["filled"] += 1
        elif corrections:
            stats["partial"] += 1
        else:
            stats["still_needs_research"] += 1
    return stats


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def main() -> int:
    from app.data.expansion.genus_fill import REVIEW_FILE as GENUS_FILE
    from app.data.expansion.wiki_enrich import REVIEW_FILE as WIKI_FILE
    from app.data.expansion.research_review import CORRECTABLE

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    args = ap.parse_args()

    genus, wiki = _load(GENUS_FILE), _load(WIKI_FILE)
    if not genus and not wiki:
        print("  No source reports found. Run the free passes first:")
        print("    python -m app.data.expansion.genus_fill --all")
        print("    python -m app.data.expansion.wiki_enrich --all")
        return 2

    print(f"  genus_fill:  {len(genus)} entries")
    print(f"  wiki_enrich: {len(wiki)} entries")

    # genus first, wiki last — wiki is authoritative on names.
    merged = merge_reports(genus, wiki)
    care_fields = [f for f in CORRECTABLE if f not in NAME_FIELDS and f != "care_notes"]
    stats = coverage(merged, care_fields)

    print(f"\n  merged: {stats['total']} species")
    print(f"    {stats['duplicates']:>5}  duplicates to remove (identification fix)")
    print(f"    {stats['filled']:>5}  care data now complete")
    print(f"    {stats['partial']:>5}  partially filled")
    print(f"    {stats['still_needs_research']:>5}  still need a horticultural source (paid pass)")

    remaining = stats["still_needs_research"] + stats["partial"]
    print(f"\n  The paid pass now has {remaining} records to cover instead of "
          f"{stats['total']} — that is the saving.")

    if args.dry_run:
        print("\n  --dry-run: nothing written.")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MERGED_FILE.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  wrote {MERGED_FILE}")
    print("  Everything here is INFERRED or taxonomic — read it before applying.")
    print(f"  python -m app.data.expansion.apply_review {MERGED_FILE}")
    print("  Nothing has been written to the catalog by this script.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
