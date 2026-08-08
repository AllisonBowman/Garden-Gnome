"""Apply the manual review pass back to the catalog.

Workflow: run_expansion.py writes output/review_sample.json. For each entry,
you cross-check the record against NC State Extension Plant Toolbox
(plants.ces.ncsu.edu) or Missouri Botanical Garden Plant Finder
(missouribotanicalgarden.org), then fill in the `review` block:

  "verdict": "confirmed"   record is right — mark verified with your citation
             "corrected"   apply the `corrections` {field: value} first, then verify
             "rejected"    delete the record from the catalog
             "uncertain"   leave the record exactly as it is
  "citation_source": "NC State Extension Plant Toolbox"
  "citation_url": "https://plants.ces.ncsu.edu/plants/..."

Then run (from garden-gnome/):
  python -m app.data.expansion.apply_review output/review_sample.json

Pass --dry-run first: it walks the whole file, prints every count and
refusal, and leaves the database byte-identical.

Entries with an empty verdict are skipped, so you can apply partial progress
any time — re-running is safe. `uncertain` is also a skip: this is the only
module that writes to the catalog, and `verified` in the database means a
human checked it, so a verdict that says "I'm not sure" must never end in
that stamp. Anything that is not one of the four known verdicts is refused
loudly rather than guessed at — a typo in a review file is not a review.

Three more refusals guard the catalog:
  - a `toxic_to_pets` true -> false correction never goes through this
    script. Telling someone a toxic plant is safe is the one mistake this
    catalog cannot survive; make that change by hand, against a source, in a
    migration that says why.
  - `rejected` is refused while any plant references the species — people
    are growing these; deleting the row out from under them would take their
    care history's meaning with it.
  - an ambiguous scientific name (two catalog rows, one name) is refused
    rather than silently picking one.
"""
import argparse
import json
from pathlib import Path

from sqlmodel import Session, select

from app.data.expansion.research_review import CORRECTABLE
from app.db.database import engine
from app.models.models import Plant, ReviewStatus, Species

KNOWN_VERDICTS = {"confirmed", "corrected", "rejected", "uncertain"}


def apply_reviews(
    entries: list[dict], session: Session, *, dry_run: bool = False,
) -> tuple[dict, list[str]]:
    """Apply a review file to the catalog through one session.

    Returns (counts, refusals). With dry_run the session is rolled back
    instead of committed — the database is left byte-identical.
    """
    counts = {"applied": 0, "uncertain": 0, "no_verdict": 0, "missing": 0}
    refused: list[str] = []

    for entry in entries:
        rec, review = entry["record"], entry["review"]
        name = rec["scientific_name"]
        verdict = (review.get("verdict") or "").strip().lower()
        if not verdict:
            counts["no_verdict"] += 1
            continue
        if verdict == "uncertain":
            counts["uncertain"] += 1
            continue
        if verdict not in KNOWN_VERDICTS:
            refused.append(f"unknown verdict {verdict!r} on {name}")
            continue

        matches = session.exec(select(Species).where(
            Species.scientific_name == name)).all()
        if not matches:
            counts["missing"] += 1
            print(f"  ! not in catalog (skipped): {name}")
            continue
        if len(matches) > 1:
            refused.append(
                f"ambiguous name {name!r} matches {len(matches)} rows "
                f"(ids {sorted(sp.id for sp in matches)})")
            continue
        species = matches[0]

        if verdict == "rejected":
            grown = session.exec(select(Plant).where(
                Plant.species_id == species.id)).first()
            if grown:
                refused.append(
                    f"rejected {name!r} refused: plants reference it")
                continue
            session.delete(species)
            counts["applied"] += 1
            continue

        if verdict == "corrected":
            corrections = review.get("corrections") or {}
            if corrections.get("toxic_to_pets") is False \
                    and species.toxic_to_pets:
                refused.append(
                    f"toxicity true -> false on {name!r} refused: "
                    "never through this script")
                continue
            for field, value in corrections.items():
                if field in CORRECTABLE:
                    setattr(species, field, value)
                else:
                    print(f"  ! unknown correction field {field!r} on {name}")

        citation = " — ".join(filter(None, [
            review.get("citation_source", "").strip(),
            review.get("citation_url", "").strip(),
            review.get("notes", "").strip(),
        ]))
        researched_by = (review.get("researched_by") or "").strip()
        if researched_by:
            citation = " — ".join(filter(None, [
                citation, f"researched by {researched_by}"]))
        species.review_status = ReviewStatus.verified
        species.review_note = citation or "manually verified"
        session.add(species)
        counts["applied"] += 1

    if dry_run:
        session.rollback()
    else:
        session.commit()
    return counts, refused


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("review_file")
    ap.add_argument(
        "--dry-run", action="store_true",
        help="walk the file and report; write nothing")
    args = ap.parse_args()

    entries = json.loads(Path(args.review_file).read_text(encoding="utf-8"))

    with Session(engine) as session:
        counts, refused = apply_reviews(
            entries, session, dry_run=args.dry_run)

    for reason in refused:
        print(f"  ! REFUSED: {reason}")
    print(
        f"Applied {counts['applied']}, "
        f"uncertain (left alone) {counts['uncertain']}, "
        f"no verdict {counts['no_verdict']}, "
        f"not found {counts['missing']}, "
        f"refused {len(refused)}"
        + (" — DRY RUN, nothing written" if args.dry_run else "")
    )
    return 1 if refused else 0


if __name__ == "__main__":
    raise SystemExit(main())
