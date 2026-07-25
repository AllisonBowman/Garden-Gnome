"""Vetted public-domain horticultural texts, and the guard that keeps the
unusable ones out.

WHY A GUARD AT ALL

The public domain is full of plant books that would poison a care database.
They are *about plants*, they are old enough to be free, and their text looks
superficially like horticulture:

  * Culpeper's Complete Herbal (1653) — astrological medicine. "This herb is
    under the dominion of Mars." Reads like plant advice; is not.
  * "The Language of Flowers" genre — floriography. Tells you a hyacinth
    signifies constancy, not what compost it wants.
  * Victorian flower poetry and devotional works — verse about plants.
  * Folk herbals generally — medicinal claims ("cures dropsy") which must NEVER
    reach care_notes. A houseplant app that tells someone a plant cures an
    illness has made a health claim, which is both false and unsafe.

So a text is admitted only if it shows positive evidence of cultivation
writing AND no strong disqualifying signal. Silence is not evidence — an
unrecognized book is rejected, not admitted.

PUBLIC DOMAIN BASIS

Works published in the US before 1929 are public domain there, as are US
government works of any date. Both bases are recorded per entry. Public domain
carries no share-alike obligation, so unlike the Wikipedia path these texts may
be quoted into care_notes with attribution.

TAXONOMY WARNING

These books predate a century of reclassification. A name in Bailey (1914) is
frequently a synonym today, and attaching its culture notes to the wrong modern
record is exactly the failure this catalog work exists to fix. Every book claim
must pass name resolution BEFORE it reaches a record — see resolve_required.
"""
from __future__ import annotations

import re

# --- the registry -----------------------------------------------------------
# Curated deliberately. This is an allowlist, not a search: a text earns a place
# here by being a cultivation reference, and the guard below is the second gate
# rather than the first.

VETTED_WORKS = [
    {
        "id": "bailey-standard-cyclopedia",
        "title": "The Standard Cyclopedia of Horticulture",
        "author": "Liberty Hyde Bailey",
        "year": 1914,
        "volumes": 6,
        "pd_basis": "US publication pre-1929",
        "authority": "high",
        "scope": (
            "Cultivated plants of North America. Broad houseplant coverage "
            "(Aspidistra, Ficus, Philodendron, Anthurium, Sansevieria, palms, "
            "ferns, Begonia) with culture, compost, temperature regime, and "
            "propagation per entry."
        ),
        "best_for": ["soil_type", "light_need", "temp_f_min", "temp_f_max"],
        # Located 2026-07-25. Internet Archive item ids; OCR text is at
        # https://archive.org/download/{id}/{id}_djvu.txt
        "archive_ids": ["standardcycloped01bail", "standardcycloped05bailrich",
                        "standardcycloped030104mbp"],
        "bhl": "https://www.biodiversitylibrary.org/bibliography/23351",
        "note": (
            "Volume ids beyond those listed follow the same pattern but were "
            "not individually confirmed — check before fetching."
        ),
    },
    {
        "id": "nicholson-illustrated-dictionary",
        "title": "The Illustrated Dictionary of Gardening",
        "author": "George Nicholson",
        "year": 1884,
        "volumes": 4,
        "pd_basis": "UK publication pre-1929",
        "authority": "high",
        "scope": (
            "British horticultural dictionary, unusually strong on stove and "
            "greenhouse plants — i.e. the tropicals now grown indoors. Good "
            "independent cross-check against Bailey."
        ),
        "best_for": ["soil_type", "light_need", "temp_f_min", "temp_f_max"],
        "archive_ids": ["illustrateddicti01nich", "illustrateddicti03nichiala",
                        "mobot31753000409331", "cu31924051991812"],
        "bhl": "https://www.biodiversitylibrary.org/bibliography/21232",
    },
    {
        "id": "usda-house-plants",
        "title": "USDA Home and Garden Bulletins / Farmers' Bulletins",
        "author": "United States Department of Agriculture",
        "year": 0,  # ongoing series; PD by authorship, not by age
        "volumes": 0,
        "pd_basis": "US government work — public domain regardless of date",
        "authority": "high",
        "scope": (
            "Modern names and modern units, which the Victorian references "
            "lack — no idiom translation needed. Notably HGB 82, 'Selecting "
            "and growing house plants' (1979). Thin on tropical houseplants "
            "overall, but what it covers is directly usable."
        ),
        "best_for": ["temp_f_min", "temp_f_max", "toxic_to_pets"],
        "archive_ids": [],
        "index": "https://pubs.nal.usda.gov/sites/pubs.nal.usda.gov/files/hgb.htm",
    },
]

# Internet Archive serves OCR text for any item at this path. It is the
# cheapest way to get a whole volume as plain text — no API key, no scraping.
IA_FULLTEXT = "https://archive.org/download/{id}/{id}_djvu.txt"


def fulltext_urls(work_id: str) -> list[str]:
    """Plain-text OCR URLs for every located volume of a vetted work."""
    work = work_by_id(work_id)
    if not work:
        return []
    return [IA_FULLTEXT.format(id=i) for i in work.get("archive_ids", [])]

# Recorded so the reasoning is not lost, and so tests can assert they stay out.
KNOWN_UNUSABLE = [
    {"title": "The Complete Herbal", "author": "Nicholas Culpeper", "year": 1653,
     "reason": "astrological medicine, not horticulture"},
    {"title": "The Language of Flowers", "author": "various", "year": 1884,
     "reason": "floriography — symbolism, no cultivation content"},
    {"title": "Flower Fables", "author": "Louisa May Alcott", "year": 1854,
     "reason": "fiction"},
]

# --- the guard --------------------------------------------------------------

# Any hit disqualifies: these mark a genre that cannot yield care facts.
DISQUALIFYING = {
    "astrology": [
        r"under the (?:dominion|government) of",
        r"governed by (?:saturn|mars|venus|jupiter|mercury|the moon|the sun)",
        r"\bplanetary (?:influence|virtue)",
        r"\b(?:choleric|phlegmatic|sanguine|melancholic)\b",
        r"\bhumou?rs? of the body\b",
    ],
    "floriography": [
        r"language of flowers",
        r"\bsignifies\b.{0,30}\b(?:love|constancy|devotion|friendship)\b",
        r"\bemblem of\b",
        r"\bfloral (?:sentiment|emblem)\b",
    ],
    "medical_claims": [
        r"\bcures?\b.{0,40}\b(?:disease|ailment|dropsy|ague|fever|consumption)\b",
        r"\bremedy for\b",
        r"\bmedicinal virtues\b",
        r"\btaken inwardly\b",
        r"\bheals? the\b",
    ],
    "verse_or_fiction": [
        r"\bthee\b.{0,40}\bthou\b",
        r"\bo'er\b|\b'tis\b|\bere long\b",
        r"\bonce upon a time\b",
        r"\bfairy\b.{0,30}\bflower\b",
    ],
}

# Evidence that this is cultivation writing. A text must show several.
CULTIVATION_MARKERS = [
    r"\bpropagat", r"\bcompost\b", r"\bloam\b", r"\bpeat\b", r"\bleaf-?mould\b",
    r"\bcutting[s]?\b", r"\bgreenhouse\b", r"\bstove\b", r"\bpotting\b",
    r"\brepot", r"\bseedling", r"\bhardy\b", r"\bglasshouse\b",
    r"\bwater(?:ed|ing)? freely\b", r"\bpartial shade\b", r"\bwell-drained\b",
]

MIN_CULTIVATION_MARKERS = 3


def screen_text(text: str) -> dict:
    """Decide whether a passage is usable horticultural nonfiction.

    Returns {'usable': bool, 'reasons': [...], 'markers': int}. Pure and
    deterministic; no network, no model."""
    low = (text or "").lower()
    reasons: list[str] = []

    for genre, patterns in DISQUALIFYING.items():
        for pat in patterns:
            if re.search(pat, low):
                reasons.append(f"disqualified: {genre}")
                break

    markers = sum(1 for pat in CULTIVATION_MARKERS if re.search(pat, low))
    if markers < MIN_CULTIVATION_MARKERS:
        reasons.append(
            f"insufficient cultivation content ({markers}/{MIN_CULTIVATION_MARKERS} markers)"
        )

    return {"usable": not reasons, "reasons": reasons, "markers": markers}


def work_by_id(work_id: str) -> dict | None:
    return next((w for w in VETTED_WORKS if w["id"] == work_id), None)


def screen_source(work_id: str, text: str) -> dict:
    """Full admission check: the work must be on the allowlist AND the passage
    must read as cultivation writing.

    An unknown work is refused rather than screened on text alone — a plausible
    passage from an unvetted book is exactly how a herbal slips in."""
    work = work_by_id(work_id)
    if work is None:
        return {
            "usable": False,
            "reasons": [f"unknown source {work_id!r} — not on the vetted list"],
            "markers": 0,
            "work": None,
        }
    screened = screen_text(text)
    return {**screened, "work": work}


def resolve_required(name: str) -> bool:
    """Whether a book-era name must be run through modern name resolution
    before its claims may touch a record.

    Always true for these sources. Kept as a function so the call site reads as
    a deliberate check rather than an omission."""
    return True
