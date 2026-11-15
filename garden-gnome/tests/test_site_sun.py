"""B2b: sun-position maths, canopy heights and the sun estimate (build spec
section 5). Known solar values, synthetic obstacles, the recorded landmark
windows, and the canopy reader against a synthetic tiled TIFF served by a
MockTransport. Nothing here reaches the network.
"""
import math
import struct
import zlib
from datetime import date, datetime, timezone

import httpx
import numpy as np
import pytest

from app.services.site import grid, sun, terrain, tiles
from app.services.site import http as site_http
from app.services.site.sources import canopy, elevation
from app.services.site.types import Reading
from tests.test_site_terrain import _fresh_caches  # noqa: F401 -- autouse
from tests.test_site_terrain import cache_window
from tests.test_site_terrain import ARBORETUM, ZILKER, owner_box, recorded, window_from

UTC = timezone.utc


# --- sun position against known values -------------------------------------------------

def test_declination_at_the_solstices_and_the_equinox():
    assert sun.declination(datetime(2026, 6, 21, 12, tzinfo=UTC)) == pytest.approx(23.44, abs=0.02)
    assert sun.declination(datetime(2026, 12, 21, 12, tzinfo=UTC)) == pytest.approx(-23.44, abs=0.02)
    # The March 2026 equinox was on 20 March at about 14:46 UTC.
    assert sun.declination(datetime(2026, 3, 20, 14, 46, tzinfo=UTC)) == pytest.approx(0, abs=0.02)


def test_equation_of_time_at_its_extremes():
    assert sun.equation_of_time(datetime(2026, 11, 3, 12, tzinfo=UTC)) == pytest.approx(16.4, abs=0.2)
    assert sun.equation_of_time(datetime(2026, 2, 11, 12, tzinfo=UTC)) == pytest.approx(-14.2, abs=0.2)


def test_noon_at_washington_on_the_june_solstice():
    # Solar noon altitude is 90 - 38.91 + 23.44 = 74.53 degrees, due south.
    elev, az = sun.sun_position(datetime(2026, 6, 21, 17, 10, tzinfo=UTC), 38.91, -76.97)
    assert elev == pytest.approx(74.5, abs=0.1)
    assert az == pytest.approx(180, abs=1.0)
    ha = sun.hour_angle(datetime(2026, 6, 21, 17, 10, tzinfo=UTC), -76.97)
    assert abs(ha) < 1.0


def test_morning_sun_is_in_the_east_and_afternoon_sun_in_the_west():
    _, am = sun.sun_position(datetime(2026, 9, 1, 13, 0, tzinfo=UTC), 38.91, -76.97)
    _, pm = sun.sun_position(datetime(2026, 9, 1, 21, 0, tzinfo=UTC), 38.91, -76.97)
    assert 60 < am < 130 and 230 < pm < 300


def test_day_length_from_the_sampled_path():
    # Geometric day length (the sun's centre above a flat horizon, no
    # refraction), so a few minutes shorter than published sunrise to sunset.
    flat = np.full((1, 72), -90.0)
    for lat, day, hours in [(0.0, date(2026, 3, 20), 12.0), (38.91, date(2026, 6, 21), 14.7),
                            (38.91, date(2026, 12, 21), 9.3)]:
        e, a, step = sun.season_sun([day], lat, -77.0, step_minutes=2)
        got = sun.direct_hours(e, a, flat, step, 1)[0]
        assert got == pytest.approx(hours, abs=0.15)


def test_the_growing_season_comes_from_the_frost_normals_or_april_to_october():
    normals = {"spring": {"32": {"p50": "04-02"}}, "fall": {"32": {"p50": "11-08"}}}
    assert sun.season_from_normals(normals) == ((4, 2), (11, 8), "frost_free_period")
    assert sun.season_from_normals(None) == ((4, 1), (10, 31), "april_to_october")
    assert sun.season_from_normals({"status": "none", "spring": {}, "fall": {}})[2] == \
        "april_to_october"
    days = sun.season_days((4, 1), (10, 31))
    assert days[0] == date(2026, 4, 1) and (days[1] - days[0]).days == 7


def test_categories_use_the_spec_thresholds():
    assert sun.category(6.0) == "full_sun" and sun.category(5.99) == "part_shade"
    assert sun.category(3.0) == "part_shade" and sun.category(2.9) == "shade"


# --- horizons and obstacles ------------------------------------------------------------

def _canopy(win, fn):
    """Canopy heights fn(east_m, north_m) on the window's lattice."""
    b = win.block
    rows, cols = win.z.shape
    lat = b.north - (np.arange(rows) + 0.5) * (b.north - b.south) / rows
    lng = b.west + (np.arange(cols) + 0.5) * (b.east - b.west) / cols
    N = (lat - ARBORETUM[0]) * elevation.M_PER_DEG_LAT
    E = (lng - ARBORETUM[1]) * elevation.M_PER_DEG_LAT * math.cos(math.radians(38.9125))
    EE, NN = np.meshgrid(E, N)
    return canopy.CanopyGrid(block=b, height_m=fn(EE, NN).astype(np.float32),
                             resolution_m=0.93)


def _est(win, cg=None, box=None, tree_share=None):
    box = box or owner_box(ARBORETUM, half_m=6, dx_m=20)
    return sun.estimate(ARBORETUM[0], ARBORETUM[1], win.block, box, ARBORETUM,
                        window=win, canopy=cg, tree_share=tree_share)


def test_open_flat_ground_gets_the_whole_day():
    win = window_from(lambda e, n: 0 * e + 10)
    est = _est(win)
    # April to October at 39 degrees north averages about 13.3 hours of daylight.
    assert est.open_sky_hours == pytest.approx(13.3, abs=0.3)
    assert est.hours == est.open_sky_hours and est.category == "full_sun"
    assert est.counted == ("terrain",)
    assert "canopy_height" in est.not_counted and "buildings" in est.not_counted


def test_a_hill_to_the_south_blocks_sun_but_an_even_slope_hardly_matters():
    # A bank 30 metres high just south of the box: the terrain horizon counts it.
    hill = window_from(lambda e, n: np.where((n < -15) & (n > -45), 30.0, 0.0))
    box = owner_box(ARBORETUM, half_m=3, dx_m=20)
    flat = _est(window_from(lambda e, n: 0 * e), box=box)
    assert _est(hill, box=box).open_sky_hours < flat.open_sky_hours - 3
    # Direct-sun hours barely change on an even slope of either facing: in the
    # growing season the low sun is in the east and west (the research found
    # 11.2 to 11.8 hours on slopes up to 30 degrees).
    g = math.tan(math.radians(20))
    north = _est(window_from(lambda e, n: 50 - g * n), box=box).open_sky_hours
    south = _est(window_from(lambda e, n: 50 + g * n), box=box).open_sky_hours
    assert abs(north - flat.open_sky_hours) < 1.5 and abs(south - flat.open_sky_hours) < 1.5


def test_a_tall_tree_line_to_the_south_shades_but_one_to_the_north_hardly_does():
    win = window_from(lambda e, n: 0 * e)
    south = _canopy(win, lambda e, n: np.where((n > -12) & (n < -6), 25.0, 0.0))
    north = _canopy(win, lambda e, n: np.where((n > 6) & (n < 12), 25.0, 0.0))
    box = owner_box(ARBORETUM, half_m=3, dx_m=20)
    s, nth = _est(win, south, box), _est(win, north, box)
    assert s.hours < nth.hours - 3
    assert nth.hours > 9
    assert s.counted == ("terrain", "canopy_height")


def test_ground_under_a_crown_is_shade_while_leaves_are_out():
    win = window_from(lambda e, n: 0 * e)
    cover = _canopy(win, lambda e, n: 0 * e + 18.0)
    est = _est(win, cover)
    assert est.hours == pytest.approx(0.0) and est.category == "shade"
    assert est.cover_share == 1.0


def test_tree_cover_share_is_the_coarse_fallback():
    win = window_from(lambda e, n: 0 * e)
    est = _est(win, None, tree_share=0.5)
    assert est.hours == pytest.approx(est.open_sky_hours / 2)
    assert "tree_cover" in est.counted and "canopy_height" in est.not_counted


def test_no_terrain_and_no_canopy_is_not_known_yet():
    win = window_from(lambda e, n: 0 * e)
    est = sun.estimate(ARBORETUM[0], ARBORETUM[1], win.block,
                       owner_box(ARBORETUM), ARBORETUM, window=None, canopy=None)
    [r] = sun.readings_for(est, is_default=False, window=None, canopy=None)
    assert r.field == "sun_estimate" and r.level == "unknown" and r.value is None


def test_confidence_never_above_area_estimate_and_rough_without_buildings():
    win = window_from(lambda e, n: 0 * e)
    cg = _canopy(win, lambda e, n: 0 * e)
    for est, default in [(_est(win, cg), False), (_est(win, cg), True),
                         (_est(win, None, tree_share=0.3), False)]:
        rs = {r.field: r for r in sun.readings_for(est, is_default=default, window=win, canopy=cg)}
        se = rs["sun_estimate"]
        assert se.level == "low"                      # buildings are never counted
        assert "buildings_not_counted" in se.reason_codes
        assert "buildings" in se.detail["not_counted"]
        assert all(r.level in ("medium", "low") for r in rs.values())
        assert se.value["category"] in ("full_sun", "part_shade", "shade")
        assert se.detail["thresholds_hours"] == {"full_sun": 6.0, "part_shade": 3.0}
    rs = {r.field: r for r in sun.readings_for(_est(win, None, tree_share=0.3),
                                               is_default=False, window=win, canopy=None)}
    assert "coarse_canopy_only" in rs["sun_estimate"].reason_codes
    assert rs["canopy_shade"].level == "low"


def test_detail_lets_the_copy_say_what_was_and_was_not_counted():
    win = window_from(lambda e, n: 0 * e)
    cg = _canopy(win, lambda e, n: np.where(n < -8, 20.0, 0.0))
    rs = {r.field: r for r in sun.readings_for(_est(win, cg), is_default=False,
                                               window=win, canopy=cg)}
    d = rs["sun_estimate"].detail
    assert d["counted"] == ["terrain", "canopy_height"]
    assert d["not_counted"] == ["buildings"]
    assert d["canopy_resolution_m"] == 0.93 and d["leaves_out"] is True
    assert rs["open_sky_sun"].value["hours"] >= rs["sun_estimate"].value["hours"]
    assert rs["canopy_shade"].value["hours_lost"] >= 0
    assert rs["canopy_shade"].detail["source_name"].startswith("Meta and World Resources")


# --- the recorded landmarks -------------------------------------------------------------

@pytest.mark.parametrize("name,pin", [("arboretum", ARBORETUM), ("zilker", ZILKER)])
def test_the_recorded_landmarks_give_a_plausible_estimate(name, pin):
    block, z, chm = recorded(name)
    win = elevation.ElevationWindow(block=block, z=z, valid=np.ones_like(z, bool),
                                    resolution_m=1.0, year=2014)
    cg = canopy.CanopyGrid(block=block, height_m=chm, resolution_m=0.93)
    box = grid.default_footprint_box(*pin)
    est = sun.estimate(pin[0], pin[1], block, box, pin, window=win, canopy=cg)
    assert 12.0 < est.open_sky_hours < 14.0
    assert 0 <= est.hours <= est.open_sky_hours
    assert est.spread[0] <= est.hours <= est.spread[1]
    assert est.points > 20


# --- the canopy reader ----------------------------------------------------------------------

def test_quadkeys_of_the_landmarks():
    for pin, key in [(ARBORETUM, "0320100323"), (ZILKER, "0231301203")]:
        x, y = canopy.global_px(*pin)
        assert canopy.quadkey(int(x) // canopy.FILE_PX, int(y) // canopy.FILE_PX) == key


def _tiff(fill):
    """A classic little-endian tiled TIFF like the canopy files: 32768 square,
    512 tiles, deflate. `fill(gtx, gty)` gives a tile's uint8 array or None."""
    n_tiles = (canopy.FILE_PX // canopy.TILE_PX) ** 2
    entries = [(256, 3, 1, canopy.FILE_PX), (257, 3, 1, canopy.FILE_PX), (258, 3, 1, 8),
               (259, 3, 1, 8), (277, 3, 1, 1), (317, 3, 1, 1), (322, 3, 1, 512),
               (323, 3, 1, 512)]
    ifd_off = 8
    n_e = len(entries) + 2
    arrays_off = ifd_off + 2 + 12 * n_e + 4
    off_arr = arrays_off
    cnt_arr = arrays_off + 4 * n_tiles
    data_start = 65536
    offsets, counts, blobs = [0] * n_tiles, [0] * n_tiles, []
    pos = data_start
    for k in range(n_tiles):
        a = fill(k % 64, k // 64)
        if a is None:
            continue
        raw = zlib.compress(a.astype(np.uint8).tobytes())
        offsets[k], counts[k] = pos, len(raw)
        blobs.append(raw)
        pos += len(raw)
    out = bytearray(b"II*\x00" + struct.pack("<I", ifd_off))
    out += struct.pack("<H", n_e)
    for tag, typ, cnt, val in entries:
        out += struct.pack("<HHIHH", tag, typ, cnt, val, 0)
    out += struct.pack("<HHII", 324, 4, n_tiles, off_arr)
    out += struct.pack("<HHII", 325, 4, n_tiles, cnt_arr)
    out += struct.pack("<I", 0)
    out += struct.pack("<" + "I" * n_tiles, *offsets)
    out += struct.pack("<" + "I" * n_tiles, *counts)
    out += b"\0" * (data_start - len(out))
    for b in blobs:
        out += b
    return bytes(out)


class FakeS3:
    def __init__(self, files):
        self.files = files
        self.requests: list[httpx.Request] = []

    def __call__(self, request):
        self.requests.append(request)
        name = request.url.path.rsplit("/", 1)[-1].removesuffix(".tif")
        body = self.files.get(name)
        if body is None:
            return httpx.Response(404)
        start, end = (int(x) for x in request.headers["Range"].split("=")[1].split("-"))
        return httpx.Response(206, content=body[start:end + 1])


def _canopy_files(block):
    """Trees 20 m tall east of the block's middle longitude, none west."""
    mid_x, _ = canopy.global_px(block.north, (block.west + block.east) / 2)

    cols, rows = canopy.block_tiles(block)
    near = {(c % 64, r % 64) for c in cols for r in rows}

    def fill(tx, ty):
        if (tx, ty) not in near:
            return None
        a = np.zeros((512, 512), np.uint8)
        gx0 = (293 * 64 + tx) * 512
        cols = np.arange(512) + gx0
        a[:, cols >= mid_x] = 20
        return a
    x, y = canopy.global_px(block.north, block.west)
    return {canopy.quadkey(int(x) // canopy.FILE_PX, int(y) // canopy.FILE_PX): _tiff(fill)}


def test_the_canopy_is_read_by_ranges_that_depend_only_on_the_block(session):
    block = grid.snap_block(*ARBORETUM)
    fake = FakeS3(_canopy_files(block))
    with site_http.OutboundClient(transport=httpx.MockTransport(fake)) as c:
        g = canopy.load_canopy(session, block, client=c)
    assert g.height_m.shape == (500, 600)
    assert g.height_m[:, :290].max() == 0 and g.height_m[:, 310:].min() == 20
    # One directory read and the four internal tiles the block touches.
    assert len(fake.requests) == 5
    assert all(r.url.path.endswith("/0320100323.tif") for r in fake.requests)
    assert fake.requests[0].headers["Range"] == "bytes=0-65535"
    # Every pin in the same block asks for exactly the same ranges.
    other = grid.snap_block(ARBORETUM[0] + 0.0004, ARBORETUM[1] - 0.0005)
    assert other == block
    fake2 = FakeS3(_canopy_files(block))
    with site_http.OutboundClient(transport=httpx.MockTransport(fake2)) as c:
        canopy.fetch_mosaic(other, c)
    assert [r.headers["Range"] for r in fake2.requests] == \
        [r.headers["Range"] for r in fake.requests]
    # Cached: nothing is sent the second time.
    with site_http.OutboundClient() as c:   # the test transport refuses
        again = canopy.load_canopy(session, block, client=c)
    assert (again.height_m == g.height_m).all()


def test_canopy_read_gives_cover_over_the_footprint(session):
    block = grid.snap_block(*ARBORETUM)
    fake = FakeS3(_canopy_files(block))
    with site_http.OutboundClient(transport=httpx.MockTransport(fake)) as c:
        east = canopy.read(block, ARBORETUM, owner_box(ARBORETUM, 10, dx_m=60), client=c,
                           session=session)
        west = canopy.read(block, ARBORETUM, owner_box(ARBORETUM, 10, dx_m=-60), client=c,
                           session=session)
    assert east[0].field == "canopy_shade" and east[0].value["cover_share"] == 1.0
    assert west[0].value["cover_share"] == 0.0
    assert east[0].detail["licence"] == "Creative Commons Attribution 4.0"
    assert east[0].level == "medium"


def test_tiff_header_parsing_refuses_what_it_cannot_read():
    with pytest.raises(ValueError):
        canopy.parse_header(b"GIF89a" + b"\0" * 100)
    lay = canopy.parse_header(_tiff(lambda tx, ty: None)[:65536])
    assert (lay.width, lay.tile_w, lay.compression, len(lay.offsets)) == (32768, 512, 8, 4096)


# --- the sun source through the cache ------------------------------------------------------

def test_sun_read_uses_the_cached_window_and_canopy_and_sends_nothing(session):
    block = grid.snap_block(*ARBORETUM)
    win = window_from(lambda e, n: 0 * e + 10)
    cache_window(session, block, win, year=2014)
    fake = FakeS3(_canopy_files(block))
    with site_http.OutboundClient(transport=httpx.MockTransport(fake)) as c:
        canopy.load_canopy(session, block, client=c)
    before = site_http.requests_sent()
    with site_http.OutboundClient() as c:   # refuses everything
        west = sun.read(block, ARBORETUM, owner_box(ARBORETUM, 8, dx_m=-90), client=c,
                        session=session)
        east = sun.read(block, ARBORETUM, owner_box(ARBORETUM, 8, dx_m=90), client=c,
                        session=session)
    assert site_http.requests_sent() == before
    w = {r.field: r for r in west}
    e = {r.field: r for r in east}
    assert set(w) == {"open_sky_sun", "canopy_shade", "sun_estimate"}
    assert w["sun_estimate"].value["category"] == "full_sun"
    assert e["sun_estimate"].value["category"] == "shade"


def test_sun_read_falls_back_to_tree_cover_when_the_canopy_map_fails(session):
    block = grid.snap_block(*ZILKER)
    win = window_from(lambda e, n: 0 * e + 150, pin=ZILKER)
    cache_window(session, block, win, year=2017)
    tree = Reading(field="tree_cover", value={"share": 0.3}, level="medium",
                   provenance="public_map", source_key="nlcd", source_version="2023",
                   method="tcc")
    def unreachable(request):   # like the profile's cached-data-only client
        raise httpx.ConnectError("cached data only", request=request)
    with site_http.OutboundClient(transport=httpx.MockTransport(unreachable),
                                  max_retries=0) as c:
        rs = {r.field: r for r in sun.read(block, ZILKER, None, client=c, session=session,
                                           readings=[tree])}
    se = rs["sun_estimate"]
    assert "tree_cover" in se.detail["counted"] and se.level == "low"
    assert "default_footprint" in se.reason_codes
    assert se.value["hours"] == pytest.approx(rs["open_sky_sun"].value["hours"] * 0.7, abs=0.1)
