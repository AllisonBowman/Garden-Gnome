"""Genus-level care inference — fills defaulted care data with no network at all.

The catalog's problem is not that care data is unknowable; it is that 1,688
rows were machine-built with mapper defaults ("no soil data — defaulted") and
verifying each one against a horticultural source costs money and time.

But care attributes are largely conserved within a genus. Every Anthurium wants
broadly the same humidity; every Sansevieria tolerates the same neglect. The
catalog already holds 252 human-approved species. Wherever a needs_review row
shares a genus with an approved, human-reviewed sibling, that sibling's care
envelope is a far better estimate than a mapper default — and it costs nothing.

WHAT THIS DOES AND DOESN'T CLAIM

  This is inference, not verification. Every entry it drafts is stamped as
  genus-inferred and carries the sibling count so a reviewer can weigh it. A
  genus with one approved sibling is a weak signal; one with six is strong.
  The verdict is never `confirmed` — that word is reserved for a record checked
  against a source.

SAFETY

  * Only fills fields that are MISSING or flagged defaulted. It never
    overwrites care data that is already present.
  * Toxicity is inherited ONLY when every approved sibling agrees. Genus
    toxicity is usually consistent (aroids and their calcium oxalate), but a
    split vote means the genus does not determine it, and guessing on a
    pet-safety field is not acceptable.
  * Never touches species-specific text (common_name, scientific_name,
    care_notes) — those do not generalize across a genus.
  * Never writes to the catalog. Drafts into the file apply_review.py consumes.

Usage:
    python -m app.data.expansion.genus_fill --limit 50
    python -m app.data.expansion.genus_fill --all
    python -m app.data.expansion.apply_review output/genus_review.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

from sqlmodel import Session, select

from app.db.database import engine
from app.models.models import Species
from app.data.expansion.research_review import CORRECTABLE, sanitize as _sanitize

OUT_DIR = Path(__file__).parent / "output"
REVIEW_FILE = OUT_DIR / "genus_review.json"

RESEARCHED_BY = "genus inference from approved siblings (unverified — needs human review)"

# Care fields that generalize across a genus. Deliberately excludes
# common_name / scientific_name / care_notes, which are species-specific.
INHERITABLE_NUMERIC = ["humidity_pct_min", "humidity_pct_max", "temp_f_min", "temp_f_max"]
INHERITABLE_CATEGORICAL = ["light_need", "soil_type"]
INHERITABLE = INHERITABLE_NUMERIC + INHERITABLE_CATEGORICAL + ["toxic_to_pets"]

# A note mentioning one of these words alongside "default" marks that field as
# machine-filled rather than sourced, so it is safe to replace.
_NOTE_FIELD_HINTS = {
    "soil": ["soil_type"],
    "humidity": ["humidity_pct_min", "humidity_pct_max"],
    "temp": ["temp_f_min", "temp_f_max"],
    "temperature": ["temp_f_min", "temp_f_max"],
    "light": ["light_need"],
}


def sanitize(review: dict) -> dict:
    """Same contract and downgrade rules as research_review, different stamp."""
    out = _sanitize(review)
    out["researched_by"] = RESEARCHED_BY
    return out


# --- pure helpers -----------------------------------------------------------

def genus_of(scientific_name: str | None) -> str:
    """First token of the binomial, normalized. '' when unusable."""
    parts = (scientific_name or "").strip().split()
    return parts[0].capitalize() if parts else ""


def _is_blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def defaulted_fields_from_note(note: str | None) -> set[str]:
    """Fields a review_note admits were machine-defaulted.

    The expansion mapper records these as e.g. 'no soil data — defaulted', so
    the note is a reliable signal that the value is a placeholder rather than
    sourced data."""
    low = (note or "").lower()
    if "default" not in low:
        return set()
    out: set[str] = set()
    for word, fields in _NOTE_FIELD_HINTS.items():
        if word in low:
            out.update(fields)
    return out


def fillable_fields(record: dict) -> set[str]:
    """Which inheritable fields may be written: blank ones, plus any the
    review_note admits were defaulted. Never a field holding real data."""
    blank = {f for f in INHERITABLE if _is_blank(record.get(f))}
    return blank | (defaulted_fields_from_note(record.get("review_note")) & set(INHERITABLE))


def genus_envelope(siblings: list[dict]) -> dict:
    """Care envelope typical of a genus, from its approved members.

    Median for numerics (robust to one odd sibling), mode for categoricals, and
    toxicity ONLY on a unanimous vote."""
    env: dict = {}
    if not siblings:
        return env

    for f in INHERITABLE_NUMERIC:
        vals = [s[f] for s in siblings if isinstance(s.get(f), (int, float))]
        if vals:
            env[f] = int(round(statistics.median(vals)))

    for f in INHERITABLE_CATEGORICAL:
        vals = [s[f] for s in siblings if not _is_blank(s.get(f))]
        if vals:
            env[f] = Counter(vals).most_common(1)[0][0]

    # Pet safety: a split genus does not determine toxicity, so require
    # unanimity. Guessing here could put an animal in front of a toxic plant.
    tox = [s["toxic_to_pets"] for s in siblings if isinstance(s.get("toxic_to_pets"), bool)]
    if tox and all(t == tox[0] for t in tox):
        env["toxic_to_pets"] = tox[0]

    return env


def derive_genus_fill(record: dict, siblings: list[dict]) -> dict:
    """Draft a verdict filling a record's defaulted care data from its genus.

    Pure: no DB, no network, no clock. `siblings` are approved species in the
    same genus (excluding this record)."""
    name = (record.get("scientific_name") or "").strip()
    genus = genus_of(name)

    if not genus:
        return sanitize({"verdict": "uncertain", "notes": f"no parsable genus in {name!r}."})
    if not siblings:
        return sanitize({
            "verdict": "uncertain",
            "notes": (
                f"no human-approved species in genus {genus} to infer from; "
                f"needs a horticultural source."
            ),
        })

    targets = fillable_fields(record)
    if not targets:
        return sanitize({
            "verdict": "uncertain",
            "notes": (
                f"care fields already hold values — nothing safe to infer. "
                f"Verification against a source is still outstanding."
            ),
        })

    envelope = genus_envelope(siblings)
    corrections = {f: v for f, v in envelope.items() if f in targets}
    if not corrections:
        return sanitize({
            "verdict": "uncertain",
            "notes": (
                f"{len(siblings)} approved sibling(s) in {genus}, but none carry "
                f"the fields this record is missing."
            ),
        })

    n = len(siblings)
    strength = "strong" if n >= 4 else "moderate" if n >= 2 else "weak"
    return sanitize({
        "verdict": "corrected",
        "citation_source": f"PlantAdvocate catalog — {n} approved {genus} species",
        # apply_review requires an http citation for a correction; point at the
        # genus query that produced this so a reviewer can reproduce it.
        "citation_url": f"https://plantadvocate.ai/catalog?genus={genus}&review_status=approved",
        "corrections": corrections,
        "notes": (
            f"Genus-inferred from {n} human-approved {genus} species "
            f"({strength} signal). Filled only fields that were missing or "
            f"machine-defaulted: {', '.join(sorted(corrections))}. "
            f"This is inference, not verification."
        ),
    })


# --- driver -----------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Genus-level care inference (offline)")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--all", action="store_true", help="process the whole backlog")
    ap.add_argument("--status", default="needs_review")
    ap.add_argument("--approved-status", default="approved",
                    help="which review_status counts as a trusted sibling")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = CORRECTABLE + ["review_status", "review_note"]

    with Session(engine) as session:
        pending = [
            {f: getattr(sp, f, None) for f in fields}
            for sp in session.exec(
                select(Species).where(Species.review_status == args.status)
            ).all()
        ]
        approved = [
            {f: getattr(sp, f, None) for f in fields}
            for sp in session.exec(
                select(Species).where(Species.review_status == args.approved_status)
            ).all()
        ]

    # Index trusted siblings by genus once — the whole point is that this runs
    # offline and fast over the entire backlog.
    by_genus: dict[str, list[dict]] = {}
    for sp in approved:
        by_genus.setdefault(genus_of(sp.get("scientific_name")), []).append(sp)

    targets = pending if args.all else pending[:max(0, args.limit)]
    print(f"  {args.status}: {len(pending)} pending, {len(approved)} approved siblings "
          f"across {len(by_genus)} genera")
    print(f"  inferring for {len(targets)} this run (offline — free)")

    entries = []
    for record in targets:
        genus = genus_of(record.get("scientific_name"))
        name = (record.get("scientific_name") or "").strip()
        siblings = [s for s in by_genus.get(genus, [])
                    if (s.get("scientific_name") or "").strip() != name]
        review = derive_genus_fill(record, siblings)
        entries.append({"record": record, "review": review})

    REVIEW_FILE.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")

    tally: dict[str, int] = {}
    filled = 0
    for e in entries:
        v = e["review"]["verdict"]
        tally[v] = tally.get(v, 0) + 1
        filled += len(e["review"]["corrections"])
    print(f"\n  wrote {REVIEW_FILE} ({len(entries)} entries)")
    print(f"  verdicts: {tally}")
    print(f"  {filled} field values proposed across {tally.get('corrected', 0)} records")
    print("\n  These are INFERRED, not verified — read them before applying.")
    print(f"  python -m app.data.expansion.apply_review {REVIEW_FILE}")
    print("  Nothing has been written to the catalog by this script.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
