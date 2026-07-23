"""Offline self-test of the eval tooling — no photos, no network, no DB.

    python -m evals.selftest

Follows the app/data/expansion/selftest.py pattern: assert + counter, exit
0 with a final tally on success.
"""
from __future__ import annotations

import io
import csv

from evals import fuzzy_mirror as fm
from evals.catalog import load_names
from evals.checklist import MANIFEST_PATH, read_manifest, validate

passed = 0


def check(cond: bool, msg: str) -> None:
    global passed
    assert cond, f"FAILED: {msg}"
    passed += 1
    print(f"ok: {msg}")


def main() -> int:
    print("mirror primitives --")
    check(fm.normalize("  Peace-Lily's leaf! ") == "peace lilys leaf", "normalize strips and collapses")
    check(fm.dice_coefficient("monstera", "monstera") == 1.0, "dice: identity is 1")
    check(fm.dice_coefficient("a", "ab") == 0.0, "dice: sub-bigram strings score 0")
    check(0 < fm.dice_coefficient("monstera", "monstero") < 1, "dice: near-miss in (0,1)")
    check(fm.score_name("this is a peace lily", "Peace Lily") == 0.97, "binomial containment scores 0.97")
    check(fm.score_name("pothos!", "Pothos") == 1.0, "exact-after-normalize scores 1")

    print("parity fixtures --")
    for ai_text, want_tier, want_top in fm.PARITY_FIXTURES:
        got = fm.grade_text(ai_text, fm.FIXTURE_CATALOG)
        top = got["candidates"][0] if got["candidates"] else None
        check(got["tier"] == want_tier and top == want_top,
              f"fixture {ai_text!r} -> {want_tier}/{want_top}")

    print("real catalog --")
    names = load_names()
    check(len(names) == 129, "129 catalog species load")
    check(len({n['id'] for n in names}) == len(names), "catalog ids unique")
    check(all(n["common_name"] and n["scientific_name"] for n in names),
          "every entry has common + scientific names")
    exact_top = sum(
        1 for n in names
        if (g := fm.grade_text(n["common_name"], names))["tier"] == "confident"
        and g["candidates"][0] == n["common_name"]
    )
    check(exact_top == len(names), f"exact common name -> confident self-top ({exact_top}/{len(names)})")

    print("manifest --")
    rows = read_manifest(MANIFEST_PATH)
    errors, warnings = validate(rows)
    check(not errors, f"example manifest has no structural errors ({len(warnings)} photo warnings ok)")

    bad = io.StringIO()
    writer = csv.DictWriter(bad, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerow({**rows[0], "id": "pX", "case_type": "not-a-type", "accept_species": "Not A Species"})
    bad.seek(0)
    bad_rows = list(csv.DictReader(bad))
    bad_errors, _ = validate(bad_rows)
    check(len(bad_errors) >= 2, "broken row is rejected (bad case_type + unknown species)")

    print(f"ALL {passed} EVAL SELF-TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
