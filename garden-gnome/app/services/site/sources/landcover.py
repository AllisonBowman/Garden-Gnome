"""Neighbourhood land cover and tree cover from the United States Geological
Survey Annual National Land Cover Database (Collection 1.2, 30 metre cells)
and its tree canopy cover layer (United States Department of Agriculture
Forest Service), PLAN.md section 6 "Land cover".

Privacy: each request is a Web Map Service GetMap for the grid-snapped
block only, in degrees (EPSG:4326). The answer is a small uncompressed
GeoTIFF covering exactly the block, which is read here and sampled on this
server. Nothing about the lot is claimed: both readings are "Neighbourhood
context" (land cover and tree cover never describe the lot, PLAN.md
section 6), so they carry reason code "neighbourhood_only".

Requests per block: land cover for the latest year, the year before and
1985 (history), percent impervious and percent tree canopy for the latest
year. Five small GETs, about 0.2 to 0.5 seconds each.
"""
from __future__ import annotations

import math
import struct
from datetime import timedelta
from typing import Optional

from app.services.site import tiles
from app.services.site.http import Coord
from app.services.site.types import Block, Reading, SourceUnavailable

SOURCE_KEY = "nlcd"
YEAR = 2025
PREVIOUS_YEAR = 2024
HISTORY_YEAR = 1985
SOURCE_VERSION = f"Annual NLCD Collection 1.2, {YEAR}"
CANOPY_VERSION = f"NLCD Tree Canopy Cover v2025-6, {YEAR}"
METHOD = "block_window_class_mix"
CACHE_VERSION = f"wms-1-{YEAR}"
GEOSERVER = "https://dmsdata.cr.usgs.gov/geoserver"
#: Output pixels across the block; several per 30 metre cell, so shares
#: follow cell areas closely.
SIZE = 32
TTL = timedelta(days=365)

#: The standard legend. Colour is how the land cover layer's styled GeoTIFF
#: carries the class.
CLASSES = {
    11: ("Open water", (70, 107, 159)),
    12: ("Perennial ice or snow", (209, 222, 248)),
    21: ("Developed, open space", (222, 197, 197)),
    22: ("Developed, low intensity", (217, 146, 130)),
    23: ("Developed, medium intensity", (235, 0, 0)),
    24: ("Developed, high intensity", (171, 0, 0)),
    31: ("Barren land", (179, 172, 159)),
    41: ("Deciduous forest", (104, 171, 95)),
    42: ("Evergreen forest", (28, 95, 44)),
    43: ("Mixed forest", (181, 197, 143)),
    52: ("Shrub or scrub", (204, 184, 121)),
    71: ("Grassland", (223, 223, 194)),
    81: ("Pasture or hay", (220, 217, 57)),
    82: ("Cultivated crops", (171, 108, 40)),
    90: ("Woody wetlands", (184, 217, 235)),
    95: ("Emergent herbaceous wetlands", (108, 159, 184)),
}
_BY_COLOUR = {rgb: code for code, (_, rgb) in CLASSES.items()}
DEVELOPED = (21, 22, 23, 24)
LAYERS = {
    "land_cover": "Land-Cover-Native_conus_year_data",
    "impervious": "Fractional-Impervious-Surface-Native_conus_year_data",
    "canopy": "NLCD-Tree-Canopy-Native_conus_year_data",
}


# --- a minimal reader for the uncompressed GeoTIFF the service returns ---------------

def read_tiff(data: bytes) -> tuple[int, int, int, bytes, Optional[float]]:
    """(width, height, samples per pixel, pixel bytes, no-data value) of an
    uncompressed, strip-organised, 8-bit TIFF. Anything else raises
    ValueError."""
    if data[:4] == b"II*\x00":
        e = "<"
    elif data[:4] == b"MM\x00*":
        e = ">"
    else:
        raise ValueError("not a TIFF")
    (ifd,) = struct.unpack(e + "I", data[4:8])
    (count,) = struct.unpack(e + "H", data[ifd:ifd + 2])
    sizes = {1: 1, 2: 1, 3: 2, 4: 4, 16: 8}
    tags: dict[int, list] = {}
    for i in range(count):
        off = ifd + 2 + 12 * i
        tag, typ, n = struct.unpack(e + "HHI", data[off:off + 8])
        size = sizes.get(typ, 1) * n
        raw = data[off + 8:off + 8 + size] if size <= 4 else data[
            struct.unpack(e + "I", data[off + 8:off + 12])[0]:][:size]
        if typ == 3:
            tags[tag] = list(struct.unpack(e + f"{n}H", raw))
        elif typ == 4:
            tags[tag] = list(struct.unpack(e + f"{n}I", raw))
        elif typ == 2:
            tags[tag] = [raw.rstrip(b"\x00").decode("ascii", "replace")]
        else:
            tags[tag] = list(raw)
    width, height = tags[256][0], tags[257][0]
    if tags.get(259, [1])[0] != 1:
        raise ValueError("compressed TIFF")
    if any(b != 8 for b in tags.get(258, [8])):
        raise ValueError("not 8-bit")
    spp = tags.get(277, [1])[0]
    pixels = b"".join(data[o:o + c] for o, c in zip(tags[273], tags[279]))
    if len(pixels) < width * height * spp:
        raise ValueError("short TIFF")
    nodata = None
    if 42113 in tags:
        try:
            nodata = float(tags[42113][0])
        except ValueError:
            nodata = None
    return width, height, spp, pixels[:width * height * spp], nodata


# --- fetching --------------------------------------------------------------------------

def _get_layer(client, layer: str, year: int, block: Block) -> list[Optional[int]]:
    """The layer over the block as a row-major list of values (None = no data).
    Land cover comes back as colours and is mapped to class codes."""
    params = {
        "service": "WMS", "version": "1.1.1", "request": "GetMap",
        "layers": layer, "styles": "", "srs": "EPSG:4326",
        "bbox": f"{block.west:.4f},{block.south:.4f},{block.east:.4f},{block.north:.4f}",
        "width": str(SIZE), "height": str(SIZE), "format": "image/geotiff",
        "time": f"{year}-01-01T00:00:00.000Z",
    }
    resp = client.get(f"{GEOSERVER}/mrlc_{layer}/wms", params=params,
                      coords={"bbox": Coord.BBOX}, source_key=SOURCE_KEY)
    if not resp.headers.get("content-type", "").startswith("image"):
        raise SourceUnavailable(SOURCE_KEY, f"{layer}: not an image ({resp.text[:120]!r})")
    try:
        w, h, spp, px, nodata = read_tiff(resp.content)
    except (ValueError, KeyError, struct.error) as exc:
        raise SourceUnavailable(SOURCE_KEY, f"{layer}: {exc}") from None
    out: list[Optional[int]] = []
    if spp >= 3:
        for i in range(w * h):
            p = px[i * spp:(i + 1) * spp]
            if spp == 4 and p[3] == 0:
                out.append(None)
            else:
                out.append(_BY_COLOUR.get((p[0], p[1], p[2])))
    else:
        for v in px:
            out.append(None if (nodata is not None and v == nodata) or v > 100 else v)
    return out


def fetch_block(client, block: Block) -> dict:
    return {
        "size": SIZE,
        "land_cover": _get_layer(client, LAYERS["land_cover"], YEAR, block),
        "land_cover_previous": _get_layer(client, LAYERS["land_cover"], PREVIOUS_YEAR, block),
        "land_cover_1985": _get_layer(client, LAYERS["land_cover"], HISTORY_YEAR, block),
        "impervious": _get_layer(client, LAYERS["impervious"], YEAR, block),
        "canopy": _get_layer(client, LAYERS["canopy"], YEAR, block),
    }


def load_block(block: Block, *, client, session=None) -> dict:
    if session is None:
        return fetch_block(client, block)
    key = f"{block.key}_nlcd"
    cached = tiles.get_json(session, SOURCE_KEY, CACHE_VERSION, key)
    if cached is not None:
        return cached
    data = fetch_block(client, block)
    tiles.put_json(session, SOURCE_KEY, CACHE_VERSION, key, data, ttl=TTL)
    return data


# --- sampling on this server -----------------------------------------------------------

def _footprint_mask(block: Block, size: int, pin, footprint: dict | None) -> list[int]:
    """Indexes of pixels whose centres fall inside the footprint's box, or
    the pixel under the pin when none do."""
    box = None
    if footprint and footprint.get("type") == "Polygon":
        ring = footprint["coordinates"][0]
        box = (min(p[0] for p in ring), min(p[1] for p in ring),
               max(p[0] for p in ring), max(p[1] for p in ring))
    dx = (block.east - block.west) / size
    dy = (block.north - block.south) / size
    idx = []
    if box:
        for r in range(size):
            y = block.north - (r + 0.5) * dy
            if not (box[1] <= y <= box[3]):
                continue
            for c in range(size):
                x = block.west + (c + 0.5) * dx
                if box[0] <= x <= box[2]:
                    idx.append(r * size + c)
    if not idx:
        lat, lng = pin
        c = min(size - 1, max(0, int((lng - block.west) / dx)))
        r = min(size - 1, max(0, int((block.north - lat) / dy)))
        idx = [r * size + c]
    return idx


def _mix(values: list[Optional[int]]) -> tuple[list[dict], int]:
    known = [v for v in values if v is not None]
    counts: dict[int, int] = {}
    for v in known:
        counts[v] = counts.get(v, 0) + 1
    total = len(known)
    mix = [{"code": code, "name": CLASSES[code][0] if code in CLASSES else "Unclassified",
            "percent": round(100 * n / total)}
           for code, n in sorted(counts.items(), key=lambda kv: -kv[1])] if total else []
    return mix, total


def _mean(values: list[Optional[int]]) -> Optional[float]:
    known = [v for v in values if v is not None]
    return round(sum(known) / len(known), 1) if known else None


def read(block: Block, pin: tuple[float, float], footprint: dict | None, *,
         client, session=None) -> list[Reading]:
    """`land_cover` and `tree_cover` for the block (neighbourhood context)."""
    data = load_block(block, client=client, session=session)
    return readings_from(data, block, pin, footprint)


def readings_from(data: dict, block: Block, pin, footprint) -> list[Reading]:
    size = data["size"]
    mix, known = _mix(data["land_cover"])
    if not known:
        return [Reading(field=f, value=None, level="unknown", provenance="public_map",
                        source_key=SOURCE_KEY, source_version=v, method=METHOD,
                        reason_codes=("outside_coverage",),
                        detail={"coverage": "contiguous United States"})
                for f, v in (("land_cover", SOURCE_VERSION), ("tree_cover", CANOPY_VERSION))]

    prev_mix, _ = _mix(data.get("land_cover_previous") or [])
    old_mix, _ = _mix(data.get("land_cover_1985") or [])
    dominant = mix[0]["code"]
    years_disagree = bool(prev_mix) and prev_mix[0]["code"] != dominant
    paved = _mean(data["impervious"])
    developed = sum(m["percent"] for m in mix if m["code"] in DEVELOPED)
    developed_1985 = sum(m["percent"] for m in old_mix if m["code"] in DEVELOPED)
    codes = ("neighbourhood_only",) + (("years_disagree",) if years_disagree else ())
    cell_m = round((block.north - block.south) * 111_320 / size, 1)

    land = Reading(
        field="land_cover",
        value={"dominant": {"code": dominant, "name": mix[0]["name"]},
               "classes": mix, "paved_percent": paved, "developed_percent": developed},
        level="low" if years_disagree else "medium",
        provenance="public_map", source_key=SOURCE_KEY, source_version=SOURCE_VERSION,
        method=METHOD, reason_codes=codes,
        detail={"year": YEAR, "previous_year": PREVIOUS_YEAR,
                "previous_dominant": prev_mix[0] if prev_mix else None,
                "history_year": HISTORY_YEAR, "developed_percent_1985": developed_1985,
                "classes_1985": old_mix, "native_cell_m": 30,
                "sample_pixel_m": cell_m, "window": "the snapped block, about 500 metres across"})

    block_canopy = _mean(data["canopy"])
    near = [data["canopy"][i] for i in _footprint_mask(block, size, pin, footprint)]
    tree = Reading(
        field="tree_cover",
        value=None if block_canopy is None else {"percent": block_canopy},
        level="unknown" if block_canopy is None else "medium",
        provenance="public_map", source_key=SOURCE_KEY, source_version=CANOPY_VERSION,
        method=METHOD,
        reason_codes=("neighbourhood_only",) if block_canopy is not None else ("no_data",),
        detail={"year": YEAR, "native_cell_m": 30,
                "footprint_percent": _mean(near),
                "footprint_note": "30 metre cells rarely line up with a lot; "
                                  "a coarse fallback for shade, not a lot value"})
    return [land, tree]
