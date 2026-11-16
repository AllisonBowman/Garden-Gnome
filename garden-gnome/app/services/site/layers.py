"""Map layers drawn over the aerial image (map and visuals spec, section 3).

Three pictures of one block, each a semi-transparent PNG that lines up with
the aerial image when stretched over the same bounds (the whole block):

    sun     average hours of direct sun a day in the growing season, on a
            5 by 5 pixel lattice (about 5.6 metres north to south and 4.3 to
            4.8 metres east to west), 120 by 100 squares
    trees   tree canopy height, on the 0.00001 degree lattice, 600 by 500
    water   where water collects (filled depth of 10 centimetres or more)
            and where runoff runs through (2,000 square metres or more
            uphill), on the 0.00001 degree lattice, 600 by 500

No outside requests, ever. Everything is drawn from the copies the server
already holds in `geodata_tile` (the elevation window and the canopy grid):
`cached_window` and `cached_canopy` read with `tiles.get` / `tiles.get_json`
and decode, and there is no client parameter anywhere in this module. A
cache miss means "not ready", never a fetch.

Drawn PNGs are cached in `geodata_tile` too (provider `site_layers`, version
`v1`, key `{block.key}_lyr_{kind}`), expiring no later than the earliest
expiry of the source tiles used, and redrawn when a source tile is newer
than the picture. Their keys start with the block key, so housekeeping
prunes them with the block's other tiles.

The sun lattice. `sun.horizons` is called on chunks of 2,000 points, and
`sun.direct_hours`'s (points x sun steps) gather is replaced by one sorted
list of sun elevations per 5 degree azimuth bin and `searchsorted`, so
memory stays at (chunk x distances) and (points x 72). The season and the
sun's path are worked out at the block centre, so the layer is the same for
every property in the block. A square whose 25 pixels are mostly under
canopy of 2 metres or more is counted as shade while leaves are out (as
`sun.estimate` does for one point); every other square is worked out at its
centre pixel.

Measured on 2026-11-16 on the development laptop (Python 3.14, numpy
2.5), with tracemalloc for memory and perf_counter for time, on a realistic
(500, 600) window: the recorded Arboretum crop (tests/fixtures/site_terrain)
mirrored out to the whole block, with its canopy (12,000 squares, 4,831 of
them mostly under canopy and so skipped), over the default season of April
to October (31 days sampled):

    sun_grid                0.93 s wall, 21.7 MB peak traced memory
    worst case: no square under canopy, a long season (15 February to
    10 December, 43 days)   1.49 s wall, 20.5 MB peak
    water_classes           0.36 s (the terrain analysis; memoised per window)
    encode_png              under 35 ms for each 600 by 500 picture; the
                            PNGs are about 2 kB (sun), 7 kB (water) and
                            16 kB (trees)

The 512 MB machine is a shared virtual processor, slower than the laptop,
so expect a few seconds there; the memory budget (80 MB) holds with room to
spare. What the stride costs in accuracy: one value per 5 by 5 pixel
square, so a shadow's edge is placed to within about 3 metres, and a square
is "under canopy" by majority. The horizon walk (1 metre steps to 60
metres, then 2 metre steps to 250 metres, 72 directions) and the sun path
(every 10 minutes on every 7th day) are not coarsened: they are the same as
the sun reading's.
"""
from __future__ import annotations

import json
import logging
import math
import struct
import zlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from sqlmodel import Session, select

from app.models.models import GeodataTile
from app.services.site import copy as words
from app.services.site import grid, sun, terrain, tiles
from app.services.site.sources import canopy as canopy_source
from app.services.site.sources import elevation
from app.services.site.types import Block

logger = logging.getLogger("plantadvocate.site_layers")

PROVIDER = "site_layers"
DATASET_VERSION = "v1"
KINDS: tuple[str, ...] = ("sun", "trees", "water")
TITLES = {"sun": "Sun", "trees": "Trees", "water": "Water"}

#: Pixels of the 0.00001 degree lattice per sun square, on each axis.
SUN_STRIDE_PX = 5
#: Points per `sun.horizons` call (memory is about 7 arrays of chunk x 155).
SUN_CHUNK = 2000
#: A sun square at least this much under canopy of 2 m or more is shade.
UNDER_CANOPY_SHARE = 0.5
#: Hours a day that start each sun step above the deepest ones.
SUN_STEPS_HOURS = (3.0, 6.0, 9.0)
#: Canopy heights (metres) that start each trees step.
TREE_STEPS_M = (canopy_source.CANOPY_MIN_M, 5.0, 10.0, 20.0)

#: The layer colours: RGBA. They are chosen to read on an aerial photograph
#: (mostly greens, browns and greys) and to be told apart by lightness and
#: by the blue to yellow axis, never by red against green. Every colour is
#: semi-transparent so the photograph shows through.
SUN_COLOURS = (
    (27, 12, 65, 200),      # under tree canopy: deepest shade
    (106, 23, 110, 175),    # under 3 hours
    (187, 55, 84, 160),     # 3 to 6 hours
    (249, 140, 10, 150),    # 6 to 9 hours
    (252, 240, 120, 140),   # 9 hours or more
)
SUN_LABELS = ("Under tree canopy, shade while leaves are out",
              "Under 3 hours, shade",
              "3 to 6 hours, part shade",
              "6 to 9 hours, full sun",
              "9 hours or more, full sun")
TREE_COLOURS = (
    (250, 205, 240, 150),   # 2 to 5 m
    (230, 120, 220, 165),   # 5 to 10 m
    (165, 50, 190, 180),    # 10 to 20 m
    (80, 20, 120, 195),     # 20 m or more
)
TREE_LABELS = ("2 to 5 metres tall", "5 to 10 metres tall", "10 to 20 metres tall",
               "20 metres or more")
WATER_COLOURS = (
    (0, 230, 255, 190),     # runs through
    (25, 70, 255, 210),     # collects
)
WATER_LABELS = ("Water runs through here after rain", "Water collects here after rain")

NOT_READY_TEXT = "The map is still being prepared. Check back in a few minutes."
#: Not ready while nothing is preparing it (the source copies ran out and
#: the background step is not running): only reading the maps again helps.
READ_AGAIN_TEXT = ("The map data for your land needs to be read again. On Your land, "
                   "tap Read the public maps again.")
OUTSIDE_US_TEXT = "Map layers are only available for land in the United States."
NO_GROUND_TEXT = "There is no elevation survey for this spot, so this layer cannot be drawn."
COARSE_TEXT = ("The elevation survey here is not detailed enough to show where water "
               "collects.")
NOTES = {
    "sun": ["Buildings are not counted.",
            "Near the edge of the map the sun reads high, because land beyond the map "
            "is not counted.",
            "This is for the growing season, when leaves are out."],
    "trees": ["A height of 0 can mean no trees or no data.",
              "Canopy under 2 metres (lawn and low shrubs) is not drawn."],
    "water": ["Soil is not drawn on this map. The Where water collects reading counts it.",
              "This is not a flood insurance determination."],
}


# --- cache-only sources ------------------------------------------------------------

def cached_window(session: Session, block: Block, *,
                  now: Optional[datetime] = None) -> Optional[elevation.ElevationWindow]:
    """The block's elevation window from the tile cache, or None. Never
    fetches: the survey details are read from the cache too (missing ones
    leave the resolution unknown). Shares `elevation`'s small memo, so the
    window the profile step just used (and its terrain analysis) is reused."""
    payload = tiles.get(session, elevation.PROVIDER, elevation.DATASET_VERSION,
                        elevation.tile_key(block), now=now)
    if payload is None:
        return None
    survey = tiles.get_json(session, elevation.PROVIDER, elevation.DATASET_VERSION,
                            elevation.survey_key(block), now=now) or {}
    key = (block.key, hash(payload), json.dumps(survey, sort_keys=True))
    hit = elevation._RECENT.get(key)
    if hit is not None:
        return hit
    try:
        z, valid, head = elevation.decode_window(payload)
    except (ValueError, KeyError, struct.error):
        return None
    win = elevation._window(block, z, valid, {**head, **survey})
    if len(elevation._RECENT) >= elevation._RECENT_MAX:
        elevation._RECENT.pop(next(iter(elevation._RECENT)))
    elevation._RECENT[key] = win
    return win


def cached_canopy(session: Session, block: Block, *,
                  now: Optional[datetime] = None) -> Optional[canopy_source.CanopyGrid]:
    """The block's canopy grid from the tile cache, or None. Never fetches.
    Decodes the cached form `canopy.load_canopy` writes."""
    payload = tiles.get(session, canopy_source.PROVIDER, canopy_source.DATASET_VERSION,
                        canopy_source.tile_key(block), now=now)
    if payload is None or len(payload) < 4:
        return None
    rows, cols = struct.unpack("<HH", payload[:4])
    if len(payload) < 4 + rows * cols:
        return None
    h = np.frombuffer(payload[4:4 + rows * cols], dtype=np.uint8).reshape(rows, cols)
    mid = (block.south + block.north) / 2
    return canopy_source.CanopyGrid(
        block=block, height_m=h.astype(np.float32),
        resolution_m=float(max(1, round(canopy_source.ground_resolution_m(mid)))))


#: The source tiles each layer is drawn from: name -> (provider, version, key).
def _source_keys(block: Block) -> dict[str, tuple[str, str, str]]:
    return {
        "dem": (elevation.PROVIDER, elevation.DATASET_VERSION, elevation.tile_key(block)),
        "survey": (elevation.PROVIDER, elevation.DATASET_VERSION, elevation.survey_key(block)),
        "chm": (canopy_source.PROVIDER, canopy_source.DATASET_VERSION,
                canopy_source.tile_key(block)),
    }


USES: dict[str, tuple[str, ...]] = {
    "sun": ("dem", "chm"),
    "trees": ("chm",),
    "water": ("dem", "survey"),
}


@dataclass(frozen=True)
class TileMeta:
    fetched_at: Optional[datetime]
    expires_at: Optional[datetime]


def _meta(session: Session, provider: str, version: str, key: str,
          now: datetime) -> Optional[TileMeta]:
    """When a live tile was stored and when it expires, without reading its
    payload. None when it is missing or expired."""
    row = session.exec(
        select(GeodataTile.fetched_at, GeodataTile.expires_at)
        .where(GeodataTile.provider == provider)
        .where(GeodataTile.dataset_version == version)
        .where(GeodataTile.tile_key == key)).first()
    if row is None:
        return None
    fetched, expires = row
    if expires is not None and expires <= now:
        return None
    return TileMeta(fetched, expires)


def layer_key(block: Block, kind: str) -> str:
    return f"{block.key}_lyr_{kind}"


# --- the sun lattice ----------------------------------------------------------------

def season_for(block: Block) -> tuple[tuple[int, int], tuple[int, int], str]:
    """The growing season at the block centre (typical frost-free period,
    else April to October). Reads a local file; no outside request."""
    lat, lng = block_centre(block)
    return sun.season_from_normals(sun._normals((lat, lng)))


def block_centre(block: Block) -> tuple[float, float]:
    return (block.south + block.north) / 2, (block.west + block.east) / 2


def _bins(elev: np.ndarray, azim: np.ndarray, n_az: int) -> list[np.ndarray]:
    """The sun's elevations above the horizon, sorted, per azimuth bin (the
    same binning as `sun.direct_hours`)."""
    up = elev > 0
    idx = np.rint(azim[up] / (360.0 / n_az)).astype(np.int64) % n_az
    e = elev[up]
    return [np.sort(e[idx == k]) for k in range(n_az)]


def lit_steps(bins: list[np.ndarray], horizon: np.ndarray) -> np.ndarray:
    """Per point, the sun steps with the sun above the horizon in its own
    direction: equal to `sun.direct_hours`'s count, without its
    (points x steps) gather."""
    out = np.zeros(horizon.shape[0], dtype=np.int64)
    for k, e in enumerate(bins):
        if e.size:
            out += e.size - np.searchsorted(e, horizon[:, k], side="right")
    return out


def sun_grid(win: elevation.ElevationWindow, canopy: Optional[canopy_source.CanopyGrid],
             season: Optional[tuple] = None, *, stride: int = SUN_STRIDE_PX,
             year: int = 2026, chunk: int = SUN_CHUNK) -> tuple[np.ndarray, np.ndarray]:
    """(hours, under): average hours of direct sun a day in the growing
    season, one value per `stride` by `stride` square of the window (north
    row first), NaN where the ground is not known; and which squares are
    mostly under canopy of 2 metres or more (they read 0 hours: shade while
    leaves are out). Ground is the window; obstacles are canopy of 1 metre
    or more. Buildings are not counted."""
    season = season or season_for(win.block)
    start, end, _ = season
    days = sun.season_days(start, end, year)
    lat, lng = block_centre(win.block)
    elev, azim, step_h = sun.season_sun(days, lat, lng)
    bins = _bins(elev, azim, sun.AZIMUTHS)
    del elev, azim

    rows, cols = win.z.shape
    nr, nc = rows // stride, cols // stride
    ground = win.z.astype(np.float32)
    if canopy is not None and canopy.height_m.shape == ground.shape:
        heights = canopy.height_m.astype(np.float32)
        obstacles = np.where(heights >= sun.OBSTACLE_MIN_M, heights, np.float32(0))
        surface = ground + obstacles
        tall = (heights[:nr * stride, :nc * stride] >= canopy_source.CANOPY_MIN_M)
        under = tall.reshape(nr, stride, nc, stride).mean(axis=(1, 3)) >= UNDER_CANOPY_SHARE
        del heights, obstacles, tall
    else:
        surface = ground
        under = np.zeros((nr, nc), bool)

    rr = np.arange(nr) * stride + stride // 2
    cc = np.arange(nc) * stride + stride // 2
    R, C = np.meshgrid(rr, cc, indexing="ij")
    ok = win.valid[R, C]
    out = np.full((nr, nc), np.nan, dtype=np.float32)
    out[ok & under] = 0.0
    todo = ok & ~under
    pts = np.stack([R[todo], C[todo]], axis=1).astype(np.int64)
    hours = np.empty(pts.shape[0], dtype=np.float32)
    per_step = step_h / max(len(days), 1)
    for s in range(0, pts.shape[0], chunk):
        part = pts[s:s + chunk]
        hz = sun.horizons(surface, part, win.dx_m, win.dy_m, base=ground)
        hours[s:s + chunk] = lit_steps(bins, hz) * per_step
    out[todo] = hours
    return out, ok & under


# --- trees and water ----------------------------------------------------------------

def water_classes(win: elevation.ElevationWindow) -> np.ndarray:
    """0 nothing, 1 water runs through here, 2 water collects here, per
    pixel of the window. Collecting wins where both hold."""
    a = terrain.analyse_window(win)
    out = np.zeros(win.z.shape, dtype=np.uint8)
    out[a.accumulation_m2 >= terrain.FLOW_CATCHMENT_M2] = 1
    out[a.depth >= terrain.LOW_SPOT_DEPTH_M] = 2
    out[~win.valid] = 0
    return out


def water_available(win: elevation.ElevationWindow) -> Optional[str]:
    """None when the water layer can be drawn from this window, else why not."""
    if win.coverage() < 0.5:
        return NO_GROUND_TEXT
    if win.resolution_m is None or win.resolution_m > terrain.WATER_MAX_RESOLUTION_M:
        return COARSE_TEXT
    return None


# --- colour and PNG -------------------------------------------------------------------

def paint(steps: np.ndarray, colours) -> np.ndarray:
    """RGBA from step numbers: 0 is transparent, n is colours[n - 1]."""
    lut = np.zeros((len(colours) + 1, 4), dtype=np.uint8)
    lut[1:] = np.asarray(colours, dtype=np.uint8)
    return lut[np.clip(steps, 0, len(colours)).astype(np.int64)]


def sun_steps(hours: np.ndarray, under: np.ndarray) -> np.ndarray:
    """Step numbers for the sun ramp: 0 no data, 1 under canopy, then one
    step per band of SUN_STEPS_HOURS."""
    steps = np.zeros(hours.shape, dtype=np.uint8)
    known = np.isfinite(hours)
    steps[known] = 2 + np.digitize(hours[known], SUN_STEPS_HOURS).astype(np.uint8)
    steps[known & under] = 1
    return steps


def tree_steps(heights: np.ndarray) -> np.ndarray:
    return np.digitize(heights, TREE_STEPS_M).astype(np.uint8)


def encode_png(rgba: np.ndarray) -> bytes:
    """An 8-bit RGBA PNG written with zlib and struct only (no imaging
    library is installed on the server). Every row uses filter type 0."""
    a = np.ascontiguousarray(rgba, dtype=np.uint8)
    if a.ndim != 3 or a.shape[2] != 4 or a.shape[0] == 0 or a.shape[1] == 0:
        raise ValueError("encode_png takes a (height, width, 4) array")
    h, w = a.shape[:2]
    raw = np.concatenate([np.zeros((h, 1), np.uint8), a.reshape(h, w * 4)], axis=1)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw.tobytes(), 9))
            + chunk(b"IEND", b""))


def _hex(c) -> str:
    return "#{:02X}{:02X}{:02X}".format(*c[:3])


def legend(kind: str) -> list[dict]:
    pairs = {"sun": (SUN_COLOURS, SUN_LABELS), "trees": (TREE_COLOURS, TREE_LABELS),
             "water": (WATER_COLOURS, WATER_LABELS)}[kind]
    return [{"color": _hex(c), "label": label} for c, label in zip(*pairs)]


def size(kind: str, shape: tuple[int, int] = (500, 600)) -> tuple[int, int]:
    """(width, height) of a layer's PNG."""
    if kind == "sun":
        return shape[1] // SUN_STRIDE_PX, shape[0] // SUN_STRIDE_PX
    return shape[1], shape[0]


def draw(kind: str, win: Optional[elevation.ElevationWindow],
         canopy: Optional[canopy_source.CanopyGrid]) -> np.ndarray:
    """The layer's RGBA image (north row first)."""
    if kind == "sun":
        return paint(sun_steps(*sun_grid(win, canopy)), SUN_COLOURS)
    if kind == "trees":
        return paint(tree_steps(canopy.height_m), TREE_COLOURS)
    if kind == "water":
        return paint(water_classes(win), WATER_COLOURS)
    raise KeyError(kind)


# --- status, drawing and the cache ------------------------------------------------------

class LayerNotReady(Exception):
    """The layer cannot be drawn now. `status` is not_ready or unavailable;
    `text` is the sentence for the owner."""

    def __init__(self, status: str, text: str):
        super().__init__(text)
        self.status = status
        self.text = text


def _sources_meta(session: Session, block: Block, kind: str,
                  now: datetime) -> dict[str, Optional[TileMeta]]:
    keys = _source_keys(block)
    return {name: _meta(session, *keys[name], now) for name in USES[kind]}


def _fresh(layer: Optional[TileMeta], srcs: dict[str, Optional[TileMeta]]) -> bool:
    """A cached picture is good while it is live, every source it needs is
    live, and no source tile it was drawn from is newer than it (the survey
    details are optional)."""
    if layer is None or layer.fetched_at is None:
        return False
    if any(m is None for name, m in srcs.items() if name != "survey"):
        return False
    return all(m.fetched_at is None or m.fetched_at <= layer.fetched_at
               for m in srcs.values() if m is not None)


def _expiry(srcs: dict[str, Optional[TileMeta]]) -> Optional[datetime]:
    ends = [m.expires_at for m in srcs.values() if m is not None and m.expires_at]
    return min(ends) if ends else None


def not_ready_text(preparing: bool) -> str:
    """The not_ready sentence: "still being prepared" only while the
    profile's background step is pending or building."""
    return NOT_READY_TEXT if preparing else READ_AGAIN_TEXT


def _check(kind: str, win, canopy, *, survey_live: bool = True) -> None:
    """Raise LayerNotReady when the sources in hand cannot make this layer.
    `survey_live` is False when the survey details are not cached (missing,
    or a partial record past its day): an unknown resolution then means
    "not read yet", not "too coarse"."""
    if kind in ("sun", "water") and win is None:
        raise LayerNotReady("not_ready", NOT_READY_TEXT)
    if kind in ("sun", "trees") and canopy is None:
        raise LayerNotReady("not_ready", NOT_READY_TEXT)
    if kind == "sun" and win.coverage() < 0.5:
        raise LayerNotReady("unavailable", NO_GROUND_TEXT)
    if kind == "water":
        if win.resolution_m is None and not survey_live and win.coverage() >= 0.5:
            raise LayerNotReady("not_ready", NOT_READY_TEXT)
        why = water_available(win)
        if why:
            raise LayerNotReady("unavailable", why)


def _load(session: Session, block: Block, kind: str, now: Optional[datetime] = None):
    win = cached_window(session, block, now=now) if kind in ("sun", "water") else None
    canopy = cached_canopy(session, block, now=now) if kind in ("sun", "trees") else None
    return win, canopy


def status(session: Session, block: Block, kind: str, *,
           in_us: bool = True, preparing: bool = True,
           now: Optional[datetime] = None) -> tuple[str, Optional[str]]:
    """(status, status_text) without drawing: ready when a fresh picture is
    cached or the cached sources can make one now. `preparing` says whether
    the profile's background step is pending or building (see
    `not_ready_text`)."""
    if kind not in KINDS:
        raise KeyError(kind)
    if not in_us:
        return "unavailable", OUTSIDE_US_TEXT
    t = now or datetime.utcnow()
    srcs = _sources_meta(session, block, kind, t)
    if _fresh(_meta(session, PROVIDER, DATASET_VERSION, layer_key(block, kind), t), srcs):
        return "ready", None
    try:
        _check(kind, *_load(session, block, kind, t),
               survey_live=srcs.get("survey") is not None)
    except LayerNotReady as exc:
        if exc.status == "not_ready":
            return exc.status, not_ready_text(preparing)
        return exc.status, exc.text
    return "ready", None


def layer_png(session: Session, block: Block, kind: str, *,
              property_id: Optional[int] = None,
              now: Optional[datetime] = None) -> bytes:
    """The layer's PNG: the cached one while it is fresh, otherwise drawn
    from the cached sources and stored. Raises LayerNotReady when a source
    is not cached (or cannot make this layer), KeyError for an unknown kind.
    Flushes; the caller commits. `property_id` only names the property in
    a log line (never the block: its key locates the land)."""
    if kind not in KINDS:
        raise KeyError(kind)
    t = now or datetime.utcnow()
    key = layer_key(block, kind)
    srcs = _sources_meta(session, block, kind, t)
    if _fresh(_meta(session, PROVIDER, DATASET_VERSION, key, t), srcs):
        hit = tiles.get(session, PROVIDER, DATASET_VERSION, key, now=t)
        if hit is not None:
            return hit
    win, canopy = _load(session, block, kind, t)
    _check(kind, win, canopy, survey_live=srcs.get("survey") is not None)
    png = encode_png(draw(kind, win, canopy))
    ends = _expiry(srcs)
    ttl = (ends - t) if ends is not None else tiles.DEFAULT_TTL
    if ttl > timedelta(0):
        try:
            tiles.put(session, PROVIDER, DATASET_VERSION, key, png, ttl=ttl, now=t)
        except Exception:  # noqa: BLE001 -- a lost race or a full disk: still answer
            logger.warning("could not store the %s layer for property %s", kind,
                           property_id, exc_info=True)
            session.rollback()
    return png


def warm(session: Session, block: Block, *, property_id: Optional[int] = None,
         now: Optional[datetime] = None) -> dict[str, str]:
    """Draw and store every layer the cached sources can make. Returns each
    kind's status. Never raises for one layer: a failure is logged and that
    layer reads "failed" here (a request draws it later)."""
    out: dict[str, str] = {}
    for kind in KINDS:
        try:
            layer_png(session, block, kind, property_id=property_id, now=now)
            out[kind] = "ready"
        except LayerNotReady as exc:
            out[kind] = exc.status
        except Exception:  # noqa: BLE001 -- one layer never sinks the others
            logger.warning("drawing the %s layer for property %s failed", kind,
                           property_id, exc_info=True)
            session.rollback()
            out[kind] = "failed"
    return out


# --- what the app is told ---------------------------------------------------------------

def _month_day(md: tuple[int, int]) -> str:
    return f"{datetime(2001, md[0], md[1]):%B} {md[1]}"


def _elevation_source(win: Optional[elevation.ElevationWindow]) -> dict:
    if win is not None:
        return words.source("3dep", str(win.year) if win.year else "",
                            elevation.survey_detail(win))
    return words.source("3dep")


def _canopy_source(canopy: Optional[canopy_source.CanopyGrid], block: Block) -> dict:
    grid_ = canopy or canopy_source.CanopyGrid(
        block=block, height_m=np.zeros((0, 0), np.float32),
        resolution_m=float(max(1, round(canopy_source.ground_resolution_m(
            block_centre(block)[0])))))
    return words.source("canopy", canopy_source.SOURCE_VERSION,
                        canopy_source.source_detail(grid_))


def explained(kind: str, block: Block, *, win=None, canopy=None) -> dict:
    """The Explained shape for a layer: what it shows, how it was worked
    out, its sources and its confidence."""
    if kind == "sun":
        start, end, how = season_for(block)
        season = (f"from {_month_day(start)} to {_month_day(end)}, the typical "
                  "frost-free season here" if how == "frost_free_period"
                  else f"from {_month_day(start)} to {_month_day(end)}")
        return {
            "display": ("Hours of direct sun a day in the growing season, "
                        f"{season}, in squares about 5 metres across."),
            "confidence": "rough_estimate",
            "reason": ("Worked out on our server from the sun's path at the middle of "
                       "this map, every 10 minutes on every 7th day, the slope of the "
                       "ground and tree canopy height. A square mostly under tree canopy "
                       "counts as shade while leaves are out. Buildings are not counted. "
                       "Near the edge of the map the sun reads high, because hills and "
                       "trees beyond the map are not counted."),
            "sources": [words.source("sunpos"), _elevation_source(win),
                        _canopy_source(canopy, block)],
            "provenance": "modelled",
        }
    if kind == "trees":
        src = _canopy_source(canopy, block)
        res = (canopy.resolution_m if canopy is not None else
               float(max(1, round(canopy_source.ground_resolution_m(block_centre(block)[0])))))
        return {
            "display": f"Tree canopy height, mapped at {res:g} metre detail.",
            "confidence": "area_estimate",
            "reason": ("From a canopy height map made from satellite imagery by Meta and "
                       "World Resources Institute. Canopy under 2 metres is not drawn. "
                       "A height of 0 can mean no trees or no data."),
            "sources": [src],
            "provenance": "modelled",
        }
    if kind == "water":
        return {
            "display": ("Where rain would collect and where runoff runs through, from "
                        "the elevation survey."),
            "confidence": "rough_estimate",
            "reason": ("Worked out on our server from the elevation survey: low spots "
                       "where rain would stand at least 10 centimetres deep, and paths "
                       "that gather runoff from at least 2,000 square metres (about half "
                       "an acre) uphill. Soil is not counted on this map. This is not a "
                       "flood insurance determination."),
            "sources": [words.source("terrain"), _elevation_source(win)],
            "provenance": "modelled",
        }
    raise KeyError(kind)


def layers_for(session: Session, block: Block, *, in_us: bool, property_id: int,
               preparing: bool = True, now: Optional[datetime] = None) -> dict:
    """The /properties/{id}/layers answer as a dict (schemas.MapLayersOut).
    Never draws and never fetches."""
    out = []
    for kind in KINDS:
        st, text = status(session, block, kind, in_us=in_us, preparing=preparing,
                          now=now)
        win = canopy = None
        if in_us and st != "not_ready":
            # Decoding is cheap and memoised; it names the survey and its year.
            win, canopy = _load(session, block, kind, now)
        width, height = size(kind)
        out.append({
            "kind": kind, "title": TITLES[kind], "status": st, "status_text": text,
            "image_path": (f"/properties/{property_id}/layers/{kind}.png"
                           if st == "ready" else None),
            "width": width, "height": height, "legend": legend(kind),
            "explained": explained(kind, block, win=win, canopy=canopy),
            "notes": list(NOTES[kind]),
        })
    return {"property_id": property_id, "bounds": grid.block_box(block), "layers": out}
