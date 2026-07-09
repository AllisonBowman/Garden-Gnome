"""Admit name-sharing and soft-default records from the review queue.

Policy (decided 2026-07-09): scientific names are the catalog's identity.
Records flagged ONLY for these reasons are admitted as review_status=
needs_review rather than held in the queue:

  - "no soil data — defaulted"           (Perenual soil field empty ~85%)
  - duplicate/shared COMMON names        (horticulturally normal)
  - cultivar/variant near-duplicates     (distinct records, related plants)

Everything else (exact scientific-name duplicates, implausible values,
missing care notes, unrecognized sunlight terms) stays in the queue.

Admitted records — and the already-cataloged plants they collide with — get
bidirectional cross-reference traits pointing at their adjacent plants by
scientific name:

  shares_common_name_with : other species with the same common name
  related_variant_of      : base species this cultivar/variant relates to

Usage (from garden-gnome/):
  python -m app.data.expansion.admit_queue           # apply
  python -m app.data.expansion.admit_queue --dry-run # counts only
"""
import argparse
import json
import re
from pathlib import Path

from sqlmodel import Session, select

from app.db.database import engine
from app.models.models import Species
from app.data.expansion.run_expansion import import_record
from app.data.expansion.recompute_xrefs import recompute_cross_references
from app.data.expansion.sample import to_review_entry, weighted_sample
from app.data.expansion.validate import _name_key

OUT_DIR = Path(__file__).parent / "output"

SOFT_PREFIXES = (
    "no soil data",
    "duplicate common name within batch",
    "common name already in catalog",
    "near-duplicate of",   # cultivar/variant containment or fuzzy
)
# Within the near-duplicate family, exact scientific-name collisions must
# stay out — they're the same plant, not an adjacent one.
HARD_PREFIXES = (
    "scientific name already in catalog",
    "duplicate scientific name within batch",
)


def is_admissible(issues: list[str]) -> bool:
    for issue in issues:
        if issue.startswith(HARD_PREFIXES):
            return False
        if not issue.startswith(SOFT_PREFIXES):
            return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sample-fraction", type=float, default=0.075)
    args = ap.parse_args()

    queue = json.loads((OUT_DIR / "review_queue.json").read_text(encoding="utf-8"))
    admit = [e for e in queue if is_admissible(e["issues"])]
    keep = [e for e in queue if not is_admissible(e["issues"])]
    print(f"queue: {len(queue)} | admissible: {len(admit)} | staying queued: {len(keep)}")

    with Session(engine) as session:
        existing = session.exec(select(Species)).all()
        existing_sci = {_name_key(s.scientific_name) for s in existing}

        # ── Import admissible records (needs_review) ─────────────────────
        imported = 0
        skipped_sci_dup = 0
        for entry in admit:
            rec = dict(entry["record"])
            if _name_key(rec["scientific_name"]) in existing_sci:
                skipped_sci_dup += 1  # exact scientific identity — true duplicate
                continue
            rec["review_status"] = "needs_review"
            rec["review_note"] = "; ".join(entry["issues"])[:400]
            if not args.dry_run:
                import_record(rec, session)
            existing_sci.add(_name_key(rec["scientific_name"]))
            imported += 1
        if not args.dry_run:
            session.commit()

        # ── Bidirectional cross-reference traits over the FULL catalog ───
        # (shared with recompute_xrefs so prod can be re-synced independently)
        common_groups, variant_links = recompute_cross_references(session)
        if not args.dry_run:
            session.commit()
        else:
            session.rollback()  # discard xref upserts in preview mode

        # ── Rewrite the queue with what's left; refresh the sample ───────
        if not args.dry_run:
            (OUT_DIR / "review_queue.json").write_text(
                json.dumps(keep, indent=2, ensure_ascii=False), encoding="utf-8")
            expansion_recs = [
                {"common_name": s.common_name, "scientific_name": s.scientific_name,
                 "source": s.source, "review_status": s.review_status,
                 "light_need": s.light_need, "toxic_to_pets": s.toxic_to_pets,
                 "humidity_pct_min": s.humidity_pct_min, "humidity_pct_max": s.humidity_pct_max,
                 "temp_f_min": s.temp_f_min, "temp_f_max": s.temp_f_max,
                 "soil_type": s.soil_type, "care_notes": s.care_notes}
                for s in session.exec(select(Species).where(
                    Species.source == "perenual")).all()
            ]
            sample = [to_review_entry(r) for r in
                      weighted_sample(expansion_recs, args.sample_fraction)]
            (OUT_DIR / "review_sample.json").write_text(
                json.dumps(sample, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"sample refreshed: {len(sample)} records for the citation pass")

        total = len(session.exec(select(Species)).all())

    print(f"imported: {imported} (skipped {skipped_sci_dup} exact scientific dups)")
    print(f"cross-references: {common_groups} shared-common-name groups, "
          f"{variant_links} variant links")
    print(f"catalog total: {total} species")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
