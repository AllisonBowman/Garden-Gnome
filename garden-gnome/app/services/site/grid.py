"""The snap grid: the only location outside geodata services ever see (D7).

The grid is fixed in degrees: rows every 0.0025 degrees of latitude (about
278 metres) and columns every 0.003 degrees of longitude (about 290 metres at
Austin, 260 metres at Washington, 220 metres at the Canadian border), so a
cell is about 250 metres across in the contiguous United States. Grid lines
are integer multiples of those steps, held as integers ("units" of 0.0001
degree) so that no key and no comparison depends on floating point.

A property's block is the fixed 2 by 2 block of cells whose shared corner is
the grid vertex nearest the pin: about 500 metres across, with the pin always
at least half a cell inside it. Which block is requested therefore depends
only on the grid, never on where the lot sits inside a cell; every pin in the
same quarter-cell neighbourhood of a vertex asks for exactly the same block.

Keys are text: "blk1_<row>_<col>" for a block (the vertex indices) and
"cell1_<row>_<col>" for a cell (its south-west corner). The "1" is the grid
version; a different grid would get a new prefix rather than reuse keys.
"""
from __future__ import annotations

import math
import re
from decimal import Decimal

from app.services.site.types import Block

GRID_VERSION = "1"
#: One unit is 0.0001 degree. Steps are whole units.
UNIT = Decimal("0.0001")
LAT_STEP_UNITS = 25   # 0.0025 degrees
LNG_STEP_UNITS = 30   # 0.003 degrees
LAT_STEP = float(LAT_STEP_UNITS * UNIT)
LNG_STEP = float(LNG_STEP_UNITS * UNIT)

#: How far a value may sit from a grid line and still count as on it, in
#: degrees: 1 centimetre, enough to forgive float arithmetic and no more.
TOLERANCE_DEG = 1e-7

BLOCK_PREFIX = f"blk{GRID_VERSION}_"
CELL_PREFIX = f"cell{GRID_VERSION}_"
_BLOCK_RE = re.compile(rf"^blk{GRID_VERSION}_(-?\d+)_(-?\d+)")

#: The default whole-lot footprint: a north-aligned square of about 8,500
#: square feet centred on the pin (PLAN.md section 5, the maps research's
#: typical United States lot). Shown as an approximate yard, never as a
#: property line.
DEFAULT_FOOTPRINT_SQFT = 8500.0
_M_PER_FT = 0.3048
_M_PER_DEG_LAT = 111_320.0


def _units(value: float) -> Decimal:
    return Decimal(repr(float(value))) / UNIT


def _edge(index: int, step_units: int) -> float:
    """A grid line as the float nearest its exact decimal value."""
    return float(Decimal(index * step_units) * UNIT)


def _nearest_index(value: float, step_units: int) -> int:
    return int((_units(value) / step_units).to_integral_value())


def _on(value: float, step_units: int) -> bool:
    if not math.isfinite(value):
        return False
    step = float(step_units * UNIT)
    nearest = round(value / step) * step
    return abs(value - nearest) <= TOLERANCE_DEG


def lat_on_grid(value: float) -> bool:
    return _on(float(value), LAT_STEP_UNITS)


def lng_on_grid(value: float) -> bool:
    return _on(float(value), LNG_STEP_UNITS)


def on_grid(value: float) -> bool:
    """On a grid line of either axis. Used where the axis is not known."""
    return lat_on_grid(value) or lng_on_grid(value)


def _check_pin(lat: float, lng: float) -> None:
    if not (math.isfinite(lat) and math.isfinite(lng)
            and -90 <= lat <= 90 and -180 <= lng <= 180):
        raise ValueError(f"not a latitude and longitude: {lat!r}, {lng!r}")


def block_for(row: int, col: int) -> Block:
    """The 2 by 2 block around grid vertex (row, col)."""
    return Block(
        key=f"{BLOCK_PREFIX}{row}_{col}",
        west=_edge(col - 1, LNG_STEP_UNITS),
        south=_edge(row - 1, LAT_STEP_UNITS),
        east=_edge(col + 1, LNG_STEP_UNITS),
        north=_edge(row + 1, LAT_STEP_UNITS),
    )


def snap_block(lat: float, lng: float) -> Block:
    """The block a pin maps to: the one whose shared corner is nearest."""
    _check_pin(lat, lng)
    return block_for(_nearest_index(lat, LAT_STEP_UNITS),
                     _nearest_index(lng, LNG_STEP_UNITS))


def block_from_key(key: str) -> Block:
    m = _BLOCK_RE.match(key)
    if not m or m.end() != len(key):
        raise ValueError(f"not a block key: {key!r}")
    return block_for(int(m.group(1)), int(m.group(2)))


def block_key_prefix(tile_key: str) -> str | None:
    """The block key a tile key starts with, or None if it names no block."""
    m = _BLOCK_RE.match(tile_key)
    if not m:
        return None
    rest = tile_key[m.end():]
    if rest and rest[0].isdigit():
        return None  # "blk1_1_23" is not a prefix of "blk1_1_234"
    return tile_key[:m.end()]


def block_cells(block: Block) -> list[str]:
    """The four cell keys in a block, south-west first, row by row."""
    m = _BLOCK_RE.match(block.key)
    if not m:
        raise ValueError(f"not a block key: {block.key!r}")
    row, col = int(m.group(1)), int(m.group(2))
    return [f"{CELL_PREFIX}{r}_{c}"
            for r in (row - 1, row) for c in (col - 1, col)]


def block_box(block: Block) -> dict:
    return {"west": block.west, "south": block.south,
            "east": block.east, "north": block.north}


# --- footprints (sampled on this server only; never sent anywhere) -----------

def box_polygon(west: float, south: float, east: float, north: float) -> dict:
    """A box as a GeoJSON Polygon (longitude, latitude; counter-clockwise)."""
    if not (west < east and south < north):
        raise ValueError("a box needs west < east and south < north")
    ring = [[west, south], [east, south], [east, north], [west, north],
            [west, south]]
    return {"type": "Polygon", "coordinates": [ring]}


def polygon_box(geojson: dict | None) -> dict | None:
    """The bounding box of a stored GeoJSON Polygon, as a Box dict."""
    if not geojson or geojson.get("type") != "Polygon":
        return None
    ring = geojson["coordinates"][0]
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return {"west": min(xs), "south": min(ys), "east": max(xs), "north": max(ys)}


def default_footprint_box(lat: float, lng: float,
                          sqft: float = DEFAULT_FOOTPRINT_SQFT) -> dict:
    """The north-aligned square of `sqft` square feet centred on the pin."""
    _check_pin(lat, lng)
    half_m = math.sqrt(sqft) * _M_PER_FT / 2
    dlat = half_m / _M_PER_DEG_LAT
    dlng = half_m / (_M_PER_DEG_LAT * math.cos(math.radians(lat)))
    return {"west": lng - dlng, "south": lat - dlat,
            "east": lng + dlng, "north": lat + dlat}


def default_footprint(lat: float, lng: float) -> dict:
    """The default whole-lot footprint as a GeoJSON Polygon."""
    b = default_footprint_box(lat, lng)
    return box_polygon(b["west"], b["south"], b["east"], b["north"])


def box_area_sqft(box: dict) -> float:
    """Approximate area of a Box in square feet (small boxes only)."""
    mid = (box["south"] + box["north"]) / 2
    h = (box["north"] - box["south"]) * _M_PER_DEG_LAT
    w = (box["east"] - box["west"]) * _M_PER_DEG_LAT * math.cos(math.radians(mid))
    return h * w / (_M_PER_FT ** 2)


# --- weather cells (about 1 kilometre, like today's weather rounding) --------

def weather_cell_key(lat: float, lng: float) -> str:
    """A text key for a forecast cell: the pin at two decimal places, as
    services/weather.py already rounds what it sends. Never a float."""
    _check_pin(lat, lng)
    r = int((Decimal(repr(float(lat))) * 100).to_integral_value())
    c = int((Decimal(repr(float(lng))) * 100).to_integral_value())
    return f"wx2_{r}_{c}"
