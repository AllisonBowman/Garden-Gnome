# Catalog research pipeline

The orchestration layer around `../covered.py`, `../land_check.py` and `../verify_quotes.py`: how a batch of species
goes from a candidate list to a landed `app/data/verified/bNN-*.json`. Run everything from `garden-gnome/` with
`.venv/bin/python`. Generated files stay in this directory and are gitignored.

1. **Pick species.** `gap-finders.js` is the Workflow that chose b81-b88 (six category lenses, covered.py dedup, NC State
   page check); its output is `batches-b81-b88.json`. Hybrids (×) are dropped because the landing pass needs a bare binomial.
2. **Generate batch scripts.** `gen_batch.py scripts/catalog/pipeline/batches-b81-b88.json` writes `bNN-catalog-research.js`
   from `template-research.js` (Sonnet research, Opus adversarial audit, null-verdict guard, summary-first return).
3. **Run** each script with the Workflow tool (`scriptPath` = its absolute path). Two or three batches at a time: eight at
   once exhausted a session limit within minutes on 2026-09-10.
4. **Recover a stalled run.** `harvest.py <run dir> [...]` pulls finished research and audits out of the runs' journals into
   `cache.json`; `make_resume.py bNN` writes `bNN-resume.js`, which replays cached agents and runs only the missing ones.
5. **Extract.** `extract_batch.py bNN <task output file>` writes `bNN_records.json`.
6. **Land.** Hand the batch to an Opus agent with `LANDING_BRIEF.md` (repairs in `bNN_repair.py` via `repair_lib.py`;
   `example_repair_b74.py` is the shape; `qc.py URL regex` ground-truths any substitute quote).
7. **Verify and commit.** `verify_and_commit.py bNN app/data/verified/bNN-<slug>.json "Land bNN: <theme>"` runs the loader
   count, land_check, verify_quotes and the tranche invariants, and commits only if all pass (`commit_batch.py` bumps the
   count test and the docs header from that file's own loader count).
