"""What the owner reads for every site value (PLAN.md section 6, "Each
value"). Plain words: every acronym is spelled out, "hardiness zone" is never
shortened to "zone", "United States" is written in full, no em dashes, and
no more precision than the data has. Every value carries a reason and at
least one named source.

The builders take readings as `R` (field -> R) and a `confidence.Decision`,
and return a `Text` (display, reason, sources). `profile` turns those into
SiteValue shapes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field
from datetime import date, datetime
from typing import Any, Mapping, Optional

from app.services.site import overrides as override_rules


@dataclass(frozen=True)
class R:
    """The parts of a stored reading the sentences use."""
    field: str
    value: Any
    level: str
    source_key: str
    source_version: str = ""
    method: str = ""
    reason_codes: tuple[str, ...] = ()
    detail: Mapping[str, Any] = dc_field(default_factory=dict)


@dataclass(frozen=True)
class Text:
    display: str
    reason: str
    sources: list[dict]


TITLES = {
    "sun": "Sun",
    "water_collects": "Where water collects",
    "soil_drainage": "Drainage",
    "soil_texture": "Topsoil",
    "soil_ph": "Soil acidity (pH)",
    "disturbed_soil": "Built-up or moved soil",
    "slope": "Steepness",
    "facing": "Faces",
    "flooding": "Flooding",
    "land_cover": "Neighbourhood context",
    "hardiness_zone": "Hardiness zone",
    "frost_dates": "Typical frost dates",
}

#: Source keys -> (name, detail, url). Names are spelled out in full.
SOURCES: dict[str, tuple[str, Optional[str], Optional[str]]] = {
    "ssurgo": ("United States Department of Agriculture soil survey",
               "Soil Survey Geographic Database, through the Soil Data Access service",
               "https://sdmdataaccess.sc.egov.usda.gov"),
    "statsgo": ("United States Department of Agriculture general soil map",
                "State Soil Geographic Database", None),
    "3dep": ("United States Geological Survey 3D Elevation Program",
             "Laser ground survey", "https://www.usgs.gov/3d-elevation-program"),
    "nlcd": ("United States Geological Survey Annual National Land Cover Database",
             "Satellite land cover mapping", "https://www.usgs.gov/centers/eros/science/annual-national-land-cover-database"),
    "phzm2023": ("United States Department of Agriculture Plant Hardiness Zone Map 2023",
                 "United States Department of Agriculture Agricultural Research Service "
                 "and the Parameter-elevation Regressions on Independent Slopes Model "
                 "(PRISM) Climate Group, Oregon State University",
                 "https://planthardiness.ars.usda.gov"),
    "canopy": ("Tree canopy height map", None, None),
    "sunpos": ("Sun position calculation on our server",
               "The sun's path at your latitude, hour by hour", None),
    "terrain": ("Elevation calculation on our server",
                "Computed from the United States Geological Survey 3D Elevation Program", None),
    "drainage": ("Drainage calculation on our server",
                 "Combines the soil survey with the elevation survey", None),
    "noaa_normals": ("National Oceanic and Atmospheric Administration station normals",
                     "1991 to 2020", "https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals"),
    "naip": ("United States Department of Agriculture National Agriculture Imagery Program",
             "Aerial photographs", None),
}

#: The source each value comes from when no reading names one.
FIELD_SOURCE = {
    "hardiness_zone": "phzm2023", "soil_drainage": "ssurgo",
    "soil_texture": "ssurgo", "soil_ph": "ssurgo", "disturbed_soil": "ssurgo",
    "flooding": "ssurgo", "slope": "3dep", "facing": "3dep", "sun": "sunpos",
    "water_collects": "drainage", "land_cover": "nlcd",
    "frost_dates": "noaa_normals",
}

APPROX_YARD = ("Worked out over an approximate yard (typical United States lot "
               "size, not your property line).")


# --- small helpers ----------------------------------------------------------------

def _num(value: Any, *keys: str) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Mapping):
        for k in keys:
            if k in value:
                return _num(value[k])
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _text(value: Any, *keys: str) -> Optional[str]:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, Mapping):
        for k in keys:
            v = value.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None


def share(value: Any) -> Optional[float]:
    """A share 0..1, accepting a percentage."""
    n = _num(value, "share", "value", "percent")
    if n is None:
        return None
    return n / 100.0 if n > 1 else n


def _percent(s: float) -> str:
    p = s * 100
    if p < 1:
        return "under 1%"
    if p < 10:
        return f"about {round(p)}%"
    return f"about {int(5 * round(p / 5))}%"


def _half(hours: float) -> str:
    h = round(hours * 2) / 2
    return f"{h:g}"


def _lower_first(s: str) -> str:
    return s[:1].lower() + s[1:] if s else s


def _words(code: str) -> str:
    return code.replace("_", " ").strip().lower()


def source(key: str, version: str = "", detail: Optional[Mapping] = None) -> dict:
    """A Source shape for a source key. A reading may name itself through
    detail["source_name"] / ["source_detail"] / ["source_url"]."""
    name, extra, url = SOURCES.get(key, (None, None, None))
    d = detail or {}
    name = d.get("source_name") or name or f"Public map data ({key})"
    out = {"name": name}
    extra = d.get("source_detail") or extra
    if extra:
        out["detail"] = extra
    if version:
        out["version"] = str(version)
    url = d.get("source_url") or url
    if url:
        out["url"] = url
    return out


def sources_of(readings: list[Optional[R]], fallback: str) -> list[dict]:
    seen: list[dict] = []
    for r in readings:
        if r is None:
            continue
        s = source(r.source_key, r.source_version, r.detail)
        if all(s["name"] != t["name"] for t in seen):
            seen.append(s)
    if not seen:
        seen.append(source(fallback))
    return seen


# --- values that are not there yet ----------------------------------------------

def missing(field: str, state: str) -> Text:
    """A row with no public value. `state` is one of: pending, failed,
    no_data, outside_us, skipped."""
    title = TITLES[field]
    src = [source(FIELD_SOURCE[field])]
    tell = (" You can tell us yourself." if override_rules.can_override(field)
            else "")
    if state == "pending":
        return Text(f"{title}: still being worked out.",
                    "We are reading public maps for the area around your pin. "
                    "This usually takes a minute or two.", src)
    if state == "failed":
        return Text(f"{title}: not known yet.",
                    f"The {src[0]['name']} did not answer. We will try again."
                    + tell, src)
    if state == "outside_us":
        return Text(f"{title}: not known yet.",
                    "The public maps we use cover the United States only." + tell, src)
    if state == "zone_pending":
        return Text(f"{title}: still being worked out for this zone.",
                    "We work this out over the box you drew once the elevation "
                    "survey for the area is loaded." + tell, src)
    if field == "frost_dates":
        return Text("Typical frost dates: no typical date for this spot.",
                    "There is no suitable weather station record near your pin, so "
                    "seasonal tasks are shown without dates.", src)
    return Text(f"{title}: not known yet.",
                f"The {src[0]['name']} has no data at this spot." + tell, src)


# --- owner corrections ------------------------------------------------------------

def owner(field: str, value: Any, method: str, when: Optional[datetime],
          public_sources: list[dict]) -> Text:
    title = TITLES[field]
    on = f" on {when.day} {when.strftime('%B %Y')}" if when else ""
    if field == "soil_ph":
        display = f"{title}: {float(value):g}, from your soil test."
        reason = f"You entered this soil test result{on}."
    else:
        label = override_rules.label(field, value) or _words(str(value))
        display = f"{title}: {_lower_first(label)}. You told us."
        reason = f"Your answer{on}."
    reason += " The public estimate stays visible beside it, and a refresh never replaces your answer."
    src = [{"name": "Your correction",
            "detail": "Recorded in this app" + (f"{on}" if on else "")}]
    for s in public_sources:
        if all(s["name"] != t["name"] for t in src):
            src.append(s)
    return Text(display, reason, src)


# --- public values ----------------------------------------------------------------

def hardiness_zone(r: R, caps: tuple[str, ...]) -> Text:
    zone = _text(r.value, "zone", "label") or str(r.value)
    d = r.detail or {}
    lo = _num(d.get("min_f"))
    hi = _num(d.get("max_f"))
    if lo is None or hi is None:
        lo, hi = _num(r.value, "low_f"), _num(r.value, "high_f")
    m = re.fullmatch(r"(\d{1,2})([ab])", zone or "")
    if (lo is None or hi is None) and m:
        n, half = int(m.group(1)), m.group(2)
        lo = -60 + ((n - 1) * 2 + (0 if half == "a" else 1)) * 5
        hi = lo + 5
    display = f"Hardiness zone {zone}"
    if lo is not None and hi is not None:
        display += (f": the average coldest night of the year is {lo:g} to "
                    f"{hi:g} degrees Fahrenheit.")
    else:
        display += "."
    reason = "Read at your pin from the 2023 hardiness zone map held on our server."
    if "near_zone_line" in caps:
        reason += (" Your pin is close to the line with the next half of a hardiness "
                   "zone, so either could apply.")
    return Text(display, reason, sources_of([r], "phzm2023"))


def _rate(value: Any) -> Optional[str]:
    t = _text(value, "class", "label", "rate")
    if t:
        return _lower_first(t)
    n = _num(value, "um_per_s", "ksat_um_s")
    if n is None:
        return None
    if n < 1.0:
        return "slowly"
    if n < 10.0:
        return "at a moderate pace"
    return "quickly"


def _soil_caveats(caps: tuple[str, ...]) -> str:
    out = []
    if "near_soil_map_line" in caps:
        out.append("Your spot is close to the edge of that mapped area, and the next "
                   "one is different.")
    if "disturbed_soil" in caps:
        out.append("Part of this soil area is mapped as built-up land, where the "
                   "original soil has often been moved or covered.")
    if "mixed_soil_area" in caps:
        out.append("The mapped area is a mix of soils.")
    if "little_texture_data" in caps:
        out.append("The soil map has texture data for only part of the area.")
    return (" " + " ".join(out)) if out else ""


def soil_drainage(r: R, rd: Mapping[str, Optional[R]], caps: tuple[str, ...]) -> Text:
    cls = _text(r.value, "class", "label") or "unknown"
    mapunit = rd.get("soil_mapunit")
    name = _text(mapunit.value, "name", "muname") if mapunit else None
    display = f"Drainage: the soil map for this area shows {_lower_first(cls)} soil"
    display += f" ({name})." if name else "."
    slow = rd.get("soil_slowest_layer")
    rate = _rate(slow.value) if slow else None
    if rate:
        display += f" How fast water moves through its slowest layer: {rate}."
    reason = ("From the area soil map, which describes several acres, not your yard. "
              "Yards are also often compacted or filled during building."
              + _soil_caveats(caps))
    return Text(display, reason, sources_of([r, mapunit, slow], "ssurgo"))


def soil_texture(r: R, rd: Mapping[str, Optional[R]], caps: tuple[str, ...]) -> Text:
    name = _text(r.value, "name", "texture", "label") or "unknown"
    cls = _text(r.detail or {}, "class") or (
        _text(r.value, "class") if isinstance(r.value, Mapping) else None)
    feel = {"sandy": "loose and gritty", "loamy": "crumbly",
            "clayey": "sticky when wet"}.get(cls or "")
    display = f"Topsoil: likely {_lower_first(name)}"
    display += f" ({feel})." if feel else "."
    wh = rd.get("soil_water_holding")
    inches = _num(wh.value, "in_per_ft", "inches_per_foot") if wh else None
    if inches is not None:
        amount = "a small" if inches < 1.2 else "a medium" if inches < 2.0 else "a large"
        display += f" Holds {amount} amount of water for roots."
    reason = ("From the area soil map, not measured in your yard." + _soil_caveats(caps))
    return Text(display, reason, sources_of([r, wh], "ssurgo"))


def _acidity(ph: float) -> str:
    if ph <= 5.0:
        return "very strongly acidic"
    if ph <= 5.5:
        return "strongly acidic"
    if ph <= 6.0:
        return "moderately acidic"
    if ph <= 6.5:
        return "slightly acidic"
    if ph <= 7.3:
        return "near neutral"
    if ph <= 7.8:
        return "slightly alkaline"
    return "alkaline"


def soil_ph(r: R, caps: tuple[str, ...]) -> Text:
    ph = _num(r.value, "ph", "value")
    if ph is None:
        return missing("soil_ph", "no_data")
    display = (f"Soil acidity (pH): soils in this area are usually "
               f"{_acidity(ph)}, around {round(ph * 2) / 2:g}.")
    reason = ("Your yard may differ. A soil test from your state Cooperative Extension "
              "office gives the real number, and you can enter it here."
              + _soil_caveats(tuple(c for c in caps if c != "soil_acidity_varies")))
    return Text(display, reason, sources_of([r], "ssurgo"))


def disturbed_soil(r: R, caps: tuple[str, ...]) -> Text:
    s = share(r.value)
    if s is None:
        return missing("disturbed_soil", "no_data")
    if s >= 0.15:
        display = (f"Heads up: {_percent(s)} of this soil area is mapped as built-up "
                   "land, where the original soil has often been moved or covered. "
                   "Treat the soil values as a starting guess.")
    elif s > 0:
        display = (f"A small part ({_percent(s)}) of this soil area is mapped as "
                   "built-up land.")
    else:
        display = "The soil map shows no built-up land in this area."
    reason = ("From the soil names and kinds in the area soil map. This flag can only "
              "lower our confidence: no flag does not prove the ground was never moved.")
    return Text(display, reason, sources_of([r], "ssurgo"))


def _months(ms: Any) -> Optional[str]:
    if not isinstance(ms, (list, tuple)) or not ms:
        return None
    names = []
    for m in ms:
        if isinstance(m, int) and 1 <= m <= 12:
            names.append(date(2000, m, 1).strftime("%B"))
        elif isinstance(m, str):
            names.append(m.strip().capitalize())
    if not names:
        return None
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


_HOW_OFTEN = {"very rare": "very rarely", "rare": "rarely", "occasional": "occasionally",
              "common": "often", "frequent": "frequently",
              "very frequent": "very frequently"}


def _often(cls: str) -> str:
    c = cls.strip().lower()
    return _HOW_OFTEN.get(c, c)


def flooding(r: R, rd: Mapping[str, Optional[R]], caps: tuple[str, ...]) -> Text:
    dom = _text(r.value, "class", "frequency", "label", "dominant")
    dom_l = _lower_first(dom) if dom else None
    if dom_l is None:
        display = "Flooding: the soil map gives no flooding class here."
    elif dom_l in ("none", "no flooding"):
        display = "Flooding: none expected for most of this soil area."
    else:
        display = f"Flooding: most of this soil area floods {_often(dom_l)}."
    d = r.detail or {}
    # The worst class may sit in detail (worst, worst_share, months) or, as
    # B2a's soil source gives it, in value.worst {class, percent, months}.
    vw = r.value.get("worst") if isinstance(r.value, Mapping) else None
    if isinstance(vw, Mapping):
        worst = _text(vw, "class", "frequency")
        ws = share(vw.get("percent")) if vw.get("percent") is not None else None
        worst_months = vw.get("months")
    else:
        worst = _text(d.get("worst"))
        ws = share(d.get("worst_share")) if d.get("worst_share") is not None else None
        worst_months = d.get("months")
    if worst and _lower_first(worst) not in (dom_l, "none"):
        part = f"A small part ({_percent(ws)})" if ws is not None else "A part"
        display += f" {part} floods {_often(_lower_first(worst))}"
        months = _months(worst_months)
        display += f", in {months}." if months else "."
    pond = rd.get("soil_ponding")
    ptxt = _text(pond.value, "class", "frequency", "dominant") if pond else None
    if ptxt and _lower_first(ptxt) not in ("none", "no ponding"):
        display += f" Water may pond on the surface ({_lower_first(ptxt)})."
    reason = ("From the soil survey's month-by-month flooding and ponding records. "
              "This is not a flood insurance determination and not a Federal "
              "Emergency Management Agency flood zone." + _soil_caveats(caps))
    return Text(display, reason, sources_of([r, pond], "ssurgo"))


def _slope_class(pct: float) -> str:
    if pct < 2:
        return "flat"
    if pct < 5:
        return "gentle"
    if pct < 10:
        return "moderate"
    if pct < 20:
        return "steep"
    return "very steep"


def _survey(d: Mapping, res: Optional[float]) -> str:
    year = d.get("year")
    what = ("a laser ground survey" if res is not None and res <= 3.5
            else "an elevation survey")
    out = f"From {what}"
    if res is not None:
        out += f" at {res:g} metre detail"
    if year:
        out += f" flown in {year}"
    return out + " (United States Geological Survey 3D Elevation Program)."


def slope(r: R, caps: tuple[str, ...], default_footprint: bool) -> Text:
    pct = _num(r.value, "percent", "pct", "value")
    if pct is None:
        return missing("slope", "no_data")
    d = r.detail or {}
    cls = _text(d, "class") or _slope_class(pct)
    display = f"Steepness: {cls}, about {round(pct):g}%."
    reason = _survey(d, _num(d.get("resolution_m")))
    reason += " Leaves out 10 metres around your pin, where the house usually is."
    if default_footprint:
        reason += " " + APPROX_YARD
    return Text(display, reason, sources_of([r], "3dep"))


_COMPASS = ("north", "north-east", "east", "south-east", "south", "south-west",
            "west", "north-west")


def facing(r: R, caps: tuple[str, ...], default_footprint: bool) -> Text:
    v = r.value
    deg = _num(v, "degrees", "aspect_deg")
    word = _text(v, "direction", "label") if not isinstance(v, (int, float)) else None
    if word is None and deg is not None:
        word = _COMPASS[int(((deg % 360) + 22.5) // 45) % 8]
    if word is None:
        return missing("facing", "no_data")
    word = word.replace("_", "-").lower()
    if word == "flat":
        display = "Faces: flat, no facing direction."
    else:
        display = (f"Faces: {word}. This is the direction the ground slopes toward; "
                   "south and west facing ground runs warmer and drier.")
    d = r.detail or {}
    reason = _survey(d, _num(d.get("resolution_m")))
    if default_footprint:
        reason += " " + APPROX_YARD
    return Text(display, reason, sources_of([r], "3dep"))


_SUN_WORDS = {"full_sun": "full sun", "part_shade": "part shade", "shade": "shade"}
_COUNTED = {
    "terrain": "the slope of the ground",
    "canopy_height": "tree canopy height",
    "first_return": "trees and roofs from the laser survey",
    "tree_cover": "the tree cover percentage from satellite land cover",
    "buildings": "buildings",
}


def _list(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def sun(r: Optional[R], rd: Mapping[str, Optional[R]], caps: tuple[str, ...],
        default_footprint: bool, leaf_habit: Optional[str] = None) -> Text:
    open_sky = rd.get("open_sky_sun")
    if r is None or _text(r.value, "category") is None and not isinstance(r.value, str):
        hours = _num(open_sky.value, "hours") if open_sky else None
        if hours is None:
            return missing("sun", "no_data")
        display = (f"Sun: not known yet. With an open sky this spot would get about "
                   f"{_half(hours)} hours of direct sun a day in the growing season.")
        reason = ("Trees and buildings are not counted yet. Is it full sun (6 or more "
                  "hours), part shade (3 to 6) or shade (under 3)?")
        return Text(display, reason, sources_of([open_sky], "sunpos"))
    cat = _text(r.value, "category") or str(r.value)
    hours = _num(r.value, "hours")
    d = r.detail or {}
    display = f"Sun: {_SUN_WORDS.get(cat, _words(cat))}"
    if hours is not None:
        display += f", about {_half(hours)} hours of direct sun a day in the growing season."
    else:
        display += " in the growing season."
    counted = [c for c in d.get("counted", []) if c in _COUNTED]
    not_counted = [c for c in d.get("not_counted", []) if c in _COUNTED]
    if not counted:
        reason = "Worked out on our server from the sun's path at your latitude."
    else:
        words = [_COUNTED[c] for c in counted]
        res = _num(d.get("canopy_resolution_m"))
        if "canopy_height" in counted and res is not None:
            words[counted.index("canopy_height")] = (
                f"tree canopy mapped at {res:g} metre detail")
        reason = ("Worked out on our server from the sun's path at your latitude. "
                  f"Counts {_list(words)}.")
    if "buildings" not in counted and "buildings" not in not_counted:
        not_counted.append("buildings")
    if not_counted:
        nc = _list([_COUNTED[c] for c in not_counted])
        plural = len(not_counted) > 1 or not_counted[0] == "buildings"
        reason += f" {nc[:1].upper() + nc[1:]} {'are' if plural else 'is'} not counted."
    if leaf_habit in ("drops_leaves", "mixed") or d.get("deciduous"):
        reason += (" This is for the growing season, when leaves are out; trees that "
                   "drop their leaves let in more sun in winter.")
    if default_footprint:
        reason += " " + APPROX_YARD
    return Text(display, reason, sources_of(
        [r, open_sky, rd.get("elevation_window"), rd.get("canopy_shade")], "sunpos"))


_WATER = {
    "drains_freely": "drains freely. Rain soaks in or runs off without collecting.",
    "slow_to_drain": "slow to drain. The ground may stay soggy for a while after heavy rain.",
    "gathers_after_rain": ("water gathers here after rain. This spot sits low or collects "
                           "runoff from uphill."),
    "often_wet": "often wet. The data points to wet ground for parts of the year.",
}
_SIGNALS = {
    "drainage_class": "the soil's natural drainage class",
    "slowest_layer": "how fast water moves through the slowest soil layer",
    "runoff_group": "how much rain the soil sheds",
    "ponding": "how often the soil map shows ponding",
    "flooding": "how often the soil map shows flooding",
    "water_table": "the depth to the seasonal water table",
    "low_spot": "low spots in the elevation survey",
    "flow": "where runoff from uphill gathers",
}


def water_collects(r: R, rd: Mapping[str, Optional[R]], caps: tuple[str, ...],
                   default_footprint: bool) -> Text:
    code = _text(r.value, "class", "category") or ""
    code = code.lower().replace(" ", "_")
    if code not in _WATER:
        return missing("water_collects", "no_data")
    display = f"Where water collects: {_WATER[code]}"
    d = r.detail or {}
    agreed = [_SIGNALS[s] for s in d.get("signals", []) if s in _SIGNALS]
    reason = (f"Worked out from {_list(agreed)}." if agreed
              else "Worked out from the soil survey and the elevation survey.")
    if any(s in d.get("signals", []) for s in ("low_spot", "flow")):
        reason += " Leaves out 10 metres around your pin, where the house usually is."
    if "disturbed_soil" in caps:
        reason += " Part of this soil area is mapped as built-up land, so treat it as a starting guess."
    if "near_soil_map_line" in caps:
        reason += (" Your spot is close to the edge of the mapped soil area, and the next one "
                   "is different, so the soil part of this answer is a rough guess.")
    if default_footprint:
        reason += " " + APPROX_YARD
    reason += " This is not a flood insurance determination."
    # Name the soil survey too when its signals went into the answer.
    soil = rd.get("soil_drainage_class") if (r.detail or {}).get("soil_signals") or any(
        sig in ("drainage_class", "slowest_layer", "runoff_group", "ponding", "flooding",
                "water_table") for sig in ((r.detail or {}).get("signals") or [])) else None
    return Text(display, reason, sources_of([r, rd.get("low_spot"), soil], "drainage"))


def land_cover(r: R, rd: Mapping[str, Optional[R]]) -> Text:
    d = r.detail or {}
    label = _text(r.value, "label", "class", "name")
    v = r.value if isinstance(r.value, Mapping) else {}
    if label is None and isinstance(v.get("dominant"), Mapping):
        label = _text(v["dominant"], "name", "label")  # B2a: {code, name}
    label = label or "mixed land"
    paved = None
    for src, key in ((d, "paved_share"), (v, "paved_share"), (d, "paved_percent"),
                     (v, "paved_percent")):
        if src.get(key) is not None:
            paved = share(src[key])
            break
    display = f"Around you: mostly {_lower_first(label)}"
    display += f" ({_percent(paved)} paved or roofed)." if paved is not None else "."
    tree = rd.get("tree_cover")
    ts = share(tree.value) if tree else None
    if ts is not None:
        display += f" Trees cover {_percent(ts)} of the area."
    res = _num(d.get("resolution_m")) or 30
    reason = f"From satellite land cover mapping at {res:g} metre detail"
    if d.get("year"):
        reason += f", year {d['year']}"
    reason += (". It describes the neighbourhood, not your lot; the zones you draw are "
               "the lot-level answer.")
    return Text(display, reason, sources_of([r, tree], "nlcd"))


# --- frost dates (from season.normals.frost_normals) ------------------------------

def _day(value: Any) -> Optional[str]:
    if isinstance(value, Mapping):
        for k in ("p50", "median", "date", "typical"):
            if value.get(k):
                return _day(value[k])
        return None
    if isinstance(value, (date, datetime)):
        return f"{value.day} {value.strftime('%B')}"
    if isinstance(value, str):
        m = re.search(r"(\d{1,2})-(\d{1,2})$", value.strip())
        if m:
            d = date(2001, int(m.group(1)), int(m.group(2)))
            return f"{d.day} {d.strftime('%B')}"
    return None


_SPRING_KEYS = ("last_spring_frost", "last_frost", "spring_32f", "last_spring")
_FALL_KEYS = ("first_fall_frost", "first_frost", "fall_32f", "first_fall")


def frost_dates(normals: Mapping[str, Any], caps: tuple[str, ...]) -> Optional[Text]:
    """None when the normals hold no dates. A normals answer that already
    carries `display` and `reason` is used as written."""
    station = normals.get("station")
    src = normals.get("source")
    sources = [src if isinstance(src, Mapping) and src.get("name")
               else source("noaa_normals")]
    if isinstance(normals.get("display"), str) and isinstance(normals.get("reason"), str):
        return Text(normals["display"], normals["reason"], [dict(s) for s in sources])
    spring = next((_day(normals[k]) for k in _SPRING_KEYS if normals.get(k)), None)
    fall = next((_day(normals[k]) for k in _FALL_KEYS if normals.get(k)), None)
    if not spring and not fall:
        return None
    parts = []
    if spring:
        parts.append(f"last spring frost around {spring}")
    if fall:
        parts.append(f"first fall frost around {fall}")
    display = "Typical " + " and typical ".join(parts) + "."
    reason = "From weather station records for 1991 to 2020"
    if isinstance(station, Mapping) and station.get("name"):
        reason += f" at the {station['name']} station"
        km = _num(station.get("distance_km"))
        if km is not None:
            miles = km / 1.609
            reason += f", about {round(miles):g} miles away" if miles >= 1 else ", under a mile away"
    reason += ". Half of years come earlier than these dates and half later."
    if "stations_differ" in caps:
        reason += " Nearby stations differ by more than a week, so treat the dates as a range."
    return Text(display, reason, [dict(s) for s in sources])
