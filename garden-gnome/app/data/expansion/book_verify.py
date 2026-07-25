"""Fact-check catalog entries against vetted public-domain horticultural texts.

For each species a book discusses, compare what the book says to what the
catalog holds, and draft a verdict. Same contract as every other pass: it writes
nothing to the catalog, a human reads the file first.

THREE GATES, IN ORDER — a claim must pass all of them:

  1. Source admission. The work must be on the vetted allowlist AND the passage
     must read as cultivation writing (book_sources.screen_source). This keeps
     astrological herbals, floriography, and verse out.
  2. Name resolution. These books predate a century of reclassification, so a
     name in Bailey (1914) is frequently a synonym today. Attaching its culture
     notes to the wrong modern record is precisely the failure the catalog work
     exists to fix, so an unresolved name is refused outright — not merely
     warned about.
  3. Claim extraction. Only unambiguous statements are read. Victorian prose is
     discursive; anything that needs interpretation is left as `uncertain`
     rather than guessed at.

HISTORICAL TEMPERATURE REGIMES

Nineteenth-century horticulture names temperature bands rather than numbers,
and those names are well defined by convention:

    stove / hothouse        65-85 F
    intermediate / warm     55-75 F
    cool house / greenhouse 45-65 F

They are approximate by nature, so they are used only to detect a CLEAR
contradiction (no overlap at all with the record) — never to nudge a number a
few degrees.
"""
from __future__ import annotations

import re

from app.data.expansion.book_sources import screen_source, resolve_required
from app.data.expansion.research_review import sanitize as _sanitize

RESEARCHED_BY = "public-domain horticultural text (unverified — needs human review)"

# name -> (min_f, max_f). Approximate by construction; see module docstring.
TEMPERATURE_REGIMES = {
    "stove": (65, 85),
    "hothouse": (65, 85),
    "hot-house": (65, 85),
    "intermediate house": (55, 75),
    "warm greenhouse": (55, 75),
    "cool house": (45, 65),
    "cool greenhouse": (45, 65),
    "greenhouse": (45, 65),
}

_REGIME_NAMES = list(TEMPERATURE_REGIMES)

LIGHT_PHRASES = [
    (r"\bdeep shade\b|\bfull shade\b", "low"),
    (r"\bpartial shade\b|\bhalf shade\b|\bdappled\b", "bright_indirect"),
    (r"\bfull sun\b|\bfull exposure to the sun\b|\bsunny position\b", "direct"),
    (r"\bshade\b|\bshady\b", "low"),
]

SOIL_COMPONENTS = ["loam", "peat", "sand", "leaf-mould", "leaf mould", "moss", "sphagnum"]


def sanitize(review: dict) -> dict:
    out = _sanitize(review)
    out["researched_by"] = RESEARCHED_BY
    return out


# --- claim extraction (pure) ------------------------------------------------

def extract_temperature(text: str) -> tuple[int, int] | None:
    """The temperature band a passage places the plant in, or None.

    A single entry often names more than one regime — the plant's own ("stove
    herbs grown for their spathes") and an incidental one for propagation
    ("seeds sown in a warm greenhouse"). These texts lead with the plant's
    classification, so the EARLIEST regime is the plant's; later mentions
    belong to whatever else the sentence is about. Ties go to the longest
    match, so "cool greenhouse" is never read as the warmer plain
    "greenhouse" sitting inside it."""
    low = (text or "").lower()
    best: tuple[int, int, str] | None = None  # (start, -length, name)
    for name in _REGIME_NAMES:
        m = re.search(rf"\b{re.escape(name)}\b", low)
        if m:
            candidate = (m.start(), -len(name), name)
            if best is None or candidate < best:
                best = candidate
    return TEMPERATURE_REGIMES[best[2]] if best else None


def extract_light(text: str) -> str | None:
    """A light_need value, or None when the passage doesn't clearly say."""
    low = (text or "").lower()
    for pattern, value in LIGHT_PHRASES:
        if re.search(pattern, low):
            return value
    return None


def soil_components(text: str) -> set[str]:
    """The compost components named in a piece of text.

    Used for BOTH extraction and comparison: comparing soil as an exact string
    makes 'peat, sand, moss-based' and 'peat, sand, moss, sphagnum-based' look
    like a disagreement, which would bury a reviewer in false conflicts."""
    low = (text or "").lower()
    found: set[str] = set()
    for comp in SOIL_COMPONENTS:
        if re.search(rf"\b{re.escape(comp)}\b", low):
            found.add(comp.replace("leaf mould", "leaf-mould"))
    # "sphagnum moss" is one component, not two.
    if "sphagnum" in found:
        found.discard("moss")
    return found


def extract_soil(text: str) -> str | None:
    """A soil description built from the compost components named.

    These texts are precise about compost, which is exactly the field the
    expansion mapper defaulted."""
    found = soil_components(text)
    if not found:
        return None
    ordered = [c for c in SOIL_COMPONENTS if c.replace("leaf mould", "leaf-mould") in found]
    return ", ".join(dict.fromkeys(c.replace("leaf mould", "leaf-mould") for c in ordered)) + "-based"


def extract_claims(text: str) -> dict:
    """Every claim the passage supports, conservatively."""
    claims: dict = {}
    temp = extract_temperature(text)
    if temp:
        claims["temp_f_min"], claims["temp_f_max"] = temp
    light = extract_light(text)
    if light:
        claims["light_need"] = light
    soil = extract_soil(text)
    if soil:
        claims["soil_type"] = soil
    return claims


def _ranges_conflict(a_min, a_max, b_min, b_max) -> bool:
    """True when two temperature ranges do not overlap at all."""
    if None in (a_min, a_max, b_min, b_max):
        return False
    return a_max < b_min or b_max < a_min


def _is_blank(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


# --- the verdict ------------------------------------------------------------

def verify_against_book(
    record: dict,
    passage: str,
    work_id: str,
    *,
    name_resolved: bool,
    citation_url: str = "",
) -> dict:
    """Fact-check one catalog record against one book passage.

    `name_resolved` must be True: the caller asserts this record's scientific
    name was mapped to the modern accepted name (GBIF/WFO) before the book's
    claims were associated with it. Pure — no network, no DB."""
    name = (record.get("scientific_name") or "").strip()

    # Gate 1 — is this a usable nonfiction horticultural source?
    screened = screen_source(work_id, passage)
    if not screened["usable"]:
        return sanitize({
            "verdict": "uncertain",
            "notes": (
                f"source rejected for {name!r}: {'; '.join(screened['reasons'])}. "
                f"No claim was read from it."
            ),
        })
    work = screened["work"]

    # Gate 2 — a book-era name must be resolved before its claims may land.
    if resolve_required(name) and not name_resolved:
        return sanitize({
            "verdict": "uncertain",
            "notes": (
                f"{work['title']} ({work['year']}) predates a century of "
                f"reclassification and {name!r} was not resolved to a modern "
                f"accepted name. Claims withheld — attaching them now risks "
                f"filing them against the wrong species."
            ),
        })

    # Gate 3 — what does the passage actually support?
    claims = extract_claims(passage)
    if not claims:
        return sanitize({
            "verdict": "uncertain",
            "citation_source": f"{work['author']}, {work['title']} ({work['year']})",
            "citation_url": citation_url,
            "notes": f"passage discusses {name!r} but states no extractable culture facts.",
        })

    citation = f"{work['author']}, {work['title']} ({work['year']})"
    conflicts: list[str] = []
    corrections: dict = {}
    agreements: list[str] = []

    # Temperature: only a total non-overlap counts as a contradiction, since
    # the historical bands are approximate.
    if "temp_f_min" in claims:
        b_min, b_max = claims["temp_f_min"], claims["temp_f_max"]
        r_min, r_max = record.get("temp_f_min"), record.get("temp_f_max")
        if _is_blank(r_min) or _is_blank(r_max):
            corrections["temp_f_min"], corrections["temp_f_max"] = b_min, b_max
        elif _ranges_conflict(r_min, r_max, b_min, b_max):
            conflicts.append(
                f"temperature: catalog {r_min}-{r_max}F vs book {b_min}-{b_max}F (no overlap)"
            )
        else:
            agreements.append("temperature")

    if "light_need" in claims:
        current = record.get("light_need")
        if _is_blank(current):
            corrections["light_need"] = claims["light_need"]
        elif str(current).strip().lower() == claims["light_need"]:
            agreements.append("light_need")
        else:
            conflicts.append(f"light_need: catalog {current!r} vs book {claims['light_need']!r}")

    # Soil is compared by component, not by string: the same compost is written
    # a dozen ways, and exact-matching it would manufacture disagreements.
    if "soil_type" in claims:
        current = record.get("soil_type")
        if _is_blank(current):
            corrections["soil_type"] = claims["soil_type"]
        else:
            book_parts = soil_components(claims["soil_type"])
            rec_parts = soil_components(str(current))
            if rec_parts & book_parts:
                agreements.append("soil_type")
            else:
                conflicts.append(f"soil_type: catalog {current!r} vs book {claims['soil_type']!r}")

    # A contradiction is reported, never auto-applied. A century-old book
    # disagreeing with a modern record is a question for a human, not a fix:
    # horticultural practice genuinely changed.
    if conflicts:
        return sanitize({
            "verdict": "uncertain",
            "citation_source": citation,
            "citation_url": citation_url,
            "corrections": corrections,
            "notes": (
                f"Book disagrees with the catalog — needs a human: "
                f"{'; '.join(conflicts)}. Practice has changed since "
                f"{work['year']}, so the book is not automatically right."
            ),
        })

    if corrections:
        return sanitize({
            "verdict": "corrected",
            "citation_source": citation,
            "citation_url": citation_url,
            "corrections": corrections,
            "notes": (
                f"Filled from {work['title']}: {', '.join(sorted(corrections))}. "
                f"Fields already holding values were left alone."
                + (f" Agrees with the catalog on {', '.join(agreements)}." if agreements else "")
            ),
        })

    return sanitize({
        "verdict": "confirmed",
        "citation_source": citation,
        "citation_url": citation_url,
        "notes": (
            f"Catalog agrees with {work['title']} on {', '.join(agreements)}. "
            f"Nothing to change."
        ),
    })
