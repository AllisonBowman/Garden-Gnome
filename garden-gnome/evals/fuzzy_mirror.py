"""Python mirror of the app's on-device answer-grounding matcher.

AUTHORITATIVE SOURCE: mobile/src/photoId/fuzzyMatch.ts — this file is a
line-for-line port so device results can be re-graded off-device
(evals/replay_device.py). If the TS thresholds or scoring change, change
them here too; PARITY_FIXTURES below is the shared contract a future jest
suite must assert byte-identically.

Species records here are plain dicts: {'id', 'common_name',
'scientific_name'} (see evals/catalog.py).
"""
from __future__ import annotations

import re
from collections import Counter

# Confidence tiers (mirror fuzzyMatch.ts):
CONFIDENT = 0.6   # populate the species field from this match
PLAUSIBLE = 0.42  # offer as a pickable candidate, not auto-trusted

_APOSTROPHES = re.compile(r"[’'`]")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize(s: str) -> str:
    s = _APOSTROPHES.sub("", (s or "").lower())
    return _NON_ALNUM.sub(" ", s).strip()


def _bigrams(s: str) -> Counter:
    t = re.sub(r"\s+", " ", s)
    return Counter(t[i:i + 2] for i in range(len(t) - 1))


def dice_coefficient(a: str, b: str) -> float:
    """Sørensen–Dice coefficient over character bigrams (0..1)."""
    if a == b:
        return 1.0
    if len(a) < 2 or len(b) < 2:
        return 0.0
    A, B = _bigrams(a), _bigrams(b)
    overlap = sum(min(n, B[bg]) for bg, n in A.items() if bg in B)
    return (2 * overlap) / (sum(A.values()) + sum(B.values()))


def _contains_all_tokens(text: str, name: str) -> bool:
    words = set(text.split())
    tokens = name.split()
    return len(tokens) > 0 and all(t in words for t in tokens)


def score_name(ai_text: str, name: str) -> float:
    a, b = normalize(ai_text), normalize(name)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if len(b) >= 4 and _contains_all_tokens(a, b):
        return 0.97 if " " in b else 0.82
    return dice_coefficient(a, b)


def match_species(ai_text: str, species: list[dict]) -> list[dict]:
    """Rank the catalog against the model's answer, best-first.

    Returns [{'species': {...}, 'score': float}, ...]; ties keep catalog
    order (both implementations use a stable sort)."""
    scored = [
        {"species": sp, "score": max(score_name(ai_text, sp["common_name"]),
                                     score_name(ai_text, sp["scientific_name"]))}
        for sp in species
    ]
    return sorted((s for s in scored if s["score"] > 0),
                  key=lambda s: -s["score"])


def classify_matches(scored: list[dict]) -> dict:
    """{'tier': 'confident'|'plausible'|'none', 'candidates': [...best-first]}"""
    best = scored[0] if scored else None
    if not best or best["score"] < PLAUSIBLE:
        return {"tier": "none", "candidates": []}
    if best["score"] >= CONFIDENT:
        near = [s for s in scored if s["score"] >= best["score"] - 0.12][:3]
        return {"tier": "confident", "candidates": near}
    return {"tier": "plausible",
            "candidates": [s for s in scored if s["score"] >= PLAUSIBLE][:4]}


def grade_text(ai_text: str, species: list[dict]) -> dict:
    """One-call helper: raw model text -> tier + candidate common names."""
    result = classify_matches(match_species(ai_text, species))
    return {
        "tier": result["tier"],
        "candidates": [c["species"]["common_name"] for c in result["candidates"]],
    }


# --- Parity contract ------------------------------------------------------
# Small fixed catalog (names mirror real catalog entries) + expected
# outcomes. evals/selftest.py asserts these; a future fuzzyMatch.test.ts
# must assert the identical table.

FIXTURE_CATALOG = [
    {"id": 1, "common_name": "Snake Plant", "scientific_name": "Dracaena trifasciata"},
    {"id": 2, "common_name": "Pothos", "scientific_name": "Epipremnum aureum"},
    {"id": 3, "common_name": "Monstera", "scientific_name": "Monstera deliciosa"},
    {"id": 4, "common_name": "Peace Lily", "scientific_name": "Spathiphyllum wallisii"},
    {"id": 5, "common_name": "Aloe Vera", "scientific_name": "Aloe barbadensis"},
]

# (ai_text, expected_tier, expected_top_common_name or None)
PARITY_FIXTURES = [
    ("Monstera deliciosa", "confident", "Monstera"),
    ("This looks like a snake plant to me.", "confident", "Snake Plant"),
    ("pothos", "confident", "Pothos"),
    ("Peace lily, maybe?", "confident", "Peace Lily"),
    ("aloe", "plausible", "Aloe Vera"),
    ("UNKNOWN", "none", None),
    ("a small orange tabby cat", "none", None),
]
