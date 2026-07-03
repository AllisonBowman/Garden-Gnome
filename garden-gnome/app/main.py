from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db.database import init_db, migrate_db
from app.data.seed import seed_default_environment
from app.routers import species, plants, environments, census


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()           # create any new tables
    migrate_db()        # add new columns to existing tables
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
