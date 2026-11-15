"""B2b: where water collects (build spec section 5). Soil readings are
passed in (this module never calls the soil source); terrain comes from
synthetic windows. Nothing here reaches the network.
"""
import math

import numpy as np
import pytest

from app.services.site import drainage, grid, terrain, tiles
from app.services.site import http as site_http
from app.services.site.sources import elevation
from app.services.site.types import Reading
from tests.test_site_terrain import _fresh_caches  # noqa: F401 -- autouse
from tests.test_site_terrain import cache_window
from tests.test_site_terrain import ARBORETUM, owner_box, window_from


def soil(**values):
    """Soil readings in the shapes the soil source writes."""
    field = {"drainage": "soil_drainage_class", "slowest": "soil_slowest_layer",
             "runoff": "soil_runoff_group", "ponding": "soil_ponding",
             "flooding": "soil_flooding", "table": "soil_water_table",
             "disturbed": "soil_disturbed_share"}
    out = []
    share = values.pop("share", 1.0)
    for k, v in values.items():
        detail = {"dominant_share": share} if k == "drainage" else None
        out.append(Reading(field=field[k], value=v, level="medium", provenance="public_map",
                           source_key="ssurgo", source_version="2026-09-11", method="sda",
                           detail=detail))
    return out


WELL = dict(drainage={"class": "Well drained"}, slowest={"um_per_s": 9.0}, runoff="B",
            ponding={"frequency": "None"}, flooding={"frequency": "None"},
            table={"depth_cm": None})
FLAT = lambda: window_from(lambda e, n: 0.002 * e + 20)             # nearly flat, sheds east
BOWL = lambda: window_from(lambda e, n: 20 + np.where(
    np.hypot(e - 12, n) < 6, -0.4 * (6 - np.hypot(e - 12, n)) / 6, 0.0))
BOX = owner_box(ARBORETUM)


def run(readings, win, box=BOX, default=False):
    s = terrain.summarise(win, box, ARBORETUM) if win is not None else None
    return drainage.combine(drainage.signals_from_soil(readings), s,
                            resolution_m=win.resolution_m if win is not None else None,
                            is_default=default)


def test_well_drained_soil_on_open_ground_drains_freely_and_can_be_a_good_estimate():
    r = run(soil(**WELL), FLAT())
    assert r.value == {"class": "drains_freely"}
    assert r.level == "high"
    assert r.detail["soil_agree"] is True and r.detail["resolution_m"] == 1.0
    assert {"drainage_class", "slowest_layer", "runoff_group", "water_table"} <= \
        set(r.detail["signals"])
    assert "pin_radius_left_out" in r.reason_codes


def test_a_low_spot_makes_water_gather_even_on_well_drained_soil():
    r = run(soil(**WELL), BOWL())
    assert r.value == {"class": "gathers_after_rain"}
    assert r.detail["signals"][0] == "low_spot"
    assert r.detail["soil_agree"] is False      # the soil says it drains: not "Good"
    assert r.level == "medium"


def test_poorly_drained_soil_with_a_shallow_water_table_is_often_wet():
    r = run(soil(drainage="Poorly drained", table={"depth_cm": 15}, runoff="C/D",
                 ponding={"frequency": "Occasional"}), FLAT())
    assert r.value == {"class": "often_wet"}
    assert set(r.detail["signals"]) == {"drainage_class", "water_table", "runoff_group", "ponding"}
    assert r.level == "high"


def test_slow_soil_is_slow_to_drain():
    r = run(soil(drainage={"class": "Moderately well drained"}, slowest={"class": "Moderately low"},
                 runoff="D"), FLAT())
    assert r.value == {"class": "slow_to_drain"}
    assert set(r.detail["signals"]) == {"drainage_class", "slowest_layer", "runoff_group"}


def test_the_default_footprint_and_disturbed_soil_are_rough():
    assert run(soil(**WELL), FLAT(), box=grid.default_footprint_box(*ARBORETUM),
               default=True).level == "low"
    r = run(soil(**WELL, disturbed={"share": 0.3}), FLAT())
    assert r.level == "low" and "disturbed_soil" in r.reason_codes


def test_soil_alone_is_an_area_estimate_only_when_the_mapped_area_agrees():
    assert run(soil(**WELL), None).level == "medium"
    mixed = run(soil(**{**WELL, "share": 0.6}), None)
    assert mixed.level == "low" and mixed.value == {"class": "drains_freely"}


def test_elevation_coarser_than_three_metres_is_not_used_for_water():
    win = BOWL()
    coarse = elevation.ElevationWindow(block=win.block, z=win.z, valid=win.valid,
                                       resolution_m=10.0)
    r = run(soil(**WELL), coarse)
    assert r.value == {"class": "drains_freely"}       # the bowl is not counted
    assert "low_spot" not in r.detail["signals"]
    assert "elevation_too_coarse_for_water" in r.reason_codes


def test_nothing_known_is_unknown():
    r = run([], None)
    assert r.level == "unknown" and r.value is None


@pytest.mark.parametrize("text,signal", [
    ("Excessively drained", "free"), ("Somewhat excessively drained", "free"),
    ("Well drained", "free"), ("Moderately well drained", "slow"),
    ("Somewhat poorly drained", "slow"), ("Poorly drained", "wet"),
    ("Very poorly drained", "wet"), ("", None)])
def test_drainage_classes(text, signal):
    assert drainage.drainage_class_signal(text) == signal


def test_value_shapes_are_read_tolerantly():
    assert drainage.slowest_layer_signal(0.4) == "slow"
    assert drainage.slowest_layer_signal({"ksat_um_s": 14}) == "free"
    assert drainage.runoff_group_signal({"group": "A"}) == "free"
    assert drainage.ponding_signal("Rare") is None
    assert drainage.flooding_signal({"class": "Frequent"}) == "wet"
    assert drainage.water_table_signal({"depth_cm": 70}) == "slow"
    assert drainage.water_table_signal({"class": "None within 200 cm"}) == "free"


def test_read_combines_passed_in_soil_with_the_cached_window(session):
    block = grid.snap_block(*ARBORETUM)
    win = BOWL()
    cache_window(session, block, win, year=2014)
    before = site_http.requests_sent()
    with site_http.OutboundClient() as c:   # refuses everything
        [r] = drainage.read(block, ARBORETUM, BOX, client=c, session=session,
                            readings=soil(**WELL))
    assert site_http.requests_sent() == before
    assert r.field == "water_collects" and r.value == {"class": "gathers_after_rain"}
    assert r.detail["year"] == 2014 and r.detail["not_flood_determination"] is True
