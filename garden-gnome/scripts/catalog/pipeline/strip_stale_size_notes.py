"""strip_stale_size_notes.py RESULT.json [--apply] -- drop unknowns lines a landed size has made false.

Run from garden-gnome/ with the project venv, AFTER merge_backfill.py --apply. Until 0020_climbs a climber took no
size by rule, and a houseplant with only an outdoor stature took none either; each such record carries an unknowns
line saying its size was deliberately left null. Once a later round lands a size on that record, the line is no
longer true, and a disclosure that contradicts the value beside it is worse than none. merge_backfill only ever
appends, so this is the one step that removes text -- which is why it is narrow: it touches only species named in
RESULT.json, only records that now hold a size, and only lines that both name a size field (or "size") and say it
was left null / withheld. Every removed line is printed. Plan only without --apply.
"""
import json
import re
import sys
from pathlib import Path

VERIFIED = Path(__file__).resolve().parents[3] / "app" / "data" / "verified"
SIZE = ("mature_height_in_min", "mature_height_in_max", "mature_spread_in_min", "mature_spread_in_max")
NAMES_SIZE = re.compile(r"mature_(height|spread)_in|\bsize\b|\bsize fields\b", re.I)
# Says the record's OWN size fields were left empty. Deliberately not "no size": a line saying a PAGE carried no
# size ("the Clemson sheet carries no size") is still true after a size lands from another page, and the first
# version of this script would have deleted two such disclosures.
SAYS_NULL = re.compile(r"\b(left|kept|set|are|is|were|was|stay|stays)\s+(deliberately\s+)?null\b"
                       r"|\bnot carried on this record\b|\bwithheld\b|\bsuppress", re.I)


def main() -> int:
    payload = json.loads(Path(sys.argv[1]).read_text())
    apply = "--apply" in sys.argv
    by_batch: dict[str, dict] = {}
    removed = 0
    for entry in payload["landed"]:
        name = entry["record"]["common_name"]
        data = by_batch.setdefault(entry["batch"], json.loads((VERIFIED / entry["batch"]).read_text()))
        rec = next((r for r in data["records"] if r.get("common_name") == name), None)
        if rec is None or not any(rec.get(f) is not None for f in SIZE):
            continue
        new_lines = set(entry["record"].get("unknowns", []))
        keep = []
        for line in rec.get("unknowns", []):
            stale = (line not in new_lines and NAMES_SIZE.search(line) and SAYS_NULL.search(line)
                     and "removed on audit" not in line)
            if stale:
                removed += 1
                print(f"- {name} [{entry['batch']}]: {line[:200]}")
            else:
                keep.append(line)
        rec["unknowns"] = keep
    if apply and removed:
        for batch, data in by_batch.items():
            (VERIFIED / batch).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"\n{removed} stale line(s) " + ("removed" if apply else "would be removed (plan only -- pass --apply)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
