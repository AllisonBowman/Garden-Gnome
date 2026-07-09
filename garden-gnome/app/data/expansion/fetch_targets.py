"""Build the nursery-common target species list.

With a Perenual Premium key, pulls the indoor-plant listing (the closest
proxy for "nursery-common houseplants") page by page and writes a TSV target
file consumed by run_expansion.py:

    perenual_id<TAB>common_name<TAB>scientific_name

Usage (from garden-gnome/):
  python -m app.data.expansion.fetch_targets --from-perenual --count 1900
  python -m app.data.expansion.fetch_targets --from-file my_list.txt   # normalize a custom list
"""
import argparse
from pathlib import Path

from app.data.expansion.perenual import PerenualClient

DEFAULT_OUT = Path(__file__).parent / "target_species.txt"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from-perenual", action="store_true")
    ap.add_argument("--from-file", default=None, help="copy/normalize an existing name list")
    ap.add_argument("--count", type=int, default=1900)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--mock-dir", default=None)
    args = ap.parse_args()

    out = Path(args.out)
    lines: list[str] = ["# target species list — one per line, or TSV: id<TAB>common<TAB>scientific"]

    if args.from_file:
        for raw in Path(args.from_file).read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if raw and not raw.startswith("#"):
                lines.append(raw)
    elif args.from_perenual:
        client = PerenualClient(mock_dir=args.mock_dir)
        seen_ids: set[int] = set()

        def harvest(label: str, **filters) -> int:
            """Paginate one filtered listing, appending unseen species."""
            page, added = 1, 0
            while len(seen_ids) < args.count:
                data = client.list_filtered(page, **filters)
                rows = data.get("data", [])
                if not rows:
                    break
                for row in rows:
                    if row["id"] in seen_ids:
                        continue
                    sci = row.get("scientific_name")
                    sci = sci[0] if isinstance(sci, list) and sci else (sci or "")
                    lines.append(f"{row['id']}\t{row.get('common_name', '')}\t{sci}")
                    seen_ids.add(row["id"])
                    added += 1
                    if len(seen_ids) >= args.count:
                        break
                if page >= int(data.get("last_page", page)):
                    break
                page += 1
            print(f"  {label}: +{added} species (total {len(seen_ids)})")
            return added

        # All true indoor/houseplants first, then tropicals/subtropicals
        # (USDA zones 13 -> 10, most tropical first) until the target count.
        harvest("indoor", indoor=1)
        for zone in (13, 12, 11, 10):
            if len(seen_ids) >= args.count:
                break
            harvest(f"hardiness zone {zone}", hardiness=zone)
        print(f"Fetched {len(seen_ids)} species from Perenual")
    else:
        ap.error("pass --from-perenual or --from-file")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines) - 1} targets to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
