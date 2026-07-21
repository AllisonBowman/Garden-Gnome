"""Manifest linting + the printable on-device test checklist.

    python -m evals.checklist --validate [--require-files]
    python -m evals.checklist --print

--validate exits non-zero on structural problems (bad case_type, unknown
species, duplicate ids, missing license on sourced photos). Missing photo
files are warnings until --require-files, so the manifest can be linted
before the photo set exists (Phase 0 of the test plan).
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from evals.catalog import common_names

EVALS_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = EVALS_DIR / "manifest.csv"

CASE_TYPES = {"in_catalog", "out_of_catalog", "junk", "blurry", "non_plant"}
COLUMNS = [
    "id", "file", "case_type", "accept_species", "species_freetext",
    "device_set", "source", "license", "source_url", "notes",
]


def read_manifest(path: Path = MANIFEST_PATH) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate(rows: list[dict], require_files: bool = False) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []
    known = common_names()
    seen_ids: set[str] = set()

    if rows and sorted(rows[0].keys()) != sorted(COLUMNS):
        errors.append(f"header mismatch: expected {COLUMNS}")

    for row in rows:
        rid = row.get("id", "?")
        if rid in seen_ids:
            errors.append(f"{rid}: duplicate id")
        seen_ids.add(rid)

        if row.get("case_type") not in CASE_TYPES:
            errors.append(f"{rid}: bad case_type {row.get('case_type')!r}")

        accept = [s for s in (row.get("accept_species") or "").split("|") if s]
        if row.get("case_type") == "in_catalog" and not accept:
            errors.append(f"{rid}: in_catalog rows need accept_species")
        if row.get("case_type") in {"out_of_catalog", "junk", "non_plant"} and accept:
            errors.append(f"{rid}: {row['case_type']} rows must leave accept_species empty")
        for name in accept:
            if name not in known:
                errors.append(f"{rid}: accept_species {name!r} not in the catalog")

        if row.get("device_set") not in {"yes", "no"}:
            errors.append(f"{rid}: device_set must be yes/no")

        if row.get("source") and row["source"] != "allison" and not row.get("license"):
            errors.append(f"{rid}: sourced photos need a license")

        photo = EVALS_DIR / (row.get("file") or "")
        if not photo.is_file():
            msg = f"{rid}: photo not found: {row.get('file')}"
            (errors if require_files else warnings).append(msg)

    return errors, warnings


def print_checklist(rows: list[dict]) -> None:
    device = [r for r in rows if r.get("device_set") == "yes"]
    print("# On-device identify checklist")
    print()
    print("Per photo: Add Plant -> Identify from a photo -> record what the app")
    print("shows, then CANCEL without saving. Raw text appears under the chips")
    print("in dev/preview builds only.")
    print()
    for row in device:
        accept = row.get("accept_species") or ""
        expected = accept if accept else "none — expect the manual-search fallback"
        print(f"## {row['id']}  ({Path(row['file']).name})")
        print(f"- case: {row['case_type']}   expected: {expected}")
        print("- candidates shown (best first): ____________________")
        print("- tier/message: [ ] confident  [ ] plausible  [ ] search-below")
        print("- raw model text: ____________________")
        print("- notes: ____________________")
        print()
    print(f"({len(device)} photos in the device set)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--require-files", action="store_true")
    parser.add_argument("--print", dest="print_", action="store_true")
    args = parser.parse_args(argv)

    rows = read_manifest(args.manifest)
    if args.validate:
        errors, warnings = validate(rows, require_files=args.require_files)
        for w in warnings:
            print(f"warning: {w}")
        for e in errors:
            print(f"ERROR: {e}")
        print(f"{len(rows)} rows — {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1 if errors else 0
    if args.print_:
        print_checklist(rows)
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
