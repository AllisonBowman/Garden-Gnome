"""Where water collects (build spec section 5, "Where water collects and
drainage"; replaces D15: built from data, never by asking the owner).

Signals, each read into "wet", "slow", "free" or nothing:

- soil survey (passed in as Readings; this module never calls the soil
  source): natural drainage class, how fast water moves through the slowest
  layer, runoff group, ponding, flooding, depth to the seasonal water table;
- elevation window (through `terrain`): filled-depression depth (low spots)
  and flow accumulation (where runoff from uphill gathers), leaving out the
  10 metre radius around the pin, and only from a survey of 3.5 metres
  detail or finer.

One outcome per footprint, the first that holds:

    often_wet           a wet soil signal (poorly drained class, water table
                        within 30 cm, ponding or frequent flooding, a dual
                        runoff group such as B/D)
    gathers_after_rain  a low spot or a flow path in the footprint
    slow_to_drain       a slow soil signal (moderately well or somewhat
                        poorly drained, slowest layer under 1 micrometre a
                        second, runoff group D, water table within 1 metre)
    drains_freely       otherwise, when at least one signal answered

`detail["signals"]` names the signals that agreed with the outcome, and
`detail["soil_agree"]` says whether every soil signal that answered points
the same way. Confidence (spec section 5): "Good estimate" (high) only on a
1 metre survey with an owner-drawn zone and agreeing soil signals; "Area
estimate" (medium) on 1 to 3 metre elevation, or soil alone with 75% or
more of the mapped area agreeing; "Rough estimate" (low) on coarser
elevation, the default footprint, or disturbed soil (15% or more). It is
never a flood insurance determination.

    signals_from_soil(readings) -> SoilSignals
    combine(soil, terrain_summary, ...) -> Reading
    read(block, pin, footprint, *, client, session, readings) -> [water_collects]
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field
from typing import Any, Optional, Sequence

from app.services.site import terrain
from app.services.site.sources import elevation
from app.services.site.types import Block, Reading, SourceUnavailable

WET, SLOW, FREE = "wet", "slow", "free"
SOIL_FIELDS = ("soil_drainage_class", "soil_slowest_layer", "soil_runoff_group",
               "soil_ponding", "soil_flooding", "soil_water_table")
SIGNAL_OF = {"soil_drainage_class": "drainage_class", "soil_slowest_layer": "slowest_layer",
             "soil_runoff_group": "runoff_group", "soil_ponding": "ponding",
             "soil_flooding": "flooding", "soil_water_table": "water_table"}
DOMINANT_SHARE = 0.75
DISTURBED_SHARE = 0.15
#: Slowest-layer rate below which water moves slowly, micrometres a second
#: (the soil survey's "moderately low" class and below).
SLOW_KSAT_UM_S = 1.0
WET_TABLE_CM = 30.0
SLOW_TABLE_CM = 100.0


# --- reading tolerant values ----------------------------------------------------------

def _text(v: Any, *keys: str) -> Optional[str]:
    if isinstance(v, str):
        return v.strip() or None
    if isinstance(v, dict):
        for k in keys:
            t = v.get(k)
            if isinstance(t, str) and t.strip():
                return t.strip()
    return None


def _num(v: Any, *keys: str) -> Optional[float]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, dict):
        for k in keys:
            if k in v:
                return _num(v[k])
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return None
    return None


def drainage_class_signal(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    t = text.lower()
    if "very poorly" in t or re.search(r"(^|\s)poorly", t) and "somewhat" not in t:
        return WET
    if "somewhat poorly" in t or "moderately well" in t:
        return SLOW
    if "drained" in t:          # well, somewhat excessively, excessively
        return FREE
    return None


def slowest_layer_signal(v: Any) -> Optional[str]:
    n = _num(v, "um_per_s", "ksat_um_s", "ksat", "value")
    if n is not None:
        return SLOW if n < SLOW_KSAT_UM_S else FREE
    t = (_text(v, "class", "label", "rate") or "").lower()
    if not t:
        return None
    if "low" in t or "slow" in t or "impermeable" in t:
        return SLOW if "moderately high" not in t else FREE
    return FREE


def runoff_group_signal(v: Any) -> Optional[str]:
    t = (_text(v, "group", "class", "value") or "").upper().replace(" ", "")
    if not t:
        return None
    if "/" in t:
        return WET           # dual group: wet unless drained
    if t == "D":
        return SLOW
    if t in ("A", "B", "C"):
        return FREE
    return None


def _frequency(v: Any) -> Optional[str]:
    return (_text(v, "class", "frequency", "label", "dominant") or "").lower() or None


def ponding_signal(v: Any) -> Optional[str]:
    t = _frequency(v)
    if t is None:
        return None
    if t in ("none", "no ponding"):
        return FREE
    if "occasional" in t or "frequent" in t:
        return WET
    return None                 # "rare": no signal either way


def flooding_signal(v: Any) -> Optional[str]:
    t = _frequency(v)
    if t is None:
        return None
    if "frequent" in t:         # frequent, very frequent
        return WET
    if t in ("none", "no flooding", "very rare", "rare"):
        return FREE
    return None                 # occasional: wet now and then, not by itself


def water_table_signal(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, dict) and v.get("depth_cm", "missing") is None:
        return FREE             # none recorded within about 2 metres
    n = _num(v, "depth_cm", "cm", "value")
    if n is None:
        t = (_text(v, "class", "label") or "").lower()
        return FREE if t.startswith("none") else None
    if n < WET_TABLE_CM:
        return WET
    if n < SLOW_TABLE_CM:
        return SLOW
    return FREE


_READERS = {
    "soil_drainage_class": lambda v: drainage_class_signal(_text(v, "class", "label", "drainage_class")),
    "soil_slowest_layer": slowest_layer_signal,
    "soil_runoff_group": runoff_group_signal,
    "soil_ponding": ponding_signal,
    "soil_flooding": flooding_signal,
    "soil_water_table": water_table_signal,
}


@dataclass(frozen=True)
class SoilSignals:
    by_signal: dict                      # signal name -> wet | slow | free
    agree_share: Optional[float]         # dominant share of the mapped area
    disturbed_share: Optional[float]
    sources: tuple = ()
    versions: tuple = ()
    extra: dict = dc_field(default_factory=dict)


def _share(v: Any) -> Optional[float]:
    n = _num(v, "share", "value", "percent")
    if n is None:
        return None
    return n / 100.0 if n > 1 else n


def signals_from_soil(readings: Sequence[Reading]) -> SoilSignals:
    """The soil signals from the newest reading of each soil field."""
    latest: dict[str, Reading] = {}
    for r in readings:
        if r.field in SOIL_FIELDS or r.field in ("soil_mapunit", "soil_disturbed_share"):
            latest[r.field] = r
    out: dict[str, str] = {}
    for f in SOIL_FIELDS:
        r = latest.get(f)
        if r is None or r.level == "unknown":
            continue
        sig = _READERS[f](r.value)
        if sig is not None:
            out[SIGNAL_OF[f]] = sig
    share = None
    for f in ("soil_drainage_class", "soil_mapunit"):
        r = latest.get(f)
        if r is not None:
            d = r.detail or {}
            s = d.get("dominant_share")
            if s is None and isinstance(r.value, dict):
                s = r.value.get("dominant_share")
            if s is None:  # B2a's soil source gives a 0..100 dominant_percent
                p = d.get("dominant_percent")
                s = float(p) / 100.0 if isinstance(p, (int, float)) else None
            if isinstance(s, (int, float)):
                share = s / 100.0 if s > 1 else float(s)
                break
    dist = latest.get("soil_disturbed_share")
    used = [latest[f] for f in SOIL_FIELDS if f in latest]
    return SoilSignals(by_signal=out, agree_share=share,
                       disturbed_share=_share(dist.value) if dist else None,
                       sources=tuple(sorted({r.source_key for r in used})),
                       versions=tuple(sorted({r.source_version for r in used if r.source_version})))


# --- combining ----------------------------------------------------------------------------

def outcome(soil: SoilSignals, low_spot: bool, flow: bool, terrain_used: bool
            ) -> tuple[Optional[str], list[str]]:
    """(outcome, signals that agreed with it)."""
    s = soil.by_signal
    wet = [k for k, v in s.items() if v == WET]
    slow = [k for k, v in s.items() if v == SLOW]
    free = [k for k, v in s.items() if v == FREE]
    if wet:
        return "often_wet", wet + (["low_spot"] if low_spot else []) + (["flow"] if flow else [])
    if low_spot or flow:
        return "gathers_after_rain", (["low_spot"] if low_spot else []) + (
            ["flow"] if flow else []) + slow
    if slow:
        return "slow_to_drain", slow
    if free or terrain_used:
        return "drains_freely", free + (["low_spot", "flow"] if terrain_used else [])
    return None, []


def _soil_agree(soil: SoilSignals, result: str) -> bool:
    want = {"often_wet": {WET}, "slow_to_drain": {SLOW}, "drains_freely": {FREE},
            "gathers_after_rain": {SLOW, WET}}[result]
    vals = set(soil.by_signal.values())
    if not vals:
        return False
    if result == "gathers_after_rain":
        return FREE not in vals or vals <= want
    return vals <= want


def combine(soil: SoilSignals, summary: Optional[terrain.Summary], *,
            resolution_m: Optional[float], is_default: bool,
            survey: Optional[dict] = None) -> Reading:
    """The water_collects reading for one footprint."""
    terrain_used = (summary is not None and summary.cells >= 9 and resolution_m is not None
                    and resolution_m <= terrain.WATER_MAX_RESOLUTION_M)
    low = terrain_used and summary.low_area_m2 >= terrain.LOW_SPOT_AREA_M2
    flow = terrain_used and summary.catchment_max_m2 >= terrain.FLOW_CATCHMENT_M2
    result, signals = outcome(soil, low, flow, terrain_used)
    codes: list[str] = ["pin_radius_left_out"] if terrain_used else []
    detail: dict = {"signals": signals, "soil_signals": dict(soil.by_signal),
                    "soil_agree_share": soil.agree_share, "default_footprint": is_default,
                    "source_name": "Drainage calculation on our server",
                    "source_detail": "Combines the soil survey with the elevation survey",
                    "not_flood_determination": True}
    if summary is not None and terrain_used:
        detail.update({"resolution_m": resolution_m,
                       "max_depth_m": round(summary.low_depth_max_m, 2),
                       "low_area_m2": round(summary.low_area_m2, 1),
                       "catchment_m2": round(summary.catchment_max_m2),
                       "catchment_reaches_edge": summary.catchment_reaches_edge,
                       "pin_radius_m": terrain.PIN_RADIUS_M})
        if survey:
            detail.update({k: survey[k] for k in ("year", "survey") if k in survey})
    elif summary is not None:
        codes.append("elevation_too_coarse_for_water")
    if result is None:
        return Reading(field="water_collects", value=None, level="unknown",
                       provenance="modelled", source_key="drainage",
                       source_version="v1", method="soil_and_terrain_signals",
                       reason_codes=tuple(codes + ["no_signals"]), detail=detail)
    agree = _soil_agree(soil, result)
    detail["soil_agree"] = agree
    disturbed = soil.disturbed_share is not None and soil.disturbed_share >= DISTURBED_SHARE
    share_ok = soil.agree_share is not None and soil.agree_share >= DOMINANT_SHARE
    if terrain_used and resolution_m <= 1.5 and not is_default and agree:
        level = "high"
    elif (terrain_used and resolution_m <= 3.5) or (soil.by_signal and share_ok):
        level = "medium"
    else:
        level = "low"
    if is_default:
        codes.append("default_footprint")
    if disturbed:
        codes.append("disturbed_soil")
    if is_default or disturbed:
        level = "low"
    if not soil.by_signal:
        codes.append("no_soil_signals")
        level = "low"
    codes.extend(f"agreed_{s}" for s in signals)
    return Reading(field="water_collects", value={"class": result}, level=level,
                   provenance="modelled", source_key="drainage", source_version="v1",
                   method="soil_and_terrain_signals", reason_codes=tuple(codes),
                   detail=detail)


def read(block: Block, pin: tuple[float, float], footprint, *, client, session=None,
         readings: Sequence[Reading] = ()) -> list[Reading]:
    """water_collects for the footprint from the soil readings passed in and
    the cached elevation window (fetched if needed; without it, soil alone)."""
    soil = signals_from_soil(readings)
    box, is_default = terrain.footprint_box(pin, footprint)
    summary, res, survey = None, None, None
    try:
        win = elevation.load_window(session, block, client=client)
        if win.coverage() >= 0.5:
            summary = terrain.summarise(win, box, pin)
            res = win.resolution_m
            survey = {"year": win.year, "survey": win.title}
            survey = {k: v for k, v in survey.items() if v}
    except SourceUnavailable:
        pass
    if summary is None and not soil.by_signal:
        return []
    return [combine(soil, summary, resolution_m=res, is_default=is_default, survey=survey)]
