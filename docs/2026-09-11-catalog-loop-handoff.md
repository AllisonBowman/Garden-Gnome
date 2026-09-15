# Catalog loop handoff: paused 2026-09-11 for the weekly usage limit

The research loop was wound down on purpose, close to the end of the weekly usage. No agent was left running:
every workflow had already ended, and everything landable was landed and committed first.

## Where things stand

- **Branch** `claude/database-build-goals-e548af` (worktree `.claude/worktrees/database-build-goals-e548af`), local
  only: not pushed, not merged. It is `care-advice-honesty` at a4a330d (b73) plus this session's work, so it
  fast-forwards that branch cleanly.
- **Catalog:** 80 batches, 2,989 claims, 576 species, 8 authorities. The full backend gate passed at b79
  (3,893 tests); b80 passed the tranche invariants, land_check and verify_quotes when it landed.
- **Landed this session, in order:** Phase 4.1 closed by decision (3bb4501); harm-capable fields never inherit, ADR
  0007 (7d36a9b); `hardiness_zones` renamed `outdoor_temp_min_f`, ADR 0006 (9d1148d); wiring-review leftovers
  (11e6cbb); the toxic_to_pets verdict pass over 43 records (8fdb85f, 79183a7); then b74 (1ea1f72), b75 (d1a8911),
  b76 (12157c0), b77 (284bea3), b78 (566fac3), b79 (7090e6e), b80 (5b9b745).

## Not landed: b81–b88, 61 species

All eight batches were launched together and all eight hit "You've hit your session limit" within about 13 minutes,
mostly in the audit stage. Nothing from them is in `app/data/verified/`. The finished work is kept in the
workflow journals and does not need re-running:

| batch | theme | researched | audited |
|---|---|---|---|
| b81 | houseplants | 7 of 8 | 0 |
| b82 | perennials | 5 of 8 | 1 (Lamb's Ear) |
| b83 | annuals and bedding | 6 of 8 | 0 |
| b84 | vegetables, herbs, fruit | 6 of 8 | 0 |
| b85 | landscape shrubs | 6 of 8 | 0 |
| b86 | bulbs and patio plants | 6 of 8 | 0 |
| b87 | mixed | 5 of 8 | 0 |
| b88 | mixed | 2 of 5 | 1 (Lima Bean) |

The run directories are under
`~/.claude/projects/-Users-allisonbowman-Developer-Garden-Gnome--claude-worktrees-database-build-goals-e548af/e53f91e1-ddb2-4d9f-8694-1b687525a69c/subagents/workflows/`:
b81 `wf_ca134ed8-9d9`, b82 `wf_bb639845-c76`, b83 `wf_21581941-2cc`, b84 `wf_5eb07f96-2ed`, b85 `wf_08d16a28-565`,
b86 `wf_8707c72d-a2d`, b87 `wf_ba4fb22e-a7c`, b88 `wf_3e9acfd1-d31`.

## How to resume

The tooling now lives in `garden-gnome/scripts/catalog/pipeline/` (README there). From `garden-gnome/`:

```bash
.venv/bin/python scripts/catalog/pipeline/gen_batch.py scripts/catalog/pipeline/batches-b81-b88.json
.venv/bin/python scripts/catalog/pipeline/harvest.py <each run directory above>
.venv/bin/python scripts/catalog/pipeline/make_resume.py b81   # repeat for b82..b88
```

In this worktree `cache.json` and the eight `bNN-resume.js` scripts are already generated (gitignored), so those
three steps are only needed in a fresh checkout. Then run each `bNN-resume.js` with the Workflow tool, **two or three
at a time**. Each replays its cached agents and runs only the missing ones: 18 research agents and 59 audits in all.
Land each finished batch with an Opus agent following `LANDING_BRIEF.md`, then commit it with
`verify_and_commit.py`.

## Decisions for Allison

- **American Beachgrass (b80).** Ammophila breviligulata landed under its North American name rather than RHS's
  dedicated-page lead, American marram. That breaks the catalog's dedicated-page-lead rule, because the North American
  name rests on two multi-species lists (Clemson, UMD); the record's name_note says so. Say if the strict rule should win.
- **Nine hybrids dropped** from the b81 candidates because landing needs a bare binomial: Chrysanthemum × morifolium,
  Nepeta × faassenii, Calibrachoa × hybrida, Verbena × hybrida, Fuchsia × hybrida, Citrus × aurantiifolia,
  Spiraea × vanhouttei, Canna × generalis, Crocosmia × crocosmiiflora. Several are among the most common garden plants;
  accepting × names in the landing pass is a small change worth making.
- **Sparganium americanum withheld** from b77: no admissible source has a dedicated page for it.
- **Merge and push.** `care-advice-honesty` is checked out in the main checkout with uncommitted icon changes. Once that
  checkout is clean, `git merge --ff-only claude/database-build-goals-e548af` there brings everything in; nothing has
  been pushed.
- **Still owed:** the production `python -m app.data.claims.sync --dry-run` on Fly, after a deploy of this code.
