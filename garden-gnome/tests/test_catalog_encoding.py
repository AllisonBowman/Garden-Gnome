"""No catalog text under app/data was mis-decoded on its way into a file.

species_catalog.json carried 25 em dashes reading "â€”" from the first commit:
UTF-8 bytes decoded once as Windows-1252 and saved again as UTF-8. Dumb Cane's
care notes showed it in the app. Nothing between a data file and the screen
can catch that -- seed.py and the claim sync copy a string onto its column as
it is, and since ADR 0010 every boot carries the curated file's prose onto
the rows already seeded, a garbled string as faithfully as a mended one. So
it is caught here, over every catalog data file, before it lands.

The pattern is the shape mis-decoding leaves, not a list of the characters
seen so far: the cp1252 reading of a UTF-8 lead byte for punctuation (â) or
for a Latin-1 letter or symbol (Ã, Â), followed by what a continuation byte
reads as, or by a plain space where a mangled no-break space was tidied; and
U+FFFD, which a lossy decode leaves where it gave up. Strings are checked
after parsing, so an escaped "\\u00e2\\u20ac" is caught as surely as the
literal characters.
"""
import json
import re
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "app" / "data"

# Scratch output from the offline expansion tools: git-ignored, local to one
# machine, and never read by the seed or the sync.
SCRATCH = DATA / "expansion" / "output"


def _as_cp1252(byte: int) -> str:
    # The five bytes cp1252 leaves undefined come through as their Latin-1
    # control characters, which is what a lenient decoder writes.
    try:
        return bytes([byte]).decode("cp1252")
    except UnicodeDecodeError:
        return chr(byte)


CONTINUATION = "".join(_as_cp1252(b) for b in range(0x80, 0xC0))
MOJIBAKE = re.compile(f"[âÃÂ][{re.escape(CONTINUATION)}]|[ÃÂ] |�")


def _mangle(text: str) -> str:
    """What a UTF-8 string reads as when its bytes are taken for cp1252."""
    return "".join(_as_cp1252(b) if b >= 0x80 else chr(b) for b in text.encode("utf-8"))


def _data_files():
    for path in sorted(DATA.rglob("*.json")):
        if SCRATCH not in path.parents:
            yield path


def _strings(node, where=""):
    """Every string in a parsed document, keys included, with where it sits."""
    if isinstance(node, str):
        yield where, node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield from _strings(key, f"{where}/{key} (key)")
            yield from _strings(value, f"{where}/{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _strings(value, f"{where}/{i}")


@pytest.mark.parametrize("text", [
    "Wear gloves — sap is an irritant.",
    "Brown tips – too-dry air.",
    "Don’t overwater; “bright” means no direct sun.",
    "Café au lait",
    "Keep above 55°F; ½ strength feed.",
    "Abelia × grandiflora",
    "Water sparingly.",
])
def test_the_check_sees_what_mis_decoding_does_to_a_sentence(text):
    assert MOJIBAKE.search(_mangle(text)), _mangle(text)
    assert not MOJIBAKE.search(text), text


def test_the_check_sees_a_tidied_no_break_space_and_a_lossy_decode():
    assert MOJIBAKE.search("WaterÂ sparingly.")
    assert MOJIBAKE.search("Water � sparingly.")


@pytest.mark.parametrize("text", [
    "Sold as “Rosé”.",
    "naïve, façade, São Paulo",
    "Nepeta × faassenii",
])
def test_accented_letters_beside_punctuation_are_not_flagged(text):
    assert not MOJIBAKE.search(text), text


def test_the_curated_catalog_is_among_the_files_checked():
    assert DATA / "species_catalog.json" in set(_data_files())


@pytest.mark.parametrize("path", list(_data_files()),
                         ids=lambda p: str(p.relative_to(DATA)))
def test_no_catalog_text_was_mis_decoded(path):
    document = json.loads(path.read_text(encoding="utf-8"))
    found = [f"{where}: ...{text[max(0, m.start() - 30):m.end() + 30]}..."
             for where, text in _strings(document)
             for m in MOJIBAKE.finditer(text)]
    assert not found, (
        f"{len(found)} mis-decoded sequence(s) in {path.relative_to(DATA)}:\n"
        + "\n".join(found[:20]))
