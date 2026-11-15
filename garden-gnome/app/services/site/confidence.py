"""Confidence rules and hard caps for site values (PLAN.md section 6,
"Confidence rules (tested)", as amended by build spec section 5).

A source reports an internal level (high, medium, low, unknown). That level
is turned into the words the owner reads, then lowered by every cap whose
condition holds. A cap only ever lowers; nothing here raises a value above
what its source claimed.

    decide(field, level, facts) -> Decision(confidence, caps)

`field` is a SiteValue field ("sun", "slope", ...). `facts` carries the few
things the caps look at, taken from the readings by the profile builder.
`caps` names every cap whose condition holds (whether or not the source's
own level was already that low), so the sentence can say why.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Optional

#: Strength order of the estimate words. "Neighbourhood context" and the
#: owner's own words sit outside this order.
RANK = {"not_known_yet": 0, "rough_estimate": 1, "area_estimate": 2,
        "good_estimate": 3}
_BY_RANK = {v: k for k, v in RANK.items()}

LEVEL_TO_CONFIDENCE = {
    "high": "good_estimate",
    "medium": "area_estimate",
    "low": "rough_estimate",
    "unknown": "not_known_yet",
}

SOIL_FIELDS = ("soil_drainage", "soil_texture", "soil_ph", "disturbed_soil",
               "flooding")

#: Disturbed or built-up share at which every soil value is a rough guess.
DISTURBED_SHARE = 0.15
#: A point this close to a soil map line whose neighbour differs is rough.
NEAR_LINE_M = 30.0
#: The dominant soil must cover this share of the mapped area.
DOMINANT_SHARE = 0.75
#: Soil texture data must cover this share of the mapped area.
TEXTURE_COVERAGE = 0.60
#: An owner-drawn zone this large (square metres) can carry a good slope.
GOOD_ZONE_M2 = 50.0
#: Facing is only a good estimate on ground at least this steep (degrees).
FACING_MIN_DEGREES = 3.0
#: Stations further apart than this (days) make the frost dates a range.
FROST_STATIONS_DIFFER_DAYS = 7


@dataclass(frozen=True)
class Facts:
    """What the caps look at. None means "not reported"; a cap that needs a
    fact that is missing assumes the cautious case."""
    default_footprint: bool = True          # the zone is the default square
    zone_area_m2: Optional[float] = None    # owner-drawn zone area
    resolution_m: Optional[float] = None    # elevation survey detail
    disturbed_share: Optional[float] = None  # 0..1
    near_soil_line: bool = False            # within 30 m of a differing neighbour
    dominant_share: Optional[float] = None  # 0..1 of the dominant soil condition
    texture_coverage: Optional[float] = None  # 0..1 with texture data
    slope_degrees: Optional[float] = None
    # sun
    terrain_counted: bool = False
    canopy_counted: bool = False            # a canopy height source answered
    coarse_canopy_only: bool = False        # only tree cover percentage
    buildings_counted: bool = False
    # water collects
    soil_signals_agree: bool = False
    soil_agree_share: Optional[float] = None
    elevation_used: bool = False            # elevation entered the result
    soil_used: bool = False                 # soil survey signals entered the result
    # hardiness and frost dates
    near_zone_line: bool = False
    stations_differ_days: Optional[float] = None


@dataclass(frozen=True)
class Decision:
    confidence: str
    caps: tuple[str, ...] = dc_field(default_factory=tuple)


def owner(method: str) -> Decision:
    """The owner's correction: "You measured" for a test result, otherwise
    "You told us". Never lowered and never overwritten by a refresh."""
    return Decision("you_measured" if method == "measured" else "you_told_us")


def _lower(conf: str, to: str) -> str:
    return _BY_RANK[min(RANK[conf], RANK[to])]


def _caps(field: str, f: Facts) -> list[tuple[str, str]]:
    """(cap name, highest allowed) for every cap whose condition holds."""
    out: list[tuple[str, str]] = []
    disturbed = f.disturbed_share is not None and f.disturbed_share >= DISTURBED_SHARE

    if field in SOIL_FIELDS:
        out.append(("soil_survey_is_area_scale", "area_estimate"))
        if disturbed:
            out.append(("disturbed_soil", "rough_estimate"))
        if f.near_soil_line:
            out.append(("near_soil_map_line", "rough_estimate"))
        if field in ("soil_drainage", "soil_texture") and (
                f.dominant_share is not None and f.dominant_share < DOMINANT_SHARE):
            out.append(("mixed_soil_area", "rough_estimate"))
        if field == "soil_texture" and (
                f.texture_coverage is not None and f.texture_coverage < TEXTURE_COVERAGE):
            out.append(("little_texture_data", "rough_estimate"))
        if field == "soil_ph":
            out.append(("soil_acidity_varies", "rough_estimate"))

    elif field in ("slope", "facing"):
        res = f.resolution_m
        if f.default_footprint:
            out.append(("default_footprint", "area_estimate"))
        if res is None or res > 1.5:
            out.append(("not_one_metre_survey", "area_estimate"))
        if res is not None and res > 3.5:
            out.append(("coarse_elevation", "rough_estimate"))
        if not f.default_footprint and (f.zone_area_m2 is None
                                        or f.zone_area_m2 < GOOD_ZONE_M2):
            out.append(("small_zone", "area_estimate"))
        if field == "facing" and (f.slope_degrees is None
                                  or f.slope_degrees < FACING_MIN_DEGREES):
            out.append(("nearly_flat", "area_estimate"))

    elif field == "sun":
        out.append(("sun_from_public_data", "area_estimate"))
        if f.coarse_canopy_only or not f.canopy_counted:
            out.append(("coarse_canopy_only", "rough_estimate"))
        if f.default_footprint:
            out.append(("default_footprint", "rough_estimate"))
        if not f.buildings_counted:
            out.append(("buildings_not_counted", "rough_estimate"))
        if not f.terrain_counted and not f.canopy_counted and not f.coarse_canopy_only:
            out.append(("nothing_counted", "not_known_yet"))

    elif field == "water_collects":
        res = f.resolution_m if f.elevation_used else None
        good_ok = (res is not None and res <= 1.5 and not f.default_footprint
                   and f.soil_signals_agree)
        if not good_ok:
            out.append(("not_one_metre_owner_zone", "area_estimate"))
        if f.elevation_used and (res is None or res > 3.5):
            out.append(("coarse_elevation", "rough_estimate"))
        if not f.elevation_used and (f.soil_agree_share is None
                                     or f.soil_agree_share < DOMINANT_SHARE):
            out.append(("soil_alone_mixed", "rough_estimate"))
        if f.default_footprint:
            out.append(("default_footprint", "rough_estimate"))
        if disturbed:
            out.append(("disturbed_soil", "rough_estimate"))
        if f.soil_used and f.near_soil_line:
            # The soil rows themselves are a rough estimate here, so an
            # answer resting on them cannot be stronger.
            out.append(("near_soil_map_line", "rough_estimate"))

    elif field == "hardiness_zone":
        if f.near_zone_line:
            out.append(("near_zone_line", "area_estimate"))

    elif field == "frost_dates":
        if (f.stations_differ_days is not None
                and f.stations_differ_days > FROST_STATIONS_DIFFER_DAYS):
            out.append(("stations_differ", "area_estimate"))

    return out


def decide(field: str, level: str, facts: Optional[Facts] = None) -> Decision:
    """The confidence the owner reads for a public value, and the caps that
    apply to it. Land cover is always "Neighbourhood context"."""
    if field == "land_cover":
        return Decision("neighbourhood_context")
    f = facts or Facts()
    conf = LEVEL_TO_CONFIDENCE.get(level, "not_known_yet")
    applied: list[str] = []
    for name, ceiling in _caps(field, f):
        applied.append(name)
        conf = _lower(conf, ceiling)
    return Decision(conf, tuple(applied))


def lowest(confidences: list[str]) -> str:
    """A recommendation's confidence is the lowest of the values it used.
    Owner words count as the strongest; neighbourhood context does not
    describe the lot, so it counts as not known."""
    def rank(c: str) -> int:
        if c in ("you_told_us", "you_measured"):
            return 4
        return RANK.get(c, 0)
    if not confidences:
        return "not_known_yet"
    worst = min(confidences, key=rank)
    return "not_known_yet" if worst == "neighbourhood_context" else worst


def can_support_fit(confidence: str) -> bool:
    """"Rough estimate" and "Not known yet" never produce "fits"."""
    return confidence in ("you_told_us", "you_measured", "good_estimate",
                          "area_estimate")
