"""Fixes after the 2026-11-15 review of the 1.2.0 build: no write lock held
across an outbound call, one United States rule for the whole app, one
background run per property, a failed survey lookup retried, the soil-line
cap on "where water collects", a moved pin's place cleared, site rows going
with a zone deleted through the old route, the property and zone caps, one
event-state row per event, and weather on Home for a property outside the
United States. No test touches the network."""
import threading
from datetime import date, datetime, timedelta

import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlmodel import Session, select

from app.models.models import (
    GeodataTile, GrowingArea, Property, SeasonEventState, SiteOverride, User)
from app.routers import properties
from app.services import coverage
from app.services import vitals as vitals_mod
from app.services.season import forecast as fcm
from app.services.season import plan as plan_mod
from app.services.site import confidence as conf
from app.services.site import grid, profile, tiles
from app.services.site import http as site_http
from app.services.site.types import Reading
from tests.season_fixtures import nws_transport
from tests.test_scoping import iso  # noqa: F401
from tests.test_site_profile import Fake, background_sources, fast_sources, rd

ARBORETUM = (38.9123, -76.9681)
NOV_15 = date(2026, 11, 15)


@pytest.fixture()
def inline(iso, monkeypatch):  # noqa: F811
    monkeypatch.setattr(profile, "SESSION_FACTORY", iso.db)
    monkeypatch.setattr(properties, "queue_background",
                        lambda background, pid: profile.build_background(pid))


@pytest.fixture()
def queued(monkeypatch):
    q: list[int] = []
    monkeypatch.setattr(properties, "queue_background", lambda background, pid: q.append(pid))
    return q


def _create(iso, who="a", pin=ARBORETUM):  # noqa: F811
    r = iso.client.post("/properties", headers=iso.__dict__[who]["headers"], json={
        "pin_lat": pin[0], "pin_lng": pin[1], "pin_source": "owner_pin"})
    assert r.status_code == 201, r.text
    return r.json()


def _delete_all_properties(iso, who="a"):  # noqa: F811
    for p in iso.client.get("/properties", headers=iso.__dict__[who]["headers"]).json():
        iso.client.delete(f"/properties/{p['id']}", headers=iso.__dict__[who]["headers"])


# --- 1. no write lock across an outbound call ------------------------------------------

class Blocking(Fake):
    """Writes a tile, then waits in "the network" until released."""

    def __init__(self, readings, entered, release):
        super().__init__(readings)
        self.entered, self.release = entered, release

    def read(self, block, pin, footprint, *, client, session=None):
        tiles.put(session, "test", "v1", f"{block.key}_blocking", b"x" * 100)
        self.entered.set()
        assert self.release.wait(10)
        return list(self.readings)


def test_other_writes_go_through_while_a_source_waits_on_the_network(iso, inline, migrated_db_url):  # noqa: F811
    entered, release = threading.Event(), threading.Event()
    src = {**fast_sources(), **background_sources()}
    src["canopy"] = Blocking([rd("canopy_shade", 0.4, "medium", "canopy")], entered, release)
    # A second connection with a short busy timeout: it fails at once if the
    # background step holds the write lock.
    other = create_engine(migrated_db_url, connect_args={"timeout": 0.5})
    with profile.use_sources(src):
        with iso.db() as s:
            pid = _create_row(s, iso.a["user_id"])
        worker = threading.Thread(target=profile.build_background, args=(pid,))
        worker.start()
        try:
            assert entered.wait(10)
            with other.begin() as conn:
                conn.execute(text("UPDATE growingarea SET name = name WHERE id = :i"),
                             {"i": iso.b["env_id"]})
        finally:
            release.set()
            worker.join(10)
    other.dispose()
    with iso.db() as s:
        assert s.get(Property, pid).profile_status["background"] == "ready"


def _create_row(s, user_id, pin=ARBORETUM):
    prop = Property(user_id=user_id, name="Lock test", pin_lat=pin[0], pin_lng=pin[1],
                    pin_source="owner_pin",
                    profile_status={"fast": "ready", "background": "pending"})
    s.add(prop)
    s.commit()
    return prop.id


def test_the_forecast_cache_is_committed_before_the_second_opinion(iso, monkeypatch):  # noqa: F811
    from app.services import weather
    prop_id = _create(iso)["id"]
    seen = {}

    async def fake_weatherkit(lat, lng, lang):
        with iso.db() as other:
            seen["cached"] = other.exec(select(fcm.ForecastCache)).first() is not None
        return None

    monkeypatch.setattr(weather, "is_configured", lambda: True)
    monkeypatch.setattr(weather, "_fetch_weatherkit", fake_weatherkit)
    prev = site_http.use_transport(lambda: nws_transport("arboretum"))
    try:
        with iso.db() as s:
            plan_mod.seasonal_plan(s, s.get(Property, prop_id), today=NOV_15)
    finally:
        site_http.use_transport(prev)
        fcm._second_opinion_memory.clear()
    assert seen == {"cached": True}  # another connection already sees it: committed


def test_the_engine_waits_for_a_lock_and_uses_write_ahead_logging(tmp_path):
    from sqlalchemy import event

    from app.db import database
    assert database.BUSY_TIMEOUT_S >= 10
    engine = create_engine(f"sqlite:///{(tmp_path / 'wal.db').as_posix()}")
    event.listen(engine, "connect", database._sqlite_pragmas)
    with engine.connect() as conn:
        assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert conn.execute(text("PRAGMA busy_timeout")).scalar() == database.BUSY_TIMEOUT_S * 1000
    engine.dispose()


# --- 2. one United States rule ----------------------------------------------------------

PLACES_IN = {"St Thomas": (18.34, -64.93), "St Croix": (17.73, -64.75),
             "Pago Pago": (-14.28, -170.70), "San Juan": (18.47, -66.10),
             "Detroit": (42.33, -83.05), "Buffalo": (42.89, -78.88),
             "Bellingham": (48.75, -122.48), "Brownsville": (25.90, -97.50),
             "Ketchikan": (55.34, -131.64), "Key West": (24.56, -81.78),
             "Arboretum": ARBORETUM, "Zilker": (30.2669, -97.7729)}
PLACES_OUT = {"Toronto": (43.65, -79.38), "Vancouver": (49.28, -123.12),
              "Monterrey": (25.67, -100.31), "Montreal": (45.50, -73.57),
              "Tijuana": (32.51, -117.04), "Nassau": (25.05, -77.35),
              "Whitehorse": (60.72, -135.05), "London": (51.5, -0.12)}


@pytest.mark.parametrize("name", sorted(PLACES_IN))
def test_united_states_places_agree_everywhere(name):
    lat, lng = PLACES_IN[name]
    assert coverage.in_united_states(lat, lng)
    assert fcm.in_united_states(lat, lng) and profile.in_united_states(lat, lng)


@pytest.mark.parametrize("name", sorted(PLACES_OUT))
def test_places_over_the_border_are_not_the_united_states(name):
    lat, lng = PLACES_OUT[name]
    assert not fcm.in_united_states(lat, lng) and not profile.in_united_states(lat, lng)


@pytest.mark.parametrize("name", ["St Thomas", "St Croix", "Pago Pago"])
def test_vitals_never_call_open_meteo_for_the_territories(iso, monkeypatch, name):  # noqa: F811
    from app.services import weather

    async def boom(*a, **k):
        raise AssertionError("Open-Meteo must not be called for United States coordinates")

    async def no_weatherkit(*a, **k):
        return None

    monkeypatch.setattr(weather, "_fetch_openmeteo", boom)
    monkeypatch.setattr(weather, "_fetch_weatherkit", no_weatherkit)
    lat, lng = PLACES_IN[name]
    with iso.db() as s:
        area = s.get(GrowingArea, iso.b["env_id"])
        area.lat, area.lng = lat, lng
        s.add(area)
        s.commit()
    # The Weather Service answers 404 here (it is down or does not cover it).
    prev = site_http.use_transport(lambda: httpx.MockTransport(
        lambda r: httpx.Response(404, json={"title": "not found"})))
    try:
        with iso.db() as s:
            out = vitals_mod.vitals(s, s.get(User, iso.b["user_id"]), None, today=NOV_15)
    finally:
        site_http.use_transport(prev)
        with iso.db() as s:
            area = s.get(GrowingArea, iso.b["env_id"])
            area.lat = area.lng = None
            s.add(area)
            s.commit()
    assert out.cards == []


# --- 3. one background run at a time ------------------------------------------------------

def test_a_refresh_during_a_run_does_not_start_a_second_one(iso, monkeypatch):  # noqa: F811
    monkeypatch.setattr(profile, "SESSION_FACTORY", iso.db)
    entered, release = threading.Event(), threading.Event()
    src = {**fast_sources(), **background_sources()}
    src["canopy"] = Blocking([rd("canopy_shade", 0.4, "medium", "canopy")], entered, release)
    runs = []
    real = profile._background

    def counting(session, prop, status, now):
        runs.append(prop.id)
        return real(session, prop, status, now)

    monkeypatch.setattr(profile, "_background", counting)
    started: list[threading.Thread] = []

    def queue(background, pid):
        t = threading.Thread(target=profile.build_background, args=(pid,))
        started.append(t)
        t.start()

    monkeypatch.setattr(properties, "queue_background", queue)
    with profile.use_sources(src):
        prop = _create(iso)
        assert entered.wait(10)
        entered.clear()
        r = iso.client.post(f"/properties/{prop['id']}/site-profile/refresh",
                            headers=iso.a["headers"])
        assert r.status_code == 202
        status = iso.client.get(f"/properties/{prop['id']}", headers=iso.a["headers"]).json()
        assert status["profile_status"]["background"] == "building"  # left alone
        assert len(runs) == 1                                       # no second run beside it
        release.set()
        for t in started:
            t.join(10)
    assert len(runs) == 2  # the asked-for run came after the first, not beside it
    body = iso.client.get(f"/properties/{prop['id']}", headers=iso.a["headers"]).json()
    assert body["profile_status"]["background"] == "ready"
    _delete_all_properties(iso)


# --- 4. a failed survey lookup is retried ----------------------------------------------------

def test_missing_survey_details_leave_the_step_partial_and_retried(iso, inline):  # noqa: F811
    src = {**fast_sources(), **background_sources()}
    src["elevation"] = Fake([Reading(
        field="elevation_window", value={"resolution_m": None}, level="low",
        provenance="public_map", source_key="3dep", source_version="dynamic service",
        method="test", reason_codes=("resolution_unknown",))])
    with profile.use_sources(src):
        prop = _create(iso)
    with iso.db() as s:
        st = s.get(Property, prop["id"]).profile_status
    assert st["sources"]["elevation"] == "partial"
    assert st["background"] == "partial" and st.get("next_retry_at")
    _delete_all_properties(iso)


def test_the_real_elevation_source_marks_a_failed_getsamples():
    from app.services.site.sources import elevation
    block = grid.snap_block(*ARBORETUM)
    win = elevation.ElevationWindow(
        block=block, z=__import__("numpy").zeros((4, 4)), valid=__import__("numpy").ones((4, 4), bool),
        resolution_m=None, raster_id=None, title=None, year=None, fetched_by="block", meta={})
    r = elevation.window_reading(win)
    assert "resolution_unknown" in r.reason_codes
    assert set(r.reason_codes) & profile.INCOMPLETE_CODES


# --- 5. where water collects near a soil map line ---------------------------------------------

def test_water_collects_near_a_soil_line_is_rough_when_soil_went_in():
    good = conf.Facts(default_footprint=False, resolution_m=1.0, elevation_used=True,
                      soil_signals_agree=True, soil_used=True)
    assert conf.decide("water_collects", "high", good).confidence == "good_estimate"
    near = conf.Facts(**{**good.__dict__, "near_soil_line": True})
    d = conf.decide("water_collects", "high", near)
    assert d.confidence == "rough_estimate" and "near_soil_map_line" in d.caps
    terrain_only = conf.Facts(**{**near.__dict__, "soil_used": False})
    assert conf.decide("water_collects", "high", terrain_only).confidence == "good_estimate"


def test_the_arboretum_drawn_bed_reads_rough_by_the_soil_line(iso, inline):  # noqa: F811
    with profile.use_sources({**fast_sources(), **background_sources()}):
        prop = _create(iso)
        whole = prop["whole_lot_zone_id"]
        box = grid.default_footprint_box(*ARBORETUM)
        r = iso.client.patch(f"/properties/{prop['id']}/zones/{whole}", headers=iso.a["headers"],
                             json={"box": box})
        assert r.status_code == 200
        iso.client.post(f"/properties/{prop['id']}/site-profile/refresh", headers=iso.a["headers"])
        body = iso.client.get(f"/properties/{prop['id']}/site-profile",
                              headers=iso.a["headers"]).json()
    rows = {v["field"]: v for v in body["values"] if v.get("zone_id") is None}
    # The fixture pin is 16.6 metres from a soil line whose neighbour differs.
    assert rows["soil_drainage"]["confidence"] == "rough_estimate"
    assert rows["water_collects"]["confidence"] == "rough_estimate"
    assert "edge of the mapped soil area" in rows["water_collects"]["reason"]
    _delete_all_properties(iso)


# --- 6. a moved pin clears the old place ---------------------------------------------------

def test_moving_the_pin_clears_city_and_time_zone_and_the_zones_get_the_new_place(iso, queued):  # noqa: F811
    prop = _create(iso)
    with iso.db() as s:
        p = s.get(Property, prop["id"])
        p.city, p.region, p.country, p.timezone = "Washington", "DC", "United States", "America/New_York"
        s.add(p)
        for z in s.exec(select(GrowingArea).where(GrowingArea.property_id == p.id)).all():
            z.city, z.region = "Washington", "DC"
            s.add(z)
        s.commit()
    r = iso.client.patch(f"/properties/{prop['id']}", headers=iso.a["headers"],
                         json={"pin_lat": 30.2669, "pin_lng": -97.7729})
    body = r.json()
    assert (body["city"], body["region"], body["timezone"]) == (None, None, None)
    prev = site_http.use_transport(lambda: nws_transport("zilker"))
    try:
        with iso.db() as s:
            plan_mod.seasonal_plan(s, s.get(Property, prop["id"]), today=NOV_15)
    finally:
        site_http.use_transport(prev)
    with iso.db() as s:
        p = s.get(Property, prop["id"])
        assert p.city and p.city != "Washington" and p.timezone == "America/Chicago"
        for z in s.exec(select(GrowingArea).where(GrowingArea.property_id == p.id)).all():
            assert z.city == p.city
    _delete_all_properties(iso)


# --- 7. the old delete route takes the zone's site rows -----------------------------------------

def test_old_route_delete_takes_the_zones_corrections_with_it(iso, queued):  # noqa: F811
    prop = _create(iso)
    box = grid.default_footprint_box(*ARBORETUM)
    small = {"west": box["west"], "south": box["south"],
             "east": box["west"] + 0.0001, "north": box["south"] + 0.0001}
    zone = iso.client.post(f"/properties/{prop['id']}/zones", headers=iso.a["headers"],
                           json={"vegetation_type": "garden_bed", "box": small}).json()
    r = iso.client.put(f"/properties/{prop['id']}/overrides", headers=iso.a["headers"],
                       json={"zone_id": zone["id"], "field": "sun", "value": "shade", "method": "tap"})
    assert r.status_code == 200
    assert iso.client.delete(f"/growing-areas/{zone['id']}", headers=iso.a["headers"]).status_code == 204
    with iso.db() as s:
        left = s.exec(select(SiteOverride).where(SiteOverride.zone_id == zone["id"])).all()
    assert left == []
    again = iso.client.post(f"/properties/{prop['id']}/zones", headers=iso.a["headers"],
                            json={"vegetation_type": "garden_bed", "box": small}).json()
    sun = [v for v in again["values"] if v["field"] == "sun"]
    assert all(v["confidence"] != "you_told_us" for v in sun)
    _delete_all_properties(iso)


# --- 10. caps ---------------------------------------------------------------------------------

def test_an_account_holds_at_most_five_properties(iso, queued):  # noqa: F811
    _delete_all_properties(iso)
    for i in range(properties.MAX_PROPERTIES_PER_ACCOUNT):
        _create(iso, pin=(38.9 + i * 0.01, -76.96))
    r = iso.client.post("/properties", headers=iso.a["headers"], json={
        "pin_lat": 39.5, "pin_lng": -76.9, "pin_source": "owner_pin"})
    assert r.status_code == 409 and "Delete one" in r.json()["detail"]
    _delete_all_properties(iso)


def test_the_site_routes_carry_a_rate_limit(iso, queued, monkeypatch):  # noqa: F811
    from app.rate_limit import limiter
    monkeypatch.setattr(properties, "_imagery_module", lambda: None)  # answers 503, no network
    limiter.reset()
    limiter.enabled = True
    try:
        codes = [iso.client.get("/imagery/block", headers=iso.a["headers"],
                                params={"lat": 38.9, "lng": -76.9}).status_code
                 for _ in range(12)]
    finally:
        limiter.enabled = False
        limiter.reset()
    assert codes[:10] == [503] * 10 and 429 in codes


def test_prune_reads_no_payloads_and_keeps_a_fresh_aerial_image(iso):  # noqa: F811
    lonely = grid.snap_block(44.3123, -111.4456).key
    old = datetime.utcnow() - timedelta(days=1)
    with iso.db() as s:
        tiles.put(s, "naip", "v1", lonely + "_img", b"fresh")
        tiles.put(s, "naip", "v1", lonely + "_img_old", b"old", now=old)
        tiles.put(s, "3dep", "v1", lonely + "_dem", b"dem")
        s.commit()
        statements = []
        from sqlalchemy import event
        listener = lambda *a: statements.append(a[2])  # noqa: E731
        event.listen(s.get_bind(), "before_cursor_execute", listener)
        try:
            tiles.prune_unused(s)
        finally:
            event.remove(s.get_bind(), "before_cursor_execute", listener)
        s.commit()
        keys = {t.tile_key for t in s.exec(select(GeodataTile)).all()}
    assert lonely + "_img" in keys
    assert lonely + "_img_old" not in keys and lonely + "_dem" not in keys
    selects = [q for q in statements if q.lstrip().upper().startswith("SELECT")
               and "geodata_tile" in q]
    assert selects and all("payload" not in q for q in selects)
    with iso.db() as s:
        tiles.prune_unused(s, keep_recent_imagery=False)
        s.commit()
        assert lonely + "_img" not in {t.tile_key for t in s.exec(select(GeodataTile)).all()}


# --- 11. one event-state row per event ---------------------------------------------------------

def test_two_rows_for_one_event_are_refused(iso, queued):  # noqa: F811
    from sqlalchemy.exc import IntegrityError
    prop = _create(iso)
    with iso.db() as s:
        s.add(SeasonEventState(property_id=prop["id"], zone_id=None, event_key="k:2026:fall",
                               status="done"))
        s.commit()
        s.add(SeasonEventState(property_id=prop["id"], zone_id=None, event_key="k:2026:fall",
                               status="done"))
        with pytest.raises(IntegrityError):
            s.commit()
        s.rollback()
        # The claim used by the plan and the route answers with the row that is there.
        row = plan_mod.claim_state(s, prop["id"], "k:2026:fall", "not_needed", datetime.utcnow())
        assert row.status == "done"
        s.commit()
        assert len(s.exec(select(SeasonEventState)
                          .where(SeasonEventState.property_id == prop["id"])).all()) == 1
    _delete_all_properties(iso)


# --- 8. weather on Home for land outside the United States ----------------------------------

def test_land_outside_the_united_states_keeps_weather_on_home(iso, queued, monkeypatch):  # noqa: F811
    seen = []

    def fake(lat, lng, **kw):
        seen.append((lat, lng, kw))
        return {"current": {"temp_f": 50}, "attribution": {"text": "Weather data by Open-Meteo.com",
                                                          "url": "https://open-meteo.com/"},
                "daily": [{"date": "2026-11-15", "high_f": 55, "low_f": 33,
                           "precip_chance_pct": 10, "condition": "Clear"}]}

    monkeypatch.setattr(vitals_mod, "_existing_weather", fake)
    prop = _create(iso, pin=(51.5, -0.12))
    with iso.db() as s:
        out = vitals_mod.vitals(s, s.get(User, iso.a["user_id"]), s.get(Property, prop["id"]),
                                today=NOV_15)
        notes = profile.site_profile(s, s.get(Property, prop["id"])).notes
    keys = [c.key for c in out.cards]
    assert "weather_now" in keys and "frost" in keys and out.forecast is not None
    assert seen == [(51.5, -0.12, {})]
    assert not any("forecast alone" in n for n in notes)
    _delete_all_properties(iso)


def test_a_point_the_weather_service_does_not_cover_uses_the_existing_service(iso, queued, monkeypatch):  # noqa: F811
    seen = []
    monkeypatch.setattr(vitals_mod, "_existing_weather",
                        lambda lat, lng, **kw: seen.append(kw) or None)
    prev = site_http.use_transport(lambda: httpx.MockTransport(
        lambda r: httpx.Response(404, json={"title": "Data Unavailable For Requested Point"})))
    try:
        prop = _create(iso, pin=(43.0, -79.0))  # inside the rough boxes, near Niagara
        with iso.db() as s:
            vitals_mod.vitals(s, s.get(User, iso.a["user_id"]), s.get(Property, prop["id"]),
                              today=NOV_15)
            # Read the cache at the same clock the report was built with
            # (vitals runs at 14:00 on `today`); the entry lives 3 hours, so
            # checking it against the real clock fails later in the day.
            assert fcm.outside_coverage(
                s, 43.0, -79.0, now=datetime(NOV_15.year, NOV_15.month, NOV_15.day, 14, 0))
    finally:
        site_http.use_transport(prev)
    assert seen == [{}]  # the full chain: the Weather Service says it is not a United States point
    _delete_all_properties(iso)


def test_vitals_say_whether_land_can_be_added(iso, monkeypatch):  # noqa: F811
    from app.config import get_settings
    r = iso.client.get("/vitals", headers=iso.b["headers"])
    assert r.status_code == 200 and r.json()["can_add_land"] is True
    monkeypatch.setattr(get_settings(), "site_profile_enabled", False)
    r = iso.client.get("/vitals", headers=iso.b["headers"])
    assert r.status_code == 200 and r.json()["can_add_land"] is False


def test_land_on_without_the_season_is_refused_at_start(monkeypatch):
    from app.config import Settings
    monkeypatch.setenv("SITE_PROFILE_ENABLED", "true")
    monkeypatch.setenv("SEASON_PLAN_ENABLED", "false")
    with pytest.raises(ValueError):
        Settings()


# --- 13. a zone added without drawing --------------------------------------------------------

def test_a_zone_added_without_drawing_counts_as_the_default_footprint(iso, queued):  # noqa: F811
    prop = _create(iso)
    box = grid.default_footprint_box(*ARBORETUM)
    z = iso.client.post(f"/properties/{prop['id']}/zones", headers=iso.a["headers"],
                        json={"vegetation_type": "grass", "box": box, "drawn": False}).json()
    assert z["boundary_source"] == "default"
    drawn = iso.client.post(f"/properties/{prop['id']}/zones", headers=iso.a["headers"],
                            json={"vegetation_type": "grass", "box": box}).json()
    assert drawn["boundary_source"] == "owner"
    _delete_all_properties(iso)
