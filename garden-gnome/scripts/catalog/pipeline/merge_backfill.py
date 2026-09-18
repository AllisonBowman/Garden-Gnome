"""Merge a backfilled field set into records that are already landed.

    python scripts/catalog/pipeline/merge_backfill.py <workflow-result.json> [--apply]

Run from garden-gnome/ with the project venv. Prints a plan; writes only with
--apply. Exit 1 on any refusal.

A normal batch lands a new species. This lands new FIELDS onto species that
are already in the corpus -- what happens when the schema grows and 600
records have never been asked the new question. It is deliberately a separate
script from the batch pipeline, and deliberately paranoid, because the failure
mode is different: a batch landing that goes wrong produces an obviously bad
new record, while a merge that goes wrong quietly corrupts a record that was
already correct.

So the merge only ever ADDS. It refuses to overwrite a field that already
holds a value, refuses a field outside the backfill set, refuses a species it
cannot find, and refuses any value the loader would not be able to pair to a
citation -- which is the same gate `claims_from_record` applies at load, run
here so a defect is caught before it reaches a file rather than after.

Input is the workflow's own result: {"landed": [{batch, record, applied, ...}]}.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.data.claims.tranche import claims_from_record  # noqa: E402

VERIFIED = Path(__file__).resolve().parents[3] / "app" / "data" / "verified"

#: The only fields a backfill may write. Anything else in a proposed record is
#: a researcher who wandered outside the brief, and is refused rather than
#: filtered -- a record that contains a field it was told not to touch is not
#: a record to trust the rest of.
BACKFILL_FIELDS = (
    "is_edible", "attracts_pollinators",
    "mature_height_in_min", "mature_height_in_max",
    "mature_spread_in_min", "mature_spread_in_max",
)
IDENTITY = ("common_name", "scientific_name_accepted")
ALLOWED = set(BACKFILL_FIELDS) | set(IDENTITY) | {"unknowns", "citations"}


def _find(records, common_name):
    hits = [r for r in records if r.get("common_name") == common_name]
    if len(hits) != 1:
        return None, f"{len(hits)} records named {common_name!r} in the batch"
    return hits[0], None


def plan(payload: dict):
    problems: list[str] = []
    changes: list[tuple] = []
    by_batch: dict[str, dict] = {}

    for entry in payload["landed"]:
        batch_file = entry["batch"]
        proposed = entry["record"]
        name = proposed.get("common_name", "?")

        stray = set(proposed) - ALLOWED
        if stray:
            problems.append(f"{name}: proposed record carries fields outside the "
                            f"backfill set: {sorted(stray)}")
            continue

        path = VERIFIED / batch_file
        if not path.exists():
            problems.append(f"{name}: no such batch file {batch_file}")
            continue
        data = by_batch.setdefault(batch_file, json.loads(path.read_text()))

        existing, err = _find(data["records"], name)
        if err:
            problems.append(f"{name}: {err}")
            continue

        accepted = existing.get("scientific_name_accepted") or existing.get("scientific_name_given")
        if proposed.get("scientific_name_accepted") != accepted:
            problems.append(
                f"{name}: proposed accepted name {proposed.get('scientific_name_accepted')!r} "
                f"is not the landed {accepted!r} -- this is a merge, not a rename")
            continue

        wrote = []
        for field in BACKFILL_FIELDS:
            value = proposed.get(field)
            if value is None:
                continue
            if existing.get(field) is not None:
                problems.append(
                    f"{name}: {field} already holds {existing[field]!r}; a backfill "
                    "never overwrites a landed value")
                continue
            wrote.append((field, value))

        if not wrote:
            changes.append((batch_file, name, [], 0, "nothing survived the audit"))
            continue

        # Simulate the merge and ask the loader whether every new value would
        # actually pair to a citation. A value the loader cannot pair never
        # becomes a claim, never reaches a column, and is dead weight in the
        # file -- better refused here than discovered as a silent gap later.
        trial = dict(existing)
        for field, value in wrote:
            trial[field] = value
        trial["citations"] = list(existing.get("citations", [])) + list(proposed.get("citations", []))
        _, unsupported = claims_from_record(trial)
        orphans = [f for f, _ in wrote if f in unsupported]
        if orphans:
            problems.append(
                f"{name}: no citation the loader accepts supports {orphans} -- "
                "check the claim text names the field (or its stem) and the "
                "domain is a registered authority")
            continue

        changes.append((batch_file, name, wrote, len(proposed.get("citations", [])),
                        entry.get("summary", "")))
    return changes, problems, by_batch


def apply(payload: dict, by_batch: dict) -> list[str]:
    touched = []
    for entry in payload["landed"]:
        data = by_batch.get(entry["batch"])
        if data is None:
            continue
        proposed = entry["record"]
        existing, err = _find(data["records"], proposed["common_name"])
        if err:
            continue
        wrote_any = False
        for field in BACKFILL_FIELDS:
            value = proposed.get(field)
            if value is not None and existing.get(field) is None:
                existing[field] = value
                wrote_any = True
        if not wrote_any:
            continue
        existing.setdefault("citations", []).extend(proposed.get("citations", []))
        # The researcher's disclosures travel with the values they explain.
        new_unknowns = [u for u in proposed.get("unknowns", []) if u]
        if new_unknowns:
            existing.setdefault("unknowns", []).extend(new_unknowns)
        touched.append(entry["batch"])

    for batch_file in sorted(set(touched)):
        data = by_batch[batch_file]
        data.setdefault("normalizations", [])
        data["normalizations"].append(
            "size backfill: mature_height_in_*, mature_spread_in_*, is_edible and "
            "attracts_pollinators added to already-landed records, researched "
            "against the pages this batch was already cited to and audited "
            "before landing. No pre-existing field was read or changed.")
        # Match the corpus's own formatting exactly -- indent 2, real
        # characters not \u escapes, one trailing newline. A backfill that
        # reflows the file buries five changed values in a seven-thousand-line
        # diff, and a diff nobody can read is a diff nobody checks.
        (VERIFIED / batch_file).write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return sorted(set(touched))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    payload = json.loads(Path(sys.argv[1]).read_text())
    changes, problems, by_batch = plan(payload)

    for batch_file, name, wrote, n_cites, summary in changes:
        head = f"{name}  [{batch_file}]"
        if not wrote:
            print(f"- {head}: nothing to write ({summary})")
            continue
        print(f"- {head}: {len(wrote)} field(s), {n_cites} citation(s)")
        for field, value in wrote:
            print(f"      {field} = {value}")

    print("\n=== problems ===")
    print("\n".join(problems) if problems else "none")
    if problems:
        return 1

    if "--apply" in sys.argv:
        touched = apply(payload, by_batch)
        print("\nwrote: " + (", ".join(touched) if touched else "nothing"))
    else:
        print("\n(plan only -- pass --apply to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
