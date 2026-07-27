"""Weighted review sampling: pull 5-10% of imported records into a manual
review file, weighted toward the most commonly-owned houseplants, for
cross-checking against NC State Extension Plant Toolbox / Missouri Botanical
Garden Plant Finder.
"""
import random
import re

# The usual suspects on every "most popular houseplants" list. Matching
# records get a heavy sampling weight so the manual review effort lands on
# the plants most users actually own.
TOP_HOUSEPLANTS = [
    "pothos", "epipremnum", "monstera", "snake plant", "dracaena trifasciata",
    "sansevieria", "spider plant", "chlorophytum", "peace lily", "spathiphyllum",
    "philodendron", "zz plant", "zamioculcas", "fiddle leaf", "ficus lyrata",
    "aloe vera", "jade", "crassula", "rubber plant", "ficus elastica",
    "boston fern", "nephrolepis", "english ivy", "hedera helix", "pilea",
    "calathea", "goeppertia", "phalaenopsis", "orchid", "african violet",
    "saintpaulia", "streptocarpus", "croton", "codiaeum", "dieffenbachia",
    "dracaena marginata", "schefflera", "hoya", "string of pearls", "senecio",
    "curio rowleyanus", "echeveria", "haworthia", "anthurium", "bird of paradise",
    "strelitzia", "majesty palm", "parlor palm", "chamaedorea", "areca",
    "dypsis", "yucca", "peperomia", "prayer plant", "maranta", "fittonia",
    "nerve plant", "lucky bamboo", "christmas cactus", "schlumbergera",
    "begonia", "tradescantia", "alocasia", "syngonium", "aglaonema",
    "chinese evergreen", "kalanchoe", "oxalis", "bromeliad", "air plant",
    "tillandsia", "cyclamen", "poinsettia", "euphorbia pulcherrima",
]

_norm = lambda s: re.sub(r"\s+", " ", (s or "").lower().strip())  # noqa: E731


def is_top_houseplant(rec: dict) -> bool:
    names = f"{_norm(rec.get('common_name'))} {_norm(rec.get('scientific_name'))}"
    return any(top in names for top in TOP_HOUSEPLANTS)


def weighted_sample(records: list[dict], fraction: float = 0.075, seed: int = 42) -> list[dict]:
    """Sample ~fraction of records, weighted toward common houseplants.

    Every record matching the TOP_HOUSEPLANTS list is included (capped at
    2/3 of the sample budget — they're the plants most users own, so they
    get reviewed first), and the remaining slots are a uniform random draw
    from the long tail."""
    if not records:
        return []
    k = max(1, round(len(records) * fraction))
    rng = random.Random(seed)

    top = [r for r in records if is_top_houseplant(r)]
    tail = [r for r in records if not is_top_houseplant(r)]
    top_budget = min(len(top), max(1, (k * 2) // 3) if len(top) > k else len(top))
    picked = rng.sample(top, top_budget) if len(top) > top_budget else list(top)
    remaining = k - len(picked)
    if remaining > 0 and tail:
        picked += rng.sample(tail, min(remaining, len(tail)))
    return picked


def to_review_entry(rec: dict) -> dict:
    """Wrap a record in the manual-review envelope the reviewer fills in."""
    return {
        "record": rec,
        "review": {
            "verdict": "",  # confirmed | corrected | rejected
            "citation_source": "",  # e.g. "NC State Extension Plant Toolbox"
            "citation_url": "",
            "corrections": {},  # field -> corrected value (only when verdict=corrected)
            "notes": "",
        },
    }
