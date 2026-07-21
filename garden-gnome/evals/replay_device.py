"""Re-grade transcribed on-device identify runs through the fuzzy mirror.

Input: a CSV transcribed from the printed checklist, columns:
    case_id, raw_text, shown_candidates, shown_tier
(`shown_candidates` pipe-separated best-first, empty when none were shown;
`shown_tier` one of confident|plausible|none — record the "search below"
fallback as none.)

    python -m evals.replay_device --input evals/output/device_run.csv

Reports, per case and in summary:
- tier agreement: does the mirror, fed the same raw text, land on the tier
  the device showed? (Gate I5 — disagreement means the port or the
  transcription drifted.)
- truth-in-shown / truth-in-mirror: with --manifest, whether an
  accept_species name appears among the shown / mirrored candidates.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from evals.catalog import load_names
from evals.checklist import MANIFEST_PATH, read_manifest
from evals.fuzzy_mirror import grade_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)

    catalog = load_names()
    accept_by_id = {
        r["id"]: [s for s in (r.get("accept_species") or "").split("|") if s]
        for r in read_manifest(args.manifest)
    }

    with args.input.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("no rows in input")
        return 1

    agree = truth_shown = truth_mirror = graded_truth = 0
    for row in rows:
        cid = row.get("case_id", "?")
        raw = row.get("raw_text") or ""
        shown = [s for s in (row.get("shown_candidates") or "").split("|") if s]
        shown_tier = (row.get("shown_tier") or "none").strip()

        mirror = grade_text(raw, catalog)
        tier_ok = mirror["tier"] == shown_tier
        agree += tier_ok

        accept = accept_by_id.get(cid, [])
        detail = f"{cid}: device={shown_tier} mirror={mirror['tier']}" + \
                 ("" if tier_ok else "  <-- DISAGREES")
        if accept:
            graded_truth += 1
            hit_shown = any(a in shown for a in accept)
            hit_mirror = any(a in mirror["candidates"] for a in accept)
            truth_shown += hit_shown
            truth_mirror += hit_mirror
            detail += f"  truth-in-shown={'y' if hit_shown else 'N'}" \
                      f" truth-in-mirror={'y' if hit_mirror else 'N'}"
        print(detail)

    n = len(rows)
    print()
    print(f"tier agreement: {agree}/{n} ({100 * agree / n:.0f}%)  [gate I5: >=90%]")
    if graded_truth:
        print(f"truth-in-shown ({graded_truth} in-catalog cases): "
              f"{truth_shown}/{graded_truth} ({100 * truth_shown / graded_truth:.0f}%)  [gate I2: >=50%]")
        print(f"truth-in-mirror: {truth_mirror}/{graded_truth}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
