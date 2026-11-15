"""Top-down aerial image of the snapped block (build spec sections 4 and 6).

Source: the National Agriculture Imagery Program (NAIP), aerial photography
flown for the United States Department of Agriculture Farm Service Agency
and served by the United States Geological Survey National Map image
service. Public domain.

Privacy: the service is sent the block's bounds only (`bbox` in degrees,
`bboxSR=4326`); the picture comes back in Web Mercator (`imageSR=3857`), whose
pixels are square on the ground. Over a block about 500 metres across the
north-south stretch of Web Mercator is under a tenth of a pixel, so the app
can map pixels to latitude and longitude linearly from `bounds`.

Pixel size, by measurement at the two test points on 2026-11-15: the
block is about 520 by 557 metres (Arboretum) and 577 by 557 metres
(Zilker). A long side of 1024 pixels is 0.54 to 0.56 metres a pixel at 140
to 162 KB; 1280 pixels is about 0.43 to 0.45 metres at about 217 KB
(Zilker); 1600 pixels is 0.35 to 0.36 metres at 264 to 444 KB. The
photography itself is 0.6 metres (Texas, 2022) or 0.3 metres (Maryland,
2023), so 1280 keeps the detail of the 0.6 metre states, keeps most of the
0.3 metre ones, and stays near 200 to 300 KB for a phone. Planting beds a
metre or two across span about 2 to 5 pixels.

The image service is slow on a cold request (12 to 61 seconds at the test
points, with read timeouts and gateway errors that the service then
repeats for a while), so an image is kept a year in the tile cache.
The capture date comes from a separate, slower catalog query, made only by
`read` (the background step); `block_imagery` reports it when the
background step has already found it.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.models.schemas import Box, ImageryOut, LatLng, SourceOut
from app.services.site import grid, tiles
from app.services.site.http import Coord
from app.services.site.types import Block, Reading, SourceUnavailable

SOURCE_KEY = "naip"
LONG_SIDE_PX = 1280
JPEG_QUALITY = 75
CACHE_VERSION = f"usgs-naip-{LONG_SIDE_PX}"
TTL = timedelta(days=365)
SERVICE = "https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer"
SOURCE_NAME = ("National Agriculture Imagery Program aerial photography, United States "
               "Department of Agriculture, through the United States Geological Survey "
               "National Map")
SOURCE_DETAIL = "Public domain. Shows the area around your pin, about 500 metres across."
SOURCE_URL = "https://www.usgs.gov/centers/eros/science/usgs-eros-archive-aerial-photography-national-agriculture-imagery-program-naip"
SUFFIX = "_naip"
META_SUFFIX = "_naipmeta"


def tile_key(block: Block) -> str:
    return f"{block.key}{SUFFIX}"


def _merc_y(lat: float) -> float:
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def image_size(block: Block, long_side: int = LONG_SIDE_PX) -> tuple[int, int]:
    """Width and height whose ratio matches the block in Web Mercator, so
    the service does not widen the area to fit the picture."""
    w = math.radians(block.east - block.west)
    h = _merc_y(block.north) - _merc_y(block.south)
    if w >= h:
        return long_side, max(1, round(long_side * h / w))
    return max(1, round(long_side * w / h)), long_side


def fetch_jpeg(client, block: Block) -> bytes:
    width, height = image_size(block)
    params = {
        "f": "image",
        "bbox": f"{block.west:.4f},{block.south:.4f},{block.east:.4f},{block.north:.4f}",
        "bboxSR": "4326", "imageSR": "3857",
        "size": f"{width},{height}", "format": "jpg",
        "compressionQuality": str(JPEG_QUALITY),
    }
    resp = client.get(f"{SERVICE}/exportImage", params=params,
                      coords={"bbox": Coord.BBOX},
                      not_coordinates=("size", "compressionQuality"),
                      source_key=SOURCE_KEY)
    body = resp.content
    if not body.startswith(b"\xff\xd8"):
        # The service answers errors as JSON with status 200.
        raise SourceUnavailable(SOURCE_KEY, f"not a JPEG: {body[:120]!r}")
    return body


def fetch_captured(client, block: Block) -> Optional[str]:
    """The capture date of the photography covering the block: one date, a
    range when several flights cover it, or None when the catalog says
    nothing. Slow (12 to 30 seconds measured)."""
    envelope = {"xmin": round(block.west, 4), "ymin": round(block.south, 4),
                "xmax": round(block.east, 4), "ymax": round(block.north, 4),
                "spatialReference": {"wkid": 4326}}
    resp = client.get(f"{SERVICE}/query", params={
        "f": "json", "geometry": json.dumps(envelope),
        "geometryType": "esriGeometryEnvelope", "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects", "where": "Category=1",
        "outFields": "Year,acquisition_date", "returnGeometry": "false",
        "orderByFields": "Year DESC",
    }, coords={"geometry": Coord.BBOX}, source_key=SOURCE_KEY)
    try:
        features = resp.json().get("features", [])
    except ValueError:
        raise SourceUnavailable(SOURCE_KEY, "unreadable catalog answer") from None
    dates = sorted({
        datetime.fromtimestamp(f["attributes"]["acquisition_date"] / 1000, tz=timezone.utc)
        .date().isoformat()
        for f in features
        if isinstance(f.get("attributes", {}).get("acquisition_date"), (int, float))})
    if not dates:
        return None
    # The newest year is what the service shows on top.
    newest_year = dates[-1][:4]
    dates = [d for d in dates if d.startswith(newest_year)]
    return dates[0] if len(dates) == 1 else f"{dates[0]} to {dates[-1]}"


def _meta(session, block: Block) -> dict:
    return tiles.get_json(session, SOURCE_KEY, CACHE_VERSION, f"{block.key}{META_SUFFIX}") or {}


def _put_meta(session, block: Block, meta: dict) -> None:
    tiles.put_json(session, SOURCE_KEY, CACHE_VERSION, f"{block.key}{META_SUFFIX}", meta, ttl=TTL)


def _jpeg(session, block: Block, client) -> bytes:
    key = tile_key(block)
    cached = tiles.get(session, SOURCE_KEY, CACHE_VERSION, key)
    if cached is not None:
        return cached
    body = fetch_jpeg(client, block)
    tiles.put(session, SOURCE_KEY, CACHE_VERSION, key, body, ttl=TTL)
    return body


def block_imagery(session, block: Block, pin: tuple[float, float],
                  footprint: dict | None, *, client) -> ImageryOut:
    """The route's entry point. Raises SourceUnavailable when the image
    service fails and nothing is cached (the route answers 503)."""
    _jpeg(session, block, client)
    width, height = image_size(block)
    meta = _meta(session, block)
    lat, lng = pin
    fp = grid.polygon_box(footprint) if footprint else None
    if fp is None:
        fp = grid.default_footprint_box(lat, lng)
    key = tile_key(block)
    return ImageryOut(
        tile_key=key, image_path=f"/imagery/tiles/{key}.jpg",
        width=width, height=height, bounds=Box(**grid.block_box(block)),
        source=SourceOut(name=SOURCE_NAME, detail=SOURCE_DETAIL,
                         version=meta.get("captured"), url=SOURCE_URL),
        captured=meta.get("captured"),
        pin=LatLng(lat=lat, lng=lng), default_footprint=Box(**fp))


def tile_jpeg(session, key: str) -> bytes | None:
    """The cached bytes for an image path, or None (the route answers 404).
    Only aerial image tiles are served."""
    if not key.endswith(SUFFIX) or grid.block_key_prefix(key) is None:
        return None
    return tiles.get(session, SOURCE_KEY, CACHE_VERSION, key)


def read(block: Block, pin: tuple[float, float], footprint: dict | None, *,
         client, session=None) -> list[Reading]:
    """The background step: make sure the image is cached and find its
    capture date. Returns no readings (no site value comes from the image).
    Without a session there is nowhere to keep either, so it does nothing.
    A failed capture-date lookup is not an error: the date stays unknown."""
    if session is None:
        return []
    _jpeg(session, block, client)
    meta = _meta(session, block)
    if "captured" not in meta:
        try:
            meta["captured"] = fetch_captured(client, block)
        except SourceUnavailable:
            return []
        _put_meta(session, block, meta)
    return []
