"""The shared geodata tile cache (`geodata_tile`, PLAN.md section 5).

What a public service answered for one grid-snapped block, compressed, with
an expiry and a last-used time. No user identifier is stored, and a tile is
shared by every property whose pin maps to the same block. A tile key must
start with the block key (`grid.BLOCK_PREFIX`), optionally followed by "_"
and a suffix ("blk1_15565_-25656_dem1m"), which is how `prune_unused`
knows when no property maps to it any more.

Sources call `fetch_or_get`; the routes and account deletion call
`prune_unused`, and the hourly housekeeping (app.services.housekeeping)
calls `prune_expired` and `prune_unused`. `put` flushes, and commits at
once on a session marked with `commit_eagerly`, which every build step and
the imagery route does: a source usually makes another outbound request
right after a write, and SQLite holds one write lock for the whole
database, so a flushed but uncommitted tile would make every other write in
the app wait for that request (and fail after the busy timeout). The tile
cache is a cache, so committing it early loses nothing. `prune_unused` only
flushes.

A read (`get`, `get_json`) is never a write in the caller's session. The
`last_used_at` bookkeeping a hit does (at most once an hour per tile) runs
on its own short connection and transaction (`_touch`): one guarded UPDATE,
committed at once, with a short wait for the lock, and skipped (logged at
debug) when the database is busy, since a later hit does it instead. So a
touch never raises to the caller, never leaves the caller's session needing
a rollback, and never leaves a GET holding SQLite's write lock for the rest
of the request. (It used to be flushed in the request's session: the
request then held the write lock until it ended, which /vitals and
/site-profile never committed, and the other requests of the Home screen
waited on it until the busy timeout and failed with "database is locked".)
The one exception: when the caller's session already holds a write
transaction (it flushed a write, say a `put` of the same tile not yet
committed), the touch is one more row in that transaction, since a second
connection could neither see an uncommitted row nor get the lock.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import threading
import time
import zlib
from datetime import datetime, timedelta
from typing import Any, Callable, Iterable, Optional

from sqlalchemy import or_, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import set_committed_value
from sqlalchemy.pool import NullPool
from sqlmodel import Session, create_engine, delete, select

from app.models.models import GeodataTile, Property
from app.services.site import grid

logger = logging.getLogger("plantadvocate.tiles")

#: How long a tile lives unless the source says otherwise. Public soil,
#: elevation and land cover change on a scale of years; imagery yearly.
DEFAULT_TTL = timedelta(days=90)
#: `last_used_at` moves forward at most this often, so a cache hit is
#: usually a read and not a write.
TOUCH_EVERY = timedelta(hours=1)
#: A tile fetched this recently is kept by `prune_unused` even when no
#: property maps to its block: someone may still be placing their pin there.
KEEP_RECENT = timedelta(hours=2)
#: The providers whose tiles `KEEP_RECENT` protects (the aerial image).
IMAGERY_PROVIDERS = frozenset({"naip"})


#: The longest a `last_used_at` touch waits for SQLite's write lock before
#: it is skipped (seconds). Short: a touch is bookkeeping, and a request
#: must never wait on it.
TOUCH_WAIT_S = 0.25


_EAGER = "tiles_commit_eagerly"


def commit_eagerly(session: Session) -> Session:
    """Mark a session so `put` commits at once (see the module note).
    Returns the session. Reads need no mark: they never write in the
    session."""
    session.info[_EAGER] = True
    return session


def _settle(session: Session) -> None:
    if session.info.get(_EAGER):
        session.commit()
    else:
        session.flush()


def _now(now: Optional[datetime]) -> datetime:
    return now or datetime.utcnow()


def _check_key(tile_key: str) -> None:
    if grid.block_key_prefix(tile_key) is None:
        raise ValueError(
            f"tile key {tile_key!r} must start with a block key "
            f"({grid.BLOCK_PREFIX}<row>_<col>)")


def _row(session: Session, provider: str, dataset_version: str,
         tile_key: str) -> Optional[GeodataTile]:
    return session.exec(
        select(GeodataTile)
        .where(GeodataTile.provider == provider)
        .where(GeodataTile.dataset_version == dataset_version)
        .where(GeodataTile.tile_key == tile_key)
    ).first()


def get(session: Session, provider: str, dataset_version: str, tile_key: str,
        *, now: Optional[datetime] = None) -> Optional[bytes]:
    """The stored bytes, or None when missing or expired. A hit moves
    `last_used_at` forward, at most once an hour, outside the caller's
    session (`_touch`); a busy database only skips that."""
    row = _row(session, provider, dataset_version, tile_key)
    t = _now(now)
    if row is None or (row.expires_at is not None and row.expires_at <= t):
        return None
    payload = zlib.decompress(row.payload)
    if row.last_used_at is None or t - row.last_used_at >= TOUCH_EVERY:
        _touch(session, row, t)
    return payload


# --- the last-used touch ------------------------------------------------------------

_TOUCH_ENGINES: dict[Any, Engine] = {}
_TOUCH_ENGINES_LOCK = threading.Lock()


def _touch_statement(row_id: int, t: datetime):
    """One row, and only if nobody moved it in the last hour (a concurrent
    request may have just done so)."""
    cutoff = t - TOUCH_EVERY
    col = GeodataTile.__table__.c.last_used_at
    return (update(GeodataTile.__table__)
            .where(GeodataTile.__table__.c.id == row_id)
            .where(or_(col.is_(None), col <= cutoff))
            .values(last_used_at=t))


def _memory_database(engine: Engine) -> bool:
    db = engine.url.database or ""
    return engine.dialect.name == "sqlite" and (
        db in ("", ":memory:") or "mode=memory" in str(engine.url))


def _touch_engine(engine: Engine) -> Engine:
    """An engine on the same database with no pool (a touch never waits for
    a pooled connection the requests are holding) and a short lock wait."""
    key = engine.url
    with _TOUCH_ENGINES_LOCK:
        eng = _TOUCH_ENGINES.get(key)
        if eng is None:
            args = ({"check_same_thread": False, "timeout": TOUCH_WAIT_S}
                    if engine.dialect.name == "sqlite" else {})
            eng = create_engine(engine.url, poolclass=NullPool, hide_parameters=True,
                                connect_args=args)
            _TOUCH_ENGINES[key] = eng
        return eng


def _holds_write_transaction(session: Session) -> bool:
    """True when the session's connection has a transaction open in the
    driver. The SQLite driver opens one only for a write (reads run outside
    a transaction), so this means the caller holds the write lock."""
    try:
        raw = session.connection().connection.dbapi_connection
    except SQLAlchemyError:
        return False
    return bool(getattr(raw, "in_transaction", False))


def _touch_within(session: Session, row_id: int, t: datetime) -> Optional[int]:
    """The touch as one more statement in the caller's open transaction.
    Through the connection, not the ORM: no flush, so a failure here never
    marks the session as needing a rollback. Returns the rows changed, or
    None when it failed."""
    try:
        return session.connection().execute(_touch_statement(row_id, t)).rowcount
    except SQLAlchemyError as exc:
        logger.debug("tile touch skipped in the caller's transaction (%s)",
                     type(exc).__name__)
        return None


def _touch_apart(engine: Engine, row_id: int, t: datetime) -> Optional[int]:
    """The touch on its own connection: BEGIN IMMEDIATE, the guarded UPDATE,
    COMMIT. Returns the rows changed, or None when it was skipped."""
    try:
        with _touch_engine(engine).connect() as conn:
            if conn.dialect.name == "sqlite":
                conn.exec_driver_sql("BEGIN IMMEDIATE")
            n = conn.execute(_touch_statement(row_id, t)).rowcount
            conn.commit()
            return n
    except SQLAlchemyError as exc:  # usually "database is locked": a later hit touches it
        logger.debug("tile touch skipped (%s)", type(exc).__name__)
        return None


def _touch(session: Session, row: GeodataTile, t: datetime) -> None:
    """Move `row.last_used_at` to `t` without writing in the caller's
    session (see the module note). Never raises."""
    try:
        bind = session.get_bind()
        engine = getattr(bind, "engine", bind)
        n: Optional[int] = None
        if _memory_database(engine) or _holds_write_transaction(session):
            n = _touch_within(session, row.id, t)
        if n is None and not _memory_database(engine):
            n = _touch_apart(engine, row.id, t)
        if n:
            # Keep the caller's copy in step without marking it changed.
            set_committed_value(row, "last_used_at", t)
    except Exception as exc:  # noqa: BLE001 -- bookkeeping never fails a read
        logger.debug("tile touch skipped (%s)", type(exc).__name__)


def put(session: Session, provider: str, dataset_version: str, tile_key: str,
        payload: bytes, *, ttl: Optional[timedelta] = DEFAULT_TTL,
        now: Optional[datetime] = None) -> GeodataTile:
    """Store (or replace) a tile. `ttl=None` means it never expires."""
    _check_key(tile_key)
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError("a tile payload is bytes; use put_json for JSON")
    t = _now(now)
    row = _row(session, provider, dataset_version, tile_key)
    if row is None:
        row = GeodataTile(provider=provider, dataset_version=dataset_version,
                          tile_key=tile_key, payload=b"")
    row.payload = zlib.compress(bytes(payload), 6)
    row.size_bytes = len(payload)
    row.fetched_at = t
    row.last_used_at = t
    row.expires_at = (t + ttl) if ttl is not None else None
    session.add(row)
    _settle(session)
    return row


def fetch_or_get(session: Session, provider: str, dataset_version: str,
                 tile_key: str, fetch: Callable[[], bytes], *,
                 ttl: Optional[timedelta] = DEFAULT_TTL,
                 now: Optional[datetime] = None) -> bytes:
    """The cached bytes, or `fetch()`'s answer stored and returned. A fetch
    that raises stores nothing and the exception propagates (a source turns
    it into SourceUnavailable)."""
    hit = get(session, provider, dataset_version, tile_key, now=now)
    if hit is not None:
        return hit
    payload = fetch()
    put(session, provider, dataset_version, tile_key, payload, ttl=ttl, now=now)
    return payload


def get_json(session: Session, provider: str, dataset_version: str,
             tile_key: str, *, now: Optional[datetime] = None):
    raw = get(session, provider, dataset_version, tile_key, now=now)
    return None if raw is None else json.loads(raw.decode("utf-8"))


def put_json(session: Session, provider: str, dataset_version: str,
             tile_key: str, value, *, ttl: Optional[timedelta] = DEFAULT_TTL,
             now: Optional[datetime] = None) -> GeodataTile:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return put(session, provider, dataset_version, tile_key, raw, ttl=ttl, now=now)


def blocks_in_use(session: Session, *, excluding_property_ids: Iterable[int] = ()) -> set[str]:
    """The block key of every property's pin, optionally leaving some out
    (account deletion leaves out the properties it is about to remove)."""
    skip = set(excluding_property_ids)
    keys = set()
    for prop in session.exec(select(Property)).all():
        if prop.id in skip:
            continue
        keys.add(grid.snap_block(prop.pin_lat, prop.pin_lng).key)
    return keys


def prune_unused(session: Session, *, keep_blocks: Iterable[str] = (),
                 excluding_property_ids: Iterable[int] = (),
                 keep_recent_imagery: bool = True,
                 now: Optional[datetime] = None) -> int:
    """Delete every tile whose block no property maps to. Returns the count.

    `keep_blocks` protects other blocks by name. An aerial image tile
    fetched in the last `KEEP_RECENT` is kept too (unless
    `keep_recent_imagery` is false, as for account deletion): someone may
    still be placing their pin on it. Tile keys that name no block are left alone
    (none should exist; `put` refuses them). Only ids and keys are read,
    never the payloads, so memory stays small however many tiles there are.
    Flushes; the caller commits."""
    in_use = blocks_in_use(session, excluding_property_ids=excluding_property_ids)
    in_use |= set(keep_blocks)
    recent = _now(now) - KEEP_RECENT
    doomed: list[int] = []
    for row_id, provider, key, fetched in session.exec(
            select(GeodataTile.id, GeodataTile.provider, GeodataTile.tile_key,
                   GeodataTile.fetched_at)).all():
        block = grid.block_key_prefix(key)
        if block is None or block in in_use:
            continue
        if (keep_recent_imagery and provider in IMAGERY_PROVIDERS
                and fetched is not None and fetched >= recent):
            continue
        doomed.append(row_id)
    for start in range(0, len(doomed), 500):
        session.execute(delete(GeodataTile).where(
            GeodataTile.id.in_(doomed[start:start + 500])))
    session.flush()
    return len(doomed)


#: How many expired tiles `prune_expired` deletes in one call.
EXPIRED_BATCH = 500


def prune_expired(session: Session, *, now: Optional[datetime] = None,
                  limit: int = EXPIRED_BATCH) -> int:
    """Delete up to `limit` tiles past their expiry. Returns the count, so a
    caller that commits after each call can repeat until it is under
    `limit` (the housekeeping timer does, keeping each write lock short).
    Only ids are read, never the payloads. A tile that never expires
    (`expires_at` is null) is left alone. Flushes; the caller commits."""
    ids = list(session.exec(
        select(GeodataTile.id)
        .where(GeodataTile.expires_at.is_not(None))
        .where(GeodataTile.expires_at <= _now(now))
        .limit(limit)).all())
    if ids:
        session.execute(delete(GeodataTile).where(GeodataTile.id.in_(ids)))
    session.flush()
    return len(ids)


# --- the volume ------------------------------------------------------------------------

#: PLAN.md section 6: an alert fires when the database volume is 70% full.
VOLUME_ALERT_SHARE = 0.70
#: The alert is logged at most this often (seconds).
VOLUME_ALERT_EVERY_S = 3600.0
_last_volume_alert = 0.0


def _database_dir() -> Optional[str]:
    url = os.environ.get("DATABASE_URL", "sqlite:///garden_gnome.db")
    if not url.startswith("sqlite:///") or ":memory:" in url:
        return None
    path = url[len("sqlite:///"):]
    return os.path.dirname(os.path.abspath(path)) or "."


def check_volume(*, path: Optional[str] = None) -> Optional[float]:
    """The share of the database volume in use (0..1), or None when it
    cannot be read. Logs a warning, at most once an hour, at 70% and above,
    so the log alert can tell the operator to grow the volume."""
    global _last_volume_alert
    where = path or _database_dir()
    if where is None:
        return None
    try:
        usage = shutil.disk_usage(where)
    except OSError:
        return None
    share = usage.used / usage.total if usage.total else None
    if share is not None and share >= VOLUME_ALERT_SHARE:
        now = time.monotonic()
        if not _last_volume_alert or now - _last_volume_alert >= VOLUME_ALERT_EVERY_S:
            _last_volume_alert = now
            logger.warning("VOLUME ALERT: the database volume is %d%% full (%d MB free); "
                           "grow it before it fills (PLAN.md section 6)",
                           round(share * 100), usage.free // (1024 * 1024))
    return share
