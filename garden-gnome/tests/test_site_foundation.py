"""The snap grid, the shared tile cache and the guarded outbound client.

PLAN.md D7 as tests: outside geodata services only ever see the grid-snapped
block, the block depends only on the grid, and the one outbound client
refuses, before anything is sent, a request that carries a finer place.
Nothing here reaches the network: every client gets an httpx.MockTransport.
"""
import random
import threading
import time
from datetime import datetime, timedelta

import httpx
import pytest

from app.config import get_settings
from app.services.site import grid, tiles
from app.services.site import http as site_http
from app.services.site.http import Coord, GeodataDisabled, OutboundRefused
from app.services.site.types import READING_FIELDS, Block, Reading, SourceUnavailable

ARBORETUM = (38.9123, -76.9681)
ZILKER = (30.2669, -97.7729)


# --- grid -------------------------------------------------------------------------

@pytest.mark.parametrize("pin", [ARBORETUM, ZILKER])
def test_the_block_holds_the_pin_well_inside_and_sits_on_grid_lines(pin):
    b = grid.snap_block(*pin)
    lat, lng = pin
    assert b.south < lat < b.north and b.west < lng < b.east
    assert min(lat - b.south, b.north - lat) >= grid.LAT_STEP / 2 - 1e-9
    assert min(lng - b.west, b.east - lng) >= grid.LNG_STEP / 2 - 1e-9
    assert grid.lat_on_grid(b.south) and grid.lat_on_grid(b.north)
    assert grid.lng_on_grid(b.west) and grid.lng_on_grid(b.east)
    assert not grid.lat_on_grid(lat) and not grid.lng_on_grid(lng)
    # About 500 metres across, as D7 requires.
    height_m = (b.north - b.south) * 111_320
    assert 450 < height_m < 600


def test_keys_are_text_with_no_floating_point():
    b = grid.snap_block(*ARBORETUM)
    assert b.key == "blk1_15565_-25656"
    assert "." not in b.key
    for cell in grid.block_cells(b):
        assert cell.startswith("cell1_") and "." not in cell
    assert grid.block_from_key(b.key) == b
    assert grid.weather_cell_key(*ARBORETUM) == "wx2_3891_-7697"


def test_the_block_depends_only_on_the_grid_not_on_where_the_pin_sits():
    """Every pin in the same neighbourhood of a grid vertex asks for the
    same block, so the request reveals the vertex and nothing finer."""
    rng = random.Random(7)
    vertex_lat = 15565 * grid.LAT_STEP
    vertex_lng = -25656 * grid.LNG_STEP
    keys = set()
    for _ in range(500):
        lat = vertex_lat + rng.uniform(-0.49, 0.49) * grid.LAT_STEP
        lng = vertex_lng + rng.uniform(-0.49, 0.49) * grid.LNG_STEP
        keys.add(grid.snap_block(lat, lng).key)
    assert keys == {"blk1_15565_-25656"}
    # And a pin past the half-way line belongs to the next vertex.
    assert grid.snap_block(vertex_lat + 0.51 * grid.LAT_STEP, vertex_lng).key \
        == "blk1_15566_-25656"


def test_the_default_footprint_is_a_north_aligned_8500_square_foot_square():
    box = grid.default_footprint_box(*ARBORETUM)
    assert abs(grid.box_area_sqft(box) - 8500) < 1
    lat, lng = ARBORETUM
    assert abs((box["south"] + box["north"]) / 2 - lat) < 1e-9
    assert abs((box["west"] + box["east"]) / 2 - lng) < 1e-9
    poly = grid.default_footprint(*ARBORETUM)
    assert poly["type"] == "Polygon"
    assert grid.polygon_box(poly) == pytest.approx(box)


def test_reading_and_block_shapes():
    assert len(READING_FIELDS) == 22 and "water_collects" in READING_FIELDS
    r = Reading(field="soil_ph", value=6.2, level="low", provenance="public_map",
                source_key="ssurgo", source_version="2025", method="dominant")
    assert r.reason_codes == () and r.detail is None
    with pytest.raises(ValueError):
        Reading(field="not_a_field", value=1, level="low",
                provenance="public_map", source_key="x", source_version="",
                method="")
    assert isinstance(grid.snap_block(*ZILKER), Block)
    assert str(SourceUnavailable("ssurgo", "HTTP 503")) == "ssurgo unavailable: HTTP 503"


# --- tiles ------------------------------------------------------------------------

def test_tiles_round_trip_compressed_with_expiry_and_last_used(session):
    key = grid.snap_block(*ARBORETUM).key + "_test"
    t0 = datetime(2026, 11, 15, 12, 0, 0)
    payload = b"elevation " * 1000
    row = tiles.put(session, "3dep", "v1", key, payload,
                    ttl=timedelta(days=1), now=t0)
    assert row.size_bytes == len(payload) and len(row.payload) < len(payload)
    assert tiles.get(session, "3dep", "v1", key, now=t0 + timedelta(hours=1)) == payload
    assert row.last_used_at == t0 + timedelta(hours=1)
    assert tiles.get(session, "3dep", "v2", key, now=t0) is None
    assert tiles.get(session, "3dep", "v1", key, now=t0 + timedelta(days=2)) is None

    calls = []
    got = tiles.fetch_or_get(session, "3dep", "v1", key,
                             lambda: calls.append(1) or b"fresh",
                             now=t0 + timedelta(days=2))
    assert got == b"fresh" and calls == [1]
    assert tiles.fetch_or_get(session, "3dep", "v1", key, lambda: b"never",
                              now=t0 + timedelta(days=2)) == b"fresh"
    tiles.put_json(session, "ssurgo", "2025", key, {"mukey": "123"})
    assert tiles.get_json(session, "ssurgo", "2025", key) == {"mukey": "123"}


def test_a_tile_key_must_name_a_block(session):
    with pytest.raises(ValueError):
        tiles.put(session, "3dep", "v1", "38.9123,-76.9681", b"x")


# --- the outbound client ----------------------------------------------------------

def _client(handler, **kw) -> site_http.OutboundClient:
    return site_http.OutboundClient(transport=httpx.MockTransport(handler),
                                    sleep=lambda s: None, **kw)


def _ok(request):
    return httpx.Response(200, json={"ok": True})


BLOCK = grid.snap_block(*ARBORETUM)
BBOX = f"{BLOCK.west},{BLOCK.south},{BLOCK.east},{BLOCK.north}"
URL = "https://example.test/arcgis/rest/services/X/ImageServer/exportImage"


def test_a_request_for_the_block_goes_out_with_a_generic_user_agent():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, content=b"tile")

    with _client(handler) as c:
        r = c.get(URL, params={"bbox": BBOX, "bboxSR": "4326", "imageSR": "26918",
                               "size": "512,512", "f": "image"},
                  coords={"bbox": Coord.BBOX}, source_key="3dep")
    assert r.content == b"tile"
    ua = seen[0].headers["user-agent"]
    assert ua == site_http.USER_AGENT and "@" not in ua


@pytest.mark.parametrize("params,coords", [
    ({"bbox": f"{ARBORETUM[1]},{ARBORETUM[0]},{BLOCK.east},{BLOCK.north}"},
     {"bbox": Coord.BBOX}),
    ({"geometry": f"{ARBORETUM[1]},{ARBORETUM[0]}"}, {"geometry": Coord.POINT_LNGLAT}),
    ({"geometry": '{"x": -76.9681, "y": 38.9123}'}, {"geometry": Coord.POINT_LNGLAT}),
    ({"lat": "38.9123"}, {"lat": Coord.LAT}),
    # Undeclared: still caught by the scan.
    ({"where": "x", "point": "-76.9681,38.9123"}, {}),
    # A projected input system would carry the house as metres.
    ({"bbox": "323456,4309876,323712,4310132", "bboxSR": "26918"}, {}),
    # Declared on the wrong axis: a longitude grid line is not a latitude one.
    ({"bbox": f"{BLOCK.west},{BLOCK.west},{BLOCK.east},{BLOCK.north}"},
     {"bbox": Coord.BBOX}),
])
def test_the_guard_refuses_an_off_grid_coordinate_before_sending(params, coords):
    sent = []
    with _client(lambda r: sent.append(r) or _ok(r)) as c:
        with pytest.raises(OutboundRefused):
            c.get(URL, params=params, coords=coords)
    assert sent == []


def test_the_guard_reads_coordinates_inside_a_sql_body():
    """The soil survey takes SQL; a WKT polygon inside it is checked pair by
    pair, and a stray point elsewhere in the text is caught by the scan."""
    good = (f"SELECT mukey FROM SDA_Get_Mukey_from_intersection_with_WktWgs84("
            f"'POLYGON(({BLOCK.west} {BLOCK.south}, {BLOCK.east} {BLOCK.south}, "
            f"{BLOCK.east} {BLOCK.north}, {BLOCK.west} {BLOCK.north}, "
            f"{BLOCK.west} {BLOCK.south}))')")
    off = good.replace(f"{BLOCK.east} {BLOCK.north}", "-76.9681 38.9123")
    stray = good + " -- near -76.9681"
    with _client(_ok) as c:
        c.post("https://sda.example.test/Tabular/post.rest",
               json={"query": good, "format": "JSON"}, coords={"query": Coord.WKT})
        for body in (off, stray):
            with pytest.raises(OutboundRefused):
                c.post("https://sda.example.test/Tabular/post.rest",
                       json={"query": body, "format": "JSON"},
                       coords={"query": Coord.WKT})


def test_the_guard_reads_the_url_path_and_geojson():
    with _client(_ok) as c:
        with pytest.raises(OutboundRefused):
            c.get("https://example.test/points/38.9123,-76.9681")
        c.get("https://example.test/points/38.91,-76.97")  # weather rounding passes
        geom = {"type": "Polygon", "coordinates": [[
            [BLOCK.west, BLOCK.south], [BLOCK.east, BLOCK.south],
            [BLOCK.east, BLOCK.north], [BLOCK.west, BLOCK.south]]]}
        c.post(URL, json={"geometry": geom}, coords={"geometry": Coord.GEOJSON})
        geom["coordinates"][0][1] = [-76.9681, 38.9123]
        with pytest.raises(OutboundRefused):
            c.post(URL, json={"geometry": geom}, coords={"geometry": Coord.GEOJSON})


def test_a_weather_point_may_carry_two_decimal_places_and_no_more():
    with _client(_ok, flag="season_plan") as c:
        c.get("https://api.example.test/points", params={"p": "38.91,-76.97"},
              coords={"p": Coord.WEATHER_POINT})
        with pytest.raises(OutboundRefused):
            c.get("https://api.example.test/points", params={"p": "38.912,-76.97"},
                  coords={"p": Coord.WEATHER_POINT})


def test_retries_are_bounded_and_end_in_source_unavailable():
    attempts = []

    def flaky(request):
        attempts.append(1)
        return httpx.Response(503)

    with _client(flaky) as c:
        with pytest.raises(SourceUnavailable) as err:
            c.get(URL, params={"bbox": BBOX}, coords={"bbox": Coord.BBOX},
                  source_key="nlcd")
    assert len(attempts) == site_http.MAX_RETRIES + 1
    assert err.value.source_key == "nlcd"

    def down(request):
        attempts.append(1)
        raise httpx.ConnectError("refused", request=request)

    attempts.clear()
    with _client(down) as c:
        with pytest.raises(SourceUnavailable):
            c.get(URL)
    assert len(attempts) == site_http.MAX_RETRIES + 1

    attempts.clear()
    with _client(lambda r: attempts.append(1) or httpx.Response(404)) as c:
        with pytest.raises(SourceUnavailable):
            c.get(URL)
    assert len(attempts) == 1  # a 404 is an answer, not a reason to retry


def test_at_most_two_requests_run_at_once_against_one_host():
    running, peak, lock = [0], [0], threading.Lock()

    def slow(request):
        with lock:
            running[0] += 1
            peak[0] = max(peak[0], running[0])
        time.sleep(0.05)
        with lock:
            running[0] -= 1
        return httpx.Response(200)

    def one():
        with _client(slow) as c:
            c.get("https://slow.example.test/x")

    threads = [threading.Thread(target=one) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert peak[0] == site_http.PER_HOST_LIMIT


def test_with_the_flag_off_nothing_is_sent(monkeypatch):
    monkeypatch.setattr(get_settings(), "site_profile_enabled", False)
    sent = []
    before = site_http.requests_sent()
    with _client(lambda r: sent.append(r) or _ok(r)) as c:
        with pytest.raises(GeodataDisabled):
            c.get(URL, params={"bbox": BBOX}, coords={"bbox": Coord.BBOX})
    assert sent == [] and site_http.requests_sent() == before


def test_tests_cannot_reach_the_network_by_default():
    with site_http.get_client() as c:
        with pytest.raises(AssertionError, match="network"):
            c.get("https://example.test/x")
