"""The landing tools in scripts/catalog/ stay runnable from the repo.

They were rebuilt once already after a session scratchpad vanished; a smoke
test is cheaper than a second rebuild. Only what would silently break is
pinned: the dedup key, and that the corpus is found from the script's own
location rather than a hard-coded path.
"""
import ast
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "catalog"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_the_dedup_key_strips_cultivar_and_infraspecific_tails():
    covered = _load("covered")
    assert covered.key("Alocasia × amazonica 'Polly'") == "alocasia x amazonica"
    assert covered.key("Brassica oleracea var. capitata") == "brassica oleracea"
    assert covered.key("  Dracaena   trifasciata ") == "dracaena trifasciata"


def test_covered_finds_the_landed_corpus_from_its_own_location():
    covered = _load("covered")
    assert covered.VERIFIED == ROOT / "app" / "data" / "verified"
    names = covered.covered()
    # b1-b18 alone covered the 129-species curated catalog.
    assert len(names) > 129
    assert "dracaena trifasciata" in names


# --- the landing gate (scripts/catalog/pipeline/repair_lib.py) -------------

PIPELINE = SCRIPTS / "pipeline"

NCSU = "https://plants.ces.ncsu.edu/plants/nepeta-x-faassenii/"


def _repair_lib():
    spec = importlib.util.spec_from_file_location(
        "repair_lib", PIPELINE / "repair_lib.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["repair_lib"] = module
    spec.loader.exec_module(module)
    return module


def landing_record(given, accepted=None, common="Faassen's Catmint"):
    """The smallest record generic_passes will look at: every non-null field cited."""
    return {
        "common_name": common,
        "scientific_name_given": given,
        "scientific_name_accepted": accepted,
        "is_houseplant": False,
        "humidity_need": "average",
        "unknowns": [],
        "citations": [{
            "claim": ("common_name, scientific_name_accepted, is_houseplant "
                      "and humidity_need"),
            "source": "NC State Extension Gardener Plant Toolbox",
            "url": NCSU, "quote": "the passage that supports it",
        }],
    }


HYBRIDS = [
    "Chrysanthemum × morifolium", "Nepeta × faassenii", "Calibrachoa × hybrida",
    "Verbena × hybrida", "Fuchsia × hybrida", "Citrus × aurantiifolia",
    "Spiraea × vanhouttei", "Canna × generalis", "Crocosmia × crocosmiiflora",
]


def test_the_landing_gate_accepts_a_hybrid_binomial():
    """The assert that dropped nine garden plants. "Genus × epithet" is a
    binomial carrying a marker, not a three-word name."""
    repair_lib = _repair_lib()
    records = [landing_record(name, common=f"Test Plant {i}")
               for i, name in enumerate(HYBRIDS)]
    repair_lib.generic_passes(records)
    assert [r["scientific_name_given"] for r in records] == HYBRIDS


def test_the_landing_gate_normalises_the_spaceless_hybrid_spelling():
    # Sources print both; the corpus keeps one, decided here, at the earliest
    # point every landed record passes through.
    repair_lib = _repair_lib()
    records = [landing_record("Nepeta ×faassenii", accepted="Nepeta ×faassenii")]
    repair_lib.generic_passes(records)
    assert records[0]["scientific_name_given"] == "Nepeta × faassenii"
    assert records[0]["scientific_name_accepted"] == "Nepeta × faassenii"


def test_the_landing_gate_leaves_an_ordinary_binomial_exactly_as_it_was():
    repair_lib = _repair_lib()
    records = [landing_record("Nepeta cataria", accepted="Nepeta cataria",
                              common="Catnip")]
    repair_lib.generic_passes(records)
    assert records[0]["scientific_name_given"] == "Nepeta cataria"
    assert records[0]["scientific_name_accepted"] == "Nepeta cataria"


@pytest.mark.parametrize("given", [
    "Adiantum pedatum L.",                  # authorship, not part of the name
    "Alocasia × amazonica 'Polly'",         # cultivar tail
    "Nepeta",                               # a bare genus is not a species
    "× Fatshedera",                         # nor is a bare nothogenus
    "Nepeta faassenii subsp. faassenii",
])
def test_the_landing_gate_still_refuses_what_it_was_written_for(given):
    repair_lib = _repair_lib()
    with pytest.raises(AssertionError):
        repair_lib.generic_passes([landing_record(given)])


@pytest.mark.parametrize("accepted", [
    "Nepeta × Faassenii",                   # the epithet is still lower-case
    "Nepeta × faassenii 'Walker's Low'",    # still no cultivar tail
    "Nepeta faassenii L.",
])
def test_the_landing_gate_still_polices_the_accepted_name(accepted):
    repair_lib = _repair_lib()
    with pytest.raises(AssertionError):
        repair_lib.generic_passes(
            [landing_record("Nepeta × faassenii", accepted=accepted)])


# --- the stalled-run harvester (pipeline/harvest.py) -----------------------

def _harvest_species_regex():
    """harvest.py is a script that works on import (it walks sys.argv), so the
    one expression under test is lifted out of its source rather than run."""
    tree = ast.parse((PIPELINE / "harvest.py").read_text())
    patterns = [ast.literal_eval(node.args[0]) for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and getattr(node.func, "attr", "") == "search"]
    assert len(patterns) == 1
    return re.compile(patterns[0], re.S)


@pytest.mark.parametrize("latin", [
    "Nepeta faassenii", "Nepeta × faassenii", "Nepeta ×faassenii",
    "Nepeta x faassenii", "Rosa rugosa-alba",
])
def test_an_audit_verdict_is_keyed_to_its_species_however_the_name_is_spelled(latin):
    """No match meant no cached audit: the species is silently dropped from the
    batch as unverified and the Opus auditor is paid for twice."""
    head = ('You are an adversarial auditor reviewing a researched plant-care '
            f'record for "Catmint" ({latin}) before it is landed')
    assert _harvest_species_regex().search(head).group(1) == latin


def test_the_species_capture_stops_at_the_first_parenthetical():
    # A greedier capture could key one species' findings onto another.
    head = ('reviewing a researched plant-care record for "X" (Nepeta faassenii)'
            ' ... (Salvia nemorosa)')
    assert _harvest_species_regex().search(head).group(1) == "Nepeta faassenii"


# --- the prompts that choose and research a species ------------------------

FIXED_NOTE_SENTENCE = (
    "Confirm taxon-specific content on the dedicated page for this exact name, "
    "never a genus-level, cultivar-only, or multi-species page; for a hybrid "
    "this means the hybrid's own page, never a parent species' page.")


def test_the_candidate_finder_no_longer_drops_a_hybrid():
    """The nine were dropped by prose, not by Python: fixing the landing gate
    alone would leave nothing to propose them again."""
    finders = (PIPELINE / "gap-finders.js").read_text()
    assert "not a bare two-word binomial" not in finders
    assert "drop any 'x ' or '×' hybrid marker from the slug" not in finders
    # The NC State slug keeps the marker as an 'x' segment; stripping it 404s.
    assert "nepeta-x-faassenii" in finders
    assert "U+00D7 MULTIPLICATION SIGN" in finders


def test_the_research_prompt_keeps_the_marker_and_still_refuses_a_cultivar_page():
    research = (PIPELINE / "template-research.js").read_text()
    assert "A scientific name is the bare binomial." not in research
    assert "never replace the hybrid with one of its parent species" in research
    assert 'NEVER refute a name merely for carrying "×"' in research
    assert "never re-file it as a cultivar of a parent" in research
    # and the cultivar-page refusal the hybrid wording must not have loosened
    assert "never a name the page assigns to a sibling species" in research


def test_the_restored_hybrids_are_in_the_candidate_pool():
    """Rule: the nine go back where step 2 (gen_batch.py) will pick them up."""
    pool = json.loads((PIPELINE / "batches-b89-hybrids.json").read_text())
    latins = [s["latin"] for b in pool for s in b["species"]]
    assert latins == HYBRIDS
    for batch in pool:
        for species in batch["species"]:
            # gen_batch.py copies the note verbatim into the research prompt.
            assert species["note"].endswith(FIXED_NOTE_SENTENCE), species["latin"]
