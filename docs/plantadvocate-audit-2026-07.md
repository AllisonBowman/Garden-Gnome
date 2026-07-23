# PlantAdvocate — System Audit (what the code does)

*Snapshot: 2026-07-23, branch `claude/plant-advocate-screenshots-xxt8ed`.*

A behavioral and architectural map of PlantAdvocate as it exists today — what
each part actually does, not what it should do. Product name **PlantAdvocate**;
internal codename **Garden Gnome** persists in repo paths, the Fly app, and the
API title. Three components: a FastAPI backend (`garden-gnome/`), an
Expo/React Native app (`mobile/`), and a static marketing site (`site/`).

**Core design principle** (stated throughout the code): a curated species
database is authoritative ground truth; models interpret those facts but never
invent care requirements or diagnoses.

---

## 1. Shape of the system

| Layer | Stack | Role |
|---|---|---|
| Backend | FastAPI + SQLModel over SQLite, Alembic, PyJWT, slowapi, Anthropic SDK | Accounts, plant/species/environment data, rule-based advice, census |
| Mobile | Expo SDK 57 / RN 0.86, React Query, React Native Paper | The product users touch; thin views over the API + two on-device AI layers |
| On-device AI | Apple Foundation Models (iOS 26) / Gemini Nano (Android) via a custom Expo module | Photo species ID + gnome-voice restyle, no network |
| Site | 15 static HTML pages | Public marketing/positioning |
| Deploy | Fly.io container (scale-to-zero) + a Windows `.exe` (PyInstaller) | Hosted API + a standalone desktop build |

Data flows through the backend for everything except the two on-device AI
features. The app is essentially offline-intolerant for core data (plants,
species, environments, census fail to a "Could not reach the backend" state),
while reminders, streaks, and on-device AI degrade gracefully.

---

## 2. Backend — API surface

Routers registered in `app/main.py:54-59`. CORS is restricted to
`localhost`/`127.0.0.1` origins (`app/main.py:47-52`). Only the four auth POST
routes are rate-limited.

**Auth (`/auth`, `/me`)** — `POST /auth/apple`, `POST /auth/google` (verify
provider token, upsert user, issue tokens; rate-limited 10/min), `POST
/auth/refresh` (rotate; 30/min), `POST /auth/logout` (revoke one token, 204),
`GET/PATCH/DELETE /me` (profile; PATCH sets only `display_name` +
`census_opt_in`; DELETE hard-deletes the account).

**Plants (`/plants`, auth required, all owner-scoped)** — CRUD; `POST /` opens a
stewardship record and writes a day-zero intake CareLog; `/transfer` moves a
plant between owned environments preserving `plant_uuid`; `/stewardship` returns
chain-of-custody; `/logs` GET/POST care events; `/timeline` and
`/timeline/summary` compute per-care-type interval stats (actual vs scheduled);
`POST /advice` returns care advice; `POST /diagnose-photo` runs diagnosis
(currently stub) and **only logs to the timeline when `backend != "stub"`**
(`plants.py:434`).

**Species (`/species`) — NO AUTH on any route**, including writes: `GET /`,
`GET /{id}`, `POST /` (create), `POST /bulk`, `POST /generate` (LLM draft),
`POST /identify-photo`.

**Environments (`/environments`, auth, owner-scoped)** — CRUD; DELETE 409s if
the environment still holds plants or has stewardship history.

**Census (`/census`, auth)** — `GET /summary` (caller's own garden),
`GET /export` (anonymized, opted-in users only), `POST /sync` (push to
`CENSUS_API_URL`).

**Misc** — `GET /` health, `GET /ai/status` (unauth; reports advisor/vision
backends, vision always `ready:false`), `/ui` static dev page.

Ownership checks return **404, not 403**, for other users' rows (no id probing).

---

## 3. Backend — auth, data model, config

**Auth.** Sign-in upserts by `(provider, provider_sub)`, falls back to matching
verified email, else creates a User + a default "My Home" environment. Apple and
Google identity tokens are verified against provider JWKS (RS256, audience/issuer
checks, nonce for Apple, `email_verified` for Google). Access tokens are
short-lived HS256 JWTs (default 30 min, `iss="plantadvocate"`); refresh tokens
are opaque 256-bit strings stored only as sha256 hashes (default 90 days) with
**family-based rotation and reuse detection** (presenting a revoked token nukes
the whole family). `DELETE /me` revokes Apple sessions, revokes all tokens, then
**hard-deletes** the user (cascade removes identities, tokens, plants, logs,
stewardship).

**Data model** (`app/models/models.py`). Core entities: `User`
(UUID PK, `deleted_at` soft-delete column, `census_opt_in`), `AuthIdentity`
(Fernet-encrypted Apple refresh token), `RefreshToken` (hash + `family_id`),
`Species` (care facts + provenance/review trail), `CareSchedule` (per-care-type
interval), `SpeciesTrait`, `Environment` (owner + coarse location; `lat`/`lng`
kept server-side only), `Plant` (stable `plant_uuid`, owner, intake snapshot),
`CareLog`, `StewardshipRecord` (chain-of-custody, separate from location).

**Config & boot** (`app/config.py`, `app/main.py`). `JWT_SECRET` and
`FERNET_KEY` gate boot (missing → fail fast). Providers are optional and only
error (503) when actually used unconfigured. Startup runs Alembic migrations to
head, a dev-only seed (`GG_DEV_SEED`), and prints vision status. `.env` is loaded
before router imports because services read backend env vars at import time.

**Rate limiting** — slowapi, per-IP; only `/auth/*` POSTs (10/min sign-in,
30/min token). Everything else is unlimited.

**Census export** — opted-in, non-deleted users only. Per plant: `plant_uuid`,
species id, maturity, coarse environment (city/region/country — **never
lat/lng**), stewardship chain with **per-export rotated** environment refs, care
history timestamps, initial condition. No nicknames, notes, emails, or user ids.

---

## 4. Backend — AI services (current state)

The Ollama backend was **removed entirely** (commit `87fb0f4`); `git grep ollama`
over `app/` finds nothing but a test asserting its absence. Each service selects
an implementation from an env-keyed dict, so provider swaps stay config-only.

- **Advisor** (`advisor.py`): backends `{stub, anthropic}`. Stub advice is
  fully deterministic — one emoji line per care type computed from the schedule
  and last log ("hold off", "inside window", "likely due"), a toxicity warning,
  and, if symptoms were entered, a note that symptom diagnosis needs the AI
  advisor. `ADVISOR_SYMPTOMS_BACKEND` can route only symptom diagnosis to Claude
  while routine advice stays free/stub. The system prompt labels species facts
  authoritative and forbids inventing care requirements. No "gnome" persona here.
- **Vision** (`vision.py`): **stub-only** — `_BACKENDS`/`_IDENTIFY_BACKENDS`
  each register just `stub`; `vision_status()` always returns `ready=False`.
  Stub diagnosis returns friendly gnome-voice copy ("📷 Photo received! The
  Gnome's photo check-ups aren't switched on yet…"), logging the byte count
  server-side (commit `ce01bf4`). Stub identify returns no candidates.
- **Catalog** (`catalog.py`): shares `ADVISOR_BACKEND`; stub returns a
  fill-in template, Anthropic drafts strict JSON species profiles.

The hosted Fly app runs `ADVISOR_BACKEND=stub` / `VISION_BACKEND=stub`.

---

## 5. Mobile — what the app does

**Structure** (`App.tsx`). Auth gate → 5-tab navigator (Plants 🌱, Species 📚,
Environments 🌍, Census 📊, Settings ⚙️). Signed-out users see `LoginScreen`; a
first-run empty-garden check shows a 3-slide onboarding overlay.

- **Plants / PlantDetail** — list of plant cards (light/toxicity chips, streak
  badges header); detail has a care-log button grid (six care types, each logs +
  reschedules reminders), the **Ask the Gnome** advice card, the **Photo
  diagnosis** card, a care guide, and recent logs.
- **AddPlant** — nickname + species (via on-device photo ID or manual search) +
  optional environment + location + initial-condition control.
- **Species / SpeciesDetail** — searchable catalog; read-only detail with
  stats, care notes, recommended schedule, traits.
- **Environments** — list + create modal (name, type, coarse location).
- **Census** — the caller's own totals, env-type breakdown, top species, and a
  "Sync now" button.
- **Settings** — account (sign out, destructive delete-account confirm), a
  gated backend-URL override, six per-care-type reminder switches, About &
  Support links.

**Two AI features, two different stacks:**

- **Species identification is 100% on-device, no server call.** `modules/plant-id`
  runs Apple Foundation Models + Vision (iOS 26, weak-linked, `@available`-gated)
  or Gemini Nano/ML Kit (Android). It returns free text, which
  `src/photoId/identify.ts` grounds against the catalog via
  `fuzzyMatch.ts` (Sørensen–Dice bigrams; tiers `confident` ≥0.6 /
  `plausible` ≥0.42 / `none`). Only real catalog rows are ever offered; the
  manual-search fallback is always present. The top candidate auto-selects. A
  **dev-only `debugRawText`** line surfaces the raw model text in dev/preview
  builds (gated by `__DEV__ || EXPO_PUBLIC_SHOW_BACKEND_OVERRIDE`).
- **Photo diagnosis is a server call** to `POST /plants/{id}/diagnose-photo`
  (190 s timeout). Today the server returns a stub, so the card shows friendly
  copy and a **"diagnosis not enabled yet"** chip.
- **Ask the Gnome** fetches rule-based advice from the server, then restyles it
  **on-device** via the same native module. `driftsFromFact` discards the
  restyle (falling back to flat text) if it introduces a number or care verb not
  in the source, or runs empty/too long. The badge reads
  **"rule-based • gnome voice"** when styling succeeded.

**Client & auth.** Base URL defaults to the Fly app, overridable in Settings
(gated). Tokens live in `expo-secure-store`; a single-flight 401→refresh
interceptor replays the original request and force-signs-out on refresh failure.
Apple/Google sign-in are native-only.

**Config.** `app.json` version **1.0.0**, bundle `com.allisonbowman.plantadvocate`.
`eas.json` now pins `ios.image: "sdk-57"` on all three profiles; dev/preview set
`EXPO_PUBLIC_SHOW_BACKEND_OVERRIDE=1` (exposing the backend-URL card and
`debugRawText`), production does not. **No test infrastructure exists in
`mobile/`** (no jest).

**Client-side extras.** Reminders (native-only) compute one batched daily
notification from care schedules; streaks/badges are derived from care logs with
no storage.

---

## 6. Data, catalog, and pipeline

**Catalog** — `species_catalog.json`, **129 species**, each `{species, schedules,
traits}`. Broader than "houseplants": classic foliage plants, culinary herbs,
vegetables, fruit, and annual/perennial flowers (hence the `direct`-light skew).
Seeding (`python -m app.data.seed`) migrates first, then inserts idempotently by
scientific name.

**Expansion pipeline** (`app/data/expansion/`, offline, never touched by the
running app) — grows the catalog toward ~1,900 species: `fetch_targets` →
`run_expansion` (tiered: Perenual API → LLM fallback → validation, with JSONL
checkpoint/resume and a care-guide circuit breaker) → `validate` /
`find_near_duplicates` → `sample` (weighted toward top houseplants) →
`admit_queue` (soft-flag rows admitted as `needs_review`, hard-flag held) →
human review → `apply_review` (verify/correct/reject against NC State / Missouri
Botanical Garden). Every row carries `source` + `review_status` provenance.
Requires a paid `PERENUAL_API_KEY` or mock fixtures.

**Migrations** (Alembic, SQLite batch mode) — `0001_baseline` (full schema),
`0002_auth` (user/identity/refresh tables + backfill plants to `dev@local`),
`0003_census_opt_in`, `0004_environment_owner`. `run_migrations()` stamps
pre-Alembic DBs at baseline before upgrading, so existing volumes adopt Alembic
without recreation.

**Deployment** — Fly.io container (`garden-gnome-api`, iad, scale-to-zero,
256 MB, SQLite on a mounted volume; secrets via `flyctl`), plus a Windows
`.exe` (PyInstaller) that self-seeds and serves a local `/ui`. Hosted config is
`ADVISOR_BACKEND=stub` / `VISION_BACKEND=stub`.

**evals/** — the pre-build device-test harness (Python mirror of `fuzzyMatch.ts`
+ parity fixtures, manifest linter, device-run replay scorer, offline selftest).

---

## 7. Observations worth a second look

These are factual observations from the audit, not blockers — flagged because
they're places where the code's behavior may surprise, or diverges from what's
stated elsewhere.

1. **The species router is entirely unauthenticated — including writes.**
   `POST /species/`, `/bulk`, `/generate`, and `/identify-photo` require no
   token. Anyone who can reach the server can mutate the catalog. Given the app
   fetches the catalog read-only and the deployment is scale-to-zero on a public
   URL, this is the most notable access-control gap.
2. **`DELETE /me` hard-deletes despite a `deleted_at` soft-delete column
   existing** and being honored by sign-in / `get_current_user`. The column is
   used for detection but deletion is a hard cascade — intentional per the code,
   but the half-present soft-delete machinery invites confusion.
3. **The marketing site describes a different product than the code runs:**
   - `privacy.html` says photos are "transmitted to our servers for processing"
     by "third-party AI service providers" — but species ID is **on-device** and
     server vision is stubbed off. The stated data-flow contradicts the design.
   - `pricing.html` advertises paid tiers (Bloom $6/mo, Estate $12/mo). There is
     **no billing, subscription, or entitlement code** anywhere in the backend.
4. **Vision is `ready:false` in every code path.** Both photo endpoints always
   return friendly not-enabled copy; the stub diagnosis is deliberately kept off
   the plant timeline (`plants.py:434`) so placeholder text never feeds back into
   future advisor prompts.
5. **The app surfaces raw backend identifiers** to users — `plant_uuid` in the
   detail header, environment `uuid` on cards.
6. **No automated tests on the mobile side.** The pure, testable matcher
   (`fuzzyMatch.ts`) has an offline Python mirror with parity fixtures in
   `evals/`, but no jest suite yet asserts them in-app.

---

*Method: three parallel read-only explorations of the backend, mobile, and
data/deployment layers, cross-checked against the working tree at the snapshot
commit. Line references point to that snapshot.*
