"""The landing tools in scripts/catalog/ stay runnable from the repo.

They were rebuilt once already after a session scratchpad vanished; a smoke
test is cheaper than a second rebuild. Only what would silently break is
pinned: the dedup key, and that the corpus is found from the script's own
location rather than a hard-coded path.
"""
import importlib.util
import sys
from pathlib import Path

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
