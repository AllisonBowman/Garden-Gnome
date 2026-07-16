# Garden Gnome 🌱

AI-powered plant care assistant for indoor houseplant hobbyists.

**Phase 1 (this scaffold):** plant inventory + curated care database. No AI yet —
the goal is a working, useful tool first. The curated `Species` table is the
authoritative care knowledge source; later phases add an LLM reasoning layer
*on top of* it (so care advice is grounded, not hallucinated).

## Build phases
1. ✅ Plant inventory + care database (no AI)
2. ✅ LLM reasoning layer (orchestrates on top of the species DB)
3. ✅ Photo-based diagnosis (local vision model) ← you are here
4. Proactive scheduling
5. Gnome character wrapper

## Quickest way to try it: GardenGnome.exe

A standalone Windows executable is included — no Python, no WSL, no setup.

1. Double-click `GardenGnome.exe` (or run it from PowerShell/cmd).
2. A console window opens and your browser opens automatically to the test
   console at http://127.0.0.1:8000/ui/.
3. To stop, close the console window (or press Ctrl+C in it).

Data is stored in `garden_gnome.db`, created next to the .exe the first time
it runs — it persists across restarts. To enable the local Ollama backends
(text advice or photo diagnosis beyond the stub), create a `.env` file next to
the .exe with the same variables as `.env.example` — it's loaded automatically.

This .exe bundles everything needed to run the app and is independent of the
WSL/Python dev setup below, which is only needed if you're changing code.

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
| `APPLE_PRIVATE_KEY_PATH` | Path to the `.p8`, e.g. `secrets/AuthKey_XXXX.p8` (gitignored) |
| `GOOGLE_CLIENT_ID` | Google OAuth iOS client id |
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

## Seed the care database

```bash
python -m app.data.seed
```

This populates ~10 common houseplants. Safe to run repeatedly (skips if already seeded).

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

The API is hosted at **https://garden-gnome-api.fly.dev** (app `garden-gnome-api`, org `allison-bowman`, region `iad`). The SQLite database lives on a persistent volume (`gnome_data` → `/data`), selected via the `DATABASE_URL` env var (`app/db/database.py` falls back to the local cwd-relative file when unset, so local dev is unchanged). The container seeds the species catalog on every boot — idempotent, so a redeploy never duplicates data.

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
  main.py            # FastAPI app + router wiring
  db/database.py     # SQLite engine + session dependency
  models/
    models.py        # Species, CareSchedule, SpeciesTrait, Plant, CareLog
    schemas.py       # request/response schemas
  routers/
    species.py       # read-only species (care DB) endpoints
    plants.py        # plant CRUD + care logs + advice + photo diagnosis
  services/
    advisor.py       # text advice service (stub/ollama/anthropic)
    vision.py        # photo diagnosis service (stub/ollama)
  data/seed.py       # curated seed data
```

## Quick test

```bash
# list the seeded species
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

Backend is chosen by `VISION_BACKEND` (`stub` | `ollama`). **No cloud/paid
backend is offered on purpose** — the default `ollama` model is
[moondream](https://github.com/vikhyat/moondream) (Apache 2.0), which is free
for unrestricted commercial use at any scale. To enable it:

```bash
ollama pull moondream
# then set VISION_BACKEND=ollama in your .env (OLLAMA_VISION_MODEL=moondream by default)
```

Other Apache-2.0 vision models (`qwen2.5vl`, `minicpm-v`) are drop-in swaps via
`OLLAMA_VISION_MODEL` for more accuracy. Avoid LLaMA-derived vision models
(`llava`, `llama3.2-vision`) — their weights carry Meta's community license
with commercial-use conditions, not a clean permissive license.

## Next steps
- **Phase 4:** proactive scheduling + notifications.
- Keep the free tier genuinely useful — basic care never paywalled (product decision, not code).
