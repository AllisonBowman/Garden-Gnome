"""Soil from the United States Department of Agriculture soil survey (the
Soil Survey Geographic Database, through the Soil Data Access service).

PLAN.md section 6 ("Soil drainage", "Soil texture and water holding", "Soil
acidity", "Disturbed or built-up soil flag", "Flooding and seasonal
wetness"); build spec sections 3 and 5 (drainage from data).

Privacy: the service is only ever sent the grid-snapped block, as a WKT
polygon inside the SQL text (`Coord.WKT`). The map unit polygons inside the
block, every component of those map units, their horizons and their
month-by-month flooding, ponding and wet-soil rows come back; the pin is
placed among them here, on this server.

Levels follow the caps in PLAN.md section 6: never above "medium" (Area
estimate); "low" (Rough estimate) when 15% or more of the map unit is
built-up or disturbed, when the pin is within 30 metres of a map line whose
neighbour differs, when the dominant condition covers less than 75% of the
map unit, or (texture and water holding) when data covers less than 60% of
it; soil acidity is "low" by default.
"""
from __future__ import annotations

import math
import re
from datetime import timedelta
from typing import Any, Iterable, Optional

from app.services.site import tiles
from app.services.site.http import Coord
from app.services.site.types import Block, Reading, SourceUnavailable

SOURCE_KEY = "ssurgo"
#: The shape of the cached block answer. Bump when the queries change.
QUERY_VERSION = "sda-1"
URL = "https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest"
METHOD = "block_polygons_sampled_at_pin"
TTL = timedelta(days=90)

NEAR_LINE_M = 30.0
DISTURBED_SHARE = 15
DOMINANT_SHARE = 75
DATA_SHARE = 60
_M_PER_DEG = 111_320.0

FIELDS = ("soil_mapunit", "soil_drainage_class", "soil_slowest_layer",
          "soil_runoff_group", "soil_texture", "soil_water_holding", "soil_ph",
          "soil_disturbed_share", "soil_flooding", "soil_ponding",
          "soil_water_table")

#: Names the survey uses for built-up, moved or covered ground
#: (research-soil-landcover-hardiness.json: a national count of names).
_DISTURBED = re.compile(
    r"urban\s*land|made\s*land|udorthents|arents|dumps?\b|cut\s*and\s*fill|"
    r"fill\s*land|pits?\b|landfill|quarr", re.IGNORECASE)

#: Worst first, as the survey ranks them.
FLOOD_ORDER = ("Very frequent", "Frequent", "Occasional", "Rare", "Very rare", "None")
POND_ORDER = ("Frequent", "Occasional", "Rare", "None")
MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")

#: Saturated hydraulic conductivity classes, micrometres per second (Soil
#: Survey Manual), slowest first.
KSAT_CLASSES = ((0.01, "very low"), (0.1, "low"), (1.0, "moderately low"),
                (10.0, "moderately high"), (100.0, "high"), (math.inf, "very high"))


# --- fetching ------------------------------------------------------------------------

def _wkt_box(block: Block) -> str:
    w, s, e, n = (f"{v:.4f}" for v in (block.west, block.south, block.east, block.north))
    return f"POLYGON(({w} {s},{e} {s},{e} {n},{w} {n},{w} {s}))"


def _query(client, sql: str) -> list[dict]:
    resp = client.post(URL, json={"query": sql, "format": "JSON+COLUMNNAME"},
                       coords={"query": Coord.WKT}, source_key=SOURCE_KEY)
    text = resp.text.strip()
    if not text:
        return []  # the service answers an empty body when nothing matches
    try:
        table = resp.json().get("Table", [])
    except ValueError as exc:
        raise SourceUnavailable(SOURCE_KEY, f"unreadable answer: {exc}") from None
    if not table:
        return []
    head, *rows = table
    return [dict(zip(head, r)) for r in rows]


def fetch_block(client, block: Block) -> dict:
    """Everything the profile needs for one block, as plain JSON."""
    aoi = _wkt_box(block)
    polygons = _query(client, (
        "~DeclareGeometry(@aoi)~ "
        f"SELECT @aoi = geometry::STGeomFromText('{aoi}', 4326); "
        "SELECT P.mukey, P.mupolygongeo.STIntersection(@aoi).STAsText() AS wkt "
        "FROM mupolygon P WHERE P.mupolygongeo.STIntersects(@aoi) = 1"))
    out = {"polygons": [[p["mukey"], p["wkt"]] for p in polygons],
           "mapunits": [], "components": [], "months": [], "wet": []}
    keys = sorted({str(p["mukey"]) for p in polygons if str(p["mukey"]).isdigit()})
    if not keys:
        return out
    ks = ",".join(keys)
    out["mapunits"] = _query(client, (
        "SELECT mu.mukey, mu.muname, mu.mukind, l.areasymbol, l.areaname, "
        "sa.saverest, ma.drclassdcd, ma.hydgrpdcd, ma.wtdepannmin, "
        "ma.flodfreqdcd, ma.pondfreqprs, ma.aws0150wta "
        "FROM mapunit mu JOIN legend l ON l.lkey = mu.lkey "
        "LEFT JOIN sacatalog sa ON sa.areasymbol = l.areasymbol "
        "LEFT JOIN muaggatt ma ON ma.mukey = mu.mukey "
        f"WHERE mu.mukey IN ({ks})"))
    out["components"] = _query(client, (
        "SELECT c.mukey, c.cokey, c.compname, c.comppct_r, c.majcompflag, "
        "c.compkind, c.drainagecl, c.hydgrp, h.hzdept_r, h.hzdepb_r, h.awc_r, "
        "h.ph1to1h2o_r, h.sandtotal_r, h.claytotal_r, "
        "(SELECT TOP 1 tg.texdesc FROM chtexturegrp tg WHERE tg.chkey = h.chkey "
        "AND tg.rvindicator = 'Yes') AS texdesc, "
        "(SELECT MIN(h2.ksat_r) FROM chorizon h2 WHERE h2.cokey = c.cokey) AS ksat_min, "
        "(SELECT TOP 1 h3.hzdept_r FROM chorizon h3 WHERE h3.cokey = c.cokey "
        "AND h3.ksat_r IS NOT NULL ORDER BY h3.ksat_r ASC, h3.hzdept_r ASC) AS ksat_min_depth, "
        "(SELECT SUM((h4.hzdepb_r - h4.hzdept_r) * h4.awc_r) FROM chorizon h4 "
        "WHERE h4.cokey = c.cokey AND h4.hzdept_r < 150) AS aws150 "
        "FROM component c LEFT JOIN chorizon h ON h.cokey = c.cokey "
        "AND h.hzdept_r = (SELECT MIN(hzdept_r) FROM chorizon WHERE cokey = c.cokey) "
        f"WHERE c.mukey IN ({ks}) ORDER BY c.mukey, c.comppct_r DESC"))
    out["months"] = _query(client, (
        "SELECT c.cokey, cm.month, cm.flodfreqcl, cm.floddurcl, cm.pondfreqcl, "
        "cm.ponddurcl FROM component c JOIN comonth cm ON cm.cokey = c.cokey "
        f"WHERE c.mukey IN ({ks}) AND (cm.flodfreqcl NOT IN ('None') "
        "OR cm.pondfreqcl NOT IN ('None'))"))
    out["wet"] = _query(client, (
        "SELECT c.cokey, cm.month, MIN(sm.soimoistdept_r) AS depth "
        "FROM component c JOIN comonth cm ON cm.cokey = c.cokey "
        "JOIN cosoilmoist sm ON sm.comonthkey = cm.comonthkey "
        f"WHERE c.mukey IN ({ks}) AND sm.soimoiststat = 'Wet' "
        "GROUP BY c.cokey, cm.month"))
    return out


def load_block(block: Block, *, client, session=None) -> dict:
    """The block's soil answer, from the tile cache when a session is given."""
    if session is None:
        return fetch_block(client, block)
    cached = tiles.get_json(session, SOURCE_KEY, QUERY_VERSION, f"{block.key}_ssurgo")
    if cached is not None:
        return cached
    data = fetch_block(client, block)
    tiles.put_json(session, SOURCE_KEY, QUERY_VERSION, f"{block.key}_ssurgo", data, ttl=TTL)
    return data


# --- geometry, on this server ------------------------------------------------------

_NON_AREA = re.compile(r"(?:MULTI)?(?:POINT|LINESTRING)\s*(?:EMPTY|\((?:[^()]|\([^()]*\))*\))",
                       re.IGNORECASE)
_RING = re.compile(r"\(([^()]+)\)")


def parse_rings(wkt: str) -> list[list[tuple[float, float]]]:
    """Every ring of the polygonal parts of a WKT geometry, as (lng, lat)."""
    rings = []
    for body in _RING.findall(_NON_AREA.sub(" ", wkt or "")):
        pts = []
        for pair in body.split(","):
            parts = pair.split()
            if len(parts) >= 2:
                pts.append((float(parts[0]), float(parts[1])))
        if len(pts) >= 3:
            rings.append(pts)
    return rings


def _inside(rings, x: float, y: float) -> bool:
    """Even-odd rule over all rings, so holes and multipart shapes work."""
    inside = False
    for ring in rings:
        n = len(ring)
        for i in range(n):
            x1, y1 = ring[i]
            x2, y2 = ring[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                xc = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if xc > x:
                    inside = not inside
    return inside


def _distance_m(rings, lng: float, lat: float) -> float:
    """Distance from the point to the nearest edge of the rings, metres."""
    kx = _M_PER_DEG * math.cos(math.radians(lat))
    best = math.inf
    for ring in rings:
        n = len(ring)
        for i in range(n):
            ax, ay = (ring[i][0] - lng) * kx, (ring[i][1] - lat) * _M_PER_DEG
            bx, by = (ring[(i + 1) % n][0] - lng) * kx, (ring[(i + 1) % n][1] - lat) * _M_PER_DEG
            dx, dy = bx - ax, by - ay
            seg = dx * dx + dy * dy
            t = 0.0 if seg == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / seg))
            px, py = ax + t * dx, ay + t * dy
            best = min(best, math.hypot(px, py))
    return best


# --- reading the map unit ------------------------------------------------------------

def _num(v) -> Optional[float]:
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


def _pct(v) -> int:
    n = _num(v)
    return int(round(n)) if n is not None else 0


def is_disturbed(comp: dict) -> bool:
    return bool(_DISTURBED.search(comp.get("compname") or ""))


def _has_data(comp: dict) -> bool:
    return comp.get("drainagecl") is not None or _num(comp.get("awc_r")) is not None


def _share_by(comps: Iterable[dict], key) -> dict[str, int]:
    out: dict[str, int] = {}
    for c in comps:
        k = key(c)
        if k is None:
            continue
        out[k] = out.get(k, 0) + _pct(c.get("comppct_r"))
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def _dominant(shares: dict[str, int]) -> tuple[Optional[str], int]:
    if not shares:
        return None, 0
    k = next(iter(shares))
    return k, shares[k]


def _family(texture: Optional[str], sand, clay) -> Optional[str]:
    """Sandy, loamy or clayey, from the survey's texture words, else from
    sand and clay percentages."""
    t = (texture or "").lower()
    if t:
        if "clay" in t and "loam" not in t:
            return "clayey"
        if "sand" in t and "loam" not in t:
            return "sandy"
        if "loam" in t:
            return "loamy"
    s, c = _num(sand), _num(clay)
    if s is None or c is None:
        return None
    if c >= 40:
        return "clayey"
    if s >= 70 and c < 15:
        return "sandy"
    return "loamy"


def _ksat_class(v: float) -> str:
    for limit, label in KSAT_CLASSES:
        if v < limit:
            return label
    return KSAT_CLASSES[-1][1]  # pragma: no cover


def _water_class(inches_per_foot: float) -> str:
    if inches_per_foot < 1.0:
        return "low"
    if inches_per_foot <= 2.0:
        return "medium"
    return "high"


def _months_by_component(rows: list[dict], freq_key: str, dur_key: str,
                         order: tuple[str, ...]) -> dict[str, dict]:
    """cokey -> {"class": worst class, "months": [...], "duration": str}."""
    rank = {c: i for i, c in enumerate(order)}
    out: dict[str, dict] = {}
    for r in rows:
        cls = r.get(freq_key)
        if not cls or cls == "None" or cls not in rank:
            continue
        entry = out.setdefault(str(r["cokey"]), {"class": cls, "months": set(), "durations": set()})
        if rank[cls] < rank[entry["class"]]:
            entry["class"] = cls
        if r.get("month") in MONTHS:
            entry["months"].add(r["month"])
        if r.get(dur_key):
            entry["durations"].add(r[dur_key])
    for e in out.values():
        e["months"] = [m for m in MONTHS if m in e["months"]]
        e["durations"] = sorted(e["durations"])
    return out


def _wetness(comps: list[dict], by_co: dict[str, dict], order: tuple[str, ...]) -> dict:
    rank = {c: i for i, c in enumerate(order)}
    rows = []
    for c in comps:
        info = by_co.get(str(c["cokey"]))
        rows.append({"component": c.get("compname"), "percent": _pct(c.get("comppct_r")),
                     "class": info["class"] if info else "None",
                     "months": info["months"] if info else [],
                     "durations": info["durations"] if info else []})
    shares: dict[str, int] = {}
    for r in rows:
        shares[r["class"]] = shares.get(r["class"], 0) + r["percent"]
    shares = dict(sorted(shares.items(), key=lambda kv: -kv[1]))
    dominant, dom_share = _dominant(shares)
    wet = [r for r in rows if r["class"] != "None"]
    worst = None
    if wet:
        worst_cls = min((r["class"] for r in wet), key=lambda c: rank[c])
        hits = [r for r in wet if r["class"] == worst_cls]
        months = sorted({m for r in hits for m in r["months"]}, key=MONTHS.index)
        worst = {"class": worst_cls, "percent": sum(r["percent"] for r in hits),
                 "months": months, "components": [r["component"] for r in hits],
                 "durations": sorted({d for r in hits for d in r["durations"]})}
    return {"dominant": dominant, "dominant_percent": dom_share, "worst": worst,
            "by_component": rows, "agree": len(shares) <= 1}


def summarise_mapunit(data: dict, mukey: str) -> dict:
    """Plain facts about one map unit (no levels)."""
    mu = next((m for m in data["mapunits"] if str(m["mukey"]) == mukey), {})
    comps = [c for c in data["components"] if str(c["mukey"]) == mukey]
    soil = [c for c in comps if not is_disturbed(c)]
    with_data = [c for c in soil if _has_data(c)]
    total = sum(_pct(c.get("comppct_r")) for c in comps) or 100
    data_share = round(100 * sum(_pct(c.get("comppct_r")) for c in with_data) / total)
    disturbed = [c for c in comps if is_disturbed(c)]
    disturbed_share = round(100 * sum(_pct(c.get("comppct_r")) for c in disturbed) / total)
    main = max(with_data, key=lambda c: _pct(c.get("comppct_r")), default=None)
    drainage = _share_by(with_data, lambda c: c.get("drainagecl"))
    groups = _share_by(soil, lambda c: c.get("hydgrp"))
    return {
        "mukey": mukey, "mapunit": mu, "components": comps, "soil": soil,
        "with_data": with_data, "main": main, "data_share": data_share,
        "no_data_share": 100 - data_share - disturbed_share if comps else 100,
        "disturbed": disturbed, "disturbed_share": disturbed_share,
        "drainage": drainage, "groups": groups,
        "texture": (main or {}).get("texdesc"),
    }


def _component_mix(summary: dict) -> list[dict]:
    return [{"name": c.get("compname"), "percent": _pct(c.get("comppct_r")),
             "kind": c.get("compkind"), "major": (c.get("majcompflag") or "").strip() == "Yes",
             "drainage": c.get("drainagecl"), "runoff_group": c.get("hydgrp"),
             "texture": c.get("texdesc"), "disturbed": is_disturbed(c),
             "has_data": _has_data(c)}
            for c in summary["components"]]


def _neighbour_differs(here: dict, there: dict) -> bool:
    a = (_dominant(here["drainage"])[0], _dominant(here["groups"])[0],
         _family(here["texture"], None, None))
    b = (_dominant(there["drainage"])[0], _dominant(there["groups"])[0],
         _family(there["texture"], None, None))
    return a != b


# --- readings -------------------------------------------------------------------------

def _version(mu: dict) -> str:
    area = mu.get("areasymbol") or "unknown area"
    when = (mu.get("saverest") or "").split(" ")[0]
    return f"{area} {when}".strip()


def _unknown(reason: str, version: str = "") -> list[Reading]:
    return [Reading(field=f, value=None, level="unknown", provenance="public_map",
                    source_key=SOURCE_KEY, source_version=version or "none",
                    method=METHOD, reason_codes=(reason,))
            for f in FIELDS]


def read(block: Block, pin: tuple[float, float], footprint: dict | None, *,
         client, session=None) -> list[Reading]:
    """Soil readings at the pin. `session`, when given, keeps the block's
    answer in the tile cache."""
    data = load_block(block, client=client, session=session)
    return readings_from(data, pin)


def readings_from(data: dict, pin: tuple[float, float]) -> list[Reading]:
    lat, lng = pin
    shapes = [(str(k), parse_rings(w)) for k, w in data.get("polygons", [])]
    here_key = next((k for k, rings in shapes if rings and _inside(rings, lng, lat)), None)
    if here_key is None:
        return _unknown("no_soil_map_here")

    here = summarise_mapunit(data, here_key)
    mu = here["mapunit"]
    version = _version(mu)

    # The nearest line to a different map unit. Any different map unit counts
    # as a neighbour that differs (PLAN.md section 6 caps the Arboretum test
    # point, 16.6 m from a different slope phase, at "Rough estimate"); the
    # detail also says whether drainage, runoff group or texture differ.
    near_key, near_m = None, math.inf
    for k, rings in shapes:
        if k == here_key or not rings:
            continue
        d = _distance_m(rings, lng, lat)
        if d < near_m:
            near_key, near_m = k, d
    neighbour = None
    properties_differ = False
    if near_key is not None:
        there = summarise_mapunit(data, near_key)
        properties_differ = _neighbour_differs(here, there)
        neighbour = {"mukey": near_key, "name": there["mapunit"].get("muname"),
                     "drainage": _dominant(there["drainage"])[0],
                     "runoff_group": _dominant(there["groups"])[0],
                     "texture": there["texture"],
                     "drainage_runoff_or_texture_differ": properties_differ}
    differs = near_key is not None
    near_line = near_m < NEAR_LINE_M
    disturbed = here["disturbed_share"] >= DISTURBED_SHARE

    base_codes = []
    if near_line:
        base_codes.append("near_map_line")
    if disturbed:
        base_codes.append("disturbed_soil")

    def level(extra_low: bool = False, codes: Iterable[str] = ()) -> tuple[str, tuple]:
        c = tuple(base_codes) + tuple(codes)
        return ("low" if (near_line or disturbed or extra_low) else "medium"), c

    def reading(field, value, lvl, codes, detail=None):
        return Reading(field=field, value=value, level=lvl, provenance="public_map",
                       source_key=SOURCE_KEY, source_version=version, method=METHOD,
                       reason_codes=codes, detail=detail)

    common = {"mukey": here_key, "map_unit": mu.get("muname"),
              "survey_area": mu.get("areaname"), "survey_version": mu.get("saverest"),
              "no_data_percent": max(0, here["no_data_share"])}
    out: list[Reading] = []

    lvl, codes = level()
    out.append(reading("soil_mapunit", {
        "mukey": here_key, "name": mu.get("muname"), "kind": mu.get("mukind"),
        "area_symbol": mu.get("areasymbol"), "area_name": mu.get("areaname"),
    }, lvl, codes, {
        **common,
        "distance_to_line_m": None if near_key is None else round(near_m, 1),
        "neighbour": neighbour, "neighbour_differs": differs,
        "components": _component_mix(here),
    }))

    main = here["main"]
    if main is None:
        # Water, built-up land or a map unit the survey gives no soil data for.
        reason = "no_soil_data_in_map_unit"
        for f in FIELDS[1:]:
            if f == "soil_disturbed_share":
                continue
            out.append(reading(f, None, "unknown", (reason,), common))
        lvl, codes = level()
        out.append(_disturbed_reading(reading, here, lvl, codes, common))
        return _order(out)

    # Drainage class: dominant condition over components with data.
    dom, share = _dominant(here["drainage"])
    lvl, codes = level(share < DOMINANT_SHARE,
                       ("mixed_map_unit",) if share < DOMINANT_SHARE else ())
    out.append(reading("soil_drainage_class", dom, lvl, codes,
                       {**common, "by_class": here["drainage"], "dominant_percent": share,
                        "map_unit_summary": mu.get("drclassdcd")}))

    # Slowest layer of the main soil.
    ksat = _num(main.get("ksat_min"))
    lvl, codes = level()
    out.append(reading("soil_slowest_layer", None if ksat is None else {
        "ksat_um_per_s": ksat, "class": _ksat_class(ksat),
        "depth_cm": _num(main.get("ksat_min_depth")),
    }, lvl if ksat is not None else "unknown", codes if ksat is not None else ("no_data",),
        {**common, "component": main.get("compname"),
         "component_percent": _pct(main.get("comppct_r"))}))

    # Runoff group (hydrologic soil group), dominant condition.
    dom, share = _dominant(here["groups"])
    lvl, codes = level(share < DOMINANT_SHARE,
                       ("mixed_map_unit",) if share < DOMINANT_SHARE else ())
    out.append(reading("soil_runoff_group", dom, lvl if dom else "unknown",
                       codes if dom else ("no_data",),
                       {**common, "by_group": here["groups"], "dominant_percent": share}))

    # Surface texture of the main soil.
    thin = here["data_share"] < DATA_SHARE
    lvl, codes = level(thin, ("thin_data",) if thin else ())
    texture = main.get("texdesc")
    out.append(reading("soil_texture", {
        "texture": texture,
        "family": _family(texture, main.get("sandtotal_r"), main.get("claytotal_r")),
        "sand_percent": _num(main.get("sandtotal_r")),
        "clay_percent": _num(main.get("claytotal_r")),
        "depth_cm": [_num(main.get("hzdept_r")), _num(main.get("hzdepb_r"))],
    }, lvl, codes, {**common, "component": main.get("compname"),
                    "data_percent": here["data_share"]}))

    # Water holding: weighted over components with data, built-up excluded.
    weights = [(c, _pct(c.get("comppct_r"))) for c in here["with_data"]
               if _num(c.get("aws150")) is not None]
    wsum = sum(w for _, w in weights)
    if wsum:
        aws = sum(_num(c["aws150"]) * w for c, w in weights) / wsum
        per_foot = aws / 150.0 * 12.0
        out.append(reading("soil_water_holding", {
            "inches_per_foot": round(per_foot, 2), "class": _water_class(per_foot),
            "available_water_cm_0_150": round(aws, 1),
        }, lvl, codes, {**common, "data_percent": here["data_share"],
                        "map_unit_summary_cm": _num(mu.get("aws0150wta"))}))
    else:
        out.append(reading("soil_water_holding", None, "unknown", ("no_data",), common))

    # Acidity: surface value with the range; rough by default.
    phs = [_num(c.get("ph1to1h2o_r")) for c in here["with_data"]]
    phs = [p for p in phs if p is not None]
    main_ph = _num(main.get("ph1to1h2o_r"))
    _, codes = level()
    out.append(reading("soil_ph", None if main_ph is None else {
        "ph": main_ph, "range": [min(phs), max(phs)] if phs else None,
    }, "low" if main_ph is not None else "unknown",
        codes + ("rough_by_default",) if main_ph is not None else ("no_data",),
        {**common, "component": main.get("compname")}))

    lvl, codes = level()
    out.append(_disturbed_reading(reading, here, lvl, codes, common))

    # Flooding and ponding, month by month (the summary row is not enough).
    flood_by = _months_by_component(data.get("months", []), "flodfreqcl", "floddurcl", FLOOD_ORDER)
    pond_by = _months_by_component(data.get("months", []), "pondfreqcl", "ponddurcl", POND_ORDER)
    for field, by, order in (("soil_flooding", flood_by, FLOOD_ORDER),
                             ("soil_ponding", pond_by, POND_ORDER)):
        w = _wetness(here["components"], by, order)
        lvl, codes = level(not w["agree"], () if w["agree"] else ("components_differ",))
        out.append(reading(field, {"dominant": w["dominant"],
                                   "dominant_percent": w["dominant_percent"],
                                   "worst": w["worst"]},
                           lvl, codes, {**common, "by_component": w["by_component"]}))

    # Seasonal water table: the shallowest wet layer, by component and month.
    wet: dict[str, dict] = {}
    for r in data.get("wet", []):
        d = _num(r.get("depth"))
        if d is None:
            continue
        e = wet.setdefault(str(r["cokey"]), {"depth_cm": d, "months": set()})
        e["depth_cm"] = min(e["depth_cm"], d)
        if r.get("month") in MONTHS:
            e["months"].add(r["month"])
    rows = []
    for c in here["soil"]:
        e = wet.get(str(c["cokey"]))
        rows.append({"component": c.get("compname"), "percent": _pct(c.get("comppct_r")),
                     "depth_cm": e["depth_cm"] if e else None,
                     "months": [m for m in MONTHS if e and m in e["months"]]})
    main_row = next((r for r in rows if r["component"] == main.get("compname")), None)
    shallow = min((r for r in rows if r["depth_cm"] is not None),
                  key=lambda r: r["depth_cm"], default=None)
    lvl, codes = level()
    out.append(reading("soil_water_table", {
        "depth_cm": main_row["depth_cm"] if main_row else None,
        "months": main_row["months"] if main_row else [],
        "shallowest": None if shallow is None else {
            "depth_cm": shallow["depth_cm"], "component": shallow["component"],
            "percent": shallow["percent"], "months": shallow["months"]},
    }, lvl, codes + (() if shallow else ("not_within_reported_depth",)),
        {**common, "by_component": rows,
         "map_unit_summary_cm": _num(mu.get("wtdepannmin"))}))

    return _order(out)


def _disturbed_reading(reading, here: dict, lvl: str, codes: tuple, common: dict) -> Reading:
    share = here["disturbed_share"]
    return reading("soil_disturbed_share", {
        "percent": share,
        "components": [c.get("compname") for c in here["disturbed"]],
        "flag": share >= DISTURBED_SHARE,
    }, lvl, codes, common)


def _order(readings: list[Reading]) -> list[Reading]:
    rank = {f: i for i, f in enumerate(FIELDS)}
    return sorted(readings, key=lambda r: rank[r.field])
