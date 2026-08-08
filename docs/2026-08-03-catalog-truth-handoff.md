# Catalog-truth work — where it stands, what's next

For the next session. Approved plan lives at
`~/.claude/plans/the-app-needs-a-twinkling-crown.md` ("Make the catalog true
before launch"); this is the state of its execution as of 2026-08-03.

## Where things are

Branch `care-advice-honesty`, two commits, **not yet pushed**, not merged:

- `59e9a0d` — Phase 1 partial: mist retired everywhere (reminders, streak,
  settings, quick-log), fertilize gated to Mar–Oct and checked against the
  landing day of the reminder, and the overdue-at-min bug fixed (status now
  derives from the window's far edge + the streak's 3-day grace; in-window
  copy reads "Last done N days ago"). Gates green, leak scan clean.
- `90dc913` — the first tranche of real data:
  `garden-gnome/app/data/verified/b1..b5.json`. 40 species (28 curated
  houseplants + all 17 in-use), 293 citations each carrying a verbatim
  supporting quote, 469 deliberate nulls with reasons. Produced by a
  research → two-adversarial-auditors → reconcile workflow; 89 of 629
  proposed values were killed in audit (14%). **Review artifacts only —
  nothing has touched the database.**

## Do next, in order

1. **Push the branch.** It exists only on this Mac.
2. **Finish Phase 1:** repot → seasonal inspection with condition checklist
   (task #17); water → "check" verb with a `checked_not_needed` outcome, streak
   counts checks (#18); suppress fabricated humidity via the `humidity_source`
   trait, with a `tier.ts` fallback (plan 1.6); free light reclassification of
   the shade-adapted genera (plan 1.7).
3. **Fix `apply_review.py` before anything lands in the DB** (plan 3.1). It
   stamps `uncertain` as `verified` (would falsely verify 1,239 rows), writes
   `toxic_to_pets: false` verbatim, deletes without cascade, has no dry-run and
   no tests. The verified/ data stays parked until this is done.
4. **Resolve the synthesis findings** before loading the tranche — they're
   transcription-convention issues, not research errors:
   - Clemson's band "min 100–150, preferred 200–500" was read top-of-band in
     b1 (Spider Plant, Philodendron: 150/500) and bottom-of-band in b3
     (Boston Fern, Prayer Plant: 100/200). Pick one convention, re-normalise.
   - ZZ's light_fc_min 25 is a UF/IFAS *survival* floor; everything else is a
     Clemson *growth* minimum. Two meanings in one column — either split the
     field or normalise to growth minimums.
   - Aloe/Jade carry light_fc_min 150 (a philodendron-level floor) after the
     audit killed their fc_good but left the floor. Re-source or null.
   - Feeding intervals survived inconsistently (Fiddle Leaf kept a 90d
     "general guidance" interval; Aspidistra's was killed for the same
     wording). Apply one rule.
   - All 10 outdoor plants read `full_sun` off NC State's first checkbox;
     three of their own quotes say part shade. Re-read the checkboxes.
5. **Name fixes, with traps:** `Aloe barbadensis miller` → `Aloe vera`
   (three errors in one string; live in `species_catalog.json`).
   `Cucumis melo var. flexuosus` → `Cucumis melo` **collides** with the
   existing "Melons" row — don't auto-apply. `Dracaena marginata`: NC State
   and MoBot disagree — leave as-is. Schlumbergera should be
   `× buckleyi` with a note that store plants are often *truncata*.
6. **Schema deltas the data demands:** drop DLI (0/40 — no extension source
   publishes it); humidity category not percentages (23/40 vs 2/40); watering
   intervals are 8/40, so the regime-first design is confirmed.

## Standing cautions

- `verified` in the DB means human-checked; **zero rows** have it. Don't let
  any automated pass set it.
- ASPCA toxicity data is legally unusable; never cite or copy it.
- Sim workflow gotchas are in memory (`plantadvocate-sim-run`): address
  simulators by UDID, never `booted`; PlantAdvocate's Metro runs on 8082
  (8081 belongs to Bridge for Lovers).
- TestFlight: 1.1.2 build 15 is live with testers; notes doc
  `docs/2026-08-02-testflight-1.1.2-notes.md`.
