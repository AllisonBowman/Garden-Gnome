"""Slope, facing, low spots and flow paths from the elevation window
(build spec section 5; PLAN.md section 6, "Slope" and "Facing direction").

The maths are pure functions on numpy arrays, tested on synthetic surfaces:

    horn_gradient(z, dx, dy)             -> (dz/d east, dz/d north)
    slope_aspect(z, dx, dy)              -> (slope degrees, downslope azimuth)
    fill_and_route(z, valid)             -> (filled, receiver, order)
    flow_accumulation(receiver, order)   -> cells draining through each cell
    footprint_mask(...)                  -> cells in a box, minus the pin radius
    summarise(window, box, pin)          -> Summary for one footprint

`read(block, pin, footprint, *, client, session, readings)` turns a Summary
into the slope, facing and low_spot readings for one footprint: the
whole-lot default square or an owner box. The 10 metre radius around the pin
is left out everywhere (the pin is usually on the house, and a bare-earth
survey only interpolates the ground under a building).

Depressions and flow use one priority flood (Barnes, Lehman and Mulla 2014):
cells are taken from the outer edge inward, lowest first; a cell lower than
the one that reached it is raised to that level (that is the fill), and the
cell that reached it is where its water goes. So every cell drains to the
edge of the window, across filled flats too, and accumulation is one pass in
reverse order.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

from app.services.site import grid
from app.services.site.sources import elevation
from app.services.site.types import Block, Reading

#: The pin radius left out of every terrain value (PLAN.md section 6).
PIN_RADIUS_M = 10.0
#: Facing has no direction below this slope (PLAN.md section 6).
FLAT_DEGREES = 2.0
#: A low spot counts when filled water would stand at least this deep...
LOW_SPOT_DEPTH_M = 0.10
#: ...over at least this much of the footprint (engineering defaults).
LOW_SPOT_AREA_M2 = 4.0
#: Runoff from at least this much ground gathering in the footprint counts as
#: a flow path (engineering default: about a fifth of a hectare).
FLOW_CATCHMENT_M2 = 2000.0
#: Elevation coarser than this gives no water reading (PLAN.md section 6).
WATER_MAX_RESOLUTION_M = 3.5
#: A footprint this close to the default square is the default square.
_DEFAULT_TOLERANCE_DEG = 2e-6

_COMPASS = ("north", "north_east", "east", "south_east", "south", "south_west",
            "west", "north_west")


# --- footprints ------------------------------------------------------------------

def footprint_box(pin: tuple[float, float], footprint) -> tuple[dict, bool]:
    """(box, is_default) for a footprint given as None (the default square),
    a GeoJSON Polygon, or a Box dict {west, south, east, north}."""
    default = grid.default_footprint_box(*pin)
    if footprint is None:
        return default, True
    if isinstance(footprint, dict) and footprint.get("type") == "Polygon":
        box = grid.polygon_box(footprint)
    elif isinstance(footprint, dict) and {"west", "south", "east", "north"} <= set(footprint):
        box = {k: float(footprint[k]) for k in ("west", "south", "east", "north")}
    else:
        raise ValueError("a footprint is a GeoJSON Polygon or a box")
    if box is None:
        return default, True
    same = all(abs(box[k] - default[k]) <= _DEFAULT_TOLERANCE_DEG for k in default)
    return box, same


def box_area_m2(box: dict) -> float:
    return grid.box_area_sqft(box) * 0.09290304


# --- gradients ---------------------------------------------------------------------

def horn_gradient(z: np.ndarray, dx: float, dy: float) -> tuple[np.ndarray, np.ndarray]:
    """Horn's 3 by 3 gradient. Row 0 is north, column 0 is west. Returns
    (rise per metre east, rise per metre north); edge cells copy their
    neighbour's stencil by padding with the edge value."""
    p = np.pad(z.astype(np.float64), 1, mode="edge")
    a, b, c = p[:-2, :-2], p[:-2, 1:-1], p[:-2, 2:]
    d, f = p[1:-1, :-2], p[1:-1, 2:]
    g, h, i = p[2:, :-2], p[2:, 1:-1], p[2:, 2:]
    dzdx = ((c + 2 * f + i) - (a + 2 * d + g)) / (8 * dx)
    dzdy = ((a + 2 * b + c) - (g + 2 * h + i)) / (8 * dy)   # north is up (row 0)
    return dzdx, dzdy


def slope_aspect(z: np.ndarray, dx: float, dy: float) -> tuple[np.ndarray, np.ndarray]:
    """Slope in degrees and facing as the downslope azimuth (0 north,
    clockwise), per cell."""
    gx, gy = horn_gradient(z, dx, dy)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    aspect = (np.degrees(np.arctan2(-gx, -gy)) + 360.0) % 360.0
    return slope, aspect


def compass(azimuth: float) -> str:
    return _COMPASS[int(((azimuth % 360) + 22.5) // 45) % 8]


# --- depressions and flow ----------------------------------------------------------

def fill_and_route(z: np.ndarray, valid: Optional[np.ndarray] = None
                   ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Priority flood. Returns (filled heights, receiver index per cell or -1
    for an outlet, the order cells were taken). Cells outside `valid` are
    outlets, like the window edge."""
    rows, cols = z.shape
    n = rows * cols
    zf = z.astype(np.float64).ravel().copy()
    ok = np.ones(n, bool) if valid is None else valid.ravel().astype(bool)
    receiver = np.full(n, -1, dtype=np.int64)
    done = np.zeros(n, dtype=bool)
    order = np.empty(n, dtype=np.int64)
    heap: list[tuple[float, int, int]] = []
    seq = 0
    edge = np.zeros((rows, cols), bool)
    edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
    seeds = np.flatnonzero(edge.ravel() | ~ok)
    for k in seeds:
        done[k] = True
        if not ok[k]:
            zf[k] = -np.inf
        heap.append((zf[k], seq, int(k)))
        seq += 1
    heapq.heapify(heap)
    offs = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
    zl = zf.tolist()
    donel = done.tolist()
    recl = receiver.tolist()
    taken = 0
    orderl = [0] * n
    push, pop = heapq.heappush, heapq.heappop
    while heap:
        h, _, k = pop(heap)
        orderl[taken] = k
        taken += 1
        r, c = divmod(k, cols)
        for dr, dc in offs:
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < cols:
                m = rr * cols + cc
                if not donel[m]:
                    donel[m] = True
                    recl[m] = k
                    if zl[m] < h:
                        zl[m] = h
                    seq += 1
                    push(heap, (zl[m], seq, m))
    filled = np.array(zl).reshape(rows, cols)
    filled = np.where(np.isfinite(filled), filled, z)
    order[:] = orderl
    return filled, np.array(recl, dtype=np.int64), order


def flow_accumulation(receiver: np.ndarray, order: np.ndarray) -> np.ndarray:
    """How many cells drain through each cell, itself included."""
    acc = np.ones(receiver.size, dtype=np.float64)
    rec = receiver.tolist()
    accl = acc.tolist()
    for k in order[::-1].tolist():
        r = rec[k]
        if r >= 0:
            accl[r] += accl[k]
    return np.array(accl)


# --- one footprint ------------------------------------------------------------------

def footprint_mask(shape: tuple[int, int], block: Block, box: dict,
                   pin: tuple[float, float], *,
                   exclude_radius_m: float = PIN_RADIUS_M) -> np.ndarray:
    """Cells whose centre is inside `box` and more than the pin radius away
    from the pin."""
    rows, cols = shape
    dlat = (block.north - block.south) / rows
    dlng = (block.east - block.west) / cols
    lat = block.north - (np.arange(rows) + 0.5) * dlat
    lng = block.west + (np.arange(cols) + 0.5) * dlng
    inside = ((lat >= box["south"]) & (lat <= box["north"]))[:, None] & \
             ((lng >= box["west"]) & (lng <= box["east"]))[None, :]
    if exclude_radius_m > 0:
        mid = math.radians((block.south + block.north) / 2)
        ny = (lat - pin[0]) * elevation.M_PER_DEG_LAT
        nx = (lng - pin[1]) * elevation.M_PER_DEG_LAT * math.cos(mid)
        inside &= (ny[:, None] ** 2 + nx[None, :] ** 2) > exclude_radius_m ** 2
    return inside


@dataclass(frozen=True)
class Analysis:
    """Whole-window results, computed once per window."""
    slope: np.ndarray
    aspect: np.ndarray
    gx: np.ndarray
    gy: np.ndarray
    depth: np.ndarray        # filled minus ground, metres
    accumulation_m2: np.ndarray
    edge_catchment: np.ndarray  # True where the catchment reaches the window edge


#: Recent analyses, each kept with its window so an identity check is safe.
_ANALYSES: list[tuple[elevation.ElevationWindow, Analysis]] = []


def analyse(z: np.ndarray, valid: np.ndarray, dx: float, dy: float) -> Analysis:
    gx, gy = horn_gradient(z, dx, dy)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    aspect = (np.degrees(np.arctan2(-gx, -gy)) + 360.0) % 360.0
    filled, receiver, order = fill_and_route(z, valid)
    depth = np.where(valid, filled - z, 0.0)
    acc = flow_accumulation(receiver, order).reshape(z.shape)
    # Catchments that start at the window edge are cut off there (ground
    # beyond it may drain in too): mark every cell downstream of a cell next
    # to the edge. The edge cells themselves are outlets.
    rows, cols = z.shape
    e2 = np.zeros((rows, cols), bool)
    if rows > 2 and cols > 2:
        e2[1, 1:-1] = e2[-2, 1:-1] = e2[1:-1, 1] = e2[1:-1, -2] = True
    edgel = e2.ravel().tolist()
    rec = receiver.tolist()
    for k in order[::-1].tolist():
        if edgel[k] and rec[k] >= 0:
            edgel[rec[k]] = True
    return Analysis(slope=slope, aspect=aspect, gx=gx, gy=gy, depth=depth,
                    accumulation_m2=acc * dx * dy,
                    edge_catchment=np.array(edgel).reshape(z.shape))


def analyse_window(win: elevation.ElevationWindow) -> Analysis:
    for w, a in _ANALYSES:
        if w is win:
            return a
    a = analyse(win.z, win.valid, win.dx_m, win.dy_m)
    _ANALYSES.append((win, a))
    if len(_ANALYSES) > 4:
        _ANALYSES.pop(0)
    return a


@dataclass(frozen=True)
class Summary:
    cells: int
    area_m2: float
    slope_deg: Optional[float]          # median cell slope
    slope_percent: Optional[float]
    plane_slope_deg: Optional[float]    # slope of the mean gradient
    facing_deg: Optional[float]         # None when flat
    facing_consistency: Optional[float]  # 0..1, 1 = every cell faces one way
    low_depth_max_m: float
    low_area_m2: float
    catchment_max_m2: float
    catchment_reaches_edge: bool
    excluded_pin: bool


def summarise_arrays(a: Analysis, mask: np.ndarray, valid: np.ndarray,
                     dx: float, dy: float, *, excluded_pin: bool = True) -> Summary:
    m = mask & valid
    cells = int(m.sum())
    if cells == 0:
        return Summary(0, 0.0, None, None, None, None, None, 0.0, 0.0, 0.0, False,
                       excluded_pin)
    s = a.slope[m]
    med = float(np.median(s))
    gx, gy = float(a.gx[m].mean()), float(a.gy[m].mean())
    plane = math.degrees(math.atan(math.hypot(gx, gy)))
    mags = np.hypot(a.gx[m], a.gy[m])
    consistency = float(math.hypot(gx, gy) / mags.mean()) if mags.mean() > 0 else 0.0
    facing = None
    if plane >= FLAT_DEGREES:
        facing = (math.degrees(math.atan2(-gx, -gy)) + 360.0) % 360.0
    low = a.depth[m] >= LOW_SPOT_DEPTH_M
    cell_area = dx * dy
    acc = a.accumulation_m2[m]
    top = int(np.argmax(acc))
    return Summary(
        cells=cells, area_m2=cells * cell_area, slope_deg=med,
        slope_percent=100.0 * math.tan(math.radians(med)),
        plane_slope_deg=plane, facing_deg=facing, facing_consistency=consistency,
        low_depth_max_m=float(a.depth[m].max()), low_area_m2=float(low.sum() * cell_area),
        catchment_max_m2=float(acc[top]),
        catchment_reaches_edge=bool(a.edge_catchment[m][top]),
        excluded_pin=excluded_pin)


def summarise(win: elevation.ElevationWindow, box: dict, pin: tuple[float, float]) -> Summary:
    a = analyse_window(win)
    mask = footprint_mask(win.z.shape, win.block, box, pin)
    return summarise_arrays(a, mask, win.valid, win.dx_m, win.dy_m)


# --- readings --------------------------------------------------------------------------

def _level(resolution_m: Optional[float], is_default: bool, area_m2: float) -> str:
    level = elevation.resolution_level(resolution_m)
    if level == "high" and (is_default or area_m2 < 50.0):
        level = "medium"
    return level


def readings_for(win: elevation.ElevationWindow, box: dict, is_default: bool,
                 pin: tuple[float, float]) -> list[Reading]:
    """slope, facing and low_spot for one footprint."""
    s = summarise(win, box, pin)
    base = elevation.survey_detail(win)
    version = str(win.year) if win.year else "dynamic service"
    method = "horn_3x3_priority_flood"
    codes = ["pin_radius_left_out"] + (["default_footprint"] if is_default else [])
    if win.resolution_m is None:
        codes.append("resolution_unknown")
    if s.cells < 9:
        unknown = dict(field="slope", value=None, level="unknown", provenance="modelled",
                       source_key="3dep", source_version=version, method=method,
                       reason_codes=tuple(codes + ["too_little_ground"]), detail=base)
        return [Reading(**unknown), Reading(**{**unknown, "field": "facing"}),
                Reading(**{**unknown, "field": "low_spot"})]
    level = _level(win.resolution_m, is_default, s.area_m2)
    common = dict(provenance="modelled", source_key="3dep", source_version=version,
                  method=method)
    detail = {**base, "degrees": round(s.slope_deg, 1),
              "plane_degrees": round(s.plane_slope_deg, 1),
              "cells": s.cells, "area_m2": round(s.area_m2),
              "pin_radius_m": PIN_RADIUS_M, "default_footprint": is_default}
    out = [Reading(field="slope", value={"percent": round(s.slope_percent, 1),
                                         "degrees": round(s.slope_deg, 1)},
                   level=level, reason_codes=tuple(codes), detail=detail, **common)]
    if s.facing_deg is None:
        fv = {"direction": "flat", "degrees": None}
        f_level = level
        f_codes = codes + ["flat"]
    else:
        fv = {"direction": compass(s.facing_deg), "degrees": round(s.facing_deg)}
        f_level = level
        f_codes = list(codes)
        if (s.facing_consistency or 0) < 0.4:
            f_level = "low" if level != "unknown" else level
            f_codes.append("mixed_facing")
        elif s.plane_slope_deg < 3.0 and level == "high":
            f_level = "medium"
            f_codes.append("nearly_flat")
    out.append(Reading(field="facing", value=fv, level=f_level, reason_codes=tuple(f_codes),
                       detail={**detail, "consistency": round(s.facing_consistency or 0, 2)},
                       **common))
    out.append(low_spot_reading(win, s, level, codes, detail, common))
    return out


def low_spot_reading(win, s: Summary, level: str, codes: list, detail: dict,
                     common: dict) -> Reading:
    res = win.resolution_m
    d = {**detail, "max_depth_m": round(s.low_depth_max_m, 2),
         "low_area_m2": round(s.low_area_m2, 1),
         "catchment_m2": round(s.catchment_max_m2),
         "catchment_reaches_edge": s.catchment_reaches_edge,
         "depth_threshold_m": LOW_SPOT_DEPTH_M, "area_threshold_m2": LOW_SPOT_AREA_M2,
         "catchment_threshold_m2": FLOW_CATCHMENT_M2}
    if res is None or res > WATER_MAX_RESOLUTION_M:
        return Reading(field="low_spot", value=None, level="unknown",
                       reason_codes=tuple(codes + ["elevation_too_coarse_for_water"]),
                       detail=d, **common)
    low = s.low_area_m2 >= LOW_SPOT_AREA_M2
    flow = s.catchment_max_m2 >= FLOW_CATCHMENT_M2
    value = {"low_spot": low, "flow_path": flow,
             "max_depth_m": round(s.low_depth_max_m, 2),
             "catchment_m2": round(s.catchment_max_m2)}
    rc = list(codes) + (["low_spot"] if low else []) + (["flow"] if flow else [])
    if s.catchment_reaches_edge:
        rc.append("catchment_at_least")
    return Reading(field="low_spot", value=value, level=level, reason_codes=tuple(rc),
                   detail=d, **common)


def read(block: Block, pin: tuple[float, float], footprint, *, client, session=None,
         readings: Sequence[Reading] = ()) -> list[Reading]:
    """slope, facing and low_spot for the footprint, from the cached window
    (fetched if needed). Raises SourceUnavailable when there is no window."""
    win = elevation.load_window(session, block, client=client)
    if win.coverage() < 0.5:
        return []
    box, is_default = footprint_box(pin, footprint)
    return readings_for(win, box, is_default, pin)
