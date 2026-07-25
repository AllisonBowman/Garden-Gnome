# PlantAdvocate — Vision Feature Test Handoff

Structured pre-build test of the two photo features, executable by a future
Claude Code session or by Allison directly. Written after the decision to
**remove the Ollama backend entirely**, which reshapes what "testing the
vision features" means:

- **Species identification** runs **on-device** (`mobile/modules/plant-id`:
  Apple Foundation Models on iOS 26+, grounded against the catalog by
  `mobile/src/photoId/fuzzyMatch.ts`). It is the star of this test and can
  only be exercised on a real iPhone.
- **Photo diagnosis** ships **disabled** (server `VISION_BACKEND` knows only
  `stub`). What we test is the *disabled-state experience*: friendly copy,
  nothing developer-flavored anywhere, nothing junk logged to the plant's
  timeline.

Tooling lives in `garden-gnome/evals/` (see its `__init__.py`); results are
committed under `docs/evals/`.

## Ground rules

- **This test measures; it does not fix.** Guard/copy changes belong to
  `plantadvocate-alignment-plan.md`. If a gate fails, the finding is the
  deliverable.
- **Photos are never committed** (privacy/EXIF-GPS, licensing, repo size).
  The committed record is `evals/manifest.csv` + the results summary.
- Gate thresholds below are proposals — ratify or adjust them at Phase 0,
  before any results exist.

## Pre-flight blockers (read before anything else)

1. **The native module has never been compiled.** `modules/plant-id` was
   written on a machine with no Xcode/Android SDK. It requires an EAS
   dev/preview build (`npx expo prebuild` path) — **the app no longer runs
   in Expo Go**. First build of this module may surface Swift compile
   errors (verify the Foundation Models API surface against the shipping
   SDK, per `modules/plant-id/README.md`).
2. **iOS build image.** `eas.json` now pins `ios.image: "sdk-57"` on the
   `development` and `preview` profiles. When building, confirm in the EAS
   build logs that the resolved image carries the **Xcode 26 SDK** — if
   not, look up the current Xcode-26 image tag on
   https://docs.expo.dev/build-reference/infrastructure/ and pin it
   explicitly.
3. **Device requirement.** On-device identify needs an
   **Apple-Intelligence-capable iPhone (15 Pro or newer) on iOS 26** with
   Apple Intelligence enabled. **If the test phone doesn't qualify**, the
   identify half collapses to fallback-UX verification: confirm the
   Identify button never renders (`isAvailable() == false`) and manual
   search works. The build decision then rests on gates I1, U1, U2 only.
4. **Alignment Phase 0 first.** With diagnosis stubbed, the `[STUB]`
   diagnosis copy and the stub-text-into-timeline auto-log
   (`plantadvocate-alignment-plan.md` Phase 0, items 1 and 4) are what
   users will actually see. Land those before cutting the build; gates
   U1/U2 verify them.

## The photo set (~30 photos)

Drop files in `garden-gnome/evals/photos/` (gitignored), named
`p0NN-short-desc.jpg`, one row each in `evals/manifest.csv` (see the
committed example rows; columns are documented by
`python -m evals.checklist --validate` errors).

| case_type | count | what |
|---|---|---|
| `in_catalog` | 15–20 | Allison's own plants, phone photos, mixed houseplants + outdoor/edibles from the 129-species catalog (Snake Plant, Monstera, Peace Lily, Lavender, Pansy, …). Vary framing: whole plant vs single leaf. |
| `out_of_catalog` | 4–6 | Real plants the catalog lacks (e.g. Staghorn Fern). Fill `species_freetext`. Expect the "isn't in our care database" fallback. |
| `junk` / `non_plant` | 3–4 | Coffee mug, bookshelf, a pet. Expect no candidates. |
| `blurry` | 2–3 | Deliberately unusable shots of real plants. Expect no candidates. |

Sourcing: Allison's own photos wherever possible (`source=allison`,
`license=own`); fill gaps from openly licensed sources (Wikimedia Commons,
CC-licensed iNaturalist) with exact `license` + `source_url` per row —
acceptable because photos are never committed or redistributed.

## Phase 0 — Tooling smoke (no photos, no phone)

```bash
cd garden-gnome
python -m evals.selftest              # 19 checks, all offline
python -m evals.checklist --validate  # example rows: 0 errors (photo warnings ok)
python -m pytest                      # backend suite stays green (78)
```

Also: ratify the gate thresholds below.

## Phase 1 — Assemble and label the photo set

Shoot/source per the table, fill `manifest.csv`, then:

```bash
python -m evals.checklist --validate --require-files   # now 0 warnings too
python -m evals.checklist --print > evals/output/checklist.md
```

## Phase 2 — Device build + on-device run

1. `eas build --profile development --platform ios` (or `preview`).
   Confirm: build succeeds, the resolved image has Xcode 26, and the
   PlantId pod compiled (search the build log for `PlantId`).
2. Install on the phone. Smoke: Add Plant shows the "Identify from a
   photo" button (that IS `isAvailable() == true`); the Ask-the-Gnome
   advice card shows the `gnome voice` badge on styled advice (same
   native module — a second signal it's alive).
3. AirDrop the `device_set=yes` photos to the phone.
4. Work through the printed checklist: for each photo, Add Plant →
   Identify from a photo → record candidates shown (best first), which
   tier message appeared, and the `raw:` debug line (dev/preview builds
   only) → **cancel without saving**.
5. Disabled-diagnosis UX smoke (any 2–3 photos, on a real plant record):
   run Photo diagnosis end-to-end against the hosted server. Verify: the
   response copy is friendly (no `[STUB]`, no env vars, no tooling
   names), the "diagnosis not enabled yet" chip shows, the plant's
   timeline afterwards contains nothing developer-flavored, and
   `GET /ai/status` reports `vision.ready: false`.

## Phase 3 — Score and record

Transcribe the checklist into `evals/output/device_run.csv`
(`case_id, raw_text, shown_candidates, shown_tier` — pipe-separate
candidates; record the search-below fallback as tier `none`), then:

```bash
python -m evals.replay_device --input evals/output/device_run.csv
```

The tool prints per-case agreement and the gate summaries. A tier
disagreement means the mirror, fed the same raw text, decided differently
than the app did — transcription error or a drifted port; investigate
before trusting the run.

Commit the record as `docs/evals/<date>-vision-test-results.md`: gate
verdict table, the replay output, counts per case type, and any findings
(e.g. species the model consistently misses). Raw CSVs stay local.

## Gates: OK-to-cut-the-build criteria

Identify (manual device run + replay):

| # | Gate | Threshold |
|---|---|---|
| I1 | PlantId module compiles; `isAvailable()` true on the test phone; zero crashes during the run | binary |
| I2 | In-catalog photos: truth among shown candidates | ≥ 50% |
| I3 | Junk / blurry / out-of-catalog: no candidates, search-below fallback shown | ≥ 80% |
| I4 | Candidates shown are always real catalog rows; `raw:` line absent in a production build | 100% |
| I5 | Replay tier agreement (mirror vs device) | ≥ 90% |

Disabled-diagnosis UX:

| # | Gate | Threshold |
|---|---|---|
| U1 | Diagnosis answers with friendly copy — zero `[STUB]`/env-var/tooling strings anywhere in the UI | 100% |
| U2 | Nothing developer-flavored written to the care timeline by a diagnosis attempt | 100% |

I2's bar is deliberately modest: a small on-device model against a
129-name catalog, graded on truth-in-candidates (not top-1). Beating it
comfortably is a bonus; missing it is a real signal to rethink the flow
(e.g. stronger Vision-label prompting) before shipping.

## Explicit non-goals

- Choosing a replacement server diagnosis backend — open product
  decision; the feature ships disabled either way.
- The Android / Gemini Nano path (no test device; module gates itself off).
- Adding jest to mobile. When that happens, port
  `evals/fuzzy_mirror.PARITY_FIXTURES` into `fuzzyMatch.test.ts` verbatim
  — the fixtures are the parity contract.
- Alignment plan Phases 1–4 (Phase 0 items 1+4 are prerequisites, tracked
  there).
- CI wiring — the interesting half of this test needs a physical iPhone.

## Suggested kickoff prompt

> Read plantadvocate-vision-test-plan.md. Run Phase 0 (selftest, manifest
> validation, pytest), confirm the alignment-plan Phase 0 prerequisites
> have landed, report results, and stop — the photo set and device run are
> Allison's part.
