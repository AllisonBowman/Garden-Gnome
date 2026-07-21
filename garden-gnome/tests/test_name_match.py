"""Grounding a model's free-text plant name in the catalog.

The reference implementation is mobile/src/photoId/fuzzyMatch.ts — these tests
pin the behaviour the Python port has to reproduce, so on-device and server
identification ground the same answer the same way.
"""
import pytest

from app.models.models import LightNeed, Species
from app.services import name_match as nm


def _sp(sid: int, common: str, scientific: str, review_status: str = "approved") -> Species:
    return Species(
        id=sid, common_name=common, scientific_name=scientific,
        light_need=LightNeed.medium, humidity_pct_min=40, humidity_pct_max=60,
        temp_f_min=60, temp_f_max=80, soil_type="mix", review_status=review_status,
    )


@pytest.mark.parametrize("ai_text,name,expected", nm.PARITY_FIXTURES)
def test_score_name_parity_with_typescript(ai_text, name, expected):
    """Shared fixtures with fuzzyMatch.ts. If these drift, the two
    implementations have diverged and the same photo will ground differently
    depending on which path answered."""
    assert nm.score_name(ai_text, name) == pytest.approx(expected)


def test_exact_binomial_is_confident():
    catalog = [_sp(1, "Monstera", "Monstera deliciosa")]
    result = nm.classify_matches(nm.match_species("Monstera deliciosa", catalog))
    assert result.tier == "confident"
    assert result.candidates[0].species.id == 1
    assert result.candidates[0].matched_on == "scientific"


def test_prose_answer_still_matches():
    """Vision models answer in sentences, not bare names."""
    catalog = [_sp(1, "Swiss Cheese Plant", "Monstera deliciosa")]
    scored = nm.match_species(
        "This appears to be a Monstera deliciosa, judging by the split leaves.", catalog
    )
    assert nm.classify_matches(scored).tier == "confident"


def test_unrelated_name_yields_nothing():
    """An out-of-catalog plant must degrade to manual search, not to the
    least-bad row. Bigram noise scores above zero, so the threshold does the
    real work here."""
    catalog = [_sp(1, "Snake Plant", "Dracaena trifasciata")]
    scored = nm.match_species("Ficus lyrata", catalog)
    assert scored[0].score < nm.PLAUSIBLE
    assert nm.classify_matches(scored).tier == "none"


def test_scientific_name_disambiguates_shared_common_names():
    """admit_queue.py policy (2026-07-09): scientific names are the catalog's
    identity because common names legitimately collide -- several records are
    called 'Anthurium'. A binomial answer must resolve to exactly one."""
    catalog = [
        _sp(1, "Anthurium", "Anthurium andraeanum"),
        _sp(2, "Anthurium", "Anthurium clarinervium"),
    ]
    result = nm.classify_matches(nm.match_species("Anthurium clarinervium", catalog))
    assert result.tier == "confident"
    assert result.candidates[0].species.id == 2
    assert result.candidates[0].matched_on == "scientific"


def test_reviewed_records_win_ties():
    """With ~87% of the catalog unreviewed, an equally-good match against care
    data a human checked is the better one to surface."""
    catalog = [
        _sp(1, "Cape Primrose", "Streptocarpus x hybridus", review_status="needs_review"),
        _sp(2, "Cape Primrose", "Streptocarpus x hybridus", review_status="approved"),
    ]
    scored = nm.match_species("Streptocarpus x hybridus", catalog)
    assert scored[0].species.id == 2
    assert scored[0].reviewed is True
    assert scored[1].reviewed is False


def test_genus_only_answer_surfaces_every_sibling():
    """A genus name scores highly against each of its species (long shared
    prefix), so "Spathiphyllum" cannot single out one of several. The near-tie
    window has to surface them all rather than silently pick the first --
    otherwise the user is handed one sibling's care data as if it were settled."""
    catalog = [
        _sp(1, "Peace Lily", "Spathiphyllum wallisii"),
        _sp(2, "Sensation Peace Lily", "Spathiphyllum sensation"),
    ]
    result = nm.classify_matches(nm.match_species("Spathiphyllum", catalog))
    assert {c.species.id for c in result.candidates} == {1, 2}


def test_species_epithet_breaks_the_genus_tie():
    """Given the full binomial, the right sibling must lead."""
    catalog = [
        _sp(1, "Peace Lily", "Spathiphyllum wallisii"),
        _sp(2, "Sensation Peace Lily", "Spathiphyllum sensation"),
    ]
    result = nm.classify_matches(nm.match_species("Spathiphyllum sensation", catalog))
    assert result.candidates[0].species.id == 2


def test_empty_and_garbage_inputs_are_safe():
    catalog = [_sp(1, "Pothos", "Epipremnum aureum")]
    assert nm.match_species("", catalog) == []
    assert nm.classify_matches([]).tier == "none"
    assert nm.score_name("Pothos", "") == 0.0
