"""Typical frost and freeze dates from NOAA station normals (PLAN.md section 6,
"Typical frost dates"; build spec section 3).

The data are the National Oceanic and Atmospheric Administration (NOAA)
1991 to 2020 U.S. Climate Normals, held on our server in
`data/frost_normals.json` (built by `data/build_frost_normals.py`; see
`data/README.md`). No request leaves the server.

    frost_normals(lat, lng) -> dict

The answer is plain JSON so the site profile can use it too:

    {"status": "ready" | "none",
     "stations": [{"id", "name", "distance_km", "elev_m"}],   # nearest first
     "fall":   {"36": {"p10": "10-14", "p50": "10-29", "p90": "11-10"}, "32": ..., "28": ...},
     "spring": {"36": ..., "32": ..., "28": ...},
     "second": {"fall": {...}, "spring": {...}} | None,       # the next station
     "occurs_pct": {"36": 100, "32": 100, "28": 100},          # share of years it happens at all
     "daily": {"fall_low55", "fall_low50", "fall_mean45", "spring_low50",
               "first_leaf", "first_bloom": "MM-DD" | None, "coldest_mean": float} | None,
     "ranges": {"fall_32": bool, "fall_36": ..., "spring_32": ...},  # nearby stations differ > 7 days
     "confidence": "area_estimate" | "rough_estimate" | "not_known_yet",
     "explained": {display, confidence, reason, sources, provenance},
     "display", "reason", "source", "station"}   # flat copies for the site profile

Semantics, pinned by tests: fall percentiles mean "on or before" (p10 is the
date reached in only one year in ten, p90 the date reached in nine years in
ten); spring percentiles mean "a later one after" (p90 is passed in nine
years in ten without a later freeze being unusual, p10 is the date after
which one year in ten still has one). "By" is only ever used with the
nine-years-in-ten date.
"""
from __future__ import annotations

import json
import math
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Optional

DATA_FILE = Path(__file__).parent / "data" / "frost_normals.json"

#: Stations farther than this are not used at all (engineering default).
MAX_STATION_KM = 100.0
#: Within this distance the dates are an "Area estimate"; farther, "Rough".
AREA_ESTIMATE_KM = 25.0
#: Two nearest stations differing by more than this show a range (PLAN.md).
RANGE_DAYS = 7
#: The second station is only compared when it is this close (engineering default).
SECOND_STATION_KM = 40.0

THRESHOLDS = ("36", "32", "28")
PERCENTS = ("p10", "p50", "p90")
DAILY_KEYS = ("fall_low55", "fall_low50", "fall_mean45", "spring_low50",
              "first_leaf", "first_bloom", "coldest_mean")

SOURCE = {
    "name": "National Oceanic and Atmospheric Administration (NOAA) station normals 1991 to 2020",
    "detail": "U.S. Climate Normals, National Centers for Environmental Information",
    "version": "1.0.1",
    "url": "https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals",
}

_MONTHS = ("January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December")


@lru_cache(maxsize=1)
def _data() -> dict:
    return json.loads(DATA_FILE.read_text())


def _km(lat1, lng1, lat2, lng2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _usable(row) -> bool:
    fall, spring = row[5], row[6]
    return fall[4] is not None and spring[4] is not None  # the 32 F medians


def nearest_stations(lat: float, lng: float, n: int = 2) -> list[tuple[float, list]]:
    """The n nearest stations with both 32 F medians, as (km, row)."""
    out = []
    for row in _data()["stations"]:
        if abs(row[2] - lat) > 1.5 or abs(row[3] - lng) > 2.0:
            continue
        if not _usable(row):
            continue
        out.append((_km(lat, lng, row[2], row[3]), row))
    out.sort(key=lambda t: t[0])
    return [t for t in out[:n] if t[0] <= MAX_STATION_KM]


# --- dates ----------------------------------------------------------------------

def _mmdd(d: date) -> str:
    return f"{d.month:02d}-{d.day:02d}"


def _fall_mmdd(offset: Optional[int]) -> Optional[str]:
    if offset is None:
        return None
    return _mmdd(date(2001, 7, 1) + timedelta(days=offset))


def _spring_mmdd(offset: Optional[int]) -> Optional[str]:
    if offset is None:
        return None
    return _mmdd(date(2001, 1, 1) + timedelta(days=offset))


def fall_date(mmdd: Optional[str], season_year: int) -> Optional[date]:
    """A fall month-day in the season that starts 1 July of `season_year`."""
    if not mmdd:
        return None
    m, d = int(mmdd[:2]), int(mmdd[3:])
    return date(season_year if m >= 7 else season_year + 1, m, d)


def spring_date(mmdd: Optional[str], season_year: int) -> Optional[date]:
    """A spring month-day in the season that starts 1 July of `season_year`
    (so spring of the following calendar year; a late-year value belongs to
    the winter before)."""
    if not mmdd:
        return None
    m, d = int(mmdd[:2]), int(mmdd[3:])
    return date(season_year if m >= 7 else season_year + 1, m, d)


def day_text(d: Optional[date]) -> str:
    return f"{d.day} {_MONTHS[d.month - 1]}" if d else ""


def mmdd_text(mmdd: Optional[str]) -> str:
    if not mmdd:
        return ""
    return f"{int(mmdd[3:])} {_MONTHS[int(mmdd[:2]) - 1]}"


def _block(offsets: list, convert) -> dict:
    out = {}
    for i, t in enumerate(THRESHOLDS):
        out[t] = {p: convert(offsets[i * 3 + j]) for j, p in enumerate(PERCENTS)}
    return out


def _days_apart(a: Optional[str], b: Optional[str], fall: bool) -> Optional[int]:
    if not a or not b:
        return None
    conv = fall_date if fall else spring_date
    return abs((conv(a, 2001) - conv(b, 2001)).days)


def _distance_text(km: float) -> str:
    miles = km * 0.621371
    if miles < 1:
        return "less than a mile"
    return f"about {round(miles)} mile{'s' if round(miles) != 1 else ''}"


_WORDS = {"NATL": "National", "AP": "Airport", "INTL": "International",
          "MUNI": "Municipal", "WSO": "Weather Service Office", "CO": "County",
          "FLD": "Field", "MTN": "Mountain", "FT": "Fort", "ST": "Saint"}


def _station_name(name: str) -> str:
    """"NATL ARBORETUM DC, MD US" -> "National Arboretum DC"."""
    words = []
    for w in name.split(",")[0].split():
        if w in _WORDS:
            words.append(_WORDS[w])
        elif len(w) == 2 and w.isalpha():
            words.append(w)  # a state or district: DC, TX
        else:
            words.append(w.capitalize() if w.isalpha() else w.title())
    return " ".join(words)


def frost_normals(lat: float, lng: float) -> dict:
    """Typical first and last frost for a place (see the module docstring).
    Never raises: a missing data file or no station in range answers
    status "none" with an Explained that says so."""
    try:
        found = nearest_stations(lat, lng, 2)
    except (OSError, ValueError, KeyError):
        found = []
    if not found:
        return {
            "status": "none", "stations": [], "fall": {}, "spring": {},
            "second": None, "occurs_pct": {}, "daily": None, "ranges": {},
            "confidence": "not_known_yet",
            "explained": {
                "display": "No typical frost date: there is no weather station "
                           "with frost records close enough to your place.",
                "confidence": "not_known_yet",
                "reason": f"No National Oceanic and Atmospheric Administration station "
                          f"with frost records lies within {round(MAX_STATION_KM * 0.621371)} miles.",
                "sources": [SOURCE], "provenance": "public_map"},
        }
    km, row = found[0]
    fall = _block(row[5], _fall_mmdd)
    spring = _block(row[6], _spring_mmdd)
    occ = dict(zip(THRESHOLDS, row[7] or [None, None, None]))
    daily = None
    if row[8]:
        vals = dict(zip(DAILY_KEYS, row[8]))
        daily = {
            "fall_low55": _fall_mmdd(vals["fall_low55"]),
            "fall_low50": _fall_mmdd(vals["fall_low50"]),
            "fall_mean45": _fall_mmdd(vals["fall_mean45"]),
            "spring_low50": _spring_mmdd(vals["spring_low50"]),
            "first_leaf": _spring_mmdd(vals["first_leaf"]),
            "first_bloom": _spring_mmdd(vals["first_bloom"]),
            "coldest_mean": vals["coldest_mean"],
        }
    stations = [{"id": r[0], "name": _station_name(r[1]), "distance_km": round(k, 1),
                 "elev_m": r[4]} for k, r in found]
    second = None
    ranges = {}
    if len(found) > 1 and found[1][0] <= SECOND_STATION_KM:
        r2 = found[1][1]
        second = {"fall": _block(r2[5], _fall_mmdd), "spring": _block(r2[6], _spring_mmdd)}
        for t in THRESHOLDS:
            fa = _days_apart(fall[t]["p50"], second["fall"][t]["p50"], True)
            sa = _days_apart(spring[t]["p50"], second["spring"][t]["p50"], False)
            ranges[f"fall_{t}"] = bool(fa is not None and fa > RANGE_DAYS)
            ranges[f"spring_{t}"] = bool(sa is not None and sa > RANGE_DAYS)
    confidence = "area_estimate" if km <= AREA_ESTIMATE_KM else "rough_estimate"
    out = {
        "status": "ready", "stations": stations, "fall": fall, "spring": spring,
        "second": second, "occurs_pct": occ, "daily": daily, "ranges": ranges,
        "confidence": confidence,
    }
    out["explained"] = _explained(out)
    # Flat copies for the site profile's frost-dates row (site/copy.py).
    out["display"] = out["explained"]["display"]
    out["reason"] = out["explained"]["reason"]
    out["source"] = out["explained"]["sources"][0]
    out["station"] = stations[0]
    return out


def typical_text(normals: dict, side: str, threshold: str) -> str:
    """"around 8 November" or "around 8 to 18 November (nearby stations
    differ)" for the median, following the range rule."""
    own = normals[side][threshold]["p50"]
    if not own:
        return ""
    if normals.get("ranges", {}).get(f"{side}_{threshold}") and normals.get("second"):
        other = normals["second"][side][threshold]["p50"]
        conv = fall_date if side == "fall" else spring_date
        a, b = sorted([conv(own, 2001), conv(other, 2001)])
        if a.month == b.month:
            span = f"{a.day} to {b.day} {_MONTHS[a.month - 1]}"
        else:
            span = f"{day_text(a)} to {day_text(b)}"
        return f"around {span} (nearby stations differ)"
    return f"around {mmdd_text(own)}"


def _explained(n: dict) -> dict:
    st = n["stations"][0]
    fall32 = n["fall"]["32"]
    spring32 = n["spring"]["32"]
    first = typical_text(n, "fall", "32")
    last = typical_text(n, "spring", "32")
    display = (f"Typical first freeze here: {first}. Typical last freeze: {last}.")
    detail = []
    if fall32["p10"] and fall32["p90"]:
        detail.append(f"At the nearest station the first freeze has come as early as "
                      f"{mmdd_text(fall32['p10'])} in one year in ten, and by "
                      f"{mmdd_text(fall32['p90'])} in nine years in ten.")
    if spring32["p10"]:
        detail.append(f"One year in ten still has a freeze after {mmdd_text(spring32['p10'])}.")
    reason = (" ".join(detail) + f" From the {st['name']} station, "
              f"{_distance_text(st['distance_km'])} away. A freeze is a night at "
              f"or below 32 degrees Fahrenheit.").strip()
    return {"display": display, "confidence": n["confidence"], "reason": reason,
            "sources": [dict(SOURCE, detail=f"{st['name']} station ({st['id']})")],
            "provenance": "public_map"}
