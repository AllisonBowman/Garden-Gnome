"""Site profile entry points (build spec section 3).

The routes in app/routers/properties.py call exactly these:

    build_fast(session, prop) -> None            hardiness and soil; inline on create
    build_background(property_id) -> None        elevation, terrain, canopy, sun,
                                                 land cover, where water collects;
                                                 opens its own session
    site_profile(session, prop) -> SiteProfileOut
    validate_override(field, value) -> None      raise ValueError to refuse a correction

How it works. Sources are modules exposing
`read(block, pin, footprint, *, client) -> list[Reading]` (build spec
section 3). They are found by name through a small registry and imported
lazily, so a source that is missing, half written or failing only turns its
own rows into "Not known yet". A source may also accept `session=` (for the
tile cache) and `readings=` (what earlier sources found); they are passed
only when its `read` declares them.

Readings are appended to `site_reading`; a new reading of a field sets
`superseded_at` on the ones it replaces, and an identical reading is not
written twice, so either step is safe to run again. The owner-facing profile
is computed on request from the active readings and the owner's corrections
(`overrides`), with the confidence caps in `confidence` and the sentences in
`copy`. Nothing derived is stored.

Status lives in `property.profile_status`: {"fast", "background"} as the
contract shows them, plus "sources" (each source's last result), "attempts",
"first_attempt_at", "next_retry_at" and "started_at" for the background step.
A failed background step is retried by `run_due_retries()` for up to 24 hours
after its first attempt; a step left "building" by a process that stopped is
picked up again once it is stale.
"""
from __future__ import annotations

import importlib
import inspect
import logging
import threading
import math
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Callable, Iterable, Iterator, Optional

import httpx
from sqlmodel import Session, select

from app.models.models import GrowingArea, Property, SiteReading
from app.services import coverage
from app.models.schemas import (
    OverrideChoice, ProfileStatus, PublicReading, SiteProfileOut, SiteValue,
    SourceOut, ZoneValues,
)
from app.services.site import confidence as conf
from app.services.site import copy as words
from app.services.site import grid
from app.services.site import http as site_http
from app.services.site import overrides as override_rules
from app.services.site import tiles
from app.services.site.types import Reading

logger = logging.getLogger("plantadvocate.site_profile")

# --- the source registry ----------------------------------------------------------

FAST_SOURCES: tuple[str, ...] = ("hardiness", "soil")
BACKGROUND_SOURCES: tuple[str, ...] = ("elevation", "canopy", "landcover")
#: Computed from what the sources above cached; also run per zone box.
DERIVED_SOURCES: tuple[str, ...] = ("terrain", "sun", "drainage")

MODULES: dict[str, str] = {
    "hardiness": "app.services.site.sources.hardiness",
    "soil": "app.services.site.sources.soil",
    "landcover": "app.services.site.sources.landcover",
    "elevation": "app.services.site.sources.elevation",
    "canopy": "app.services.site.sources.canopy",
    "terrain": "app.services.site.terrain",
    "sun": "app.services.site.sun",
    "drainage": "app.services.site.drainage",
    "imagery": "app.services.site.sources.imagery",
}
#: Best effort after the others: warms the aerial image cache and finds its
#: capture date. Gives no site value, so it never changes the step's status.
IMAGERY_SOURCE = "imagery"

#: Which sources a site value waits on, to tell "still being worked out"
#: from "the service did not answer".
VALUE_SOURCES: dict[str, tuple[str, ...]] = {
    "hardiness_zone": ("hardiness",),
    "soil_drainage": ("soil",), "soil_texture": ("soil",), "soil_ph": ("soil",),
    "disturbed_soil": ("soil",), "flooding": ("soil",),
    "land_cover": ("landcover",),
    "slope": ("elevation", "terrain"), "facing": ("elevation", "terrain"),
    "sun": ("elevation", "canopy", "sun"),
    "water_collects": ("soil", "elevation", "drainage"),
}

#: The reading each site value is read from.
VALUE_READING: dict[str, str] = {
    "hardiness_zone": "hardiness_zone", "soil_drainage": "soil_drainage_class",
    "soil_texture": "soil_texture", "soil_ph": "soil_ph",
    "disturbed_soil": "soil_disturbed_share",
    "flooding": "soil_flooding", "land_cover": "land_cover", "slope": "slope",
    "facing": "facing", "sun": "sun_estimate", "water_collects": "water_collects",
}

#: The order values are listed in.
LOT_FIELDS: tuple[str, ...] = (
    "sun", "water_collects", "soil_drainage", "soil_texture", "soil_ph",
    "disturbed_soil", "flooding", "slope", "facing", "hardiness_zone",
    "frost_dates", "land_cover")
#: Values worked out per zone box.
ZONE_FIELDS: tuple[str, ...] = ("sun", "water_collects", "slope", "facing")

#: A "building" step older than this was left by a process that stopped.
STALE_AFTER = timedelta(minutes=15)
#: Retries stop this long after the first attempt (PLAN.md section 6).
RETRY_FOR = timedelta(hours=24)
#: Wait before retry n (the last repeats).
RETRY_BACKOFF = (timedelta(minutes=5), timedelta(minutes=30), timedelta(hours=2),
                 timedelta(hours=6))

_overrides: dict[str, Any] = {}
#: Opens the background step's session; tests point it at their database.
SESSION_FACTORY: Optional[Callable[[], Session]] = None


@contextmanager
def use_sources(mapping: dict[str, Any]) -> Iterator[None]:
    """Replace sources by name for a test (a value of None removes one)."""
    saved = dict(_overrides)
    _overrides.update(mapping)
    try:
        yield
    finally:
        _overrides.clear()
        _overrides.update(saved)


def load_source(name: str) -> Any:
    """The module (or object) with `read`, or None if it is not installed."""
    if name in _overrides:
        return _overrides[name]
    try:
        module = importlib.import_module(MODULES[name])
    except Exception:  # noqa: BLE001 -- missing or half written: degrade
        logger.info("site source %s is not available", name)
        return None
    return module if callable(getattr(module, "read", None)) else None


def _call(source: Any, block, pin, footprint, *, client, session, readings) -> list[Reading]:
    read = source.read
    kwargs: dict[str, Any] = {"client": client}
    try:
        params = inspect.signature(read).parameters
    except (TypeError, ValueError):
        params = {}
    takes_any = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())
    if takes_any or "session" in params:
        kwargs["session"] = session
    if takes_any or "readings" in params:
        kwargs["readings"] = list(readings)
    out = read(block, pin, footprint, **kwargs)
    return [r for r in (out or []) if isinstance(r, Reading)]


# --- where the sources reach -------------------------------------------------------

def in_united_states(lat: float, lng: float) -> bool:
    """Where the United States datasets reach: the app's one rule
    (`app.services.coverage`), shared with the seasonal forecast."""
    return coverage.in_united_states(lat, lng)


# --- status ------------------------------------------------------------------------

def profile_status(prop: Property) -> ProfileStatus:
    status = prop.profile_status or {}
    return ProfileStatus(fast=status.get("fast", "pending"),
                         background=status.get("background", "pending"))


def _status(prop: Property) -> dict:
    return dict(prop.profile_status or {"fast": "pending", "background": "pending"})


def _save_status(prop: Property, status: dict) -> None:
    prop.profile_status = dict(status)  # a new dict, so the JSON column is saved


def _iso(t: datetime) -> str:
    return t.replace(microsecond=0).isoformat()


def _parse(t: Any) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(t) if isinstance(t, str) else None
    except ValueError:
        return None


#: Reason codes that mean a source answered but part of its answer is still
#: missing (the elevation survey's detail and year, when the survey lookup
#: failed). The source counts as "partial", so the step is tried again.
INCOMPLETE_CODES = frozenset({"resolution_unknown"})


def _overall(results: dict[str, str]) -> str:
    good = [k for k, v in results.items() if v in ("ready", "no_data", "skipped")]
    if len(good) == len(results):
        return "ready"
    return "partial" if good else "failed"


# --- readings ------------------------------------------------------------------------

def _whole_lot(session: Session, prop: Property) -> Optional[GrowingArea]:
    return session.exec(
        select(GrowingArea).where(GrowingArea.property_id == prop.id)
        .where(GrowingArea.user_id == prop.user_id)
        .where(GrowingArea.is_whole_lot == True)  # noqa: E712
    ).first()


def _zones(session: Session, prop: Property) -> list[GrowingArea]:
    return list(session.exec(
        select(GrowingArea)
        .where(GrowingArea.property_id == prop.id)
        .where(GrowingArea.user_id == prop.user_id)
        .order_by(GrowingArea.is_whole_lot.desc(), GrowingArea.id.asc())
    ).all())


def _active_rows(session: Session, property_id: int) -> list[SiteReading]:
    return list(session.exec(
        select(SiteReading).where(SiteReading.property_id == property_id)
        .where(SiteReading.superseded_at == None)  # noqa: E711
        .order_by(SiteReading.fetched_at.asc(), SiteReading.id.asc())
    ).all())


def _same(row: SiteReading, r: Reading, detail: dict) -> bool:
    level = row.level.value if hasattr(row.level, "value") else row.level
    prov = row.provenance.value if hasattr(row.provenance, "value") else row.provenance
    return (row.value == r.value and level == r.level and prov == r.provenance
            and row.source_key == r.source_key
            and row.source_version == r.source_version and row.method == r.method
            and list(row.reason_codes or []) == list(r.reason_codes)
            and (row.detail or {}) == detail)


def store_readings(session: Session, property_id: int, zone_id: Optional[int],
                   readings: Iterable[Reading], *, block_key: str,
                   footprint_box: Optional[dict] = None,
                   now: Optional[datetime] = None) -> int:
    """Append readings, superseding the active ones of the same field and
    zone. An identical active reading is kept as it is (safe to run twice).
    Returns how many rows were written. Flushes; the caller commits."""
    t = now or datetime.utcnow()
    written = 0
    for r in readings:
        detail = dict(r.detail or {})
        detail["block_key"] = block_key
        if footprint_box is not None:
            detail["footprint_box"] = {k: round(v, 7) for k, v in footprint_box.items()}
        q = (select(SiteReading).where(SiteReading.property_id == property_id)
             .where(SiteReading.field == r.field)
             .where(SiteReading.superseded_at == None))  # noqa: E711
        q = q.where(SiteReading.zone_id == zone_id) if zone_id is not None \
            else q.where(SiteReading.zone_id == None)  # noqa: E711
        current = list(session.exec(q).all())
        if len(current) == 1 and _same(current[0], r, detail):
            continue
        for old in current:
            old.superseded_at = t
            session.add(old)
        session.add(SiteReading(
            property_id=property_id, zone_id=zone_id, field=r.field, value=r.value,
            level=r.level, provenance=r.provenance, source_key=r.source_key,
            source_version=r.source_version, method=r.method,
            reason_codes=list(r.reason_codes), detail=detail, fetched_at=t))
        written += 1
    session.flush()
    return written


def _as_reading(row: SiteReading) -> Reading:
    level = row.level.value if hasattr(row.level, "value") else row.level
    prov = row.provenance.value if hasattr(row.provenance, "value") else row.provenance
    detail = {k: v for k, v in (row.detail or {}).items()
              if k not in ("block_key", "footprint_box")}
    return Reading(field=row.field, value=row.value, level=level, provenance=prov,
                   source_key=row.source_key, source_version=row.source_version,
                   method=row.method, reason_codes=tuple(row.reason_codes or ()),
                   detail=detail or None)


def _run_sources(names: Iterable[str], session: Session, prop: Property, block,
                 footprint: Optional[dict], client, prior: list[Reading],
                 *, zone_id: Optional[int] = None,
                 footprint_box: Optional[dict] = None,
                 now: Optional[datetime] = None) -> tuple[dict[str, str], dict[str, str]]:
    """Run each source, store what it read. Returns (result per source,
    error detail per failed source)."""
    results: dict[str, str] = {}
    errors: dict[str, str] = {}
    found = list(prior)
    session.commit()  # nothing of ours is left open while a source calls out
    for name in names:
        source = load_source(name)
        if source is None:
            results[name] = "missing"
            continue
        try:
            got = _call(source, block, (prop.pin_lat, prop.pin_lng), footprint,
                        client=client, session=session, readings=found)
        except Exception as exc:  # noqa: BLE001 -- one source never sinks the rest
            results[name] = "failed"
            errors[name] = str(exc)[:200] or exc.__class__.__name__
            logger.info("site source %s failed for property %s: %s", name,
                        prop.id, errors[name])
            continue
        store_readings(session, prop.id, zone_id, got, block_key=block.key,
                       footprint_box=footprint_box, now=now)
        # Commit before the next source goes to the network: SQLite has one
        # write lock for the whole database, and an open write would make
        # every other request wait for that call (and fail after the busy
        # timeout).
        session.commit()
        found.extend(got)
        if any(set(r.reason_codes) & INCOMPLETE_CODES for r in got):
            results[name] = "partial"
        else:
            results[name] = "ready" if any(r.level != "unknown" for r in got) else "no_data"
    return results, errors


# --- the fast step -----------------------------------------------------------------

def build_fast(session: Session, prop: Property) -> None:
    """Hardiness and soil for the pin, inline. Stores readings and the fast
    status; the route commits (and marks the step failed if this raises)."""
    status = _status(prop)
    sources = dict(status.get("sources") or {})
    if not in_united_states(prop.pin_lat, prop.pin_lng):
        for name in FAST_SOURCES:
            sources[name] = "skipped"
        status.update(fast="ready", sources=sources, outside_us=True)
        _save_status(prop, status)
        session.add(prop)
        return
    status.pop("outside_us", None)
    block = grid.snap_block(prop.pin_lat, prop.pin_lng)
    whole = _whole_lot(session, prop)
    footprint = whole.boundary_geojson if whole else grid.default_footprint(
        prop.pin_lat, prop.pin_lng)
    tiles.commit_eagerly(session)
    # Inline in the request that creates the property: one short attempt per
    # outside call. A source that does not answer in time is marked failed
    # here and tried again by the background step, which is queued next.
    with site_http.OutboundClient(flag="site_profile",
                                  timeout=site_http.INLINE_TIMEOUT,
                                  max_retries=0) as client:
        results, errors = _run_sources(FAST_SOURCES, session, prop, block, footprint,
                                       client, [])
    sources.update(results)
    status.update(fast=_overall(results), sources=sources)
    if errors:
        status["errors"] = {**(status.get("errors") or {}), **errors}
    _save_status(prop, status)
    session.add(prop)
    session.flush()


# --- the background step -------------------------------------------------------------

def _session() -> Session:
    if SESSION_FACTORY is not None:
        return tiles.commit_eagerly(SESSION_FACTORY())
    from app.db.database import engine
    return tiles.commit_eagerly(Session(engine))


#: Background steps running in this process, and those asked to run again
#: when the current run ends (a refresh or a moved pin during a run). The
#: server runs one worker, so this is the whole picture there; the
#: "building" status with its start time covers a restart.
_RUN_LOCK = threading.Lock()
_RUNNING: set[int] = set()
_RERUN: set[int] = set()


def request_rerun(property_id: int) -> bool:
    """True when the background step for this property is running now: it
    is marked to run once more when it ends, and the caller must leave its
    "building" status alone. False when nothing is running."""
    with _RUN_LOCK:
        if property_id in _RUNNING:
            _RERUN.add(property_id)
            return True
    return False


def build_background(property_id: int) -> None:
    """The slow sources for one property, in its own session, after the
    response has gone. Safe to run twice and after a restart: a run already
    in progress is left alone (and runs once more at its end if a refresh
    asked for it meanwhile), a stale one is taken over, and identical
    readings are not written again. Runs only while SITE_PROFILE_ENABLED is
    on."""
    if not site_http.flags_allow("site_profile"):
        return
    with _RUN_LOCK:
        if property_id in _RUNNING:
            _RERUN.add(property_id)
            return
        _RUNNING.add(property_id)
    try:
        while True:
            _build_background_once(property_id)
            with _RUN_LOCK:
                again = property_id in _RERUN
                _RERUN.discard(property_id)
                if not again:
                    _RUNNING.discard(property_id)
                    return
    finally:
        with _RUN_LOCK:
            _RUNNING.discard(property_id)
            _RERUN.discard(property_id)


def _build_background_once(property_id: int) -> None:
    now = datetime.utcnow()
    with _session() as session:
        prop = session.get(Property, property_id)
        if prop is None:
            return
        status = _status(prop)
        started = _parse(status.get("started_at"))
        if status.get("background") == "building" and started and now - started < STALE_AFTER:
            return  # another process holds it (this one's own passes end the status)
        status.update(background="building", started_at=_iso(now))
        status.setdefault("first_attempt_at", _iso(now))
        _save_status(prop, status)
        session.add(prop)
        session.commit()
        fast_at_start = status.get("fast")
        try:
            status = _background(session, prop, status, now)
        except Exception as exc:  # noqa: BLE001 -- recorded, never raised
            session.rollback()
            logger.exception("background site profile step failed for property %s",
                             property_id)
            prop = session.get(Property, property_id)
            if prop is None:
                return
            status = _status(prop)
            status["background"] = "failed"
            status["errors"] = {**(status.get("errors") or {}),
                                "background": str(exc)[:200]}
            _schedule_retry(status, now)
        status.pop("started_at", None)
        # A refresh may have run the fast step while this ran: keep its result.
        session.expire(prop)
        prop = session.get(Property, property_id)
        if prop is None:
            return
        live = _status(prop)
        if live.get("fast") != fast_at_start:
            status["fast"] = live.get("fast")
            sources = dict(status.get("sources") or {})
            for name in FAST_SOURCES:
                if name in (live.get("sources") or {}):
                    sources[name] = live["sources"][name]
            status["sources"] = sources
        _save_status(prop, status)
        session.add(prop)
        session.commit()


def _schedule_retry(status: dict, now: datetime) -> None:
    attempts = int(status.get("attempts") or 0) + 1
    status["attempts"] = attempts
    first = _parse(status.get("first_attempt_at")) or now
    wait = RETRY_BACKOFF[min(attempts - 1, len(RETRY_BACKOFF) - 1)]
    if now + wait - first <= RETRY_FOR:
        status["next_retry_at"] = _iso(now + wait)
    else:
        status.pop("next_retry_at", None)


def _background(session: Session, prop: Property, status: dict, now: datetime) -> dict:
    sources = dict(status.get("sources") or {})
    if not in_united_states(prop.pin_lat, prop.pin_lng):
        for name in BACKGROUND_SOURCES + DERIVED_SOURCES:
            sources[name] = "skipped"
        status.update(background="ready", sources=sources, outside_us=True)
        status.pop("next_retry_at", None)
        return status
    block = grid.snap_block(prop.pin_lat, prop.pin_lng)
    whole = _whole_lot(session, prop)
    footprint = whole.boundary_geojson if whole else grid.default_footprint(
        prop.pin_lat, prop.pin_lng)
    prior = [_as_reading(r) for r in _active_rows(session, prop.id) if r.zone_id is None]
    # A fast source that failed is tried again here.
    again = tuple(n for n in FAST_SOURCES if sources.get(n) in ("failed", "missing"))
    results: dict[str, str] = {}
    errors: dict[str, str] = {}
    with site_http.OutboundClient(flag="site_profile",
                                  timeout=site_http.SLOW_TIMEOUT) as client:
        if again:
            res, err = _run_sources(again, session, prop, block, footprint, client,
                                    prior, now=now)
            results.update(res)
            errors.update(err)
            if all(v != "failed" and v != "missing" for v in res.values()):
                status["fast"] = "ready"
            prior = [_as_reading(r) for r in _active_rows(session, prop.id)
                     if r.zone_id is None]
        res, err = _run_sources(BACKGROUND_SOURCES + DERIVED_SOURCES, session, prop,
                                block, footprint, client, prior, now=now)
        results.update(res)
        errors.update(err)
        lot = [_as_reading(r) for r in _active_rows(session, prop.id) if r.zone_id is None]
        if any(r.field == "elevation_window" and r.level != "unknown" for r in lot):
            for zone in _zones(session, prop):
                box = grid.polygon_box(zone.boundary_geojson)
                if zone.is_whole_lot or box is None:
                    continue
                zres, zerr = _run_sources(DERIVED_SOURCES, session, prop, block,
                                          zone.boundary_geojson, client, lot,
                                          zone_id=zone.id, footprint_box=box, now=now)
                for k, v in zerr.items():
                    errors[f"{k}:zone{zone.id}"] = v
        imagery = load_source(IMAGERY_SOURCE)
        if imagery is not None:
            try:
                _call(imagery, block, (prop.pin_lat, prop.pin_lng), footprint,
                      client=client, session=session, readings=())
                sources[IMAGERY_SOURCE] = "ready"
            except Exception as exc:  # noqa: BLE001 -- the image is optional here
                sources[IMAGERY_SOURCE] = "failed"
                logger.info("imagery warm-up failed for property %s: %s", prop.id, exc)
    sources.update(results)
    status["sources"] = sources
    status["background"] = _overall(results)
    if errors:
        status["errors"] = errors
    else:
        status.pop("errors", None)
    if status["background"] == "ready":
        for k in ("attempts", "next_retry_at", "first_attempt_at"):
            status.pop(k, None)
    else:
        _schedule_retry(status, now)
    return status


def due_for_retry(session: Session, *, now: Optional[datetime] = None) -> list[int]:
    """Properties whose background step should run again: a retry that is
    due, or a step left building or pending by a process that stopped."""
    t = now or datetime.utcnow()
    out: list[int] = []
    for prop in session.exec(select(Property)).all():
        st = prop.profile_status or {}
        bg = st.get("background", "pending")
        nxt = _parse(st.get("next_retry_at"))
        started = _parse(st.get("started_at"))
        if bg in ("partial", "failed") and nxt is not None and nxt <= t:
            out.append(prop.id)
        elif bg == "building" and (started is None or t - started >= STALE_AFTER):
            out.append(prop.id)
        elif bg == "pending" and t - prop.created_at >= STALE_AFTER:
            out.append(prop.id)
    return out


def run_due_retries(*, now: Optional[datetime] = None) -> list[int]:
    """Run every due background step (for a start-up hook or a timer)."""
    with _session() as session:
        ids = due_for_retry(session, now=now)
    for pid in ids:
        build_background(pid)
    return ids


# --- corrections ---------------------------------------------------------------------

def validate_override(field: str, value: Any) -> None:
    """Refuse an owner correction whose value is not one of the field's
    choices (ValueError with a plain sentence)."""
    override_rules.validate(field, value)


# --- the profile -----------------------------------------------------------------------

def _r(reading: Optional[Reading]) -> Optional[words.R]:
    if reading is None:
        return None
    return words.R(field=reading.field, value=reading.value, level=reading.level,
                   source_key=reading.source_key, source_version=reading.source_version,
                   method=reading.method, reason_codes=tuple(reading.reason_codes),
                   detail=dict(reading.detail or {}))


def _codes(rd: dict[str, Optional[words.R]], *fields: str) -> set[str]:
    out: set[str] = set()
    for f in fields:
        r = rd.get(f)
        if r is not None:
            out.update(r.reason_codes)
    return out


def _detail(rd: dict, f: str, key: str) -> Any:
    r = rd.get(f)
    return (r.detail or {}).get(key) if r is not None else None


def _detail_all(rd: dict, f: str) -> dict:
    r = rd.get(f)
    return dict(r.detail or {}) if r is not None else {}


def _share_key(d: dict, share_key: str, percent_key: str) -> Optional[float]:
    """A 0..1 share from `share_key`, else from a 0..100 `percent_key`."""
    v = d.get(share_key)
    if isinstance(v, (int, float)):
        return v / 100.0 if v > 1 else float(v)
    v = d.get(percent_key)
    if isinstance(v, (int, float)):
        return float(v) / 100.0
    return None


SOIL_READINGS = ("soil_mapunit", "soil_drainage_class", "soil_slowest_layer",
                 "soil_runoff_group", "soil_texture", "soil_water_holding",
                 "soil_ph", "soil_disturbed_share", "soil_flooding",
                 "soil_ponding", "soil_water_table")


def facts_for(field: str, rd: dict[str, Optional[words.R]], *,
              default_footprint: bool, zone_box: Optional[dict] = None,
              normals: Optional[dict] = None) -> conf.Facts:
    """The facts the confidence caps look at, from the readings. Reads only
    the reading fields and detail keys listed in the module report."""
    dist = rd.get("soil_disturbed_share")
    disturbed = words.share(dist.value) if dist else None
    codes = _codes(rd, *SOIL_READINGS)
    near_line = bool(codes & {"near_map_line", "near_soil_line"})
    for f in SOIL_READINGS:
        d = _detail(rd, f, "near_line_m")
        if isinstance(d, (int, float)) and d < conf.NEAR_LINE_M and \
                _detail(rd, f, "neighbour_differs") is not False:
            near_line = True
    main = rd.get(VALUE_READING.get(field, ""))
    md = (main.detail or {}) if main else {}
    dominant = _share_key(md, "dominant_share", "dominant_percent")
    if dominant is None:
        dominant = _share_key(_detail_all(rd, "soil_mapunit"), "dominant_share",
                              "dominant_percent")
    # B2a's soil source names these dominant_percent and data_percent (0..100).
    texture_cov = _share_key(_detail_all(rd, "soil_texture"), "coverage_share",
                             "data_percent")
    area_m2 = grid.box_area_sqft(zone_box) * 0.09290304 if zone_box else None

    res = words._num(md.get("resolution_m"))
    if res is None:
        ew = rd.get("elevation_window")
        if ew is not None:
            res = words._num(ew.detail.get("resolution_m")) if ew.detail else None
            if res is None:
                res = words._num(ew.value, "resolution_m")
    slope_r = rd.get("slope")
    slope_deg = words._num((slope_r.detail or {}).get("degrees")) if slope_r else None
    if slope_deg is None and slope_r is not None:
        pct = words._num(slope_r.value, "percent", "pct", "value")
        slope_deg = math.degrees(math.atan(pct / 100.0)) if pct is not None else None

    counted = set(md.get("counted") or []) if field == "sun" else set()
    canopy = bool(counted & {"canopy_height", "first_return"})
    signals = set(md.get("signals") or []) if field == "water_collects" else set()
    elev_used = bool(signals & {"low_spot", "flow"}) or (
        field == "water_collects" and md.get("resolution_m") is not None)
    soil_used = field == "water_collects" and (
        bool(md.get("soil_signals")) or bool(signals - {"low_spot", "flow"}))

    hz_codes = _codes(rd, "hardiness_zone")
    near_zone = bool(hz_codes & {"near_zone_line"}) or bool(
        _detail(rd, "hardiness_zone", "near_line"))
    return conf.Facts(
        default_footprint=default_footprint,
        zone_area_m2=area_m2,
        resolution_m=res,
        disturbed_share=disturbed,
        near_soil_line=near_line,
        dominant_share=dominant if isinstance(dominant, (int, float)) else None,
        texture_coverage=texture_cov if isinstance(texture_cov, (int, float)) else None,
        slope_degrees=slope_deg,
        terrain_counted="terrain" in counted,
        canopy_counted=canopy,
        coarse_canopy_only=("tree_cover" in counted and not canopy),
        buildings_counted="buildings" in counted,
        soil_signals_agree=bool(md.get("soil_agree")),
        soil_agree_share=md.get("soil_agree_share"),
        elevation_used=elev_used,
        soil_used=soil_used,
        near_zone_line=near_zone,
        stations_differ_days=(normals or {}).get("stations_differ_days"),
    )


def _value_of(field: str, r: Optional[words.R]) -> Any:
    if r is None:
        return None
    v = r.value
    if field == "sun" and isinstance(v, dict):
        return v.get("category")
    if isinstance(v, (dict, list)):
        return v
    return v


def _site_value(field: str, text: words.Text, confidence: str, provenance: str,
                value: Any, zone_id: Optional[int]) -> SiteValue:
    spec = override_rules.spec(field)
    return SiteValue(
        field=field, title=words.TITLES[field], value=value, zone_id=zone_id,
        display=text.display, confidence=confidence, reason=text.reason,
        sources=[SourceOut(**s) for s in text.sources], provenance=provenance,
        can_override=spec.kind != "none",
        override_choices=[OverrideChoice(**c) for c in override_rules.choices(field)],
        override_kind=spec.kind)


def _missing_state(field: str, status: dict, zone: bool = False) -> str:
    if status.get("outside_us"):
        return "outside_us"
    srcs = status.get("sources") or {}
    names = VALUE_SOURCES.get(field, ())
    step = "fast" if all(n in FAST_SOURCES for n in names) else "background"
    if any(srcs.get(n) in ("failed", "missing") for n in names) and \
            status.get(step) in ("failed", "partial", "ready"):
        return "failed"
    if zone and status.get(step) == "ready":
        return "zone_pending"
    if status.get(step, "pending") in ("pending", "building"):
        return "pending"
    return "no_data"


def _public_value(field: str, rd: dict[str, Optional[words.R]], status: dict, *,
                  default_footprint: bool, zone_id: Optional[int],
                  zone_box: Optional[dict] = None, leaf_habit: Optional[str] = None,
                  normals: Optional[dict] = None, zone: bool = False) -> SiteValue:
    if field == "frost_dates":
        facts = conf.Facts(stations_differ_days=(normals or {}).get("stations_differ_days"))
        level = (normals or {}).get("level") or "medium"
        d = conf.decide(field, level if level in conf.LEVEL_TO_CONFIDENCE else "medium",
                        facts)
        text = words.frost_dates(normals or {}, d.caps) if normals else None
        if text is None:
            state = "outside_us" if status.get("outside_us") else (
                "pending" if (normals or {}).get("status") == "pending" else "no_data")
            if state == "pending":
                text = words.Text("Typical frost dates: still being worked out.",
                                  "We read these from weather station records held on "
                                  "our server.", [words.source("noaa_normals")])
            else:
                text = words.missing("frost_dates", state)
            return _site_value(field, text, "not_known_yet", "default", None, zone_id)
        return _site_value(field, text, d.confidence, "public_map", None, zone_id)

    main = rd.get(VALUE_READING[field])
    if field == "sun" and (main is None or main.level == "unknown"):
        open_sky = rd.get("open_sky_sun")
        if open_sky is not None and open_sky.level != "unknown":
            text = words.sun(None, rd, (), default_footprint, leaf_habit)
            return _site_value(field, text, "not_known_yet", "modelled", None, zone_id)
    if main is None:
        text = words.missing(field, _missing_state(field, status, zone))
        return _site_value(field, text, "not_known_yet", "default", None, zone_id)
    if main.level == "unknown":
        text = words.missing(field, "no_data")
        text = words.Text(text.display, text.reason,
                          words.sources_of([main], words.FIELD_SOURCE[field]))
        return _site_value(field, text, "not_known_yet",
                           _prov(rd, field), None, zone_id)

    facts = facts_for(field, rd, default_footprint=default_footprint,
                      zone_box=zone_box, normals=normals)
    d = conf.decide(field, main.level, facts)
    builders: dict[str, Callable[[], words.Text]] = {
        "hardiness_zone": lambda: words.hardiness_zone(main, d.caps),
        "soil_drainage": lambda: words.soil_drainage(main, rd, d.caps),
        "soil_texture": lambda: words.soil_texture(main, rd, d.caps),
        "soil_ph": lambda: words.soil_ph(main, d.caps),
        "disturbed_soil": lambda: words.disturbed_soil(main, d.caps),
        "flooding": lambda: words.flooding(main, rd, d.caps),
        "slope": lambda: words.slope(main, d.caps, default_footprint),
        "facing": lambda: words.facing(main, d.caps, default_footprint),
        "sun": lambda: words.sun(main, rd, d.caps, default_footprint, leaf_habit),
        "water_collects": lambda: words.water_collects(main, rd, d.caps, default_footprint),
        "land_cover": lambda: words.land_cover(main, rd),
    }
    text = builders[field]()
    confidence = d.confidence if not text.display.endswith("not known yet.") else "not_known_yet"
    return _site_value(field, text, confidence, _prov(rd, field),
                       _value_of(field, main), zone_id)


def _prov(rd: dict, field: str) -> str:
    return rd.get("__prov__", {}).get(VALUE_READING.get(field, ""), "public_map")


def _with_owner(sv: SiteValue, row) -> SiteValue:
    method = row.method.value if hasattr(row.method, "value") else str(row.method)
    if sv.field == "soil_ph":
        method = "measured"
    d = conf.owner(method)
    public_sources = [s.model_dump(exclude_none=True) for s in sv.sources]
    text = words.owner(sv.field, row.value, method, row.created_at, public_sources)
    out = _site_value(sv.field, text, d.confidence, "owner", row.value, sv.zone_id)
    out.public = PublicReading(display=sv.display, confidence_label=sv.confidence_label)
    return out


def _grouped(session: Session, prop: Property, block_key: str
             ) -> tuple[dict[Optional[int], dict[str, Optional[words.R]]], Optional[datetime]]:
    groups: dict[Optional[int], dict[str, Any]] = {}
    latest: Optional[datetime] = None
    for row in _active_rows(session, prop.id):
        if (row.detail or {}).get("block_key", block_key) != block_key:
            continue  # read for an earlier pin
        rd = groups.setdefault(row.zone_id, {"__prov__": {}, "__box__": {}})
        reading = _as_reading(row)
        rd[row.field] = _r(reading)
        rd["__prov__"][row.field] = reading.provenance
        rd["__box__"][row.field] = (row.detail or {}).get("footprint_box")
        latest = row.fetched_at if latest is None or row.fetched_at > latest else latest
    return groups, latest


def _normals(prop: Property) -> Optional[dict]:
    try:
        from app.services.season.normals import frost_normals
        out = frost_normals(prop.pin_lat, prop.pin_lng)
        return out if isinstance(out, dict) else None
    except Exception:  # noqa: BLE001 -- the row says not known
        logger.info("frost normals unavailable for property %s", prop.id)
        return None


def _cached_only_client() -> site_http.OutboundClient:
    """A client that sends nothing: per-zone values computed on request use
    only what the background step already cached."""
    def refuse(request):
        raise httpx.ConnectError("cached data only", request=request)
    return site_http.OutboundClient(flag="site_profile",
                                    transport=httpx.MockTransport(refuse), max_retries=0)


def _zone_readings_now(session: Session, prop: Property, zone: GrowingArea,
                       lot: dict[str, Any]) -> dict[str, Any]:
    """Per-zone values from the cached background data, without storing or
    sending anything. Empty when nothing could be computed."""
    lot_readings = []
    for f, r in lot.items():
        if f.startswith("__") or r is None:
            continue
        lot_readings.append(Reading(
            field=r.field, value=r.value, level=r.level,
            provenance=lot["__prov__"].get(f, "public_map"), source_key=r.source_key,
            source_version=r.source_version, method=r.method,
            reason_codes=tuple(r.reason_codes), detail=dict(r.detail) or None))
    if not any(r.field == "elevation_window" and r.level != "unknown" for r in lot_readings):
        return {}
    block = grid.snap_block(prop.pin_lat, prop.pin_lng)
    out: dict[str, Any] = {"__prov__": {}, "__box__": {}}
    found = list(lot_readings)
    try:
        client = _cached_only_client()
    except Exception:  # noqa: BLE001
        return {}
    with client:
        for name in DERIVED_SOURCES:
            source = load_source(name)
            if source is None:
                continue
            try:
                got = _call(source, block, (prop.pin_lat, prop.pin_lng),
                            zone.boundary_geojson, client=client, session=session,
                            readings=found)
            except Exception:  # noqa: BLE001 -- not cached yet: the row waits
                continue
            found.extend(got)
            for r in got:
                out[r.field] = _r(r)
                out["__prov__"][r.field] = r.provenance
    return out if len(out) > 2 else {}


def site_profile(session: Session, prop: Property) -> SiteProfileOut:
    """The owner-facing profile, computed on request: lot values, then the
    values worked out for each zone, with statuses and plain notes."""
    status = _status(prop)
    zones = _zones(session, prop)
    whole = next((z for z in zones if z.is_whole_lot), None)
    whole_id = whole.id if whole else None
    in_us = in_united_states(prop.pin_lat, prop.pin_lng)
    if not in_us:
        status["outside_us"] = True
    block_key = grid.snap_block(prop.pin_lat, prop.pin_lng).key if in_us else ""
    groups, latest = _grouped(session, prop, block_key) if in_us else ({}, None)
    lot = groups.get(None, {"__prov__": {}, "__box__": {}})
    found = override_rules.active(session, prop)
    normals = _normals(prop) if in_us else None

    lot_default = whole is None or _enum(whole.boundary_source) != "owner"
    lot_box = grid.polygon_box(whole.boundary_geojson) if whole else None
    leaf = _enum(whole.leaf_habit) if whole else None

    lot_values: list[SiteValue] = []
    by_field: dict[str, SiteValue] = {}
    for field in LOT_FIELDS:
        sv = _public_value(field, lot, status, default_footprint=lot_default,
                           zone_id=None, zone_box=None if lot_default else lot_box,
                           leaf_habit=leaf, normals=normals)
        by_field[field] = sv
        row = override_rules.for_zone(found, field, None, whole_id)
        lot_values.append(_with_owner(sv, row) if row is not None else sv)

    zone_out: list[ZoneValues] = []
    for z in zones:
        values: list[SiteValue] = []
        box = grid.polygon_box(z.boundary_geojson)
        if z.is_whole_lot:
            for field in ZONE_FIELDS:
                sv = by_field[field].model_copy(update={"zone_id": z.id})
                row = override_rules.for_zone(found, field, z.id, whole_id)
                values.append(_with_owner(sv, row) if row is not None else sv)
        else:
            rd = dict(groups.get(z.id, {}))
            fresh = {k: v for k, v in rd.items() if not k.startswith("__")
                     and rd.get("__box__", {}).get(k) == (
                         {k2: round(v2, 7) for k2, v2 in box.items()} if box else None)}
            if not fresh and box is not None and in_us:
                now_rd = _zone_readings_now(session, prop, z, lot)
                fresh = {k: v for k, v in now_rd.items() if not k.startswith("__")}
                rd = now_rd or rd
            zrd: dict[str, Any] = {k: v for k, v in lot.items()
                                   if k.startswith("soil_") or k in (
                                       "elevation_window", "tree_cover", "canopy_shade")}
            zrd.update(fresh)
            zrd["__prov__"] = {**lot.get("__prov__", {}), **rd.get("__prov__", {})}
            for field in ZONE_FIELDS:
                if VALUE_READING[field] not in fresh:
                    zrd.pop(VALUE_READING[field], None)
                sv = _public_value(field, zrd, status,
                                   default_footprint=_enum(z.boundary_source) != "owner",
                                   zone_id=z.id, zone_box=box,
                                   leaf_habit=_enum(z.leaf_habit), normals=normals,
                                   zone=True)
                row = override_rules.for_zone(found, field, z.id, whole_id)
                values.append(_with_owner(sv, row) if row is not None else sv)
            # Other corrections the owner made for this zone.
            for (zid, field), row in found.items():
                if zid == z.id and field not in ZONE_FIELDS and field in words.TITLES:
                    base = by_field[field].model_copy(update={"zone_id": z.id})
                    values.append(_with_owner(base, row))
        zone_out.append(ZoneValues(zone_id=z.id, name=z.name,
                                   is_whole_lot=bool(z.is_whole_lot), values=values))

    return SiteProfileOut(
        property_id=prop.id, status=profile_status(prop), updated_at=latest,
        values=lot_values, zones=zone_out,
        notes=_notes(status, in_us, lot_default))


def _enum(v: Any) -> Any:
    return v.value if hasattr(v, "value") else v


def _notes(status: dict, in_us: bool, default_footprint: bool) -> list[str]:
    notes: list[str] = []
    if not in_us:
        notes.append("Your pin is outside the United States. The public maps we use "
                     "cover the United States only, so tell us about sun and soil "
                     "yourself. Home still shows your local weather, but the seasonal plan "
                     "uses United States climate data and has little to show here.")
        return notes
    fast, bg = status.get("fast", "pending"), status.get("background", "pending")
    if fast in ("pending", "building") or bg in ("pending", "building"):
        notes.append("Some values are still being worked out from public maps. "
                     "Check back in a minute or two.")
    if fast in ("failed", "partial") or bg in ("failed", "partial"):
        notes.append("A public map service did not answer. We will try again, and "
                     "your own answers are kept either way.")
    if default_footprint:
        notes.append("Values for the whole lot use an approximate yard (typical United "
                     "States lot size, not your property line). Draw a box over a bed "
                     "to get values for that spot.")
    notes.append("Soil values describe a mapped area of several acres, not your yard.")
    return notes
