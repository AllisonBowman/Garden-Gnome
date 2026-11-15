"""Confidence rules and hard caps (PLAN.md section 6 as amended by build
spec section 5). One row per cap: the field, the source's level, the facts,
the words the owner must read, and the cap that must have fired."""
import pytest

from app.services.site import confidence as conf
from app.services.site.confidence import Facts, decide

OWNER_ZONE = dict(default_footprint=False, zone_area_m2=120.0)
ONE_M = dict(resolution_m=1.0)

CASES = [
    # soil survey: never above "Area estimate"
    ("soil_drainage", "high", Facts(), "area_estimate", "soil_survey_is_area_scale"),
    ("soil_texture", "high", Facts(), "area_estimate", "soil_survey_is_area_scale"),
    ("flooding", "high", Facts(), "area_estimate", "soil_survey_is_area_scale"),
    ("soil_drainage", "medium", Facts(dominant_share=0.8), "area_estimate", None),
    # disturbed share 15% or more: every soil value rough
    ("soil_drainage", "medium", Facts(disturbed_share=0.15), "rough_estimate", "disturbed_soil"),
    ("soil_texture", "medium", Facts(disturbed_share=0.40), "rough_estimate", "disturbed_soil"),
    ("flooding", "medium", Facts(disturbed_share=0.20), "rough_estimate", "disturbed_soil"),
    ("disturbed_soil", "medium", Facts(disturbed_share=0.30), "rough_estimate", "disturbed_soil"),
    ("soil_drainage", "medium", Facts(disturbed_share=0.14), "area_estimate", None),
    # within 30 m of a differing soil map line
    ("soil_drainage", "medium", Facts(near_soil_line=True), "rough_estimate", "near_soil_map_line"),
    # dominant condition under 75%
    ("soil_drainage", "medium", Facts(dominant_share=0.6), "rough_estimate", "mixed_soil_area"),
    # texture data under 60% of the area
    ("soil_texture", "medium", Facts(texture_coverage=0.5), "rough_estimate", "little_texture_data"),
    # soil acidity rough by default
    ("soil_ph", "medium", Facts(), "rough_estimate", "soil_acidity_varies"),
    # slope and facing
    ("slope", "high", Facts(**OWNER_ZONE, **ONE_M), "good_estimate", None),
    ("slope", "high", Facts(default_footprint=True, **ONE_M), "area_estimate", "default_footprint"),
    ("slope", "high", Facts(**OWNER_ZONE, resolution_m=3.0), "area_estimate", "not_one_metre_survey"),
    ("slope", "high", Facts(**OWNER_ZONE, resolution_m=10.0), "rough_estimate", "coarse_elevation"),
    ("slope", "high", Facts(default_footprint=False, zone_area_m2=30.0, **ONE_M),
     "area_estimate", "small_zone"),
    ("facing", "high", Facts(**OWNER_ZONE, **ONE_M, slope_degrees=5.0), "good_estimate", None),
    ("facing", "high", Facts(**OWNER_ZONE, **ONE_M, slope_degrees=1.0), "area_estimate", "nearly_flat"),
    ("facing", "high", Facts(default_footprint=True, **ONE_M, slope_degrees=5.0),
     "area_estimate", "default_footprint"),
    ("slope", "unknown", Facts(**OWNER_ZONE, **ONE_M), "not_known_yet", None),
    # sun: never above "Area estimate" from public data
    ("sun", "high", Facts(default_footprint=False, terrain_counted=True, canopy_counted=True,
                          buildings_counted=True), "area_estimate", "sun_from_public_data"),
    ("sun", "high", Facts(default_footprint=False, terrain_counted=True,
                          coarse_canopy_only=True, buildings_counted=True),
     "rough_estimate", "coarse_canopy_only"),
    ("sun", "medium", Facts(default_footprint=True, terrain_counted=True, canopy_counted=True,
                            buildings_counted=True), "rough_estimate", "default_footprint"),
    ("sun", "medium", Facts(default_footprint=False, terrain_counted=True, canopy_counted=True,
                            buildings_counted=False), "rough_estimate", "buildings_not_counted"),
    ("sun", "medium", Facts(default_footprint=False), "not_known_yet", "nothing_counted"),
    # where water collects
    ("water_collects", "high", Facts(**OWNER_ZONE, **ONE_M, elevation_used=True,
                                     soil_signals_agree=True), "good_estimate", None),
    ("water_collects", "high", Facts(**OWNER_ZONE, **ONE_M, elevation_used=True,
                                     soil_signals_agree=False),
     "area_estimate", "not_one_metre_owner_zone"),
    ("water_collects", "high", Facts(**OWNER_ZONE, resolution_m=3.0, elevation_used=True,
                                     soil_signals_agree=True),
     "area_estimate", "not_one_metre_owner_zone"),
    ("water_collects", "high", Facts(**OWNER_ZONE, resolution_m=10.0, elevation_used=True,
                                     soil_signals_agree=True), "rough_estimate", "coarse_elevation"),
    ("water_collects", "medium", Facts(**OWNER_ZONE, soil_agree_share=0.8), "area_estimate", None),
    ("water_collects", "medium", Facts(**OWNER_ZONE, soil_agree_share=0.6),
     "rough_estimate", "soil_alone_mixed"),
    ("water_collects", "high", Facts(default_footprint=True, **ONE_M, elevation_used=True,
                                     soil_signals_agree=True), "rough_estimate", "default_footprint"),
    ("water_collects", "high", Facts(**OWNER_ZONE, **ONE_M, elevation_used=True,
                                     soil_signals_agree=True, disturbed_share=0.2),
     "rough_estimate", "disturbed_soil"),
    # hardiness zone
    ("hardiness_zone", "high", Facts(), "good_estimate", None),
    ("hardiness_zone", "high", Facts(near_zone_line=True), "area_estimate", "near_zone_line"),
    ("hardiness_zone", "unknown", Facts(), "not_known_yet", None),
    # frost dates
    ("frost_dates", "high", Facts(stations_differ_days=10), "area_estimate", "stations_differ"),
    ("frost_dates", "high", Facts(stations_differ_days=5), "good_estimate", None),
    # land cover: always neighbourhood context, whatever the source says
    ("land_cover", "high", Facts(), "neighbourhood_context", None),
    ("land_cover", "unknown", Facts(), "neighbourhood_context", None),
]


@pytest.mark.parametrize("field,level,facts,want,cap", CASES,
                         ids=[f"{c[0]}-{c[4] or 'none'}-{i}" for i, c in enumerate(CASES)])
def test_every_cap(field, level, facts, want, cap):
    d = decide(field, level, facts)
    assert d.confidence == want
    if cap is not None:
        assert cap in d.caps
    else:
        assert all(c for c in d.caps)  # no cap needed; any listed must be named


@pytest.mark.parametrize("level", ["high", "medium", "low", "unknown"])
@pytest.mark.parametrize("field", ["sun", "slope", "facing", "soil_drainage", "soil_ph",
                                   "water_collects", "flooding", "hardiness_zone"])
def test_a_cap_never_raises(field, level, ):
    base = conf.LEVEL_TO_CONFIDENCE[level]
    for facts in (Facts(), Facts(default_footprint=False, zone_area_m2=500, resolution_m=1.0,
                                 terrain_counted=True, canopy_counted=True,
                                 buildings_counted=True, elevation_used=True,
                                 soil_signals_agree=True, slope_degrees=8)):
        got = decide(field, level, facts).confidence
        assert conf.RANK[got] <= conf.RANK[base]


def test_public_sun_and_soil_never_reach_good():
    best = Facts(default_footprint=False, zone_area_m2=500, resolution_m=1.0,
                 terrain_counted=True, canopy_counted=True, buildings_counted=True)
    for field in ("sun", "soil_drainage", "soil_texture", "flooding", "soil_ph"):
        assert decide(field, "high", best).confidence != "good_estimate"


def test_owner_words():
    assert conf.owner("tap").confidence == "you_told_us"
    assert conf.owner("measured").confidence == "you_measured"


def test_lowest_and_fit_rules():
    assert conf.lowest(["good_estimate", "rough_estimate", "you_told_us"]) == "rough_estimate"
    assert conf.lowest(["you_told_us", "area_estimate"]) == "area_estimate"
    assert conf.lowest(["neighbourhood_context", "good_estimate"]) == "not_known_yet"
    assert not conf.can_support_fit("rough_estimate")
    assert not conf.can_support_fit("not_known_yet")
    assert conf.can_support_fit("area_estimate") and conf.can_support_fit("you_told_us")
