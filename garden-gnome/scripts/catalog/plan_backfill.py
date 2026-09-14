"""Split the species still missing mature size into evenly-sized waves.

    python scripts/catalog/plan_backfill.py                  # summarise the waves
    python scripts/catalog/plan_backfill.py --write          # write wave files
    python scripts/catalog/plan_backfill.py --waves 3 --batch 8

Run from garden-gnome/ with the project venv.

The pilot proved the backfill works and told us what it costs: roughly 190k
subagent tokens per species, so the ~594 species still without a mature size
are on the order of 110M tokens. That is not a thing to run in one sitting,
and it is not a thing to run in an order chosen by filename either.

ORDER IS THE POINT. Wave 1 is the woody plants -- trees, shrubs, conifers,
climbers. They are first because they are where a missing size does actual
damage: the fit engine recommended American Beech for a 32 sq ft raised bed,
and it did that because a 60-80 ft tree and a 2 ft perennial were equally
unknown to it. Every wrong recommendation of this kind comes from a plant
that gets big, so the plants that get big go first. Wave 2 is the rest of the
outdoor catalog, where size decides crowding rather than absurdity. Wave 3 is
the houseplants, last on purpose: indoor light is the axis an indoor area
actually turns on, and the catalog cannot answer it (3% footcandle coverage),
so size buys the least there.

Each wave is emitted as batches of eight, in the shape the backfill workflow
takes as `args` -- common name, accepted binomial, batch file, and the pages
that record is ALREADY cited to. Handing the researcher the record's own
sources is what keeps a backfilled value anchored to the same authorities as
the rest of the row, and it is also what stopped the pilot inventing URLs.
"""
import argparse
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.data.claims.tranche import claims_from_record  # noqa: E402

VERIFIED = Path(__file__).resolve().parents[2] / "app" / "data" / "verified"
OUT = Path(__file__).resolve().parent / "pipeline"

SIZE_FIELDS = ("mature_height_in_min", "mature_height_in_max",
               "mature_spread_in_min", "mature_spread_in_max")

#: Batch-name fragments that mark a woody batch. Crude on purpose -- it only
#: has to get the ordering roughly right, and `is_houseplant` does the real
#: work of separating indoor from out.
WOODY = ("tree", "shrub", "conifer", "vine", "climber", "beech", "poplar",
         "hedge", "rose", "azalea", "rhododendron", "bamboo", "palm")


def has_size(record) -> bool:
    cited = {c.field for c in claims_from_record(record)[0]}
    return any(f in cited for f in SIZE_FIELDS)


def wave_of(batch_name: str, record) -> int:
    """1 woody outdoor, 2 other outdoor, 3 indoor. See the module docstring."""
    if record.get("is_houseplant") is True:
        return 3
    if any(w in batch_name.lower() for w in WOODY):
        return 1
    return 2


def collect():
    rows = []
    for path in sorted(glob.glob(str(VERIFIED / "b*.json"))):
        batch = Path(path).name
        for r in json.loads(Path(path).read_text())["records"]:
            if has_size(r):
                continue
            urls = []
            for c in r.get("citations", []):
                if c["url"] not in urls:
                    urls.append(c["url"])
            rows.append({
                "common": r.get("common_name"),
                "latin": r.get("scientific_name_accepted") or r.get("scientific_name_given"),
                "batch": batch,
                "urls": urls,
                "is_houseplant": r.get("is_houseplant"),
                "_wave": wave_of(batch, r),
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--waves", type=int, default=3)
    ap.add_argument("--batch", type=int, default=8, help="species per workflow run")
    ap.add_argument("--write", action="store_true", help="write the wave files")
    args = ap.parse_args()

    rows = collect()
    # Sort by the priority band, then by batch so one workflow run touches as
    # few files as possible -- a merge that rewrites one file is easier to
    # review than one that rewrites eight.
    rows.sort(key=lambda r: (r["_wave"], r["batch"], r["common"] or ""))

    per = -(-len(rows) // args.waves)   # ceiling, so the last wave is the short one
    waves = [rows[i * per:(i + 1) * per] for i in range(args.waves)]

    print(f"{len(rows)} species still have no cited mature size\n")
    band = {1: "woody outdoor", 2: "other outdoor", 3: "indoor"}
    for n, wave in enumerate(waves, 1):
        if not wave:
            continue
        mix = {}
        for r in wave:
            mix[band[r["_wave"]]] = mix.get(band[r["_wave"]], 0) + 1
        runs = -(-len(wave) // args.batch)
        cost = len(wave) * 190_000
        print(f"wave {n}: {len(wave):3} species | {runs:2} runs of {args.batch} "
              f"| ~{cost/1_000_000:.0f}M tokens | " +
              ", ".join(f"{v} {k}" for k, v in mix.items()))

    total = len(rows) * 190_000
    print(f"\ntotal ~{total/1_000_000:.0f}M subagent tokens at the pilot's "
          f"~190k/species. The pilot's own three runs are the basis; a clean\n"
          f"single run was 1.5M for 8 species.")

    if args.write:
        OUT.mkdir(exist_ok=True)
        for n, wave in enumerate(waves, 1):
            if not wave:
                continue
            for r in wave:
                r.pop("_wave", None)
            batches = [wave[i:i + args.batch] for i in range(0, len(wave), args.batch)]
            path = OUT / f"size-wave{n}.json"
            path.write_text(json.dumps(batches, indent=1) + "\n")
            print(f"wrote {path.relative_to(Path.cwd())}: "
                  f"{len(batches)} runs of up to {args.batch}")
    else:
        print("\n(summary only -- pass --write to emit the wave files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
