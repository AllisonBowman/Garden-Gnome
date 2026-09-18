"""Per-batch landing review for a raw Workflow result, before it is copied into
app/data/verified/.

    python scripts/catalog/land_check.py bNN_records.json

Run from garden-gnome/ with the project venv. Exit 1 on any problem.

Corpus-wide *invariants* (enum tokens, stray keys, string-"null", null
common_name, citation pointers, duplicate species) now live permanently in
garden-gnome/tests/test_tranche_invariants.py and run over every batch. This
script holds only the batch *conventions* the loader does not depend on, plus
the review dumps I otherwise retype by hand:

  1. name_note non-null  =>  at least one citation labelled name_note
  2. every non-null claim field traces to a citation (the loader's own rule,
     via claims_from_record, so COMPANIONS/STEMS aliases count)
  3. exact-match dedup of every binomial against the landed corpus
  4. dump of every FLAGGED / "removed on audit" entry, for manual review
  5. dump of every toxic_to_pets citation + quote, to eyeball cat/dog scoping
"""
import json
import sys
from pathlib import Path

# garden-gnome/ for `app`, and this directory for `covered`, from any cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.data.claims.tranche import claims_from_record  # noqa: E402
from covered import covered, key  # noqa: E402

path = Path(sys.argv[1])
data = json.loads(path.read_text())
records = data["records"]
cov = covered()
problems: list[str] = []

print(f"batch {data.get('batch')}: {len(records)} records\n")
if not records:
    # An all-failed workflow (session limit, API outage) returns records: []
    # with no error of its own. That is not a batch; refuse it loudly.
    print("=== problems ===\nno records at all -- every agent failed; do not land, retry the workflow")
    sys.exit(1)
for r in records:
    name = r.get("common_name") or r.get("scientific_name_given")
    print(f"- {name} | {r.get('scientific_name_given')} -> {r.get('scientific_name_accepted')}"
          f" | toxic_to_pets={r.get('toxic_to_pets')}")

    if r.get("name_note") and not any("name_note" in c["claim"] for c in r["citations"]):
        problems.append(f"{name}: name_note set but no citation labelled name_note")

    claims, unsupported = claims_from_record(r)
    if unsupported:
        problems.append(f"{name}: loader finds no citation for {unsupported}")

    for field in ("scientific_name_given", "scientific_name_accepted"):
        if r.get(field):
            # exclude this batch's own landed file, so a re-check of an
            # already-landed batch does not flag every species against itself
            own = f"{data.get('batch')}.json"
            hits = [h for h in cov.get(key(r[field]), []) if h[0] != own]
            if hits:
                problems.append(f"{name}: {field} {r[field]!r} already covered in {sorted(set(hits))}")

print("\n=== FLAGGED / removed on audit ===")
for r in records:
    name = r.get("common_name") or r.get("scientific_name_given")
    for u in r.get("unknowns", []):
        if "FLAGGED on audit" in u or "removed on audit" in u:
            print(f"\n[{name}] {u[:1800]}")

print("\n=== toxic_to_pets citations (check cats/dogs are named) ===")
for r in records:
    if r.get("toxic_to_pets") is None:
        continue
    name = r.get("common_name") or r.get("scientific_name_given")
    print(f"\n[{name}] toxic_to_pets={r['toxic_to_pets']}")
    for c in r["citations"]:
        if "toxic_to_pets" in c["claim"]:
            print(f"   {c['claim'][:110]}\n      quote: {c['quote'][:200]!r}")

print("\n=== problems ===")
print("\n".join(problems) if problems else "none")
sys.exit(1 if problems else 0)
