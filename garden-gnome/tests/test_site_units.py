"""Lengths the owner reads are in feet, inches, miles or acres, never metric
("switch it to feet"). The app already speaks in degrees Fahrenheit and
inches; this keeps the land text in step.

Builds the full site profile, the map layers answer, the vitals answer and
the seasonal plan with the existing fixtures, walks every string in the JSON
and fails on any metric length: metre/meter, centimetre, kilometre, or a
number followed by m, cm or km. Thresholds and stored values stay metric;
only the words change.
"""
from __future__ import annotations

import re
from datetime import datetime

import pytest
from sqlmodel import Session, create_engine, select

from app.models.models import ForecastCache
from app.routers import properties
from app.services.season import forecast as fcm
from app.services.season import plan as plan_mod
from app.services.site import copy as words
from app.services.site import http as site_http
from app.services.site import layers
from app.services.site.copy import R
from tests.season_fixtures import nws_transport
from tests.test_property_routes import LAYER_PIN, layer_prop, layer_tiles  # noqa: F401
from tests.test_scoping import iso  # noqa: F401
from tests.test_site_profile import ARBORETUM, inline, sources  # noqa: F401

#: A metric length in owner-facing text. "thermometer" and "Parameter" are
#: not lengths, so the metre words must start a word.
METRIC = re.compile(
    r"(?<![a-z])(metre|meter)s?\b|centimet|kilomet|\b\d+(?:[.,]\d+)?\s?(?:m|cm|km)\b",
    re.I)


def metric_strings(value, path="$"):
    """Every string inside a JSON value that names a metric length."""
    found = []
    if isinstance(value, str):
        if METRIC.search(value):
            found.append(f"{path}: {value!r}")
    elif isinstance(value, dict):
        for k, v in value.items():
            found.extend(metric_strings(v, f"{path}.{k}"))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            found.extend(metric_strings(v, f"{path}[{i}]"))
    return found


def assert_no_metric(body):
    found = metric_strings(body)
    assert not found, "metric lengths the owner would read:\n  " + "\n  ".join(found)


def test_the_scan_catches_what_it_should():
    for bad in ("mapped at 1 metre detail", "about 2.5 kilometres across",
                "10 centimetres deep", "20 meters", "a 30 m cell", "3 cm down",
                "about 4 km away", "2m tall"):
        assert metric_strings(bad), bad
    for fine in ("not a thermometer in your yard", "Parameter-elevation Regressions",
                 "about 33 feet", "5 miles per hour", "at 2 pm", "item 3 of 5",
                 "4 inches deep"):
        assert not metric_strings(fine), fine


# --- the helper ---------------------------------------------------------------------

@pytest.mark.parametrize("metres, said", [
    (0.3, "about 1 foot"), (1, "about 3 feet"), (2, "about 7 feet"),
    (3, "about 10 feet"), (5, "about 16 feet"), (10, "about 30 feet"),
    (20, "about 70 feet"), (30, "about 100 feet"), (60, "about 200 feet"),
    (500, "about 1,600 feet"),
])
def test_feet_said_rounds_the_way_a_gardener_would(metres, said):
    assert words.feet_said(metres) == said


def test_squares_across_reads_as_a_phrase():
    assert words.squares_across(1) == "in squares about 3 feet across"
    assert words.squares_across(30) == "in squares about 100 feet across"


def test_survey_sentences_read_in_feet():
    r = R("slope", 6.0, "high", "3dep", detail={"resolution_m": 1.0, "year": 2014})
    t = words.slope(r, (), False)
    assert t.reason.startswith("From a laser ground survey flown in 2014, mapped in "
                               "squares about 3 feet across (United States")
    assert "Leaves out about 33 feet around your pin" in t.reason
    no_year = words.slope(R("slope", 6.0, "high", "3dep",
                            detail={"resolution_m": 10.0}), (), False)
    assert no_year.reason.startswith("From an elevation survey mapped in squares about "
                                     "30 feet across (United States")
    lc = words.land_cover(R("land_cover", "lawns", "high", "nlcd",
                            detail={"year": 2025}), {})
    assert lc.reason.startswith("From satellite land cover mapping in squares about "
                                "100 feet across, year 2025.")


@pytest.mark.parametrize("km, said", [
    (0.8, ", under a mile away"), (2.0, ", about 1 mile away"),
    (8.0, ", about 5 miles away"),
])
def test_station_distance_is_in_whole_miles(km, said):
    t = words.frost_dates({"last_spring_frost": "04-10",
                           "station": {"name": "Test", "distance_km": km}}, ())
    assert said in t.reason
    assert_no_metric(t.reason)


def test_layer_labels_and_notes_are_in_feet():
    assert layers.TREE_LABELS == ("6 to 16 feet tall", "16 to 33 feet tall",
                                  "33 to 66 feet tall", "66 feet or more")
    assert "Canopy under 6 feet (lawn and low shrubs) is not drawn." in layers.NOTES["trees"]
    assert_no_metric([layers.TREE_LABELS, layers.NOTES, layers.SUN_LABELS,
                      layers.WATER_LABELS, layers.NOT_READY_TEXT,
                      layers.READ_AGAIN_TEXT, layers.NO_GROUND_TEXT,
                      layers.COARSE_TEXT, layers.OUTSIDE_US_TEXT])
    assert_no_metric([list(v) for v in words.SOURCES.values()])


# --- every answer the app reads -----------------------------------------------------

@pytest.fixture()
def clean_forecasts(monkeypatch, migrated_db_url):
    fcm._second_opinion_memory.clear()
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


def test_profile_plan_and_vitals_have_no_metric_lengths(iso, sources, inline,  # noqa: F811
                                                        clean_forecasts, monkeypatch):
    monkeypatch.setattr(plan_mod, "_clock",
                        lambda prop, today: (datetime(2026, 11, 15, 14),
                                             datetime(2026, 11, 15).date()))
    h = iso.a["headers"]
    r = iso.client.post("/properties", headers=h, json={
        "pin_lat": ARBORETUM[0], "pin_lng": ARBORETUM[1], "pin_source": "owner_pin",
        "lot_contents": ["trees_that_drop_leaves", "lawn", "garden_beds"]})
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    prev = site_http.use_transport(lambda: nws_transport("arboretum"))
    try:
        profile = iso.client.get(f"/properties/{pid}/site-profile", headers=h)
        plan = iso.client.get(f"/properties/{pid}/seasonal-plan", headers=h)
        vitals = iso.client.get("/vitals", headers=h)
    finally:
        site_http.use_transport(prev)
    for resp in (profile, plan, vitals):
        assert resp.status_code == 200, resp.text
    body = profile.json()
    assert body["status"] == {"fast": "ready", "background": "ready"}
    # The sentences that used to carry metres are all there to be scanned.
    reasons = " ".join(v["reason"] for v in body["values"])
    assert "in squares about 3 feet across" in reasons
    assert plan.json()["events"] and vitals.json()["cards"]
    for answer in (body, plan.json(), vitals.json()):
        assert_no_metric(answer)


def test_map_layers_have_no_metric_lengths(iso, layer_tiles, layer_prop,  # noqa: F811
                                           monkeypatch):
    monkeypatch.setattr(properties, "queue_background", lambda background, pid: None)
    _, put = layer_tiles
    h = iso.a["headers"]
    before = iso.client.get(f"/properties/{layer_prop}/layers", headers=h)
    assert before.status_code == 200, before.text
    assert_no_metric(before.json())
    put()
    after = iso.client.get(f"/properties/{layer_prop}/layers", headers=h).json()
    assert all(l["status"] == "ready" for l in after["layers"]), after
    trees = next(l for l in after["layers"] if l["kind"] == "trees")
    assert [x["label"] for x in trees["legend"]] == list(layers.TREE_LABELS)
    assert_no_metric(after)
