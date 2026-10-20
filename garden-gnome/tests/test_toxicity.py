"""Part-aware toxicity and the sentences generated from it.

The cases here are the ones a boolean gets wrong: plants that are both food and
poison depending on the part, and plants whose risk differs sharply by animal.
"""
import json
from pathlib import Path

import pytest

from app.services import toxicity as tx


# --- the contradictory cases ------------------------------------------------

def test_tomato_leads_with_what_is_edible():
    """'Tomato: toxic' is contradictory to anyone holding a tomato. Confirm the
    reader's experience first, then warn about the part that matters."""
    t = tx.lookup("Solanum lycopersicum")
    assert t.is_contradictory
    text = tx.describe(t, "Tomato")
    assert text.startswith("The ripe fruit is the crop;")
    assert text.index("crop") < text.index("toxic"), "safe part must come first"
    assert "leaves and stems" in text
    assert "tomatine" in text


def test_rhubarb_distinguishes_stalk_from_leaf():
    t = tx.lookup("Rheum rhabarbarum")
    text = tx.describe(t, "Rhubarb")
    assert "stalks" in text and "leaves" in text
    assert t.severity == "severe"


def test_potato_names_the_green_and_sprouted_exception():
    t = tx.lookup("Solanum tuberosum")
    assert "tuber" in t.edible_parts
    text = tx.describe(t, "Potato")
    assert "solanine" in text
    # Every part key has a label: "and sprout are toxic" was the old slip.
    assert "the sprouts" in text and "green skin on the tubers" in text
    assert " sprout " not in text and "green_tuber" not in text


# --- risk that differs by animal --------------------------------------------

def test_lily_warns_specifically_about_cats():
    """The worst failure mode of a boolean: lilies are lethal to cats and only
    mildly upsetting to dogs."""
    t = tx.lookup("Lilium longiflorum")
    assert t.at_risk == ["cats"]
    assert t.severity == "severe"
    text = tx.describe(t, "Easter Lily")
    assert "cats" in text
    assert "vet" in text
    assert "kidney" in text


def test_daylily_is_also_a_cat_risk():
    assert tx.lookup("Hemerocallis fulva").at_risk == ["cats"]


def test_the_aroid_table_states_the_pattern_and_leaves_severity_to_sources():
    """Calcium oxalate in every part is the family's; how bad it is is the
    species'. NC State rates Monstera low and Dieffenbachia high, so the
    table claims no severity of its own -- and never "unpleasant rather than
    dangerous", which no source said about any of them."""
    t = tx.lookup("Epipremnum aureum")
    assert t.severity == "unknown"
    text = tx.describe(t, "Pothos")
    assert "calcium oxalate" in text
    assert "people" in text
    assert "⚠️" not in text
    assert "ildly" not in text
    assert "rather than dangerous" not in text


@pytest.mark.parametrize("name", [
    "Monstera deliciosa", "Philodendron hederaceum", "Spathiphyllum wallisii",
    "Dieffenbachia seguine", "Anthurium andraeanum",
])
def test_aroid_genera_are_recognized(name):
    assert tx.lookup(name).agent == "calcium oxalate crystals"


def test_unknown_species_has_no_special_case():
    assert tx.lookup("Ficus lyrata") is None
    assert tx.lookup("") is None


# --- honesty about absence --------------------------------------------------

def test_unknown_is_not_reported_as_safe():
    text = tx.describe(tx.Toxicity(toxic=None), "This plant")
    assert "unknown rather than safe" in text


def test_a_false_flag_is_not_a_guarantee():
    """A stored False means 'nothing recorded', which is weaker than 'safe'."""
    text = tx.describe(tx.from_legacy(False, "Ficus lyrata"), "Fiddle Leaf Fig")
    assert "not a guarantee" in text


def test_silence_in_prose_is_never_read_as_safety():
    assert tx.parse_toxicity("A handsome plant with glossy leaves.") is None


# --- parsing prose ----------------------------------------------------------

def test_parses_parts_animals_and_agent():
    t = tx.parse_toxicity(
        "The leaves are toxic to cats and dogs, containing calcium oxalate."
    )
    assert "leaf" in t.parts
    assert set(t.at_risk) == {"cats", "dogs"}
    assert t.agent == "calcium oxalate"


def test_severity_is_read_from_language():
    assert tx.parse_toxicity("Fatal if eaten; causes kidney failure.").severity == "severe"
    assert tx.parse_toxicity("A mild irritant if chewed.").severity == "mild"


def test_all_parts_collapses_other_parts():
    t = tx.parse_toxicity("All parts are poisonous, including the leaves and berries.")
    assert t.parts == ["all"]


# --- legacy upgrade ---------------------------------------------------------

def test_known_nuance_overrides_a_legacy_flag():
    """The catalog's boolean says only 'toxic'; the nuance is better."""
    t = tx.from_legacy(True, "Solanum lycopersicum")
    assert t.is_contradictory
    assert "ripe_fruit" in t.edible_parts


def test_legacy_true_without_nuance_stays_conservative():
    """Still a warning, but not "all parts": a bare flag says the plant is
    toxic, not which of it is, and the part list was invented detail."""
    t = tx.from_legacy(True, "Ficus lyrata")
    assert t.toxic is True
    assert t.parts == []
    text = tx.describe(t, "Fiddle Leaf Fig")
    assert text.startswith("Toxic to pets.")
    assert "all parts" not in text


def test_entry_point_renders_for_a_catalog_row():
    text = tx.describe_for_species("Solanum lycopersicum", "Tomato", True)
    assert text.startswith("The ripe fruit is the crop; the leaves and stems "
                           "are toxic to cats and dogs (tomatine)")
    assert "You can eat" not in text


def test_severe_cases_direct_to_a_vet_and_do_not_triage():
    text = tx.describe_for_species("Lilium longiflorum", "Easter Lily", True)
    assert "contact a vet" in text.lower()
    assert "do not wait" in text.lower()
    # Cats only: nothing recorded about people, so no Poison Control line.
    assert "Poison Control" not in text


# --- it actually reaches the client -----------------------------------------

def test_species_model_exposes_the_generated_sentence():
    """A property on the model, so every endpoint returning a Species picks it
    up without each router being patched."""
    from app.models.models import Species
    sp = Species(common_name="Tomato", scientific_name="Solanum lycopersicum",
                 light_need="direct", humidity_pct_min=40, humidity_pct_max=70,
                 temp_f_min=55, temp_f_max=90, soil_type="loam",
                 toxic_to_pets=True)
    assert "The ripe fruit is the crop" in sp.toxicity_description


def test_derived_field_survives_serialization_to_the_api_schema():
    """Guards the wiring: a schema change that drops the field would otherwise
    fail silently, and the app would quietly fall back to the flat chip."""
    from app.models.models import Species
    from app.models.schemas import SpeciesDetail, SpeciesRead

    sp = Species(id=1, common_name="Easter Lily", scientific_name="Lilium longiflorum",
                 light_need="direct", humidity_pct_min=40, humidity_pct_max=60,
                 temp_f_min=50, temp_f_max=80, soil_type="loam",
                 toxic_to_pets=True)
    for schema in (SpeciesDetail, SpeciesRead):
        out = schema.model_validate(sp, from_attributes=True)
        assert "cats" in out.toxicity_description
        assert out.toxic_to_pets is True, "the raw flag stays available for filtering"


# --- what a claim settled ---------------------------------------------------

def test_no_verdict_is_not_reported_as_no_information():
    """A minted row can hold a cited description of harm server-side and no
    verdict yet; 'no information recorded' would be untrue of it."""
    text = tx.describe(tx.Toxicity(toxic=None), "Winter Daphne")
    assert text.startswith("No toxicity verdict recorded for winter daphne yet")
    assert "unknown rather than safe" in text


def test_a_cited_false_names_who_said_so():
    """'Nothing harmful has been noted' is the legacy flag's story. When an
    authority stated the flag, the sentence credits it -- and stays short of
    a guarantee, because a hazard to people is not a hazard to pets."""
    text = tx.describe_for_species("Toxicodendron radicans", "Poison Ivy", False,
                                   cited_to="UGA Cooperative Extension")
    assert text.startswith(
        "UGA Cooperative Extension records no toxicity to pets for poison ivy")
    assert "not a guarantee" in text
    assert "nothing harmful" not in text


def test_a_false_nobody_cited_is_not_called_a_finding():
    """A legacy False is a catalog default. "Nothing harmful has been noted"
    claimed someone looked; nobody on record did."""
    text = tx.describe_for_species("Ficus lyrata", "Fiddle Leaf Fig", False)
    assert text.startswith(
        "No toxicity is recorded for fiddle leaf fig in our sources yet.")
    assert "not a guarantee of safety" in text
    assert "nothing harmful has been noted" not in text


def test_cited_authority_is_read_off_the_page_that_won_the_flag():
    page = {"authority": "UGA Cooperative Extension", "url": "https://x/",
            "fields": ["toxic_to_pets"], "inferred": False}
    other = {"authority": "NC State Extension", "url": "https://y/",
             "fields": ["soil_base"], "inferred": False}
    assert tx.cited_authority({"toxic_to_pets": "sourced"}, [other, page]) == \
        "UGA Cooperative Extension"
    assert tx.cited_authority({"toxic_to_pets": "sourced"}, [other]) == ""
    assert tx.cited_authority({"toxic_to_pets": "sourced"}, None) == ""
    assert tx.cited_authority(None, [page]) == ""


# --- the cited evidence outranks the tables ---------------------------------
#
# Fixtures are shaped like the tranche's own text: `toxicity_detail` is the
# researcher's restatement of the NC State poison block, and a passage is a
# claim's verbatim quote with the authority that published it.

class P:
    """A claim passage, as claims.store.safety_passages returns one."""

    def __init__(self, field, value, quote, authority="NC State Extension"):
        self.field, self.value, self.quote = field, value, quote
        self.authority = authority


DIEFFENBACHIA_DETAIL = (
    "Severity rated HIGH by NC State Extension. Leaves, stems, roots and sap "
    "all contain calcium oxalate crystals and oxalic acid. Throat swelling can "
    "compromise the airway.")
POTATO_DETAIL = (
    "NC State Extension's Plant Toolbox rates this species \"High\" poison "
    "severity, names solanine and other alkaloids as the toxic principle, and "
    "separately flags it a problem for cats, dogs, horses and children.")
POISON_IVY_DETAIL = (
    "This species' hazard is a contact-dermatitis one, not an ingestion "
    "toxin. All parts contain urushiol; NC State Extension rates human Poison "
    "Severity as \"High\".")


def test_a_cited_high_rating_beats_the_aroid_table():
    """The audit's blocker: Dieffenbachia read "Mildly toxic ... Unpleasant
    rather than dangerous" while NC State rates it high severity."""
    text = tx.describe_for_species("Dieffenbachia seguine", "Dumb Cane", True,
                                   cited_to="NC State Extension",
                                   detail=DIEFFENBACHIA_DETAIL)
    # NC State's rating is the people's: they are seriously at risk, and the
    # animals are what the pet tags say, toxic.
    assert text.startswith("⚠️ Seriously toxic to people, and toxic to cats "
                           "and dogs: all parts")
    assert "NC State Extension rates its poison severity for people high." in text
    assert "Poison Control (US 1-800-222-1222)" in text
    assert "ildly" not in text and "rather than dangerous" not in text


@pytest.mark.parametrize("rating", ["Medium", "High"])
def test_a_cited_medium_or_high_hazard_is_never_called_mild(rating):
    detail = f"NC State rates poison severity {rating}. All parts contain calcium oxalate."
    text = tx.describe_for_species("Epipremnum aureum", "Pothos", True,
                                   cited_to="NC State Extension", detail=detail)
    assert "ildly" not in text
    assert f"rates its poison severity for people {rating.lower()}" in text


def test_a_cited_low_rating_is_the_only_way_to_read_mild():
    """And it reads mild for people only. NC State's Poison Severity sits
    under its Poisonous to Humans heading; the cat tag carries no severity,
    and "mildly toxic to cats" would put words in its mouth -- on garlic,
    azaleas and daffodils among others."""
    detail = "NC State rates poison severity Low and flags the plant as a problem for cats."
    text = tx.describe_for_species("Monstera deliciosa", "Monstera", True,
                                   cited_to="NC State Extension", detail=detail)
    assert text.startswith("Toxic to cats and dogs, and mildly toxic to people:")
    assert "NC State Extension rates its poison severity for people low." in text
    assert "ildly toxic to cats" not in text


def test_a_low_rating_on_a_bare_pet_flag_is_not_read_as_mild_for_pets():
    """Garlic: NC State tags cats, dogs and horses, and its Poisonous to
    Humans block says Low. The old sentence was "Mildly toxic to pets and
    people"."""
    passages = [P("toxic_to_pets", True,
                  "Problem for Cats Problem for Dogs Problem for Horses "
                  "Poisonous to Humans: Poison Severity: Low")]
    text = tx.describe_for_species("Allium testivum", "Garlic", True,
                                   cited_to="NC State Extension", passages=passages)
    assert text.startswith("Toxic to pets, and mildly toxic to people.")
    assert "ildly toxic to pets" not in text
    tox = tx.from_legacy(True, "Allium testivum", "NC State Extension",
                         tx.read_evidence(None, passages))
    assert (tox.animal_severity, tox.people_severity) == ("unknown", "mild")
    assert tx.hazard_line(tox) == "Toxic to pets and people."


def test_a_high_rating_is_serious_for_people_and_not_said_of_pets():
    detail = "NC State's Poisonous to Humans block: Poison Severity: High."
    tox = tx.from_legacy(True, "Testus highii", "NC State Extension",
                         tx.read_evidence(detail))
    text = tx.describe(tox, "Test Plant")
    assert text.startswith("⚠️ Seriously toxic to people, and toxic to pets.")
    assert tx.hazard_line(tox) == "Seriously toxic to people, and toxic to pets."


def test_a_source_calling_it_fatal_to_pets_is_what_makes_pets_serious():
    """The grave animal wording the rating cannot supply: NC State's own
    "Ingestion of this plant by pets can be fatal" (Kalanchoe)."""
    passages = [P("toxicity_detail", "prose",
                  "Ingestion of this plant by pets can be fatal and causing "
                  "abnormal heart rate, seizures, and death.")]
    evidence = tx.read_evidence(None, passages)
    assert evidence.animals_grave and not evidence.people
    tox = tx.from_legacy(True, "Kalanchoe testii", "NC State Extension", evidence)
    assert tox.animal_severity == "severe"
    assert tx.describe(tox, "Kalanchoe").startswith("⚠️ Seriously toxic to pets.")


@pytest.mark.parametrize("detail", [
    # A pet tag carries no severity, so a grave word beside one is not the pets'.
    "Every part except the aril is toxic, ingestion may be fatal, and the "
    "species is separately tagged a problem for cats, dogs and horses.",
    # Mentioning pets to say the statement does not name them.
    "MBG adds an unscoped statement, \"All parts of this plant are highly toxic "
    "if ingested\", which does not itself name cats or dogs.",
    # Grave words about horses and livestock are not about pets.
    "May be fatal to horses and livestock.",
])
def test_grave_words_near_a_pet_tag_are_not_grave_words_about_pets(detail):
    assert not tx.read_evidence(detail).animals_grave


def test_potato_takes_its_severity_from_nc_state():
    """The table said moderate and "stomach upset"; NC State says high
    severity, may be fatal. The source wins."""
    text = tx.describe_for_species("Solanum tuberosum", "Potatoes", True,
                                   cited_to="NC State Extension",
                                   detail=POTATO_DETAIL)
    # The tubers are the crop, and the rating is the people's: the pets get
    # the table's own word.
    assert text.startswith("⚠️ The tubers are the crop; the leaves and stems, "
                           "the sprouts, the berries and any green skin on the "
                           "tubers are seriously toxic to people, and toxic to "
                           "cats and dogs (solanine).")
    assert "NC State Extension rates its poison severity for people high." in text
    assert "stomach upset" not in text


def test_a_table_severity_is_never_talked_down_by_a_lower_rating():
    """NC State rates the regal lily medium for people; for cats the table's
    kidney-failure warning stands, and people get their own sentence so the
    cat's kidneys are not read as theirs."""
    detail = ("NC State's Poisonous to Humans block (human-scoped) gives "
              "Poison Severity: Medium. NC State prose: 'The plant is toxic "
              "to cats and can be fatal.'")
    text = tx.describe_for_species("Lilium regale", "Regal Lily", True,
                                   cited_to="NC State Extension", detail=detail)
    assert text.startswith("⚠️ Seriously toxic to cats: all parts")
    assert ("It is also toxic to people: NC State Extension rates its poison "
            "severity medium.") in text


def test_a_cited_false_beats_the_tables():
    """An authority that says non-toxic is believed over a pattern in code."""
    t = tx.from_legacy(False, "Lilium testii", cited_to="NC State Extension")
    assert t.toxic is False
    assert tx.describe(t, "Test Lily").startswith(
        "NC State Extension records no toxicity to pets for test lily")


# --- people ------------------------------------------------------------------

def test_poison_ivy_names_people_and_its_rating():
    """NC State tags poison ivy non-toxic for cats and dogs. A pets-only
    sentence told a family it had no recorded toxicity."""
    text = tx.describe_for_species("Toxicodendron radicans", "Poison Ivy", False,
                                   cited_to="NC State Extension",
                                   detail=POISON_IVY_DETAIL)
    assert text.startswith("⚠️ Seriously toxic to people.")
    assert "NC State Extension rates its poison severity for people high." in text
    assert "NC State Extension records no toxicity to pets" in text
    assert "not a guarantee of safety" in text
    assert "Poison Control" in text


def test_a_hazard_to_people_with_no_pet_verdict():
    """Carolina jessamine: NC State rates it high, and no source speaks for
    pets. Both halves are said."""
    detail = ("NC State Extension's Poison block (human-scoped) rates Poison "
              "Severity: High; may cause respiratory failure.")
    text = tx.describe_for_species("Gelsemium sempervirens", "Carolina Jessamine",
                                   None, detail=detail)
    assert text.startswith("⚠️ Seriously toxic to people.")
    assert "No verdict on pets is recorded yet" in text
    assert "unknown" in text and "safe" in text


def test_a_detail_that_says_people_are_not_addressed_is_not_a_hazard():
    for detail in (
        "The page carries no \"Poisonous to Humans\" section, and no admissible "
        "source addresses human toxicity for this species.",
        "NC State Extension states the plant is non-toxic to pets and humans.",
        "NC State's page has no Poison block, so there is no human-scoped "
        "severity rating.",
    ):
        evidence = tx.read_evidence(detail)
        assert not evidence.people, detail
        assert evidence.rating == "", detail


@pytest.mark.parametrize("detail,rating", [
    # The negation is the cat tag's, closed by the parenthesis.
    ("NC State's Poisonous to Humans block (human-scoped, not a cat/dog "
     "rating) gives Poison Severity Medium.", "medium"),
    ("Its \"Poisonous to Humans\" (human-scoped, not cat/dog-scoped) with "
     "Poison Severity \"High\".", "high"),
    # The negation is the scope's, not the hazard's.
    ("The page-top banner, which states no scope, reads \"This plant has "
     "medium severity poison characteristics.\"", "medium"),
])
def test_a_negation_of_something_else_does_not_cancel_the_rating(detail, rating):
    evidence = tx.read_evidence(detail)
    assert evidence.rating == rating
    assert evidence.people


def test_a_tag_list_negates_only_its_own_tag():
    evidence = tx.read_evidence(
        "Tags: #non-edible berries #problem for children #problem for dogs")
    assert evidence.people


def test_a_rating_about_a_look_alike_is_not_this_plants():
    """The parsnip record mentions that hemlock is rated high on its own
    page; that is hemlock's rating."""
    detail = ("NC State rates Poison Severity Medium. Pastinaca sativa is often "
              "confused with Conium maculatum (poison hemlock, rated high "
              "severity on its own NC State page).")
    assert tx.read_evidence(detail).rating == "medium"


def test_people_and_ratings_are_read_from_claim_passages():
    """Foxglove's detail is empty; the pet flag's citation carries NC State's
    Problems list, and the edibility citation carries RHS's people line."""
    evidence = tx.read_evidence(None, [
        P("toxic_to_pets", True, "Problems: Poisonous to Humans Problem for "
          "Cats Problem for Children Problem for Dogs"),
        P("is_edible", False, "TOXIC if eaten.", "Royal Horticultural Society"),
    ])
    assert evidence.people and not evidence.grave
    rated = tx.read_evidence(None, [P("toxicity_detail", "...",
                                      "Poisonous to Humans: Poison Severity: Low")])
    assert rated.people and rated.rating == "low"
    assert rated.rated_by == "NC State Extension"


def test_an_edibility_passage_calling_it_fatal_is_grave():
    evidence = tx.read_evidence(None, [
        P("is_edible", False, "Highly toxic and can be fatal if ingested.")])
    assert evidence.people and evidence.grave
    text = tx.describe(tx.from_legacy(True, "Colchicum autumnale",
                                      evidence=evidence), "Autumn Crocus")
    # Grave for people; the pets' half is what their flag says.
    assert text.startswith("⚠️ Seriously toxic to people, and toxic to pets.")


def test_harm_to_an_animal_in_an_edibility_passage_is_not_harm_to_people():
    evidence = tx.read_evidence(None, [
        P("is_edible", False, "The foliage is toxic to horses and livestock.")])
    assert not evidence.people


def test_the_pet_flags_citation_is_about_pets_unless_it_names_people():
    evidence = tx.read_evidence(None, [
        P("toxic_to_pets", True,
          "Major Toxicity: May result in serious illness or death if ingested.",
          "UGA Cooperative Extension")])
    assert not evidence.people and not evidence.grave


# --- the short caution and the candidate rule --------------------------------

def test_hazard_line_says_who_in_a_few_words():
    assert tx.hazard_line(tx.from_legacy(True, "Ficus lyrata")) == "Toxic to pets."
    people = tx.read_evidence("NC State rates poison severity Low.")
    assert tx.hazard_line(tx.from_legacy(True, "Ficus lyrata", evidence=people)) \
        == "Toxic to pets and people."
    assert tx.hazard_line(tx.from_legacy(True, "Lilium longiflorum")) \
        == "Seriously toxic to cats."
    # No record is no line -- not a line saying it is safe.
    assert tx.hazard_line(tx.from_legacy(None, "Ficus lyrata")) is None
    assert tx.hazard_line(tx.from_legacy(False, "Ficus lyrata",
                                         cited_to="NC State Extension")) is None


def test_never_put_forward_a_high_severity_poison_or_a_noxious_weed():
    high = tx.read_evidence(POISON_IVY_DETAIL)
    assert tx.never_put_forward(
        tx.from_legacy(False, "Toxicodendron radicans", "NC State Extension", high),
        high)
    grave = tx.read_evidence(None, [P("is_edible", False,
                                      "HIGHLY TOXIC, MAY BE FATAL IF EATEN!")])
    assert tx.never_put_forward(tx.from_legacy(True, "Conium maculatum",
                                               evidence=grave), grave)
    weed = tx.read_evidence("Missouri Botanical Garden notes it is listed as a "
                            "noxious weed in one or more Midwestern states.")
    assert tx.never_put_forward(tx.from_legacy(None, "Pyrus calleryana",
                                               evidence=weed), weed)
    medium = tx.read_evidence("NC State rates poison severity Medium.")
    assert not tx.never_put_forward(
        tx.from_legacy(True, "Epipremnum aureum", evidence=medium), medium)


# --- food crops: the eaten part first ----------------------------------------
#
# NC State rates these five a high-severity poison for people. The sentence
# leads with what is eaten, so the warning about the foliage is never read as
# a warning about dinner, and the edibility note names the same parts.

EGGPLANT_PASSAGES = [
    P("is_edible", True, "The fruits and seeds are edible; however, the "
      "remainder of the plant is poisonous . The fruits should not be consumed raw."),
    P("toxic_to_pets", True, "Problems: Problem for Cats, Problem for Children, "
      "Problem for Dogs, Problem for Horses. Poisonous to Humans: Poison "
      "Severity: High. Poison Symptoms: If the leaves, flowers, stems, or roots "
      "are ingested, throat burning, nausea, vomiting, and irregular heart "
      "rhythm can occur which may be fatal."),
]


def _crop(name, flag, passages, detail=None):
    evidence = tx.read_evidence(detail, passages)
    return tx.from_legacy(flag, name, "NC State Extension", evidence), evidence


@pytest.mark.parametrize("name", [
    "Solanum tuberosum", "Solanum melongena", "Arachis hypogaea",
    "Physalis philadelphica", "Phaseolus lunatus",
    "Solanum lycopersicum", "Rheum rhabarbarum",
])
def test_the_crop_table_names_the_eaten_part(name):
    assert tx.is_food_crop(name)
    assert tx.lookup(name).edible_parts


@pytest.mark.parametrize("name", ["Podophyllum peltatum", "Colocasia esculenta",
                                  "Wisteria floribunda", "Ficus lyrata", ""])
def test_a_plant_merely_recorded_as_eaten_is_not_a_crop(name):
    assert not tx.is_food_crop(name)


def test_eggplant_leads_with_the_fruit():
    tox, evidence = _crop("Solanum melongena", True, EGGPLANT_PASSAGES)
    text = tx.describe(tox, "Eggplant")
    assert text.startswith(
        "⚠️ The fruit is the crop; the leaves and stems, the flowers and the "
        "roots are seriously toxic to people, and toxic to cats and dogs (solanine).")
    assert tx.edibility_note(True, tox, evidence) == (
        "The fruit is eaten; the leaves and stems, the flowers and the roots "
        "are not. Check the source for how it is prepared.")


def test_tomatos_people_sentence_is_about_the_foliage_not_the_fruit():
    """"It is also poisonous to people", right after "the ripe fruit is
    eaten", read as if the fruit were the poison."""
    tox, evidence = _crop("Solanum lycopersicum", True, [
        P("is_edible", True, "The fruits or berries of the tomato are edible. "
          "They may be eaten raw, cooked, dried, or processed.")],
        detail="NC State lists the poison parts as leaves and stems, severity Medium.")
    text = tx.describe(tox, "Tomatoes")
    assert "It is also" not in text
    assert ("The leaves and stems are also toxic to people: NC State Extension "
            "rates the plant's poison severity medium.") in text
    note = tx.edibility_note(True, tox, evidence)
    assert note == "The ripe fruit is eaten; the leaves and stems are not."
    assert "pets" not in note and "Check the source" not in note


def test_peanut_is_the_allergy_its_rating_is_about():
    detail = ("Poisonous to Humans block: Poison Severity: High; Poison "
              "Symptoms: Peanut-allergic reactions; Poison Part: Seeds.")
    tox, evidence = _crop("Arachis hypogaea", None, [
        P("is_edible", True, "The peanut is the most common edible plant part.")],
        detail=detail)
    text = tx.describe(tox, "Peanut")
    assert text.startswith("⚠️ The peanuts are the crop, and they are seriously "
                           "toxic to people with a peanut allergy")
    assert "No verdict on pets is recorded yet" in text
    assert "trimmings" not in text
    assert tx.hazard_line(tox) == "Seriously toxic to people with a peanut allergy."
    assert tx.edibility_note(True, tox, evidence) == \
        "The peanuts are eaten, but not by people with a peanut allergy."


def test_butter_beans_are_eaten_cooked():
    detail = ("Poisonous to Humans block rates Poison Severity High. Toxic, may "
              "be fatal if eaten raw. The raw mature seed is poisonous.")
    tox, evidence = _crop("Phaseolus lunatus", None,
                          [P("is_edible", True, "producing edible beans")], detail)
    assert tx.describe(tox, "Butter Beans").startswith(
        "⚠️ The cooked beans are the crop; the raw mature beans and the roots "
        "are seriously toxic to people (hydrocyanic acid).")
    assert tx.edibility_note(True, tox, evidence) == \
        "The cooked beans are eaten; the raw mature beans and the roots are not."


def test_a_cited_non_toxic_for_pets_leaves_a_crop_a_crop():
    """If a source someday says peanuts are not toxic to pets, the eaten part
    and the people's hazard are still the crop's."""
    detail = "Poisonous to Humans: Poison Severity: High."
    tox = tx.from_legacy(False, "Arachis hypogaea", "Some Extension",
                         tx.read_evidence(detail))
    assert tox.toxic is False and tox.is_crop
    text = tx.describe(tox, "Peanut")
    assert text.startswith("⚠️ The peanuts are the crop")
    assert "Some Extension records no toxicity to pets" in text


def test_a_condition_on_the_eaten_part_is_told_from_one_on_the_rest():
    """Potato's passage says the green parts are inedible: a limit on the
    parts, no condition on the tubers. Eggplant's says not to eat the fruit
    raw: a condition on what is eaten."""
    potato = tx.read_evidence(None, [P("is_edible", True,
        "The plant produces stolon's that bear edible underground tubers. All "
        "green parts of the potato plant are inedible because they contain a "
        "toxin known as solanine.")])
    assert potato.edibility_limited and not potato.edibility_conditional
    eggplant = tx.read_evidence(None, EGGPLANT_PASSAGES)
    assert eggplant.edibility_limited and eggplant.edibility_conditional


def test_an_invasive_species_tag_is_never_put_forward():
    """NC State's Problems field for Chinese wisteria: a cited reason not to
    recommend planting it, the same as a noxious weed."""
    evidence = tx.read_evidence(None, [P(
        "toxic_to_pets", True, "Problems: Invasive Species Problem for Cats "
        "Problem for Dogs Problem for Horses Weedy")])
    assert evidence.invasive
    assert tx.never_put_forward(tx.from_legacy(True, "Wisteria testensis",
                                               evidence=evidence), evidence)
    assert not tx.read_evidence("It is not an invasive species here.").invasive


# --- edibility ---------------------------------------------------------------

def test_edible_and_poisonous_gets_a_note():
    tox = tx.from_legacy(True, "Sambucus nigra")
    note = tx.edibility_note(True, tox, tx.Evidence())
    # Toxic to pets alone is a reason to keep scraps from the dog, not to
    # tell a person to doubt the fruit.
    assert note == ("Some parts are eaten, and it is recorded as poisonous to "
                    "pets, so keep scraps and trimmings away from them.")


@pytest.mark.parametrize("quote", [
    "Mature dried seeds are edible if thoroughly boiled.",
    "Poisonous until cooked. Use salted water and boil for at least one hour.",
    "The seeds can be eaten ONLY once cooked.",
    "Ripe (yellow and soft) fruit is edible raw but in limited quantity.",
    "The beautiful flowers are edible in small amounts.",
])
def test_a_conditional_edibility_passage_gets_a_note(quote):
    evidence = tx.read_evidence(None, [P("is_edible", True, quote)])
    assert evidence.edibility_limited
    assert tx.edibility_note(True, tx.from_legacy(None, "Testus testii"),
                             evidence) is not None


@pytest.mark.parametrize("quote", [
    "Fruit can be eaten raw or cooked and delicious when eaten out of hand.",
    "The fruit is seedy and has a sweet flavor when fully ripened.",
    "Leaves as flavoring and garnish",
    "Nuts are edible.",
])
def test_a_plain_edibility_passage_gets_no_note(quote):
    evidence = tx.read_evidence(None, [P("is_edible", True, quote)])
    assert not evidence.edibility_limited
    assert tx.edibility_note(True, tx.from_legacy(None, "Testus testii"),
                             evidence) is None


def test_a_condition_alone_reads_as_a_condition():
    evidence = tx.read_evidence(None, [P(
        "is_edible", True, "The beautiful flowers are edible in small amounts.")])
    assert tx.edibility_note(True, tx.from_legacy(None, "Viola tricolor"),
                             evidence) == (
        "Some parts are eaten, but only certain parts or after preparation. "
        "Check the source before eating any of it.")


def test_both_conditions_give_the_full_note():
    evidence = tx.read_evidence(None, [P(
        "is_edible", True, "EDIBLE PARTS: Ripe fruit is edible raw but in "
        "limited quantity. CAUTION: The roots, seeds, and leaves are poisonous.")])
    assert evidence.people
    note = tx.edibility_note(True, tx.from_legacy(True, "Podophyllum peltatum",
                                                  evidence=evidence), evidence)
    assert note == ("Some parts are eaten, but only certain parts or after "
                    "preparation, and other parts are poisonous. Check the "
                    "source before eating any of it.")


def test_no_note_unless_it_is_recorded_as_eaten():
    tox = tx.from_legacy(True, "Ficus lyrata")
    assert tx.edibility_note(None, tox, tx.Evidence()) is None
    assert tx.edibility_note(False, tox, tx.Evidence()) is None


def test_the_read_model_carries_the_edibility_note():
    """The contract with the app: `edibility_note` is on SpeciesRead and
    SpeciesDetail, set for an edible plant recorded as poisonous, and null
    otherwise -- the app shows "grown to eat" only then."""
    from app.models.models import Species
    from app.models.schemas import SpeciesDetail, SpeciesRead

    elder = Species(id=1, common_name="Black Elder", scientific_name="Sambucus nigra",
                    toxic_to_pets=True, is_edible=True)
    basil = Species(id=2, common_name="Basil", scientific_name="Ocimum basilicum",
                    toxic_to_pets=None, is_edible=True)
    for schema in (SpeciesRead, SpeciesDetail):
        assert "edibility_note" in schema.model_fields
        assert schema.model_validate(elder).edibility_note.startswith(
            "Some parts are eaten, and it is recorded as poisonous to pets")
        assert schema.model_validate(basil).edibility_note is None


# --- a catalog row reads its own passages -------------------------------------

def _store_claims(session, subject, rows):
    import json as _json

    from sqlmodel import select

    from app.models.models import Authority, Claim
    authority = session.exec(select(Authority).where(
        Authority.name == "NC State Extension")).first()
    if authority is None:
        authority = Authority(name="NC State Extension", tier=2)
        session.add(authority)
        session.flush()
    for field, value, quote in rows:
        session.add(Claim(subject=subject, field=field,
                          value_json=_json.dumps(value), authority_id=authority.id,
                          citation_url=f"https://plants.ces.ncsu.edu/{subject}/{field}/",
                          quote=quote))
    session.flush()


def test_a_stored_row_reads_its_passages_through_its_session(session):
    from app.data.claims.store import forget_safety_passages
    from app.models.models import Species

    sp = Species(common_name="Testfoxglove", scientific_name="Digitalis testii",
                 toxic_to_pets=True, is_edible=False)
    session.add(sp)
    _store_claims(session, "Digitalis testii", [
        ("toxic_to_pets", True, "Problems: Poisonous to Humans Problem for Cats"),
    ])
    forget_safety_passages(session)
    assert sp.toxicity_description.startswith("Toxic to pets and people.")

    # The same row out of a session is described from its columns alone.
    detached = Species(common_name="Testfoxglove", scientific_name="Digitalis testii",
                       toxic_to_pets=True)
    assert detached.toxicity_description.startswith("Toxic to pets.")


def test_new_claims_are_not_hidden_behind_the_cache(session):
    from app.data.claims.ingest import ingest_records
    from app.models.models import Species

    sp = Species(common_name="Cachetest Bean", scientific_name="Lablab cachetestii",
                 is_edible=True)
    session.add(sp)
    session.flush()
    assert sp.edibility_note is None  # fills the cache with nothing for it

    ingest_records(session, [{
        "scientific_name_accepted": "Lablab cachetestii",
        "is_edible": True,
        "citations": [{
            "claim": "is_edible true (Edibility field)",
            "source": "NC State Extension Plant Toolbox",
            "url": "https://plants.ces.ncsu.edu/plants/lablab-cachetestii/",
            "quote": "Mature dried seeds are edible if thoroughly boiled.",
        }],
    }], commit=False)
    assert sp.edibility_note == ("Some parts are eaten, but only certain parts "
                                 "or after preparation. Check the source before "
                                 "eating any of it.")


# --- the named poisons, read from their own records ------------------------

_VERIFIED = Path(__file__).resolve().parents[1] / "app" / "data" / "verified"


def _record(batch: str, name: str) -> dict:
    with open(_VERIFIED / batch, encoding="utf-8") as fh:
        return next(r for r in json.load(fh)["records"]
                    if r.get("scientific_name_accepted") == name)


@pytest.mark.parametrize("batch, name", [
    ("b16-perennials2.json", "Digitalis purpurea"),
    ("b26-toxic-and-more-trees.json", "Taxus baccata"),
    ("b29-mistletoe-and-more.json", "Aconitum napellus"),
    ("b31-avocado-and-more.json", "Datura stramonium"),
])
def test_the_named_poisons_carry_nc_states_high_rating(batch, name):
    """Foxglove, English yew, monkshood and jimsonweed each cite NC State's
    Poisonous to Humans block, and the record reads as a high-severity poison
    to people that no growing area may put forward. An audit once nulled
    these details as human-scoped; this pins them so it cannot happen
    unnoticed again."""
    from app.data.claims.tranche import claims_from_record

    record = _record(batch, name)
    claims, unsupported = claims_from_record(record)
    assert not unsupported
    passages = [P(c.field, c.value, c.quote, c.authority.name) for c in claims
                if c.field in ("toxic_to_pets", "toxicity_detail", "is_edible")]
    evidence = tx.read_evidence(record["toxicity_detail"], passages)
    assert evidence.people
    assert (evidence.rating, evidence.rated_by) == ("high", "NC State Extension")
    tox = tx.from_legacy(record["toxic_to_pets"], name, "NC State Extension", evidence)
    assert tox.severity == "severe"
    assert tx.never_put_forward(tox, evidence)
    block = next(c for c in record["citations"]
                 if c["claim"].startswith("toxicity_detail") and "ncsu.edu" in c["url"])
    assert "Poison Severity: High" in block["quote"]
