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
- Two committed screenshots (`docs/screenshots/2026-07-20-*.png`) document
  user-facing defects in a shipped build: `[STUB] … Set VISION_BACKEND=ollama`
  rendered to a user, and a gnome note claiming *"I've watered your Front Yard
  Sunflower"* signed *"Love, [Your Name]"*. Fixes are
  `plantadvocate-alignment-plan.md` Phase 0/1 — not addressed here.

## How to re-run

```bash
cd garden-gnome && .venv-win/Scripts/python.exe -m pytest   # expect 87 passed
cd mobile && npm run typecheck                              # expect exit 0
```

`pytest.ini` pins `testpaths = tests`, so packages added outside `tests/` are
not collected.
