"""Perenual API client and field mapper.

Maps Perenual's species-details + care-guide responses onto our
SpeciesCreate schema. Every mapped record is tagged source="perenual" with
the Perenual species id in source_ref for traceability.

Requires PERENUAL_API_KEY (Premium tier — the care-guide endpoint and the
`indoor` filter are paid features). A mock mode reads JSON fixtures from a
directory instead of the network, for tests and dry runs.
"""
import json
import os
import re
import time
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()  # pick up PERENUAL_API_KEY from garden-gnome/.env

BASE_V2 = "https://perenual.com/api/v2"
BASE_V1 = "https://perenual.com/api"  # care-guide list still lives here

# Fallback watering intervals (days) when watering_general_benchmark is
# missing/unparseable, keyed by Perenual's coarse watering category.
WATERING_FALLBACK = {
    "frequent": (3, 7),
    "average": (7, 14),
    "minimum": (14, 30),
    "none": (30, 60),
}

# Derived indoor humidity comfort ranges by watering category. Perenual has
# no humidity field; this heuristic is recorded as a trait so reviewers know
# the value is derived, not sourced.
HUMIDITY_BY_WATERING = {
    "frequent": (50, 70),
    "average": (40, 60),
    "minimum": (30, 50),
    "none": (20, 40),
}

# USDA hardiness zone -> approximate coldest survivable temperature (°F)
ZONE_MIN_F = {
    1: -60, 2: -50, 3: -40, 4: -30, 5: -20, 6: -10, 7: 0,
    8: 10, 9: 20, 10: 30, 11: 40, 12: 50, 13: 60,
}

SUNLIGHT_MAP = {
    "full shade": "low",
    "deep shade": "low",
    "part shade": "medium",
    "partial shade": "medium",
    "filtered shade": "medium",
    "sun-part shade": "bright_indirect",
    "part sun": "bright_indirect",
    "part sun/part shade": "bright_indirect",
    "sun/part shade": "bright_indirect",
    "full sun": "direct",
    "full sun only if soil kept moist": "direct",
}


class PerenualClient:
    """Thin client with retry/backoff. Pass mock_dir to read fixtures
    (species-list.json, details-<id>.json, care-guide-<id>.json) instead of
    hitting the network."""

    def __init__(self, api_key: Optional[str] = None, mock_dir: Optional[str] = None):
        self.mock_dir = Path(mock_dir) if mock_dir else None
        self.api_key = api_key or os.getenv("PERENUAL_API_KEY", "")
        if not self.mock_dir and not self.api_key:
            raise RuntimeError(
                "PERENUAL_API_KEY is not set. Get a Premium key at "
                "https://perenual.com/subscription-api-pricing and export it, "
                "or run with --mock-dir for fixture-based testing."
            )

    # Probed 2026-07-08: 10 rapid requests at 0.5s spacing all pass, shared
    # 10k/day quota. 1s pacing is comfortably polite.
    MIN_INTERVAL = 1.0
    _last_request = 0.0

    def _get(self, url: str, params: dict) -> dict:
        params = {**params, "key": self.api_key}
        for attempt in range(7):
            wait = self.MIN_INTERVAL - (time.monotonic() - PerenualClient._last_request)
            if wait > 0:
                time.sleep(wait)
            PerenualClient._last_request = time.monotonic()
            try:
                resp = httpx.get(url, params=params, timeout=30.0)
                if resp.status_code == 429:
                    # Sustained burst quotas can last minutes — wait them out
                    # (5s, 10s, 20s, ... ~5min total patience)
                    time.sleep(min(2 ** attempt * 5, 120))
                    continue
                resp.raise_for_status()
                return resp.json()
            except (httpx.RequestError, json.JSONDecodeError):
                if attempt == 6:
                    raise
                time.sleep(2 ** attempt)
        raise RuntimeError(f"Perenual request kept failing: {url}")

    def _mock(self, name: str) -> Optional[dict]:
        path = self.mock_dir / name
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def search(self, query: str) -> list[dict]:
        """Search species by name; returns the data array (may be empty)."""
        if self.mock_dir:
            listing = self._mock("species-list.json") or {"data": []}
            q = _norm(query)
            return [
                row for row in listing["data"]
                if q in _norm(row.get("common_name", ""))
                or any(q in _norm(s) for s in _as_list(row.get("scientific_name")))
            ]
        return self._get(f"{BASE_V2}/species-list", {"q": query}).get("data", [])

    def list_indoor(self, page: int) -> dict:
        """One page of the indoor species listing (Premium filter)."""
        return self.list_filtered(page, indoor=1)

    def list_filtered(self, page: int, **filters) -> dict:
        """One page of the species listing with arbitrary filters
        (e.g. hardiness=11)."""
        if self.mock_dir:
            return self._mock("species-list.json") or {"data": [], "last_page": 1}
        return self._get(f"{BASE_V2}/species-list", {**filters, "page": page})

    def details(self, species_id: int) -> Optional[dict]:
        if self.mock_dir:
            return self._mock(f"details-{species_id}.json")
        return self._get(f"{BASE_V2}/species/details/{species_id}", {})

    def care_guide_sections(
        self, species_id: int, expect_scientific: str = "",
    ) -> list[dict]:
        """Care-guide sections [{type, description}, ...]; empty when absent.

        When expect_scientific is given, the guide is only returned if its
        plant name matches — guards against attaching another species' care
        text if the guide endpoint's id space ever drifts from v2 ids."""
        if self.mock_dir:
            guide = self._mock(f"care-guide-{species_id}.json")
        else:
            guide = self._get(
                f"{BASE_V1}/species-care-guide-list", {"species_id": species_id}
            )
        if not guide or not guide.get("data"):
            return []
        entry = guide["data"][0]
        if expect_scientific:
            guide_names = {_norm(s) for s in _as_list(entry.get("scientific_name"))}
            guide_names.add(_norm(entry.get("common_name", "")))
            if _norm(expect_scientific) not in guide_names:
                return []
        return entry.get("section", [])


# ── Mapping helpers ───────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _as_list(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _sentence_clip(text: str, limit: int = 280) -> str:
    """Trim to whole sentences within limit."""
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    dot = cut.rfind(". ")
    return (cut[: dot + 1] if dot > 40 else cut.rstrip() + "…")


def parse_benchmark(benchmark: Optional[dict], watering: str) -> tuple[int, int, str]:
    """Turn watering_general_benchmark ({'value': '5-7', 'unit': 'days'}) into
    (min_days, max_days, provenance_note). Falls back to the coarse watering
    category when the benchmark is missing or unparseable."""
    if benchmark and benchmark.get("value"):
        raw = str(benchmark["value"]).strip().strip('"')
        m = re.match(r"^(\d+)\s*-\s*(\d+)$", raw) or re.match(r"^(\d+)$", raw)
        if m:
            lo = int(m.group(1))
            hi = int(m.group(2)) if m.lastindex == 2 else lo + max(2, lo // 2)
            unit = _norm(benchmark.get("unit") or "days")
            if unit.startswith("day"):
                return lo, max(hi, lo), "from Perenual watering benchmark"
    lo, hi = WATERING_FALLBACK.get(_norm(watering), (7, 14))
    return lo, hi, f"from Perenual watering category '{watering or 'unknown'}'"


def map_sunlight(sunlight: list) -> tuple[str, Optional[str]]:
    """Map Perenual's sunlight terms to our LightNeed. Uses the first
    recognized term (Perenual lists the primary preference first).
    Returns (light_need, warning_or_None)."""
    for term in _as_list(sunlight):
        mapped = SUNLIGHT_MAP.get(_norm(term))
        if mapped:
            return mapped, None
    return "medium", f"unrecognized sunlight terms {sunlight!r} — defaulted to medium"


def zone_to_temp_range(hardiness: Optional[dict], watering: str) -> tuple[int, int, Optional[str]]:
    """Approximate an indoor care temperature range from USDA hardiness.

    The coldest survivable zone gives a tolerance floor; indoor guidance sits
    well above survival minimum, so we lift it and clamp to houseplant range.
    """
    warning = None
    try:
        min_zone = int(str((hardiness or {}).get("min", "")).strip())
        floor = ZONE_MIN_F.get(min_zone)
    except (ValueError, TypeError):
        floor = None
    if floor is None:
        floor, warning = 40, "no usable hardiness zone — defaulted temp range"
    temp_min = max(40, min(65, floor + 15))
    # Desert/dry plants tolerate more heat than rainforest ones
    temp_max = 90 if _norm(watering) in ("minimum", "none") else 85
    return temp_min, temp_max, warning


def map_perenual_record(details: dict, sections: list[dict]) -> tuple[dict, list[str]]:
    """Map a Perenual details payload (+ optional care-guide sections) to a
    SpeciesCreate-shaped dict. Returns (record, warnings) — warnings flag
    derived/defaulted fields so validation can route them to review."""
    warnings: list[str] = []

    sci_names = _as_list(details.get("scientific_name"))
    scientific = (sci_names[0] if sci_names else "").strip()
    common = (details.get("common_name") or "").strip().title()
    if not scientific:
        warnings.append("missing scientific_name")
    if not common:
        warnings.append("missing common_name")

    watering = details.get("watering") or ""
    water_lo, water_hi, water_src = parse_benchmark(
        details.get("watering_general_benchmark"), watering
    )
    light_need, w = map_sunlight(details.get("sunlight"))
    if w:
        warnings.append(w)
    temp_min, temp_max, w = zone_to_temp_range(details.get("hardiness"), watering)
    if w:
        warnings.append(w)
    hum_lo, hum_hi = HUMIDITY_BY_WATERING.get(_norm(watering), (40, 60))

    soil_list = [s for s in _as_list(details.get("soil")) if s]
    soil_type = ", ".join(soil_list) if soil_list else "Well-draining potting mix"
    if not soil_list:
        warnings.append("no soil data — defaulted")

    by_type = {_norm(s.get("type", "")): (s.get("description") or "") for s in sections}
    care_notes = _sentence_clip(
        " ".join(filter(None, [by_type.get("watering", ""), by_type.get("sunlight", "")]))
    )
    if not care_notes:
        care_notes = _sentence_clip(details.get("description") or "")
    if not care_notes:
        warnings.append("no care notes available from source")

    schedules = [
        {
            "care_type": "water",
            "interval_days_min": water_lo,
            "interval_days_max": water_hi,
            "notes": _sentence_clip(by_type.get("watering", ""), 200) or f"Interval {water_src}.",
        },
        {
            "care_type": "fertilize",
            "interval_days_min": 30,
            "interval_days_max": 60,
            "notes": "During the growing season; pause or halve frequency in winter.",
        },
        {
            "care_type": "repot",
            "interval_days_min": 365,
            "interval_days_max": 730,
            "notes": "Typical cadence — repot when roots crowd the pot.",
        },
    ]
    if by_type.get("pruning"):
        schedules.append({
            "care_type": "prune",
            "interval_days_min": 90,
            "interval_days_max": 180,
            "notes": _sentence_clip(by_type["pruning"], 200),
        })

    traits = []
    for trait, value in [
        ("family", details.get("family")),
        ("cycle", details.get("cycle")),
        ("care_level", details.get("care_level")),
        ("hardiness_zone", _format_zone(details.get("hardiness"))),
        ("humidity_source", "derived from watering category (no source humidity data)"),
    ]:
        if value:
            traits.append({"trait": trait, "value": str(value), "unit": ""})

    record = {
        "common_name": common,
        "scientific_name": scientific,
        "light_need": light_need,
        "humidity_pct_min": hum_lo,
        "humidity_pct_max": hum_hi,
        "temp_f_min": temp_min,
        "temp_f_max": temp_max,
        "soil_type": soil_type,
        "toxic_to_pets": bool(details.get("poisonous_to_pets")),
        "care_notes": care_notes,
        "source": "perenual",
        "source_ref": str(details.get("id", "")),
        "review_status": "approved",  # validation may downgrade to needs_review
        "review_note": "",
        "schedules": schedules,
        "traits": traits,
    }
    return record, warnings


def _format_zone(hardiness: Optional[dict]) -> str:
    if not hardiness:
        return ""
    lo, hi = hardiness.get("min"), hardiness.get("max")
    if lo and hi:
        return f"{lo}-{hi}" if str(lo) != str(hi) else str(lo)
    return str(lo or hi or "")
