# Garden Gnome

*A plant care assistant that knows what it's talking about.*

## What it is

Garden Gnome is a houseplant care app: a React Native (Expo) mobile client backed by a FastAPI service. You add plants, log care events (watering, fertilizing, misting, etc.), and get care advice and photo-based symptom diagnosis, all tailored to the specific species and that plant's own history. It's built for plant owners who want more than a generic watering-reminder app — and, at the systems level, for anyone evaluating how to build an AI feature that gives reliable answers instead of plausible-sounding ones.

## Why it's interesting

The core design decision is that the AI never reasons from scratch. Every species in the app has a curated database record — light needs, humidity/temperature ranges, soil type, toxicity, and a per-care-type schedule (water every 7–10 days, fertilize every 30–60, etc.). When the app generates care advice or diagnoses a photo, the LLM or vision model is handed those facts plus the plant's actual care log and instructed, explicitly in the system prompt, to answer *only* from what it's given — not to invent care requirements or diagnoses the data doesn't support.

This matters because plant care misinformation is exactly the kind of thing an ungrounded model produces confidently and wrong: a hallucinated watering interval or an invented pest diagnosis looks just as authoritative as a correct one. Grounding the model in a structured, human-reviewed knowledge base trades a little flexibility for a real gain in trustworthiness — the app can always point to *why* it said something. The advisor also runs as a hybrid: a free, deterministic rule-based backend handles routine schedule advice, while an LLM is invoked only for open-ended symptom diagnosis, which is the part that actually needs reasoning.

## Architecture

```
┌────────────────────┐        HTTPS/JSON        ┌──────────────────────┐
│  Mobile app (Expo)  │ ───────────────────────▶ │   FastAPI backend     │
│  React Native +      │ ◀─────────────────────── │   (Python)            │
│  React Query          │                          │                       │
└────────────────────┘                          │  ┌─────────────────┐  │
                                                  │  │ SQLite (SQLModel)│  │
                                                  │  │ Species/Plant/   │  │
                                                  │  │ CareLog/Env      │  │
                                                  │  └─────────────────┘  │
                                                  │           │            │
                                                  │  ┌────────▼────────┐  │
                                                  │  │ advisor.py       │──┼──▶ stub / Ollama (local LLM) / Claude API
                                                  │  │ vision.py        │──┼──▶ stub / Ollama vision model (moondream)
                                                  │  └──────────────────┘  │
                                                  └──────────────────────┘
```

The species/schedule tables are the single source of truth; `advisor.py` and `vision.py` are the only modules that talk to a model, and both are swappable via an environment variable without touching the rest of the app.

## Tech stack

- **Backend:** Python, FastAPI, SQLModel/SQLAlchemy over SQLite, Pydantic, httpx, python-dotenv, Anthropic Python SDK, Uvicorn. Packaged as a standalone Windows `.exe` via PyInstaller.
- **Mobile:** TypeScript, React Native + Expo (v57), React Navigation, TanStack React Query, React Native Paper, Axios, Expo Camera / Image Picker / Notifications / Secure Store.
- **AI/vision:** Anthropic Claude API (cloud) or Ollama (local, self-hosted) for text advice; Ollama with `moondream` (Apache 2.0, permissively licensed) for photo diagnosis.

## Key features (implemented)

- **Species catalog** — 129 curated houseplant species with light/humidity/temperature ranges, soil, toxicity, and per-care-type schedules; extensible key-value traits table.
- **Plant inventory** — create, read, and delete plants (no generic update endpoint; state changes go through purpose-built endpoints like transfer and care logging), intake condition snapshot at acquisition, care logging across 8 care types.
- **Timeline & stats** — full chronological care history with gap-from-previous per care type, plus per-type aggregate stats (avg/min/max interval vs. the species' scheduled interval).
- **Care advice** — `/plants/{id}/advice`, grounded in species facts + schedules + recent logs; stub/Ollama/Anthropic backends; optional free-text symptom diagnosis. The rule-based stub backend renders as one labeled, emoji-tagged line per care type (not raw debug output), with toxicity warnings called out separately.
- **Photo diagnosis** — `/plants/{id}/diagnose-photo`, vision-model reasoning over an uploaded photo plus the same grounding facts; auto-logged to the timeline. (Backend-complete; not yet wired into the mobile UI.)
- **Photo identification** — `/species/identify-photo`, wired into the mobile Add Plant flow: snap or pick a photo and the vision backend names the species *from the curated catalog only* (never a species the app can't actually care for), returning tap-to-select candidates with the best match pre-selected.
- **Environments & stewardship** — plants belong to a physical environment (home, nursery, community garden, etc.) and can be transferred between environments with a full chain-of-custody record, while keeping a stable UUID.
- **Anonymized census** — aggregate/export/sync endpoints that strip all PII (no nicknames, no addresses) for cross-installation species and care-health analysis.
- **LLM-assisted catalog authoring** — `/species/generate` drafts a new species record (schedules + traits) from a plant name for review before saving.
- **Mobile app** — tab-based navigation (Plants, Species, Environments, Census, Settings), quick care logging with a confirmation snackbar per logged action, an "Ask the Gnome" advice card with symptom input and styled advice output, photo identification in Add Plant, and species detail views.

## Setup

### Backend (FastAPI)

```bash
cd garden-gnome
python3 -m venv .venv
source .venv/bin/activate        # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# seed the curated species database (idempotent, safe to re-run)
python -m app.data.seed

# run the API
uvicorn app.main:app --reload
```

- API docs: http://127.0.0.1:8000/docs
- Built-in test console (not the product UI, just a manual test harness): http://127.0.0.1:8000/ui/

By default the app runs entirely offline with deterministic (non-AI) advice. To enable model-backed features, copy `.env.example` to `.env` and set:
- `ADVISOR_BACKEND=ollama` (local, free) or `anthropic` (cloud, requires `ANTHROPIC_API_KEY`) — text care advice.
- `ADVISOR_SYMPTOMS_BACKEND=anthropic` — recommended hybrid: keep routine advice free/instant, use an LLM only for symptom diagnosis.
- `VISION_BACKEND=ollama` — photo diagnosis and species identification via a local vision model (`ollama pull moondream`).

A packaged Windows executable (`GardenGnome.exe`, built via `build_exe.ps1`) is also available for running the backend with no Python install required.

#### Hosted backend (Fly.io)

The backend is deployed at **https://garden-gnome-api.fly.dev** (app `garden-gnome-api`, region `iad`). It runs as a single machine with the SQLite database on a persistent 1 GB volume (`gnome_data`, mounted at `/data` via the `DATABASE_URL` env var), seeds the species catalog on every boot (idempotent), and auto-stops when idle — the first request after a quiet period takes a couple of seconds while the machine wakes.

To redeploy after backend changes:

```bash
cd garden-gnome
flyctl deploy
```

Deployment config lives in `garden-gnome/Dockerfile` and `garden-gnome/fly.toml`.

### Mobile app (Expo)

```bash
cd mobile
npm install
npm run start     # then press w for web, or scan the QR code in Expo Go
```

The mobile app talks to the FastAPI backend over HTTPS. By default it points at the hosted backend (`https://garden-gnome-api.fly.dev` — see `src/api/client.ts`); iOS release builds require https to non-localhost hosts, so the default must stay https. For local development against a backend on your own machine, override the URL in the app's Settings tab (e.g. `http://localhost:8000`, or `http://192.168.x.x:8000` from a phone on the same network).

Store builds are configured in `mobile/eas.json` (`development`, `preview`, and `production` profiles for EAS Build).

## Project status / roadmap

| Phase | Status |
|---|---|
| 1. Plant inventory + curated care database | ✅ Done |
| 2. LLM reasoning layer on top of the care database | ✅ Done |
| 3. Photo-based diagnosis + identification (local vision model) | ✅ Backend done; photo ID live in Add Plant; diagnosis UI pending |
| 4. Proactive scheduling & notifications | 🔜 Planned |
| 5. Full "Gnome" character wrapper | 🔜 Planned |

Product principle carried through every phase: the free tier stays genuinely useful — basic care guidance is never paywalled.
