# PlantAdvocate — backend 🌱

FastAPI service for **PlantAdvocate**, an AI-powered plant care assistant. The
curated `Species` table is the authoritative care-knowledge source; the LLM /
vision layers reason *on top of* it so advice is grounded, not hallucinated.
(The gnome is the app's mascot; some identifiers keep the original
`garden-gnome` name.) The product-level overview is in the
[repo root README](../README.md).

This service is multi-user and deployed: social sign-in, per-user data
isolation, Alembic-managed SQLite on a persistent volume, and a live Fly.io
deployment. See the sections below.

## What's here
- Curated **species catalog** (400+) with per-care-type schedules, traits, and
  provenance/review status.
- **Plant inventory, environments, care logging, timeline & stats**, all scoped
  to the signed-in user.
- **Grounded advice** (`/plants/{id}/advice`) and **photo diagnosis /
  identification** — pluggable backends (`stub` / Anthropic for advice;
  vision ships stub-only, see below).
- **User accounts & auth** — Apple + Google sign-in, rotating refresh tokens,
  account deletion, per-IP rate limiting (see below).
- **Alembic** migrations and a **pytest** suite.

## Quickest way to try it: GardenGnome.exe

A standalone Windows executable is included — no Python, no WSL, no setup.

1. Double-click `GardenGnome.exe` (or run it from PowerShell/cmd).
2. A console window opens and your browser opens automatically to the test
   console at http://127.0.0.1:8000/ui/.
3. To stop, close the console window (or press Ctrl+C in it).

Data is stored in `garden_gnome.db`, created next to the .exe the first time
it runs — it persists across restarts. It loads a `.env` next to the .exe
automatically.

> **Note:** now that the API is multi-user, the app **won't boot without**
> `JWT_SECRET` and `FERNET_KEY` in that `.env` (see the auth section below).
> The `.exe` path predates the accounts work and the Fly.io deployment; for a
> shared backend, the hosted API is the primary target. To enable the Claude
> advice backend beyond the stub, add the `ADVISOR_BACKEND` variable as in
> `.env.example`.

This .exe bundles everything needed to run the app and is independent of the
Python dev setup below, which is only needed if you're changing code.

### Rebuilding the .exe after code changes
```powershell
# one-time: install a real Windows Python (not the Microsoft Store stub) and
# set up the build venv
winget install --id Python.Python.3.12 -e
python -m venv .venv-win
.\.venv-win\Scripts\pip install -r requirements.txt pyinstaller

# every time you change code:
.\build_exe.ps1
```

## Setup (Python dev environment, for changing code)

```bash
# from the project root, in your WSL2 Ubuntu terminal
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## User accounts & auth (PlantAdvocate)

The API is multi-user: every non-species endpoint requires a Bearer access
token obtained via Sign in with Apple or Google Sign-In (`POST /auth/apple`,
`POST /auth/google`), refreshed via rotating refresh tokens
(`POST /auth/refresh`). Accounts are deletable in-app via `DELETE /me`
(App Store 5.1.1(v) — also revokes the user's Apple session). `/auth/*`
endpoints are rate-limited per IP.

### Required configuration (.env)

Copy `.env.example` to `.env` and fill these — the app **refuses to boot**
without the first two. Variable names only; generate/collect your own values:

| Variable | What it is |
|---|---|
| `JWT_SECRET` | HS256 signing secret for access tokens (32+ random bytes, hex) |
| `FERNET_KEY` | Encrypts stored Apple refresh tokens at rest |
| `APPLE_BUNDLE_ID` | The iOS app's bundle identifier |
| `APPLE_TEAM_ID` | Apple Developer team id |
| `APPLE_KEY_ID` | Sign in with Apple key id (from the `.p8` filename) |
| `APPLE_PRIVATE_KEY_PATH` | Path to the `.p8`, e.g. `secrets/AuthKey_XXXX.p8` (gitignored) — for local dev |
| `APPLE_PRIVATE_KEY` | The `.p8` PEM contents **inline** (used instead of the path where there's no file on disk, e.g. Fly). Literal `\n` is normalized to real newlines. Inline wins if both are set. |
| `GOOGLE_CLIENT_ID` | Google OAuth iOS client id |
| `ADVISOR_BACKEND` | `stub` (default) / `anthropic` — see below |
| `VISION_BACKEND` | `stub` (default and only value — no hosted vision backend) |
| `ADVISOR_SYMPTOMS_BACKEND` | Backend for free-text symptom diagnosis only (hybrid) |
| `RATE_LIMIT_SIGNIN` / `RATE_LIMIT_TOKEN` | Optional overrides, e.g. `10/minute` |

Provider variables are only needed once real Apple/Google sign-ins are
exercised; the test suite runs fully mocked without them.

### Database migrations (Alembic)

The schema is owned by Alembic — `create_all` is no longer used. The server
runs migrations automatically at startup (pre-Alembic databases are detected
and stamped at the baseline first). To migrate manually:

```bash
alembic upgrade head     # bring the DB at DATABASE_URL to the latest schema
```

New schema changes: `alembic revision --autogenerate -m "..."`, review the
generated file, commit it. Never edit applied revisions.

### Running the test suite

```bash
pip install -r requirements-dev.txt
python -m pytest
```

On the Windows dev box the venv is `.venv-win` (Windows layout — `Scripts`,
not `bin`), so the interpreter is addressed directly:

```bash
.venv-win/Scripts/python.exe -m pytest
```

`pytest.ini` pins `testpaths = tests`, so anything added outside `tests/`
is not collected.

## Seed the care database

```bash
python -m app.data.seed
```

This populates the curated catalog (400+ species) from `species_catalog.json`.
Idempotent — safe to run repeatedly (skips species already present) and it
migrates the DB to head first, so it's also what the container runs on boot.

## Run the API

```bash
uvicorn app.main:app --reload
```

- Interactive docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/
- **Test console (GUI):** http://127.0.0.1:8000/ui/ — a single-page test
  harness (species browser, plant creation with intake fields, care logging,
  timeline/summary viewer, advice, photo diagnosis upload). Not the product
  UI, just a manual testing tool. Served by the same FastAPI process, no
  extra setup or dependencies.

## Deploy (Fly.io)

The API is hosted at **https://garden-gnome-api.fly.dev** (app `garden-gnome-api`, org `personal`, region `iad`). The SQLite database lives on a persistent volume (`gnome_data` → `/data`), selected via the `DATABASE_URL` env var (`app/db/database.py` falls back to the local cwd-relative file when unset, so local dev is unchanged). On every boot the container runs Alembic migrations and seeds the species catalog — both idempotent, so a redeploy never duplicates data or skips a schema change. (Migrations run at boot rather than as a Fly `release_command` because release machines don't mount the volume — boot-time is the correct place for volume-backed SQLite.)

**Secrets** are set with `fly secrets set`/`import` (never committed). The two required ones (`JWT_SECRET`, `FERNET_KEY`) gate boot; the Apple/Google provider vars enable sign-in; on Fly the Apple key is supplied inline via `APPLE_PRIVATE_KEY` (there's no `.p8` file in the container). The hosted app runs `ADVISOR_BACKEND=stub` / `VISION_BACKEND=stub` (no LLM key in the container) — deterministic rule-based advice; upgrade later by setting `ADVISOR_BACKEND=anthropic` + `ANTHROPIC_API_KEY` and redeploying.

**Verify a deploy from outside:** `GET /` → 200; `GET /plants/` → 401 (auth enforced); `POST /auth/google` with a garbage token → 401 (not 503 — a 503 would mean `GOOGLE_CLIENT_ID` didn't load).

```bash
# redeploy after code changes (config: Dockerfile + fly.toml)
flyctl deploy

# tail production logs
flyctl logs

# status / scale / volume info
flyctl status
flyctl volumes list
```

The machine auto-stops when idle (`auto_stop_machines = "stop"`), so the first request after a quiet period cold-starts in a couple of seconds. Keep it at exactly one machine — SQLite on a volume cannot be shared across machines.

## Project layout

```
app/
  main.py            # FastAPI app + router wiring, lifespan (migrate + seed)
  config.py          # pydantic-settings; required secrets fail fast at boot
  deps.py            # get_current_user (Bearer JWT -> active User)
  rate_limit.py      # slowapi limiter for /auth/*
  db/database.py     # SQLite engine, session dependency, run_migrations()
  models/
    models.py        # Species, CareSchedule, SpeciesTrait, Plant, CareLog,
                     # Environment, User, AuthIdentity, RefreshToken
    schemas.py       # request/response schemas
  routers/
    species.py       # read-only species DB + /species/identify-photo
    plants.py        # plant CRUD + care logs + advice + photo diagnosis
    environments.py  # per-user environments
    census.py        # opt-in anonymized aggregate/export/sync
    auth.py          # sign-in (apple/google), refresh, logout, /me, DELETE /me
  services/
    advisor.py       # text advice service (stub/anthropic)
    vision.py        # photo diagnosis + identification (stub only)
    tokens.py        # access JWTs + rotating refresh tokens (reuse detection)
    oauth/           # apple.py, google.py, jwks.py — provider verification
  data/
    seed.py          # curated seed data (migrates then seeds)
    expansion/       # Perenual catalog-expansion pipeline + review
alembic/             # migration environment + versions/
tests/               # pytest suite (models, tokens, auth API, deletion, ...)
Dockerfile, fly.toml # Fly.io deployment
```

## Quick test

> **Auth note:** species endpoints are public, but plant/care/advice endpoints
> now require a `Authorization: Bearer <access_token>` header (obtained via
> `/auth/apple` or `/auth/google`). The plant examples below are historical —
> against the current API they return 401 without a token. The
> [interactive docs](http://127.0.0.1:8000/docs) are the easiest way to
> exercise authenticated routes.

```bash
# list the seeded species (public)
curl http://127.0.0.1:8000/species/

# add a plant (species_id 1 = Snake Plant)
curl -X POST http://127.0.0.1:8000/plants/ \
  -H "Content-Type: application/json" \
  -d '{"nickname": "Sir Hiss", "species_id": 1, "location": "office desk"}'

# add a plant with intake condition (auto-logged as its first timeline entry)
curl -X POST http://127.0.0.1:8000/plants/ \
  -H "Content-Type: application/json" \
  -d '{"nickname": "Sir Hiss", "species_id": 1, "location": "office desk",
       "soil_moisture_at_acquisition": "moist",
       "leaf_condition_at_acquisition": "yellowing",
       "intake_notes": "a couple unopened new leaves"}'

# log a watering for plant 1
curl -X POST http://127.0.0.1:8000/plants/1/logs \
  -H "Content-Type: application/json" \
  -d '{"action": "water", "notes": "soil was bone dry"}'

# get care advice (all care types, not just watering)
curl -X POST http://127.0.0.1:8000/plants/1/advice

# get advice with a free-text symptom (LLM backends diagnose against the
# species facts + history; stub backend acknowledges but can't diagnose)
curl -X POST http://127.0.0.1:8000/plants/1/advice \
  -H "Content-Type: application/json" \
  -d '{"symptoms": "leaves are turning yellow and mushy at the base"}'

# view species detail with care schedules and traits
curl http://127.0.0.1:8000/species/1

# full chronological care history, with gap-from-previous per care type
curl http://127.0.0.1:8000/plants/1/timeline

# narrow to a date range (e.g. "this time last summer")
curl "http://127.0.0.1:8000/plants/1/timeline?since=2025-06-01&until=2025-08-31"

# per-care-type stats: count, last logged, actual vs scheduled interval
curl http://127.0.0.1:8000/plants/1/timeline/summary

# diagnose a plant from a photo (auto-logged to its timeline)
curl -X POST http://127.0.0.1:8000/plants/1/diagnose-photo \
  -F "photo=@leaf.jpg;type=image/jpeg" \
  -F "notes=lower leaves looking droopy"

# identify which catalog species a photo shows (used by the mobile Add Plant flow)
curl -X POST http://127.0.0.1:8000/species/identify-photo \
  -F "photo=@mystery-plant.jpg;type=image/jpeg"
```

## Care model
Care events are modelled generically via `CareType` (water, fertilize, mist,
prune, repot, rotate, clean, other). Each species has a `CareSchedule` row per
care type with min/max interval days, so the advisor reasons across **all** care
types equally — not just watering.

`SpeciesTrait` is a key-value extension table for additional species parameters
(growth rate, propagation method, native region, etc.) without schema migrations.

`/advice` accepts an optional `symptoms` free-text field. LLM backends diagnose
it against the species facts and care history (grounded, not guessed). The stub
backend acknowledges the symptom but cannot diagnose free text.

`POST /plants/` accepts optional intake condition fields (`soil_moisture_at_acquisition`,
`leaf_condition_at_acquisition`, `pest_observed_at_acquisition`, `intake_notes`). If any
are provided, they're auto-logged as the plant's first `CareLog` entry (action=`other`),
so the intake snapshot becomes day-zero of its `/timeline`.

## Photo diagnosis & identification (Phase 3)
`POST /plants/{id}/diagnose-photo` accepts a JPEG/PNG/WebP image (max 8MB) plus
optional free-text `notes`, and reasons over it the same way `/advice` reasons
over symptoms: grounded in the species facts, not invented. The diagnosis is
auto-logged to the plant's timeline.

`POST /species/identify-photo` accepts the same image types and asks the vision
backend to name the species — constrained to the curated catalog, so it can only
suggest plants the app actually has care data for. Returns candidates (most
likely first) plus the model's observation text; the mobile Add Plant flow
renders these as tap-to-select chips. Uses the same `VISION_BACKEND` switch.

**No hosted vision backend is configured, on purpose.** `VISION_BACKEND`
knows only `stub`: both endpoints answer with a friendly not-enabled message
(and, for identification, no candidates). Photo species ID runs *on-device*
in the mobile app (Apple Foundation Models / Gemini Nano — see the mobile
README); server-side photo diagnosis ships disabled until a backend
direction is chosen. The service keeps advisor.py's backend-swap shape, so
enabling one later is a config change in `vision.py`, nothing else.

`GET /ai/status` (unauthenticated, like `/`) reports the active advisor and
vision backends plus vision readiness — always `ready: false` today — so a
fresh deploy can be smoke-checked with one request and the mobile app can
gate photo UI on reality. The same check prints one `[vision]` line at
startup.

## Status
Backend feature-complete for v1: grounded advice, photo diagnosis +
identification, per-user accounts with Apple/Google sign-in, account deletion,
opt-in census, Alembic migrations, and a live Fly.io deployment. Next up is App
Store submission (the mobile client ships the sign-in and account-management UI;
see the root README roadmap). Product principle throughout: the free tier stays
genuinely useful — basic care is never paywalled.
