"""Map layers over the aerial image (map and visuals spec, section 3).

The PNG encoder against Pillow, cache-only sources, pixel alignment with
the block, the sun lattice's sanity and its agreement with the reading's
own maths, statuses, expiry, housekeeping, and the warm step. Nothing here
builds an outbound client: the tests that matter patch its constructor to
raise. The measured time and memory of the sun lattice are in the module
docstring of app/services/site/layers.py.
"""
import io
import logging
import math
import struct
from datetime import datetime, timedelta

import numpy as np
import pytest
from PIL import Image
from sqlmodel import Session, create_engine, select

from app.models.models import GeodataTile
from app.models.schemas import MapLayersOut
from app.services import housekeeping as hk
from app.services.site import grid, layers, profile, sun, terrain, tiles
from app.services.site import http as site_http
from app.services.site.sources import canopy as canopy_source
from app.services.site.sources import elevation
from app.services.site.types import Block
from tests.explained_walker import assert_explained
from tests.test_site_terrain import cache_window, window_from

ARBORETUM = (38.9123, -76.9681)
BLOCK = grid.snap_block(*ARBORETUM)


@pytest.fixture(autouse=True)
def _fresh_caches():
    elevation._RECENT.clear()
    elevation._SURVEY_TRIED.clear()
    terrain._ANALYSES.clear()
    yield
    elevation._RECENT.clear()
    terrain._ANALYSES.clear()


@pytest.fixture()
def no_client(monkeypatch):
    """Building an OutboundClient fails the test; nothing may be sent."""
    def refuse(self, *a, **k):
        raise AssertionError("the map layers built an outbound client")
    monkeypatch.setattr(site_http.OutboundClient, "__init__", refuse)
    before = site_http.requests_sent()
    yield
    assert site_http.requests_sent() == before


def decode(png: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(png))
    assert img.format == "PNG" and img.mode == "RGBA"
    return np.asarray(img)


def cache_canopy(session, block, heights, ttl=canopy_source.TTL, now=None):
    h = np.asarray(heights).astype(np.uint8)
    tiles.put(session, canopy_source.PROVIDER, canopy_source.DATASET_VERSION,
              canopy_source.tile_key(block), struct.pack("<HH", *h.shape) + h.tobytes(),
              ttl=ttl, now=now)


def flat(height=10.0, **kw):
    return window_from(lambda e, n: 0 * e + height, **kw)


def small_block(side_px=150):
    """A block-shaped area smaller than a real block, for quick sun maths."""
    w, n = BLOCK.west, BLOCK.north
    return Block(key=BLOCK.key, west=w, south=n - side_px * 1e-5,
                 east=w + side_px * 1e-5, north=n)


def small_window(z, valid=None, resolution_m=1.0):
    b = small_block(z.shape[0])
    return elevation.ElevationWindow(block=b, z=z.astype(np.float32),
                                     valid=np.ones(z.shape, bool) if valid is None else valid,
                                     resolution_m=resolution_m, year=2014)


SEASON = ((4, 1), (10, 31), "april_to_october")


# --- the PNG encoder -----------------------------------------------------------------

@pytest.mark.parametrize("shape", [(1, 1), (3, 7), (100, 120), (500, 600)])
def test_encode_png_decodes_back_to_the_same_pixels(shape):
    rng = np.random.default_rng(7)
    a = rng.integers(0, 256, size=(*shape, 4), dtype=np.uint8)
    back = decode(layers.encode_png(a))
    assert back.shape == (*shape, 4)
    assert (back == a).all()


def test_encode_png_uses_only_zlib_and_struct_and_refuses_bad_shapes():
    import ast
    import inspect
    src = inspect.getsource(layers)
    imported = {n.name for node in ast.walk(ast.parse(src))
                if isinstance(node, ast.Import) for n in node.names}
    assert "PIL" not in src.replace("Pillow", "") and not any("PIL" in i for i in imported)
    for bad in (np.zeros((4, 4, 3), np.uint8), np.zeros((0, 4, 4), np.uint8),
                np.zeros((4, 4), np.uint8)):
        with pytest.raises(ValueError):
            layers.encode_png(bad)


def test_paint_is_transparent_at_step_zero_and_semi_transparent_elsewhere():
    rgba = layers.paint(np.array([[0, 1, 2]]), layers.WATER_COLOURS)
    assert rgba[0, 0, 3] == 0
    assert tuple(rgba[0, 1]) == layers.WATER_COLOURS[0]
    for colours in (layers.SUN_COLOURS, layers.TREE_COLOURS, layers.WATER_COLOURS):
        assert all(100 <= c[3] < 255 for c in colours)


def test_colours_do_not_rely_on_red_against_green():
    """Neighbouring steps differ in lightness, so they are told apart
    without hue, and no colour is a green (it would vanish on lawn)."""
    def lightness(c):
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    for colours in (layers.SUN_COLOURS, layers.TREE_COLOURS, layers.WATER_COLOURS):
        ls = [lightness(c) for c in colours]
        assert all(abs(a - b) >= 25 for a, b in zip(ls, ls[1:])), ls
        assert all(not (c[1] > c[0] + 30 and c[1] > c[2] + 30) for c in colours)
    # The sun ramp runs dark to light: deepest shade darkest.
    sl = [lightness(c) for c in layers.SUN_COLOURS]
    assert sl == sorted(sl)


def test_legends_match_the_colours_drawn():
    for kind, colours in (("sun", layers.SUN_COLOURS), ("trees", layers.TREE_COLOURS),
                          ("water", layers.WATER_COLOURS)):
        leg = layers.legend(kind)
        assert [s["color"] for s in leg] == ["#%02X%02X%02X" % c[:3] for c in colours]
        assert all(s["label"] and "—" not in s["label"] for s in leg)


# --- cache-only sources ------------------------------------------------------------------

def test_cached_sources_have_no_client_and_read_only_the_cache(session, no_client):
    import inspect
    for fn in (layers.cached_window, layers.cached_canopy, layers.layer_png,
               layers.warm, layers.status, layers.layers_for):
        assert "client" not in inspect.signature(fn).parameters
    assert layers.cached_window(session, BLOCK) is None
    assert layers.cached_canopy(session, BLOCK) is None
    win = flat()
    cache_window(session, BLOCK, win)
    h = np.zeros((500, 600))
    h[10, 20] = 17
    cache_canopy(session, BLOCK, h)
    got = layers.cached_window(session, BLOCK)
    assert got.resolution_m == 1.0 and got.year == 2014
    assert np.allclose(got.z, win.z) and got.valid.all()
    assert layers.cached_window(session, BLOCK) is got       # memoised
    cg = layers.cached_canopy(session, BLOCK)
    assert cg.height_m.shape == (500, 600) and cg.height_m[10, 20] == 17


def test_the_survey_details_are_optional(session):
    win = flat()
    tiles.put(session, elevation.PROVIDER, elevation.DATASET_VERSION,
              elevation.tile_key(BLOCK),
              elevation.encode_window(win.z, win.valid, {"fetched_by": "block"}))
    got = layers.cached_window(session, BLOCK)
    assert got is not None and got.resolution_m is None
    assert elevation._SURVEY_TRIED == {}     # no survey request was attempted


# --- alignment ------------------------------------------------------------------------------

def test_one_tall_canopy_cell_lands_on_its_own_trees_pixel(session, no_client):
    lat, lng = 38.9131, -76.9702
    win = flat()
    r, c = (int(v) for v in win.to_pixel(lat, lng))
    h = np.zeros((500, 600))
    h[r, c] = 25
    cache_canopy(session, BLOCK, h)
    img = decode(layers.layer_png(session, BLOCK, "trees"))
    assert img.shape == (500, 600, 4)
    assert (layers.size("trees")) == (600, 500)
    assert tuple(img[r, c]) == layers.TREE_COLOURS[3]
    others = img[..., 3].copy()
    others[r, c] = 0
    assert others.max() == 0
    # The same spot on the aerial image, which covers exactly the block.
    x = (c + 0.5) / 600
    y = (r + 0.5) / 500
    assert abs(BLOCK.west + x * (BLOCK.east - BLOCK.west) - lng) < 1e-5
    assert abs(BLOCK.north - y * (BLOCK.north - BLOCK.south) - lat) < 1e-5


def test_one_pit_lands_on_its_own_water_pixel(session, no_client):
    win = window_from(lambda e, n: 10 + 0.01 * n)     # gently down to the south
    r, c = 321, 123
    win.z[r, c] -= 0.5
    cache_window(session, BLOCK, win)
    img = decode(layers.layer_png(session, BLOCK, "water"))
    assert img.shape == (500, 600, 4)
    assert tuple(img[r, c]) == layers.WATER_COLOURS[1]           # collects here
    collects = (img[..., :3] == layers.WATER_COLOURS[1][:3]).all(axis=2) & (img[..., 3] > 0)
    assert collects.sum() == 1


def test_a_tall_canopy_block_lands_on_its_sun_squares(session, no_client):
    win = flat()
    cache_window(session, BLOCK, win)
    h = np.zeros((500, 600))
    h[200:220, 300:320] = 20                      # squares rows 40-43, cols 60-63
    cache_canopy(session, BLOCK, h)
    img = decode(layers.layer_png(session, BLOCK, "sun"))
    assert img.shape == (100, 120, 4) and layers.size("sun") == (120, 100)
    for rr in range(40, 44):
        for cc in range(60, 64):
            assert tuple(img[rr, cc]) == layers.SUN_COLOURS[0]
    assert tuple(img[39, 61]) != layers.SUN_COLOURS[0]
    assert tuple(img[44, 61]) != layers.SUN_COLOURS[0]


# --- the sun lattice ------------------------------------------------------------------------

def test_flat_open_ground_reads_full_sun_everywhere():
    win = small_window(np.full((150, 150), 10.0))
    hours, under = layers.sun_grid(win, None, SEASON)
    assert hours.shape == (30, 30) and not under.any()
    # About 13.3 hours of daylight a day, April to October at 39 degrees north.
    assert np.nanmin(hours) == pytest.approx(13.3, abs=0.3)
    steps = layers.sun_steps(hours, under)
    assert (steps == len(layers.SUN_COLOURS)).all()


def _tree_block():
    h = np.zeros((150, 150), np.float32)
    h[60:90, 60:90] = 20.0
    return h


def test_north_of_a_tall_canopy_block_gets_less_sun_than_south_of_it():
    win = small_window(np.full((150, 150), 10.0))
    cg = canopy_source.CanopyGrid(block=win.block, height_m=_tree_block(), resolution_m=1.0)
    hours, under = layers.sun_grid(win, cg, SEASON)
    # Squares 12 and 18 hold rows 60-64 and 90-94: the block's first and
    # last rows. Just north is square 11, just south square 18.
    north, south = hours[11, 15], hours[18, 15]
    assert north < south - 2.0, (north, south)
    assert under[12:18, 12:18].all() and not under[11, 15] and not under[18, 15]
    steps = layers.sun_steps(hours, under)
    assert (steps[12:18, 12:18] == 1).all()                   # the deepest step
    assert steps.min() == 1 and (steps[~under] >= 2).all()


def test_the_lattice_counts_exactly_what_direct_hours_counts():
    rng = np.random.default_rng(3)
    z = 10 + rng.normal(0, 0.5, (150, 150)).cumsum(axis=0) * 0.05
    win = small_window(z)
    h = np.where(rng.random((150, 150)) > 0.97, 15.0, 0.0).astype(np.float32)
    cg = canopy_source.CanopyGrid(block=win.block, height_m=h, resolution_m=1.0)
    days = sun.season_days(*SEASON[:2])
    lat, lng = layers.block_centre(win.block)
    elev, azim, step_h = sun.season_sun(days, lat, lng)
    pts = np.array([[2, 2], [77, 52], [102, 147], [147, 7]])
    surface = win.z + np.where(h >= sun.OBSTACLE_MIN_M, h, 0)
    hz = sun.horizons(surface, pts, win.dx_m, win.dy_m, base=win.z)
    want = sun.direct_hours(elev, azim, hz, step_h, len(days))
    got = layers.lit_steps(layers._bins(elev, azim, sun.AZIMUTHS), hz) * step_h / len(days)
    assert np.allclose(got, want)
    hours, under = layers.sun_grid(win, cg, SEASON)
    for (r, c), w in zip(pts, want):
        if not under[r // 5, c // 5] and r % 5 == 2 and c % 5 == 2:
            assert hours[r // 5, c // 5] == pytest.approx(w, abs=1e-4)


def test_unknown_ground_is_transparent_on_the_sun_layer():
    valid = np.ones((150, 150), bool)
    valid[:50] = False
    win = small_window(np.full((150, 150), 10.0), valid=valid)
    hours, under = layers.sun_grid(win, None, SEASON)
    assert np.isnan(hours[:10]).all() and np.isfinite(hours[10:]).all()
    assert (layers.paint(layers.sun_steps(hours, under), layers.SUN_COLOURS)[:10, ..., 3]
            == 0).all()


def test_the_season_is_worked_out_at_the_block_centre(monkeypatch):
    seen = []
    monkeypatch.setattr(sun, "_normals", lambda pin: seen.append(pin) or None)
    assert layers.season_for(BLOCK)[2] == "april_to_october"
    assert seen == [layers.block_centre(BLOCK)]


# --- statuses ---------------------------------------------------------------------------------

def test_statuses_follow_the_cached_sources(session, no_client):
    st = {k: layers.status(session, BLOCK, k) for k in layers.KINDS}
    assert st == {k: ("not_ready", layers.NOT_READY_TEXT) for k in layers.KINDS}
    cache_canopy(session, BLOCK, np.zeros((500, 600)))
    assert layers.status(session, BLOCK, "trees") == ("ready", None)
    assert layers.status(session, BLOCK, "sun")[0] == "not_ready"
    cache_window(session, BLOCK, flat(resolution_m=10.0))
    assert layers.status(session, BLOCK, "sun") == ("ready", None)
    assert layers.status(session, BLOCK, "water") == ("unavailable", layers.COARSE_TEXT)
    with pytest.raises(layers.LayerNotReady) as exc:
        layers.layer_png(session, BLOCK, "water")
    assert exc.value.status == "unavailable"
    assert layers.status(session, BLOCK, "sun", in_us=False) == \
        ("unavailable", layers.OUTSIDE_US_TEXT)
    with pytest.raises(KeyError):
        layers.layer_png(session, BLOCK, "roads")


def test_an_expired_partial_survey_is_not_ready_not_too_coarse(session, no_client):
    # A partial survey record (resolution, no year) lives a day; the window
    # lives 90. Once the record has gone the resolution is unknown, which is
    # "not read yet", not "too coarse".
    t0 = datetime(2026, 11, 16, 12, 0)
    win = flat()
    tiles.put(session, elevation.PROVIDER, elevation.DATASET_VERSION,
              elevation.tile_key(BLOCK),
              elevation.encode_window(win.z, win.valid, {"fetched_by": "block"}),
              ttl=elevation.TTL, now=t0)
    tiles.put_json(session, elevation.PROVIDER, elevation.DATASET_VERSION,
                   elevation.survey_key(BLOCK), {"resolution_m": 1.0},
                   ttl=elevation.TTL_PARTIAL, now=t0)
    assert layers.status(session, BLOCK, "water", now=t0) == ("ready", None)
    later = t0 + timedelta(days=2)
    assert layers.status(session, BLOCK, "water", now=later) == \
        ("not_ready", layers.NOT_READY_TEXT)
    with pytest.raises(layers.LayerNotReady) as exc:
        layers.layer_png(session, BLOCK, "water", now=later)
    assert exc.value.status == "not_ready"
    # A survey record that says the ground is coarse is still unavailable.
    tiles.put_json(session, elevation.PROVIDER, elevation.DATASET_VERSION,
                   elevation.survey_key(BLOCK), {"resolution_m": 10.0},
                   ttl=elevation.TTL_PARTIAL, now=later)
    assert layers.status(session, BLOCK, "water", now=later) == \
        ("unavailable", layers.COARSE_TEXT)


def test_not_ready_promises_minutes_only_while_the_profile_is_preparing(session, no_client):
    for kind in layers.KINDS:
        assert layers.status(session, BLOCK, kind, preparing=True) == \
            ("not_ready", layers.NOT_READY_TEXT)
        st, text = layers.status(session, BLOCK, kind, preparing=False)
        assert st == "not_ready" and text == layers.READ_AGAIN_TEXT
        assert "minutes" not in text and "Read the public maps again" in text
        assert "\u2014" not in text
    body = layers.layers_for(session, BLOCK, in_us=True, property_id=1, preparing=False)
    assert {l["status_text"] for l in body["layers"]} == {layers.READ_AGAIN_TEXT}


def test_a_window_with_too_little_ground_is_unavailable(session):
    win = flat()
    valid = np.zeros((500, 600), bool)
    valid[:100] = True
    tiles.put(session, elevation.PROVIDER, elevation.DATASET_VERSION,
              elevation.tile_key(BLOCK), elevation.encode_window(win.z, valid, {}))
    tiles.put_json(session, elevation.PROVIDER, elevation.DATASET_VERSION,
                   elevation.survey_key(BLOCK), {"resolution_m": 1.0, "year": 2014})
    cache_canopy(session, BLOCK, np.zeros((500, 600)))
    assert layers.status(session, BLOCK, "sun") == ("unavailable", layers.NO_GROUND_TEXT)
    assert layers.status(session, BLOCK, "water") == ("unavailable", layers.NO_GROUND_TEXT)


def test_the_answer_has_every_layer_in_order_with_its_reason(session, no_client):
    cache_canopy(session, BLOCK, np.zeros((500, 600)))
    out = layers.layers_for(session, BLOCK, in_us=True, property_id=7)
    MapLayersOut.model_validate(out)
    assert_explained(out)
    assert [l["kind"] for l in out["layers"]] == ["sun", "trees", "water"]
    by = {l["kind"]: l for l in out["layers"]}
    assert by["trees"]["status"] == "ready"
    assert by["trees"]["image_path"] == "/properties/7/layers/trees.png"
    assert by["sun"]["image_path"] is None and by["sun"]["status_text"]
    assert by["sun"]["explained"]["confidence"] == "rough_estimate"
    assert by["water"]["explained"]["confidence"] == "rough_estimate"
    assert by["trees"]["explained"]["confidence"] == "area_estimate"
    assert "Buildings are not counted." in by["sun"]["notes"]
    assert any("edge of the map" in n for n in by["sun"]["notes"])
    assert any("Soil is not drawn" in n for n in by["water"]["notes"])
    assert any("no trees or no data" in n for n in by["trees"]["notes"])
    assert out["bounds"] == grid.block_box(BLOCK)
    text = repr(out)
    assert "—" not in text and " AI " not in text


# --- the cache and its expiry -----------------------------------------------------------------

def _row(session, kind):
    return session.exec(select(GeodataTile).where(
        GeodataTile.provider == layers.PROVIDER,
        GeodataTile.tile_key == layers.layer_key(BLOCK, kind))).first()


def test_layers_expire_no_later_than_their_sources(session, no_client):
    now = datetime(2026, 11, 16, 12, 0)
    cache_window(session, BLOCK, flat())     # 90 days (tiles default)
    tiles.put_json(session, elevation.PROVIDER, elevation.DATASET_VERSION,
                   elevation.survey_key(BLOCK), {"resolution_m": 1.0, "year": 2014},
                   ttl=timedelta(days=1), now=now)
    cache_canopy(session, BLOCK, np.zeros((500, 600)), ttl=timedelta(days=365), now=now)
    got = layers.warm(session, BLOCK, now=now)
    assert got == {"sun": "ready", "trees": "ready", "water": "ready"}

    def expiry(provider, version, key):
        return session.exec(select(GeodataTile.expires_at).where(
            GeodataTile.provider == provider, GeodataTile.dataset_version == version,
            GeodataTile.tile_key == key)).first()
    dem = expiry(elevation.PROVIDER, elevation.DATASET_VERSION, elevation.tile_key(BLOCK))
    survey = expiry(elevation.PROVIDER, elevation.DATASET_VERSION, elevation.survey_key(BLOCK))
    chm = expiry(canopy_source.PROVIDER, canopy_source.DATASET_VERSION,
                 canopy_source.tile_key(BLOCK))
    assert _row(session, "trees").expires_at <= chm
    assert _row(session, "sun").expires_at <= min(dem, chm)
    assert _row(session, "water").expires_at <= min(dem, survey)
    assert _row(session, "water").expires_at == survey
    assert _row(session, "trees").dataset_version == "v1"
    assert _row(session, "trees").tile_key == f"{BLOCK.key}_lyr_trees"


def test_a_cached_layer_is_read_back_and_redrawn_when_a_source_is_newer(session, no_client):
    now = datetime(2026, 11, 16, 12, 0)
    h = np.zeros((500, 600))
    cache_canopy(session, BLOCK, h, now=now)
    first = layers.layer_png(session, BLOCK, "trees", now=now)
    stored_at = _row(session, "trees").fetched_at
    again = layers.layer_png(session, BLOCK, "trees", now=now + timedelta(minutes=5))
    assert again == first and _row(session, "trees").fetched_at == stored_at
    h[0, 0] = 30
    cache_canopy(session, BLOCK, h, now=now + timedelta(hours=1))
    redrawn = layers.layer_png(session, BLOCK, "trees", now=now + timedelta(hours=2))
    assert redrawn != first and decode(redrawn)[0, 0, 3] > 0
    # Once its source has expired, a picture is not served either.
    later = now + timedelta(days=400)
    assert layers.status(session, BLOCK, "trees", now=later)[0] == "not_ready"
    with pytest.raises(layers.LayerNotReady):
        layers.layer_png(session, BLOCK, "trees", now=later)


def test_housekeeping_prunes_layer_tiles_with_the_block(migrated_db_url):
    engine = create_engine(migrated_db_url, connect_args={"check_same_thread": False})
    # A block no property maps to (the middle of the Gulf of Maine).
    lonely = grid.snap_block(43.0, -68.0)
    try:
        with Session(engine) as s:
            cache_canopy(s, lonely, np.zeros((500, 600)))
            layers.layer_png(s, lonely, "trees")
            s.commit()
            assert s.exec(select(GeodataTile).where(
                GeodataTile.provider == layers.PROVIDER,
                GeodataTile.tile_key == f"{lonely.key}_lyr_trees")).first() is not None
        hk.prune_unused_tiles(lambda: Session(engine), datetime.utcnow())
        with Session(engine) as s:
            assert s.exec(select(GeodataTile).where(
                GeodataTile.tile_key.startswith(lonely.key))).all() == []
        # And an expired layer goes with the expired tiles.
        with Session(engine) as s:
            tiles.put(s, layers.PROVIDER, layers.DATASET_VERSION, f"{lonely.key}_lyr_sun",
                      b"x", ttl=timedelta(seconds=1), now=datetime(2020, 1, 1))
            s.commit()
        assert hk.prune_expired_tiles(lambda: Session(engine), datetime.utcnow()) >= 1
        with Session(engine) as s:
            assert s.exec(select(GeodataTile).where(
                GeodataTile.tile_key.startswith(lonely.key))).all() == []
    finally:
        with Session(engine) as s:
            for row in s.exec(select(GeodataTile).where(
                    GeodataTile.tile_key.startswith(lonely.key))).all():
                s.delete(row)
            s.commit()
        engine.dispose()


# --- the warm step ------------------------------------------------------------------------------

def test_warm_draws_what_it_can_and_never_raises(session, no_client, monkeypatch, caplog):
    assert layers.warm(session, BLOCK) == {k: "not_ready" for k in layers.KINDS}
    cache_canopy(session, BLOCK, np.zeros((500, 600)))
    assert layers.warm(session, BLOCK)["trees"] == "ready"
    assert _row(session, "trees") is not None

    def broken(*a, **k):
        raise RuntimeError("drawing failed")
    monkeypatch.setattr(layers, "draw", broken)
    tiles.put(session, canopy_source.PROVIDER, canopy_source.DATASET_VERSION,
              canopy_source.tile_key(BLOCK), struct.pack("<HH", 500, 600) + bytes(300000),
              now=datetime.utcnow() + timedelta(hours=1))   # newer than the picture
    with caplog.at_level(logging.WARNING, logger="plantadvocate.site_layers"):
        assert layers.warm(session, BLOCK, property_id=7)["trees"] == "failed"
    # The log names the property, never the block (its key locates the land).
    logged = [r.getMessage() for r in caplog.records]
    assert any("property 7" in m for m in logged)
    assert not any(BLOCK.key in m for m in logged)


def test_a_layer_that_cannot_be_stored_logs_no_block_key(session, no_client, monkeypatch,
                                                         caplog):
    cache_canopy(session, BLOCK, np.zeros((500, 600)))

    def full(*a, **k):
        raise RuntimeError("disk full")
    monkeypatch.setattr(layers.tiles, "put", full)
    with caplog.at_level(logging.WARNING, logger="plantadvocate.site_layers"):
        assert layers.layer_png(session, BLOCK, "trees", property_id=7)
    logged = [r.getMessage() for r in caplog.records]
    assert any("property 7" in m for m in logged)
    assert not any(BLOCK.key in m for m in logged)


def test_the_profile_step_warms_the_layers_without_a_client(session, monkeypatch, no_client):
    calls = []
    monkeypatch.setattr(layers, "warm",
                        lambda s, b, **k: calls.append((b.key, k.get("property_id"))))
    profile._warm_layers(session, BLOCK, 1)
    assert calls == [(BLOCK.key, 1)]

    def broken(s, b, **k):
        raise RuntimeError("no")
    monkeypatch.setattr(layers, "warm", broken)
    profile._warm_layers(session, BLOCK, 1)           # logged, never raised


class _Caching:
    """A background source that caches a grid the way the real one does,
    sends nothing, and gives no reading."""

    def __init__(self, put):
        self.put = put

    def read(self, block, pin, footprint, *, client, session=None):
        self.put(session, block)
        return []


def test_the_background_step_leaves_every_layer_drawn(iso, monkeypatch):  # noqa: F811
    from app.routers import properties
    from tests.test_site_profile import Fake, rd
    monkeypatch.setattr(properties, "queue_background", lambda background, pid: None)
    monkeypatch.setattr(profile, "SESSION_FACTORY", iso.db)
    r = iso.client.post("/properties", headers=iso.a["headers"], json={
        "pin_lat": ARBORETUM[0], "pin_lng": ARBORETUM[1], "pin_source": "owner_pin"})
    pid = r.json()["id"]
    h = np.zeros((500, 600))
    h[100:130, 100:130] = 18
    stubs = {
        "hardiness": Fake([rd("hardiness_zone", "7b", "high", "phzm2023")]),
        "soil": Fake([]),
        "elevation": _Caching(lambda s, b: cache_window(s, b, flat())),
        "canopy": _Caching(lambda s, b: cache_canopy(s, b, h)),
        "landcover": Fake([]), "terrain": Fake([]), "sun": Fake([]),
        "drainage": Fake([]), "imagery": None,
    }
    before = site_http.requests_sent()
    try:
        with profile.use_sources(stubs):
            profile.build_background(pid)
        assert site_http.requests_sent() == before
        with iso.db() as s:
            keys = {row.tile_key for row in s.exec(select(GeodataTile).where(
                GeodataTile.provider == layers.PROVIDER)).all()}
            assert {f"{BLOCK.key}_lyr_{k}" for k in layers.KINDS} <= keys
        # A failure to draw never fails the profile.
        monkeypatch.setattr(layers, "warm", lambda *a, **k: 1 / 0)
        with profile.use_sources(stubs):
            profile.build_background(pid)
        with iso.db() as s:
            from app.models.models import Property
            assert s.get(Property, pid).profile_status["background"] != "failed"
    finally:
        with iso.db() as s:
            for row in s.exec(select(GeodataTile).where(
                    GeodataTile.tile_key.startswith(BLOCK.key))).all():
                s.delete(row)
            s.commit()


from tests.test_scoping import iso  # noqa: E402,F401  (fixture)
