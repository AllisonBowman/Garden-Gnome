"""Owner-facing wording for every site value (PLAN.md section 6, "Each
value"; build spec section 2, "Plain words"). Builds every sentence the copy
module can produce and scans it: no em dashes, no acronym used before it is
spelled out, "hardiness zone" never shortened, every value with a reason and
a named source."""
import re
from datetime import datetime

import pytest

from app.services.site import copy as words
from app.services.site import overrides as override_rules
from app.services.site.copy import R

#: Acronyms that must never appear unless their spelled-out form comes first.
ACRONYMS = {
    "USDA": "United States Department of Agriculture",
    "USGS": "United States Geological Survey",
    "NOAA": "National Oceanic and Atmospheric Administration",
    "NLCD": "National Land Cover Database",
    "SSURGO": "Soil Survey Geographic Database",
    "STATSGO": "State Soil Geographic Database",
    "NAIP": "National Agriculture Imagery Program",
    "FEMA": "Federal Emergency Management Agency",
    "NWS": "National Weather Service",
    "PRISM": "Parameter-elevation Regressions on Independent Slopes Model",
    "3DEP": "3D Elevation Program",
    "DEM": "digital elevation model",
    "NRCS": "Natural Resources Conservation Service",
    "US": "United States",
    "USA": "United States",
    "pH": "acidity",
}


def wording_problems(text: str) -> list[str]:
    found = []
    if "—" in text:
        found.append(f"em dash in {text!r}")
    for acronym, expansion in ACRONYMS.items():
        for m in re.finditer(rf"(?<![A-Za-z0-9]){re.escape(acronym)}(?![A-Za-z0-9])", text):
            if expansion.lower() not in text[:m.start()].lower():
                found.append(f"{acronym} not spelled out first in {text!r}")
                break
    if re.search(r"(?<!hardiness )\bzone [0-9]", text, re.I):
        found.append(f"'zone' without 'hardiness' in {text!r}")
    return found


def test_the_scan_catches_what_it_should():
    assert wording_problems("Source: USDA soil map")
    assert wording_problems("Drainage — good")
    assert wording_problems("Zone 7b")
    assert wording_problems("Soil pH is 5")
    assert not wording_problems("Soil acidity (pH): 5")
    assert not wording_problems("United States Department of Agriculture (USDA) map")


def rd(field, value, level="medium", source="ssurgo", codes=(), **detail):
    return R(field=field, value=value, level=level, source_key=source,
             source_version="2026", reason_codes=tuple(codes), detail=detail)


SOIL = {
    "soil_mapunit": rd("soil_mapunit", {"name": "Sassafras fine sandy loam"}),
    "soil_slowest_layer": rd("soil_slowest_layer", "moderately slow"),
    "soil_water_holding": rd("soil_water_holding", 1.6),
    "soil_ponding": rd("soil_ponding", "Occasional"),
    "open_sky_sun": rd("open_sky_sun", {"hours": 12.1}, "high", "sunpos"),
    "tree_cover": rd("tree_cover", 0.3, "medium", "nlcd"),
}
ALL_CAPS = ("near_soil_map_line", "disturbed_soil", "mixed_soil_area",
            "little_texture_data", "near_zone_line", "stations_differ")


def every_text():
    """Every sentence the module builds, with a label for the failure."""
    out = []
    for field in words.TITLES:
        for state in ("pending", "failed", "no_data", "outside_us", "zone_pending"):
            out.append((f"{field}/{state}", words.missing(field, state)))
        if override_rules.can_override(field):
            spec = override_rules.spec(field)
            values = [v for v, _ in spec.choices] or [6.2]
            for v in values:
                out.append((f"{field}/owner/{v}", words.owner(
                    field, v, "measured" if spec.measured else "tap",
                    datetime(2026, 11, 15), [words.source("ssurgo")])))
    for caps in ((), ALL_CAPS):
        out += [
            ("hardiness", words.hardiness_zone(rd("hardiness_zone", "7b", "high", "phzm2023"), caps)),
            ("hardiness/range", words.hardiness_zone(
                rd("hardiness_zone", "10a", "high", "phzm2023", min_f=30, max_f=35), caps)),
            ("drainage", words.soil_drainage(rd("soil_drainage_class", "Well drained"), SOIL, caps)),
            ("texture", words.soil_texture(rd("soil_texture", "fine sandy loam", **{"class": "sandy"}),
                                           SOIL, caps)),
            ("ph", words.soil_ph(rd("soil_ph", 5.1), caps + ("soil_acidity_varies",))),
            ("ph/alkaline", words.soil_ph(rd("soil_ph", 8.1), caps)),
            ("disturbed/high", words.disturbed_soil(rd("soil_disturbed_share", 0.3), caps)),
            ("disturbed/low", words.disturbed_soil(rd("soil_disturbed_share", 4), caps)),
            ("disturbed/none", words.disturbed_soil(rd("soil_disturbed_share", 0), caps)),
            ("flooding", words.flooding(rd("soil_flooding", "None", worst="Occasional",
                                           worst_share=0.02, months=[3, 4, 10]), SOIL, caps)),
            ("flooding/frequent", words.flooding(rd("soil_flooding", "Frequent"), SOIL, caps)),
            ("slope", words.slope(rd("slope", 6.2, "high", "3dep", resolution_m=1, year=2014),
                                  caps, True)),
            ("slope/coarse", words.slope(rd("slope", 25, "low", "3dep", resolution_m=10), caps, False)),
            ("facing", words.facing(rd("facing", 63.0, "high", "3dep", resolution_m=1), caps, True)),
            ("facing/flat", words.facing(rd("facing", "flat", "high", "3dep"), caps, False)),
            ("sun", words.sun(rd("sun_estimate", {"category": "part_shade", "hours": 4.6}, "medium",
                                 "sunpos", counted=["terrain", "canopy_height"],
                                 canopy_resolution_m=1), SOIL, caps, True, "drops_leaves")),
            ("sun/coarse", words.sun(rd("sun_estimate", {"category": "full_sun", "hours": 8},
                                        "low", "sunpos", counted=["terrain", "tree_cover"],
                                        not_counted=["canopy_height"]), SOIL, caps, False)),
            ("sun/open-sky", words.sun(None, SOIL, caps, True)),
            ("land_cover", words.land_cover(rd("land_cover", "lightly built-up land", "high", "nlcd",
                                               paved_share=0.45, year=2025), SOIL)),
            ("frost", words.frost_dates({"last_spring_frost": {"p50": "04-10"},
                                         "first_fall_frost": "2026-10-28",
                                         "station": {"name": "National Arboretum",
                                                     "distance_km": 0.8},
                                         "stations_differ_days": 10}, caps)),
        ]
        for code in ("drains_freely", "slow_to_drain", "gathers_after_rain", "often_wet"):
            out.append((f"water/{code}", words.water_collects(
                rd("water_collects", code, "medium", "drainage",
                   signals=["drainage_class", "ponding", "low_spot", "flow"]), SOIL, caps, True)))
    return out


@pytest.mark.parametrize("label,text", every_text(), ids=lambda x: x if isinstance(x, str) else "")
def test_every_sentence_follows_the_wording_rules(label, text):
    assert text.display.strip() and text.reason.strip(), label
    assert text.sources and all(s.get("name") for s in text.sources), label
    whole = " ".join([text.display, text.reason]
                     + [f"{s['name']} {s.get('detail') or ''}" for s in text.sources])
    assert wording_problems(whole) == [], label
    # No invented precision: no number with more than one decimal place.
    assert not re.search(r"\d\.\d{2,}", text.display + " " + text.reason), label


def test_override_labels_follow_the_wording_rules():
    for field, spec in override_rules.SPECS.items():
        for _, label in spec.choices:
            assert wording_problems(label) == [], (field, label)
    for field in ("hardiness_zone", "land_cover", "frost_dates", "soil_ph"):
        try:
            override_rules.validate(field, "x")
        except ValueError as exc:
            assert wording_problems(str(exc)) == []


def test_the_examples_read_as_planned():
    t = words.hardiness_zone(rd("hardiness_zone", "8a", "high", "phzm2023"), ())
    assert t.display == ("Hardiness zone 8a: the average coldest night of the year is "
                         "10 to 15 degrees Fahrenheit.")
    t = words.facing(rd("facing", 63.0, "high", "3dep"), (), False)
    assert t.display.startswith("Faces: north-east.")
    t = words.flooding(rd("soil_flooding", "None", worst="Occasional", worst_share=0.02,
                          months=[4, 10]), {}, ())
    assert t.display == ("Flooding: none expected for most of this soil area. A small part "
                         "(about 2%) floods occasionally, in April and October.")
    t = words.land_cover(rd("land_cover", "lightly built-up land with lawns and trees", "high",
                            "nlcd", paved_share=0.45, year=2025), {})
    assert t.display == ("Around you: mostly lightly built-up land with lawns and trees "
                         "(about 45% paved or roofed).")
    assert "year 2025" in t.reason and "not your lot" in t.reason
    assert words.TITLES["land_cover"] == "Neighbourhood context"
