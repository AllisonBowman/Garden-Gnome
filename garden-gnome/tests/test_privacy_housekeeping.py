"""What the 1.2.0 privacy policy says about logs and cached data, held true.

The access log never records a query string (GET /imagery/block carries the
exact pin there), the outbound guard's refusal never quotes the coordinate
it refused, and an hourly clean-out deletes expired forecasts, expired
tiles and unused tiles (keeping an aerial image fetched in the last two
hours). No test touches the network, and none sleeps: the clean-out's
pace comes from an injected clock."""
import logging
from datetime import datetime, timedelta

import pytest
from sqlmodel import select
from uvicorn.logging import AccessFormatter

from app import main
from app.config import get_settings
from app.models.models import ForecastCache, GeodataTile, Property
from app.services import housekeeping as hk
from app.services.site import grid, tiles
from app.services.site import http as site_http
from tests.test_scoping import iso  # noqa: F401

PIN_QUERY = "/imagery/block?lat=38.9123456&lng=-76.9681234"
COORD_DIGITS = ("38", "9123456", "912", "76", "9681234", "968")


# --- the access log ---------------------------------------------------------------

def _access_record(full_path: str) -> logging.LogRecord:
    # The record uvicorn's h11/httptools protocols write for each response.
    return logging.getLogger("uvicorn.access").makeRecord(
        "uvicorn.access", logging.INFO, __file__, 1,
        '%s - "%s %s HTTP/%s" %d',
        ("203.0.113.5:50000", "GET", full_path, "1.1", 200), None)


def _format_through_access_logger(record: logging.LogRecord) -> list[str]:
    lines: list[str] = []

    class Capture(logging.Handler):
        def emit(self, rec):
            lines.append(self.format(rec))

    handler = Capture()
    handler.setFormatter(AccessFormatter(
        '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
        use_colors=False))
    access = logging.getLogger("uvicorn.access")
    access.addHandler(handler)
    try:
        access.handle(record)  # filters run here, as for a real request
    finally:
        access.removeHandler(handler)
    return lines


def test_the_access_log_keeps_the_path_and_drops_the_pin():
    assert any(isinstance(f, main.DropQueryString)
               for f in logging.getLogger("uvicorn.access").filters)
    [line] = _format_through_access_logger(_access_record(PIN_QUERY))
    assert '"GET /imagery/block HTTP/1.1" 200' in line
    assert "203.0.113.5:50000" in line
    assert "?" not in line and "lat=" not in line and "lng=" not in line
    for digits in COORD_DIGITS:
        assert digits not in line, (digits, line)


def test_the_filter_leaves_other_records_alone():
    f = main.DropQueryString()
    plain = _access_record("/properties/3")
    assert f.filter(plain) and plain.args[2] == "/properties/3"
    for args in (None, ("only", "three", "args"), ({"path": "/x?lat=1.23456"},)):
        rec = logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1,
                                "msg", args, None)
        before = rec.args
        assert f.filter(rec) is True and rec.args is before
    odd = logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1,
                            "%s %s %s %s %s", ("a", "b", 3, "d", "e"), None)
    assert f.filter(odd) and odd.args == ("a", "b", 3, "d", "e")


def test_installing_the_filters_twice_adds_one():
    main.install_log_filters()
    main.install_log_filters()
    access = logging.getLogger("uvicorn.access")
    assert sum(isinstance(f, main.DropQueryString) for f in access.filters) == 1
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING


# --- the outbound guard's refusal ------------------------------------------------------

@pytest.mark.parametrize("kwargs, names", [
    ({"params": {"lat": 38.9123456, "lng": -76.9681234},
      "coords": {"lat": site_http.Coord.LAT, "lng": site_http.Coord.LNG}}, "'lat'"),
    ({"params": {"geometry": "-76.9681234,38.9123456"},
      "coords": {"geometry": site_http.Coord.POINT_LNGLAT}}, "'geometry'"),
    ({"params": {"where": "x near 38.9123456"}}, "'where'"),
    ({"params": {"point": "38.9123,-76.9681"},
      "coords": {"point": site_http.Coord.WEATHER_POINT}}, "'point'"),
])
def test_a_refusal_names_the_parameter_and_not_the_coordinate(kwargs, names):
    with pytest.raises(site_http.OutboundRefused) as caught:
        site_http.guard("https://example.invalid/query", **kwargs)
    message = str(caught.value)
    assert names in message
    for digits in ("9123", "9681", "38.9", "76.9"):
        assert digits not in message, message


def test_a_refused_url_path_says_where_and_not_what():
    with pytest.raises(site_http.OutboundRefused) as caught:
        site_http.guard("https://example.invalid/points/38.9123456,-76.9681234")
    message = str(caught.value)
    assert "URL path" in message and "9123" not in message and "9681" not in message


# --- the hourly clean-out ------------------------------------------------------------

class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


@pytest.fixture()
def keeper(iso):  # noqa: F811
    clock = Clock()
    now = datetime.utcnow()
    return hk.Housekeeping(session_factory=iso.db, clock=clock,
                           utcnow=lambda: now), clock, now


def _forecast(s, cell, expires_at):
    s.add(ForecastCache(cell_key=cell, provider="nws", payload={"x": 1},
                        fetched_at=expires_at - timedelta(hours=3),
                        expires_at=expires_at))


def _keys(iso, model, field):  # noqa: F811
    with iso.db() as s:
        return {getattr(r, field) for r in s.exec(select(model)).all()}


def test_expired_forecasts_go_and_live_ones_stay(iso, keeper):  # noqa: F811
    house, _, now = keeper
    with iso.db() as s:
        _forecast(s, "hk_old", now - timedelta(minutes=1))
        _forecast(s, "hk_live", now + timedelta(hours=2))
        s.commit()
    done = house.run_if_due()
    assert done["forecasts"] >= 1
    cells = _keys(iso, ForecastCache, "cell_key")
    assert "hk_live" in cells and "hk_old" not in cells
    with iso.db() as s:
        for r in s.exec(select(ForecastCache).where(ForecastCache.cell_key == "hk_live")):
            s.delete(r)
        s.commit()


def _in_use_property(iso, pin):  # noqa: F811
    with iso.db() as s:
        p = Property(user_id=iso.a["user_id"], pin_lat=pin[0], pin_lng=pin[1])
        s.add(p)
        s.commit()
        return p.id


def _drop_property(iso, pid):  # noqa: F811
    with iso.db() as s:
        s.delete(s.get(Property, pid))
        s.commit()


def test_expired_tiles_go_in_batches_and_live_ones_stay(iso, keeper, monkeypatch):  # noqa: F811
    house, _, now = keeper
    pin = (44.4123, -110.5456)
    block = grid.snap_block(*pin).key
    pid = _in_use_property(iso, pin)  # so prune_unused leaves these alone
    with iso.db() as s:
        for i in range(5):
            tiles.put(s, "3dep", "v1", f"{block}_hk_old{i}", b"old",
                      ttl=timedelta(days=1), now=now - timedelta(days=2))
        tiles.put(s, "3dep", "v1", f"{block}_hk_live", b"live", ttl=timedelta(days=90), now=now)
        tiles.put(s, "3dep", "v1", f"{block}_hk_forever", b"keep", ttl=None, now=now)
        s.commit()
    statements = []
    from sqlalchemy import event
    listener = lambda *a: statements.append(a[2])  # noqa: E731
    event.listen(iso.engine, "before_cursor_execute", listener)
    try:
        assert hk.prune_expired_tiles(iso.db, now, batch=2) >= 5
    finally:
        event.remove(iso.engine, "before_cursor_execute", listener)
    keys = _keys(iso, GeodataTile, "tile_key")
    assert f"{block}_hk_live" in keys and f"{block}_hk_forever" in keys
    assert not any(f"{block}_hk_old{i}" in keys for i in range(5))
    selects = [q for q in statements if q.lstrip().upper().startswith("SELECT")
               and "geodata_tile" in q]
    assert selects and all("payload" not in q for q in selects)
    deletes = [q for q in statements if q.lstrip().upper().startswith("DELETE")]
    assert len(deletes) >= 3  # 5 rows at 2 a batch: three transactions
    _drop_property(iso, pid)
    with iso.db() as s:
        tiles.prune_unused(s, keep_recent_imagery=False)
        s.commit()


def test_an_unused_old_image_goes_and_one_in_use_stays(iso, keeper):  # noqa: F811
    house, _, now = keeper
    used_pin = (45.6123, -109.2456)
    used = grid.snap_block(*used_pin).key
    lonely = grid.snap_block(46.1123, -108.7456).key
    pid = _in_use_property(iso, used_pin)
    three_hours_ago = now - timedelta(hours=3)
    with iso.db() as s:
        tiles.put(s, "naip", "v1", f"{used}_hk_img", b"used", now=three_hours_ago)
        tiles.put(s, "naip", "v1", f"{lonely}_hk_img_old", b"old", now=three_hours_ago)
        tiles.put(s, "naip", "v1", f"{lonely}_hk_img_new", b"new",
                  now=now - timedelta(minutes=30))
        s.commit()
    done = house.run_if_due()
    assert done["unused_tiles"] >= 1
    keys = _keys(iso, GeodataTile, "tile_key")
    assert f"{used}_hk_img" in keys
    assert f"{lonely}_hk_img_new" in keys       # under two hours old: kept
    assert f"{lonely}_hk_img_old" not in keys
    _drop_property(iso, pid)
    with iso.db() as s:
        tiles.prune_unused(s, keep_recent_imagery=False)
        s.commit()


def test_one_failing_job_does_not_stop_the_others(iso, keeper, monkeypatch):  # noqa: F811
    house, _, now = keeper
    lonely = grid.snap_block(47.3123, -107.1456).key
    ran = []

    def broken(session_factory, now):
        ran.append("expired_tiles")
        raise RuntimeError("disk on fire")

    monkeypatch.setattr(hk, "prune_expired_tiles", broken)
    with iso.db() as s:
        _forecast(s, "hk_fail_old", now - timedelta(minutes=1))
        tiles.put(s, "3dep", "v1", f"{lonely}_hk_dem", b"dem", now=now)
        s.commit()
    done = house.run_if_due()
    assert ran == ["expired_tiles"]
    assert done["expired_tiles"] == hk.FAILED
    assert isinstance(done["forecasts"], int) and isinstance(done["unused_tiles"], int)
    assert "hk_fail_old" not in _keys(iso, ForecastCache, "cell_key")
    assert f"{lonely}_hk_dem" not in _keys(iso, GeodataTile, "tile_key")


def test_it_runs_at_most_once_an_hour(iso, keeper, monkeypatch):  # noqa: F811
    house, clock, _ = keeper
    calls = []
    monkeypatch.setattr(hk, "prune_forecasts", lambda f, now: calls.append("f") or 0)
    monkeypatch.setattr(hk, "prune_expired_tiles", lambda f, now: calls.append("e") or 0)
    monkeypatch.setattr(hk, "prune_unused_tiles", lambda f, now: calls.append("u") or 0)
    assert house.run_if_due() is not None
    for step in (300, 600, 1800, 3599):
        clock.t = 1000.0 + step
        assert house.run_if_due() is None
    clock.t = 1000.0 + 3600
    assert house.run_if_due() is not None
    clock.t = 1000.0 + 3600 + 3599
    assert house.run_if_due() is None
    assert calls == ["f", "e", "u", "f", "e", "u"]


def test_each_job_waits_on_its_own_flag(iso, keeper, monkeypatch):  # noqa: F811
    house, clock, _ = keeper
    for name in ("prune_forecasts", "prune_expired_tiles", "prune_unused_tiles"):
        monkeypatch.setattr(hk, name, lambda f, now: 0)
    monkeypatch.setattr(get_settings(), "site_profile_enabled", False)
    assert set(house.run_if_due()) == {"forecasts"}
    clock.t += 3600
    monkeypatch.setattr(get_settings(), "site_profile_enabled", True)
    monkeypatch.setattr(get_settings(), "season_plan_enabled", False)
    assert set(house.run_if_due()) == {"expired_tiles", "unused_tiles"}


# --- the timer -------------------------------------------------------------------------

def test_a_failed_retry_pass_does_not_stop_the_clean_out(monkeypatch):
    from app.services.site import profile, tiles as site_tiles

    def boom():
        raise RuntimeError("retry broke")

    monkeypatch.setattr(site_tiles, "check_volume", lambda: None)
    monkeypatch.setattr(profile, "run_due_retries", boom)

    class Spy:
        runs = 0

        def run_if_due(self):
            Spy.runs += 1
            raise RuntimeError("clean-out broke too")

    main._background_pass(Spy())  # neither failure escapes
    assert Spy.runs == 1


def test_the_season_flag_alone_starts_the_timer_without_retries(monkeypatch):
    import threading

    from app.services.site import profile

    started = []

    class FakeThread:
        def __init__(self, target, name, daemon):
            self.target = target
            started.append(name)

        def start(self):
            pass

    monkeypatch.setattr(threading, "Thread", FakeThread)
    monkeypatch.setattr(get_settings(), "site_profile_enabled", False)
    monkeypatch.setattr(get_settings(), "season_plan_enabled", True)
    main._start_site_profile_retries()
    assert started == ["site-profile-retries"]

    retried = []
    monkeypatch.setattr(profile, "run_due_retries", lambda: retried.append(1))

    class Spy:
        runs = 0

        def run_if_due(self):
            Spy.runs += 1

    main._background_pass(Spy())
    assert retried == [] and Spy.runs == 1

    started.clear()
    monkeypatch.setattr(get_settings(), "season_plan_enabled", False)
    main._start_site_profile_retries()
    assert started == []


# --- what a failed database write may say, and where the aerial image is asked for ---

def test_a_failed_write_does_not_put_the_values_in_the_error_text():
    """SQLAlchemy would otherwise add "[parameters: (38.89..., -77.03...)]" to
    the error, and that error is logged."""
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError
    from sqlmodel import Session

    from app.db.database import engine

    with Session(engine) as s:
        with pytest.raises(SQLAlchemyError) as caught:
            s.execute(text("insert into no_such_table (lat, lng) values (:lat, :lng)"),
                      {"lat": 38.8976543, "lng": -77.0365432})
    message = str(caught.value)
    assert "38.8976543" not in message and "77.0365432" not in message


def test_no_aerial_image_is_asked_for_outside_the_united_states(iso):  # noqa: F811
    before = site_http.requests_sent()
    r = iso.client.get("/imagery/block", headers=iso.a["headers"],
                       params={"lat": 48.8566, "lng": 2.3522})  # Paris
    assert r.status_code == 503 and "aerial image" in r.json()["detail"]
    assert site_http.requests_sent() == before
