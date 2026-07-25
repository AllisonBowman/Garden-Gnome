"""Genus-level care inference.

derive_genus_fill is pure, so every case runs offline. These tests pin the
properties that make the inference safe to apply in bulk: it never overwrites
real data, it never guesses toxicity from a split genus, and it never claims
`confirmed`.
"""
import pytest

from app.data.expansion import genus_fill as gf


def sibling(**over):
    base = {
        "scientific_name": "Anthurium andraeanum",
        "light_need": "bright_indirect",
        "humidity_pct_min": 50,
        "humidity_pct_max": 70,
        "temp_f_min": 60,
        "temp_f_max": 85,
        "soil_type": "peat-based",
        "toxic_to_pets": True,
    }
    base.update(over)
    return base


def target(**over):
    base = {
        "scientific_name": "Anthurium veitchii",
        "common_name": "King Anthurium",
        "light_need": None,
        "humidity_pct_min": None,
        "humidity_pct_max": None,
        "temp_f_min": None,
        "temp_f_max": None,
        "soil_type": None,
        "toxic_to_pets": None,
        "care_notes": "",
        "review_status": "needs_review",
        "review_note": "",
    }
    base.update(over)
    return base


# --- pure helpers -----------------------------------------------------------

@pytest.mark.parametrize("name,genus", [
    ("Anthurium andraeanum", "Anthurium"),
    ("epipremnum aureum", "Epipremnum"),
    ("Ficus", "Ficus"),
    ("", ""),
    (None, ""),
])
def test_genus_of(name, genus):
    assert gf.genus_of(name) == genus


def test_defaulted_fields_from_note():
    assert gf.defaulted_fields_from_note("no soil data — defaulted") == {"soil_type"}
    assert gf.defaulted_fields_from_note("humidity defaulted") == {
        "humidity_pct_min", "humidity_pct_max"}
    # No "default" anywhere means nothing is claimed as a placeholder.
    assert gf.defaulted_fields_from_note("near-duplicate of Anthurium andraeanum") == set()
    assert gf.defaulted_fields_from_note(None) == set()


def test_fillable_only_covers_blank_or_defaulted_fields():
    rec = target(soil_type="loam", humidity_pct_min=40, review_note="no soil data — defaulted")
    fill = gf.fillable_fields(rec)
    assert "soil_type" in fill          # note admits it is a placeholder
    assert "humidity_pct_min" not in fill  # real value, left alone
    assert "temp_f_min" in fill         # blank


def test_genus_envelope_uses_median_and_mode():
    sibs = [
        sibling(humidity_pct_min=40, light_need="low", soil_type="peat-based"),
        sibling(humidity_pct_min=50, light_need="bright_indirect", soil_type="peat-based"),
        sibling(humidity_pct_min=90, light_need="bright_indirect", soil_type="loam"),
    ]
    env = gf.genus_envelope(sibs)
    assert env["humidity_pct_min"] == 50           # median, not dragged by the 90
    assert env["light_need"] == "bright_indirect"  # mode
    assert env["soil_type"] == "peat-based"        # mode


def test_toxicity_inherited_only_on_a_unanimous_genus():
    unanimous = [sibling(toxic_to_pets=True), sibling(toxic_to_pets=True)]
    assert gf.genus_envelope(unanimous)["toxic_to_pets"] is True

    split = [sibling(toxic_to_pets=True), sibling(toxic_to_pets=False)]
    assert "toxic_to_pets" not in gf.genus_envelope(split), (
        "a split genus must not determine a pet-safety field"
    )


# --- verdicts ---------------------------------------------------------------

def test_fills_blank_care_fields_from_approved_siblings():
    v = gf.derive_genus_fill(target(), [sibling(), sibling(scientific_name="Anthurium clarinervium")])
    assert v["verdict"] == "corrected"
    c = v["corrections"]
    assert c["light_need"] == "bright_indirect"
    assert c["humidity_pct_min"] == 50
    assert c["temp_f_max"] == 85
    assert "2 approved" in v["citation_source"]


def test_never_overwrites_existing_care_data():
    rec = target(light_need="low", humidity_pct_min=30, soil_type="cactus mix")
    v = gf.derive_genus_fill(rec, [sibling()])
    for held in ("light_need", "humidity_pct_min", "soil_type"):
        assert held not in v["corrections"], f"{held} already had real data"


def test_no_approved_siblings_is_uncertain():
    v = gf.derive_genus_fill(target(), [])
    assert v["verdict"] == "uncertain"
    assert v["corrections"] == {}
    assert "no human-approved species" in v["notes"]


def test_species_specific_text_is_never_inferred():
    """common_name / scientific_name / care_notes do not generalize by genus."""
    v = gf.derive_genus_fill(target(), [sibling()])
    for f in ("common_name", "scientific_name", "care_notes"):
        assert f not in v["corrections"]


def test_verdict_is_never_confirmed():
    """'confirmed' is reserved for a record checked against a source. Inference
    must not launder itself into verification."""
    v = gf.derive_genus_fill(target(), [sibling()] * 6)
    assert v["verdict"] != "confirmed"
    assert "inference, not verification" in v["notes"]


def test_sibling_count_and_strength_are_disclosed():
    weak = gf.derive_genus_fill(target(), [sibling()])
    strong = gf.derive_genus_fill(target(), [sibling(scientific_name=f"Anthurium s{i}") for i in range(5)])
    assert "weak" in weak["notes"]
    assert "strong" in strong["notes"]


def test_record_with_nothing_missing_is_uncertain_not_corrected():
    full = target(
        light_need="low", humidity_pct_min=30, humidity_pct_max=50,
        temp_f_min=60, temp_f_max=80, soil_type="loam", toxic_to_pets=False,
    )
    v = gf.derive_genus_fill(full, [sibling()])
    assert v["verdict"] == "uncertain"
    assert v["corrections"] == {}


# --- contract ---------------------------------------------------------------

def test_shape_and_stamp_match_apply_review_contract():
    v = gf.derive_genus_fill(target(), [sibling()])
    assert set(v) == {
        "verdict", "citation_source", "citation_url",
        "corrections", "notes", "researched_by",
    }
    assert "unverified" in v["researched_by"]
    assert "genus" in v["researched_by"].lower()


def test_corrections_are_limited_to_correctable_fields():
    for f in gf.derive_genus_fill(target(), [sibling()])["corrections"]:
        assert f in gf.CORRECTABLE
