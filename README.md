# PlantAdvocate

*A plant care assistant that knows what it's talking about.*

> **Name vs. mascot:** the product is **PlantAdvocate**. The gnome (🧙) is its
> mascot and the voice of its advice — "Ask the Gnome" — not the product name.
> Some internal identifiers, repo paths, and the Fly.io app still use the
> original `garden-gnome` name; that's deliberate and harmless.

## What it is

PlantAdvocate is a houseplant care app: a React Native (Expo) mobile client
backed by a FastAPI service. You sign in, add your plants, log care events
(watering, fertilizing, misting, …), and get care advice, photo-based species
identification, and photo symptom diagnosis — all tailored to the specific
species and that plant's own history. It's built for plant owners who want more
than a generic watering-reminder app, and — at the systems level — as a study
in building AI features that give *reliable* answers instead of merely
plausible-sounding ones.

## Why it's interesting

**The AI never reasons from scratch.** Every species has a curated database
record — light needs, humidity/temperature ranges, soil type, toxicity, and a
per-care-type schedule (water every 7–10 days, fertilize every 30–60, …). When
the app generates advice, identifies a plant, or diagnoses a photo, the model is
handed those facts plus the plant's actual care log and instructed — explicitly
in the system prompt — to answer *only* from what it's given, never inventing
care requirements or diagnoses the data doesn't support.

This matters because plant-care misinformation is exactly what an ungrounded
model produces confidently and wrong: a hallucinated watering interval or an
invented pest diagnosis looks just as authoritative as a correct one. Grounding
the model in a structured, human-reviewed knowledge base trades a little
flexibility for real trustworthiness — the app can always point to *why* it said
something. Two concrete expressions of that principle:

- **Advice is a hybrid.** A free, deterministic rule-based engine handles
  routine schedule advice (it does the interval math against the species DB and
  the care log); an LLM is invoked only for open-ended symptom diagnosis, the
  part that actually needs reasoning.
- **Photo identification is catalog-constrained.** The vision model may only
  suggest species that exist in the curated catalog — so it can never propose a
  plant the app has no real care data for.

**On-device AI where it counts.** The mobile app runs generative models
*locally* — Apple Foundation Models (iOS 26) and Gemini Nano via ML Kit
(Android) — for two features, with no network round-trip and no per-call cost:

- **Photo species ID** in the Add Plant flow (the model's guess is then
  fuzzy-matched against the catalog before anything is offered).
- **The Gnome's voice** — the rule-based advisor still produces the factual
  answer; the on-device model only *restyles* it in a warm, whimsical gnome
  voice. A drift guard compares the restyled text against the source facts and
  falls back to the plain text if the model adds any number or care action that
  wasn't in the input, so tone can never change substance. On devices without
  on-device AI, advice simply speaks plainly.

## Architecture

```
   ┌─────────────────────────────┐        HTTPS / JSON + Bearer JWT
   │  Mobile app (Expo / RN)     │ ───────────────────────────────────┐
   │  • Sign in with Apple/Google│                                     │
   │  • SecureStore tokens       │ ◀───────────────────────────────┐  │
   │  • On-device AI:            │                                  │  ▼
   │      photo ID (FoundationML │                          ┌───────────────────────┐
   │      / Gemini Nano)         │                          │  FastAPI backend       │
   │      gnome-voice restyle    │                          │  (Fly.io, region iad)  │
   └─────────────────────────────┘                          │                        │
                                                            │  Auth: JWT access +    │
                                                            │  rotating refresh,     │
                                                            │  Apple/Google verify   │
                                                            │  ┌──────────────────┐  │
                                                            │  │ SQLite (SQLModel)│  │
                                                            │  │ on a persistent  │  │
                                                            │  │ volume; Alembic  │  │
                                                            │  │ migrations       │  │
                                                            │  └──────────────────┘  │
                                                            │  ┌──────────────────┐  │
                                                            │  │ advisor.py ──────┼──┼─▶ stub / Claude
                                                            │  │ vision.py  ──────┼──┼─▶ stub (not enabled)
                                                            │  └──────────────────┘  │
                                                            └───────────────────────┘
```

The species/schedule tables are the single source of truth. `advisor.py` and
`vision.py` are the only modules that talk to a *server-side* model, and both
are swappable via one environment variable. Every non-species endpoint is
scoped to the signed-in user.

## Tech stack

- **Backend:** Python, FastAPI, SQLModel/SQLAlchemy over SQLite, Pydantic +
  pydantic-settings, Alembic (migrations), PyJWT + cryptography (auth), slowapi
  (rate limiting), httpx, Anthropic SDK, Uvicorn. Containerized for Fly.io;
  also packageable as a standalone Windows `.exe` (PyInstaller).
- **Mobile:** TypeScript, React Native + Expo (SDK 57), React Navigation,
  TanStack React Query, React Native Paper, Axios. Auth via
  `expo-apple-authentication` + `@react-native-google-signin/google-signin`,
  tokens in `expo-secure-store`. Notifications, Camera, Image Picker. A custom
  Expo native module (`modules/plant-id`) bridges Apple Foundation Models
  (Swift) and Gemini Nano / ML Kit GenAI (Kotlin).
- **Server-side AI:** Anthropic Claude API (cloud) for text advice; no hosted
  vision backend (server photo diagnosis ships disabled). **On-device AI:**
  Apple Foundation Models (iOS 26+) / Gemini Nano (AICore Android) — no key,
  no network, no cost.

## Key features

**Accounts & privacy**
- **Social sign-in only** — Sign in with Apple and Google; no passwords. Short
  lived JWT access tokens + rotating refresh tokens with reuse detection
  (a replayed token revokes the whole family).
- **Per-user data isolation** — every plant, environment, and care log belongs
  to its owner; other users' resources return 404, not 403.
- **In-app account deletion** (`DELETE /me`) — wipes all user data and revokes
  the user's Apple session (App Store Guideline 5.1.1(v)).
- **Opt-in anonymized census** — aggregate species/care-health data for
  environmental analysis, off by default and stripped of all identifiers
  (no nicknames, no addresses, no precise geo, rotated environment references).

**Care**
- **Species catalog** — 400+ curated houseplant species with light/humidity/
  temperature ranges, soil, toxicity, and per-care-type schedules; an
  extensible key-value traits table; provenance + review status for entries
  sourced beyond the original hand-written set.
- **Plant inventory & environments** — plants live in per-user growing
  environments (home, balcony, greenhouse, …) and can be transferred between a
  user's own environments with a full chain-of-custody record, keeping a stable
  UUID and their entire care history.
- **Care logging & timeline** — quick logging across 8 care types with a
  confirmation snackbar, full chronological history with gap-from-previous per
  care type, and per-type stats (actual vs. scheduled interval).
- **Ask the Gnome** — grounded care advice (`/plants/{id}/advice`) with optional
  free-text symptom input; rule-based by default, LLM for symptom diagnosis,
  restyled in the gnome's voice on-device where available.
- **Photo diagnosis** — `/plants/{id}/diagnose-photo` reasons over an uploaded
  photo plus the grounding facts and auto-logs the result to the timeline.
- **Photo identification** — on-device species ID in Add Plant, catalog
  constrained, with tap-to-select candidates.
- **Care reminders** — local notifications when plants come due, based on each
  species' schedule and the plant's real history; per-care-type toggles; plants
  due the same day share one notification.
- **Streaks, badges & onboarding** — light engagement touches and a first-run
  guide for empty accounts.

## Setup

### Backend (FastAPI)

See **[`garden-gnome/README.md`](garden-gnome/README.md)** for the full backend
guide (auth configuration, Alembic migrations, the test suite, deployment). In
short:

```bash
cd garden-gnome
python -m venv .venv
source .venv/bin/activate        # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

cp .env.example .env             # then fill JWT_SECRET + FERNET_KEY (required)
alembic upgrade head             # create/upgrade the schema (Alembic owns it)
python -m app.data.seed          # populate the curated species catalog (idempotent)
uvicorn app.main:app --reload
```

- Interactive API docs: http://127.0.0.1:8000/docs
- Built-in manual test console (not the product UI): http://127.0.0.1:8000/ui/

By default the server runs entirely offline with deterministic rule-based
advice. Model-backed features are opt-in via `.env` (`ADVISOR_BACKEND`,
`ADVISOR_SYMPTOMS_BACKEND`, `VISION_BACKEND` — see the backend README).

### Hosted backend (Fly.io)

Live at **https://garden-gnome-api.fly.dev** (app `garden-gnome-api`, region
`iad`). SQLite lives on a persistent 1 GB volume (`gnome_data` → `/data`);
Alembic migrations and species seeding run on boot; the machine auto-stops when
idle, so the first request after a lull cold-starts in a second or two. Redeploy
with `flyctl deploy` from `garden-gnome/`. Full deploy notes (secrets by name,
inline Apple key, verification checks) are in the backend README.

### Mobile app (Expo)

```bash
cd mobile
npm install
npm run start        # press w for the web preview
```

The app defaults to the hosted backend (`src/api/client.ts`); iOS release builds
require HTTPS to non-localhost hosts. In development and `preview` builds a
**Settings → Backend connection** card lets you point at a local server; it's
hidden in production.

> **Expo Go won't run the full app.** PlantAdvocate uses a custom native module
> (on-device AI) and native sign-in, neither of which exists in Expo Go. Use an
> **EAS build** — `eas build --profile development --platform ios` for the dev
> client, or `--profile preview` for a standalone internal build. Sign in with
> Apple additionally requires a real device. The **web preview** renders the UI
> and the login gate but can't perform native sign-in or on-device AI. Build
> profiles live in `mobile/eas.json`.

## Project status / roadmap

| Phase | Status |
|---|---|
| 1. Plant inventory + curated care database | ✅ Done |
| 2. LLM reasoning layer on top of the care database | ✅ Done |
| 3. Photo diagnosis + on-device photo identification | ✅ Done |
| 4. Proactive scheduling & notifications | ✅ Done |
| 5. Gnome character voice (on-device restyle) | ✅ Done |
| 6. User accounts, data isolation & account deletion | ✅ Done (backend + client) |
| 7. Cloud deployment (Fly.io) | ✅ Done |
| — Catalog expansion pipeline (Perenual + review) | ✅ Done |
| Next: App Store submission (TestFlight → review) | 🔜 In progress |

Product principle carried through every phase: the free tier stays genuinely
useful — basic care guidance is never paywalled.

## Repository layout

```
garden-gnome/     FastAPI backend — API, auth, SQLite/Alembic, AI services,
                  Fly.io deploy config, tests.  See its README.
mobile/           Expo / React Native app — screens, auth, on-device AI native
                  module (modules/plant-id), reminders, streaks, onboarding.
garden-gnome-auth-plan.md   The user-accounts implementation plan and the
                  recorded design decisions it was built against.
```
