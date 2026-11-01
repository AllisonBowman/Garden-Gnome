"""Every sentence of a lengthened care note stands on a cited record.

On 2026-10-30 the 33 curated notes that called a plant "Pet-safe", "harmless"
or "safe for most pets" lost the claim, and most of their words went with it
(tests/test_curated_notes.py says why). The notes in PINNED were written back
up from the verified records, one sentence to one citation, and
app/data/curated_note_sources.json holds the trace: each note's sentences in
order, each with the url and the verbatim part of the quote it rests on.

So a lengthened note cannot change without its trace changing with it, and a
trace cannot name a quote the species' own record does not hold. A sentence
with no quote behind it is the kind of prose the file was cleaned of: it has
no citation, and it cannot follow the evidence when the evidence changes.

These notes stand under the hazard sentence and beside the Care facts card,
and they are read on a phone, so they are held to a shape as well: 3 to 6
sentences, 40 to 90 words, one paragraph. They make no safety claim in either
direction, and they stay off the subjects only the hazard sentence speaks to.

A note reaches a database that already exists only through the boot refresh
(ADR 0010), so the last two tests boot on older text and look for the new.
The first reads the ship tip's file out of git and skips on CI's one-commit
checkout. The second builds its own stale file and runs anywhere.
"""
import json
import re
import subprocess
from pathlib import Path

import pytest

from tests.test_curated_notes import CATALOG, claims
from tests.test_curated_text_refresh import REPO, _db_prose, boot  # noqa: F401

VERIFIED = CATALOG.parent / "verified"
SOURCES = CATALOG.parent / "curated_note_sources.json"
#: The ship tip this work was cut from. Its notes are the short ones.
BEFORE = "2ac7b19"
#: A sentence may rest on part of a longer quote only if the part runs this
#: long, so that it cannot be a few words lifted out of their context. A quote
#: the record holds whole is not lifted from anything, so it may be shorter.
MIN_QUOTE_WORDS = 6

#: Subjects a care note leaves to the hazard sentence, or leaves out. The
#: words tests/test_curated_notes.py refuses are refused here too, by claims().
OFF_SUBJECT = re.compile(
    r"\b(?:pets?|cats?|dogs?|child(?:ren)?|kids?|bab(?:y|ies)|animals?"
    r"|livestock|horses?|eat(?:s|en|ing)?|food|medicine|remedy|tea|sweetener"
    r"|cures?)\b",
    re.I)

#: Scientific name -> the exact note species_catalog.json holds. An edit here
#: has to come with the same edit to curated_note_sources.json.
PINNED = {
    "Chlorophytum comosum": (
        "Spider plant grows best in average humidity and moist soil, though it tolerates drought and dry soil. "
        "Check the soil and let it dry out briefly before you water again. "
        "When you pot or repot it, use a general-purpose potting mix."
    ),
    "Goeppertia orbifolia": (
        "You may know this plant by an older name, Calathea orbifolia. "
        "Keep the soil evenly moist, but never wet or soggy. "
        "Give it at least 60% humidity so it can thrive. "
        "Aim for a stable temperature between 65°F and 75°F. "
        "Feed it once a month during the growing season."
    ),
    "Hoya carnosa": (
        "Wax plant is a climber that also suits a hanging basket. "
        "Through the growing season, water moderately and consistently, letting the soil get nearly dry in between. "
        "In winter, the plant needs less water and less bright light. "
        "It loves high humidity, so try a humidifier or set the pot on a tray of wet pebbles. "
        "Use a loose, fast-draining mix rich in organic matter and a pot with good drainage. "
        "Soil kept too wet or too dry can make the leaves drop."
    ),
    "Maranta leuconeura": (
        "Grow prayer plant indoors in bright light, away from strong direct sun. "
        "Too much sun will fade the colors of its leaves. "
        "Keep the soil evenly moist through the growing season, then water less so it dries out in winter. "
        "The plant needs high humidity, so keep it in a humidified room or on a tray of wet pebbles. "
        "Pot it in a soil-based potting mix. "
        "Feed it monthly in the growing season, then feed much less from autumn to late winter."
    ),
    "Pilea peperomioides": (
        "Set your Chinese money plant near a north, east, or west window. "
        "In a south-facing room, set it back from the window so it gets no direct sun. "
        "Keep it out of cold drafts and always above 50°F. "
        "Water when the top few centimeters of soil start drying, checking with a finger or by lifting the pot. "
        "From April to September, you can feed every 1 to 2 months with balanced liquid fertilizer at label strength."
    ),
    "Phalaenopsis spp.": (
        "Moth orchids are grown in pots of a bark-based mix that drains very well. "
        "Water mature plants more often when summer is hot. "
        "Feed with a balanced fertilizer at half strength 2 times a month, or at quarter strength each week. "
        "Spring bloomers with large white flowers need 1 week of autumn nights near 55°F to start flower spikes."
    ),
    "Aspidistra elatior": (
        "Give your cast iron plant bright indirect light where you can, though it copes with full shade. "
        "Keep it out of direct sun. "
        "Water it from spring through fall, then water less in winter while it rests. "
        "It puts up with less than regular watering, and you do not need to raise the humidity. "
        "Grow it in rich soil that drains well."
    ),
    "Nepeta cataria": (
        "This plant can turn weedy, so think about growing it in a container. "
        "It grows in full sun with at least 6 hours of direct sunlight a day. "
        "It also grows in partial shade with 2 to 6 hours of direct sun. "
        "Plant it in any soil that drains well. "
        "It copes if the soil goes dry at times."
    ),
    "Stevia rebaudiana": (
        "Stevia is a white-flowered herb that can be kept as a houseplant. "
        "Give it full sun if possible, though it will tolerate partial shade. "
        "Choose a spot with moderate temperatures and humid air. "
        "Keep it in moist, well-drained soil that is loamy, sandy, rich in organic matter and slightly acidic."
    ),
    "Centaurea cyanus": (
        "Bachelor's button is a cool-weather annual grown in average, well-drained soil. "
        "Plant it in beds, borders, cottage gardens, meadows, or a cutting garden. "
        "Give it full sun to light shade, since too much shade makes the stems flop. "
        "It prefers moderately moist soil but copes with little water. "
        "Avoid spots that stay wet. "
        "It tolerates poor soil and needs little or no fertilizer."
    ),
    "Celosia argentea": (
        "Grow celosia in containers and hanging baskets, on a patio, or indoors as a houseplant. "
        "Give it full sun, at least 6 hours of direct sun a day. "
        "Moist soil suits it, as long as the soil drains well. "
        "Feed it a balanced liquid fertilizer. "
        "Indoors, watch for aphids and spider mites, which you can wash off."
    ),
    "Impatiens walleriana": (
        "Impatiens can be grown as a bedding annual, a container plant, or a houseplant. "
        "Outdoors, give it part to full shade, because too much sun can scorch the leaves. "
        "Plant it in moist, well-drained, slightly acidic soil enriched with organic matter. "
        "It does not tolerate drought well. "
        "Overwatering can make the plant rot."
    ),
    "Tropaeolum majus": (
        "Nasturtium is a warm-season annual with long stems and parasol-like leaves, grown in many kinds of gardens. "
        "Climbing types can quickly cover a fence or trellis. "
        "Choose a spot in full sun, with some afternoon shade when summers run hot. "
        "It tolerates drought. "
        "Plant it in poor, well-drained soil, since overly rich soil brings leaves at the expense of flowers. "
        "Fertilizer also adds leaves but cuts down on flowering."
    ),
    "Viola x wittrockiana": (
        "Pansy is a bedding plant for cool weather. "
        "Set it where it gets full sun to part shade. "
        "Plant it in humus-rich soil that stays evenly moist yet drains well. "
        "Water it thoroughly after planting. "
        "Never let the roots sit in soggy soil."
    ),
    "Petunia x hybrida": (
        "Petunia is grown in beds, border fronts, patio edges, containers, hanging baskets and window boxes. "
        "It can live in heavy shade, but flowering will suffer. "
        "It grows best in well-drained, light soil that is moderately fertile. "
        "Feed it with a balanced fertilizer to support fast growth and heavy blooming."
    ),
    "Salvia splendens": (
        "Annual salvia is a bedding plant. "
        "A spot with morning sun and midafternoon shade suits it. "
        "The soil should drain very well, so use raised beds or work compost into heavy ground. "
        "Water during dry spells. "
        "Pinch back the young shoots to encourage bushier growth."
    ),
    "Zinnia elegans": (
        "Zinnia is an upright flowering annual from Mexico, in the aster family. "
        "Grow it in full sun, with at least 6 hours of direct sunlight each day. "
        "Plant it in loam or a soil rich in organic matter, with good drainage."
    ),
    "Rudbeckia hirta": (
        "Grow black-eyed Susan in moist, well-drained soil, whether clay, loam, or sandy. "
        "Give it 6 or more hours of direct sun a day, or 2 to 6 hours in part shade. "
        "It holds up moderately well to drought and salt. "
        "Expect each plant to be very short-lived."
    ),
    "Gaillardia x grandiflora": (
        "Grow blanket flower at the front of a border, in containers, on a patio, or along a walkway. "
        "Give it full sun, with at least 6 hours of direct sunlight each day. "
        "Keep cutting off spent flowers, and it can bloom for most of the season."
    ),
    "Echinacea purpurea": (
        "Coneflower is a long-blooming plant for borders or groupings in pollinator gardens, meadows, and naturalized areas. "
        "It grows in full sun with at least 6 hours of direct sunlight a day. "
        "It also grows in partial shade with 2 to 6 hours of direct sun. "
        "Plant it in well-drained soil that can be moist or occasionally dry."
    ),
    "Coreopsis lanceolata": (
        "Lanceleaf coreopsis is a daisy-family wildflower of prairies and fields. "
        "Give it direct sun, 6 or more hours a day, or 2 to 6 hours in part shade. "
        "Plant it in soil that drains well. "
        "Take care not to overwater it. "
        "Feeding is optional, but if you feed it, use a low rate of controlled-release fertilizer."
    ),
    "Rudbeckia fulgida": (
        "Orange coneflower is grown in perennial beds, borders and naturalized areas. "
        "Give it full sun if you can, though it tolerates partial shade. "
        "Plant it in humus-rich soil that holds moisture but drains well. "
        "That said, it does fine in any soil that is not soggy. "
        "Once it is established, it can handle drought."
    ),
    "Viola cornuta": (
        "Horned violet is a tufted perennial that spreads by creeping stems. "
        "Grow it as a perennial in borders and woodland gardens, or as an annual in window boxes and containers. "
        "You can also use it as a ground cover. "
        "Plant it where it gets full sun or part shade. "
        "Give it fertile, humus-rich soil that is moist but drains well."
    ),
}


def _key(name: str) -> str:
    """A scientific name as the catalog and the records can both spell it."""
    return " ".join(name.replace("×", "x").lower().split())


@pytest.fixture(scope="module")
def catalog_notes():
    return {entry["species"]["scientific_name"]: entry["species"]["care_notes"]
            for entry in json.loads(CATALOG.read_text(encoding="utf-8"))}


@pytest.fixture(scope="module")
def traced():
    data = json.loads(SOURCES.read_text(encoding="utf-8"))
    return {note["scientific_name"]: note for note in data["notes"]}


@pytest.fixture(scope="module")
def citations():
    """Normalised scientific name -> every citation its records hold."""
    found: dict[str, list[dict]] = {}
    for path in sorted(VERIFIED.glob("*.json")):
        for record in json.loads(path.read_text(encoding="utf-8"))["records"]:
            names = {record.get("scientific_name_accepted"),
                     record.get("scientific_name_given")}
            for name in {_key(n) for n in names if n}:
                found.setdefault(name, []).extend(record.get("citations") or [])
    return found


@pytest.mark.parametrize("name", sorted(PINNED))
def test_the_catalog_holds_the_pinned_note(name, catalog_notes):
    assert catalog_notes[name] == PINNED[name]


def test_the_trace_covers_the_pinned_notes_and_no_others(traced):
    assert set(traced) == set(PINNED)


@pytest.mark.parametrize("name", sorted(PINNED))
def test_every_sentence_is_traced_in_order(name, traced):
    entry = traced[name]
    texts = [sentence["text"] for sentence in entry["sentences"]]
    assert entry["note"] == PINNED[name]
    assert " ".join(texts) == PINNED[name]
    for text in texts:
        assert text.endswith("."), text
        assert ". " not in text, f"two sentences on one trace entry: {text}"


@pytest.mark.parametrize("name", sorted(PINNED))
def test_every_quote_is_in_the_species_own_record(name, traced, citations):
    held = citations[_key(name)]
    for sentence in traced[name]["sentences"]:
        quote = sentence["quote"]
        at_url = [c for c in held if c.get("url") == sentence["url"]]
        sources = [c["source"] for c in at_url if quote in (c.get("quote") or "")]
        assert sources, f"no citation of {name} holds this quote at this url: {quote!r}"
        assert sentence["source"] in sources
        whole = any(quote == c.get("quote") for c in at_url)
        assert whole or len(quote.split()) >= MIN_QUOTE_WORDS, quote


@pytest.mark.parametrize("name", sorted(PINNED))
def test_no_note_makes_a_claim_or_strays_off_its_subject(name):
    note = PINNED[name]
    assert not claims(note, name)
    assert not OFF_SUBJECT.findall(note)


@pytest.mark.parametrize("name", sorted(PINNED))
def test_every_note_has_the_shape_the_page_expects(name, traced):
    note = PINNED[name]
    assert 3 <= len(traced[name]["sentences"]) <= 6
    assert 40 <= len(note.split()) <= 90
    assert note.endswith(".")
    assert "\n" not in note and "  " not in note
    assert not set("—;()") & set(note)


def _before(tmp_path: Path) -> Path:
    """species_catalog.json as it stood at BEFORE, saved under the temp dir."""
    try:
        shown = subprocess.run(
            ["git", "-C", str(REPO), "show",
             f"{BEFORE}:garden-gnome/app/data/species_catalog.json"],
            capture_output=True, check=False, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        pytest.skip(f"git is not available to read {BEFORE}: {exc}")
    if shown.returncode != 0:
        pytest.skip(f"this clone does not have {BEFORE} (a one-commit "
                    f"checkout, as CI makes): {shown.stderr.decode()[:200]}")
    path = tmp_path / f"species_catalog_{BEFORE}.json"
    path.write_bytes(shown.stdout)
    return path


def _boot_onto_the_pinned_notes(boot, older: Path):  # noqa: F811
    engine, run, _ = boot
    run(older)
    stale = _db_prose(engine)

    out = run()

    found = re.search(r"curated text refreshed (\d+)", out)
    assert found, out
    assert int(found.group(1)) >= len(PINNED)
    fresh = _db_prose(engine)
    for name, note in PINNED.items():
        assert stale[(name, "care_notes")] != note
        assert fresh[(name, "care_notes")] == note


def test_a_database_seeded_at_the_ship_tip_takes_the_notes_on_the_next_boot(boot, tmp_path):  # noqa: F811
    _boot_onto_the_pinned_notes(boot, _before(tmp_path))


def test_the_boot_refresh_carries_the_notes_into_any_older_database(boot, tmp_path):  # noqa: F811
    entries = json.loads(CATALOG.read_text(encoding="utf-8"))
    for entry in entries:
        if entry["species"]["scientific_name"] in PINNED:
            entry["species"]["care_notes"] = "A shorter note."
    older = tmp_path / "older.json"
    older.write_text(json.dumps(entries), encoding="utf-8")
    _boot_onto_the_pinned_notes(boot, older)
