"""The tile cache's `last_used_at` touch under concurrent requests.

Seen on a local server on 2026-11-16: the Home screen fires six requests at
once, and two answered 500 with "database is locked" on
`UPDATE geodata_tile SET last_used_at=...`, then PendingRollbackError later
in the same request. The touch was flushed in the request's own session, so
the request held SQLite's write lock until it ended (and /vitals,
/site-profile and /zones never commit, so the touch was then rolled back);
every other request's touch waited for it and failed after the busy timeout,
leaving its session needing a rollback.

The touch now runs on its own short transaction (tiles._touch). These tests
hold it to: (a) a busy database never raises to the caller, (b) the caller's
session is never left failed, (c) no request is left holding the write lock
because of a touch, (d) touches still happen.
"""
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import numpy as np
import pytest
from sqlalchemy import event, text
from sqlmodel import Session, create_engine, select

from app.models.models import GeodataTile
from app.services.site import grid, tiles
from tests.test_scoping import iso  # noqa: F401  (fixture)

#: Blocks no other test uses (the test database is shared).
BLOCK_A = "blk1_99901_-1"
BLOCK_B = "blk1_99902_-1"


def _wal_engine(url, timeout_s):
    """An engine like the app's (app.db.database): write-ahead logging and a
    busy timeout, here a short one so a wait that would end in "database is
    locked" ends quickly."""
    engine = create_engine(url, connect_args={"check_same_thread": False,
                                              "timeout": timeout_s})

    def pragmas(dbapi_connection, _record):
        cur = dbapi_connection.cursor()
        try:
            cur.execute(f"PRAGMA busy_timeout = {int(timeout_s * 1000)}")
            cur.execute("PRAGMA journal_mode = WAL")
        finally:
            cur.close()
    event.listen(engine, "connect", pragmas)
    return engine


def _path(url):
    return url.removeprefix("sqlite:///")


def _write_lock_is_free(url) -> bool:
    other = sqlite3.connect(_path(url), timeout=0)
    try:
        other.execute("BEGIN IMMEDIATE")
        other.rollback()
        return True
    except sqlite3.OperationalError:
        return False
    finally:
        other.close()


def _last_used(engine, key):
    with Session(engine) as s:
        return s.exec(select(GeodataTile.last_used_at)
                      .where(GeodataTile.tile_key == key)).one()


STALE = timedelta(hours=2)


@pytest.fixture()
def wal(migrated_db_url):
    engine = _wal_engine(migrated_db_url, 1.0)
    old = datetime.utcnow() - STALE
    with Session(engine) as s:
        for key in (f"{BLOCK_A}_touch", f"{BLOCK_B}_touch"):
            tiles.put(s, "touchtest", "v1", key, key.encode(), now=old)
        s.commit()
    yield engine
    with Session(engine) as s:
        for row in s.exec(select(GeodataTile)
                          .where(GeodataTile.provider == "touchtest")).all():
            s.delete(row)
        s.commit()
    engine.dispose()


def test_a_touch_after_another_connection_wrote_never_raises(wal):
    """A read transaction in A, a write committed by B since, then a stale
    hit in A: A's snapshot cannot become a write (SQLite answers "database
    is locked" at once, whatever the busy timeout). The read still answers,
    A's session still works, and the touch is made on its own transaction."""
    key = f"{BLOCK_A}_touch"
    before = _last_used(wal, key)
    with Session(wal) as a, Session(wal) as b:
        a.connection().exec_driver_sql("BEGIN")       # a read transaction ...
        a.exec(select(GeodataTile.id)).all()          # ... with its snapshot taken
        b.exec(text("UPDATE geodata_tile SET bytes = bytes + 1 "
                    "WHERE tile_key = :k"), params={"k": f"{BLOCK_B}_touch"})
        b.commit()                                    # B wrote since A's snapshot
        assert tiles.get(a, "touchtest", "v1", key) == key.encode()
        assert a.exec(select(GeodataTile.id)).all()   # not PendingRollbackError
        a.commit()
    assert _last_used(wal, key) > before + timedelta(hours=1)


def test_a_touch_never_holds_the_write_lock_for_the_rest_of_the_request(wal, migrated_db_url):
    """Two requests, each a stale hit: before, the first held the write lock
    until its session ended, and the second waited out the busy timeout,
    failed with "database is locked" and was left needing a rollback."""
    ka, kb = f"{BLOCK_A}_touch", f"{BLOCK_B}_touch"
    with Session(wal) as a, Session(wal) as b:
        assert tiles.get(a, "touchtest", "v1", ka) == ka.encode()
        assert _write_lock_is_free(migrated_db_url)     # (c)
        assert not a.dirty and not a.new                # nothing left in A to flush
        started = time.monotonic()
        assert tiles.get(b, "touchtest", "v1", kb) == kb.encode()
        assert time.monotonic() - started < 0.5         # no wait for A
        assert b.exec(select(GeodataTile.id)).all()     # (b)
        # Neither session commits, as /vitals and /site-profile never do.
    now = datetime.utcnow()
    for key in (ka, kb):                                 # (d) the touches stand
        assert now - _last_used(wal, key) < timedelta(minutes=1)


def test_a_locked_database_skips_the_touch_and_a_later_hit_makes_it(wal, migrated_db_url):
    key = f"{BLOCK_A}_touch"
    before = _last_used(wal, key)
    holder = sqlite3.connect(_path(migrated_db_url), timeout=0)
    try:
        holder.execute("BEGIN IMMEDIATE")              # someone else is writing
        with Session(wal) as s:
            started = time.monotonic()
            assert tiles.get(s, "touchtest", "v1", key) == key.encode()   # (a)
            assert time.monotonic() - started < tiles.TOUCH_WAIT_S + 0.5
            assert s.exec(select(GeodataTile.id)).all()                    # (b)
    finally:
        holder.rollback()
        holder.close()
    assert _last_used(wal, key) == before                # skipped, not half-done
    with Session(wal) as s:
        tiles.get(s, "touchtest", "v1", key)
    assert _last_used(wal, key) > before                 # (d)


def test_a_touch_happens_at_most_once_an_hour(wal):
    key = f"{BLOCK_A}_touch"
    t0 = datetime.utcnow()
    with Session(wal) as s:
        tiles.get(s, "touchtest", "v1", key, now=t0)
    assert _last_used(wal, key) == t0
    with Session(wal) as s:
        row = s.exec(select(GeodataTile).where(GeodataTile.tile_key == key)).one()
        assert row.last_used_at == t0
        tiles.get(s, "touchtest", "v1", key, now=t0 + timedelta(minutes=59))
        assert row.last_used_at == t0 and not s.dirty
    assert _last_used(wal, key) == t0
    with Session(wal) as s:
        row = s.exec(select(GeodataTile).where(GeodataTile.tile_key == key)).one()
        tiles.get(s, "touchtest", "v1", key, now=t0 + timedelta(hours=1))
        assert row.last_used_at == t0 + timedelta(hours=1) and not s.dirty
    assert _last_used(wal, key) == t0 + timedelta(hours=1)


def test_a_touch_of_a_tile_the_session_has_not_committed_joins_its_transaction(wal):
    """A build step that wrote a tile and reads it back before committing:
    another connection could not see the row, so the touch is made in the
    caller's transaction (which already holds the lock) and commits with it."""
    key = f"{BLOCK_A}_fresh"
    t0 = datetime(2026, 11, 16, 2, 0)
    with Session(wal) as s:
        row = tiles.put(s, "touchtest", "v1", key, b"new", now=t0)
        assert tiles.get(s, "touchtest", "v1", key, now=t0 + timedelta(hours=1)) == b"new"
        assert row.last_used_at == t0 + timedelta(hours=1)
        s.commit()
    assert _last_used(wal, key) == t0 + timedelta(hours=1)


# --- the Home screen, end to end ------------------------------------------------------

#: A pin no other test uses.
HOME_PIN = (41.2565, -95.9345)
#: How long working out a zone takes here, and the app sessions' busy
#: timeout: scaled down from seconds and 15 s, keeping a request that held
#: the lock through its analysis longer than another request would wait.
ANALYSIS_S = 0.3
BUSY_S = 0.5


@pytest.fixture()
def home(iso, migrated_db_url, monkeypatch):  # noqa: F811
    """A property at HOME_PIN with a finished background step, an owner
    zone whose values are worked out on request from the cached terrain, and
    every tile the Home screen reads cached; the app's sessions use an
    engine like production's (write-ahead logging, a busy timeout)."""
    from app.db.database import get_session
    from app.main import app
    from app.routers import properties
    from app.services import vitals as vitals_mod
    from app.services.site import layers as layer_service
    from app.services.site import profile, terrain
    from app.services.site.sources import canopy as canopy_source
    from app.services.site.sources import elevation, imagery
    from tests import test_site_profile as tsp
    from tests.test_site_terrain import cache_window, window_from

    block = grid.snap_block(*HOME_PIN)

    class TerrainFromTiles(tsp.ZoneAware):
        """Reads the cached grids the way the real terrain and sun sources
        do, so working out a zone touches their tiles, then takes a moment
        over them, as the real analysis does (seconds on the small server;
        a sleep here, which, like numpy, lets the other requests run)."""

        def read(self, block, pin, footprint, *, client, session=None, readings=()):
            if session is not None:
                layer_service.cached_window(session, block)
                layer_service.cached_canopy(session, block)
                time.sleep(ANALYSIS_S)
            return super().read(block, pin, footprint, client=client, readings=readings)

    sources = {**tsp.fast_sources(), **tsp.background_sources()}
    sources["terrain"] = TerrainFromTiles(sources["terrain"].readings)
    monkeypatch.setattr(vitals_mod, "_existing_weather", lambda *a, **k: None)

    with iso.db() as s:
        cache_window(s, block, window_from(lambda e, n: 0 * e + 300.0, pin=HOME_PIN))
        h = np.zeros((500, 600), np.uint8)
        h[240:260, 290:310] = 20
        import struct
        tiles.put(s, canopy_source.PROVIDER, canopy_source.DATASET_VERSION,
                  canopy_source.tile_key(block), struct.pack("<HH", *h.shape) + h.tobytes())
        tiles.put(s, imagery.SOURCE_KEY, imagery.CACHE_VERSION, imagery.tile_key(block),
                  b"\xff\xd8 not really a jpeg", ttl=imagery.TTL)
        tiles.put_json(s, imagery.SOURCE_KEY, imagery.CACHE_VERSION,
                       f"{block.key}{imagery.META_SUFFIX}", {"captured": "2023-07-01"},
                       ttl=imagery.TTL)
        s.commit()
    elevation._RECENT.clear()
    terrain._ANALYSES.clear()

    hdr = iso.a["headers"]
    with profile.use_sources(sources):
        monkeypatch.setattr(profile, "SESSION_FACTORY", iso.db)
        monkeypatch.setattr(properties, "queue_background",
                            lambda background, pid: profile.build_background(pid))
        r = iso.client.post("/properties", headers=hdr, json={
            "pin_lat": HOME_PIN[0], "pin_lng": HOME_PIN[1], "pin_source": "owner_pin"})
        assert r.status_code == 201, r.text
        pid = r.json()["id"]
        # The zone's values stay unstored, so every profile works them out.
        monkeypatch.setattr(properties, "queue_background", lambda background, pid: None)
        d = 0.0001
        z = iso.client.post(f"/properties/{pid}/zones", headers=hdr, json={
            "vegetation_type": "garden_bed",
            "box": {"west": HOME_PIN[1] - d, "south": HOME_PIN[0] - d,
                    "east": HOME_PIN[1] + d, "north": HOME_PIN[0] + d}})
        assert z.status_code == 201, z.text

        engine = _wal_engine(migrated_db_url, BUSY_S)

        def wal_session():
            with Session(engine) as s:
                yield s
        app.dependency_overrides[get_session] = wal_session

        def make_stale():
            with Session(engine) as s:
                for row in s.exec(select(GeodataTile).where(
                        GeodataTile.tile_key.startswith(block.key))).all():
                    row.last_used_at = datetime.utcnow() - STALE
                    s.add(row)
                s.commit()

        yield {"pid": pid, "headers": hdr, "block": block, "engine": engine,
               "make_stale": make_stale, "client": iso.client}

    with iso.db() as s:
        for row in s.exec(select(GeodataTile).where(
                GeodataTile.tile_key.startswith(block.key))).all():
            s.delete(row)
        s.commit()
    engine.dispose()
    elevation._RECENT.clear()
    terrain._ANALYSES.clear()


def test_the_home_screen_requests_at_once_all_answer(home):
    """The Home screen's six GETs at once, against tiles over an hour stale,
    several times over. Before the fix, some answered 500 with "database is
    locked" (and PendingRollbackError) every round."""
    pid, client, h = home["pid"], home["client"], home["headers"]
    paths = [f"/vitals?property_id={pid}", f"/properties/{pid}/site-profile",
             f"/properties/{pid}/imagery", f"/properties/{pid}/zones",
             f"/properties/{pid}/layers", "/plants/"]
    failures = []
    for round_ in range(6):
        home["make_stale"]()
        start = threading.Barrier(len(paths))

        def fetch(path):
            start.wait()
            r = client.get(path, headers=h)
            return path, r.status_code, r.text[:200]
        with ThreadPoolExecutor(len(paths)) as pool:
            results = list(pool.map(fetch, paths))
        failures += [(round_, p, code, body) for p, code, body in results if code != 200]
    assert failures == []
    # (d) the touches still happened, and were kept although these GETs
    # (/vitals, /site-profile, /zones) never commit.
    with Session(home["engine"]) as s:
        used = {r.tile_key: r.last_used_at for r in s.exec(select(GeodataTile).where(
            GeodataTile.tile_key.startswith(home["block"].key))).all()}
    b = home["block"].key
    read_by_home = {f"{b}_dem", f"{b}_dem_survey", f"{b}_chm", f"{b}_naip",
                    f"{b}_naipmeta"}
    stale = {k for k in read_by_home if datetime.utcnow() - used[k] > timedelta(minutes=5)}
    assert stale == set()
