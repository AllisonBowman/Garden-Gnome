# Verification baseline — 2026-07-21

First run of both acceptance gates against released code. Every plan in this
repo (`plantadvocate-1.0.1-plan.md`, `plantadvocate-alignment-plan.md`, the
vision-eval handoff) ends its phases with "the suite green and the mobile
typecheck clean" — until today neither command had a recorded result, and one
of them did not exist.

## Why this file exists

- `mobile/` had **no `typecheck` script**, so the mobile half of every gate was
  unrunnable as written.
- `.pytest_cache` was stamped **2026-07-19 15:13** — *before* the 1.0 Phase 0
  commits at 2026-07-19 23:54. The release commits had never been run against a
  suite.
- The Ollama vision work lived on `claude/plant-advocate-screenshots-xxt8ed`,
  never fetched locally, so analyses run against `master` silently missed it.

The branch has since been fast-forward merged into `master`.

## Results

Both gates pass as of commit `3f7d80d`+merge.

### Backend suite

```bash
cd garden-gnome
.venv-win/Scripts/python.exe -m pytest
```

```
87 passed, 2 warnings in 7.45s
```

71 pre-existing tests + 16 in `tests/test_vision.py`.

**Now 89** — alignment-plan Phase 0 added two regression tests (see below).

**First run failed: `2 failed, 85 passed`** — `ModuleNotFoundError: No module
named 'PIL'` in `test_prepare_image_downscales_and_reencodes` and
`test_diagnose_sends_downscaled_photo`. Not a code defect: commit `a99b1fb`
added `pillow>=10` to `requirements.txt`, but the local `.venv-win` predated it.
Resolved by the README's own setup step, `pip install -r requirements-dev.txt`
(installed pillow 12.3.0). **If you see those two failures, your venv is stale.**

### Mobile typecheck

```bash
cd mobile
npm run typecheck        # tsc --noEmit
```

Exit code 0, no diagnostics. Script added 2026-07-21; `tsconfig.json` already
extended `expo/tsconfig.base` with `"strict": true`.

## Answered

**Are the 2026-07-19 Phase 0 release commits green?** Yes — both gates pass on
the merged tree. They were shipped unverified, but they were not broken.

## Still open

- **`mobile/modules/plant-id` has never been compiled into any build.** Its own
  README says so outright ("written but **not compiled** here"). On-device
  identification is the app's headline feature and no build has ever contained
  it. Needs an EAS **dev** build (`--profile development`) with an Xcode-26
  `ios.image` pin — Expo Go cannot load a native module. On-device inference
  additionally needs an Apple-Intelligence-capable iPhone (15 Pro+) on iOS 26;
  if the test device doesn't qualify, verifying the `isAvailable() === false`
  fallback path is a valid result.

  The image pin is now in place: `development` and `preview` in
  `mobile/eas.json` pin `ios.image` to `macos-tahoe-26.5-xcode-26.6`, verified
  against Expo's build-infrastructure docs on 2026-07-21 — it carries Xcode
  26.6 and is the image aliased `sdk-57`/`latest`, matching this app's
  `expo ~57.0.7`. Re-check the tag against the current image list when it next
  needs bumping; these tags are retired over time.

  Remaining step is Allison's: `eas build --profile development --platform ios`,
  install on device, confirm `isAvailable()`.
- The gnome-voice drift in `docs/screenshots/2026-07-20-gnome-voice-letter.png`
  ("I've watered…", "Love, [Your Name]", "thirty-five days") is **not** fixed.
  That is alignment-plan Phases 1–2 (persona contract + drift guard v2).

## Alignment plan Phase 0 — done 2026-07-21

"Stop shipping developer text." All four items complete; suite 89 passed,
typecheck exit 0.

1. `vision._diagnose_stub` rewritten in the `_identify_stub` voice. Byte count,
   `VISION_BACKEND`, and `ollama pull` moved to `logger.info`.
2. `AdvisorUnavailable` added (mirrors `VisionUnavailable`): `_advise_ollama`,
   `_advise_anthropic`, and every `catalog.generate_species_profile` failure
   path now raise a user-safe message and log the cause. The stray
   `print("[advisor] anthropic tokens…")` became `logger.info`.
3. Stub diagnoses no longer auto-file a `CareLog`, and `advisor._build_prompt`
   summarizes any note starting with `PHOTO_DIAGNOSIS_PREFIX` to
   "photo check-up filed, N days ago" instead of inlining it — model output
   can no longer re-enter a prompt as owner-recorded history.
4. Mobile "Check the backend connection" alerts replaced with caretaker copy
   via the new `serverMessage()` helper (`mobile/src/api/errorMessage.ts`),
   which surfaces the server's 503 `detail` when present and falls back
   otherwise.

Also fixed in passing: `_advise_stub` said "Symptom diagnosis needs the AI
advisor", violating the handoff's "care engine, never AI" rebrand rule.

### Accept-when results

```bash
grep -rniE "\[stub\]|VISION_BACKEND|ADVISOR_BACKEND|ANTHROPIC_API_KEY|ollama|api key" mobile/src/
# no matches

grep -rnE "\[STUB\]" garden-gnome/app/
# no matches
```

Two regression tests lock it in — `test_stub_diagnose_leaks_no_developer_text`
(asserts the six leak strings are absent from the returned diagnosis) and
`test_stub_diagnosis_files_no_care_log` (drives the real route and asserts the
plant's timeline stays empty).

**Known, deliberate exception:** `vision_status()` detail strings
("Ollama is not reachable", "Model 'x' is not pulled") do name the tool. They
are served only by `GET /ai/status`, which is an operator/ops endpoint that
the mobile app never calls — its docstring commits to "operator-facing but
contains no hosts or secrets." If the app ever probes `/ai/status` to gate its
photo UI, that copy must not be shown to a caretaker verbatim.

## How to re-run

```bash
cd garden-gnome && .venv-win/Scripts/python.exe -m pytest   # expect 87 passed
cd mobile && npm run typecheck                              # expect exit 0
```

`pytest.ini` pins `testpaths = tests`, so packages added outside `tests/` are
not collected.
