"""Splitting a scanned horticultural dictionary into per-plant entries.

The hard part is OCR noise, not structure: running heads repeat on every page
in the same capitals as a real heading, and words hyphenate across line breaks.
"""
from app.data.expansion import book_index as bi


# Shaped like real Internet Archive OCR: running heads, page numbers, and a
# word broken across a line.
OCR = """THE STANDARD CYCLOPEDIA OF HORTICULTURE
342

ANTHURIUM (Greek, tail flower). Aracece. Stove herbs grown for
their showy spathes. They need a compost of rough fibrous peat and
sharp sand. Propaga-
tion is by division of the crowns. A. andraeanum is the best known;
A. scherzerianum is dwarfer. Partial shade is essential.

APHELANDRA (Greek, simple sheath). Acanthacece. Stove shrubs of
easy culture in a compost of loam and peat, requiring free watering
during growth. A. squarrosa is the species usually grown in gardens.

THE STANDARD CYCLOPEDIA OF HORTICULTURE
343

ABELE. See Populus.
"""


def test_splits_on_genus_headings():
    entries = bi.split_entries(OCR)
    assert "ANTHURIUM" in entries
    assert "APHELANDRA" in entries


def test_running_heads_are_not_treated_as_entries():
    """'THE STANDARD CYCLOPEDIA...' appears on every page in the same capitals
    as a real heading; treating it as one would shred the entries."""
    entries = bi.split_entries(OCR)
    for noise in ("THE", "STANDARD", "CYCLOPEDIA", "HORTICULTURE"):
        assert noise not in entries


def test_cross_reference_stubs_are_dropped():
    """'ABELE. See Populus.' carries no culture information to verify."""
    assert "ABELE" not in bi.split_entries(OCR)


def test_hyphenation_across_line_breaks_is_repaired():
    entries = bi.split_entries(OCR)
    assert "propagation" in entries["ANTHURIUM"].lower()
    assert "propaga- tion" not in entries["ANTHURIUM"].lower()


def test_entry_text_is_preserved_for_verification():
    entry = bi.split_entries(OCR)["ANTHURIUM"]
    assert "stove" in entry.lower()
    assert "peat" in entry.lower()
    assert "partial shade" in entry.lower()


# --- species extraction -----------------------------------------------------

def test_expands_abbreviated_binomials_using_the_heading():
    """Dictionaries abbreviate the genus after first mention: 'A. andraeanum'."""
    entries = bi.split_entries(OCR)
    species = bi.species_in_entry("ANTHURIUM", entries["ANTHURIUM"])
    assert "Anthurium andraeanum" in species
    assert "Anthurium scherzerianum" in species


def test_does_not_invent_species_from_ordinary_prose():
    species = bi.species_in_entry("ANTHURIUM", "They are grown for the showy spathes.")
    for bogus in ("Anthurium are", "Anthurium the", "Anthurium grown"):
        assert bogus not in species


def test_index_volume_returns_records_ready_to_verify():
    records = bi.index_volume(OCR)
    by_genus = {r["genus"]: r for r in records}
    assert "Anthurium" in by_genus
    rec = by_genus["Anthurium"]
    assert rec["heading"] == "ANTHURIUM"
    assert "Anthurium andraeanum" in rec["species"]
    assert rec["text"]


def test_empty_input_is_safe():
    assert bi.split_entries("") == {}
    assert bi.index_volume("") == []


def test_sentence_prose_is_never_harvested_as_a_species():
    """Regression: 'Stove herbs', 'Water freely' and 'Partial shade' all match
    the shape of a binomial. Harvesting them would fabricate species."""
    entry = (
        "Stove herbs grown for their spathes. They require peat. Water freely "
        "during growth. Partial shade is essential. A. andraeanum is best known."
    )
    species = bi.species_in_entry("ANTHURIUM", entry)
    assert species == ["Anthurium andraeanum"]
    for fake in ("Stove herbs", "They require", "Water freely", "Partial shade"):
        assert fake not in species


def test_other_genera_are_cross_references_not_species_of_this_entry():
    entry = (
        "A. andraeanum is the best known. Compare Philodendron scandens, which "
        "is often confused with it."
    )
    species = bi.species_in_entry("ANTHURIUM", entry)
    assert species == ["Anthurium andraeanum"]
    assert "Philodendron scandens" not in species
