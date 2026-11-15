"""B2a sources: soil survey, hardiness grid, land cover and the aerial image.

Every test replays answers recorded live on 2026-11-15 at the two public
landmarks (tests/fixtures/site_sources/*.json) or built from them; nothing
reaches the network. Each source has a failure path and an
out-of-coverage path.
"""
import base64
import json
import math
from pathlib import Path

import httpx
import pytest

from app.services.site import grid
from app.services.site import http as site_http
from app.services.site.sources import hardiness, imagery, landcover, soil
from app.services.site.types import READING_FIELDS, Reading, SourceUnavailable
from tests.explained_walker import assert_explained

ARBORETUM = (38.9123, -76.9681)
ZILKER = (30.2669, -97.7729)
FIXTURES = Path(__file__).parent / "fixtures" / "site_sources"


# --- replay ----------------------------------------------------------------------------

def _recorded(name: str) -> dict:
    out = {}
    for e in json.loads((FIXTURES / name).read_text()):
        out[(e["method"], e["url"], e["body"])] = e
    return out


class Replay:
    """An httpx transport answering only the exact requests recorded."""

    def __init__(self, *names, status=None):
        self.answers = {}
        for n in names:
            self.answers.update(_recorded(n))
        self.sent = []
        self.status = status

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = request.content.decode() if request.content else None
        self.sent.append((request.method, str(request.url), body))
        if self.status is not None:
            return httpx.Response(self.status, text="busy")
        e = self.answers.get((request.method, str(request.url), body))
        if e is None:
            raise AssertionError(f"unrecorded request: {request.method} {request.url} {body!r:.200}")
        return httpx.Response(e["status"], headers={"content-type": e["content_type"] or ""},
                              content=base64.b64decode(e["body_b64"]))


def _client(handler):
    return site_http.OutboundClient(flag="site_profile",
                                    transport=httpx.MockTransport(handler),
                                    sleep=lambda s: None)


def _by_field(readings):
    return {r.field: r for r in readings}


def _jsonable(readings):
    for r in readings:
        assert isinstance(r, Reading) and r.field in READING_FIELDS
        json.dumps(r.value)
        json.dumps(r.detail)


def _no_pin_in(sent, pin):
    """Requests carry the block, never the pin."""
    lat, lng = pin
    for _, url, body in sent:
        text = url + (body or "")
        assert f"{lat}" not in text and f"{lng}" not in text
        assert f"{lat:.4f}" not in text and f"{lng:.4f}" not in text


# --- hardiness -------------------------------------------------------------------------

def test_hardiness_reads_8a_at_the_arboretum_on_the_line_and_9a_at_zilker():
    arb = _by_field(hardiness.read(grid.snap_block(*ARBORETUM), ARBORETUM, None))
    zil = _by_field(hardiness.read(grid.snap_block(*ZILKER), ZILKER, None))
    a, z = arb["hardiness_zone"], zil["hardiness_zone"]
    assert a.value == {"zone": "8a", "low_f": 10, "high_f": 15}
    assert a.level == "medium" and a.reason_codes == ("near_zone_line",)
    assert a.detail["distance_to_line_f"] < 1
    assert z.value == {"zone": "9a", "low_f": 20, "high_f": 25}
    assert z.level == "high" and z.reason_codes == ()
    assert a.source_key == "phzm2023" and a.provenance == "public_map"
    _jsonable([a, z])


def test_hardiness_sends_nothing_anywhere():
    before = site_http.requests_sent()
    hardiness.read(grid.snap_block(*ARBORETUM), ARBORETUM, None, client=None)
    assert site_http.requests_sent() == before


@pytest.mark.parametrize("pin", [(21.3069, -157.8583), (38.0, -70.0), (51.5, -0.12)])
def test_hardiness_outside_the_contiguous_united_states_is_not_known(pin):
    (r,) = hardiness.read(grid.snap_block(*pin), pin, None)
    assert r.level == "unknown" and r.value is None
    assert r.reason_codes == ("outside_coverage",)


@pytest.mark.parametrize("temp,zone", [(10.0, "8a"), (9.5, "7b"), (14.5, "8a"),
                                        (15.0, "8b"), (-60.0, "1a"), (64.5, "13a"), (66.0, "13b")])
def test_zone_lines_fall_every_five_degrees(temp, zone):
    assert hardiness.zone_for(temp)[0] == zone


def test_the_hardiness_file_stays_small():
    assert hardiness.DATA_FILE.stat().st_size < 5_000_000


# --- soil ------------------------------------------------------------------------------

def test_soil_at_the_arboretum_is_sunnyside_capped_rough_near_a_map_line(session):
    replay = Replay("arboretum_soil.json")
    block = grid.snap_block(*ARBORETUM)
    with _client(replay) as c:
        rs = soil.read(block, ARBORETUM, None, client=c, session=session)
    _jsonable(rs)
    f = _by_field(rs)
    assert set(f) == set(soil.FIELDS)
    mu = f["soil_mapunit"]
    assert mu.value["name"].startswith("Sunnyside fine sandy loam")
    assert mu.source_version == "DC001 9/11/2026"
    assert 10 < mu.detail["distance_to_line_m"] < 30
    assert [c["name"] for c in mu.detail["components"]] == ["Sunnyside"]
    # Within 30 m of a different map unit: every soil value is a rough estimate.
    assert {r.level for r in rs} == {"low"}
    assert all("near_map_line" in r.reason_codes for r in rs)
    assert f["soil_drainage_class"].value == "Well drained"
    assert f["soil_runoff_group"].value == "B"
    assert f["soil_texture"].value["texture"] == "Fine sandy loam"
    assert f["soil_texture"].value["family"] == "loamy"
    assert f["soil_ph"].value["ph"] == 5.0 and "rough_by_default" in f["soil_ph"].reason_codes
    assert f["soil_disturbed_share"].value["percent"] == 0
    assert f["soil_flooding"].value["worst"] is None
    assert f["soil_ponding"].value["dominant"] == "None"
    assert f["soil_water_table"].value["depth_cm"] is None
    assert f["soil_slowest_layer"].value["class"] == "moderately high"
    assert 1.0 <= f["soil_water_holding"].value["inches_per_foot"] <= 2.0
    _no_pin_in(replay.sent, ARBORETUM)
    assert len(replay.sent) == 5


def test_soil_at_zilker_flags_built_up_land_and_finds_the_small_flooding_part():
    replay = Replay("zilker_soil.json")
    with _client(replay) as c:
        rs = soil.read(grid.snap_block(*ZILKER), ZILKER, None, client=c)
    f = _by_field(rs)
    assert f["soil_mapunit"].value["name"].startswith("Volente soils and Urban land")
    d = f["soil_disturbed_share"]
    assert d.value == {"percent": 20, "components": ["Urban land"], "flag": True}
    assert all(r.level == "low" and "disturbed_soil" in r.reason_codes for r in rs)
    # The summary row says "None"; the month-by-month rows find Orif.
    flood = f["soil_flooding"].value
    assert flood["dominant"] == "None"
    assert flood["worst"]["class"] == "Occasional" and flood["worst"]["percent"] == 2
    assert flood["worst"]["components"] == ["Orif"]
    assert flood["worst"]["months"] == ["March", "April", "May", "June",
                                        "September", "October"]
    mix = {c["name"]: c for c in f["soil_mapunit"].detail["components"]}
    assert mix["Urban land"]["disturbed"] and mix["Volente"]["percent"] == 45
    assert f["soil_mapunit"].detail["no_data_percent"] == 8  # rock outcrop
    assert f["soil_texture"].value["texture"] == "Silty clay loam"
    assert f["soil_ph"].value["ph"] == 8.2


def test_soil_keeps_the_block_in_the_tile_cache(session):
    block = grid.snap_block(*ZILKER)
    first = Replay("zilker_soil.json")
    with _client(first) as c:
        a = soil.read(block, ZILKER, None, client=c, session=session)
    second = Replay("zilker_soil.json")
    with _client(second) as c:
        b = soil.read(block, ZILKER, None, client=c, session=session)
    assert len(first.sent) == 5 and second.sent == [] and a == b


def test_soil_service_failure_raises_source_unavailable():
    with _client(Replay(status=503)) as c, pytest.raises(SourceUnavailable) as e:
        soil.read(grid.snap_block(*ZILKER), ZILKER, None, client=c)
    assert e.value.source_key == "ssurgo"


def test_soil_with_no_survey_map_here_is_not_known():
    """Soil Data Access answers an empty body when nothing intersects."""
    with _client(lambda r: httpx.Response(200, text="")) as c:
        rs = soil.read(grid.snap_block(38.0, -70.0), (38.0, -70.0), None, client=c)
    assert [r.field for r in rs] == list(soil.FIELDS)
    assert all(r.level == "unknown" and r.reason_codes == ("no_soil_map_here",) for r in rs)


def test_a_map_unit_without_soil_data_says_so():
    lng, lat = -76.97, 38.91
    ring = f"POLYGON (({lng - .001} {lat - .001}, {lng + .001} {lat - .001}, " \
           f"{lng + .001} {lat + .001}, {lng - .001} {lat + .001}, {lng - .001} {lat - .001}))"
    data = {"polygons": [["1", ring]],
            "mapunits": [{"mukey": "1", "muname": "Water", "areasymbol": "DC001",
                          "saverest": "9/11/2026 6:22:34 PM"}],
            "components": [{"mukey": "1", "cokey": "9", "compname": "Water",
                            "comppct_r": "100", "compkind": "Miscellaneous area"}],
            "months": [], "wet": []}
    f = _by_field(soil.readings_from(data, (lat, lng)))
    assert f["soil_mapunit"].value["name"] == "Water"
    assert f["soil_drainage_class"].level == "unknown"
    assert f["soil_drainage_class"].reason_codes == ("no_soil_data_in_map_unit",)
    assert f["soil_disturbed_share"].value["percent"] == 0


def test_wkt_rings_holes_and_distance():
    outer = "POLYGON ((0 0, 0.002 0, 0.002 0.002, 0 0.002, 0 0), " \
            "(0.0005 0.0005, 0.0015 0.0005, 0.0015 0.0015, 0.0005 0.0015, 0.0005 0.0005))"
    rings = soil.parse_rings("GEOMETRYCOLLECTION (" + outer + ", LINESTRING (0 0, 1 1))")
    assert len(rings) == 2
    assert soil._inside(rings, 0.0002, 0.0002)
    assert not soil._inside(rings, 0.001, 0.001)  # in the hole
    d = soil._distance_m(rings, 0.001, 0.0002)
    assert math.isclose(d, 0.0002 * 111_320, rel_tol=1e-3)


def test_soil_requests_put_the_block_inside_the_sql_and_pass_the_guard():
    sql = soil._wkt_box(grid.snap_block(*ARBORETUM))
    assert sql == ("POLYGON((-76.9710 38.9100,-76.9650 38.9100,-76.9650 38.9150,"
                   "-76.9710 38.9150,-76.9710 38.9100))")
    site_http.guard(soil.URL, json={"query": f"SELECT '{sql}'"},
                    coords={"query": site_http.Coord.WKT})


# --- land cover ------------------------------------------------------------------------

def test_land_cover_and_tree_cover_at_the_arboretum_are_neighbourhood_context(session):
    replay = Replay("arboretum_landcover.json")
    block = grid.snap_block(*ARBORETUM)
    with _client(replay) as c:
        rs = landcover.read(block, ARBORETUM, grid.default_footprint(*ARBORETUM),
                            client=c, session=session)
    _jsonable(rs)
    f = _by_field(rs)
    land, tree = f["land_cover"], f["tree_cover"]
    assert land.value["dominant"]["code"] == 21
    assert sum(m["percent"] for m in land.value["classes"]) in range(98, 103)
    assert 15 <= land.value["paved_percent"] <= 30
    assert land.level == "medium" and land.reason_codes == ("neighbourhood_only",)
    assert land.detail["developed_percent_1985"] < land.value["developed_percent"]
    assert 30 <= tree.value["percent"] <= 45
    assert tree.detail["footprint_percent"] is not None
    assert tree.reason_codes == ("neighbourhood_only",)
    _no_pin_in(replay.sent, ARBORETUM)
    again = Replay("arboretum_landcover.json")
    with _client(again) as c:
        landcover.read(block, ARBORETUM, None, client=c, session=session)
    assert again.sent == []


def test_land_cover_at_zilker_is_mostly_built_up_with_little_tree_cover_at_the_pin():
    with _client(Replay("zilker_landcover.json")) as c:
        f = _by_field(landcover.read(grid.snap_block(*ZILKER), ZILKER, None, client=c))
    assert f["land_cover"].value["dominant"]["code"] == 22
    assert f["land_cover"].value["developed_percent"] >= 80
    assert f["tree_cover"].detail["footprint_percent"] == 0


def test_land_cover_is_lowered_when_two_years_disagree():
    block = grid.snap_block(*ZILKER)
    n = landcover.SIZE * landcover.SIZE
    data = {"size": landcover.SIZE, "land_cover": [41] * n, "land_cover_previous": [22] * n,
            "land_cover_1985": [41] * n, "impervious": [5] * n, "canopy": [70] * n}
    land, _ = landcover.readings_from(data, block, ZILKER, None)
    assert land.level == "low" and "years_disagree" in land.reason_codes


def test_land_cover_outside_coverage_is_not_known():
    block = grid.snap_block(*ZILKER)
    n = landcover.SIZE * landcover.SIZE
    data = {"size": landcover.SIZE, "land_cover": [None] * n, "land_cover_previous": [None] * n,
            "land_cover_1985": [None] * n, "impervious": [None] * n, "canopy": [None] * n}
    rs = landcover.readings_from(data, block, ZILKER, None)
    assert [(r.field, r.level, r.reason_codes) for r in rs] == [
        ("land_cover", "unknown", ("outside_coverage",)),
        ("tree_cover", "unknown", ("outside_coverage",))]


def test_land_cover_service_errors_raise_source_unavailable():
    xml = '<?xml version="1.0"?><ServiceExceptionReport/>'
    with _client(lambda r: httpx.Response(200, text=xml,
                                          headers={"content-type": "application/xml"})) as c:
        with pytest.raises(SourceUnavailable):
            landcover.read(grid.snap_block(*ZILKER), ZILKER, None, client=c)
    with _client(Replay(status=502)) as c, pytest.raises(SourceUnavailable):
        landcover.read(grid.snap_block(*ZILKER), ZILKER, None, client=c)


def test_the_tiff_reader_matches_the_recorded_pixels():
    e = json.loads((FIXTURES / "zilker_landcover.json").read_text())[4]
    w, h, spp, px, nodata = landcover.read_tiff(base64.b64decode(e["body_b64"]))
    assert (w, h, spp) == (landcover.SIZE, landcover.SIZE, 1)
    assert max(px) <= 100
    with pytest.raises(ValueError):
        landcover.read_tiff(b"GIF89a")


# --- imagery ---------------------------------------------------------------------------

JPEG = b"\xff\xd8\xff\xe0" + b"recorded-size stand-in" + b"\xff\xd9"
#: The capture-date catalog, as it answered for the Arboretum block.
CATALOG = {"features": [{"attributes": {"OBJECTID": 73609, "Year": 2023,
                                        "acquisition_date": 1693526400000}}]}


def _naip(request: httpx.Request) -> httpx.Response:
    q = dict(request.url.params)
    assert q.get("bbox") == "-76.9710,38.9100,-76.9650,38.9150" or q.get("geometry")
    if request.url.path.endswith("/exportImage"):
        assert q["bboxSR"] == "4326" and q["imageSR"] == "3857" and q["format"] == "jpg"
        assert q["size"] == "1195,1280"
        return httpx.Response(200, content=JPEG, headers={"content-type": "image/jpeg"})
    if request.url.path.endswith("/query"):
        assert json.loads(q["geometry"])["xmin"] == -76.971
        return httpx.Response(200, json=CATALOG)
    raise AssertionError(request.url)


def test_imagery_is_fetched_by_block_cached_and_served(session):
    block = grid.snap_block(*ARBORETUM)
    sent = []

    def handler(r):
        sent.append(str(r.url))
        return _naip(r)

    with _client(handler) as c:
        out = imagery.block_imagery(session, block, ARBORETUM, None, client=c)
        assert len(sent) == 1
        assert out.tile_key == "blk1_15565_-25656_naip"
        assert out.image_path == "/imagery/tiles/blk1_15565_-25656_naip.jpg"
        assert (out.width, out.height) == (1195, 1280)
        assert out.bounds.model_dump() == grid.block_box(block)
        assert out.captured is None
        assert "National Agriculture Imagery Program" in out.source.name
        assert out.pin.lat == ARBORETUM[0]
        fp = out.default_footprint
        assert fp.west < ARBORETUM[1] < fp.east and fp.south < ARBORETUM[0] < fp.north
        assert imagery.tile_jpeg(session, out.tile_key) == JPEG
        # The background step finds the capture date; the image is not fetched again.
        assert imagery.read(block, ARBORETUM, None, client=c, session=session) == []
        assert len(sent) == 2 and "/query" in sent[1]
        again = imagery.block_imagery(session, block, ARBORETUM, None, client=c)
        assert again.captured == "2023-09-01" and again.source.version == "2023-09-01"
        assert len(sent) == 2
    _no_pin_in([("GET", u, None) for u in sent], ARBORETUM)


def test_imagery_tiles_serve_only_aerial_images(session):
    assert imagery.tile_jpeg(session, "blk1_15565_-25656_ssurgo") is None
    assert imagery.tile_jpeg(session, "nothing_naip") is None
    assert imagery.tile_jpeg(session, "blk1_15565_-25656_naip") is None


def test_imagery_failure_raises_source_unavailable(session):
    block = grid.snap_block(*ARBORETUM)
    with _client(Replay(status=504)) as c, pytest.raises(SourceUnavailable):
        imagery.block_imagery(session, block, ARBORETUM, None, client=c)
    err = {"error": {"code": 500, "message": "Error exporting image"}}
    with _client(lambda r: httpx.Response(200, json=err)) as c, pytest.raises(SourceUnavailable):
        imagery.block_imagery(session, block, ARBORETUM, None, client=c)


def test_imagery_outside_coverage_has_no_capture_date(session):
    """Where the catalog holds no photography the date stays unknown and a
    failed date lookup is not an error."""
    pin = (51.5, -0.12)
    block = grid.snap_block(*pin)

    def handler(r):
        if r.url.path.endswith("/query"):
            return httpx.Response(200, json={"features": []})
        return httpx.Response(200, content=JPEG)

    with _client(handler) as c:
        imagery.read(block, pin, None, client=c, session=session)
        assert imagery.block_imagery(session, block, pin, None, client=c).captured is None

    def failing_catalog(r):
        if r.url.path.endswith("/query"):
            return httpx.Response(503)
        return httpx.Response(200, content=JPEG)

    other = grid.snap_block(*ZILKER)
    with _client(failing_catalog) as c:
        assert imagery.read(other, ZILKER, None, client=c, session=session) == []


def test_imagery_size_matches_the_block_shape():
    for pin in (ARBORETUM, ZILKER):
        w, h = imagery.image_size(grid.snap_block(*pin))
        assert max(w, h) == imagery.LONG_SIDE_PX
    assert imagery.image_size(grid.snap_block(*ZILKER)) == (1280, 1235)


def test_imagery_routes_answer_with_the_image(iso, monkeypatch):  # noqa: F811
    previous = site_http.use_transport(lambda: httpx.MockTransport(_naip))
    try:
        h = iso.a["headers"]
        r = iso.client.get("/imagery/block", headers=h,
                           params={"lat": ARBORETUM[0], "lng": ARBORETUM[1]})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["image_path"] == "/imagery/tiles/blk1_15565_-25656_naip.jpg"
        assert_explained(body)
        img = iso.client.get(body["image_path"], headers=h)
        assert img.status_code == 200 and img.content == JPEG
        assert img.headers["content-type"] == "image/jpeg"
    finally:
        site_http.use_transport(previous)


from tests.test_scoping import iso  # noqa: E402,F401  (fixture: two users)
