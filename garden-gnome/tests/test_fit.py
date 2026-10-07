"""The fit engine: does this species belong in this growing area?

Pure functions over constructed rows, in the style of test_advisor_weather --
no database, because `app.services.fit` has none in it.

The assertions that matter most are the negative ones. Most of this catalog is
sparse, so the common case is a species the sources are silent about on some
axis, and the single rule the whole feature rests on is that silence is not a
pass. Half these tests exist to pin that.
"""
import pytest

from app.models.models import (
    GrowingArea, GrowingAreaType, GrowingGoal, GrowingSurface, OutdoorSunExposure,
    Species, Shelter, SunExposure, TempExposure,
)
from app.services import fit
from app.services.care_facts import length_said
from app.services.fit import Axis, Verdict


def make_species(**kw) -> Species:
    base = dict(common_name="Test Plant", scientific_name="Testus plantus")
    base.update(kw)
    return Species(**base)


def make_area(**kw) -> GrowingArea:
    base = dict(
        name="Test area", type=GrowingAreaType.home,
        shelter=Shelter.sheltered, temp_exposure=TempExposure.indoor,
        sun_exposure=SunExposure.partial_sun,
    )
    base.update(kw)
    return GrowingArea(**base)


def verdict_on(findings, axis: Axis) -> Verdict:
    for f in findings:
        if f.axis == axis:
            return f.verdict
    return Verdict.unknown


OUTDOOR_BED = dict(
    temp_exposure=TempExposure.outdoor, shelter=Shelter.exposed,
    sun_exposure=SunExposure.full_sun, surface=GrowingSurface.raised_bed,
)


# --- the rule everything rests on ------------------------------------------

def test_a_species_the_catalog_knows_nothing_about_fits_nothing():
    findings = fit.assess(make_species(), make_area(**OUTDOOR_BED))
    assert findings, "every axis should still report"
    assert all(f.verdict == Verdict.unknown for f in findings)
    assert fit.score(findings) == 0
    assert fit.misfits(findings) == []


def test_unknown_never_counts_toward_the_score():
    known = make_species(is_houseplant=False, outdoor_sun_exposure=["full_sun"])
    area = make_area(**OUTDOOR_BED)
    assert fit.score(fit.assess(known, area)) == 2
    assert fit.score(fit.assess(make_species(), area)) == 0


def test_an_unexamined_species_is_not_a_candidate():
    """Zero misfits is not the same as suitable, and the list must not say it is."""
    area = make_area(**OUTDOOR_BED)
    assert fit.candidates([make_species()], area) == []


# --- indoor / outdoor ------------------------------------------------------

def test_an_outdoor_plant_indoors_is_a_misfit():
    f = fit.assess(make_species(is_houseplant=False), make_area())
    assert verdict_on(f, Axis.indoor_outdoor) == Verdict.misfits


def test_a_houseplant_indoors_fits():
    f = fit.assess(make_species(is_houseplant=True), make_area())
    assert verdict_on(f, Axis.indoor_outdoor) == Verdict.fits


def test_a_houseplant_outdoors_is_unknown_not_a_misfit():
    """Sources say it is grown indoors. They do not say it cannot go out, and
    plenty of houseplants summer on a patio."""
    f = fit.assess(make_species(is_houseplant=True), make_area(**OUTDOOR_BED))
    assert verdict_on(f, Axis.indoor_outdoor) == Verdict.unknown


def test_no_record_of_where_it_lives_is_unknown():
    f = fit.assess(make_species(is_houseplant=None), make_area())
    assert verdict_on(f, Axis.indoor_outdoor) == Verdict.unknown


# --- sun -------------------------------------------------------------------

@pytest.mark.parametrize("area_sun,tokens,expected", [
    (SunExposure.full_sun,    ["full_sun"],    Verdict.fits),
    (SunExposure.full_sun,    ["part_sun"],    Verdict.fits),
    (SunExposure.full_sun,    ["full_shade"],  Verdict.misfits),
    (SunExposure.full_sun,    ["part_shade"],  Verdict.misfits),
    (SunExposure.shade,       ["full_shade"],  Verdict.fits),
    (SunExposure.shade,       ["part_shade"],  Verdict.fits),
    (SunExposure.shade,       ["full_sun"],    Verdict.misfits),
    (SunExposure.partial_sun, ["part_sun"],    Verdict.fits),
    (SunExposure.partial_sun, ["full_sun"],    Verdict.misfits),
    # A species recorded for a spread of conditions fits if any of them match.
    (SunExposure.shade, ["full_sun", "part_shade"], Verdict.fits),
])
def test_outdoor_sun_is_compared_band_to_band(area_sun, tokens, expected):
    area = make_area(**{**OUTDOOR_BED, "sun_exposure": area_sun})
    f = fit.assess(make_species(outdoor_sun_exposure=tokens), area)
    assert verdict_on(f, Axis.sun) == expected


def test_a_shade_plant_in_a_sunny_bed_says_which_way_round_it_is():
    area = make_area(**OUTDOOR_BED)
    f = fit.assess(make_species(outdoor_sun_exposure=["full_shade"]), area)
    sentence = next(x for x in f if x.axis == Axis.sun).sentence
    assert "6+ hours of direct sun" in sentence and "full shade" in sentence


def test_indoor_light_is_admitted_to_be_uncheckable():
    """3% of the catalog carries a footcandle figure and nothing measures the
    room, so the indoor answer is "can't tell" — never a quiet pass."""
    f = fit.assess(make_species(is_houseplant=True), make_area())
    assert verdict_on(f, Axis.sun) == Verdict.unknown
    assert "Indoor light isn't comparable" in next(
        x for x in f if x.axis == Axis.sun).sentence


def test_indoor_light_never_falls_back_to_the_legacy_column():
    """`light_need` is the column where 77% of the old import wrongly claimed
    `direct`. Reading it here would rebuild that error on a new surface."""
    f = fit.assess(make_species(light_need="direct"), make_area())
    assert verdict_on(f, Axis.sun) == Verdict.unknown


def test_outdoor_sun_is_unknown_when_the_species_has_no_range():
    f = fit.assess(make_species(), make_area(**OUTDOOR_BED))
    assert verdict_on(f, Axis.sun) == Verdict.unknown


# --- soil ------------------------------------------------------------------

def test_a_garden_bed_species_fits_a_bed_and_not_a_pot():
    bed = make_area(**OUTDOOR_BED)
    pot = make_area(surface=GrowingSurface.windowsill)
    species = make_species(soil_base="garden_bed")
    assert verdict_on(fit.assess(species, bed), Axis.soil) == Verdict.fits
    assert verdict_on(fit.assess(species, pot), Axis.soil) == Verdict.misfits


def test_a_specialist_mix_fits_a_container_and_not_open_ground():
    species = make_species(soil_base="cactus_succulent")
    pot = make_area(surface=GrowingSurface.containers)
    bed = make_area(**{**OUTDOOR_BED, "surface": GrowingSurface.in_ground_bed})
    assert verdict_on(fit.assess(species, pot), Axis.soil) == Verdict.fits
    assert verdict_on(fit.assess(species, bed), Axis.soil) == Verdict.misfits


def test_soil_is_unknown_when_the_area_never_said_what_it_is():
    f = fit.assess(make_species(soil_base="garden_bed"), make_area(surface=None))
    assert verdict_on(f, Axis.soil) == Verdict.unknown


def test_water_fits_a_pond_and_soil_does_not():
    pond = make_area(**{**OUTDOOR_BED, "surface": GrowingSurface.pond_or_water})
    assert verdict_on(
        fit.assess(make_species(soil_base="semi_hydro"), pond), Axis.soil) == Verdict.fits
    assert verdict_on(
        fit.assess(make_species(soil_base="garden_bed"), pond), Axis.soil) == Verdict.misfits


# --- footprint -------------------------------------------------------------

def test_a_plant_taller_than_the_headroom_is_a_misfit():
    area = make_area(surface=GrowingSurface.windowsill, headroom_in=18)
    f = fit.assess(make_species(mature_height_in_max=48), area)
    assert verdict_on(f, Axis.footprint) == Verdict.misfits


def test_a_plant_inside_the_headroom_fits():
    area = make_area(surface=GrowingSurface.windowsill, headroom_in=24)
    f = fit.assess(make_species(mature_height_in_max=14), area)
    assert verdict_on(f, Axis.footprint) == Verdict.fits


def test_a_plant_wider_than_the_bed_is_a_misfit():
    area = make_area(**OUTDOOR_BED, area_sqft=4)     # about 2 ft across
    f = fit.assess(make_species(mature_spread_in_max=96), area)
    assert verdict_on(f, Axis.footprint) == Verdict.misfits


def test_a_spread_is_set_against_the_square_feet_given_never_an_invented_width():
    """32 sq ft is a 4 x 8 bed as often as a square one. The old sentence
    said "a space about 5.7 ft wide" -- the square root of 32, a dimension
    nobody measured -- so the sentence now states the spread and the square
    feet, the two numbers somebody actually gave."""
    area = make_area(**OUTDOOR_BED, area_sqft=32)
    wide = next(x for x in fit.assess(make_species(mature_spread_in_max=120), area)
                if x.axis == Axis.footprint)
    assert wide.verdict == Verdict.misfits
    assert "spreads to 10 ft across and the space is 32 sq ft" in wide.sentence
    assert "wide" not in wide.sentence and "5.7" not in wide.sentence

    small = next(x for x in fit.assess(make_species(mature_spread_in_max=36), area)
                 if x.axis == Axis.footprint)
    assert small.verdict == Verdict.fits
    assert "spreads to 3 ft, within the 32 sq ft here" in small.sentence


def test_a_spread_needing_more_ground_than_the_space_has_is_a_misfit():
    """A plant claims a square its own spread on a side: 6 ft across is 36 sq
    ft of ground, more than 32; 5 ft across is 25, which 32 has room for."""
    area = make_area(**OUTDOOR_BED, area_sqft=32)
    assert verdict_on(fit.assess(make_species(mature_spread_in_max=72), area),
                      Axis.footprint) == Verdict.misfits
    assert verdict_on(fit.assess(make_species(mature_spread_in_max=60), area),
                      Axis.footprint) == Verdict.fits


def test_size_is_unknown_while_the_catalog_has_none():
    """Today's real case: 0 of 600 records carry a mature size."""
    area = make_area(surface=GrowingSurface.windowsill, headroom_in=18)
    f = fit.assess(make_species(), area)
    assert verdict_on(f, Axis.footprint) == Verdict.unknown
    assert "no source" in next(
        x for x in f if x.axis == Axis.footprint).sentence.lower()


def test_a_known_size_against_an_unmeasured_area_is_unknown():
    """The species answered; the gardener has not. That is not a fit."""
    area = make_area(surface=GrowingSurface.windowsill)   # nothing measured
    f = fit.assess(make_species(mature_height_in_max=48), area)
    assert verdict_on(f, Axis.footprint) == Verdict.unknown


def test_a_zero_would_have_been_a_disaster_and_null_is_not_zero():
    """If an unmeasured area arrived as 0 headroom, everything would misfit."""
    area = make_area(surface=GrowingSurface.windowsill, headroom_in=None)
    assert verdict_on(
        fit.assess(make_species(mature_height_in_max=6), area),
        Axis.footprint) == Verdict.unknown


def test_a_climber_over_the_headroom_is_a_misfit_that_says_it_climbs():
    """A 40 ft wisteria against a 7 ft fence: still a misfit, but the reason
    is reach, and the sentence has to say what that costs the gardener."""
    area = make_area(**OUTDOOR_BED, headroom_in=84)
    f = fit.assess(make_species(climbs=True, mature_height_in_max=480), area)
    found = next(x for x in f if x.axis == Axis.footprint)
    assert found.verdict == Verdict.misfits
    assert "climbs to 40 ft" in found.sentence
    assert "cutting back" in found.sentence
    # Says what the cutting back is for, rather than trailing off "to stay."
    assert found.sentence.endswith("to stay in this space.")


def test_a_climber_inside_the_headroom_fits_and_still_says_climbs():
    area = make_area(**OUTDOOR_BED, headroom_in=96)
    f = fit.assess(make_species(climbs=True, mature_height_in_max=72), area)
    found = next(x for x in f if x.axis == Axis.footprint)
    assert found.verdict == Verdict.fits
    assert "climbs to" in found.sentence and "reaches" not in found.sentence


#: Shared with mobile/src/care/facts.test.ts (`lengthSaid`): the app prints a
#: gardener's measurement by the same rule the sentences use. If these drift,
#: an area's card and its findings disagree about the same number.
LENGTHS_SAID = [
    (18, "18 in"), (23.5, "23.5 in"), (24, "2 ft"), (84, "7 ft"),
    (87, "7.3 ft"), (81, "6.8 ft"), (39.4, "3.3 ft"), (59.1, "4.9 ft"),
    (720, "60 ft"),
]


@pytest.mark.parametrize("inches,said", LENGTHS_SAID)
def test_a_length_is_said_the_way_the_app_prints_it(inches, said):
    assert length_said(inches) == said


def test_the_headroom_in_a_sentence_is_the_headroom_on_the_card():
    """87 in typed; the app's card prints "7.3 ft (87 in)". round() would have
    said 7.2 ft here -- a half to even -- and the two would disagree."""
    area = make_area(**OUTDOOR_BED, headroom_in=87)
    size = next(x for x in fit.assess(make_species(mature_height_in_max=120), area)
                if x.axis == Axis.footprint)
    assert "there is 7.3 ft of headroom" in size.sentence


def test_a_climber_with_no_size_is_unknown_and_says_why():
    area = make_area(**OUTDOOR_BED, headroom_in=96)
    found = next(x for x in fit.assess(make_species(climbs=True), area)
                 if x.axis == Axis.footprint)
    assert found.verdict == Verdict.unknown
    assert "climber" in found.sentence.lower()


# --- upkeep ----------------------------------------------------------------

def test_upkeep_is_only_asked_when_the_gardener_asked_for_it():
    thirsty = make_species(water_regime="keep_moist")
    assert not any(f.axis == Axis.upkeep
                   for f in fit.assess(thirsty, make_area(**OUTDOOR_BED)))
    wanted = make_area(**OUTDOOR_BED, goals=[GrowingGoal.low_upkeep.value])
    assert verdict_on(fit.assess(thirsty, wanted), Axis.upkeep) == Verdict.misfits


def test_a_drought_tolerant_species_fits_a_low_upkeep_wish():
    area = make_area(**OUTDOOR_BED, goals=[GrowingGoal.low_upkeep.value])
    f = fit.assess(make_species(water_regime="dry_thoroughly_between"), area)
    assert verdict_on(f, Axis.upkeep) == Verdict.fits


# --- goals -----------------------------------------------------------------

def test_a_goal_narrows_and_never_loosens():
    inedible = make_species(is_edible=False)
    plain = make_area(**OUTDOOR_BED)
    # Without the goal the field is not consulted at all.
    assert not any(f.axis == Axis.goal for f in fit.assess(inedible, plain))
    asked = make_area(**OUTDOOR_BED, goals=[GrowingGoal.edible.value])
    assert verdict_on(fit.assess(inedible, asked), Axis.goal) == Verdict.misfits


def test_an_unrecorded_goal_is_unknown_not_a_refusal():
    area = make_area(**OUTDOOR_BED, goals=[GrowingGoal.pollinators.value])
    f = fit.assess(make_species(attracts_pollinators=None), area)
    assert verdict_on(f, Axis.goal) == Verdict.unknown


def test_two_goals_produce_two_findings():
    area = make_area(
        **OUTDOOR_BED,
        goals=[GrowingGoal.edible.value, GrowingGoal.pollinators.value])
    f = fit.assess(
        make_species(is_edible=True, attracts_pollinators=True), area)
    assert len([x for x in f if x.axis == Axis.goal]) == 2


def test_an_area_asked_and_answered_nothing_gets_no_goal_findings():
    area = make_area(**OUTDOOR_BED, goals=[])
    f = fit.assess(make_species(is_edible=True), area)
    assert not any(x.axis == Axis.goal for x in f)


# --- borrowed values -------------------------------------------------------

def test_a_genus_borrowed_value_is_labelled_wherever_it_is_shown():
    """ADR 0002: a reader must never have to guess whether a fact was said
    about this species or about its cousins."""
    species = make_species(
        outdoor_sun_exposure=["full_sun"],
        care_provenance={"outdoor_sun_exposure": "genus_inferred"})
    f = fit.assess(species, make_area(**OUTDOOR_BED))
    sun = next(x for x in f if x.axis == Axis.sun)
    assert sun.borrowed is True
    assert "from the genus" in sun.sentence


def test_a_species_scoped_value_is_not_labelled():
    species = make_species(
        outdoor_sun_exposure=["full_sun"],
        care_provenance={"outdoor_sun_exposure": "sourced"})
    sun = next(x for x in fit.assess(species, make_area(**OUTDOOR_BED))
               if x.axis == Axis.sun)
    assert sun.borrowed is False
    assert "from the genus" not in sun.sentence


# --- cold is deliberately absent -------------------------------------------

def test_nothing_claims_to_know_whether_a_plant_survives_the_winter():
    """ADR 0006: there is no climate-normals source here, only a ten-day
    forecast, and a survival verdict from that is misattribution with
    arithmetic on top. The advisor's per-plant weather nudges keep that job."""
    species = make_species(chill_damage_f=20, outdoor_temp_min_f=-10)
    f = fit.assess(species, make_area(**OUTDOOR_BED))
    assert not any("winter" in x.sentence.lower() or "survive" in x.sentence.lower()
                   for x in f)


# --- enums arrive spelled two ways -----------------------------------------
# A row loaded from the table carries enum members; one built in code carries
# raw strings. Every test above builds rows in code, which is exactly how a
# comparison that only works on strings shipped once: every plant that
# belonged in its bed came back a misfit as soon as the rows came from the
# database. These run each axis both ways.

def test_every_axis_reads_an_enum_row_the_same_as_a_string_row():
    from app.models.models import SoilBase, WaterRegime

    as_strings = fit.assess(
        make_species(is_houseplant=False, outdoor_sun_exposure=["full_sun"],
                     soil_base="garden_bed", water_regime="dry_thoroughly_between",
                     is_edible=True),
        make_area(temp_exposure="outdoor", shelter="exposed",
                  sun_exposure="full_sun", surface="raised_bed",
                  goals=["low_upkeep", "edible"]))
    as_enums = fit.assess(
        make_species(is_houseplant=False,
                     outdoor_sun_exposure=[OutdoorSunExposure.full_sun],
                     soil_base=SoilBase.garden_bed,
                     water_regime=WaterRegime.dry_thoroughly_between,
                     is_edible=True),
        make_area(temp_exposure=TempExposure.outdoor, shelter=Shelter.exposed,
                  sun_exposure=SunExposure.full_sun,
                  surface=GrowingSurface.raised_bed,
                  goals=[GrowingGoal.low_upkeep, GrowingGoal.edible]))

    assert [(f.axis, f.verdict) for f in as_strings] == [
        (f.axis, f.verdict) for f in as_enums]
    assert [f.sentence for f in as_strings] == [f.sentence for f in as_enums]
    # And it is a real answer either way, not two matching piles of unknown.
    assert fit.score(as_enums) == 5


def test_an_enum_spelled_row_that_belongs_in_its_bed_is_not_a_misfit():
    """The exact failure: `str(SoilBase.garden_bed)` is not "garden_bed"."""
    from app.models.models import SoilBase

    area = make_area(temp_exposure=TempExposure.outdoor,
                     sun_exposure=SunExposure.full_sun,
                     surface=GrowingSurface.raised_bed)
    species = make_species(soil_base=SoilBase.garden_bed)
    assert verdict_on(fit.assess(species, area), Axis.soil) == Verdict.fits


# --- ranking ---------------------------------------------------------------

def test_one_misfit_disqualifies_however_good_the_rest_reads():
    area = make_area(**OUTDOOR_BED)
    good_but_wrong = make_species(
        common_name="Wrong", is_houseplant=False, soil_base="garden_bed",
        outdoor_sun_exposure=["full_shade"])      # the one contradiction
    assert fit.candidates([good_but_wrong], area) == []


def test_better_evidenced_species_rank_above_thinner_ones():
    area = make_area(**OUTDOOR_BED)
    thin = make_species(common_name="Thin", is_houseplant=False)
    thick = make_species(
        common_name="Thick", is_houseplant=False,
        outdoor_sun_exposure=["full_sun"], soil_base="garden_bed")
    ranked = fit.candidates([thin, thick], area)
    assert [c.species.common_name for c in ranked] == ["Thick", "Thin"]


def test_ties_break_on_name_so_the_list_does_not_reshuffle():
    area = make_area(**OUTDOOR_BED)
    b = make_species(common_name="Betony", is_houseplant=False)
    a = make_species(common_name="Achillea", is_houseplant=False)
    assert [c.species.common_name for c in fit.candidates([b, a], area)] == [
        "Achillea", "Betony"]


def test_a_tie_is_a_to_z_as_a_reader_sees_it_not_by_character_code():
    """The screens say level candidates are in A to Z order; a lower-case
    initial sorted by code point would land after every capital."""
    area = make_area(**OUTDOOR_BED)
    zinnia = make_species(common_name="Zinnia", is_houseplant=False)
    aloe = make_species(common_name="aloe", is_houseplant=False)
    assert [c.species.common_name for c in fit.candidates([zinnia, aloe], area)] == [
        "aloe", "Zinnia"]


def test_two_species_sharing_a_name_keep_one_order_whatever_order_they_arrive_in():
    """Two Blackberries: without a key past the common name, their order was
    whichever the database returned first -- free to change between requests."""
    area = make_area(**OUTDOOR_BED)
    fruticosus = make_species(common_name="Blackberry", scientific_name="Rubus fruticosus",
                              is_houseplant=False)
    allegheniensis = make_species(common_name="Blackberry",
                                  scientific_name="Rubus allegheniensis", is_houseplant=False)
    for arrival in ([fruticosus, allegheniensis], [allegheniensis, fruticosus]):
        assert [c.species.scientific_name for c in fit.candidates(arrival, area)] == [
            "Rubus allegheniensis", "Rubus fruticosus"]


def test_the_tie_order_never_outranks_the_evidence():
    """A to Z only ever decides between equals: an 'Aaron's Beard' with less
    confirmed still sits below a 'Zebra Grass' with more."""
    area = make_area(**OUTDOOR_BED)
    thin = make_species(common_name="Aaron's Beard", is_houseplant=False)
    thick = make_species(common_name="Zebra Grass", is_houseplant=False,
                         outdoor_sun_exposure=["full_sun"])
    assert [c.species.common_name for c in fit.candidates([thin, thick], area)] == [
        "Zebra Grass", "Aaron's Beard"]


def test_misfits_returns_only_what_needs_addressing():
    area = make_area(**OUTDOOR_BED)
    species = make_species(
        is_houseplant=False,                       # fits
        outdoor_sun_exposure=["full_shade"],       # misfits
        soil_base="cactus_succulent")              # misfits in a bed
    problems = fit.misfits(fit.assess(species, area))
    assert {f.axis for f in problems} == {Axis.sun, Axis.soil}


# --- who said so -----------------------------------------------------------
# A misfit is something a caretaker is asked to act on, so it has to be able
# to say whose word it is: "NC State Extension records it for part shade",
# not the app's opinion. Read off the same `care_sources` the care facts
# credit, and only for a value sourced for this species (ADR 0002).

NCSU = {"authority": "NC State Extension", "url": "https://plants.ces.ncsu.edu/x",
        "fields": ["outdoor_sun_exposure", "is_houseplant"], "inferred": False}
RHS = {"authority": "Royal Horticultural Society", "url": "https://rhs.org.uk/y",
       "fields": ["mature_height_in_max"], "inferred": False}


def test_a_sourced_misfit_names_the_authority_that_recorded_it():
    species = make_species(
        outdoor_sun_exposure=["part_shade", "full_shade"],
        care_provenance={"outdoor_sun_exposure": "sourced"},
        care_sources=[NCSU])
    sun = next(x for x in fit.assess(species, make_area(**OUTDOOR_BED))
               if x.axis == Axis.sun)
    assert sun.verdict == Verdict.misfits
    assert sun.authorities == ("NC State Extension",)


def test_a_genus_borrowed_value_is_not_credited_to_an_authority():
    """A genus page does not speak for the species; `borrowed` says so instead."""
    species = make_species(
        outdoor_sun_exposure=["full_sun"],
        care_provenance={"outdoor_sun_exposure": "genus_inferred"},
        care_sources=[{**NCSU, "inferred": True}])
    sun = next(x for x in fit.assess(species, make_area(**OUTDOOR_BED))
               if x.axis == Axis.sun)
    assert sun.borrowed is True
    assert sun.authorities == ()


def test_an_unknown_is_credited_to_nobody():
    findings = fit.assess(make_species(), make_area(**OUTDOOR_BED))
    assert all(f.authorities == () for f in findings)


def test_a_value_resolved_before_sources_existed_names_nobody_rather_than_guessing():
    species = make_species(
        outdoor_sun_exposure=["full_sun"],
        care_provenance={"outdoor_sun_exposure": "sourced"}, care_sources=None)
    sun = next(x for x in fit.assess(species, make_area(**OUTDOOR_BED))
               if x.axis == Axis.sun)
    assert sun.verdict == Verdict.fits and sun.authorities == ()


def test_size_is_credited_and_labelled_by_the_measurement_its_sentence_states():
    """A height-only misfit is not "from the genus" because the spread was,
    the rule the care facts keep: a flag on a field the row did not use does
    not taint it."""
    area = make_area(surface=GrowingSurface.windowsill, headroom_in=18)  # no footprint
    species = make_species(
        mature_height_in_max=48, mature_spread_in_max=30,
        care_provenance={"mature_height_in_max": "sourced",
                         "mature_spread_in_max": "genus_inferred"},
        care_sources=[RHS])
    size = next(x for x in fit.assess(species, area) if x.axis == Axis.footprint)
    assert size.verdict == Verdict.misfits
    assert size.borrowed is False
    assert "from the genus" not in size.sentence
    assert size.authorities == ("Royal Horticultural Society",)


def test_size_stays_labelled_when_the_borrowed_measurement_is_the_one_stated():
    area = make_area(**OUTDOOR_BED, area_sqft=4)          # about 2 ft across
    species = make_species(
        mature_spread_in_max=96,
        care_provenance={"mature_spread_in_max": "genus_inferred"})
    size = next(x for x in fit.assess(species, area) if x.axis == Axis.footprint)
    assert size.verdict == Verdict.misfits and size.borrowed is True
    assert "from the genus" in size.sentence


# --- which goal a finding answers ------------------------------------------

def test_each_goal_finding_says_which_goal_it_answers():
    """Edible and pollinators share an axis; a client saying "nothing here
    was checked for edibility" has to be able to tell them apart."""
    area = make_area(**OUTDOOR_BED, goals=["edible", "pollinators", "low_upkeep"])
    findings = fit.assess(
        make_species(is_edible=True, attracts_pollinators=None,
                     water_regime="keep_moist"), area)
    by_goal = {f.goal: f for f in findings if f.goal}
    assert by_goal["edible"].verdict == Verdict.fits
    assert by_goal["pollinators"].verdict == Verdict.unknown
    assert by_goal["low_upkeep"].axis == Axis.upkeep
    assert by_goal["low_upkeep"].verdict == Verdict.misfits


def test_the_space_axes_answer_no_goal():
    findings = fit.assess(
        make_species(is_houseplant=False, outdoor_sun_exposure=["full_sun"]),
        make_area(**OUTDOOR_BED))
    assert all(f.goal is None for f in findings)


# --- the candidate rule, stated once ---------------------------------------

def test_is_candidate_needs_no_misfit_and_one_confirmed_fit():
    area = make_area(**OUTDOOR_BED)
    assert fit.is_candidate(fit.assess(make_species(is_houseplant=False), area))
    assert not fit.is_candidate(fit.assess(make_species(), area)), \
        "nothing known is not a recommendation"
    assert not fit.is_candidate(fit.assess(
        make_species(is_houseplant=False, outdoor_sun_exposure=["full_shade"]), area))
