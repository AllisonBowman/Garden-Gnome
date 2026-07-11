# plant-id — on-device plant identification

Expo local native module that runs **on-device** generative AI to identify a
plant from a photo, per platform:

- **iOS** — Apple **Foundation Models** (iOS 26+), paired with **Vision** for
  image perception. `ios/PlantIdModule.swift`
- **Android** — **Gemini Nano** via **ML Kit GenAI Prompt API** (AICore-backed).
  `android/.../PlantIdModule.kt`

Same JS API on both (`index.ts`): `isAvailable()` and `identify(uri, prompt)`.
The app never trusts the model's raw text — `src/photoId/` fuzzy-matches it
against the curated species catalog and only offers real records with real care
data. On unsupported devices `isAvailable()` returns `false` and the UI falls
back to manual species search.

## ⚠️ Build & test requirements (not verifiable on the dev machine)

This module was written but **not compiled** here (no macOS/Xcode, no Android
SDK). Both native paths need on-device compilation and testing.

**This changes the workflow: the app now needs a dev/prebuild build (EAS or
`npx expo prebuild`). It will no longer run in Expo Go**, because Expo Go can't
load custom native modules. The JS/web paths (and manual search) still work
anywhere; on-device AI only lights up in a real build on capable hardware.

### iOS
- Requires the **Xcode 26 SDK** to compile (Foundation Models). The framework
  is weak-linked and every use is `@available(iOS 26.0)`-guarded, so the app
  still installs and runs on older iOS — it just reports `isAvailable() == false`.
- Runtime needs an **Apple-Intelligence-capable device** with the feature
  enabled and not region/language-restricted.
- Verify the Foundation Models API surface (`LanguageModelSession` init and
  `respond(to:)`) against the shipping SDK — Apple has iterated on it.
- On the EAS build profile, pin an image with Xcode 26
  (`eas.json` → `build.<profile>.ios.image`).

### Android
- Uses `com.google.mlkit:genai-prompt` (see `android/build.gradle`). **Verify
  the artifact name/version** against the current ML Kit GenAI release — the
  Prompt API is new and coordinates may change.
- Gemini Nano runs only on **AICore-capable devices** (currently newer
  flagships). Others return `isAvailable() == false`.
- `checkFeatureStatus()` gates inference; `DOWNLOADABLE` triggers a one-time
  model download before the first inference.

## Design note
Foundation Models (iOS 26) is a *text* model, so iOS does photo→name in two
on-device steps: Vision extracts visual labels, then Foundation Models names the
species from those labels. Android's Gemini Nano is natively multimodal, so it
takes the image + prompt directly.
