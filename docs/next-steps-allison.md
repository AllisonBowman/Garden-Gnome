# Next steps — what only you can do

Everything in this file needs your Apple account, your EAS account, or your
phone. Nothing here can be done from the dev machine.

Work top to bottom. Step 1 is the one that matters most: it answers a question
that has been open since the on-device identification module was written.

---

## Step 1 — Compile the on-device module (the open question)

**Why this matters.** `mobile/modules/plant-id` is the native code behind
"identify my plant from a photo." Its own README says it was "written but
**not compiled** here." No build has ever contained it. It might work
perfectly; it might not compile at all. Nobody knows, and it is the app's
headline feature.

**Why a normal build won't tell you.** Expo Go cannot load native modules, so
testing in Expo Go proves nothing about this code. You need a *development*
build, which compiles the native module into a real app you install on a real
phone.

All commands below are **PowerShell**, run from
`C:\Users\14439\Garden-Gnome\mobile`.

> PowerShell 5.1 has no `&&`. Chain with `;` if you want commands on one line.

### 1a. Already done — no action needed

Checked on 2026-07-21:

- `eas-cli` is installed globally (v20.5.1) — no `npx` needed, just `eas`.
- You are already signed in as **allisonbowman** (`bowman0509@gmail.com`),
  which matches `owner` in `app.json`. **No login step.**
- Two iPhones are already registered to Apple team `FK6E9XBY6Y`
  ("I 13" and "Allison's iPhone"). **No `device:create` step.**

Your Apple Team ID is **`FK6E9XBY6Y`**. Some `eas` commands can't pick a team
on their own and need `--apple-team-id FK6E9XBY6Y` appended.

To re-check any of that:

```powershell
Set-Location C:\Users\14439\Garden-Gnome\mobile
eas whoami
eas device:list --apple-team-id FK6E9XBY6Y
```

### 1b. Confirm the build profile (optional, ~20 seconds)

Already verified, but it's the cheapest way to catch a config mistake before a
30-minute build:

```powershell
Set-Location C:\Users\14439\Garden-Gnome\mobile
eas config --platform ios --profile development --non-interactive
```

Look for `"image": "macos-tahoe-26.5-xcode-26.6"`, `"developmentClient": true`,
and `"distribution": "internal"`.

### 1c. Build

```powershell
Set-Location C:\Users\14439\Garden-Gnome\mobile
eas build --profile development --platform ios
```

Run this in your own terminal — it may prompt about credentials, and answering
"yes, let EAS handle it" is correct.

This runs on Expo's macOS machines (~15–30 min). The build image is pinned to
`macos-tahoe-26.5-xcode-26.6` in `mobile/eas.json`, because the module needs
the **Xcode 26 SDK** for Apple's Foundation Models framework. Without that pin
the build would use a default image and could fail — or worse, quietly produce
a build with the feature stripped out.

**Optional:** `eas-cli` 21.0.2 is available (you have 20.5.1). Not required —
20.5.1 accepted the pinned image fine. If you want it:
`npm install -g eas-cli`

### 1d. Read the result carefully

**This step is a test, not a formality. All three outcomes are useful:**

| What you see | What it means | What to do |
|---|---|---|
| Build succeeds | The native module compiles. Genuinely good news. | Continue to Step 2. |
| Build fails in "Run fastlane" / compile phase, errors naming `PlantIdModule.swift` or `FoundationModels` | The module has never-caught compile errors. | **Send me the full log URL.** This is the outcome worth finding now rather than during App Review. |
| Build fails on credentials/provisioning | Signing setup, not the module. | Usually re-running and letting EAS manage credentials fixes it. |

Do not skip past a failure here or work around it — a failure *is* the answer
to the open question, and it's better to have it today.

---

## Step 2 — Check what the module actually does on your phone

Install the build from the EAS link (or the QR at the end of the build).

### 2a. First, the hardware question

On-device identification runs on **Apple Intelligence**, which requires an
**iPhone 15 Pro / 15 Pro Max or newer, on iOS 26**. Base iPhone 15, iPhone 14,
and older cannot run it — no exceptions, it's a hardware limit.

**Check the phone you'll install on: Settings → General → About → Model Name,
plus the iOS version.**

Of your two registered devices, the one named "I 13" is almost certainly an
iPhone 13, which **cannot** run Apple Intelligence — install on that one and
you are testing path 2c. I can't tell what "Allison's iPhone" is from its UDID,
so check it in Settings rather than assuming.

- **If your phone qualifies** → do 2b.
- **If it doesn't** → do 2c instead. That is still a real, necessary test, not
  a consolation prize.

### 2b. If your phone qualifies

1. Open the app → **Add Plant**.
2. The photo-identify button should be **visible**. (The app hides it when the
   module reports unavailable — so if you can see it, `isAvailable()` returned
   true, which already proves the module loaded.)
3. Photograph a plant you can identify yourself. Something distinctive.
4. Note what comes back: does it offer candidate chips? Are they real species
   from the catalog? Is the right one among them?

Write down what happened for 5–6 plants. Don't worry about scoring it
properly — that's the vision-eval plan's job later. Right now you're
answering "does this work at all."

### 2c. If your phone does not qualify

1. Open the app → **Add Plant**.
2. The photo-identify button should be **absent** — not greyed out, not
   showing an error, just not there.
3. Confirm you can still find and pick a species using the search field.

That's the fallback path, and confirming it is genuinely important: it's what
most of your users will see, since most iPhones in use can't run Apple
Intelligence.

**If you see a visible button that then errors, tell me** — that's a bug (a
dead button), and the app is supposed to hide it instead.

---

## Step 3 — Confirm today's fixes on a real build

The two screenshots in `docs/screenshots/` came from a real build and showed
two defects. I fixed one of them today. This step confirms the fix on device
and gives us a "before/after" pair.

### 3a. Photo diagnosis no longer shows setup instructions

**Before** (`2026-07-20-photo-diagnosis-stub.png`): "Gnome's Findings" showed
`[STUB] … Set VISION_BACKEND=ollama and pull a vision model…`

1. Open any plant → run a photo diagnosis.
2. **Expect:** "📷 Photo received! The Gnome's photo check-ups aren't switched
   on yet, so there's no reading to share for *[plant name]* this time. Jot
   down what you're seeing in the care log…"
3. **Then scroll to that plant's care history.** There should be **no new
   entry** from this diagnosis. Previously it filed the `[STUB]` text into the
   plant's permanent timeline.
4. Screenshot both and save as `docs/screenshots/2026-07-21-photo-diagnosis-fixed.png`.

**If you see the word "STUB", or any mention of a backend or Ollama, stop and
tell me** — something didn't ship.

### 3b. What is NOT fixed yet (don't be alarmed)

`2026-07-20-gnome-voice-letter.png` showed the gnome writing a letter signed
"Love, **[Your Name]**", spelling numbers out ("thirty-five days"), and
claiming *"I've watered your lovely Front Yard Sunflower"* — which it never
did; you did.

**That is still broken.** It's alignment-plan Phases 1–2, not today's work. If
you see it on this build, that's expected. Note it and move on.

---

## Step 4 — Tell me what you found

The useful things to report back, roughly in order:

1. Did the build succeed? If not, the log URL.
2. Does your phone qualify for Apple Intelligence? Which model / iOS version?
3. Was the identify button visible, and did it return anything sensible?
4. Did the diagnosis copy look right, and did the care history stay clean?
5. Anything that looked wrong that I haven't mentioned — trust your eye here,
   you know how this is supposed to feel better than I do.

---

## What I'd suggest doing after that

Depending on how Step 1 goes:

- **If the module compiles and identification works** → alignment-plan Phases
  1–2 (fix the gnome-voice letter drift), then the 1.0.1 Phase 0 leftovers
  (typed icon registry, `APP_VERSION` deduplication, the Android package name
  still reading `com.allisonbowman.gardengnome`).
- **If the module doesn't compile** → that becomes the whole priority, and the
  1.0 submission plan needs rethinking, because the headline feature isn't
  real yet.
- **The 50-photo vision eval** comes after both. It measures quality, and
  there's no point measuring until we know the thing runs.

---

## Reference — PowerShell commands on the dev machine

Backend tests (expect `89 passed`):

```powershell
Set-Location C:\Users\14439\Garden-Gnome\garden-gnome
.\.venv-win\Scripts\python.exe -m pytest
```

Mobile typecheck (expect no output; `$LASTEXITCODE` is 0):

```powershell
Set-Location C:\Users\14439\Garden-Gnome\mobile
npm run typecheck
$LASTEXITCODE
```

If pytest fails with `No module named 'PIL'`, the venv is behind
`requirements.txt`:

```powershell
Set-Location C:\Users\14439\Garden-Gnome\garden-gnome
.\.venv-win\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Check build status / grab a log URL after a build:

```powershell
Set-Location C:\Users\14439\Garden-Gnome\mobile
eas build:list --platform ios --limit 5
```
