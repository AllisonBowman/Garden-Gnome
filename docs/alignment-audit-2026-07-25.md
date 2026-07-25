# Alignment cross-surface audit — 2026-07-25

Phase 4 of `plantadvocate-alignment-plan.md`. Every surface where model output
can reach a caretaker, checked against the persona contract
(`mobile/src/gnomeVoice/persona.ts`, `app/services/persona.py`) and the
no-developer-text rule.

Suites at time of audit: backend **287 passed**, mobile **88 passed**,
`tsc --noEmit` clean.

## Surfaces

| Surface | Model output? | Guarded by | Persona contract | Dev text |
|---|---|---|---|---|
| Care advice card (`PlantDetailScreen`) | yes — advisor backend, then on-device restyle | `grounding_failures` server-side, `driftReasons` on device | ✅ prompt + both guards | ✅ `UNAVAILABLE_MESSAGE` only |
| Photo diagnosis card | yes — vision backend | `grounding_failures(check_care_stems=False)`, retry once then unavailable | ✅ shared `PERSONA_PREAMBLE` | ✅ stub copy rewritten, `[STUB]` is server-log only |
| Identify chips (`photoId`) | yes — vision identify | name-matched against the curated catalog; free text never rendered | n/a — no prose | ✅ |
| Timeline / care-log notes | filed diagnosis text | only logged when `backend != "stub"`; excluded from later prompts via `PHOTO_DIAGNOSIS_PREFIX` | n/a | ✅ |
| Notifications / reminders | no — rule-based scheduler | n/a | n/a | ✅ |
| Species catalog copy | curated + `generate_species_profile` | `AdvisorUnavailable` on the 503 path | n/a | ✅ |

## Checklist

- [x] **One persona definition per platform.** `persona.ts` and `persona.py`;
      no other prompt text defines voice (grep for `You are a warm` /
      `whimsical` / `cozy note` outside `persona*` returns nothing).
- [x] **Sign-off appended by code, never by the model.** `appendSignOff` runs
      *after* the drift guard, so a code-written signature can never be read as
      model drift; `PERSONA_CONTRACT` does not contain `SIGN_OFF` (pinned by
      test). Exactly one sign-off per note (pinned by test).
- [x] **No "Garden Gnome" in user-facing copy**, including the new sign-off
      (`— the Gnome 🧙`). Remaining hits are developer surfaces only:
      `app/main.py` OpenAPI title and `app/static/index.html` test console.
- [x] **No developer text in user-visible strings.** No `[STUB]`, env var
      names, API-key references, or model-server names in `mobile/src` or in
      any API response body.
- [x] **The screenshot letter can never render again.** Rejected by four
      independent checks on device (`placeholder`, `first-person-care`,
      `commitment`, `letter-scaffolding`) and by the same four server-side.
- [x] **Guard failure is always honest.** Advisor falls back to `_advise_stub`
      and reports `backend: "stub"`, `guarded: true`, so the badge describes
      what the user is reading. Vision retries once, then returns the
      unavailable message rather than an ungrounded diagnosis.
- [x] **Verified through the wired route**, not only the service:
      `test_advice_route_grounding.py` drives `POST /plants/{id}/advice` with
      the screenshot letter as the backend's response and asserts it never
      appears in the response body. A guard that works in the service but is
      bypassed by the route protects nobody.
- [x] **Report affordances present** on both model-facing surfaces
      (`ReportResult` in `PlantDetailScreen` and `AddPlantScreen`).
- [x] **Rejections are logged without PII** — reasons plus a 120-char excerpt,
      never the full output or the photo (`log_rejection`).

## Not done

- **Re-taking the two evidence screenshots on a dev build** (plan Phase 4
  item 3). Blocked: this machine has no Apple signing certificate, so
  `npm run ios` cannot build. The app runs via a direct `xcodebuild`
  simulator build, but the advisor path needs a reachable backend and a
  seeded plant to reproduce the exact card. The behaviour is pinned by the
  golden-path tests in `restyle.test.ts` and by the route-level tests in
  `test_advice_route_grounding.py` instead — the wired server path is now
  covered, so what a screenshot would add is confirmation of the *rendered*
  card. Worth redoing once signing is set up.
- **On-device restyle has never run on real hardware.** The simulator has no
  Apple Foundation Models backing `plant-id`, so `isAvailable()` is false
  there and `gnomeVoice` always returns the flat fallback. Every mobile guard
  test drives `driftReasons` directly or mocks `generate`. The guard logic is
  covered; the native round trip is not.
- **Guard parity is maintained by hand.** `CARE_STEMS` and the number-word
  tables exist in both TypeScript and Python. They are tested against the same
  fixtures, so a divergence shows up as a failing test on one side only — but
  nothing mechanically keeps them in step.
