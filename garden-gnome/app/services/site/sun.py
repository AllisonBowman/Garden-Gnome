"""The sun estimate (build spec section 5, "Sun estimate").

1. The sun's position through the growing season at the pin's latitude,
   every 10 minutes on every 7th day: the National Oceanic and Atmospheric
   Administration (NOAA) solar equations, after Meeus, "Astronomical
   Algorithms". Geometric elevation, no refraction.
2. For sample points spread over the footprint (leaving out the 10 metre
   radius around the pin), the horizon in 72 directions is found by walking
   outward over the elevation window: once over bare ground (the open-sky
   horizon), once over ground plus tree canopy height.
3. A time step counts as direct sun at a point when the sun is higher than
   that point's horizon in the sun's direction. Hours a day are averaged over
   the season and over the points.
4. Category: full sun (6 hours or more), part shade (3 to 6), shade (under 3).

When the canopy height map is not available, the tree cover percentage from
land cover (a `tree_cover` reading) is the coarse fallback: the open-sky
hours are reduced by that share. Buildings are never counted (no source
within the dependency rule; see the design note), so the estimate is never
above "Rough estimate" from public data, which the reading says.

    sun_position(when_utc, lat, lng) -> (elevation degrees, azimuth degrees)
    declination(when_utc), equation_of_time(when_utc), hour_angle(...)
    season_days(start, end, step_days) and season_from_normals(normals)
    horizons(surface, rows, cols, dx, dy, ...) -> horizon angles per direction
    estimate(...) -> Estimate
    read(block, pin, footprint, *, client, session, readings)
        -> [open_sky_sun, canopy_shade, sun_estimate]
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field as dc_field
from datetime import date, datetime, timedelta, timezone
from typing import Iterable, Optional, Sequence

import numpy as np

from app.services.site import terrain
from app.services.site.sources import canopy as canopy_source
from app.services.site.sources import elevation
from app.services.site.types import Block, Reading, SourceUnavailable

FULL_SUN_HOURS = 6.0
PART_SHADE_HOURS = 3.0
STEP_MINUTES = 10
DAY_STEP = 7
AZIMUTHS = 72                      # every 5 degrees
#: The eye height above the ground where sun is counted (a bed of plants).
OBSERVER_M = 0.5
#: Most sample points per footprint (a square lattice inside the box).
MAX_POINTS = 49
#: Canopy lower than this is not an obstacle (lawn, low shrubs, noise).
OBSTACLE_MIN_M = 1.0
#: How far the horizon walk goes. The pin is always at least half a cell
#: (about 125 metres) inside the block, so hills farther than that may lie
#: outside the window and are not counted.
HORIZON_M = 250.0
DEFAULT_SEASON = ((4, 1), (10, 31))   # April to October (build spec section 5)
METHOD = "noaa_sun_position_horizon_raymarch"
SOURCE_NAME = "Sun position calculation on our server"


# --- sun position (NOAA / Meeus) -----------------------------------------------------

def _julian_century(when: np.ndarray) -> np.ndarray:
    """`when` as seconds since 1970-01-01 UTC."""
    jd = when / 86400.0 + 2440587.5
    return (jd - 2451545.0) / 36525.0


def _solar_terms(jc: np.ndarray):
    L0 = np.mod(280.46646 + jc * (36000.76983 + jc * 0.0003032), 360.0)
    M = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    e = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    Mr = np.radians(M)
    C = (np.sin(Mr) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
         + np.sin(2 * Mr) * (0.019993 - 0.000101 * jc) + np.sin(3 * Mr) * 0.000289)
    true_long = L0 + C
    omega = np.radians(125.04 - 1934.136 * jc)
    app_long = true_long - 0.00569 - 0.00478 * np.sin(omega)
    mean_obliq = 23 + (26 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60) / 60
    obliq = mean_obliq + 0.00256 * np.cos(omega)
    decl = np.degrees(np.arcsin(np.sin(np.radians(obliq)) * np.sin(np.radians(app_long))))
    y = np.tan(np.radians(obliq / 2)) ** 2
    L0r = np.radians(L0)
    eot = 4 * np.degrees(y * np.sin(2 * L0r) - 2 * e * np.sin(Mr)
                         + 4 * e * y * np.sin(Mr) * np.cos(2 * L0r)
                         - 0.5 * y * y * np.sin(4 * L0r) - 1.25 * e * e * np.sin(2 * Mr))
    return decl, eot


def _seconds(when) -> np.ndarray:
    if isinstance(when, datetime):
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        return np.array(when.timestamp(), dtype=np.float64)
    return np.asarray(when, dtype=np.float64)


def declination(when) -> float:
    """The sun's declination in degrees."""
    return float(_solar_terms(_julian_century(_seconds(when)))[0])


def equation_of_time(when) -> float:
    """Apparent minus mean solar time, minutes."""
    return float(_solar_terms(_julian_century(_seconds(when)))[1])


def hour_angle(when, lng: float) -> float:
    """Degrees from local solar noon, negative in the morning."""
    s = _seconds(when)
    _, eot = _solar_terms(_julian_century(s))
    minutes = np.mod(s, 86400.0) / 60.0
    tst = np.mod(minutes + eot + 4.0 * lng, 1440.0)
    return float(tst / 4.0 - 180.0)


def sun_positions(seconds: np.ndarray, lat: float, lng: float) -> tuple[np.ndarray, np.ndarray]:
    """(elevation, azimuth clockwise from north) in degrees for UTC instants
    given as seconds since 1970."""
    s = np.asarray(seconds, dtype=np.float64)
    decl, eot = _solar_terms(_julian_century(s))
    minutes = np.mod(s, 86400.0) / 60.0
    tst = np.mod(minutes + eot + 4.0 * lng, 1440.0)
    ha = np.radians(tst / 4.0 - 180.0)
    phi, d = math.radians(lat), np.radians(decl)
    cos_z = np.clip(math.sin(phi) * np.sin(d) + math.cos(phi) * np.cos(d) * np.cos(ha), -1, 1)
    zen = np.arccos(cos_z)
    elev = 90.0 - np.degrees(zen)
    denom = math.cos(phi) * np.sin(zen)
    with np.errstate(invalid="ignore", divide="ignore"):
        cos_az = np.clip((math.sin(phi) * np.cos(zen) - np.sin(d)) / denom, -1, 1)
    acos = np.degrees(np.arccos(np.where(np.isfinite(cos_az), cos_az, 1.0)))
    az = np.where(ha > 0, np.mod(acos + 180.0, 360.0), np.mod(540.0 - acos, 360.0))
    return elev, az


def sun_position(when: datetime, lat: float, lng: float) -> tuple[float, float]:
    e, a = sun_positions(_seconds(when)[None], lat, lng)
    return float(e[0]), float(a[0])


# --- the season --------------------------------------------------------------------------

def _mmdd(text) -> Optional[tuple[int, int]]:
    if not isinstance(text, str) or "-" not in text:
        return None
    try:
        m, d = (int(x) for x in text.strip()[-5:].split("-"))
        date(2001, m, d)
        return m, d
    except ValueError:
        return None


def season_from_normals(normals: Optional[dict]) -> tuple[tuple[int, int], tuple[int, int], str]:
    """(start month-day, end month-day, how) from season.normals.frost_normals:
    the typical last spring and first fall 32 degree Fahrenheit dates, else
    April to October."""
    try:
        start = _mmdd(normals["spring"]["32"]["p50"])
        end = _mmdd(normals["fall"]["32"]["p50"])
    except (TypeError, KeyError):
        start = end = None
    if start and end and (end[0], end[1]) > (start[0], start[1]):
        return start, end, "frost_free_period"
    return DEFAULT_SEASON[0], DEFAULT_SEASON[1], "april_to_october"


def season_days(start: tuple[int, int], end: tuple[int, int], year: int = 2026,
                step_days: int = DAY_STEP) -> list[date]:
    d0, d1 = date(year, *start), date(year, *end)
    out, d = [], d0
    while d <= d1:
        out.append(d)
        d += timedelta(days=step_days)
    return out


def season_sun(days: Iterable[date], lat: float, lng: float,
               step_minutes: int = STEP_MINUTES) -> tuple[np.ndarray, np.ndarray, float]:
    """Sun elevation and azimuth for every step of every day (UTC days cover
    the whole local day in the United States), with the step in hours."""
    secs = []
    for d in days:
        base = datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()
        # A whole solar day around local noon: start 12 hours before it.
        noon = base + (12 * 3600 - lng * 240)
        secs.append(noon - 43200 + np.arange(0, 86400, step_minutes * 60))
    s = np.concatenate(secs)
    e, a = sun_positions(s, lat, lng)
    return e, a, step_minutes / 60.0


# --- horizons ------------------------------------------------------------------------------

def horizons(surface: np.ndarray, points: np.ndarray, dx: float, dy: float, *,
             base: Optional[np.ndarray] = None, observer_m: float = OBSERVER_M,
             n_az: int = AZIMUTHS, step_m: float = 1.0,
             max_m: Optional[float] = None) -> np.ndarray:
    """Horizon elevation angle (degrees) at each point for `n_az` directions
    clockwise from north. `points` is (P, 2) row, col; `surface` is what
    blocks the view (ground, or ground plus canopy); `base` is the ground the
    observer stands on (defaults to `surface`). Walks outward to the window
    edge, or `max_m`."""
    rows, cols = surface.shape
    base = surface if base is None else base
    pr = points[:, 0].astype(np.float64)
    pc = points[:, 1].astype(np.float64)
    z0 = base[points[:, 0], points[:, 1]].astype(np.float64) + observer_m
    reach = max_m or HORIZON_M
    # Fine steps near the point, where a tree or a bank matters most.
    dist = np.concatenate([np.arange(step_m, 60.0, step_m),
                           np.arange(60.0, reach + 2 * step_m, 2 * step_m)])
    out = np.empty((points.shape[0], n_az))
    # One direction at a time keeps memory to (points x distances).
    for k in range(n_az):
        a = math.radians(k * 360.0 / n_az)
        ri = np.rint(pr[:, None] - math.cos(a) * dist[None, :] / dy).astype(np.int64)
        ci = np.rint(pc[:, None] + math.sin(a) * dist[None, :] / dx).astype(np.int64)
        inside = (ri >= 0) & (ri < rows) & (ci >= 0) & (ci < cols)
        h = surface[np.clip(ri, 0, rows - 1), np.clip(ci, 0, cols - 1)].astype(np.float64)
        ang = np.degrees(np.arctan2(h - z0[:, None], dist[None, :]))
        out[:, k] = np.where(inside, ang, -90.0).max(axis=1)
    return out


def direct_hours(elev: np.ndarray, azim: np.ndarray, horizon: np.ndarray,
                 step_h: float, n_days: int) -> np.ndarray:
    """Average direct-sun hours a day at each point: steps where the sun is
    above the horizon in its own direction."""
    n_az = horizon.shape[1]
    up = elev > 0
    idx = np.rint(azim[up] / (360.0 / n_az)).astype(np.int64) % n_az
    lit = elev[up][None, :] > horizon[:, idx]
    return lit.sum(axis=1) * step_h / max(n_days, 1)


def category(hours: float) -> str:
    if hours >= FULL_SUN_HOURS:
        return "full_sun"
    if hours >= PART_SHADE_HOURS:
        return "part_shade"
    return "shade"


# --- sample points -------------------------------------------------------------------------

def sample_points(mask: np.ndarray, max_points: int = MAX_POINTS) -> np.ndarray:
    """Up to `max_points` cells from `mask`, spread evenly over it."""
    rr, cc = np.nonzero(mask)
    if rr.size == 0:
        return np.zeros((0, 2), dtype=np.int64)
    if rr.size <= max_points:
        return np.stack([rr, cc], axis=1)
    side = int(math.ceil(math.sqrt(max_points)))
    r0, r1, c0, c1 = rr.min(), rr.max(), cc.min(), cc.max()
    want_r = np.linspace(r0, r1, side)
    want_c = np.linspace(c0, c1, side)
    picked = []
    for wr in want_r:
        for wc in want_c:
            k = int(np.argmin((rr - wr) ** 2 + (cc - wc) ** 2))
            picked.append((rr[k], cc[k]))
    uniq = sorted(set(picked))[:max_points]
    return np.array(uniq, dtype=np.int64)


# --- the estimate ----------------------------------------------------------------------------

@dataclass(frozen=True)
class Estimate:
    open_sky_hours: Optional[float]
    hours: Optional[float]
    category: Optional[str]
    counted: tuple[str, ...]
    not_counted: tuple[str, ...]
    points: int
    spread: Optional[tuple[float, float]]
    season: dict
    canopy_resolution_m: Optional[float] = None
    cover_share: Optional[float] = None
    extra: dict = dc_field(default_factory=dict)


def _tree_share(readings: Sequence[Reading]) -> Optional[float]:
    for r in reversed(list(readings)):
        if r.field != "tree_cover" or r.level == "unknown":
            continue
        v = r.value
        if isinstance(v, dict):
            v = next((v[k] for k in ("share", "value", "percent") if k in v), None)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v) / 100.0 if v > 1 else float(v)
    return None


def estimate(lat: float, lng: float, block: Block, box: dict, pin: tuple[float, float], *,
             window: Optional[elevation.ElevationWindow],
             canopy: Optional[canopy_source.CanopyGrid],
             tree_share: Optional[float] = None,
             season: tuple[tuple[int, int], tuple[int, int], str] = (*DEFAULT_SEASON, "april_to_october"),
             year: int = 2026) -> Estimate:
    start, end, how = season
    days = season_days(start, end, year)
    season_d = {"start": f"{start[0]:02d}-{start[1]:02d}", "end": f"{end[0]:02d}-{end[1]:02d}",
                "how": how, "days_sampled": len(days), "step_minutes": STEP_MINUTES}
    not_counted = ["buildings"]
    have_ground = window is not None and window.coverage() >= 0.5
    if not have_ground and canopy is None:
        return Estimate(None, None, None, (), ("terrain", "canopy_height", "buildings"),
                        0, None, season_d)
    shape = window.z.shape if have_ground else canopy.height_m.shape
    if have_ground:
        ground = window.z.astype(np.float64)
        valid = window.valid
        dx, dy = window.dx_m, window.dy_m
    else:
        ground = np.zeros(shape)
        valid = np.ones(shape, bool)
        mid = math.radians((block.south + block.north) / 2)
        dy = (block.north - block.south) / shape[0] * elevation.M_PER_DEG_LAT
        dx = (block.east - block.west) / shape[1] * elevation.M_PER_DEG_LAT * math.cos(mid)
        not_counted.insert(0, "terrain")
    mask = terrain.footprint_mask(shape, block, box, pin) & valid
    pts = sample_points(mask)
    if pts.shape[0] == 0:
        return Estimate(None, None, None, (), tuple(not_counted), 0, None, season_d)
    elev_, azim, step_h = season_sun(days, lat, lng)
    counted: list[str] = ["terrain"] if have_ground else []
    open_h = direct_hours(elev_, azim, horizons(ground, pts, dx, dy), step_h, len(days))
    open_mean = float(open_h.mean())
    extra: dict = {}
    if canopy is not None:
        obstacles = np.where(canopy.height_m >= OBSTACLE_MIN_M, canopy.height_m, 0.0)
        hz = horizons(ground + obstacles, pts, dx, dy, base=ground)
        # A point under a crown is shaded while leaves are out.
        under = obstacles[pts[:, 0], pts[:, 1]] >= canopy_source.CANOPY_MIN_M
        hz[under, :] = 90.0
        hrs = direct_hours(elev_, azim, hz, step_h, len(days))
        counted.append("canopy_height")
        cover = canopy_source.cover_stats(canopy.height_m, mask)["cover_share"]
        extra["points_under_canopy"] = int(under.sum())
        res = canopy.resolution_m
    elif tree_share is not None:
        hrs = open_h * (1.0 - min(max(tree_share, 0.0), 1.0))
        counted.append("tree_cover")
        not_counted.insert(0, "canopy_height")
        cover, res = tree_share, None
    else:
        hrs = open_h
        not_counted.insert(0, "canopy_height")
        cover, res = None, None
    mean = float(hrs.mean())
    return Estimate(open_sky_hours=open_mean, hours=mean, category=category(mean),
                    counted=tuple(counted), not_counted=tuple(not_counted),
                    points=int(pts.shape[0]),
                    spread=(float(hrs.min()), float(hrs.max())), season=season_d,
                    canopy_resolution_m=res, cover_share=cover, extra=extra)


# --- readings -------------------------------------------------------------------------------

def readings_for(est: Estimate, *, is_default: bool, window, canopy) -> list[Reading]:
    """open_sky_sun, canopy_shade and sun_estimate from one Estimate, with the
    confidence rules of build spec section 5."""
    version = "noaa-meeus"
    base = {"season": est.season, "points": est.points, "default_footprint": is_default,
            "pin_radius_m": terrain.PIN_RADIUS_M, "source_name": SOURCE_NAME,
            "source_detail": "The sun's path at your latitude, every 10 minutes"}
    if window is not None:
        base["resolution_m"] = window.resolution_m
        if window.year:
            base["elevation_year"] = window.year
    out: list[Reading] = []
    if est.hours is None:
        return [Reading(field="sun_estimate", value=None, level="unknown",
                        provenance="modelled", source_key="sunpos", source_version=version,
                        method=METHOD, reason_codes=("nothing_counted",),
                        detail={**base, "counted": [], "not_counted": list(est.not_counted)})]
    if "terrain" in est.counted:
        out.append(Reading(
            field="open_sky_sun", value={"hours": round(est.open_sky_hours, 1)},
            level=("medium" if window and elevation.resolution_level(window.resolution_m)
                   in ("high", "medium") else "low"),
            provenance="modelled", source_key="sunpos", source_version=version,
            method=METHOD, reason_codes=("terrain_only",),
            detail={**base, "counted": ["terrain"],
                    "not_counted": ["canopy_height", "buildings"]}))
    lost = max(0.0, (est.open_sky_hours or 0) - est.hours)
    if "canopy_height" in est.counted:
        out.append(Reading(
            field="canopy_shade",
            value={"hours_lost": round(lost, 1), "cover_share": est.cover_share},
            level="medium", provenance="modelled", source_key="canopy",
            source_version=canopy_source.SOURCE_VERSION, method=METHOD,
            reason_codes=("canopy_height",),
            detail={**base, **canopy_source.source_detail(canopy), **est.extra}))
    elif "tree_cover" in est.counted:
        out.append(Reading(
            field="canopy_shade",
            value={"hours_lost": round(lost, 1), "cover_share": est.cover_share},
            level="low", provenance="modelled", source_key="sunpos",
            source_version=version, method="tree_cover_share_fallback",
            reason_codes=("coarse_tree_cover",),
            detail={**base, "kind": "tree_cover"}))
    # Never above "Area estimate" (medium); "Rough estimate" (low) with only
    # the coarse fallback, on the default footprint, or without buildings,
    # which are never counted in this build.
    codes = ["buildings_not_counted"]
    if "canopy_height" not in est.counted:
        codes.append("coarse_canopy_only" if "tree_cover" in est.counted else "canopy_not_counted")
    if is_default:
        codes.append("default_footprint")
    level = "low"
    detail = {**base, "counted": list(est.counted), "not_counted": list(est.not_counted),
              "open_sky_hours": round(est.open_sky_hours, 1),
              "hours_range": [round(est.spread[0], 1), round(est.spread[1], 1)],
              "leaves_out": "canopy_height" in est.counted or "tree_cover" in est.counted,
              "thresholds_hours": {"full_sun": FULL_SUN_HOURS, "part_shade": PART_SHADE_HOURS}}
    if est.canopy_resolution_m is not None:
        detail["canopy_resolution_m"] = est.canopy_resolution_m
    out.append(Reading(field="sun_estimate",
                       value={"category": est.category, "hours": round(est.hours, 1)},
                       level=level, provenance="modelled", source_key="sunpos",
                       source_version=version, method=METHOD, reason_codes=tuple(codes),
                       detail=detail))
    return out


def _normals(pin: tuple[float, float]) -> Optional[dict]:
    try:
        from app.services.season.normals import frost_normals
        return frost_normals(*pin)
    except Exception:  # noqa: BLE001 -- the season falls back to April to October
        return None


def read(block: Block, pin: tuple[float, float], footprint, *, client, session=None,
         readings: Sequence[Reading] = ()) -> list[Reading]:
    """open_sky_sun, canopy_shade and sun_estimate for the footprint, from the
    cached elevation window and canopy grid (fetched if needed). Either may
    be missing; with neither, sun_estimate reads "unknown"."""
    try:
        window = elevation.load_window(session, block, client=client)
        if window.coverage() < 0.5:
            window = None
    except SourceUnavailable:
        window = None
    try:
        canopy = canopy_source.load_canopy(session, block, client=client)
    except SourceUnavailable:
        canopy = None
    box, is_default = terrain.footprint_box(pin, footprint)
    est = estimate(pin[0], pin[1], block, box, pin, window=window, canopy=canopy,
                   tree_share=_tree_share(readings),
                   season=season_from_normals(_normals(pin)))
    return readings_for(est, is_default=is_default, window=window, canopy=canopy)
