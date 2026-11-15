"""Elevation window for the snapped block (build spec sections 3 and 5).

Source: the United States Geological Survey 3D Elevation Program (3DEP)
dynamic elevation service, which mosaics every published survey and uses
the finest one at each place (1 metre laser ground survey where it exists,
else about 3 metres, else about 10 metres). Public domain.

How it is called (PLAN.md P0-3 and D26, measured 2026-11-15, see
docs/design/2026-11-15-sun-and-drainage-sources.md):

- `exportImage` with the block bounds in degrees (`bboxSR=4326`), output in
  degrees (`imageSR=4326`) on a fixed lattice of 0.00001 degree (about 1.1
  metres north to south, 0.87 to 0.96 metres east to west in the contiguous
  United States), so the 0.006 by 0.005 degree block is always 600 by 500
  pixels and the server keeps the box exactly. `format=bsq` is raw 32-bit
  floats followed by a 1-bit validity mask; the image formats come back
  padded, and the length of the raw answer is checked in full.
- When the whole block does not come back (the service answered 504 to
  some requests on 2026-11-15, and its cache repeats a 504 for a while), the
  four cells of the block are asked for one by one and stitched. Either way
  only grid lines leave this server.
- `getSamples` at the block's centre vertex (a grid point) tells which survey
  the mosaic used there and its resolution; a catalog `query` by that
  survey's identifier gives its title and year. Both are optional: without
  them the window is still used, and the resolution reads as unknown.

The window is cached in the shared tile store as centimetres, row by row as
differences (it compresses to about a fifth of the raw floats).
"""
from __future__ import annotations

import json
import math
import re
import struct
import time
from dataclasses import dataclass, field as dc_field
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

import numpy as np

from app.services.site import tiles
from app.services.site.http import Coord
from app.services.site.types import Block, Reading, SourceUnavailable

BASE = "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer"
SOURCE_KEY = "3dep"
PROVIDER = "3dep"
#: Our encoding of the cached window. A new encoding gets a new version, so an
#: old tile is simply not found rather than misread.
DATASET_VERSION = "dynamic-bsq-1e-5deg-v1"
SOURCE_NAME = "United States Geological Survey 3D Elevation Program"
SOURCE_URL = "https://www.usgs.gov/3d-elevation-program"
ATTRIBUTION = ("Map services and data available from U.S. Geological Survey, "
               "National Geospatial Program.")

#: The lattice step in degrees, both axes. Grid lines are whole multiples of
#: it, so a block is always a whole number of pixels.
STEP_DEG = 1e-5
#: The cache keeps a window, and complete survey details, this long;
#: incomplete survey details a day (so they are asked for again soon).
TTL = timedelta(days=90)
TTL_PARTIAL = timedelta(days=1)
#: Attempts at a full-length answer (the service often cuts answers short).
FETCH_ATTEMPTS = 3
#: Values outside this range are not ground heights.
MIN_M, MAX_M = -500.0, 9000.0
M_PER_DEG_LAT = 111_320.0
_MAGIC = b"DEM1"


@dataclass(frozen=True)
class ElevationWindow:
    """Ground heights over one block, north row first, west column first."""
    block: Block
    z: np.ndarray                 # float32 metres, shape (rows, cols)
    valid: np.ndarray             # bool, same shape
    resolution_m: Optional[float]  # native survey detail at the centre; None = unknown
    raster_id: Optional[int] = None
    title: Optional[str] = None
    year: Optional[int] = None
    fetched_by: str = "block"     # "block" or "cells"
    meta: dict = dc_field(default_factory=dict)

    @property
    def rows(self) -> int:
        return int(self.z.shape[0])

    @property
    def cols(self) -> int:
        return int(self.z.shape[1])

    @property
    def dlat(self) -> float:
        return (self.block.north - self.block.south) / self.rows

    @property
    def dlng(self) -> float:
        return (self.block.east - self.block.west) / self.cols

    @property
    def dy_m(self) -> float:
        """Pixel height on the ground, metres."""
        return self.dlat * M_PER_DEG_LAT

    @property
    def dx_m(self) -> float:
        """Pixel width on the ground at the block's middle latitude, metres."""
        mid = (self.block.south + self.block.north) / 2
        return self.dlng * M_PER_DEG_LAT * math.cos(math.radians(mid))

    def to_pixel(self, lat: float, lng: float) -> tuple[float, float]:
        """(row, col) as fractions; pixel centres sit at whole + 0.5."""
        return ((self.block.north - lat) / self.dlat,
                (lng - self.block.west) / self.dlng)

    def coverage(self) -> float:
        return float(self.valid.mean()) if self.valid.size else 0.0


# --- the lattice ----------------------------------------------------------------

def lattice_shape(west: float, south: float, east: float, north: float) -> tuple[int, int]:
    """(rows, cols) of the fixed lattice over a grid-aligned box."""
    return (int(round((north - south) / STEP_DEG)),
            int(round((east - west) / STEP_DEG)))


def _grid_text(v: float) -> str:
    """A grid line as short decimal text (grid lines have at most 4 decimals)."""
    return repr(round(v, 4))


def _bbox(west: float, south: float, east: float, north: float) -> str:
    return ",".join(_grid_text(v) for v in (west, south, east, north))


def block_cells_boxes(block: Block) -> list[tuple[float, float, float, float]]:
    """The block's four cells as (west, south, east, north): grid lines only."""
    mid_lng = round((block.west + block.east) / 2, 4)
    mid_lat = round((block.south + block.north) / 2, 4)
    return [(block.west, mid_lat, mid_lng, block.north),   # north-west
            (mid_lng, mid_lat, block.east, block.north),   # north-east
            (block.west, block.south, mid_lng, mid_lat),   # south-west
            (mid_lng, block.south, block.east, mid_lat)]   # south-east


# --- the raw answer ---------------------------------------------------------------

def parse_bsq(body: bytes, rows: int, cols: int) -> tuple[np.ndarray, np.ndarray]:
    """Raw little-endian float32 pixels, then (optionally) a 1-bit validity
    mask, most significant bit first. Raises ValueError on a short body or
    an error document."""
    n = rows * cols
    if body[:1] in (b"{", b"<"):
        raise ValueError("the service sent an error document, not pixels")
    if len(body) < 4 * n:
        raise ValueError(f"answer cut short: {len(body)} bytes, need {4 * n}")
    z = np.frombuffer(body[:4 * n], dtype="<f4").reshape(rows, cols).astype(np.float32)
    valid = np.isfinite(z) & (z > MIN_M) & (z < MAX_M)
    mask = body[4 * n:]
    if len(mask) * 8 >= n:
        bits = np.unpackbits(np.frombuffer(mask, dtype=np.uint8))[:n].reshape(rows, cols)
        valid &= bits.astype(bool)
    z = np.where(valid, z, np.float32(0))
    return z, valid


def encode_window(z: np.ndarray, valid: np.ndarray, header: dict) -> bytes:
    """Our cached form: magic, header length, JSON header, the window in
    whole centimetres as row-wise differences (int32), then the packed mask."""
    cm = np.where(valid, np.round(z.astype(np.float64) * 100.0), 0).astype(np.int64)
    delta = np.diff(cm, axis=1, prepend=0).astype("<i4")
    head = dict(header, rows=int(z.shape[0]), cols=int(z.shape[1]))
    hb = json.dumps(head, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return (_MAGIC + struct.pack("<I", len(hb)) + hb + delta.tobytes()
            + np.packbits(valid.astype(np.uint8).ravel()).tobytes())


def decode_window(payload: bytes) -> tuple[np.ndarray, np.ndarray, dict]:
    if payload[:4] != _MAGIC:
        raise ValueError("not a cached elevation window")
    (hl,) = struct.unpack("<I", payload[4:8])
    head = json.loads(payload[8:8 + hl].decode("utf-8"))
    rows, cols = head["rows"], head["cols"]
    n = rows * cols
    off = 8 + hl
    delta = np.frombuffer(payload[off:off + 4 * n], dtype="<i4").reshape(rows, cols)
    cm = np.cumsum(delta.astype(np.int64), axis=1)
    bits = np.unpackbits(np.frombuffer(payload[off + 4 * n:], dtype=np.uint8))[:n]
    valid = bits.reshape(rows, cols).astype(bool)
    z = (cm / 100.0).astype(np.float32)
    return z, valid, head


# --- fetching ----------------------------------------------------------------------

def _export(client, box: tuple[float, float, float, float]) -> tuple[np.ndarray, np.ndarray]:
    rows, cols = lattice_shape(*box)
    params = {
        "bbox": _bbox(*box), "bboxSR": "4326", "imageSR": "4326",
        "size": f"{cols},{rows}", "format": "bsq", "pixelType": "F32",
        "interpolation": "RSP_BilinearInterpolation", "f": "image",
    }
    last = ""
    for _ in range(FETCH_ATTEMPTS):
        r = client.get(BASE + "/exportImage", params=params,
                       coords={"bbox": Coord.BBOX}, not_coordinates=("size",),
                       source_key=SOURCE_KEY)
        try:
            return parse_bsq(r.content, rows, cols)
        except ValueError as exc:
            last = str(exc)
    raise SourceUnavailable(SOURCE_KEY, last or "no usable answer")


def fetch_pixels(block: Block, client) -> tuple[np.ndarray, np.ndarray, str]:
    """The block's window: one request, or its four cells if that fails."""
    try:
        z, valid = _export(client, (block.west, block.south, block.east, block.north))
        return z, valid, "block"
    except SourceUnavailable as first:
        parts = []
        for box in block_cells_boxes(block):
            try:
                parts.append(_export(client, box))
            except SourceUnavailable as exc:
                raise SourceUnavailable(
                    SOURCE_KEY, f"block: {first.detail}; cell: {exc.detail}") from exc
    (nw, nwv), (ne, nev), (sw, swv), (se, sev) = parts
    z = np.vstack([np.hstack([nw, ne]), np.hstack([sw, se])])
    valid = np.vstack([np.hstack([nwv, nev]), np.hstack([swv, sev])])
    return z, valid, "cells"


def centre_vertex(block: Block) -> tuple[float, float]:
    """(lng, lat) of the grid vertex at the block's centre."""
    return (round((block.west + block.east) / 2, 4),
            round((block.south + block.north) / 2, 4))


def fetch_survey(block: Block, client) -> dict:
    """Which survey the mosaic uses at the block's centre vertex. Never
    raises: an empty dict means the details are not known."""
    out: dict = {}
    lng, lat = centre_vertex(block)
    geometry = json.dumps({"points": [[lng, lat]], "spatialReference": {"wkid": 4326}})
    try:
        r = client.get(BASE + "/getSamples", params={
            "geometry": geometry, "geometryType": "esriGeometryMultipoint",
            "returnFirstValueOnly": "true", "f": "json"},
            # An Esri multipoint, not GeoJSON: the guard scans it, and both
            # numbers must sit on grid lines (they are the centre vertex).
            source_key=SOURCE_KEY)
        sample = (r.json().get("samples") or [{}])[0]
        if sample.get("resolution") is not None:
            out["resolution_m"] = float(sample["resolution"])
        if sample.get("rasterId") is not None:
            out["raster_id"] = int(sample["rasterId"])
    except (SourceUnavailable, TypeError, KeyError, IndexError, AttributeError,
            json.JSONDecodeError):
        return out
    if "raster_id" not in out:
        return out
    try:
        r = client.get(BASE + "/query", params={
            "objectIds": str(out["raster_id"]),
            "outFields": "OBJECTID,title,AcquisitionDate,LowPS",
            "returnGeometry": "false", "f": "json"},
            not_coordinates=("objectIds",), source_key=SOURCE_KEY)
        feats = [f.get("attributes") or {} for f in (r.json().get("features") or [])]
        attrs = next((a for a in feats if a.get("OBJECTID") == out["raster_id"]), {})
        if attrs.get("title"):
            out["title"] = str(attrs["title"])
        if attrs.get("AcquisitionDate"):
            out["year"] = datetime.fromtimestamp(
                attrs["AcquisitionDate"] / 1000, tz=timezone.utc).year
        if "year" not in out and out.get("title"):
            m = re.search(r"(19|20)\d\d(?!.*(19|20)\d\d)", out["title"])
            if m:
                out["year"] = int(m.group(0))   # the survey project's year
        if out.get("resolution_m") is None and attrs.get("LowPS") is not None:
            out["resolution_m"] = float(attrs["LowPS"])
    except (SourceUnavailable, TypeError, KeyError, IndexError, AttributeError,
            json.JSONDecodeError):
        pass
    return out


def tile_key(block: Block) -> str:
    return f"{block.key}_dem"


def survey_key(block: Block) -> str:
    return f"{block.key}_dem_survey"


def _window(block: Block, z, valid, head) -> ElevationWindow:
    return ElevationWindow(
        block=block, z=z, valid=valid, resolution_m=head.get("resolution_m"),
        raster_id=head.get("raster_id"), title=head.get("title"),
        year=head.get("year"), fetched_by=head.get("fetched_by", "block"),
        meta=head)


def _complete(survey: dict) -> bool:
    return "resolution_m" in survey and "year" in survey


#: A few recently used windows, so several zones in one request decode once.
_RECENT: dict[tuple, ElevationWindow] = {}
_RECENT_MAX = 4
#: When the survey details were last asked for, per block, in this process.
#: The catalog answers slowly or not at all some days (20 to 50 seconds and
#: 502 answers on 2026-11-15), so a block is asked at most once an hour.
_SURVEY_TRIED: dict[str, float] = {}
SURVEY_RETRY_SECONDS = 3600.0


def _survey(session, block: Block, client) -> dict:
    """The survey details, cached on their own: complete details live as long
    as the window, incomplete ones a day, so the year is asked for again
    without fetching the window again."""
    cached = None
    if session is not None:
        cached = tiles.get_json(session, PROVIDER, DATASET_VERSION, survey_key(block))
    if cached is not None and _complete(cached):
        return cached
    now = time.monotonic()
    last = _SURVEY_TRIED.get(block.key)
    if last is not None and now - last < SURVEY_RETRY_SECONDS:
        return cached or {}
    _SURVEY_TRIED[block.key] = now
    got = {**(cached or {}), **fetch_survey(block, client)}
    if session is not None and got:
        tiles.put_json(session, PROVIDER, DATASET_VERSION, survey_key(block), got,
                       ttl=TTL if _complete(got) else TTL_PARTIAL)
    return got


def load_window(session, block: Block, *, client) -> ElevationWindow:
    """The block's window, from the tile cache when it is there, otherwise
    fetched (and stored, when there is a session). Raises SourceUnavailable
    when there is no window; missing survey details only leave the
    resolution and year unknown."""
    payload = None
    if session is not None:
        payload = tiles.get(session, PROVIDER, DATASET_VERSION, tile_key(block))
    if payload is None:
        z, valid, how = fetch_pixels(block, client)
        payload = encode_window(z, valid, {"block": block.key, "fetched_by": how})
        if session is not None:
            tiles.put(session, PROVIDER, DATASET_VERSION, tile_key(block), payload, ttl=TTL)
    survey = _survey(session, block, client)
    key = (block.key, hash(payload), json.dumps(survey, sort_keys=True))
    hit = _RECENT.get(key)
    if hit is not None:
        return hit
    z, valid, head = decode_window(payload)
    win = _window(block, z, valid, {**head, **survey})
    if len(_RECENT) >= _RECENT_MAX:
        _RECENT.pop(next(iter(_RECENT)))
    _RECENT[key] = win
    return win


# --- the reading ---------------------------------------------------------------------

def resolution_level(resolution_m: Optional[float]) -> str:
    """The highest level the survey's detail allows (PLAN.md section 6)."""
    if resolution_m is None:
        return "low"
    if resolution_m <= 1.5:
        return "high"
    if resolution_m <= 3.5:
        return "medium"
    return "low"


def survey_detail(win: ElevationWindow) -> dict:
    """The detail every terrain reading carries, so the copy can name the
    survey: resolution, year, title, and the source's own name."""
    d = {"resolution_m": win.resolution_m, "source_name": SOURCE_NAME,
         "source_url": SOURCE_URL, "attribution": ATTRIBUTION,
         "pixel_m": [round(win.dx_m, 2), round(win.dy_m, 2)]}
    if win.year:
        d["year"] = win.year
    if win.title:
        d["survey"] = win.title
    if win.raster_id is not None:
        d["raster_id"] = win.raster_id
    d["source_detail"] = ("Laser ground survey" if win.resolution_m is not None
                          and win.resolution_m <= 3.5 else "Elevation survey")
    return {k: v for k, v in d.items() if v is not None}


def window_reading(win: ElevationWindow) -> Reading:
    cover = win.coverage()
    version = str(win.year) if win.year else "dynamic service"
    if cover < 0.5:
        return Reading(field="elevation_window", value=None, level="unknown",
                       provenance="public_map", source_key=SOURCE_KEY,
                       source_version=version, method="3dep_exportimage_bsq",
                       reason_codes=("no_elevation_here",),
                       detail={"coverage_share": round(cover, 3), **survey_detail(win)})
    zs = win.z[win.valid]
    codes = []
    if win.resolution_m is None:
        codes.append("resolution_unknown")
    if win.fetched_by == "cells":
        codes.append("fetched_by_cell")
    value = {"resolution_m": win.resolution_m, "rows": win.rows, "cols": win.cols,
             "min_m": round(float(zs.min()), 2), "max_m": round(float(zs.max()), 2)}
    return Reading(field="elevation_window", value=value,
                   level=resolution_level(win.resolution_m), provenance="public_map",
                   source_key=SOURCE_KEY, source_version=version,
                   method="3dep_exportimage_bsq", reason_codes=tuple(codes),
                   detail={"coverage_share": round(cover, 3), **survey_detail(win)})


def read(block: Block, pin: tuple[float, float], footprint: Optional[dict], *,
         client, session=None, readings: Sequence[Reading] = ()) -> list[Reading]:
    """The elevation_window reading for the block (build spec section 3)."""
    return [window_reading(load_window(session, block, client=client))]
