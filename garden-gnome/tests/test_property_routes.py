"""Properties, zones and the other land stewardship routes (build spec
section 4), with the guardrails of section 2: user isolation on every new
route, 404 and zero outbound requests while a flag is off, zones that are
outdoor growing areas, and old clients that cannot tell anything changed.

Service bodies are other packages' work; these tests hold the routes to the
contract with whatever the services answer, stubs included.
"""
import httpx
import pytest
from sqlmodel import select

from app.config import get_settings
from app.models.models import (
    GeodataTile, GrowingArea, Plant, Property, SeasonEventState, Shelter,
    SiteOverride, SiteReading, SunExposure, TempExposure,
)
from app.models.schemas import SeasonEvent, SeasonalPlanOut
from app.routers import properties
from app.services.site import grid, tiles
from app.services.site import http as site_http
from tests.explained_walker import assert_explained, problems
from tests.test_scoping import iso  # noqa: F401  (fixture: two users, one area each)

ARBORETUM = (38.9123, -76.9681)
ZILKER = (30.2669, -97.7729)


@pytest.fixture(autouse=True)
def _background_inline(monkeypatch):
    """Record the background step instead of running it after the response."""
    queued: list[int] = []
    monkeypatch.setattr(properties, "queue_background",
                        lambda background, pid: queued.append(pid))
    return queued


def _create(iso, who="a", pin=ARBORETUM, **body):  # noqa: F811
    r = iso.client.post("/properties", headers=iso.__dict__[who]["headers"], json={
        "pin_lat": pin[0], "pin_lng": pin[1], "pin_source": "owner_pin", **body})
    assert r.status_code == 201, r.text
    return r.json()


# --- properties -------------------------------------------------------------------

def test_creating_a_property_makes_one_outdoor_whole_lot_zone(iso, _background_inline):  # noqa: F811
    calls = []
    from app.services.site import profile
    real = profile.build_fast
    try:
        profile.build_fast = lambda session, prop: calls.append(prop.id)
        body = _create(iso, name="  ", lot_contents=["lawn", "lawn", "shrubs"])
    finally:
        profile.build_fast = real

    assert body["name"] == "My land"
    assert body["lot_contents"] == ["lawn", "shrubs"]
    assert body["profile_status"] == {"fast": "pending", "background": "pending"}
    assert body["city"] is None and body["timezone"] is None
    assert calls == [body["id"]]                # the fast step ran inline
    assert _background_inline == [body["id"]]   # the background step was queued

    with iso.db() as s:
        zones = s.exec(select(GrowingArea)
                       .where(GrowingArea.property_id == body["id"])).all()
        assert len(zones) == 1
        z = zones[0]
        assert z.id == body["whole_lot_zone_id"] and z.is_whole_lot
        assert z.temp_exposure == TempExposure.outdoor
        assert z.shelter == Shelter.exposed
        assert z.type.value == "home" and z.surface is None
        assert z.sun_source is None
        assert (z.lat, z.lng) == ARBORETUM
        assert z.boundary_source.value == "default"
        assert abs(grid.box_area_sqft(grid.polygon_box(z.boundary_geojson)) - 8500) < 1


def test_no_address_or_place_is_accepted_from_the_client(iso):  # noqa: F811
    r = iso.client.post("/properties", headers=iso.a["headers"], json={
        "pin_lat": 38.9, "pin_lng": -76.9, "pin_source": "owner_pin",
        "city": "Washington", "postal_code": "20002"})
    assert r.status_code == 422


def test_property_get_list_and_patch(iso, _background_inline):  # noqa: F811
    prop = _create(iso)
    h = iso.a["headers"]
    assert [p["id"] for p in iso.client.get("/properties", headers=h).json()] == [prop["id"]]
    assert iso.client.get(f"/properties/{prop['id']}", headers=h).json() == prop

    r = iso.client.patch(f"/properties/{prop['id']}", headers=h,
                         json={"frost_bias": "earlier", "name": "Back forty"})
    assert r.json()["frost_bias"] == "earlier" and r.json()["name"] == "Back forty"
    assert _background_inline == [prop["id"]]  # nothing rebuilt for a rename
    r = iso.client.patch(f"/properties/{prop['id']}", headers=h, json={"frost_bias": None})
    assert r.json()["frost_bias"] is None

    r = iso.client.patch(f"/properties/{prop['id']}", headers=h,
                         json={"pin_lat": ZILKER[0], "pin_lng": ZILKER[1]})
    assert r.status_code == 200
    assert _background_inline == [prop["id"], prop["id"]]
    with iso.db() as s:
        z = s.get(GrowingArea, prop["whole_lot_zone_id"])
        assert (z.lat, z.lng) == ZILKER
        box = grid.polygon_box(z.boundary_geojson)
        assert box["south"] < ZILKER[0] < box["north"]
    assert iso.client.patch(f"/properties/{prop['id']}", headers=h,
                            json={"pin_lat": 1.0}).status_code == 422


def test_deleting_a_property_keeps_zones_with_plants_as_plain_areas(iso):  # noqa: F811
    prop = _create(iso)
    h = iso.a["headers"]
    pid = prop["id"]
    bed = iso.client.post(f"/properties/{pid}/zones", headers=h, json={
        "vegetation_type": "garden_bed", "box": _box_near(ARBORETUM)}).json()
    empty = iso.client.post(f"/properties/{pid}/zones", headers=h, json={
        "vegetation_type": "shrub", "box": _box_near(ARBORETUM)}).json()
    r = iso.client.post("/plants/", headers=h, json={
        "species_id": iso.species_id, "nickname": "Bed rose",
        "growing_area_id": bed["id"]})
    assert r.status_code == 201, r.text
    with iso.db() as s:
        s.add(SiteReading(property_id=pid, field="soil_ph", value=6.5, level="low",
                          provenance="public_map", source_key="ssurgo"))
        s.commit()

    assert iso.client.delete(f"/properties/{pid}", headers=h).status_code == 204
    with iso.db() as s:
        assert s.get(Property, pid) is None
        kept = s.get(GrowingArea, bed["id"])
        assert kept is not None and kept.property_id is None
        assert kept.temp_exposure == TempExposure.outdoor
        assert s.get(GrowingArea, empty["id"]) is None
        assert s.get(GrowingArea, prop["whole_lot_zone_id"]) is None
        assert s.exec(select(SiteReading).where(SiteReading.property_id == pid)).all() == []


# --- zones ------------------------------------------------------------------------

def _box_near(pin, d=0.0001):
    return {"west": pin[1] - d, "south": pin[0] - d,
            "east": pin[1] + d, "north": pin[0] + d}


def test_zone_create_patch_delete(iso):  # noqa: F811
    prop = _create(iso)
    h = iso.a["headers"]
    base = f"/properties/{prop['id']}/zones"
    zone = iso.client.post(base, headers=h, json={
        "vegetation_type": "tree", "leaf_habit": "drops_leaves",
        "box": _box_near(ARBORETUM)})
    assert zone.status_code == 201, zone.text
    z = zone.json()
    assert z["growing_area_id"] == z["id"] and z["name"] == "Trees"
    assert z["boundary_source"] == "owner" and not z["is_whole_lot"]
    assert z["box"] == pytest.approx(_box_near(ARBORETUM))

    listed = iso.client.get(base, headers=h).json()
    assert [x["id"] for x in listed] == [prop["whole_lot_zone_id"], z["id"]]
    assert listed[0]["is_whole_lot"] and listed[0]["vegetation_type"] is None

    r = iso.client.patch(f"{base}/{z['id']}", headers=h,
                         json={"name": "Oaks", "leaf_habit": "mixed"})
    assert r.json()["name"] == "Oaks" and r.json()["leaf_habit"] == "mixed"
    whole = iso.client.patch(f"{base}/{prop['whole_lot_zone_id']}", headers=h,
                             json={"box": _box_near(ARBORETUM, 0.0003)})
    assert whole.json()["boundary_source"] == "owner"

    too_big = iso.client.post(base, headers=h, json={
        "vegetation_type": "grass", "box": _box_near(ARBORETUM, 0.05)})
    assert too_big.status_code == 422
    backwards = iso.client.post(base, headers=h, json={
        "vegetation_type": "grass",
        "box": {"west": 1, "south": 1, "east": 0, "north": 2}})
    assert backwards.status_code == 422

    assert iso.client.delete(f"{base}/{prop['whole_lot_zone_id']}",
                             headers=h).status_code == 409
    iso.client.post("/plants/", headers=h, json={
        "species_id": iso.species_id, "growing_area_id": z["id"]})
    assert iso.client.delete(f"{base}/{z['id']}", headers=h).status_code == 409
    other = iso.client.post(base, headers=h, json={
        "vegetation_type": "bare_hardscape", "box": _box_near(ARBORETUM)}).json()
    assert iso.client.delete(f"{base}/{other['id']}", headers=h).status_code == 204


# --- corrections ------------------------------------------------------------------

def test_a_sun_correction_is_recorded_and_reaches_the_growing_area(iso):  # noqa: F811
    prop = _create(iso)
    h = iso.a["headers"]
    url = f"/properties/{prop['id']}/overrides"
    r = iso.client.put(url, headers=h, json={"field": "sun", "value": "shade",
                                             "method": "tap"})
    assert r.status_code == 200, r.text
    r = iso.client.put(url, headers=h, json={"field": "sun", "value": "full_sun",
                                             "method": "tap"})
    with iso.db() as s:
        rows = s.exec(select(SiteOverride)
                      .where(SiteOverride.property_id == prop["id"])
                      .order_by(SiteOverride.id)).all()
        assert [(o.value, o.retracted_at is None) for o in rows] == [
            ("shade", False), ("full_sun", True)]
        z = s.get(GrowingArea, prop["whole_lot_zone_id"])
        assert z.sun_source == "owner" and z.sun_exposure == SunExposure.full_sun

    assert iso.client.put(url, headers=h, json={
        "field": "sun", "value": "lots", "method": "tap"}).status_code == 422
    assert iso.client.put(url, headers=h, json={
        "field": "not_a_field", "value": 1, "method": "tap"}).status_code == 422

    r = iso.client.delete(f"{url}/sun", headers=h)
    assert r.status_code == 200
    with iso.db() as s:
        assert s.get(GrowingArea, prop["whole_lot_zone_id"]).sun_source is None
        assert all(o.retracted_at is not None for o in s.exec(
            select(SiteOverride).where(SiteOverride.property_id == prop["id"])).all())


# --- services through the routes ----------------------------------------------------

def test_service_answers_are_valid_without_the_network(iso):  # noqa: F811
    # The network is refused in tests, so soil fails and the fast step is partial;
    # the local hardiness grid still answers. The background step is queued, not run.
    prop = _create(iso)
    h = iso.a["headers"]
    pid = prop["id"]
    profile = iso.client.get(f"/properties/{pid}/site-profile", headers=h).json()
    assert profile["status"] == {"fast": "partial", "background": "pending"}
    assert profile["zones"][0]["is_whole_lot"]
    assert iso.client.post(f"/properties/{pid}/site-profile/refresh",
                           headers=h).status_code == 202
    plan = iso.client.get(f"/properties/{pid}/seasonal-plan", headers=h)
    assert plan.status_code == 200 and isinstance(plan.json()["events"], list)
    assert iso.client.put(f"/properties/{pid}/seasonal-plan/events/first_frost:2026",
                          headers=h, json={"state": "done"}).status_code == 404
    v = iso.client.get("/vitals", headers=h).json()
    assert v["property"]["id"] == pid
    assert {s["kind"] for s in v["spaces"]} == {"zone", "space"}
    for body in (profile, plan.json(), v):
        assert_explained(body)


def test_an_event_state_is_kept_and_cleared(iso, monkeypatch):  # noqa: F811
    from app.services.season import plan as plan_module

    explained = {"display": "Around 28 October", "confidence": "area_estimate",
                 "reason": "From 30 years of freeze records near you.",
                 "sources": [{"name": "National Centers for Environmental Information"}],
                 "provenance": "public_map"}

    def fake_plan(session, prop, *, today=None):
        state = session.exec(select(SeasonEventState)
                             .where(SeasonEventState.property_id == prop.id)).first()
        return SeasonalPlanOut(
            property_id=prop.id, generated_at="2026-11-15T00:00:00Z",
            season_label="Late fall",
            events=[SeasonEvent(
                event_key="first_frost:2026:fall", type="first_frost",
                title="First frost", status=state.status if state else "expected",
                window={"text": "Late October"}, explained=explained,
                owner_actions=["mark_happened"])])

    monkeypatch.setattr(plan_module, "seasonal_plan", fake_plan)
    prop = _create(iso)
    url = f"/properties/{prop['id']}/seasonal-plan/events/first_frost:2026:fall"
    r = iso.client.put(url, headers=iso.a["headers"],
                       json={"state": "done", "observed_on": "2026-10-30"})
    assert r.status_code == 200 and r.json()["status"] == "done"
    assert_explained(r.json())
    r = iso.client.put(url, headers=iso.a["headers"], json={"state": "clear"})
    assert r.json()["status"] == "expected"
    assert iso.client.put(url, headers=iso.b["headers"],
                          json={"state": "done"}).status_code == 404


def test_imagery_says_plainly_when_no_source_is_installed(iso, monkeypatch):  # noqa: F811
    monkeypatch.setattr(properties, "_imagery_module", lambda: None)
    h = iso.a["headers"]
    r = iso.client.get("/imagery/block", headers=h,
                       params={"lat": ARBORETUM[0], "lng": ARBORETUM[1]})
    assert r.status_code == 503 and "aerial image" in r.json()["detail"]
    assert iso.client.get("/imagery/tiles/blk1_1_2_naip.jpg",
                          headers=h).status_code == 404
    assert iso.client.get("/imagery/tiles/..%2Fetc.jpg", headers=h).status_code == 404


def test_the_walker_fails_on_an_empty_reason_or_source():
    good = {"display": "x", "reason": "Because.", "sources": [{"name": "Soil survey"}]}
    assert problems({"values": [good]}) == []
    assert problems({"values": [dict(good, reason=" ")]}) == ["$.values[0]: empty reason"]
    assert problems({"task": dict(good, sources=[])}) == ["$.task: no sources"]
    assert problems([dict(good, sources=[{"name": ""}])]) == [
        "$[0].sources[0]: a source with no name"]
    with pytest.raises(AssertionError):
        assert_explained({"explained": dict(good, reason="")})


# --- isolation --------------------------------------------------------------------

def _routes_for(pid: int, zid: int):
    return [
        ("get", f"/properties/{pid}", None),
        ("patch", f"/properties/{pid}", {"name": "Mine now"}),
        ("delete", f"/properties/{pid}", None),
        ("get", f"/properties/{pid}/site-profile", None),
        ("post", f"/properties/{pid}/site-profile/refresh", None),
        ("put", f"/properties/{pid}/overrides",
         {"field": "sun", "value": "shade", "method": "tap"}),
        ("delete", f"/properties/{pid}/overrides/sun", None),
        ("get", f"/properties/{pid}/zones", None),
        ("post", f"/properties/{pid}/zones",
         {"vegetation_type": "tree", "box": _box_near(ARBORETUM)}),
        ("patch", f"/properties/{pid}/zones/{zid}", {"name": "Mine"}),
        ("delete", f"/properties/{pid}/zones/{zid}", None),
        ("get", f"/properties/{pid}/imagery", None),
        ("get", f"/properties/{pid}/seasonal-plan", None),
        ("put", f"/properties/{pid}/seasonal-plan/events/first_frost:2026:fall",
         {"state": "done"}),
        ("get", f"/vitals?property_id={pid}", None),
    ]


def _call(client, method, url, body, headers=None):
    kwargs = {"headers": headers or {}}
    if body is not None:
        kwargs["json"] = body
    return getattr(client, method)(url, **kwargs) if method in ("get", "delete") \
        and body is None else client.request(method.upper(), url, **kwargs)


def test_every_new_route_is_scoped_to_its_owner(iso):  # noqa: F811
    theirs = _create(iso, who="b")
    pid, zid = theirs["id"], theirs["whole_lot_zone_id"]
    for method, url, body in _routes_for(pid, zid):
        r = _call(iso.client, method, url, body, iso.a["headers"])
        assert r.status_code == 404, f"{method} {url} answered {r.status_code}"
    # B's rows are untouched, and A's lists do not show them.
    assert iso.client.get("/properties", headers=iso.a["headers"]).json() == []
    with iso.db() as s:
        assert s.get(Property, pid).name == "My land"
        assert s.exec(select(SiteOverride)
                      .where(SiteOverride.property_id == pid)).all() == []
    # A's own zone cannot be addressed under B's property either.
    mine = _create(iso, who="a")
    r = iso.client.patch(f"/properties/{mine['id']}/zones/{zid}",
                         headers=iso.a["headers"], json={"name": "x"})
    assert r.status_code == 404


def test_every_new_route_needs_a_token(iso):  # noqa: F811
    for method, url, body in _routes_for(1, 1) + [
            ("get", "/properties", None), ("post", "/properties", {}),
            ("get", "/vitals", None), ("get", "/imagery/block?lat=1&lng=1", None),
            ("get", "/imagery/tiles/blk1_1_1.jpg", None)]:
        assert _call(iso.client, method, url, body).status_code == 401, url


# --- dark launch ------------------------------------------------------------------

def test_flags_off_means_404_everywhere_and_nothing_sent(iso, monkeypatch,  # noqa: F811
                                                         _background_inline):
    prop = _create(iso)
    queued_before = list(_background_inline)
    settings = get_settings()
    monkeypatch.setattr(settings, "site_profile_enabled", False)
    monkeypatch.setattr(settings, "season_plan_enabled", False)

    sent = []
    monkeypatch.setattr(site_http, "_transport_factory",
                        lambda: httpx.MockTransport(lambda r: sent.append(r)))
    before = site_http.requests_sent()

    h = iso.a["headers"]
    routes = _routes_for(prop["id"], prop["whole_lot_zone_id"]) + [
        ("get", "/properties", None),
        ("post", "/properties", {"pin_lat": 1, "pin_lng": 1, "pin_source": "owner_pin"}),
        ("get", "/vitals", None),
        ("get", f"/imagery/block?lat={ARBORETUM[0]}&lng={ARBORETUM[1]}", None),
        ("get", "/imagery/tiles/blk1_1_1.jpg", None),
    ]
    for method, url, body in routes:
        r = _call(iso.client, method, url, body, h)
        assert r.status_code == 404, f"{method} {url} answered {r.status_code}"
    assert sent == [] and site_http.requests_sent() == before
    assert _background_inline == queued_before
    properties._run_background(prop["id"])  # a queued step that wakes late
    assert site_http.requests_sent() == before
    with iso.db() as s:
        assert s.get(Property, prop["id"]).name == "My land"  # the PATCH never ran


def test_vitals_without_land_answers_with_the_season_flag_alone(iso, monkeypatch):  # noqa: F811
    _create(iso)
    monkeypatch.setattr(get_settings(), "site_profile_enabled", False)
    v = iso.client.get("/vitals", headers=iso.a["headers"])
    assert v.status_code == 200 and v.json()["property"] is None
    assert iso.client.get("/vitals?property_id=1",
                          headers=iso.a["headers"]).status_code == 404


# --- the shipped client -----------------------------------------------------------

def test_old_client_cannot_relocate_zone(iso):  # noqa: F811
    prop = _create(iso)
    zid = prop["whole_lot_zone_id"]
    r = iso.client.patch(f"/growing-areas/{zid}", headers=iso.a["headers"], json={
        "city": "Elsewhere", "region": "XX", "country": "US",
        "lat": 40.0, "lng": -100.0})
    assert r.status_code == 200
    assert (r.json()["lat"], r.json()["lng"]) == ARBORETUM
    assert r.json()["city"] == ""


def test_old_client_post_never_gets_property(iso):  # noqa: F811
    _create(iso)
    r = iso.client.post("/environments/", headers=iso.a["headers"], json={
        "name": "Porch", "property_id": 1, "is_whole_lot": True})
    assert r.status_code == 201
    with iso.db() as s:
        area = s.get(GrowingArea, r.json()["id"])
        assert area.property_id is None and not area.is_whole_lot


def test_zone_defaults_are_outdoor_exposed_through_the_old_routes(iso):  # noqa: F811
    prop = _create(iso)
    body = iso.client.get(f"/growing-areas/{prop['whole_lot_zone_id']}",
                          headers=iso.a["headers"]).json()
    assert body["temp_exposure"] == "outdoor" and body["shelter"] == "exposed"
    assert body["surface"] is None
    from tests.test_legacy_client_fields import OLD_AREA_KEYS
    assert OLD_AREA_KEYS <= set(body)


def test_old_route_sun_edit_is_override(iso):  # noqa: F811
    prop = _create(iso)
    zid = prop["whole_lot_zone_id"]
    r = iso.client.patch(f"/growing-areas/{zid}", headers=iso.a["headers"],
                         json={"sun_exposure": "shade"})
    assert r.status_code == 200 and r.json()["sun_exposure"] == "shade"
    with iso.db() as s:
        row = s.exec(select(SiteOverride)
                     .where(SiteOverride.property_id == prop["id"])).one()
        assert row.method.value == "old_client_edit" and row.value == "shade"
        assert s.get(GrowingArea, zid).sun_source == "owner"


def test_old_route_cannot_delete_whole_lot(iso):  # noqa: F811
    prop = _create(iso)
    r = iso.client.delete(f"/growing-areas/{prop['whole_lot_zone_id']}",
                          headers=iso.a["headers"])
    assert r.status_code == 409


def test_old_areas_still_list_unchanged(iso):  # noqa: F811
    before = iso.client.get("/growing-areas/", headers=iso.a["headers"]).json()
    prop = _create(iso)
    after = iso.client.get("/growing-areas/", headers=iso.a["headers"]).json()
    assert after[:len(before)] == before
    assert after[-1]["id"] == prop["whole_lot_zone_id"]
    assert set(after[-1]) == set(before[0])


# --- account deletion -------------------------------------------------------------

def test_account_deletion_removes_land_and_unshared_tiles(iso):  # noqa: F811
    # Pins no other test uses: the test database is shared, and a block
    # another test's property maps to is rightly kept.
    lonely, shared = (44.0123, -110.0456), (44.1234, -110.1567)
    mine = _create(iso, who="a", pin=lonely)
    _create(iso, who="a", pin=shared)
    _create(iso, who="b", pin=shared)
    shared_block = grid.snap_block(*shared).key
    with iso.db() as s:
        tiles.put(s, "3dep", "v1", grid.snap_block(*lonely).key + "_dem", b"a")
        tiles.put(s, "3dep", "v1", shared_block + "_dem", b"b")
        s.add(SiteOverride(property_id=mine["id"], field="sun", value="shade",
                           method="tap"))
        s.add(SeasonEventState(property_id=mine["id"], event_key="k", status="done"))
        s.commit()

    assert iso.client.delete("/me", headers=iso.a["headers"]).status_code == 204
    with iso.db() as s:
        assert s.exec(select(Property).where(Property.user_id == iso.a["user_id"])).all() == []
        for model in (SiteOverride, SeasonEventState, SiteReading):
            assert s.exec(select(model).where(model.property_id == mine["id"])).all() == []
        keys = {t.tile_key for t in s.exec(select(GeodataTile)).all()}
        assert shared_block + "_dem" in keys
        assert grid.snap_block(*lonely).key + "_dem" not in keys
        assert s.exec(select(GrowingArea)
                      .where(GrowingArea.user_id == iso.a["user_id"])).all() == []
        assert s.exec(select(Plant).where(Plant.user_id == iso.a["user_id"])).all() == []
