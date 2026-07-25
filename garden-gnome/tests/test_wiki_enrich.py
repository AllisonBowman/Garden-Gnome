"""Wikipedia catalog triage.

The decision surface (derive_verdict) is pure, so every case is testable with
no network and no database. These tests pin the safety properties that matter:
duplicates are rejected rather than silently corrected, toxicity only ever moves
in the safe direction, and anything unverified stays 'uncertain'.
"""
import pytest

from app.data.expansion import wiki_enrich as we


def record(**over):
    base = {
        "common_name": "Flamingo Flower",
        "scientific_name": "Anthurium andraeanum",
        "light_need": "bright_indirect",
        "humidity_pct_min": 50,
        "humidity_pct_max": 70,
        "temp_f_min": 60,
        "temp_f_max": 85,
        "soil_type": "peat-based",
        "toxic_to_pets": False,
        "care_notes": "",
    }
    base.update(over)
    return base


def page(title, extract="", redirected_from=None, disambiguation=False):
    return {
        "title": title,
        "extract": extract,
        "url": we.article_url(title),
        "redirected_from": redirected_from,
        "is_disambiguation": disambiguation,
    }


# --- pure helpers -----------------------------------------------------------

@pytest.mark.parametrize("name,ok", [
    ("Anthurium andraeanum", True),
    ("Epipremnum aureum", True),
    ("Ficus elastica var. decora", True),
    ("Anthurium", False),                      # genus only
    ("List of Anthurium species", False),
    ("Monstera 'Thai Constellation'", False),  # cultivar string
    ("", False),
])
def test_looks_like_binomial(name, ok):
    assert we.looks_like_binomial(name) is ok


@pytest.mark.parametrize("text,toxic", [
    ("The plant is toxic to cats and dogs if chewed.", True),
    ("All parts are poisonous to pets.", True),
    ("The sap is toxic if ingested.", True),
    ("Contains calcium oxalate crystals which cause irritation.", True),
    ("A popular houseplant native to Colombia with glossy leaves.", False),
    ("It is grown for its toxic-looking red spathe.", False),  # no ingestion/animal context
    ("", False),
])
def test_detect_toxicity_requires_an_explicit_statement(text, toxic):
    assert we.detect_toxicity(text) is toxic


# --- verdicts ---------------------------------------------------------------

def test_missing_article_is_uncertain_not_a_rejection():
    """A name Wikipedia doesn't know is unverified, NOT proof it isn't real."""
    v = we.derive_verdict(record(), {"missing": True}, set())
    assert v["verdict"] == "uncertain"
    assert v["corrections"] == {}


def test_disambiguation_page_is_uncertain():
    v = we.derive_verdict(record(), page("Anthurium", disambiguation=True), set())
    assert v["verdict"] == "uncertain"


def test_synonym_duplicating_an_existing_row_is_rejected():
    """The identification fix: two rows for one plant is what makes ID ambiguous."""
    rec = record(scientific_name="Anthurium scherzerianum x")
    wiki = page("Anthurium andraeanum", redirected_from="Anthurium scherzerianum x")
    v = we.derive_verdict(rec, wiki, {"anthurium andraeanum"})
    assert v["verdict"] == "rejected"
    assert "same plant" in v["notes"]
    assert v["citation_url"].startswith("https://en.wikipedia.org/wiki/")


def test_synonym_with_no_existing_row_corrects_the_name():
    rec = record(scientific_name="Anthurium scherzerianum x")
    wiki = page("Anthurium andraeanum", redirected_from="Anthurium scherzerianum x")
    v = we.derive_verdict(rec, wiki, set())          # no other row holds it
    assert v["verdict"] == "corrected"
    assert v["corrections"] == {"scientific_name": "Anthurium andraeanum"}


def test_redirect_to_a_non_species_page_is_uncertain():
    """Never 'correct' a species name to a genus or a list article."""
    rec = record(scientific_name="Anthurium sp.")
    wiki = page("Anthurium", redirected_from="Anthurium sp.")
    v = we.derive_verdict(rec, wiki, set())
    assert v["verdict"] == "uncertain"
    assert v["corrections"] == {}


def test_toxicity_is_added_when_stated_and_record_says_pet_safe():
    wiki = page("Anthurium andraeanum", extract="All parts are toxic to cats and dogs.")
    v = we.derive_verdict(record(toxic_to_pets=False), wiki, set())
    assert v["verdict"] == "corrected"
    assert v["corrections"] == {"toxic_to_pets": True}


def test_toxicity_is_never_cleared_by_silence():
    """Absence of a toxicity mention must NOT downgrade a toxic record to safe —
    that would be an unsafe inference about a pet-safety field."""
    wiki = page("Anthurium andraeanum", extract="A popular houseplant with glossy leaves.")
    v = we.derive_verdict(record(toxic_to_pets=True), wiki, set())
    assert v["verdict"] == "uncertain"
    assert "toxic_to_pets" not in v["corrections"]


def test_matching_title_does_not_confirm_care_data():
    """Wikipedia proves the species exists; it says nothing about watering.
    Claiming 'confirmed' here would launder an unverified record."""
    wiki = page("Anthurium andraeanum", extract="A species of flowering plant.")
    v = we.derive_verdict(record(), wiki, set())
    assert v["verdict"] == "uncertain"
    assert "care data" in v["notes"] or "care numbers" in v["notes"] or "still need" in v["notes"]


# --- contract with apply_review ---------------------------------------------

def test_every_verdict_is_stamped_machine_drafted():
    for wiki in [{"missing": True}, page("Anthurium andraeanum")]:
        v = we.derive_verdict(record(), wiki, set())
        assert "unverified" in v["researched_by"]
        assert "wikipedia" in v["researched_by"].lower()


def test_verdict_shape_matches_apply_review_contract():
    v = we.derive_verdict(record(), page("Anthurium andraeanum"), set())
    assert set(v) == {
        "verdict", "citation_source", "citation_url",
        "corrections", "notes", "researched_by",
    }
    assert v["verdict"] in {"confirmed", "corrected", "rejected", "uncertain"}


def test_corrections_outside_the_allowed_fields_are_stripped():
    """Inherited from research_review.sanitize — pinned here so a future edit to
    this module can't quietly widen what it may write."""
    out = we.sanitize({
        "verdict": "corrected",
        "citation_url": "https://en.wikipedia.org/wiki/Anthurium_andraeanum",
        "citation_source": "Wikipedia",
        "corrections": {"scientific_name": "Anthurium andraeanum", "id": 99, "user_id": "x"},
    })
    assert set(out["corrections"]) == {"scientific_name"}


def test_a_verdict_without_a_citation_is_downgraded():
    out = we.sanitize({"verdict": "corrected", "corrections": {"soil_type": "peat"}})
    assert out["verdict"] == "uncertain"
