"""Fact-checking catalog entries against public-domain horticultural texts.

The two properties that matter most are negative ones: a non-horticultural
"plant book" must never yield a claim, and a book-era name must never attach
its claims to a modern record without resolution. Both are asserted here with
real text from the genres that would otherwise slip through.
"""
import pytest

from app.data.expansion import book_sources as bs, book_verify as bv


# Real-shaped passages from each genre the guard has to separate.
BAILEY_STYLE = (
    "ANTHURIUM. Stove herbs grown for their showy spathes. They require a "
    "compost of rough fibrous peat, sphagnum moss and sharp sand, with perfect "
    "drainage. Water freely during the growing season. Propagation is by "
    "division of the crowns, or by seeds sown in a warm greenhouse. Partial "
    "shade is essential; full exposure scorches the foliage."
)
CULPEPER_STYLE = (
    "It is an herb of Mars, and under the dominion of that planet. Being taken "
    "inwardly it cures the dropsy and openeth obstructions of the liver, and "
    "the decoction is a remedy for the ague."
)
FLORIOGRAPHY_STYLE = (
    "The hyacinth signifies constancy in love, and is the emblem of a faithful "
    "heart. In the language of flowers no bloom speaks more plainly of devotion."
)
VERSE_STYLE = (
    "O'er the green bank where thou didst lie, ere long the fairy flower shall "
    "wake, and thee it calls, and thou shalt hear."
)


def record(**over):
    base = {
        "scientific_name": "Anthurium andraeanum",
        "common_name": "Flamingo Flower",
        "light_need": None,
        "humidity_pct_min": None,
        "humidity_pct_max": None,
        "temp_f_min": None,
        "temp_f_max": None,
        "soil_type": None,
        "toxic_to_pets": None,
        "care_notes": "",
    }
    base.update(over)
    return base


# --- the nonfiction guard ---------------------------------------------------

def test_horticultural_prose_is_admitted():
    s = bs.screen_text(BAILEY_STYLE)
    assert s["usable"] is True
    assert s["markers"] >= bs.MIN_CULTIVATION_MARKERS


@pytest.mark.parametrize("text,genre", [
    (CULPEPER_STYLE, "astrology"),
    (FLORIOGRAPHY_STYLE, "floriography"),
    (VERSE_STYLE, "verse_or_fiction"),
])
def test_non_horticultural_plant_books_are_rejected(text, genre):
    s = bs.screen_text(text)
    assert s["usable"] is False
    assert any(genre in r for r in s["reasons"])


def test_medical_claims_are_disqualifying():
    """A houseplant app repeating a folk cure has made a health claim."""
    s = bs.screen_text(
        "A fine stove plant. Grown in loam and peat with sand. The root, taken "
        "inwardly, is a remedy for fever and heals the stomach."
    )
    assert s["usable"] is False
    assert any("medical_claims" in r for r in s["reasons"])


def test_an_unvetted_source_is_refused_even_if_the_prose_looks_right():
    """Plausible prose from an unknown book is exactly how a herbal slips in."""
    out = bs.screen_source("some-random-herbal", BAILEY_STYLE)
    assert out["usable"] is False
    assert "not on the vetted list" in out["reasons"][0]


def test_vetted_works_are_all_nonfiction_cultivation_references():
    for w in bs.VETTED_WORKS:
        assert w["pd_basis"]
        assert w["authority"] == "high"
        assert w["best_for"]


def test_known_unusable_titles_are_not_in_the_registry():
    titles = {w["title"].lower() for w in bs.VETTED_WORKS}
    for bad in bs.KNOWN_UNUSABLE:
        assert bad["title"].lower() not in titles


# --- claim extraction -------------------------------------------------------

def test_extracts_temperature_regime():
    assert bv.extract_temperature("A stove plant of easy culture.") == (65, 85)
    assert bv.extract_temperature("Thrives in a cool greenhouse.") == (45, 65)
    assert bv.extract_temperature("No temperature is mentioned here.") is None


def test_longer_regime_name_wins():
    """'cool greenhouse' must not be read as the warmer plain 'greenhouse'."""
    assert bv.extract_temperature("Best in a cool greenhouse.") == (45, 65)


def test_extracts_light_and_soil():
    assert bv.extract_light("Partial shade is essential.") == "bright_indirect"
    assert bv.extract_light("Give a sunny position.") == "direct"
    soil = bv.extract_soil("A compost of fibrous peat, sphagnum moss and sharp sand.")
    assert "peat" in soil and "sand" in soil and soil.endswith("-based")


def test_extraction_is_silent_when_the_passage_says_nothing():
    assert bv.extract_claims("A handsome plant, much admired.") == {}


# --- verdicts ---------------------------------------------------------------

def test_unresolved_name_withholds_every_claim():
    """The load-bearing safety gate: 1914 names are often modern synonyms."""
    v = bv.verify_against_book(
        record(), BAILEY_STYLE, "bailey-standard-cyclopedia", name_resolved=False,
    )
    assert v["verdict"] == "uncertain"
    assert v["corrections"] == {}
    assert "not resolved" in v["notes"]


def test_fills_blank_fields_from_a_resolved_record():
    v = bv.verify_against_book(
        record(), BAILEY_STYLE, "bailey-standard-cyclopedia",
        name_resolved=True, citation_url="https://biodiversitylibrary.org/page/1",
    )
    assert v["verdict"] == "corrected"
    c = v["corrections"]
    assert c["temp_f_min"] == 65 and c["temp_f_max"] == 85
    assert c["light_need"] == "bright_indirect"
    assert "peat" in c["soil_type"]
    assert "Bailey" in v["citation_source"]


def test_existing_values_are_never_overwritten():
    rec = record(light_need="low", soil_type="cactus mix", temp_f_min=60, temp_f_max=80)
    v = bv.verify_against_book(
        rec, BAILEY_STYLE, "bailey-standard-cyclopedia", name_resolved=True,
    )
    assert "light_need" not in v["corrections"]
    assert "soil_type" not in v["corrections"]


def test_a_contradiction_is_reported_not_applied():
    """A century-old book disagreeing with a modern record is a question for a
    human — horticultural practice genuinely changed."""
    rec = record(temp_f_min=35, temp_f_max=50)   # no overlap with stove 65-85
    v = bv.verify_against_book(
        rec, BAILEY_STYLE, "bailey-standard-cyclopedia", name_resolved=True,
    )
    assert v["verdict"] == "uncertain"
    assert "no overlap" in v["notes"]
    assert "temp_f_min" not in v["corrections"]


def test_agreement_confirms_without_changing_anything():
    rec = record(temp_f_min=65, temp_f_max=85, light_need="bright_indirect",
                 soil_type="peat, sand, moss-based")
    v = bv.verify_against_book(
        rec, BAILEY_STYLE, "bailey-standard-cyclopedia",
        name_resolved=True, citation_url="https://biodiversitylibrary.org/page/1",
    )
    assert v["verdict"] == "confirmed"
    assert v["corrections"] == {}
    assert "temperature" in v["notes"]


def test_a_rejected_source_yields_no_claim_even_for_a_resolved_name():
    v = bv.verify_against_book(
        record(), CULPEPER_STYLE, "bailey-standard-cyclopedia", name_resolved=True,
    )
    assert v["verdict"] == "uncertain"
    assert v["corrections"] == {}
    assert "source rejected" in v["notes"]


# --- contract ---------------------------------------------------------------

def test_shape_and_stamp_match_apply_review_contract():
    v = bv.verify_against_book(
        record(), BAILEY_STYLE, "bailey-standard-cyclopedia",
        name_resolved=True, citation_url="https://biodiversitylibrary.org/page/1",
    )
    assert set(v) == {
        "verdict", "citation_source", "citation_url",
        "corrections", "notes", "researched_by",
    }
    assert "unverified" in v["researched_by"]


# --- regressions ------------------------------------------------------------

def test_plants_own_regime_beats_an_incidental_propagation_one():
    """Entries name two regimes: the plant's ('Stove herbs') and one for
    propagation ('sown in a warm greenhouse'). The plant's leads the entry."""
    passage = (
        "ANTHURIUM. Stove herbs grown for their spathes. Seeds are sown in a "
        "warm greenhouse in spring."
    )
    assert bv.extract_temperature(passage) == (65, 85)   # stove, not warm greenhouse


def test_soil_is_compared_by_component_not_by_string():
    """Same compost written differently must not read as a disagreement —
    false conflicts are exactly the noise a reviewer can't afford."""
    rec = record(temp_f_min=65, temp_f_max=85, light_need="bright_indirect",
                 soil_type="fibrous peat with sharp sand")
    v = bv.verify_against_book(
        rec, BAILEY_STYLE, "bailey-standard-cyclopedia", name_resolved=True,
        citation_url="https://biodiversitylibrary.org/page/1",
    )
    assert v["verdict"] == "confirmed"
    assert "soil_type" in v["notes"] or "soil" in v["notes"]


def test_genuinely_different_soil_is_still_a_conflict():
    rec = record(temp_f_min=65, temp_f_max=85, light_need="bright_indirect",
                 soil_type="cactus grit mix")
    v = bv.verify_against_book(
        rec, BAILEY_STYLE, "bailey-standard-cyclopedia", name_resolved=True,
    )
    assert v["verdict"] == "uncertain"
    assert "soil_type" in v["notes"]


def test_sphagnum_moss_counts_as_one_component():
    assert bv.soil_components("sphagnum moss and sand") == {"sphagnum", "sand"}


def test_located_works_expose_fetchable_fulltext_urls():
    """The registry has to be actionable, not just descriptive — every located
    volume resolves to a plain-text OCR URL."""
    urls = bs.fulltext_urls("bailey-standard-cyclopedia")
    assert urls, "Bailey has located archive ids"
    assert all(u.startswith("https://archive.org/download/") for u in urls)
    assert all(u.endswith("_djvu.txt") for u in urls)
    assert bs.fulltext_urls("no-such-work") == []
