"""What the fit fields still don't know, per batch and per species.

    python scripts/catalog/fit_gaps.py                # coverage summary by field
    python scripts/catalog/fit_gaps.py --batches      # worst batches first
    python scripts/catalog/fit_gaps.py --names b4     # species missing size in one batch
    python scripts/catalog/fit_gaps.py --names        # every species missing size

Run from garden-gnome/ with the project venv.

0019 added the fields a growing area is matched against. `is_houseplant` came
with the corpus -- researchers had been recording it since b1, it simply had
nowhere to go -- but mature size, edibility and pollinator value are new
questions nobody was asked, so they are empty until batches are re-researched
against the updated template.

The point of this script is that "unknown" stays visible. A fit engine that
reads a missing height as "fits anywhere" would put a forty-foot tree on a
windowsill, so the engine treats null as unknown and refuses to score it --
which means coverage here is the ceiling on how much the feature can actually
say. Counting it is how the campaign knows what is left.

A field counts as covered only when a citation supports it (the same pairing
`app.data.claims.tranche` applies at load). A value nobody cited never becomes
a claim and never reaches a column, so counting the raw key would overstate
what the app knows.
"""
import argparse
import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.data.claims.tranche import claims_from_record  # noqa: E402

VERIFIED = Path(__file__).resolve().parents[2] / "app" / "data" / "verified"

SIZE_FIELDS = ("mature_height_in_min", "mature_height_in_max",
               "mature_spread_in_min", "mature_spread_in_max")
FIT_FIELDS = ("is_houseplant", "is_edible", "attracts_pollinators") + SIZE_FIELDS


def records():
    for path in sorted(glob.glob(str(VERIFIED / "b*.json"))):
        batch = Path(path).name
        for record in json.loads(Path(path).read_text())["records"]:
            yield batch, record


def cited_fields(record) -> set[str]:
    """The fields that would actually become claims, not merely the keys set."""
    return {c.field for c in claims_from_record(record)[0]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batches", action="store_true",
                    help="per-batch size coverage, worst first")
    ap.add_argument("--names", nargs="?", const="", metavar="BATCH",
                    help="species with no cited mature height, optionally in one batch")
    args = ap.parse_args()

    total = 0
    covered = Counter()
    by_batch = defaultdict(lambda: [0, 0])   # batch -> [with size, total]
    missing_size = []

    for batch, record in records():
        total += 1
        cited = cited_fields(record)
        for field in FIT_FIELDS:
            if field in cited:
                covered[field] += 1
        has_size = any(f in cited for f in SIZE_FIELDS)
        by_batch[batch][1] += 1
        if has_size:
            by_batch[batch][0] += 1
        else:
            missing_size.append((batch, record.get("common_name") or "?",
                                 record.get("scientific_name_accepted")
                                 or record.get("scientific_name_given") or "?"))

    if args.names is not None:
        rows = [r for r in missing_size
                if not args.names or r[0].startswith(args.names)]
        for batch, common, latin in rows:
            print(f"{batch:38} {common:34} {latin}")
        print(f"\n{len(rows)} species with no cited mature size")
        return 0

    if args.batches:
        ranked = sorted(by_batch.items(), key=lambda kv: (kv[1][0] / kv[1][1], kv[0]))
        for batch, (have, n) in ranked:
            print(f"{batch:38} {have:3}/{n:3}  {have / n:5.0%}")
        return 0

    print(f"{total} records in the verified tranche\n")
    for field in FIT_FIELDS:
        n = covered[field]
        print(f"  {field:24} {n:4}/{total}  {n / total:5.0%}")
    with_size = sum(v[0] for v in by_batch.values())
    print(f"\n  {'any mature size':24} {with_size:4}/{total}  {with_size / total:5.0%}")
    print("\nRe-research fills these: scripts/catalog/pipeline/template-research.js\n"
          "carries the four size fields, is_edible and attracts_pollinators.\n"
          "`--batches` ranks where to start; `--names` lists the species.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
