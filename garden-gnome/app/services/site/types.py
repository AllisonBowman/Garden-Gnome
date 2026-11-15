"""Shapes shared by every site source (build spec section 3).

B1 writes these; no other package changes their fields without saying so in
its report. A source module exposes

    read(block: Block, pin: tuple[float, float], footprint: dict | None,
         *, client) -> list[Reading]

It fetches by block (through `tiles`, with `http.OutboundClient` as
`client`), samples at the pin or over the footprint on this server, raises
`SourceUnavailable` when the service fails, and returns a Reading with level
"unknown" when the service answers but has no data there.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

#: Every field a Reading may carry.
READING_FIELDS: tuple[str, ...] = (
    "hardiness_zone",
    "soil_mapunit",
    "soil_drainage_class",
    "soil_slowest_layer",
    "soil_runoff_group",
    "soil_texture",
    "soil_water_holding",
    "soil_ph",
    "soil_disturbed_share",
    "soil_flooding",
    "soil_ponding",
    "soil_water_table",
    "land_cover",
    "tree_cover",
    "elevation_window",
    "slope",
    "facing",
    "low_spot",
    "canopy_shade",
    "open_sky_sun",
    "sun_estimate",
    "water_collects",
)

LEVELS: tuple[str, ...] = ("high", "medium", "low", "unknown")
PROVENANCES: tuple[str, ...] = ("public_map", "modelled", "default")


class SourceUnavailable(Exception):
    """A public service failed to answer (network, timeout, server error, a
    body that could not be read). Not raised for "answered, but no data
    here": that is a Reading with level "unknown"."""

    def __init__(self, source_key: str, detail: str = ""):
        self.source_key = source_key
        self.detail = detail
        super().__init__(f"{source_key} unavailable" + (f": {detail}" if detail else ""))


@dataclass(frozen=True)
class Reading:
    field: str            # one of READING_FIELDS
    value: Any            # JSON-serialisable
    level: str            # "high" | "medium" | "low" | "unknown"
    provenance: str       # "public_map" | "modelled" | "default"
    source_key: str       # e.g. "ssurgo", "3dep", "nlcd", "phzm2023", "naip", "canopy"
    source_version: str
    method: str
    reason_codes: tuple[str, ...] = ()
    detail: dict | None = None   # extra numbers the copy needs (shares, resolution, months)

    def __post_init__(self):
        if self.field not in READING_FIELDS:
            raise ValueError(f"unknown reading field {self.field!r}")
        if self.level not in LEVELS:
            raise ValueError(f"unknown reading level {self.level!r}")
        if self.provenance not in PROVENANCES:
            raise ValueError(f"unknown reading provenance {self.provenance!r}")


@dataclass(frozen=True)
class Block:              # the grid-snapped area sent to outside services
    key: str              # text, never floating point
    west: float
    south: float
    east: float
    north: float
