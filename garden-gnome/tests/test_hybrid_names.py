"""Hybrid binomials are names like any other, and every gate keys them alike.

A hybrid is written "Genus × epithet" (U+00D7). The catalog landed ten of them
between b4 and b44 and then grew a landing gate that asserted a name splits
into exactly two whitespace tokens, so nine common garden plants -- Chrysanthemum
× morifolium, Nepeta × faassenii, Calibrachoa × hybrida, Verbena × hybrida,
Fuchsia × hybrida, Citrus × aurantiifolia, Spiraea × vanhouttei, Canna ×
generalis, Crocosmia × crocosmiiflora -- were dropped before research.

Two things are pinned here. First, the rules in app/data/claims/names.py: the
three spellings of one marker are one name, the marker never hides a bare genus,
and an ordinary binomial is untouched. Second, that the four gates which decide
whether two names are the same plant -- the pre-landing dedup (covered.py), the
commit gate (test_tranche_invariants), the sync that mints rows, and the
expansion admit path -- all answer with the same key. They used to hold four
private copies of the rule, and two of them disagreed.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

from app.data.claims import names
from app.data.claims.sync import binomial_key
from app.data.expansion.validate import _name_key
from tests.test_tranche_invariants import _binomial

ROOT = Path(__file__).resolve().parents[1]

#: The nine the old "bare binomial" rule dropped, in the spelling the catalog stores.
DROPPED_NINE = [
    "Chrysanthemum × morifolium", "Nepeta × faassenii", "Calibrachoa × hybrida",
    "Verbena × hybrida", "Fuchsia × hybrida", "Citrus × aurantiifolia",
    "Spiraea × vanhouttei", "Canna × generalis", "Crocosmia × crocosmiiflora",
]


def _covered():
    spec = importlib.util.spec_from_file_location(
        "covered", ROOT / "scripts" / "catalog" / "covered.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["covered"] = module
    spec.loader.exec_module(module)
    return module


# --- what a name is --------------------------------------------------------

@pytest.mark.parametrize("spelling", [
    "Nepeta × faassenii",   # the form this catalog stores
    "Nepeta ×faassenii",    # the form several sources print
    "Nepeta x faassenii",   # the ASCII form, already in the corpus (b37, b42)
    "Nepeta  X  faassenii",
])
def test_every_spelling_of_one_hybrid_is_one_name(spelling):
    assert names.key(spelling) == "nepeta x faassenii"
    assert names.canonical("Nepeta ×faassenii") == "Nepeta × faassenii"


@pytest.mark.parametrize("name,expected", [
    ("Dracaena trifasciata", "dracaena trifasciata"),
    ("  Dracaena   trifasciata ", "dracaena trifasciata"),
    ("Solanum xanti", "solanum xanti"),              # a real epithet, not a marker
    ("Xanthosoma sagittifolium", "xanthosoma sagittifolium"),
    ("Adiantum pedatum L.", "adiantum pedatum l."),
    (None, ""),
])
def test_an_ordinary_name_is_keyed_exactly_as_before(name, expected):
    assert names.key(name) == expected


def test_the_marker_is_a_token_and_never_merges_two_taxa():
    # A nothospecies and a same-epithet species are different names. Folding
    # the marker away would be a guess about which plant the evidence
    # describes, and that is the one thing this catalog never guesses at.
    assert names.key("Citrus × aurantiifolia") != names.key("Citrus aurantiifolia")


@pytest.mark.parametrize("name,words", [
    ("Chrysanthemum × morifolium", ["Chrysanthemum", "morifolium"]),
    ("Chrysanthemum ×morifolium", ["Chrysanthemum", "morifolium"]),
    ("x Cuprocyparis leylandii", ["Cuprocyparis", "leylandii"]),  # a nothogenus, b42
    ("Dracaena trifasciata", ["Dracaena", "trifasciata"]),
    ("Adiantum pedatum L.", ["Adiantum", "pedatum", "L."]),
    ("Alocasia × mortfontanensis 'Polly'",
     ["Alocasia", "mortfontanensis", "'Polly'"]),
    ("× Fatshedera", ["Fatshedera"]),                             # still a bare genus
])
def test_the_marker_is_set_aside_when_a_name_is_counted(name, words):
    assert names.words(name) == words


@pytest.mark.parametrize("name,genus", [
    ("Clematis × jackmanii", "Clematis"),
    ("Dracaena trifasciata", "Dracaena"),
    ("× Fatshedera lizei", "Fatshedera"),
    ("x Cuprocyparis leylandii", "Cuprocyparis"),
    ("", ""),
])
def test_the_marker_is_never_read_as_the_genus(name, genus):
    assert names.genus_token(name) == genus


# --- the gates agree -------------------------------------------------------

@pytest.mark.parametrize("name", DROPPED_NINE + [
    "Nepeta ×faassenii", "Abelia x grandiflora", "Dracaena trifasciata",
    "Citrus aurantiifolia", "x Cuprocyparis leylandii",
])
def test_every_gate_keys_a_name_the_same_way(name):
    """covered.py gates landing, the invariants gate the commit, the sync mints
    the row and validate admits an expansion record. A name they key differently
    is a batch that passes one gate and fails the next -- or a duplicate row."""
    covered = _covered()
    assert names.key(name) == binomial_key(name) == _binomial(name)
    assert names.key(name) == covered.norm(name) == _name_key(name)


def test_the_pre_landing_dedup_catches_a_hybrid_already_in_the_corpus():
    covered = _covered()
    landed = covered.covered()
    # Abelia × grandiflora is landed (b42) as "Abelia x grandiflora" given,
    # "Abelia × grandiflora" accepted. All three spellings must find it.
    for spelling in ("Abelia × grandiflora", "Abelia ×grandiflora",
                     "Abelia x grandiflora"):
        assert covered.key(spelling) in landed, spelling
    for name in DROPPED_NINE:
        assert covered.key(name) not in landed, name


def test_the_dedup_key_still_strips_a_cultivar_tail_from_a_hybrid():
    covered = _covered()
    assert covered.key("Alocasia × amazonica 'Polly'") == "alocasia x amazonica"
    assert covered.key("Nepeta × faassenii 'Walker's Low'") == "nepeta x faassenii"
