"""Part-aware toxicity and the sentences generated from it.

The cases here are the ones a boolean gets wrong: plants that are both food and
poison depending on the part, and plants whose risk differs sharply by animal.
"""
import pytest

from app.services import toxicity as tx


# --- the contradictory cases ------------------------------------------------

def test_tomato_leads_with_what_is_edible():
    """'Tomato: toxic' is contradictory to anyone holding a tomato. Confirm the
    reader's experience first, then warn about the part that matters."""
    t = tx.lookup("Solanum lycopersicum")
    assert t.is_contradictory
    text = tx.describe(t, "Tomato")
    assert text.index("eat") < text.index("toxic"), "safe part must come first"
    assert "leaves and stems" in text
    assert "tomatine" in text


def test_rhubarb_distinguishes_stalk_from_leaf():
    t = tx.lookup("Rheum rhabarbarum")
    text = tx.describe(t, "Rhubarb")
    assert "stems" in text and "leaves" in text
    assert t.severity == "severe"


def test_potato_names_the_green_and_sprouted_exception():
    t = tx.lookup("Solanum tuberosum")
    assert "tuber" in t.edible_parts
    assert "solanine" in tx.describe(t, "Potato")


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


def test_aroids_are_flagged_mild_not_alarming():
    """Pothos and a lily must not read the same. Over-warning on the common
    case is what teaches people to ignore the warning on the deadly one."""
    t = tx.lookup("Epipremnum aureum")
    assert t.severity == "mild"
    text = tx.describe(t, "Pothos")
    assert "calcium oxalate" in text
    assert "⚠️" not in text
    assert "Unpleasant rather than dangerous" in text


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
    assert "fruit" in t.edible_parts


def test_legacy_true_without_nuance_stays_conservative():
    t = tx.from_legacy(True, "Ficus lyrata")
    assert t.toxic is True
    assert t.parts == ["all"]


def test_entry_point_renders_for_a_catalog_row():
    text = tx.describe_for_species("Solanum lycopersicum", "Tomato", True)
    assert "You can eat the fruit" in text and "toxic" in text


def test_severe_cases_direct_to_a_vet_and_do_not_triage():
    text = tx.describe_for_species("Lilium longiflorum", "Easter Lily", True)
    assert "contact a vet" in text.lower()
    assert "do not wait" in text.lower()
