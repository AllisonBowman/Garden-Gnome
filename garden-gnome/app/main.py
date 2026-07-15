from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load .env before importing routers: the advisor/vision services read their
# backend config from the environment at import time. run_app.py does this
# for the packaged .exe; this covers `uvicorn app.main:app` dev runs.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db.database import run_migrations  # noqa: E402
from app.data.seed import seed_default_environment  # noqa: E402
from app.routers import auth, species, plants, environments, census  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings()      # fail fast if required secrets are missing
    run_migrations()    # Alembic owns the schema now (replaces init/migrate_db)
    seed_default_environment()  # ensure an environment exists for new plants
    yield


app = FastAPI(
    title="Garden Gnome API",
    description="AI-powered plant care assistant. Phase 1: inventory + curated care database.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(species.router)
app.include_router(plants.router)
app.include_router(environments.router)
app.include_router(census.router)

app.mount(
    "/ui",
    StaticFiles(directory=Path(__file__).parent / "static", html=True),
    name="ui",
)


@app.get("/")
def root():
    return {"status": "ok", "service": "garden-gnome", "version": "0.2.0"}
