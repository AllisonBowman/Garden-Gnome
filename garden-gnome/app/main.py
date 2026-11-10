import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load .env before importing routers: the advisor/vision services read their
# backend config from the environment at import time. run_app.py does this
# for the packaged .exe; this covers `uvicorn app.main:app` dev runs.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.middleware.gzip import GZipMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from sqlmodel import Session  # noqa: E402

from slowapi import _rate_limit_exceeded_handler  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db.catalog_state import catalog_status  # noqa: E402
from app.db.database import engine, get_session, run_migrations  # noqa: E402
from app.data.seed import seed_default_growing_area  # noqa: E402
from app.rate_limit import limiter  # noqa: E402
from app.routers import ai, auth, species, plants, growing_areas, census  # noqa: E402
from app.services.vision import vision_status  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings()      # fail fast if required secrets are missing
    run_migrations()    # Alembic owns the schema now (replaces init/migrate_db)
    seed_default_growing_area()  # ensure a growing area exists for new plants
    # A deleted account's Apple revoke that failed is tried again on each
    # cold start, in the background (auth.revoke_pending_apple_grants), and
    # one past its 30 days or 10 tries is dropped first, Apple or no Apple.
    auth.purge_expired_apple_revocations(engine)
    auth.start_queued_apple_revokes(engine)
    census.operator_token()  # a too-short operator secret is said at boot
    vs = await vision_status()  # surface a dead vision config at boot, not first photo
    print(f"[vision] backend={vs['backend']} ready={vs['ready']} "
          f"model={vs['model'] or '-'} — {vs['detail']}")
    yield


app = FastAPI(
    title="Garden Gnome API",
    description="AI-powered plant care assistant. Phase 1: inventory + curated care database.",
    version="0.2.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
    # A browser hides response headers it isn't told to show. The candidate
    # count travels in one (growing_areas.TOTAL_HEADER), and the web preview
    # needs it as much as the phone does.
    expose_headers=[growing_areas.TOTAL_HEADER],
)

# The catalog goes to the phone whole -- the Species tab, Add Plant and the
# Almanac each need every species -- and as JSON that is most of a megabyte,
# nearly all of it the same field names and sentences over and over; an
# area's full candidate list is the same story. Compressed, each is a small
# fraction of that, and the phone's networking unpacks it unasked. Small
# answers are left alone, and nothing here streams.
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(ai.router)
app.include_router(auth.router)
app.include_router(species.router)
app.include_router(plants.router)
app.include_router(growing_areas.router)
app.include_router(growing_areas.legacy_router)
app.include_router(census.router)

app.mount(
    "/ui",
    StaticFiles(directory=Path(__file__).parent / "static", html=True),
    name="ui",
)


@app.get("/")
def root(session: Session = Depends(get_session)):
    """Liveness, plus whether the catalog this build ships is the one serving.

    The deploy's smoke check reads `catalog.synced`: seed.py lets a failed
    claim sync pass so the API still boots, which leaves an answering server
    serving stale care data with nothing to say so. A failure to read the
    state is reported as not synced, never as an error, so this route keeps
    answering whatever the catalog's condition."""
    try:
        catalog = catalog_status(session)
    except Exception:  # noqa: BLE001 -- liveness must not depend on it
        logging.getLogger(__name__).exception("Could not read catalog state")
        catalog = {"synced": False}
    return {"status": "ok", "service": "garden-gnome", "version": "0.2.0",
            "catalog": catalog}
