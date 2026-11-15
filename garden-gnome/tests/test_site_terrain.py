"""B2b: the elevation window and the terrain maths (build spec section 5).

Pure maths on synthetic surfaces with known answers (a plane, a bowl, a
ridge), the recorded Arboretum and Zilker windows, and the elevation source
through a MockTransport. Nothing here reaches the network.
"""
import json
import math
from pathlib import Path

import httpx
import numpy as np
import pytest

from app.services.site import grid, terrain, tiles
from app.services.site import http as site_http
from app.services.site.sources import elevation
from app.services.site.types import Block, SourceUnavailable

ARBORETUM = (38.9123, -76.9681)
ZILKER = (30.2669, -97.7729)
FIX = Path(__file__).parent / "fixtures" / "site_terrain"


# --- helpers -----------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _fresh_caches():
    """The in-process memos would otherwise carry one test's answers into
    the next."""
    elevation._RECENT.clear()
    elevation._SURVEY_TRIED.clear()
    terrain._ANALYSES.clear()
    yield

def window_from(fn, pin=ARBORETUM, resolution_m=1.0, year=2014, block=None):
    """A window over the pin's block whose height is fn(east_m, north_m),
    metres measured from the pin."""
    b = block or grid.snap_block(*pin)
    rows, cols = elevation.lattice_shape(b.west, b.south, b.east, b.north)
    lat = b.north - (np.arange(rows) + 0.5) * (b.north - b.south) / rows
    lng = b.west + (np.arange(cols) + 0.5) * (b.east - b.west) / cols
    north = (lat - pin[0]) * elevation.M_PER_DEG_LAT
    mid = math.radians((b.south + b.north) / 2)
    east = (lng - pin[1]) * elevation.M_PER_DEG_LAT * math.cos(mid)
    E, N = np.meshgrid(east, north)
    z = fn(E, N).astype(np.float32)
    return elevation.ElevationWindow(block=b, z=z, valid=np.ones_like(z, bool),
                                     resolution_m=resolution_m, year=year)


def recorded(name):
    d = np.load(FIX / f"{name}_crop.npz")
    w, s, e, n = (float(x) for x in d["bounds"])
    block = Block(key="blk1_0_0", west=w, south=s, east=e, north=n)
    z = d["z_cm"].astype(np.float32) / 100
    return block, z, d["chm_m"].astype(np.float32)


def owner_box(pin, half_m=15.0, dx_m=0.0, dy_m=0.0):
    lat, lng = pin
    dlat = half_m / elevation.M_PER_DEG_LAT
    dlng = half_m / (elevation.M_PER_DEG_LAT * math.cos(math.radians(lat)))
    clat = lat + dy_m / elevation.M_PER_DEG_LAT
    clng = lng + dx_m / (elevation.M_PER_DEG_LAT * math.cos(math.radians(lat)))
    return {"west": clng - dlng, "south": clat - dlat, "east": clng + dlng,
            "north": clat + dlat}


def cache_window(session, block, win, year=2014):
    """Store a window and its survey details the way load_window does."""
    tiles.put(session, elevation.PROVIDER, elevation.DATASET_VERSION, f"{block.key}_dem",
              elevation.encode_window(win.z, win.valid, {"fetched_by": "block"}))
    tiles.put_json(session, elevation.PROVIDER, elevation.DATASET_VERSION,
                   f"{block.key}_dem_survey", {"resolution_m": win.resolution_m, "year": year})


def bsq_body(z: np.ndarray, valid=None) -> bytes:
    v = np.ones_like(z, bool) if valid is None else valid
    return z.astype("<f4").tobytes() + np.packbits(v.astype(np.uint8).ravel()).tobytes()


# --- footprints -------------------------------------------------------------------

def test_footprints_accept_the_default_square_geojson_or_an_owner_box():
    box, default = terrain.footprint_box(ARBORETUM, None)
    assert default and box == pytest.approx(grid.default_footprint_box(*ARBORETUM))
    box, default = terrain.footprint_box(ARBORETUM, grid.default_footprint(*ARBORETUM))
    assert default
    b = owner_box(ARBORETUM)
    box, default = terrain.footprint_box(ARBORETUM, b)
    assert not default and box == b
    box, default = terrain.footprint_box(ARBORETUM, grid.box_polygon(
        b["west"], b["south"], b["east"], b["north"]))
    assert not default and box == pytest.approx(b)


def test_the_pin_radius_is_left_out_of_the_footprint():
    win = window_from(lambda e, n: 0 * e)
    box = owner_box(ARBORETUM, half_m=12)
    with_pin = terrain.footprint_mask(win.z.shape, win.block, box, ARBORETUM, exclude_radius_m=0)
    without = terrain.footprint_mask(win.z.shape, win.block, box, ARBORETUM)
    gone = (with_pin & ~without).sum() * win.dx_m * win.dy_m
    assert gone == pytest.approx(math.pi * 10 ** 2, rel=0.08)


# --- slope and facing on synthetic planes -------------------------------------------

@pytest.mark.parametrize("facing_deg", [0, 45, 90, 135, 180, 225, 270, 315, 63])
def test_a_tilted_plane_gives_its_slope_and_facing_to_a_tenth_of_a_degree(facing_deg):
    slope = 6.0
    g = math.tan(math.radians(slope))
    a = math.radians(facing_deg)
    # Ground falls toward `facing_deg`.
    win = window_from(lambda e, n: 50 - g * (e * math.sin(a) + n * math.cos(a)))
    s = terrain.summarise(win, owner_box(ARBORETUM), ARBORETUM)
    assert s.slope_deg == pytest.approx(slope, abs=0.1)
    assert s.facing_deg == pytest.approx(facing_deg, abs=0.1)
    assert s.facing_consistency > 0.99
    assert s.low_area_m2 == 0


def test_under_two_degrees_is_flat_with_no_compass_word():
    g = math.tan(math.radians(1.5))
    win = window_from(lambda e, n: 10 - g * e)
    rs = {r.field: r for r in terrain.readings_for(
        win, owner_box(ARBORETUM), False, ARBORETUM)}
    assert rs["facing"].value == {"direction": "flat", "degrees": None}
    assert "flat" in rs["facing"].reason_codes
    assert rs["slope"].value["degrees"] == pytest.approx(1.5, abs=0.1)


def test_horn_gradient_matches_the_plane_and_the_compass_words():
    z = np.add.outer(np.arange(5) * -1.0, np.arange(6) * 2.0)   # rises east, rises north
    gx, gy = terrain.horn_gradient(z, 1.0, 1.0)
    assert gx[2, 2] == pytest.approx(2.0) and gy[2, 2] == pytest.approx(1.0)
    _, aspect = terrain.slope_aspect(z, 1.0, 1.0)
    assert aspect[2, 2] == pytest.approx((math.degrees(math.atan2(-2, -1)) + 360) % 360)
    assert terrain.compass(59) == "north_east" and terrain.compass(350) == "north"


# --- depressions and flow on a bowl and a ridge --------------------------------------

def test_a_bowl_fills_to_its_rim_and_everything_drains_to_its_middle():
    z = np.full((41, 41), 5.0)
    r = np.hypot(*np.meshgrid(np.arange(41) - 20.0, np.arange(41) - 20.0))
    z = np.where(r < 15, 5.0 - (15 - r) * 0.1, z)       # 1.5 m deep at the centre
    filled, receiver, order = terrain.fill_and_route(z)
    depth = filled - z
    assert depth[20, 20] == pytest.approx(1.5, abs=1e-6)
    assert depth[0, 0] == 0 and np.all(filled >= z - 1e-12)
    acc = terrain.flow_accumulation(receiver, order).reshape(z.shape)
    # Every cell drains somewhere; the edge outlets together take all of it.
    outlets = receiver.reshape(z.shape) < 0
    assert acc[outlets].sum() == pytest.approx(z.size)


def test_a_bowl_in_the_window_is_a_low_spot_and_water_gathers():
    win = window_from(lambda e, n: 20 + 0.0 * e + np.where(
        np.hypot(e - 12, n) < 6, -0.4 * (6 - np.hypot(e - 12, n)) / 6, 0.0))
    s = terrain.summarise(win, owner_box(ARBORETUM), ARBORETUM)
    assert s.low_depth_max_m == pytest.approx(0.4, abs=0.05)
    assert s.low_area_m2 > terrain.LOW_SPOT_AREA_M2
    rs = {r.field: r for r in terrain.readings_for(win, owner_box(ARBORETUM), False, ARBORETUM)}
    assert rs["low_spot"].value["low_spot"] is True
    assert "low_spot" in rs["low_spot"].reason_codes


def test_a_ridge_sheds_water_both_ways_and_has_no_low_spot():
    g = math.tan(math.radians(8))
    win = window_from(lambda e, n: 30 - g * np.abs(e))   # ridge runs north-south
    a = terrain.analyse_window(win)
    assert a.depth.max() == pytest.approx(0, abs=1e-6)
    rows, cols = win.z.shape
    mid = int(np.argmax(win.z[rows // 2]))
    acc = a.accumulation_m2[rows // 2]
    # Runoff builds up away from the crest on both sides.
    assert acc[mid] < acc[mid - 100] and acc[mid] < acc[mid + 100]
    east = terrain.summarise(win, owner_box(ARBORETUM, half_m=8, dx_m=30), ARBORETUM)
    west = terrain.summarise(win, owner_box(ARBORETUM, half_m=8, dx_m=-30), ARBORETUM)
    assert east.facing_deg == pytest.approx(90, abs=0.5)
    assert west.facing_deg == pytest.approx(270, abs=0.5)


def test_a_valley_gathers_runoff_from_uphill_but_a_plain_slope_does_not():
    g = math.tan(math.radians(3))
    valley = window_from(lambda e, n: 40 - g * n + 0.05 * np.abs(e))   # drains north
    bottom = owner_box((ARBORETUM[0] + 110 / elevation.M_PER_DEG_LAT, ARBORETUM[1]), 8)
    s = terrain.summarise(valley, bottom, ARBORETUM)
    assert s.catchment_max_m2 > terrain.FLOW_CATCHMENT_M2
    assert s.catchment_reaches_edge   # it starts at the window edge: "at least"
    plane = window_from(lambda e, n: 40 - g * n)
    assert terrain.summarise(plane, bottom, ARBORETUM).catchment_max_m2 < terrain.FLOW_CATCHMENT_M2


# --- confidence levels --------------------------------------------------------------

def _plane(resolution_m):
    g = math.tan(math.radians(5))
    return window_from(lambda e, n: 10 - g * n, resolution_m=resolution_m)


def test_levels_follow_the_survey_and_the_footprint():
    box = owner_box(ARBORETUM)
    default = grid.default_footprint_box(*ARBORETUM)
    lv = lambda win, b, d: {r.field: r.level for r in terrain.readings_for(win, b, d, ARBORETUM)}
    assert lv(_plane(1.0), box, False)["slope"] == "high"
    assert lv(_plane(1.0), default, True)["slope"] == "medium"
    assert lv(_plane(3.0), box, False)["slope"] == "medium"
    assert lv(_plane(10.0), box, False)["slope"] == "low"
    assert lv(_plane(None), box, False)["slope"] == "low"
    # Small zones never reach "Good estimate".
    assert lv(_plane(1.0), owner_box(ARBORETUM, half_m=3, dx_m=20), False)["slope"] == "medium"
    # No water reading from elevation coarser than 3.5 metres.
    lows = {r.field: r for r in terrain.readings_for(_plane(10.0), box, False, ARBORETUM)}
    assert lows["low_spot"].level == "unknown"
    assert "elevation_too_coarse_for_water" in lows["low_spot"].reason_codes


# --- the recorded landmarks ----------------------------------------------------------

def test_the_recorded_arboretum_window_slopes_gently_north_east():
    block, z, _ = recorded("arboretum")
    win = elevation.ElevationWindow(block=block, z=z, valid=np.ones_like(z, bool),
                                    resolution_m=1.0, year=2014)
    s = terrain.summarise(win, grid.default_footprint_box(*ARBORETUM), ARBORETUM)
    # The spike read 4.13 degrees facing 59 over a 60 metre window.
    assert 3.0 < s.slope_deg < 5.5
    assert terrain.compass(s.facing_deg) == "north_east"


def test_the_recorded_zilker_window_is_nearly_flat():
    block, z, _ = recorded("zilker")
    win = elevation.ElevationWindow(block=block, z=z, valid=np.ones_like(z, bool),
                                    resolution_m=1.0, year=2017)
    s = terrain.summarise(win, grid.default_footprint_box(*ZILKER), ZILKER)
    assert s.slope_deg < 3.0


# --- the elevation source -------------------------------------------------------------

class FakeElevation:
    """Answers like the 3DEP service: a plane falling north, the recorded
    survey details, and optionally failures."""

    def __init__(self, *, fail_block=False, truncate_first=False, samples=True):
        self.requests: list[httpx.Request] = []
        self.fail_block = fail_block
        self.truncate_first = truncate_first
        self.samples = samples

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        q = dict(request.url.params)
        path = request.url.path
        if path.endswith("/exportImage"):
            w, s, e, n = (float(x) for x in q["bbox"].split(","))
            cols, rows = (int(x) for x in q["size"].split(","))
            if self.fail_block and cols == 600:
                return httpx.Response(504, text="<html>504 Gateway Time-out</html>")
            lat = n - (np.arange(rows) + 0.5) * (n - s) / rows
            z = np.repeat((10 + (lat - 38.9) * 1000)[:, None], cols, axis=1)
            body = bsq_body(z)
            if self.truncate_first:
                self.truncate_first = False
                body = body[:1000]
            return httpx.Response(200, content=body)
        if path.endswith("/getSamples"):
            if not self.samples:
                return httpx.Response(502)
            return httpx.Response(200, json=json.loads((FIX / "arboretum_getsamples.json").read_text()))
        if path.endswith("/query"):
            return httpx.Response(200, json=json.loads((FIX / "catalog_query.json").read_text()))
        return httpx.Response(404)


def _client(fake):
    return site_http.OutboundClient(transport=httpx.MockTransport(fake), sleep=lambda s: None)


def test_the_window_is_asked_for_by_block_bounds_only_and_read_as_raw_values(session):
    fake = FakeElevation()
    block = grid.snap_block(*ARBORETUM)
    with _client(fake) as c:
        [r] = elevation.read(block, ARBORETUM, None, client=c, session=session)
    export = [q for q in fake.requests if q.url.path.endswith("/exportImage")]
    assert len(export) == 1
    p = dict(export[0].url.params)
    assert p["bbox"] == "-76.971,38.91,-76.965,38.915"
    assert p["bboxSR"] == "4326" and p["format"] == "bsq" and p["size"] == "600,500"
    for v in p["bbox"].split(","):
        assert grid.on_grid(float(v))
    samples = [q for q in fake.requests if q.url.path.endswith("/getSamples")][0]
    assert json.loads(samples.url.params["geometry"])["points"] == [[-76.968, 38.9125]]
    assert r.field == "elevation_window" and r.level == "high"
    assert r.detail["resolution_m"] == 1.0 and r.detail["year"] == 2014
    assert "MD VA Sandy NCR 2014" in r.detail["survey"]
    assert r.detail["source_name"] == "United States Geological Survey 3D Elevation Program"
    # Cached: a second read sends nothing.
    n = len(fake.requests)
    with _client(fake) as c:
        elevation._RECENT.clear()
        elevation.read(block, ARBORETUM, None, client=c, session=session)
    assert len(fake.requests) == n
    row = tiles.get(session, elevation.PROVIDER, elevation.DATASET_VERSION, f"{block.key}_dem")
    assert row is not None


def test_a_failed_block_falls_back_to_its_four_cells(session):
    fake = FakeElevation(fail_block=True)
    block = grid.snap_block(*ARBORETUM)
    with _client(fake) as c:
        win = elevation.load_window(None, block, client=c)
    cells = [q for q in fake.requests
             if q.url.path.endswith("/exportImage") and q.url.params["size"] == "300,250"]
    assert len(cells) == 4
    for q in cells:
        for v in q.url.params["bbox"].split(","):
            assert grid.on_grid(float(v))
    assert win.fetched_by == "cells" and win.z.shape == (500, 600)
    # Stitched in the right order: heights rise to the north without a seam.
    col = win.z[:, 10]
    assert np.all(np.diff(col) <= 0) and col[0] - col[-1] > 4


def test_a_cut_short_answer_is_asked_for_again():
    fake = FakeElevation(truncate_first=True)
    with _client(fake) as c:
        win = elevation.load_window(None, grid.snap_block(*ARBORETUM), client=c)
    assert win.coverage() == 1.0
    assert sum(q.url.path.endswith("/exportImage") for q in fake.requests) == 2


def test_unknown_survey_details_read_low_and_are_asked_for_again_later(session):
    fake = FakeElevation(samples=False)
    block = grid.snap_block(*ARBORETUM)
    with _client(fake) as c:
        [r] = elevation.read(block, ARBORETUM, None, client=c, session=session)
        assert r.level == "low" and "resolution_unknown" in r.reason_codes
        # Within the hour nothing is asked again, by any of the readers.
        n = len(fake.requests)
        elevation.read(block, ARBORETUM, None, client=c, session=session)
        assert len(fake.requests) == n
        # Later, only the survey details are asked for; the window is cached.
        elevation._SURVEY_TRIED.clear()
        fake.samples = True
        [r] = elevation.read(block, ARBORETUM, None, client=c, session=session)
    later = fake.requests[n:]
    assert not any(q.url.path.endswith("/exportImage") for q in later)
    assert r.level == "high" and r.detail["year"] == 2014


def test_a_service_that_keeps_failing_is_source_unavailable():
    def down(request):
        return httpx.Response(503)
    with site_http.OutboundClient(transport=httpx.MockTransport(down), sleep=lambda s: None) as c:
        with pytest.raises(SourceUnavailable):
            elevation.load_window(None, grid.snap_block(*ZILKER), client=c)


def test_the_cached_form_keeps_centimetres_and_compresses():
    win = window_from(lambda e, n: 12 + 0.05 * e + 0.3 * np.sin(n / 7))
    valid = np.ones_like(win.z, bool)
    valid[:3, :3] = False
    payload = elevation.encode_window(win.z, valid, {"resolution_m": 1.0})
    z, v, head = elevation.decode_window(payload)
    assert np.abs(z[v] - win.z[v]).max() <= 0.0051
    assert (v == valid).all() and head["resolution_m"] == 1.0
    import zlib
    assert len(zlib.compress(payload, 6)) < len(win.z.tobytes()) / 3


def test_raw_answers_are_checked_in_full():
    z = np.arange(12, dtype=np.float32).reshape(3, 4)
    got, valid = elevation.parse_bsq(bsq_body(z), 3, 4)
    assert (got == z).all() and valid.all()
    with pytest.raises(ValueError):
        elevation.parse_bsq(bsq_body(z)[:20], 3, 4)
    with pytest.raises(ValueError):
        elevation.parse_bsq(b'{"error": {"code": 500}}' + b" " * 100, 3, 4)
    mask = np.ones((3, 4), bool)
    mask[0, 1] = False
    _, valid = elevation.parse_bsq(bsq_body(z, mask), 3, 4)
    assert not valid[0, 1] and valid.sum() == 11


def test_terrain_reads_from_the_cache_without_sending(session):
    block = grid.snap_block(*ARBORETUM)
    win = _plane(1.0)
    cache_window(session, block, win, year=2014)
    before = site_http.requests_sent()
    with site_http.OutboundClient() as c:   # the test transport refuses everything
        rs = terrain.read(block, ARBORETUM, owner_box(ARBORETUM), client=c, session=session)
    assert site_http.requests_sent() == before
    by = {r.field: r for r in rs}
    assert set(by) == {"slope", "facing", "low_spot"}
    assert by["slope"].detail["degrees"] == pytest.approx(5, abs=0.15)
    assert by["facing"].value["direction"] == "north"
    assert by["slope"].detail["year"] == 2014
