"""Hourly clean-out of cached public data nobody can use any more.

Run from the background timer in app.main, at most once every `EVERY`:

- `forecasts`: forecast_cache rows past their `expires_at` (a forecast
  lives `forecast.CACHE_LIFE`, three hours). While SEASON_PLAN_ENABLED.
- `expired_tiles`: geodata_tile rows past their `expires_at`, `BATCH` at a
  time. While SITE_PROFILE_ENABLED.
- `unused_tiles`: tiles whose block no property maps to
  (`tiles.prune_unused`), keeping an aerial image fetched in the last
  `tiles.KEEP_RECENT` (two hours) because someone may still be placing their
  pin on it. While SITE_PROFILE_ENABLED.

Each job has its own session and commits on its own (the expired tiles
after every batch), so no write lock is held for long: the database is
SQLite in write-ahead-log mode with one writer. A job that fails is logged
and never stops the others. No payload is read into memory.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Callable, Optional

from sqlmodel import Session

from app.config import get_settings
from app.services.season import forecast
from app.services.site import tiles

logger = logging.getLogger("plantadvocate.housekeeping")

#: The clean-out runs at most this often.
EVERY = timedelta(hours=1)
#: Expired tiles deleted per transaction.
BATCH = tiles.EXPIRED_BATCH
#: A run stops deleting expired tiles after this many batches and picks up
#: the rest an hour later, so one run never holds the writer for long.
MAX_BATCHES = 200

FAILED = "failed"


def _default_session() -> Session:
    from app.db.database import engine
    return Session(engine)


def prune_forecasts(session_factory: Callable[[], Session], now: datetime) -> int:
    with session_factory() as session:
        n = forecast.prune_expired(session, now=now)
        session.commit()
    return n


def prune_expired_tiles(session_factory: Callable[[], Session], now: datetime, *,
                        batch: int = BATCH, max_batches: int = MAX_BATCHES) -> int:
    total = 0
    with session_factory() as session:
        for _ in range(max_batches):
            n = tiles.prune_expired(session, now=now, limit=batch)
            session.commit()
            total += n
            if n < batch:
                break
    return total


def prune_unused_tiles(session_factory: Callable[[], Session], now: datetime) -> int:
    with session_factory() as session:
        n = tiles.prune_unused(session, keep_recent_imagery=True, now=now)
        session.commit()
    return n


class Housekeeping:
    """Remembers when the clean-out last ran. `clock` paces it (monotonic
    seconds) and `utcnow` dates the cut-offs; tests pass their own."""

    def __init__(self, *, session_factory: Optional[Callable[[], Session]] = None,
                 clock: Callable[[], float] = time.monotonic,
                 utcnow: Callable[[], datetime] = datetime.utcnow,
                 every: timedelta = EVERY):
        self.session_factory = session_factory or _default_session
        self.clock = clock
        self.utcnow = utcnow
        self.every_s = every.total_seconds()
        self.last_run: Optional[float] = None

    def due(self) -> bool:
        return self.last_run is None or self.clock() - self.last_run >= self.every_s

    def run_if_due(self) -> Optional[dict[str, int | str]]:
        """Run the jobs whose flag is on, if an hour has passed since the
        last run. Returns what each job deleted ("failed" for one that
        raised), or None when it was not yet due."""
        if not self.due():
            return None
        self.last_run = self.clock()
        settings = get_settings()
        now = self.utcnow()
        jobs: list[tuple[str, Callable[[Callable[[], Session], datetime], int]]] = []
        if settings.season_plan_enabled:
            jobs.append(("forecasts", prune_forecasts))
        if settings.site_profile_enabled:
            jobs.append(("expired_tiles", prune_expired_tiles))
            jobs.append(("unused_tiles", prune_unused_tiles))
        done: dict[str, int | str] = {}
        for name, job in jobs:
            try:
                done[name] = job(self.session_factory, now)
            except Exception:  # noqa: BLE001 -- one job never stops the others
                done[name] = FAILED
                logger.exception("housekeeping job %s failed", name)
        return done
