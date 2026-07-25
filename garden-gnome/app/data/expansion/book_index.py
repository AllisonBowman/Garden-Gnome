"""Split a scanned horticultural dictionary into entries keyed by plant name.

Internet Archive serves each volume as one undifferentiated OCR blob
(`{id}_djvu.txt`, often 5-15 MB). Bailey and Nicholson are both alphabetical
dictionaries, so the structure is recoverable: an entry begins with its genus
name set in capitals at the start of a line, and runs until the next one.

    ANTHURIUM (Greek, tail flower). Aracece. Stove herbs grown for...
    APHELANDRA (Greek, simple sheath). Acanthacece. Stove shrubs...

What makes this messy is OCR, not structure:

  * Running heads repeat the book's title and the page's first/last entry on
    every page, in the same capitals as a real heading.
  * Page numbers and plate captions interleave with the text.
  * Words hyphenate across line breaks ("propaga-\\ntion").
  * Old typography reads as noise: long-s, "Aracece" for "Araceae", stray
    punctuation.

So headings are recognized structurally and then filtered against the things
that merely look like headings. Everything here is pure and offline — the
fetching is the caller's problem.
"""
from __future__ import annotations

import re

# A heading: capitals at line start, optionally hyphenated or accented, at
# least three characters so initials and stray caps don't qualify.
_HEADING = re.compile(r"^([A-Z][A-Z\-'ÆŒ]{2,})(?=[\s.,(]|$)")

# Words that appear in capitals but are never a plant entry. Running heads are
# the big one: they repeat on every page and would otherwise shred entries.
_NOT_HEADINGS = {
    "THE", "AND", "FOR", "WITH", "PLATE", "FIG", "VOL", "PART", "INDEX",
    "CONTENTS", "PREFACE", "APPENDIX", "CHAPTER", "SEE", "ALSO", "END",
    "STANDARD", "CYCLOPEDIA", "CYCLOPAEDIA", "HORTICULTURE", "DICTIONARY",
    "GARDENING", "ILLUSTRATED", "ENCYCLOPEDIA", "AMERICAN", "GENERAL",
    "COPYRIGHT", "PUBLISHED", "MACMILLAN", "COMPANY", "LONDON", "YORK",
}

# An entry this short is a cross-reference stub ("ABELE. See Populus."), not a
# description worth fact-checking against.
MIN_ENTRY_CHARS = 120


def dehyphenate(text: str) -> str:
    """Rejoin words split across a line break by typesetting."""
    return re.sub(r"([a-z])-\n([a-z])", r"\1\2", text)


def looks_like_heading(word: str) -> bool:
    return word not in _NOT_HEADINGS and not word.isdigit() and len(word) >= 3


def split_entries(raw_text: str) -> dict[str, str]:
    """Break a volume's OCR into {GENUS: entry text}.

    Later occurrences of a heading are appended rather than replacing earlier
    ones — a genus can be interrupted by a page break and resume, and dropping
    the tail would silently lose the culture notes that usually sit at the end
    of an entry."""
    text = dehyphenate(raw_text or "")
    entries: dict[str, list[str]] = {}
    current: str | None = None
    buffer: list[str] = []

    for line in text.splitlines():
        m = _HEADING.match(line.strip())
        if m and looks_like_heading(m.group(1)):
            if current:
                entries.setdefault(current, []).append("\n".join(buffer))
            current = m.group(1)
            buffer = [line.strip()]
        elif current:
            buffer.append(line.strip())

    if current:
        entries.setdefault(current, []).append("\n".join(buffer))

    merged = {k: " ".join(v).strip() for k, v in entries.items()}
    return {k: v for k, v in merged.items() if len(v) >= MIN_ENTRY_CHARS}


# --- species within an entry ------------------------------------------------

# "A. andraeanum" — genus abbreviated to an initial, the dictionary convention.
_ABBREVIATED = re.compile(r"\b([A-Z])\.\s+([a-z][a-z\-]{2,})\b")
# "Anthurium andraeanum" written out in full.
_FULL_BINOMIAL = re.compile(r"\b([A-Z][a-z]{2,})\s+([a-z][a-z\-]{2,})\b")

# Latin words that follow a capitalized word without forming a binomial.
_NOT_EPITHETS = {
    "and", "the", "with", "from", "for", "see", "also", "var", "syn", "sub",
    "is", "are", "was", "has", "have", "this", "that", "these", "those",
    "genus", "species", "family", "plant", "plants", "leaves", "flowers",
    "native", "grown", "cult", "cultivated", "figs", "fig",
}


def species_in_entry(heading: str, entry: str) -> list[str]:
    """Binomials an entry names, expanded to full scientific names.

    Only species of THIS entry's genus are returned, and that restriction is
    load-bearing rather than tidiness. Any capitalized word followed by a
    lowercase one looks like a binomial — "Stove herbs", "Water freely",
    "Partial shade" all match the shape — so accepting arbitrary genera
    fabricates species out of ordinary sentence-initial prose. An entry headed
    ANTHURIUM describes Anthurium; a mention of another genus is a
    cross-reference, not a species this entry documents."""
    genus = heading.capitalize()
    found: list[str] = []

    def add(epithet: str) -> None:
        if epithet in _NOT_EPITHETS:
            return
        name = f"{genus} {epithet}"
        if name not in found:
            found.append(name)

    # "A. andraeanum" — the dictionary's own abbreviation, unambiguous.
    for initial, epithet in _ABBREVIATED.findall(entry):
        if initial.upper() == genus[0].upper():
            add(epithet)

    # "Anthurium andraeanum" written out — accepted only for this genus.
    for g, epithet in _FULL_BINOMIAL.findall(entry):
        if g.lower() == genus.lower():
            add(epithet)

    return found


def index_volume(raw_text: str) -> list[dict]:
    """Everything the splitter can offer a volume: one record per entry, with
    the species it names and the text a verifier can read."""
    out = []
    for heading, entry in split_entries(raw_text).items():
        out.append({
            "heading": heading,
            "genus": heading.capitalize(),
            "species": species_in_entry(heading, entry),
            "text": entry,
        })
    return out
