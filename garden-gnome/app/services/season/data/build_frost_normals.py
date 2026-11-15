"""Builds frost_normals.json from the NOAA 1991 to 2020 climate normals.

Run by hand, off the request path, when a new edition appears (the next is
the 2001 to 2030 normals, about 2031). It reads two archives published by the
National Centers for Environmental Information (NCEI), unpacked locally:

  annual/seasonal, by station (one CSV per station):
    https://www.ncei.noaa.gov/data/normals-annualseasonal/1991-2020/archive/
    us-climate-normals_1991-2020_v1.0.1_annualseasonal_multivariate_by-station_c20230404.tar.gz
  daily temperature, by variable (dly-temp-normal.csv):
    https://www.ncei.noaa.gov/data/normals-daily/1991-2020/archive/
    us-climate-normals_1991-2020_v1.0.1_daily_temperature_by-variable_c20230403.tar.gz

    python build_frost_normals.py ANNUAL_DIR DLY_TEMP_CSV OUT_JSON

Only stations that publish first-and-last freeze probabilities are kept.
Dates are stored as small integers so the file stays small:
  fall dates   days after 1 July   (1 July = 0; may run past 31 December)
  spring dates days after 1 January (1 January = 0; may be negative)
Missing values are null.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

THRESHOLDS = (36, 32, 28)
PERCENTS = (10, 50, 90)
#: Spring Index stand-in (see README): cumulative degree days above 32 F from
#: 1 January on the daily normal mean. Engineering defaults calibrated on two
#: stations, not published values.
GDD_BASE_F = 32.0
GDD_FIRST_LEAF = 470.0
GDD_FIRST_BLOOM = 1000.0


def _fall_offset(mmdd: str):
    m, d = (int(x) for x in mmdd.split("/"))
    off = (date(2001 if m >= 7 else 2002, m, d) - date(2001, 7, 1)).days
    return off


def _spring_offset(mmdd: str):
    m, d = (int(x) for x in mmdd.split("/"))
    if m >= 8:  # a "last" date in late year belongs before 1 January
        return (date(2000, m, d) - date(2001, 1, 1)).days
    return (date(2001, m, d) - date(2001, 1, 1)).days


def _date_value(raw):
    raw = (raw or "").strip()
    return raw if "/" in raw else None


def _num(raw):
    try:
        v = float((raw or "").strip())
    except ValueError:
        return None
    return None if v <= -999 else v


def read_annual(annual_dir: Path) -> dict:
    out = {}
    for f in sorted(annual_dir.glob("*.csv")):
        with f.open(newline="") as fh:
            row = next(csv.DictReader(fh), None)
        if not row or "ANN-TMIN-PRBFST-T32FP50" not in row:
            continue
        fall, spring = [], []
        for t in THRESHOLDS:
            for p in PERCENTS:
                fv = _date_value(row.get(f"ANN-TMIN-PRBFST-T{t}FP{p}"))
                sv = _date_value(row.get(f"ANN-TMIN-PRBLST-T{t}FP{p}"))
                fall.append(_fall_offset(fv) if fv else None)
                spring.append(_spring_offset(sv) if sv else None)
        occ = []
        for t in ("036", "032", "028"):
            v = _num(row.get(f"ANN-TMIN-PRBOCC-LSTH{t}"))
            occ.append(None if v is None else round(v * 100) if v <= 1 else round(v))
        if all(v is None for v in fall + spring):
            continue
        sid = row["STATION"].strip()
        out[sid] = {
            "name": row["NAME"].strip(),
            "lat": float(row["LATITUDE"]), "lng": float(row["LONGITUDE"]),
            "elev_m": _num(row["ELEVATION"]),
            "fall": fall, "spring": spring, "occ": occ,
        }
    return out


def read_daily(path: Path, keep: set) -> dict:
    """Per station: 365 (tmin, tavg) pairs, 29 February dropped."""
    rows: dict[str, list] = {}
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            sid = r["GHCN_ID"].strip()
            if sid not in keep or (r["month"] == "02" and r["day"] == "29"):
                continue
            rows.setdefault(sid, []).append(
                (int(r["month"]), int(r["day"]),
                 _num(r["DLY-TMIN-NORMAL"]), _num(r["DLY-TAVG-NORMAL"])))
    return rows


def daily_dates(days: list) -> dict | None:
    if len(days) != 365 or any(d[2] is None or d[3] is None for d in days):
        return None
    jan1 = date(2001, 1, 1)
    doy = [(date(2001, m, d) - jan1).days for m, d, _, _ in days]
    tmin = [d[2] for d in days]
    tavg = [d[3] for d in days]
    jul1 = (date(2001, 7, 1) - jan1).days

    def fall_first(series, limit):
        # From 1 July onward, wrapping into the next year.
        for k in range(365):
            i = (jul1 + k) % 365
            if series[i] <= limit:
                return k
        return None

    def spring_first_at_or_above(series, limit):
        for i in range(jul1):
            if series[i] >= limit and all(series[j] >= limit for j in range(i, min(i + 7, 365))):
                return doy[i]
        return None

    def gdd_date(threshold):
        total = 0.0
        for i in range(365):
            total += max(0.0, tavg[i] - GDD_BASE_F)
            if total >= threshold:
                return doy[i]
        return None

    return {
        "fall_low55": fall_first(tmin, 55.0),
        "fall_low50": fall_first(tmin, 50.0),
        "fall_mean45": fall_first(tavg, 45.0),
        "spring_low50": spring_first_at_or_above(tmin, 50.0),
        "first_leaf": gdd_date(GDD_FIRST_LEAF),
        "first_bloom": gdd_date(GDD_FIRST_BLOOM),
        "coldest_mean": round(min(tavg), 1),
    }


DAILY_KEYS = ("fall_low55", "fall_low50", "fall_mean45", "spring_low50",
              "first_leaf", "first_bloom", "coldest_mean")


def main(annual_dir: str, dly_csv: str, out_path: str) -> None:
    ann = read_annual(Path(annual_dir))
    dly = read_daily(Path(dly_csv), set(ann))
    stations = []
    for sid, s in sorted(ann.items()):
        dd = daily_dates(dly.get(sid, [])) or {}
        stations.append([
            sid, s["name"], round(s["lat"], 4), round(s["lng"], 4),
            None if s["elev_m"] is None else round(s["elev_m"]),
            s["fall"], s["spring"], s["occ"],
            [dd.get(k) for k in DAILY_KEYS] if dd else None,
        ])
    doc = {
        "source": "NOAA National Centers for Environmental Information, "
                  "U.S. Climate Normals 1991-2020, version 1.0.1",
        "fields": ["id", "name", "lat", "lng", "elev_m", "fall", "spring", "occ", "daily"],
        "fall_spring_order": [f"{t}F_p{p}" for t in THRESHOLDS for p in PERCENTS],
        "occ_order": ["36F", "32F", "28F"],
        "daily_order": list(DAILY_KEYS),
        "gdd": {"base_f": GDD_BASE_F, "first_leaf": GDD_FIRST_LEAF,
                "first_bloom": GDD_FIRST_BLOOM},
        "stations": stations,
    }
    Path(out_path).write_text(json.dumps(doc, separators=(",", ":")))
    print(f"{len(stations)} stations, {sum(1 for s in stations if s[8])} with daily dates")


if __name__ == "__main__":
    main(*sys.argv[1:4])
