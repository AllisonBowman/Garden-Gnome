"""The seasonal plan and Home vitals with a database: the Weather Service
forecast and its three-hour cache, the property's place filled from the
lookup, owner answers through the route, the forecast-seen fallback for
"happened", no stored Apple data, and every response walked for reason and
source. The network is replaced by recorded fixtures from the two landmarks."""
from datetime import date, datetime, timedelta

import httpx
import pytest
from sqlmodel import select

from app.models.models import (
    ForecastCache, GrowingArea, ObservedCellSeason, Property, ProviderUsage,
    SeasonEventState, User)
from app.routers import properties
from app.services import vitals as vitals_mod
from app.services.season import forecast as fcm
from app.services.season import plan as plan_mod
from app.services.site import http as site_http
from tests.explained_walker import assert_explained
from tests.season_fixtures import ARBORETUM, ZILKER, nws_transport
from tests.test_scoping import iso  # noqa: F401

NOV_15 = date(2026, 11, 15)


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, migrated_db_url):
    monkeypatch.setattr(properties, "queue_background", lambda background, pid: None)
    fcm._second_opinion_memory.clear()
    from sqlmodel import Session, create_engine
    engine = create_engine(migrated_db_url)

    def clear():
        with Session(engine) as s:
            for r in s.exec(select(ForecastCache)).all():
                s.delete(r)
            s.commit()
    clear()
    yield
    clear()
    fcm._second_opinion_memory.clear()


def _create(iso, who="a", pin=ARBORETUM, **body):  # noqa: F811
    r = iso.client.post("/properties", headers=iso.__dict__[who]["headers"], json={
        "pin_lat": pin[0], "pin_lng": pin[1], "pin_source": "owner_pin", **body})
    assert r.status_code == 201, r.text
    return r.json()


def _use(name, calls=None, fail=False):
    return site_http.use_transport(lambda: nws_transport(name, calls=calls, fail=fail))


def test_plan_reads_the_weather_service_and_caches_it(iso):  # noqa: F811
    prop = _create(iso, lot_contents=["trees_that_drop_leaves", "lawn", "garden_beds"])
    calls: list[str] = []
    prev = _use("arboretum", calls)
    try:
        with iso.db() as s:
            p = s.get(Property, prop["id"])
            plan = plan_mod.seasonal_plan(s, p, today=NOV_15)
            assert plan.forecast is not None and plan.forecast.provider == "nws"
            assert plan.forecast.provider_name == "National Weather Service"
            assert len(plan.forecast.days) == 7
            assert plan.forecast.days[0].frost_risk == "frost"       # 35 F tonight
            first = len(calls)
            assert first == 3                                         # points, grid, text
            assert all(".91,-76.97" in c for c in calls[:1])        # the weather cell only
            plan_mod.seasonal_plan(s, p, today=NOV_15)
            assert len(calls) == first                                # served from the cache
            rows = s.exec(select(ForecastCache)).all()
            assert {r.provider for r in rows} == {"nws", "nws_points"}
            for r in rows:
                assert r.cell_key == "wx2_3891_-7697"
                assert r.expires_at - r.fetched_at == timedelta(hours=3)
            s.refresh(p)
            assert (p.city, p.region, p.country, p.timezone) == (
                "Washington", "DC", "United States", "America/New_York")
            body = plan.model_dump(mode="json")
            assert_explained(body)
            types = {e["type"] for e in body["events"]}
            assert {"first_frost", "first_freeze", "hard_freeze", "fall_hardening", "leaf_drop",
                    "dormancy", "last_frost", "spring_emergence", "spring_cleanup"} <= types
            assert plan.alerts and all(a.built_from_forecast_at for a in plan.alerts)
    finally:
        site_http.use_transport(prev)


def test_cache_expires_after_three_hours(iso):  # noqa: F811
    prop = _create(iso)
    calls: list[str] = []
    prev = _use("arboretum", calls)
    try:
        with iso.db() as s:
            t0 = datetime(2026, 11, 15, 14)
            fcm.get_forecast(s, *ARBORETUM, now=t0)
            n = len(calls)
            fcm.get_forecast(s, *ARBORETUM, now=t0 + timedelta(hours=2, minutes=59))
            assert len(calls) == n
            fcm.get_forecast(s, *ARBORETUM, now=t0 + timedelta(hours=3, minutes=1))
            assert len(calls) == 2 * n  # the points lookup expired too: all three again
            s.rollback()
    finally:
        site_http.use_transport(prev)
    assert prop


def test_no_forecast_still_renders_from_normals(iso):  # noqa: F811
    prop = _create(iso, pin=ZILKER)
    prev = _use("zilker", fail=True)
    try:
        with iso.db() as s:
            plan = plan_mod.seasonal_plan(s, s.get(Property, prop["id"]), today=NOV_15)
    finally:
        site_http.use_transport(prev)
    assert plan.forecast is None and plan.alerts == []
    assert any("typical dates" in n for n in plan.notes)
    assert all(e.status != "forecast" for e in plan.events)
    assert_explained(plan.model_dump(mode="json"))


def test_zilker_mid_november_has_no_frost_in_the_forecast(iso):  # noqa: F811
    prop = _create(iso, pin=ZILKER)
    prev = _use("zilker")
    try:
        with iso.db() as s:
            p = s.get(Property, prop["id"])
            plan = plan_mod.seasonal_plan(s, p, today=NOV_15)
            s.refresh(p)
            assert (p.city, p.region, p.timezone) == ("Austin", "TX", "America/Chicago")
    finally:
        site_http.use_transport(prev)
    assert all(d.frost_risk == "none" for d in plan.forecast.days)
    by = {e.event_key: e for e in plan.events}
    assert by["first_frost:2026:fall"].status in ("expected", "typically_around")
    assert plan.alerts == []


def test_a_cold_night_seen_in_the_forecast_reads_happened_next_day(iso):  # noqa: F811
    prop = _create(iso)
    prev = _use("arboretum")
    try:
        with iso.db() as s:
            plan_mod.seasonal_plan(s, s.get(Property, prop["id"]), today=NOV_15)
            row = s.exec(select(SeasonEventState).where(
                SeasonEventState.property_id == prop["id"])).all()
            assert [(r.event_key, r.status, r.band, r.provider_name, r.observed_on) for r in row] == [
                ("first_frost:2026:fall", "seen_in_forecast", "frost", "National Weather Service",
                 NOV_15)]
    finally:
        site_http.use_transport(prev)
    with iso.db() as s:
        plan = plan_mod.seasonal_plan(s, s.get(Property, prop["id"]), today=NOV_15 + timedelta(days=1))
    frost = next(e for e in plan.events if e.event_key == "first_frost:2026:fall")
    assert frost.status == "happened" and frost.explained.confidence == "rough_estimate"
    assert "Not measured at your place" in frost.explained.display
    # The owner can say it did not happen, through the route.
    r = iso.client.put(f"/properties/{prop['id']}/seasonal-plan/events/first_frost:2026:fall",
                       headers=iso.a["headers"], json={"state": "not_yet"})
    assert r.status_code == 200 and r.json()["status"] != "happened"


def test_owner_answers_persist_through_the_route(iso, monkeypatch):  # noqa: F811
    monkeypatch.setattr(plan_mod, "_clock", lambda prop, today: (datetime(2026, 11, 15, 14), NOV_15))
    prop = _create(iso)
    h = iso.a["headers"]
    plan = iso.client.get(f"/properties/{prop['id']}/seasonal-plan", headers=h)
    assert plan.status_code == 200
    assert_explained(plan.json())
    url = f"/properties/{prop['id']}/seasonal-plan/events/leaf_drop:2026:fall"
    r = iso.client.put(url, headers=h, json={"state": "done"})
    assert r.status_code == 200 and r.json()["status"] == "done"
    assert all(t["state"] == "done" for t in r.json()["tasks"])
    assert "clear" in r.json()["owner_actions"]
    r = iso.client.put(f"/properties/{prop['id']}/seasonal-plan/events/first_freeze:2026:fall",
                       headers=h, json={"state": "happened", "observed_on": "2026-11-12"})
    assert r.json()["status"] == "happened"
    assert r.json()["explained"]["confidence_label"] == "You told us"
    plan = iso.client.get(f"/properties/{prop['id']}/seasonal-plan", headers=h).json()
    frost = next(e for e in plan["events"] if e["event_key"] == "first_frost:2026:fall")
    assert frost["status"] == "happened"  # a freeze counts as a frost too
    r = iso.client.put(url, headers=h, json={"state": "clear"})
    assert r.json()["status"] == "happening"
    assert iso.client.put(f"/properties/{prop['id']}/seasonal-plan/events/leaf_drop:1999:fall",
                          headers=h, json={"state": "done"}).status_code == 404


def test_no_stored_row_holds_an_apple_source(iso, monkeypatch):  # noqa: F811
    from app.services import weather

    async def fake_weatherkit(lat, lng, lang):
        assert (lat, lng) == (38.91, -76.97)
        return {"current": {}, "attribution": weather.ATTRIBUTION,
                "daily": [{"date": "2026-11-16", "low_f": 34}, {"date": "2026-11-17", "low_f": 33}]}

    monkeypatch.setattr(weather, "is_configured", lambda: True)
    monkeypatch.setattr(weather, "_fetch_weatherkit", fake_weatherkit)
    prop = _create(iso)
    prev = _use("arboretum")
    try:
        with iso.db() as s:
            plan = plan_mod.seasonal_plan(s, s.get(Property, prop["id"]), today=NOV_15)
            fc = fcm._second_opinion_memory["wx2_3891_-7697"][1]
            assert fc == {"2026-11-15": 34, "2026-11-16": 33}  # filed under the night before
            for row in s.exec(select(ForecastCache)).all():
                blob = f"{row.provider} {row.payload}".lower()
                assert "apple" not in blob and "weatherkit" not in blob
            for row in s.exec(select(SeasonEventState)).all():
                assert "apple" not in f"{row.provider_name}".lower()
            assert s.exec(select(ObservedCellSeason)).all() == []
            usage = s.exec(select(ProviderUsage).where(ProviderUsage.provider == "weatherkit")).one()
            assert usage.calls >= 1
            with pytest.raises(ValueError):
                fcm._cache_put(s, "wx2_1_1", "weatherkit", {}, datetime.utcnow())
            s.rollback()
    finally:
        site_http.use_transport(prev)
    assert_explained(plan.model_dump(mode="json"))


def test_plan_never_calls_open_meteo(iso, monkeypatch):  # noqa: F811
    from app.services import weather

    async def boom(*a, **k):
        raise AssertionError("Open-Meteo must not be called for United States coordinates")

    monkeypatch.setattr(weather, "_fetch_openmeteo", boom)
    prop = _create(iso)
    calls: list[str] = []
    prev = _use("arboretum", calls)
    try:
        with iso.db() as s:
            plan_mod.seasonal_plan(s, s.get(Property, prop["id"]), today=NOV_15)
            vitals_mod.vitals(s, s.get(User, iso.a["user_id"]), s.get(Property, prop["id"]),
                              today=NOV_15)
    finally:
        site_http.use_transport(prev)
    assert calls and all(c.startswith("https://api.weather.gov/") for c in calls)


# --- Home vitals -----------------------------------------------------------------------

def test_vitals_with_land(iso):  # noqa: F811
    prop = _create(iso, lot_contents=["trees_that_drop_leaves", "garden_beds", "potted_plants"])
    prev = _use("arboretum")
    try:
        with iso.db() as s:
            out = vitals_mod.vitals(s, s.get(User, iso.a["user_id"]), s.get(Property, prop["id"]),
                                    today=NOV_15)
    finally:
        site_http.use_transport(prev)
    keys = [c.key for c in out.cards]
    assert keys == ["weather_now", "frost", "rain", "heat", "sun", "soil", "drainage", "season"]
    cards = {c.key: c for c in out.cards}
    assert cards["frost"].tone == "act" and "tonight" in cards["frost"].value_text
    assert cards["sun"].value_text == "Not known yet"  # the site profile is still pending
    assert cards["season"].value_text == "Late fall 2026"
    assert out.headline.startswith("Frost possible tonight")
    assert out.forecast is not None
    assert any(i.event_key == "first_frost:2026:fall" for i in out.this_week)
    assert 0 < len(out.season_ahead) <= 5
    assert {s.kind for s in out.spaces} == {"zone", "space"}
    assert "—" not in out.headline
    assert_explained(out.model_dump(mode="json"))


def test_vitals_with_no_property_uses_the_first_space_with_coordinates(iso):  # noqa: F811
    with iso.db() as s:
        area = s.get(GrowingArea, iso.b["env_id"])
        area.lat, area.lng = ZILKER
        s.add(area)
        s.commit()
    prev = _use("zilker")
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
    assert out.property is None and out.forecast is not None
    assert {c.key for c in out.cards} == {"weather_now", "frost", "rain", "heat"}
    assert out.headline and "missing" not in out.headline.lower()
    assert out.notes and out.notes[0].startswith("If you look after a yard")
    assert_explained(out.model_dump(mode="json"))


def test_vitals_outside_the_united_states_uses_the_existing_service(iso, monkeypatch):  # noqa: F811
    seen = []

    def fake(lat, lng):
        seen.append((lat, lng))
        return {"current": {"temp_f": 50}, "attribution": {"text": "Weather data by Open-Meteo.com",
                                                          "url": "https://open-meteo.com/"},
                "daily": [{"date": "2026-11-15", "high_f": 55, "low_f": 33, "precip_chance_pct": 10,
                           "condition": "Clear"}]}

    monkeypatch.setattr(vitals_mod, "_existing_weather", fake)
    with iso.db() as s:
        area = s.get(GrowingArea, iso.b["env_id"])
        area.lat, area.lng = 51.5, -0.12  # London
        s.add(area)
        s.commit()
    try:
        with iso.db() as s:
            out = vitals_mod.vitals(s, s.get(User, iso.b["user_id"]), None, today=NOV_15)
    finally:
        with iso.db() as s:
            area = s.get(GrowingArea, iso.b["env_id"])
            area.lat = area.lng = None
            s.add(area)
            s.commit()
    assert seen == [(51.5, -0.12)]
    assert {c.key for c in out.cards} == {"weather_now", "frost"}
    assert_explained(out.model_dump(mode="json"))


def test_vitals_route_walks_clean(iso, monkeypatch):  # noqa: F811
    monkeypatch.setattr(plan_mod, "_clock", lambda prop, today: (datetime(2026, 11, 15, 14), NOV_15))
    _create(iso)
    prev = _use("arboretum")
    try:
        r = iso.client.get("/vitals", headers=iso.a["headers"])
    finally:
        site_http.use_transport(prev)
    assert r.status_code == 200
    body = r.json()
    assert body["property"]["city"] == "Washington"
    assert body["headline"]
    assert_explained(body)


def test_zilker_vitals_read_plainly(iso):  # noqa: F811
    prop = _create(iso, pin=ZILKER, lot_contents=["potted_plants", "lawn"])
    prev = _use("zilker")
    try:
        with iso.db() as s:
            out = vitals_mod.vitals(s, s.get(User, iso.a["user_id"]), s.get(Property, prop["id"]),
                                    today=NOV_15)
    finally:
        site_http.use_transport(prev)
    cards = {c.key: c for c in out.cards}
    assert cards["frost"].tone == "ok" and cards["rain"].value_text.startswith("Rain likely today")
    assert "hardening" not in out.headline  # no trees, shrubs or beds on this lot
    assert "Fall hardening" not in cards["season"].detail
    assert out.headline and "—" not in out.headline
    assert_explained(out.model_dump(mode="json"))


# --- writes made while answering a GET, under concurrent requests ---------------------

def test_two_requests_storing_the_same_forecast_cell_both_succeed(migrated_db_url):
    """Home asks for /vitals and the seasonal plan at once: on a cold cache
    both fetch the same cell and store it. The second store used to fail
    the unique index on (cell, provider) and answer 500."""
    from sqlalchemy import event
    from sqlmodel import Session, create_engine
    engine = create_engine(migrated_db_url)
    now = datetime(2026, 11, 16, 2, 24)
    with Session(engine) as a, Session(engine) as b:
        assert fcm._cache_get(b, "wx2_1_2", fcm.PROVIDER, now) is None
        stored_a = []

        def a_stores():
            fcm._cache_put(a, "wx2_1_2", fcm.PROVIDER, {"from": "a"}, now)
            a.commit()
            stored_a.append(True)

        @event.listens_for(b, "do_orm_execute")
        def a_stores_meanwhile(state):
            """A stores the cell between B's look for a row and B's write:
            after B's look when B looks first, else just before B writes."""
            if stored_a:
                return None
            if state.is_select:
                result = state.invoke_statement()
                a_stores()
                return result
            a_stores()
            return None

        fcm._cache_put(b, "wx2_1_2", fcm.PROVIDER, {"from": "b"}, now)
        b.commit()
        assert stored_a
    with Session(engine) as s:
        rows = s.exec(select(ForecastCache).where(ForecastCache.cell_key == "wx2_1_2")).all()
        assert [r.payload for r in rows] == [{"from": "b"}]
        assert rows[0].expires_at == now + fcm.CACHE_LIFE
    engine.dispose()


def test_a_busy_database_loses_the_forecast_cache_write_not_the_request(migrated_db_url):
    import sqlite3

    from sqlmodel import Session, create_engine
    engine = create_engine(migrated_db_url, connect_args={"timeout": 0.2})
    holder = sqlite3.connect(migrated_db_url.removeprefix("sqlite:///"), timeout=0)
    now = datetime(2026, 11, 16, 2, 24)
    try:
        holder.execute("BEGIN IMMEDIATE")
        with Session(engine) as s:
            fcm._cache_put(s, "wx2_1_3", fcm.PROVIDER, {"x": 1}, now)   # never raises
            assert fcm._cache_get(s, "wx2_1_3", fcm.PROVIDER, now) is None  # usable; not kept
    finally:
        holder.rollback()
        holder.close()
    with Session(engine) as s:   # the next request stores it
        fcm._cache_put(s, "wx2_1_3", fcm.PROVIDER, {"x": 1}, now)
        assert fcm._cache_get(s, "wx2_1_3", fcm.PROVIDER, now) == {"x": 1}
    engine.dispose()


def test_two_requests_counting_weatherkit_calls_lose_no_count(migrated_db_url):
    """The monthly quota counter: two first-of-the-month counts at once used
    to insert two rows (the second failing the unique index), and two later
    ones could both write calls + 1 over the same old value."""
    from sqlalchemy import event
    from sqlmodel import Session, create_engine
    engine = create_engine(migrated_db_url)
    now = datetime(2031, 1, 1, 0, 5)   # a month no other test counts in
    try:
        for _ in range(2):   # the first count of the month, then a later one
            with Session(engine) as a, Session(engine) as b:
                assert fcm._usage_ok(a, now) and fcm._usage_ok(b, now)
                counted_a = []

                def a_counts_meanwhile(state):
                    """A counts between B's read of the counter and B's write."""
                    if counted_a or state.session is not b:
                        return None
                    result = state.invoke_statement() if state.is_select else None
                    fcm._count_usage(a, now)
                    a.commit()
                    counted_a.append(True)
                    return result
                event.listen(b, "do_orm_execute", a_counts_meanwhile)
                fcm._count_usage(b, now)
                b.commit()
                assert counted_a
        with Session(engine) as s:
            rows = s.exec(select(ProviderUsage).where(ProviderUsage.month == "2031-01")).all()
            assert [(r.provider, r.calls) for r in rows] == [(fcm.WEATHERKIT, 4)]
    finally:
        with Session(engine) as s:
            for r in s.exec(select(ProviderUsage).where(ProviderUsage.month == "2031-01")).all():
                s.delete(r)
            s.commit()
        engine.dispose()


def test_home_still_answers_when_the_land_report_fails_with_a_failed_flush(iso, monkeypatch):  # noqa: F811
    """/vitals catches a failing land report and carries on, but the
    session was left needing a rollback, so the next read (its spaces) used
    to raise PendingRollbackError and the whole report answered 500."""
    from app.services.site import profile as profile_mod
    prop = _create(iso)

    def broken(session, prop):
        session.add(ProviderUsage(provider="broken", month=None))   # NOT NULL
        session.flush()
    monkeypatch.setattr(profile_mod, "site_profile", broken)
    monkeypatch.setattr(vitals_mod, "_existing_weather", lambda *a, **k: None)
    r = iso.client.get(f"/vitals?property_id={prop['id']}", headers=iso.a["headers"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert {c["value_text"] for c in body["cards"] if c["key"] in ("sun", "soil")} == {
        "Not known yet"}
    assert body["spaces"]
