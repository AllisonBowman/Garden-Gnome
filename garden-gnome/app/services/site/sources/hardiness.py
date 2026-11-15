"""Hardiness zone from the 2023 USDA Plant Hardiness Zone Map, held on this
server (PLAN.md P0-7, section 6 "Hardiness zone").

`data/phzm2023_conus.bin` is built from the official raster by
`data/build_phzm2023.py` (see `data/README.md`). Nothing is sent anywhere:
the pin is looked up in the file. The contiguous United States only; a pin
outside it (Alaska, Hawaii, Puerto Rico, abroad, open water) reads "unknown".

Confidence (PLAN.md section 6): "high" when the cell's value is 1 °F or more
from a zone line, "medium" when closer ("on the line between").
"""
from __future__ import annotations

import json
import math
import struct
import threading
import zlib
from functools import lru_cache
from pathlib import Path

from app.services.site.types import Block, Reading

SOURCE_KEY = "phzm2023"
SOURCE_VERSION = "2023"
METHOD = "grid_sample_30_arc_second"
DATA_FILE = Path(__file__).parent / "data" / "phzm2023_conus.bin"
MAGIC = b"PHZM2023"
#: Every zone line is a multiple of 5 °F; zone 1a starts at -60 °F.
ZONE_BASE_F = -60
BAND_F = 5
#: The stored values are floored to this step.
STEP_F = 0.5
#: Closer than this to a zone line reads "medium" (PLAN.md section 6).
NEAR_LINE_F = 1.0


class _Grid:
    def __init__(self, path: Path):
        self._f = open(path, "rb")
        self._lock = threading.Lock()
        magic = self._f.read(len(MAGIC))
        if magic != MAGIC:
            raise ValueError(f"{path} is not a hardiness grid file")
        head_len, n_tiles = struct.unpack("<II", self._f.read(8))
        self.header = json.loads(self._f.read(head_len))
        self._offsets = struct.unpack(f"<{n_tiles + 1}Q", self._f.read(8 * (n_tiles + 1)))
        self._base = self._f.tell()
        h = self.header
        self.tile = h["tile"]
        self.tiles_across = math.ceil(h["cols"] / self.tile)

    def _tile_bytes(self, index: int) -> bytes:
        with self._lock:
            self._f.seek(self._base + self._offsets[index])
            raw = self._f.read(self._offsets[index + 1] - self._offsets[index])
        return zlib.decompress(raw)

    @lru_cache(maxsize=16)
    def _tile(self, tr: int, tc: int) -> tuple[bytes, int]:
        h = self.header
        width = min(self.tile, h["cols"] - tc * self.tile)
        return self._tile_bytes(tr * self.tiles_across + tc), width

    def value(self, lat: float, lng: float) -> int | None:
        """The stored value (half degrees Fahrenheit, floored) or None."""
        h = self.header
        col = math.floor((lng - h["west"]) / h["cell_deg"])
        row = math.floor((h["north"] - lat) / h["cell_deg"])
        if not (0 <= row < h["rows"] and 0 <= col < h["cols"]):
            return None
        data, width = self._tile(row // self.tile, col // self.tile)
        b = data[(row % self.tile) * width + (col % self.tile)]
        v = b - 256 if b > 127 else b
        return None if v == h["nodata"] else v


_grid: _Grid | None = None
_grid_lock = threading.Lock()


def _get_grid() -> _Grid:
    global _grid
    with _grid_lock:
        if _grid is None:
            _grid = _Grid(DATA_FILE)
        return _grid


def zone_for(temp_f: float) -> tuple[str, int, int]:
    """(zone label like "8a", low °F, high °F) for an extreme minimum."""
    band = math.floor((temp_f - ZONE_BASE_F) / BAND_F)
    band = max(0, min(band, 25))           # 1a .. 13b
    number, half = band // 2 + 1, "ab"[band % 2]
    low = ZONE_BASE_F + band * BAND_F
    return f"{number}{half}", low, low + BAND_F


def lookup(lat: float, lng: float) -> dict | None:
    """The hardiness zone at a point, or None outside coverage."""
    stored = _get_grid().value(lat, lng)
    if stored is None:
        return None
    lo = stored * STEP_F
    hi = lo + STEP_F               # the true value lies in [lo, hi)
    zone, low, high = zone_for(lo)
    # Conservative: the distance from the nearest edge of [lo, hi) to a line.
    distance = min(lo - low, high - hi)
    nearest = low if (lo - low) <= (high - hi) else high
    return {
        "zone": zone, "low_f": low, "high_f": high,
        "extreme_min_f": [lo, hi], "distance_to_line_f": round(distance, 2),
        "nearest_line_f": nearest,
    }


def read(block: Block, pin: tuple[float, float], footprint: dict | None, *,
         client=None, session=None) -> list[Reading]:
    """One `hardiness_zone` reading at the pin. No network: `client` and
    `session` are accepted for the shared signature and not used."""
    lat, lng = pin
    found = lookup(lat, lng)
    if found is None:
        return [Reading(
            field="hardiness_zone", value=None, level="unknown",
            provenance="public_map", source_key=SOURCE_KEY,
            source_version=SOURCE_VERSION, method=METHOD,
            reason_codes=("outside_coverage",),
            detail={"coverage": "contiguous United States"})]
    near = found["distance_to_line_f"] < NEAR_LINE_F
    return [Reading(
        field="hardiness_zone",
        value={"zone": found["zone"], "low_f": found["low_f"], "high_f": found["high_f"]},
        level="medium" if near else "high",
        provenance="public_map", source_key=SOURCE_KEY,
        source_version=SOURCE_VERSION, method=METHOD,
        reason_codes=("near_zone_line",) if near else (),
        detail={"extreme_min_f": found["extreme_min_f"],
                "distance_to_line_f": found["distance_to_line_f"],
                "nearest_line_f": found["nearest_line_f"],
                "cell": "30 arc-seconds, about 800 metres",
                "period": "1991 to 2020"})]
