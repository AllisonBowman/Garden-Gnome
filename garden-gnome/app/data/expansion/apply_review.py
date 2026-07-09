"""Apply the manual review pass back to the catalog.

Workflow: run_expansion.py writes output/review_sample.json. For each entry,
you cross-check the record against NC State Extension Plant Toolbox
(plants.ces.ncsu.edu) or Missouri Botanical Garden Plant Finder
(missouribotanicalgarden.org), then fill in the `review` block:

  "verdict": "confirmed"   record is right — mark verified with your citation
             "corrected"   apply the `corrections` {field: value} first, then verify
             "rejected"    delete the record from the catalog
  "citation_source": "NC State Extension Plant Toolbox"
  "citation_url": "https://plants.ces.ncsu.edu/plants/..."

Then run (from garden-gnome/):
  python -m app.data.expansion.apply_review output/review_sample.json

Entries with an empty verdict are skipped, so you can apply partial progress
any time — re-running is safe.
"""
import argparse
import json
from pathlib import Path

from sqlmodel import Session, select

from app.db.database import engine
from app.models.models import Species

SPECIES_FIELDS = {
    "common_name", "scientific_name", "light_need", "humidity_pct_min",
    "humidity_pct_max", "temp_f_min", "temp_f_max", "soil_type",
    "toxic_to_pets", "care_notes",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("review_file")
    args = ap.parse_args()

    entries = json.loads(Path(args.review_file).read_text(encoding="utf-8"))
    applied = skipped = missing = 0

    with Session(engine) as session:
        for entry in entries:
            rec, review = entry["record"], entry["review"]
            verdict = (review.get("verdict") or "").strip().lower()
            if not verdict:
                skipped += 1
                continue

            species = session.exec(select(Species).where(
                Species.scientific_name == rec["scientific_name"])).first()
            if not species:
                missing += 1
                print(f"  ! not in catalog (skipped): {rec['scientific_name']}")
                continue

            if verdict == "rejected":
                session.delete(species)
                applied += 1
                continue

            if verdict == "corrected":
                for field, value in (review.get("corrections") or {}).items():
                    if field in SPECIES_FIELDS:
                        setattr(species, field, value)
                    else:
                        print(f"  ! unknown correction field {field!r} on {rec['scientific_name']}")

            citation = " — ".join(filter(None, [
                review.get("citation_source", "").strip(),
                review.get("citation_url", "").strip(),
                review.get("notes", "").strip(),
            ]))
            species.review_status = "verified"
            species.review_note = citation or "manually verified"
            session.add(species)
            applied += 1

        session.commit()

    print(f"Applied {applied}, skipped (no verdict) {skipped}, not found {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
