"""The fact block reads the claim graph, and says where it got each value.

The advisor prompt, the vision prompt and the deterministic stub all describe
a species to someone. Until now each read the six legacy columns as if every
row had them; a row minted from the claim tranche has none (ADR 0005), a row
the tranche resolved has something better, and a value borrowed from the genus
has to be labelled wherever it shows (ADR 0002). These tests pin one shared
helper for all three surfaces: a resolved concept replaces its legacy line,
nothing is stated twice, nothing absent is invented, and the authorities are
named -- names only, never a quote (ADR 0003).
"""
from app.models.models import (
    CareDataStatus, Environment, LightNeed, MaturityStage, Plant, Shelter,
    Species, SpeciesSource, SunExposure, TempExposure,
)
from app.services.advisor import (
    _advise_stub, _build_prompt, _weather_nudges, species_fact_lines,
)
from app.services.vision import _build_context

NCSU = "https://plants.ces.ncsu.edu/plants/fuchsia-magellanica/"
RHS = "https://www.rhs.org.uk/plants/fuchsia-magellanica"
GENUS_PAGE = "https://plants.ces.ncsu.edu/plants/fuchsia/"

RESOLVED = dict(
    light_fc_min=100, light_fc_good=250, direct_sun_hours_max=2.0,
    water_regime="dry_surface_between", water_check_depth_cm=3.0,
    water_growing_days_est=7, water_dormant_days_est=14,
    humidity_need="high",
    day_f_min=65, day_f_max=80, night_f_min=55, chill_damage_f=45,
    soil_base="chunky_aroid", soil_drainage="fast",
    soil_ph_min=5.5, soil_ph_max=6.5,
    fertilize_active_months=[3, 4, 5, 6, 7, 8, 9, 10],
    fertilize_interval_days=14, fertilize_strength="half",
    outdoor_sun_exposure=["part_sun", "part_shade"],
    hardiness_zones=[7, 8, 9, 10],
)
ALL_SOURCED = {f: "sourced" for f in RESOLVED}
SOURCES = [
    {"authority": "Royal Horticultural Society", "url": RHS,
     "fields": ["day_f_max", "day_f_min", "water_regime"], "inferred": False},
    {"authority": "NC State Extension", "url": NCSU,
     "fields": ["light_fc_good", "light_fc_min", "soil_base"], "inferred": False},
    {"authority": "NC State Extension", "url": GENUS_PAGE,
     "fields": ["chill_damage_f"], "inferred": True},
]


def legacy_species(**over):
    fields = dict(
        common_name="Test Fern", scientific_name="Testus fernus",
        light_need=LightNeed.bright_indirect, humidity_pct_min=40,
        humidity_pct_max=60, temp_f_min=60, temp_f_max=85,
        soil_type="well-draining", toxic_to_pets=False)
    fields.update(over)
    return Species(**fields)


def minted_species(**over):
    """A row the sync minted: name, common name, and nothing invented."""
    fields = dict(
        common_name="Hardy Fuchsia", scientific_name="Fuchsia magellanica",
        source=SpeciesSource.claims, toxic_to_pets=None, care_notes="")
    fields.update(over)
    return Species(**fields)


def sourced_species(**over):
    provenance = dict(ALL_SOURCED, chill_damage_f="genus_inferred")
    fields = dict(RESOLVED, care_data_status=CareDataStatus.sourced,
                  care_provenance=provenance, care_sources=SOURCES)
    fields.update(over)
    return minted_species(**fields)


def make_plant():
    return Plant(nickname="Ferny", species_id=1,
                 maturity_stage=MaturityStage.mature)


def make_env():
    return Environment(name="Balcony", shelter=Shelter.exposed,
                       temp_exposure=TempExposure.outdoor,
                       sun_exposure=SunExposure.full_sun)


def forecast(high=82, low=66, rain=10):
    return {"current": {"temp_f": 78, "uv_index": 5},
            "daily": [{"date": "2026-07-24", "high_f": high, "low_f": low,
                       "precip_chance_pct": rain, "uv_max": 6}]}


def line_starting(lines, prefix):
    found = [ln for ln in lines if ln.startswith(prefix)]
    assert len(found) == 1, f"{prefix!r}: {found}"
    return found[0]


# --- legacy rows read exactly as before -------------------------------------

def test_legacy_lines_are_unchanged():
    lines = species_fact_lines(legacy_species())
    for pinned in ("- Light need: bright_indirect", "- Humidity: 40-60%",
                   "- Temperature: 60-85 F", "- Soil: well-draining",
                   "- Toxic to pets: no"):
        assert pinned in lines
    # A legacy row with values has data; it is not "none cited".
    assert not any(ln.startswith("- Care data:") for ln in lines)


def test_toxicity_line_has_three_states():
    assert "- Toxic to pets: yes" in species_fact_lines(
        legacy_species(toxic_to_pets=True))
    assert "- Toxic to pets: no" in species_fact_lines(
        legacy_species(toxic_to_pets=False))
    assert "- Toxic to pets: no record" in species_fact_lines(
        legacy_species(toxic_to_pets=None))


# --- resolved values replace, never sit beside, their legacy line -----------

def test_resolved_concepts_replace_their_legacy_lines():
    """A linked row keeps its legacy columns; the block must not read them
    for any concept the claims resolved."""
    linked = legacy_species(**RESOLVED, care_data_status="sourced",
                            care_provenance=ALL_SOURCED, care_sources=SOURCES)
    lines = species_fact_lines(linked)

    assert not any(ln.startswith("- Light need:") for ln in lines)
    assert "- Humidity: 40-60%" not in lines
    assert "- Temperature: 60-85 F" not in lines
    assert "- Soil: well-draining" not in lines

    light = line_starting(lines, "- Light:")
    assert "100 footcandles" in light and "250 footcandles" in light
    assert "2 hours of direct sun" in light
    assert line_starting(lines, "- Humidity:").startswith("- Humidity: high")
    temp = line_starting(lines, "- Temperature:")
    assert "days 65-80 F" in temp and "nights from 55 F" in temp
    assert "cold damage below 45 F" in temp
    soil = line_starting(lines, "- Soil:")
    assert "chunky aroid mix" in soil and "fast-draining" in soil
    assert "pH 5.5-6.5" in soil
    assert "chunky_aroid" not in soil  # a token is not a fact for a reader

    for concept in ("- Light", "- Humidity", "- Temperature", "- Soil",
                    "- Water", "- Fertilize"):
        assert sum(ln.startswith(concept) for ln in lines) == 1, concept


def test_a_legacy_line_under_a_cited_line_is_marked_as_a_catalog_value():
    """A linked row keeps its legacy columns for every concept nothing
    resolved, and those lines then sit under "cited to ..." looking equally
    cited. The care-data line names which of them are not -- the pinned
    legacy strings themselves stay exactly as they were."""
    one_fact = legacy_species(
        water_regime="dry_surface_between", care_data_status="sourced",
        care_provenance={"water_regime": "sourced"}, care_sources=SOURCES[:1])
    lines = species_fact_lines(one_fact)
    assert "- Light need: bright_indirect" in lines
    assert line_starting(lines, "- Care data:") == (
        "- Care data: cited to Royal Horticultural Society; light, humidity, "
        "temperature and soil above are catalog values, not cited")

    all_but_soil = legacy_species(
        **dict(RESOLVED, soil_base=None, soil_drainage=None,
               soil_ph_min=None, soil_ph_max=None),
        care_data_status="sourced", care_provenance=ALL_SOURCED,
        care_sources=SOURCES)
    assert line_starting(species_fact_lines(all_but_soil), "- Care data:") == (
        "- Care data: cited to NC State Extension, Royal Horticultural "
        "Society; soil above is a catalog value, not cited")

    borrowed = legacy_species(
        water_regime="dry_surface_between", care_data_status="inferred",
        care_provenance={"water_regime": "genus_inferred"},
        care_sources=[dict(SOURCES[0], inferred=True)])
    assert line_starting(species_fact_lines(borrowed), "- Care data:") == (
        "- Care data: borrowed from the genus, not confirmed for this "
        "species; light, humidity, temperature and soil above are catalog "
        "values, not cited")

    # A legacy row nothing resolved has no cited line to sit under.
    assert not any(ln.startswith("- Care data:")
                   for ln in species_fact_lines(legacy_species()))


def test_a_zero_hour_sun_ceiling_reads_as_no_direct_sun():
    light = line_starting(
        species_fact_lines(sourced_species(direct_sun_hours_max=0)), "- Light:")
    assert light.endswith("; no direct sun")
    assert "0 hours" not in light


def test_water_line_wording_and_no_dry_down_target():
    sp = sourced_species(water_dry_down_target="verbatim researcher prose")
    water = line_starting(species_fact_lines(sp), "- Water:")
    assert water == (
        "- Water: let the surface dry between waterings; check 3 cm down; "
        "roughly every 7 days in growth, 14 in dormancy (estimate)")

    for regime, sentence in (
        ("keep_moist", "keep the medium evenly moist"),
        ("keep_barely_moist", "keep the medium barely moist"),
        ("dry_thoroughly_between",
         "let the medium dry thoroughly between waterings"),
    ):
        sp = sourced_species(water_regime=regime, water_check_depth_cm=None,
                             water_growing_days_est=None,
                             water_dormant_days_est=None)
        assert line_starting(species_fact_lines(sp), "- Water:") == (
            f"- Water: {sentence}")

    partial = sourced_species(water_dormant_days_est=None)
    assert line_starting(species_fact_lines(partial), "- Water:").endswith(
        "roughly every 7 days in growth (estimate)")
    assert "verbatim" not in "\n".join(species_fact_lines(partial))


def test_fertilize_months_read_as_a_span_only_when_contiguous():
    def months(active):
        sp = sourced_species(fertilize_active_months=active,
                             fertilize_interval_days=None,
                             fertilize_strength=None)
        return line_starting(species_fact_lines(sp), "- Fertilize:")

    assert months([3, 4, 5, 6, 7, 8, 9, 10]) == "- Fertilize: Mar-Oct"
    assert months([11, 12, 1, 2, 3]) == "- Fertilize: Nov-Mar"
    assert months([3, 9]) == "- Fertilize: Mar and Sep"
    assert months([3, 6, 9]) == "- Fertilize: Mar, Jun and Sep"
    full = line_starting(species_fact_lines(sourced_species()), "- Fertilize:")
    assert full == "- Fertilize: Mar-Oct; every 14 days; half strength"


def test_outdoor_sun_and_hardiness_lines():
    lines = species_fact_lines(sourced_species())
    assert "- Outdoor sun: part sun, part shade" in lines
    assert "- Hardiness zones: 7, 8, 9, 10" in lines


# --- provenance is visible ---------------------------------------------------

def test_genus_inferred_values_are_labelled_and_sourced_ones_are_not():
    lines = species_fact_lines(sourced_species())
    temp = line_starting(lines, "- Temperature:")
    assert "cold damage below 45 F (genus-inferred)" in temp
    assert "days 65-80 F (genus-inferred)" not in temp
    assert "(genus-inferred)" not in line_starting(lines, "- Water:")


def test_sourced_row_names_its_authorities_sorted_and_deduped():
    lines = species_fact_lines(sourced_species())
    assert ("- Care data: cited to NC State Extension, "
            "Royal Horticultural Society") in lines
    assert not any("rhs.org.uk" in ln or "ncsu.edu" in ln for ln in lines)


def test_row_borrowed_entirely_from_the_genus_says_so():
    borrowed = sourced_species(
        care_data_status=CareDataStatus.inferred,
        care_provenance={f: "genus_inferred" for f in RESOLVED},
        care_sources=[dict(s, inferred=True) for s in SOURCES])
    lines = species_fact_lines(borrowed)
    assert ("- Care data: borrowed from the genus, not confirmed for this "
            "species") in lines
    value_lines = [ln for ln in lines if ln.startswith((
        "- Light:", "- Humidity:", "- Temperature:", "- Soil:", "- Water:",
        "- Fertilize:", "- Outdoor sun:", "- Hardiness zones:"))]
    assert value_lines and all("(genus-inferred)" in ln for ln in value_lines)


def test_bare_minted_row_states_only_what_it_has():
    lines = species_fact_lines(minted_species())
    assert lines == [
        "- Common name: Hardy Fuchsia",
        "- Scientific name: Fuchsia magellanica",
        "- Toxic to pets: no record",
        "- Care data: none cited for this species yet",
    ]
    assert "None" not in "\n".join(lines)


def test_curated_notes_line_only_when_there_are_notes():
    assert not any(ln.startswith("- Curated notes:")
                   for ln in species_fact_lines(minted_species()))
    assert "- Curated notes: Likes a cool porch." in species_fact_lines(
        legacy_species(care_notes="Likes a cool porch."))


# --- both prompts and the stub use the one block -----------------------------

def test_advisor_prompt_and_vision_context_carry_the_shared_block():
    sp = sourced_species()
    block = "\n".join(species_fact_lines(sp))
    assert block in _build_prompt(sp, make_plant(), [], [])
    assert block in _build_context(sp, make_plant(), [])

    minted = "\n".join(species_fact_lines(minted_species()))
    assert minted in _build_prompt(minted_species(), make_plant(), [], [])
    assert minted in _build_context(minted_species(), make_plant(), [])


def test_stub_adds_a_sources_line_for_the_regime():
    out = _advise_stub(sourced_species(), make_plant(), [], [])
    assert "💧 From its sources: let the surface dry between waterings." in out
    assert "(borrowed from the genus)" not in out
    assert "From its sources" not in _advise_stub(
        legacy_species(), make_plant(), [], [])


def test_borrowed_regime_is_labelled_in_prompt_and_stub():
    sp = sourced_species(care_provenance=dict(
        ALL_SOURCED, water_regime="genus_inferred"))
    prompt = _build_prompt(sp, make_plant(), [], [])
    assert ("- Water: let the surface dry between waterings (genus-inferred); "
            "check 3 cm down") in prompt
    out = _advise_stub(sp, make_plant(), [], [])
    assert ("💧 From its sources: let the surface dry between waterings. "
            "(borrowed from the genus)") in out


# --- weather nudges read the resolved thresholds -----------------------------

def test_nudges_prefer_resolved_thresholds_over_legacy():
    sp = legacy_species(temp_f_min=55, temp_f_max=85,
                        day_f_max=90, chill_damage_f=40,
                        care_provenance={"day_f_max": "sourced",
                                         "chill_damage_f": "sourced"})
    quiet = _weather_nudges(sp, make_env(), forecast(high=88, low=45))
    assert not any("Heat ahead" in n or "Cold night" in n for n in quiet)

    loud = _weather_nudges(sp, make_env(), forecast(high=95, low=35))
    heat = next(n for n in loud if "Heat ahead" in n)
    cold = next(n for n in loud if "Cold night" in n)
    assert "90°F" in heat and "85°F" not in heat
    assert "40°F" in cold and "55°F" not in cold
    assert "(borrowed from the genus)" not in heat + cold


def test_nudges_label_a_borrowed_threshold():
    sp = sourced_species(care_provenance=dict(
        ALL_SOURCED, day_f_max="genus_inferred", chill_damage_f="genus_inferred"))
    nudges = _weather_nudges(sp, make_env(), forecast(high=95, low=35))
    heat = next(n for n in nudges if "Heat ahead" in n)
    cold = next(n for n in nudges if "Cold night" in n)
    assert heat.endswith(" (borrowed from the genus)")
    assert "(borrowed from the genus)" in cold  # chill_damage_f is inferred
    assert "45°F" in cold


def test_nudges_keep_their_guards_on_a_bare_row():
    nudges = _weather_nudges(minted_species(), make_env(),
                             forecast(high=110, low=10, rain=90))
    assert not any("Heat ahead" in n or "Cold night" in n for n in nudges)
    assert any("Rain likely" in n for n in nudges)
