"""Ground a vision model's free-text answer in the species catalog.

Python port of mobile/src/photoId/fuzzyMatch.ts. **That file is the reference
implementation** — the scoring, the thresholds, and the tie-handling here must
stay byte-for-byte equivalent in behaviour, so the same photo grounds the same
way whether it was identified on-device or on the server. Change one, change
both, and keep PARITY_FIXTURES in sync.

Why free-text matching rather than a candidate list: the catalog is ~1,940
species. Listing every candidate in the prompt costs ~20k tokens per request
(~$0.04) and asks the model to scan a long flat list — a harder task than
simply naming the plant, which vision models do well from pretraining. So the
model names the plant openly and this module decides whether that name
corresponds to a record we actually hold.

The model's raw text is NEVER authoritative. It is a query into records with
real care data, and a weak match yields no species rather than a wrong one.

Identity is the SCIENTIFIC name. Per the expansion policy recorded in
app/data/expansion/admit_queue.py (2026-07-09), common names legitimately
collide across the catalog ("Anthurium" names several records), so a common-name
hit alone is weaker evidence than a binomial hit.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.models import Species

# Confidence tiers — must match fuzzyMatch.ts.
CONFIDENT = 0.6   # good enough to pre-select the species
PLAUSIBLE = 0.42  # offer as a pickable candidate, never auto-trusted

# Review states whose care data a human has actually checked.
REVIEWED_STATES = {"approved", "verified"}

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_QUOTES = re.compile(r"['’`]")


def normalize(s: str) -> str:
    return _NON_ALNUM.sub(" ", _QUOTES.sub("", (s or "").lower())).strip()


def _bigrams(s: str) -> dict[str, int]:
    t = re.sub(r"\s+", " ", s)
    out: dict[str, int] = {}
    for i in range(len(t) - 1):
        bg = t[i:i + 2]
        out[bg] = out.get(bg, 0) + 1
    return out


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
    """True when every token of `name` appears in `text` (order-independent)."""
    words = {w for w in text.split(" ") if w}
    tokens = [t for t in name.split(" ") if t]
    return bool(tokens) and all(t in words for t in tokens)


def score_name(ai_text: str, name: str) -> float:
    """Score how well the model's answer matches one candidate name.

    The model usually answers in prose ("This looks like a Monstera deliciosa,
    commonly called the Swiss cheese plant"), so whole-name containment is the
    strongest signal; character-level Dice catches typos and inflections."""
    a, b = normalize(ai_text), normalize(name)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if len(b) >= 4 and _contains_all_tokens(a, b):
        # Longer, more specific names (binomials) are stronger evidence.
        return 0.97 if " " in b else 0.82
    return dice_coefficient(a, b)


@dataclass
class ScoredSpecies:
    species: Species
    score: float
    matched_on: str  # "scientific" | "common"

    @property
    def reviewed(self) -> bool:
        return (self.species.review_status or "") in REVIEWED_STATES


def match_species(ai_text: str, catalog: list[Species]) -> list[ScoredSpecies]:
    """Rank the catalog against the model's answer, best first.

    Ties break toward records a human has reviewed: with ~87% of the catalog
    still needs_review, a scientifically equivalent match against checked care
    data is the better one to surface."""
    scored: list[ScoredSpecies] = []
    for sp in catalog:
        sci = score_name(ai_text, sp.scientific_name)
        com = score_name(ai_text, sp.common_name)
        best = max(sci, com)
        if best > 0:
            scored.append(ScoredSpecies(
                species=sp,
                score=best,
                matched_on="scientific" if sci >= com else "common",
            ))

    # Sort: score desc, then reviewed first, then binomial hits over common-name
    # hits (scientific names are the catalog's identity), then stable by id.
    scored.sort(key=lambda s: (
        -s.score,
        not s.reviewed,
        s.matched_on != "scientific",
        s.species.id or 0,
    ))
    return scored


@dataclass
class MatchResult:
    tier: str  # "confident" | "plausible" | "none"
    candidates: list[ScoredSpecies]


def classify_matches(scored: list[ScoredSpecies]) -> MatchResult:
    """Turn ranked matches into a decision: a confident hit, a few plausible
    options, or nothing worth showing."""
    if not scored or scored[0].score < PLAUSIBLE:
        return MatchResult(tier="none", candidates=[])
    best = scored[0]
    if best.score >= CONFIDENT:
        # Include near-ties so the obvious pick leads but alternatives show.
        near = [s for s in scored if s.score >= best.score - 0.12][:3]
        return MatchResult(tier="confident", candidates=near)
    return MatchResult(
        tier="plausible",
        candidates=[s for s in scored if s.score >= PLAUSIBLE][:4],
    )


# Shared expectations for the TS/Python parity test. Each entry is
# (model_answer, candidate_name, expected_score) computed by score_name.
# A jest test asserting the same numbers keeps the two implementations honest.
PARITY_FIXTURES = [
    ("Monstera deliciosa", "Monstera deliciosa", 1.0),
    ("This looks like a Monstera deliciosa to me", "Monstera deliciosa", 0.97),
    ("Looks like a Pothos", "Pothos", 0.82),
    # An unrelated name scores low but not zero — bigram noise. The value is
    # what matters: well under PLAUSIBLE, so it never reaches the user.
    ("Snake Plant", "Dracaena trifasciata", 0.06896551724137931),
]
