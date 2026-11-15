"""Overhanging features: tree canopy height over the snapped block (build
spec section 5, step 3).

Source chosen (proved at both test landmarks on 2026-11-15; see
docs/design/2026-11-15-sun-and-drainage-sources.md): the Meta and World
Resources Institute High Resolution Canopy Height Maps, version 2, on the
Amazon Web Services Registry of Open Data. Tree height in whole metres at
about 1.19 metres in Web Mercator (about 0.93 metres on the ground at
Washington, 1.03 at Austin), made by a machine-learning model from satellite
imagery. Licence: Creative Commons Attribution 4.0; attribution "Meta and
World Resources Institute".

Each file is a tiled GeoTIFF covering one zoom-10 Web Mercator tile (about
39 kilometres): 32768 by 32768 pixels in 512 by 512 tiles, deflate
compressed. We read it with plain HTTP range requests: the first 64
kilobytes (the directory, the same for every block), then only the internal
tiles that the block's bounds touch. The file name (the zoom-10 tile) and
the byte ranges depend only on the block, so nothing finer than the snap
grid is revealed. The reader below is about 60 lines of standard-library
Python plus numpy; no imaging library is needed.

Not read, and why (also in the design note): building footprints with
heights (Overture Maps) need a Parquet reader, outside the dependency rule;
a first-return surface from the laser survey needs the point cloud tools;
neither is counted, so "buildings are not counted" is always said. The
coarse fallback, the tree cover percentage, comes from B2a's land cover
source as a `tree_cover` reading and is used by `sun` when this source
fails.
"""
from __future__ import annotations

import math
import struct
import zlib
from dataclasses import dataclass, field as dc_field
from datetime import timedelta
from typing import Optional, Sequence

import numpy as np

from app.services.site import tiles
from app.services.site.types import Block, Reading, SourceUnavailable

SOURCE_KEY = "canopy"
PROVIDER = "meta_wri_chm"
DATASET_VERSION = "chm-v2-ml3-lattice-1e-5deg-v1"
SOURCE_VERSION = "v2 (dinov3_global_chm_v2_ml3)"
SOURCE_NAME = "Meta and World Resources Institute High Resolution Canopy Height Maps"
SOURCE_DETAIL = "Tree canopy height from satellite imagery, version 2"
SOURCE_URL = "https://registry.opendata.aws/dataforgood-fb-forestsv2/"
LICENCE = "Creative Commons Attribution 4.0"
BASE = ("https://dataforgood-fb-data.s3.amazonaws.com/forests/v2/global/"
        "dinov3_global_chm_v2_ml3/chm")

#: Pixels in one file and one internal tile, and the file's zoom level.
FILE_ZOOM = 10
FILE_PX = 32768
TILE_PX = 512
_PX_ZOOM = FILE_ZOOM + 15           # 2**15 pixels per zoom-10 tile
_R = 6378137.0
_WORLD = 2 * math.pi * _R
PIXEL_M = _WORLD / 2 ** _PX_ZOOM    # 1.194 m in Web Mercator units
HEADER_BYTES = 65536
#: A pixel at least this tall counts as tree canopy (engineering default).
CANOPY_MIN_M = 2.0
STEP_DEG = 1e-5                     # the same lattice as the elevation window
TTL = timedelta(days=365)           # the map is a single edition


# --- Web Mercator ---------------------------------------------------------------

def global_px(lat: float, lng: float) -> tuple[float, float]:
    """(x, y) in zoom-25 pixels from the top-left of the world."""
    x = _R * math.radians(lng)
    y = _R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return (x + _WORLD / 2) / PIXEL_M, (_WORLD / 2 - y) / PIXEL_M


def quadkey(tx: int, ty: int, zoom: int = FILE_ZOOM) -> str:
    out = []
    for i in range(zoom, 0, -1):
        digit = 0
        mask = 1 << (i - 1)
        if tx & mask:
            digit += 1
        if ty & mask:
            digit += 2
        out.append(str(digit))
    return "".join(out)


def ground_resolution_m(lat: float) -> float:
    return PIXEL_M * math.cos(math.radians(lat))


# --- a minimal tiled-TIFF reader ---------------------------------------------------

_TYPES = {1: ("B", 1), 3: ("H", 2), 4: ("I", 4), 12: ("d", 8), 16: ("Q", 8)}


@dataclass
class TiffLayout:
    width: int
    height: int
    tile_w: int
    tile_h: int
    compression: int
    predictor: int
    bits: int
    offsets: list
    counts: list
    pending: dict = dc_field(default_factory=dict)   # tag -> (offset, count, fmt)


def parse_header(buf: bytes) -> TiffLayout:
    """The first image directory of a classic little- or big-endian TIFF.
    Arrays that lie beyond `buf` are left in `pending` for the caller."""
    if buf[:2] not in (b"II", b"MM"):
        raise ValueError("not a TIFF file")
    bo = "<" if buf[:2] == b"II" else ">"
    if struct.unpack(bo + "H", buf[2:4])[0] != 42:
        raise ValueError("not a classic TIFF file")
    (ifd,) = struct.unpack(bo + "I", buf[4:8])
    (n,) = struct.unpack(bo + "H", buf[ifd:ifd + 2])
    tags: dict = {}
    pending: dict = {}
    for i in range(n):
        e = buf[ifd + 2 + 12 * i: ifd + 14 + 12 * i]
        tag, typ, cnt = struct.unpack(bo + "HHI", e[:8])
        if typ not in _TYPES:
            continue
        fmt, size = _TYPES[typ]
        total = size * cnt
        if total <= 4:
            tags[tag] = list(struct.unpack(bo + fmt * cnt, e[8:8 + total]))
            continue
        (off,) = struct.unpack(bo + "I", e[8:12])
        if off + total <= len(buf):
            tags[tag] = list(struct.unpack(bo + fmt * cnt, buf[off:off + total]))
        else:
            pending[tag] = (off, cnt, bo + fmt)
    need = (256, 257, 322, 323)
    if any(t not in tags for t in need):
        raise ValueError("not a tiled TIFF file")
    return TiffLayout(width=tags[256][0], height=tags[257][0], tile_w=tags[322][0],
                      tile_h=tags[323][0], compression=tags.get(259, [1])[0],
                      predictor=tags.get(317, [1])[0], bits=tags.get(258, [8])[0],
                      offsets=tags.get(324, []), counts=tags.get(325, []),
                      pending=pending)


def decode_tile(raw: bytes, layout: TiffLayout) -> np.ndarray:
    if layout.bits != 8:
        raise ValueError("expected 8-bit heights")
    if layout.compression in (8, 32946):
        data = zlib.decompress(raw)
    elif layout.compression == 1:
        data = raw
    else:
        raise ValueError(f"unsupported TIFF compression {layout.compression}")
    a = np.frombuffer(data, dtype=np.uint8)[: layout.tile_w * layout.tile_h]
    a = a.reshape(layout.tile_h, layout.tile_w)
    if layout.predictor == 2:
        a = np.cumsum(a.astype(np.uint32), axis=1).astype(np.uint8)
    return a


# --- fetching ----------------------------------------------------------------------

def _range(client, url: str, start: int, end: int) -> bytes:
    r = client.get(url, headers={"Range": f"bytes={start}-{end}"}, source_key=SOURCE_KEY)
    body = r.content
    if r.status_code == 200 and len(body) > end - start + 1:
        body = body[start:end + 1]        # a server that ignores ranges
    if len(body) != end - start + 1:
        raise SourceUnavailable(SOURCE_KEY, f"short read {len(body)} of {end - start + 1}")
    return body


def _layout(client, url: str) -> TiffLayout:
    head = _range(client, url, 0, HEADER_BYTES - 1)
    try:
        layout = parse_header(head)
    except (ValueError, struct.error) as exc:
        raise SourceUnavailable(SOURCE_KEY, f"unreadable header: {exc}") from exc
    for tag, (off, cnt, fmt) in layout.pending.items():
        size = struct.calcsize(fmt)
        vals = list(struct.unpack(fmt[0] + fmt[1] * cnt,
                                  _range(client, url, off, off + size * cnt - 1)))
        if tag == 324:
            layout.offsets = vals
        elif tag == 325:
            layout.counts = vals
    if not layout.offsets or len(layout.offsets) != len(layout.counts):
        raise SourceUnavailable(SOURCE_KEY, "no tile directory")
    return layout


def block_tiles(block: Block) -> tuple[range, range]:
    """Global internal-tile columns and rows the block touches."""
    x0, y0 = global_px(block.north, block.west)
    x1, y1 = global_px(block.south, block.east)
    return (range(int(x0) // TILE_PX, int(x1) // TILE_PX + 1),
            range(int(y0) // TILE_PX, int(y1) // TILE_PX + 1))


def fetch_mosaic(block: Block, client) -> tuple[np.ndarray, int, int, dict]:
    """The internal tiles under the block, stitched. Returns (heights,
    first global pixel column, first global pixel row, measurements)."""
    cols, rows = block_tiles(block)
    per_file = FILE_PX // TILE_PX
    mosaic = np.zeros((len(rows) * TILE_PX, len(cols) * TILE_PX), dtype=np.uint8)
    layouts: dict[str, TiffLayout] = {}
    bytes_read = 0
    for j, gty in enumerate(rows):
        for i, gtx in enumerate(cols):
            fx, fy = gtx // per_file, gty // per_file
            name = quadkey(fx, fy)
            url = f"{BASE}/{name}.tif"
            if name not in layouts:
                layouts[name] = _layout(client, url)
                bytes_read += HEADER_BYTES
            lay = layouts[name]
            k = (gty % per_file) * (lay.width // lay.tile_w) + (gtx % per_file)
            off, cnt = lay.offsets[k], lay.counts[k]
            if cnt == 0:
                continue              # an empty tile: no canopy there
            raw = _range(client, url, off, off + cnt - 1)
            bytes_read += cnt
            try:
                tile = decode_tile(raw, lay)
            except (ValueError, zlib.error) as exc:
                raise SourceUnavailable(SOURCE_KEY, f"unreadable tile: {exc}") from exc
            mosaic[j * TILE_PX:(j + 1) * TILE_PX, i * TILE_PX:(i + 1) * TILE_PX] = tile
    return mosaic, cols.start * TILE_PX, rows.start * TILE_PX, {
        "files": sorted(layouts), "tiles": len(cols) * len(rows), "bytes": bytes_read}


def resample_to_lattice(mosaic: np.ndarray, px0: int, py0: int, block: Block) -> np.ndarray:
    """Nearest canopy pixel for every cell of the block's 0.00001 degree
    lattice (north row first). Web Mercator x depends on longitude only and y
    on latitude only, so the lookup is separable."""
    rows = int(round((block.north - block.south) / STEP_DEG))
    cols = int(round((block.east - block.west) / STEP_DEG))
    lats = block.north - (np.arange(rows) + 0.5) * (block.north - block.south) / rows
    lngs = block.west + (np.arange(cols) + 0.5) * (block.east - block.west) / cols
    ix = np.array([int(global_px(block.north, g)[0]) - px0 for g in lngs])
    iy = np.array([int(global_px(a, block.west)[1]) - py0 for a in lats])
    ix = np.clip(ix, 0, mosaic.shape[1] - 1)
    iy = np.clip(iy, 0, mosaic.shape[0] - 1)
    return mosaic[iy[:, None], ix[None, :]]


@dataclass(frozen=True)
class CanopyGrid:
    block: Block
    height_m: np.ndarray            # float32 metres on the elevation lattice
    resolution_m: float             # ground size of a source pixel
    meta: dict = dc_field(default_factory=dict)


def tile_key(block: Block) -> str:
    return f"{block.key}_chm"


def load_canopy(session, block: Block, *, client) -> CanopyGrid:
    """Canopy heights on the block's lattice, cached. Raises SourceUnavailable."""
    payload = None
    if session is not None:
        payload = tiles.get(session, PROVIDER, DATASET_VERSION, tile_key(block))
    if payload is None:
        mosaic, px0, py0, _ = fetch_mosaic(block, client)
        grid8 = resample_to_lattice(mosaic, px0, py0, block)
        payload = struct.pack("<HH", *grid8.shape) + grid8.tobytes()
        if session is not None:
            tiles.put(session, PROVIDER, DATASET_VERSION, tile_key(block), payload, ttl=TTL)
    rows, cols = struct.unpack("<HH", payload[:4])
    h = np.frombuffer(payload[4:4 + rows * cols], dtype=np.uint8).reshape(rows, cols)
    mid = (block.south + block.north) / 2
    return CanopyGrid(block=block, height_m=h.astype(np.float32),
                      # Whole metres: the owner reads "mapped at 1 metre detail".
                      resolution_m=float(max(1, round(ground_resolution_m(mid)))))


# --- the reading --------------------------------------------------------------------

def source_detail(grid_: CanopyGrid) -> dict:
    return {"source_name": SOURCE_NAME, "source_detail": SOURCE_DETAIL,
            "source_url": SOURCE_URL, "licence": LICENCE,
            "attribution": "Meta and World Resources Institute",
            "canopy_resolution_m": grid_.resolution_m, "kind": "canopy_height"}


def cover_stats(heights: np.ndarray, mask: np.ndarray) -> dict:
    h = heights[mask]
    if h.size == 0:
        return {"cover_share": None, "mean_height_m": None, "max_height_m": None}
    tree = h >= CANOPY_MIN_M
    return {"cover_share": round(float(tree.mean()), 3),
            "mean_height_m": round(float(h[tree].mean()), 1) if tree.any() else 0.0,
            "max_height_m": float(h.max())}


def read(block: Block, pin: tuple[float, float], footprint, *, client, session=None,
         readings: Sequence[Reading] = ()) -> list[Reading]:
    """canopy_shade: how much of the footprint is under tree canopy. The
    hours of shade it casts are worked out by `sun`, which supersedes this
    reading with its own canopy_shade (same field, hours added)."""
    from app.services.site import terrain   # local: terrain imports the sources
    g = load_canopy(session, block, client=client)
    box, is_default = terrain.footprint_box(pin, footprint)
    mask = terrain.footprint_mask(g.height_m.shape, block, box, pin, exclude_radius_m=0)
    stats = cover_stats(g.height_m, mask)
    codes = ("default_footprint",) if is_default else ()
    return [Reading(field="canopy_shade", value=stats, level="medium",
                    provenance="modelled", source_key=SOURCE_KEY,
                    source_version=SOURCE_VERSION, method="chm_cover_over_footprint",
                    reason_codes=codes, detail=source_detail(g))]
