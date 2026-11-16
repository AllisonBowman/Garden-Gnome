"""The site profile (build spec sections 3 to 5): the fast and background
steps with fake sources behind the read(block, pin, footprint, *, client)
signature, append-only readings, statuses and retries, per-zone values,
owner corrections, and the reason-and-source walker on every answer.

No test here touches the network: the fakes never send, and conftest makes
every OutboundClient refuse."""
from datetime import datetime, timedelta

import pytest
from sqlmodel import select

from app.models.models import GrowingArea, Property, SiteOverride, SiteReading, SunExposure
from app.routers import properties
from app.services.site import grid, profile
from app.services.site.types import Reading, SourceUnavailable
from tests.explained_walker import assert_explained
from tests.test_scoping import iso  # noqa: F401

ARBORETUM = (38.9123, -76.9681)
PARIS = (48.8566, 2.3522)


def rd(field, value, level="medium", source="ssurgo", **detail):
    return Reading(field=field, value=value, level=level, provenance="public_map",
                   source_key=source, source_version="2026-09-11", method="test",
                   detail=detail or None)


class Fake:
    """A source: returns fixed readings, or raises, and counts its calls."""

    def __init__(self, readings=(), fail=False):
        self.readings = list(readings)
        self.fail = fail
        self.calls = []

    def read(self, block, pin, footprint, *, client):
        self.calls.append((block.key, pin, footprint))
        if self.fail:
            raise SourceUnavailable("fake", "down")
        return list(self.readings)


class ZoneAware(Fake):
    """A derived source that answers per footprint and sees earlier readings."""

    def read(self, block, pin, footprint, *, client, readings=()):
        self.calls.append((block.key, pin, footprint, [r.field for r in readings]))
        if self.fail:
            raise SourceUnavailable("fake", "down")
        box = grid.polygon_box(footprint)
        small = box and (box["east"] - box["west"]) < 0.00025
        return [r if not small else Reading(
            field=r.field, value=self._zone_value(r), level=r.level,
            provenance="modelled", source_key=r.source_key,
            source_version=r.source_version, method=r.method, detail=r.detail)
            for r in self.readings]

    @staticmethod
    def _zone_value(r):
        return {"sun_estimate": {"category": "shade", "hours": 2.2},
                "water_collects": "gathers_after_rain",
                "slope": 12.0, "facing": "south"}.get(r.field, r.value)


def fast_sources():
    return {
        "hardiness": Fake([rd("hardiness_zone", "7b", "high", "phzm2023")]),
        "soil": Fake([
            rd("soil_mapunit", {"name": "Sassafras fine sandy loam"},
               dominant_share=0.85, near_line_m=16.6, neighbour_differs=True),
            rd("soil_drainage_class", "Well drained"),
            rd("soil_slowest_layer", "moderately slow"),
            rd("soil_texture", "fine sandy loam", **{"class": "loamy"}),
            rd("soil_water_holding", 1.6),
            rd("soil_ph", 5.1),
            rd("soil_disturbed_share", 0.05),
            rd("soil_flooding", "None", worst="occasionally", worst_share=0.02,
               months=[3, 4, 10]),
            rd("soil_ponding", "None"),
        ]),
    }


def background_sources():
    return {
        "elevation": Fake([rd("elevation_window", {"tile_key": "x"}, "high", "3dep",
                              resolution_m=1.0, year=2014)]),
        "canopy": Fake([rd("canopy_shade", 0.4, "medium", "canopy")]),
        "landcover": Fake([rd("land_cover", "lightly built-up land with lawns and trees",
                              "high", "nlcd", paved_share=0.45, year=2025),
                           rd("tree_cover", 0.3, "medium", "nlcd")]),
        "terrain": ZoneAware([rd("slope", 6.0, "high", "3dep", resolution_m=1.0, year=2014),
                              rd("facing", "north-east", "high", "3dep", resolution_m=1.0),
                              rd("open_sky_sun", {"hours": 12.1}, "high", "sunpos")]),
        "sun": ZoneAware([rd("sun_estimate", {"category": "part_shade", "hours": 4.6},
                             "medium", "sunpos",
                             counted=["terrain", "canopy_height"],
                             canopy_resolution_m=1)]),
        "drainage": ZoneAware([rd("water_collects", "drains_freely", "medium", "drainage",
                                  signals=["drainage_class", "slowest_layer"],
                                  soil_agree_share=0.85)]),
    }


@pytest.fixture()
def sources():
    s = {**fast_sources(), **background_sources()}
    with profile.use_sources(s):
        yield s


@pytest.fixture()
def inline(iso, monkeypatch):  # noqa: F811
    monkeypatch.setattr(profile, "SESSION_FACTORY", iso.db)
    monkeypatch.setattr(properties, "queue_background",
                        lambda background, pid: profile.build_background(pid))


def _create(iso, pin=ARBORETUM):  # noqa: F811
    r = iso.client.post("/properties", headers=iso.a["headers"], json={
        "pin_lat": pin[0], "pin_lng": pin[1], "pin_source": "owner_pin"})
    assert r.status_code == 201, r.text
    return r.json()


def _profile(iso, pid):  # noqa: F811
    r = iso.client.get(f"/properties/{pid}/site-profile", headers=iso.a["headers"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert_explained(body)
    return body


def _value(values, field):
    return next(v for v in values if v["field"] == field)


# --- the fast and background steps ---------------------------------------------------

def test_fast_step_alone_gives_hardiness_and_soil_and_waits_for_the_rest(iso, monkeypatch):  # noqa: F811
    monkeypatch.setattr(properties, "queue_background", lambda background, pid: None)
    with profile.use_sources(fast_sources()):
        prop = _create(iso)
        body = _profile(iso, prop["id"])
    assert body["status"] == {"fast": "ready", "background": "pending"}
    hz = _value(body["values"], "hardiness_zone")
    assert hz["display"].startswith("Hardiness zone 7b: the average coldest night")
    assert "5 to 10 degrees Fahrenheit" in hz["display"]
    assert hz["confidence_label"] == "Good estimate" and not hz["can_override"]
    drainage = _value(body["values"], "soil_drainage")
    assert drainage["confidence_label"] == "Rough estimate"  # 16.6 m from a differing line
    assert "close to the edge" in drainage["reason"]
    assert _value(body["values"], "soil_ph")["confidence_label"] == "Rough estimate"
    for field in ("sun", "slope", "facing", "water_collects", "land_cover"):
        v = _value(body["values"], field)
        assert v["confidence"] == "not_known_yet" and "still being worked out" in v["display"]
    assert any("still being worked out" in n for n in body["notes"])


def test_full_profile_with_every_source(iso, sources, inline):  # noqa: F811
    prop = _create(iso)
    body = _profile(iso, prop["id"])
    assert body["status"] == {"fast": "ready", "background": "ready"}
    values = {v["field"]: v for v in body["values"]}
    assert set(values) == {"sun", "water_collects", "soil_drainage", "soil_texture",
                           "soil_ph", "disturbed_soil", "flooding", "slope", "facing",
                           "hardiness_zone", "frost_dates", "land_cover"}
    sun = values["sun"]
    assert sun["value"] == "part_shade"
    assert "about 4.5 hours" in sun["display"]
    # The hours ride alongside the category word, additively.
    assert sun["facts"] == {"hours": 4.6}
    assert all(v["facts"] is None for f, v in values.items() if f != "sun")
    assert ("Counts the slope of the ground and tree canopy mapped in squares "
            "about 3 feet across. Buildings are not counted.") in sun["reason"]
    assert sun["confidence_label"] == "Rough estimate"  # default footprint, no buildings
    assert sun["override_kind"] == "choice"
    assert [c["value"] for c in sun["override_choices"]] == ["full_sun", "part_shade", "shade"]
    lc = values["land_cover"]
    assert lc["confidence_label"] == "Neighbourhood context" and not lc["can_override"]
    assert "about 45% paved or roofed" in lc["display"]
    slope = values["slope"]
    assert slope["confidence_label"] == "Area estimate"  # default footprint cap
    assert "approximate yard" in slope["reason"]
    assert values["water_collects"]["confidence_label"] == "Rough estimate"
    assert "not a flood insurance determination" in values["flooding"]["reason"]
    frost = values["frost_dates"]  # real NOAA normals near the pin
    assert frost["confidence"] in ("area_estimate", "rough_estimate")
    assert frost["reason"] and frost["sources"] and not frost["can_override"]
    whole = body["zones"][0]
    assert whole["is_whole_lot"] and [v["field"] for v in whole["values"]] == list(
        profile.ZONE_FIELDS)
    assert all(v["zone_id"] == whole["zone_id"] for v in whole["values"])


def test_background_is_safe_to_run_twice(iso, sources, inline):  # noqa: F811
    prop = _create(iso)
    with iso.db() as s:
        n = len(s.exec(select(SiteReading)
                       .where(SiteReading.property_id == prop["id"])).all())
    profile.build_background(prop["id"])
    with iso.db() as s:
        rows = s.exec(select(SiteReading)
                      .where(SiteReading.property_id == prop["id"])).all()
        assert len(rows) == n
        assert all(r.superseded_at is None for r in rows)


def test_a_new_reading_supersedes_the_old_one(iso, sources, inline):  # noqa: F811
    prop = _create(iso)
    sources["hardiness"].readings = [rd("hardiness_zone", "8a", "high", "phzm2023")]
    r = iso.client.post(f"/properties/{prop['id']}/site-profile/refresh",
                        headers=iso.a["headers"])
    assert r.status_code == 202
    with iso.db() as s:
        rows = s.exec(select(SiteReading).where(SiteReading.field == "hardiness_zone")
                      .where(SiteReading.property_id == prop["id"])
                      .order_by(SiteReading.id)).all()
        assert [(x.value, x.superseded_at is None) for x in rows] == [
            ("7b", False), ("8a", True)]
    assert _value(_profile(iso, prop["id"])["values"],
                  "hardiness_zone")["display"].startswith("Hardiness zone 8a")


def test_a_failing_source_degrades_only_its_rows_and_is_retried(iso, sources, inline):  # noqa: F811
    sources["elevation"].fail = True
    sources["terrain"].fail = True
    prop = _create(iso)
    body = _profile(iso, prop["id"])
    assert body["status"]["background"] == "partial"
    slope = _value(body["values"], "slope")
    assert slope["confidence"] == "not_known_yet" and "did not answer" in slope["reason"]
    assert _value(body["values"], "land_cover")["confidence"] == "neighbourhood_context"
    with iso.db() as s:
        st = s.get(Property, prop["id"]).profile_status
    assert st["sources"]["elevation"] == "failed" and st["attempts"] == 1
    due_at = datetime.fromisoformat(st["next_retry_at"])

    with iso.db() as s:
        assert prop["id"] not in profile.due_for_retry(s, now=due_at - timedelta(seconds=1))
        assert prop["id"] in profile.due_for_retry(s, now=due_at)
    sources["elevation"].fail = False
    sources["terrain"].fail = False
    assert prop["id"] in profile.run_due_retries(now=due_at)
    with iso.db() as s:
        st = s.get(Property, prop["id"]).profile_status
    assert st["background"] == "ready" and "next_retry_at" not in st


def test_retries_stop_after_a_day(iso, sources, inline):  # noqa: F811
    sources["landcover"].fail = True
    prop = _create(iso)
    with iso.db() as s:
        p = s.get(Property, prop["id"])
        st = dict(p.profile_status)
        st["first_attempt_at"] = (datetime.utcnow() - timedelta(hours=23, minutes=59)).isoformat()
        p.profile_status = st
        s.add(p)
        s.commit()
    profile.build_background(prop["id"])
    with iso.db() as s:
        assert "next_retry_at" not in s.get(Property, prop["id"]).profile_status


def test_a_missing_module_is_not_known_yet(iso, inline):  # noqa: F811
    with profile.use_sources({**fast_sources(), "elevation": None, "canopy": None,
                              "landcover": None, "terrain": None, "sun": None,
                              "drainage": None}):
        prop = _create(iso)
        body = _profile(iso, prop["id"])
    assert body["status"] == {"fast": "ready", "background": "failed"}
    assert _value(body["values"], "sun")["confidence"] == "not_known_yet"


def test_a_step_left_building_by_a_stopped_process_is_taken_over(iso, sources, inline):  # noqa: F811
    prop = _create(iso)
    with iso.db() as s:
        p = s.get(Property, prop["id"])
        p.profile_status = {**p.profile_status, "background": "building",
                            "started_at": datetime.utcnow().isoformat()}
        s.add(p)
        s.commit()
    calls = len(sources["elevation"].calls)
    profile.build_background(prop["id"])   # a run in progress: left alone
    assert len(sources["elevation"].calls) == calls
    with iso.db() as s:
        later = datetime.utcnow() + profile.STALE_AFTER
        assert prop["id"] in profile.due_for_retry(s, now=later)
        p = s.get(Property, prop["id"])
        p.profile_status = {**p.profile_status,
                            "started_at": (datetime.utcnow() - profile.STALE_AFTER).isoformat()}
        s.add(p)
        s.commit()
    profile.build_background(prop["id"])
    assert len(sources["elevation"].calls) == calls + 1
    with iso.db() as s:
        assert s.get(Property, prop["id"]).profile_status["background"] == "ready"


def test_background_does_nothing_while_the_flag_is_off(iso, sources, inline, monkeypatch):  # noqa: F811
    prop = _create(iso)
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), "site_profile_enabled", False)
    calls = len(sources["elevation"].calls)
    profile.build_background(prop["id"])
    assert len(sources["elevation"].calls) == calls


def test_outside_the_united_states(iso, sources, inline):  # noqa: F811
    prop = _create(iso, pin=PARIS)
    body = _profile(iso, prop["id"])
    assert sources["soil"].calls == [] and sources["elevation"].calls == []
    assert body["status"] == {"fast": "ready", "background": "ready"}
    assert any("outside the United States" in n for n in body["notes"])
    sun = _value(body["values"], "sun")
    assert "United States only" in sun["reason"] and sun["can_override"]


def test_sources_get_the_block_and_only_derived_ones_see_readings(iso, sources, inline):  # noqa: F811
    _create(iso)
    block = grid.snap_block(*ARBORETUM)
    key, pin, footprint = sources["soil"].calls[0]
    assert key == block.key and pin == ARBORETUM
    assert grid.polygon_box(footprint) is not None
    seen = sources["drainage"].calls[0][3]
    assert "soil_drainage_class" in seen and "elevation_window" in seen


# --- zones -------------------------------------------------------------------------

def _zone_box(dlat=0.0001):
    lat, lng = ARBORETUM
    return {"west": lng - dlat, "south": lat - dlat, "east": lng + dlat, "north": lat + dlat}


def test_zone_values_are_worked_out_over_the_box(iso, sources, inline):  # noqa: F811
    prop = _create(iso)
    h = iso.a["headers"]
    z = iso.client.post(f"/properties/{prop['id']}/zones", headers=h, json={
        "vegetation_type": "garden_bed", "box": _zone_box(), "leaf_habit": "drops_leaves"})
    assert z.status_code == 201, z.text
    zone = z.json()
    # Computed on request from the cached background data, before any rerun.
    zv = {v["field"]: v for v in zone["values"]}
    assert set(zv) == set(profile.ZONE_FIELDS)
    assert zv["sun"]["value"] == "shade" and zv["sun"]["zone_id"] == zone["id"]
    assert "leaves are out" in zv["sun"]["reason"]
    assert "approximate yard" not in zv["sun"]["reason"]
    assert zv["water_collects"]["display"].startswith("Where water collects: water gathers")
    assert_explained(zone)

    # The next background run stores them for the zone.
    profile.build_background(prop["id"])
    with iso.db() as s:
        rows = s.exec(select(SiteReading).where(SiteReading.zone_id == zone["id"])
                      .where(SiteReading.superseded_at == None)).all()  # noqa: E711
        assert {r.field for r in rows} >= {"slope", "facing", "sun_estimate", "water_collects"}
    body = _profile(iso, prop["id"])
    zvals = {v["field"]: v for v in body["zones"][1]["values"]}
    assert zvals["slope"]["value"] == 12.0
    # 1 metre survey over an owner-drawn zone of about 500 square metres
    assert zvals["slope"]["confidence_label"] == "Good estimate"


def test_a_zone_without_cached_terrain_waits(iso, monkeypatch):  # noqa: F811
    monkeypatch.setattr(properties, "queue_background", lambda background, pid: None)
    with profile.use_sources(fast_sources()):
        prop = _create(iso)
        z = iso.client.post(f"/properties/{prop['id']}/zones", headers=iso.a["headers"],
                            json={"vegetation_type": "grass", "box": _zone_box()}).json()
    for v in z["values"]:
        assert v["confidence"] == "not_known_yet"
    assert_explained(z)


# --- corrections ---------------------------------------------------------------------

def test_owner_sun_correction_wins_and_the_estimate_stays_visible(iso, sources, inline):  # noqa: F811
    prop = _create(iso)
    h = iso.a["headers"]
    r = iso.client.put(f"/properties/{prop['id']}/overrides", headers=h,
                       json={"field": "sun", "value": "full_sun", "method": "tap"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert_explained(body)
    sun = _value(body["values"], "sun")
    assert sun["confidence_label"] == "You told us" and sun["provenance"] == "owner"
    assert sun["value"] == "full_sun" and sun["display"].startswith("Sun: full sun")
    # An owner's answer has no hours.
    assert sun["facts"] is None
    assert sun["public"]["confidence_label"] == "Rough estimate"
    assert "part shade" in sun["public"]["display"]
    assert sun["sources"][0]["name"] == "Your correction"
    whole_sun = _value(body["zones"][0]["values"], "sun")
    assert whole_sun["confidence_label"] == "You told us"
    with iso.db() as s:
        z = s.get(GrowingArea, prop["whole_lot_zone_id"])
        assert z.sun_source == "owner" and z.sun_exposure == SunExposure.full_sun

    # A refresh never touches it.
    iso.client.post(f"/properties/{prop['id']}/site-profile/refresh", headers=h)
    assert _value(_profile(iso, prop["id"])["values"], "sun")["value"] == "full_sun"

    back = iso.client.delete(f"/properties/{prop['id']}/overrides/sun", headers=h).json()
    sun = _value(back["values"], "sun")
    assert sun["value"] == "part_shade" and sun["public"] is None
    assert sun["facts"] == {"hours": 4.6}


def test_soil_acidity_measured_and_choices_refused(iso, sources, inline):  # noqa: F811
    prop = _create(iso)
    url = f"/properties/{prop['id']}/overrides"
    h = iso.a["headers"]
    r = iso.client.put(url, headers=h, json={"field": "soil_ph", "value": 6.4,
                                             "method": "measured"})
    ph = _value(r.json()["values"], "soil_ph")
    assert ph["confidence_label"] == "You measured" and "6.4" in ph["display"]
    for bad in ({"field": "soil_ph", "value": 14, "method": "measured"},
                {"field": "soil_texture", "value": "gravel", "method": "tap"},
                {"field": "land_cover", "value": "forest", "method": "tap"},
                {"field": "hardiness_zone", "value": "8a", "method": "tap"},
                {"field": "water_collects", "value": "maybe", "method": "tap"}):
        assert iso.client.put(url, headers=h, json=bad).status_code == 422, bad


def test_a_zone_correction_applies_to_that_zone_only(iso, sources, inline):  # noqa: F811
    prop = _create(iso)
    h = iso.a["headers"]
    zone = iso.client.post(f"/properties/{prop['id']}/zones", headers=h, json={
        "vegetation_type": "garden_bed", "box": _zone_box()}).json()
    r = iso.client.put(f"/properties/{prop['id']}/overrides", headers=h, json={
        "zone_id": zone["id"], "field": "water_collects", "value": "stays_dry",
        "method": "tap"})
    body = r.json()
    assert_explained(body)
    zv = _value(next(z for z in body["zones"] if z["zone_id"] == zone["id"])["values"],
                "water_collects")
    assert zv["display"] == "Where water collects: this stays dry. You told us."
    assert zv["public"]["display"].startswith("Where water collects: water gathers")
    assert _value(body["values"], "water_collects")["confidence"] != "you_told_us"
    r = iso.client.put(f"/properties/{prop['id']}/overrides", headers=h, json={
        "zone_id": zone["id"], "field": "soil_texture", "value": "clayey", "method": "tap"})
    zvals = next(z for z in r.json()["zones"] if z["zone_id"] == zone["id"])["values"]
    assert _value(zvals, "soil_texture")["display"].startswith("Topsoil: clayey")
    with iso.db() as s:
        assert len(s.exec(select(SiteOverride)
                          .where(SiteOverride.property_id == prop["id"])).all()) == 2


def test_frost_dates_row_comes_from_the_normals(iso, sources, inline, monkeypatch):  # noqa: F811
    from app.services.season import normals
    monkeypatch.setattr(normals, "frost_normals", lambda lat, lng: {
        "last_spring_frost": {"p10": "03-25", "p50": "04-10", "p90": "04-28"},
        "first_fall_frost": {"p50": "10-28"},
        "station": {"name": "National Arboretum", "distance_km": 0.8},
        "stations_differ_days": 10, "level": "high"})
    prop = _create(iso)
    frost = _value(_profile(iso, prop["id"])["values"], "frost_dates")
    assert frost["display"] == ("Typical last spring frost around 10 April and typical "
                                "first fall frost around 28 October.")
    assert frost["confidence_label"] == "Area estimate"  # stations differ by over a week
    assert "National Arboretum station" in frost["reason"] and not frost["can_override"]


def test_the_real_hardiness_source_through_the_profile(iso, monkeypatch):  # noqa: F811
    """B2a's hardiness module reads a file on our server, so it can run here;
    the Arboretum sits close to a half-zone line."""
    pytest.importorskip("app.services.site.sources.hardiness")
    monkeypatch.setattr(properties, "queue_background", lambda background, pid: None)
    with profile.use_sources({"soil": fast_sources()["soil"]}):
        prop = _create(iso)
        hz = _value(_profile(iso, prop["id"])["values"], "hardiness_zone")
    assert hz["display"].startswith("Hardiness zone 8a:")
    assert hz["confidence_label"] == "Area estimate"
    assert "either could apply" in hz["reason"]


def test_sun_facts_carry_the_hours_and_nothing_else():
    from app.services.site.copy import R
    r = lambda v: R(field="sun_estimate", value=v, level="low", source_key="sunpos")  # noqa: E731
    assert profile._facts_of("sun", r({"category": "full_sun", "hours": 7})) == {"hours": 7.0}
    assert profile._facts_of("sun", r({"category": "full_sun", "hours": 6.96})) == {"hours": 7.0}
    assert profile._facts_of("sun", r({"category": "full_sun"})) is None
    assert profile._facts_of("sun", r({"category": "full_sun", "hours": True})) is None
    assert profile._facts_of("sun", r("full_sun")) is None
    assert profile._facts_of("sun", None) is None
    assert profile._facts_of("slope", r({"hours": 3})) is None
