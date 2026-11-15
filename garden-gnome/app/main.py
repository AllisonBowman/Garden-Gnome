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
from app.routers import properties  # noqa: E402
from app.services.vision import vision_status  # noqa: E402


SITE_RETRY_EVERY_S = 300


# --- what the logs may hold ---------------------------------------------------------

class DropQueryString(logging.Filter):
    """Removes the query string from uvicorn's access log line.

    GET /imagery/block?lat=..&lng=.. carries the exact pin in its query (the
    shipped iPhone build calls it that way), and uvicorn's default access log
    writes the full path with the query. The method, the path itself, the
    status and the client address are kept. uvicorn's record has
    `args = (client_addr, method, full_path, http_version, status_code)`;
    any other shape is passed through untouched."""

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if (isinstance(args, tuple) and len(args) == 5
                and isinstance(args[2], str) and "?" in args[2]):
            record.args = (args[0], args[1], args[2].split("?", 1)[0], args[3], args[4])
        return True


def install_log_filters() -> None:
    """Idempotent; run at import and again at startup, in case the logging
    setup was replaced in between."""
    access = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, DropQueryString) for f in access.filters):
        access.addFilter(DropQueryString())
    # httpx logs every outbound request's full URL at INFO, and a geodata URL
    # carries the grid-snapped block (finer than a kilometre). Nothing sets
    # INFO today; this keeps it so if something ever does.
    for name in ("httpx", "httpcore"):
        if logging.getLogger(name).level < logging.WARNING:
            logging.getLogger(name).setLevel(logging.WARNING)


install_log_filters()


# --- the background timer ---------------------------------------------------------

def _background_pass(housekeeping, *, settings=None) -> None:
    """One tick of the timer: the site profile retries (while
    SITE_PROFILE_ENABLED), then the hourly housekeeping, which keeps each of
    its jobs behind its own flag. Neither can stop the other."""
    settings = settings or get_settings()
    if settings.site_profile_enabled:
        from app.services.site import profile as site_profile
        from app.services.site import tiles as site_tiles
        try:
            site_tiles.check_volume()
            site_profile.run_due_retries()
        except Exception:  # noqa: BLE001 -- logged, and tried again later
            logging.getLogger("plantadvocate.site_profile").exception(
                "site profile retry pass failed")
    try:
        housekeeping.run_if_due()
    except Exception:  # noqa: BLE001 -- logged, and tried again later
        logging.getLogger("plantadvocate.housekeeping").exception(
            "housekeeping pass failed")


def _start_site_profile_retries() -> None:
    """Every 5 minutes, run the site profile background steps whose retry is
    due (app.services.site.profile.run_due_retries), and at most once an
    hour clear out expired and unused cached data
    (app.services.housekeeping). Started while SITE_PROFILE_ENABLED or
    SEASON_PLAN_ENABLED is on; a daemon thread, so it never holds shutdown."""
    settings = get_settings()
    if not (settings.site_profile_enabled or settings.season_plan_enabled):
        return
    import threading
    import time

    from app.services.housekeeping import Housekeeping

    housekeeping = Housekeeping()

    def loop():
        while True:
            _background_pass(housekeeping)
            time.sleep(SITE_RETRY_EVERY_S)

    threading.Thread(target=loop, name="site-profile-retries", daemon=True).start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings()      # fail fast if required secrets are missing
    install_log_filters()  # no query string (an exact pin) in the access log
    run_migrations()    # Alembic owns the schema now (replaces init/migrate_db)
    seed_default_growing_area()  # ensure a growing area exists for new plants
    # A deleted account's Apple revoke that failed is tried again on each
    # cold start, in the background (auth.revoke_pending_apple_grants), and
    # one past its 30 days or 10 tries is dropped first, Apple or no Apple.
    auth.purge_expired_apple_revocations(engine)
    auth.start_queued_apple_revokes(engine)
    census.operator_token()  # a too-short operator secret is said at boot
    _start_site_profile_retries()  # failed background steps retried; hourly clean-out
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
# Land stewardship (1.2.0). Every route here answers 404 while its feature
# flag is off (app.config: SITE_PROFILE_ENABLED, SEASON_PLAN_ENABLED).
app.include_router(properties.router)
app.include_router(properties.imagery_router)
app.include_router(properties.vitals_router)

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
