# PlantAdvocate — 1.0.1 Feature Plan

Implementation plan for Claude Code. Repo: `C:\Users\14439\garden-gnome`
(backend at root, app in `mobile\`). Work phases in order; each ends with the
suite green and the mobile typecheck clean. Follow the adopted decisions in
garden-gnome-auth-plan.md and the PLANTADVOCATE-HANDOFF doc rules (rebrand,
"care engine" not "AI" in user-facing copy, gnome = mascot).

## Ground rules

- **Do not derail 1.0.** Phase 0 items ship in the 1.0 submission; everything
  else targets the 1.0.1 release. No schema migrations in this plan.
- App Store version strings: 1.0 now in TestFlight; this plan releases as
  1.0.1 (bump `expo.version` in Phase 1).

---

## Phase 0 — 1.0 blockers (fix before submitting for review)

1. **Missing-icon sweep ("question marks").** Care logs (and possibly other
   screens) render ? / tofu glyphs where icons should be — classic
   react-native-vector-icons failure in release builds: font not bundled, or
   icon names that don't exist in the chosen set. Audit every icon reference,
   confirm the config plugin bundles the font families used, fix or replace
   invalid names, and add a single typed icon registry so future misses fail
   typecheck instead of rendering tofu. Verify list: every screen that renders
   care-log entries, plus tab bars and buttons.
2. **Report + support (also a 1.0 compliance item).** Per the handoff's AI
   disclosure requirements: every AI-produced result (photo diagnosis,
   care-engine advice) gets a small "Report this result" affordance, and
   Settings gains an "About & Support" card:
   - Website → opens https://plantadvocate.ai in the default browser
     (`Linking.openURL`)
   - Support & feedback → https://plantadvocate.ai/support.html
   - Report links pass context as query params (species id, result type — no
     user identifiers) so the support page can prefill a form.
3. Re-run the pre-submission audit from the handoff section 2 (report button,
   photo-consent copy, no "Garden Gnome" strings) and list any remaining gaps.

**Accept when:** a release-mode build renders zero tofu; report/support links
open externally; audit passes.

## Phase 1 — Gnome persona consistency

The "Ask the Gnome" voice drifts (sometimes addresses the plant, sometimes
nobody). Lock the persona:

- Create ONE persona module (`mobile/src/gnome/persona.ts` + backend
  equivalent for advisor prompts) defining: the gnome speaks **to the human
  caretaker**, refers to **the plant in third person by its nickname**,
  acknowledges the human's logged care actions ("you watered Fern Gully three
  days ago"), and **signs off as the gnome** (pick one signature, e.g.
  "— your Garden Gnome", and use it everywhere).
- Route every gnome-voiced surface (advice responses, notifications,
  empty-state copy, diagnosis explanations) through that module. Remove
  inline prompt fragments.
- Tests: snapshot/regex tests assert second-person address to the caretaker,
  third-person plant references, and the signature on every gnome surface.
  Backend advisor prompt templates get the same persona preamble (stub and
  anthropic backends).

## Phase 2 — Camera capture with focus-region preview

Replace the current photo picker path with a proper capture flow:

- `expo-camera` full-screen capture screen (shutter, flash toggle, flip).
- After capture: preview screen where the user **selects the region of
  interest** — draggable/resizable crop box over the photo, pinch to zoom,
  with a subtle dimming outside the selection. Confirm → the cropped region
  (plus the full frame) feeds the diagnosis pipeline.
- **IP note:** the Google Lens *interaction logic* (capture → select region →
  analyze) is fair to learn from; do NOT copy Lens's visual design, corner
  animations, iconography, or branding. Use our own visual language (gnome
  palette, existing design tokens). No Google assets anywhere.
- Library fallback stays (choose from Photos) with the same region step.
- Accept when: capture → region-select → diagnosis works in a dev build;
  cropped bytes measurably smaller than full frame; all-new UI assets.

## Phase 3 — Photo diagnosis wiring (on-device first)

Current state: server `VISION_BACKEND=stub`; the app already contains an
on-device `PlantId` native module (weak-linked FoundationModels, iOS-26
gated). Wire the flow honestly:

1. **Audit first:** document exactly what the PlantId module can do today
   (classification labels? confidence? input size?) and what the iOS
   Foundation Models / Vision framework APIs actually support on-device on
   current iOS — do not overpromise "Apple Intelligence" beyond what the
   device API returns. Report findings before wiring.
2. Routing order for a diagnosis request: (a) on-device pipeline when the
   device supports it — private, free, offline; (b) else server
   `POST /plants/{id}/diagnose` IF a hosted vision backend is enabled;
   (c) else the friendly "not enabled" state (current stub behavior).
3. Results always return **confirmable candidates** (top-N with confidence),
   never a single asserted answer — this is the guideline 4.2 defense in the
   review notes; keep it true.
4. Consent rule (handoff section 2): photos processed on-device need no
   upload consent; the FIRST time a photo would leave the device (server
   path), show the consent sheet, store the choice on the user profile.
5. Decision for Allison (not blocking): enabling the hosted fallback means
   `VISION_BACKEND`/`ADVISOR_BACKEND=anthropic` + `ANTHROPIC_API_KEY` on Fly
   and per-call costs. Ship 1.0.1 with on-device primary + stub fallback
   unless she says otherwise.

## Phase 4 — SmugMug photography as app/site art

Allison's own photography (she owns the rights) replaces generic art:

1. Allison provides her SmugMug URL and picks candidate galleries.
2. Claude (Cowork session) or Claude Code fetches the chosen images at
   suitable resolution — download originals/large renders, never hotlink
   SmugMug URLs in the app.
3. Process: crop to the needed aspect ratios, compress (webp/heic), generate
   the required scale variants; store in `mobile/assets/photography/` with a
   CREDITS.md noting © Allison Bowman.
4. Integrate: onboarding background, empty states, Environment-type default
   headers, website hero images (site repo), and App Store screenshots
   backdrop if desired.
5. Accept when: bundle size increase < ~3 MB (compress aggressively), no
   hotlinks, credits file present.

## Phase 5 — Release

- Bump `expo.version` to 1.0.1, build number auto-increments.
- `eas build --profile production --platform ios` → `eas submit` → TestFlight
  pass on device → submit as update once 1.0 is approved (App Store Connect
  will offer a new 1.0.1 version page; metadata carries over).
- Update the handoff doc UPDATE LOG.

## Suggested kickoff prompt (Phase 0 only — protect the 1.0 timeline)

> Read plantadvocate-1.0.1-plan.md. Implement Phase 0 only (1.0 blockers):
> the missing-icon sweep, the Report/Support links per spec, and the
> handoff-section-2 audit. Run the suite + mobile typecheck, stop, and
> report the audit results with anything that should block 1.0 submission.
