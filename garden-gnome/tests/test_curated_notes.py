"""The curated catalog's prose makes no safety claim of its own.

species_catalog.json holds the 129 curated entries, the ones with check
schedules. Their care notes show in the Care notes card on a species page and
in the Care guide on a plant's page, and their schedule notes ride along with
the checks. 33 of those notes called a plant "Pet-safe", "harmless" or "safe
for most pets", and on Parsley, Catnip, Nasturtium and Gourds the hazard
sentence on the same page said the opposite. A missing record is "no
record", never "safe" (ADR 0002, ADR 0005), and whether a plant can hurt
anyone is said in one place: the hazard sentence that
app/services/toxicity.py builds from the claim graph.

The other direction breaks the same rule. Sage, Thyme, Baby's Breath,
Hollyhock and China Aster were "mildly toxic" in their notes while NC State
records no toxicity to pets for them, and Moonflower's "all parts" went past
its source, which names only the seeds. A verdict typed into prose has no
citation and cannot follow the evidence when it changes, so a note states
none, in either direction: no "safe", no "toxic", and no "edible", which is
a harm-capable field shown only with its conditions (ADR 0008). A note may
send the reader to the hazard note on the page, and that is all.

The check reads phrases, not a list of the plants that once had them, so a
new entry is held to it too. A phrase that is genuinely about something else
goes on the allow-list with its reason; there is none today.
"""
import json
import re
from pathlib import Path

import pytest

CATALOG = Path(__file__).resolve().parents[1] / "app" / "data" / "species_catalog.json"

#: Any form of "safe" counts, because on a page beside a hazard sentence a
#: reader takes "safe to cut" or "safe for most pets" the same way.
SAFETY_CLAIM = re.compile(
    r"\b(?:pet|cat|dog|child|kid|baby|animal)[- ]?(?:safe|friendly|proof)\b"
    r"|\b(?:un)?safe(?:ly|ty)?\b"
    r"|\bharmless\b|\bbenign\b|\binnocuous\b"
    r"|\bnon-?toxic\w*|\bnot toxic\b|\bno toxicity\b",
    re.I)

#: A verdict that the plant harms someone, in the words such prose uses.
#: "Fatal" and "irritant" count: "the latter usually fatal" beside a plant
#: the hazard sentence calls toxic to pets reads as a hazard, whatever it
#: meant about overwatering.
VERDICT = re.compile(
    r"\btoxi\w*|\bpoison\w*|\bvenom\w*|\bharmful\b|\birrita(?:nt|tion|tes?)\b"
    r"|\bfatal\b|\bdeadly\b|\blethal\b|\bdangerous\b",
    re.I)

#: What a person may eat, or take for their health: ADR 0008 makes
#: edibility harm-capable, and a care note is no place for medicine.
EATING = re.compile(r"\b(?:in)?edible\b|\bmedicinal\b", re.I)

#: A note may point at the hazard sentence without restating it.
REFERENCE = re.compile(
    r"\b(?:see|read|check)\s+the\s+(?:hazard|safety|toxicity)\s+(?:note|sentence|line)\b",
    re.I)

#: (scientific name, exact phrase) -> why the phrase is not a claim.
ALLOWED: dict[tuple[str, str], str] = {}


def _prose(catalog):
    """Every prose value an entry carries: its care notes, its soil, and the
    note on each of its schedules -- the fields the boot refresh keeps in
    step with this file (ADR 0010)."""
    for entry in catalog:
        species = entry["species"]
        name = species["scientific_name"]
        yield name, "care_notes", species.get("care_notes") or ""
        yield name, "soil_type", species.get("soil_type") or ""
        for schedule in entry["schedules"]:
            yield name, f"schedules[{schedule['care_type']}].notes", schedule.get("notes") or ""


def _cleared(text: str, name: str) -> str:
    for (allowed_name, phrase) in ALLOWED:
        if allowed_name == name:
            text = text.replace(phrase, " ")
    return REFERENCE.sub(" ", text)


def claims(text: str, name: str = "") -> list[str]:
    """The safety claims in a piece of prose: that it is safe, that it is
    toxic, or that it is food or medicine."""
    text = _cleared(text, name)
    return [m.group(0) for pattern in (SAFETY_CLAIM, VERDICT, EATING)
            for m in pattern.finditer(text)]


@pytest.fixture(scope="module")
def catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


@pytest.mark.parametrize("text", [
    "Pet-safe. Brown leaf tips usually mean fluoride in tap water.",
    "Perennial herb beloved by cats (and harmless to them).",
    "Ornamental gourds are not edible but safe for most pets.",
    "Safe around children and dogs.",
    "Harvest once 1 foot tall; safe to cut up to half the plant at a time.",
    "A pet friendly fern.",
    "Cat-safe and easy.",
    "Non-toxic to cats and dogs.",
    "A nontoxic choice for a nursery.",
    "Not toxic to pets.",
    "Unsafe for cats.",
])
def test_the_check_sees_a_safety_claim(text):
    assert claims(text), text


@pytest.mark.parametrize("text", [
    "Mildly toxic to cats and dogs.",
    "ALL PARTS TOXIC — seeds especially.",
    "TOXIC to dogs and cats (allium family).",
    "All parts are poisonous to pets and humans.",
    "Seeds and sap are harmful to pets.",
    "Wear gloves — sap is an irritant.",
    "Can cause skin irritation.",
    "Can be fatal to pets and livestock.",
    "Seeds and pods are especially dangerous to pets.",
    "Toxicity is low.",
])
def test_the_check_sees_a_toxicity_verdict(text):
    assert claims(text), text


@pytest.mark.parametrize("text", [
    "Purple flowers are edible.",
    "Ornamental gourds are inedible.",
    "Native perennial and medicinal herb.",
])
def test_the_check_sees_a_claim_about_eating(text):
    assert claims(text), text


@pytest.mark.parametrize("text", [
    "Let soil dry fully between waterings; rot is the main risk.",
    "Harvest once 1 foot tall; cut up to half the plant at a time.",
    "Wear gloves when pruning.",
    "Keep away from cold drafts and dry air.",
    "Excellent companion plant that deters aphids.",
    "Plant when all frost danger passes.",
    "Reduce watering as fruits cure on the vine.",
    "Wear gloves when pruning; see the hazard note on this page.",
    "Before sharing a cutting, read the toxicity note.",
])
def test_the_check_leaves_care_advice_and_a_reference_alone(text):
    assert not claims(text), text


def test_every_prose_field_is_read(catalog):
    """A walker that skipped the schedule notes would pass a file full of
    claims, so it is held to the count."""
    values = list(_prose(catalog))
    schedules = sum(len(entry["schedules"]) for entry in catalog)
    assert len(catalog) == 129
    assert len(values) == 2 * len(catalog) + schedules


def test_the_allow_list_names_real_phrases(catalog):
    """An entry for a phrase the file no longer has is a stale exemption."""
    text = {name: " ".join(t for n, _, t in _prose(catalog) if n == name)
            for name in {entry["species"]["scientific_name"] for entry in catalog}}
    for (name, phrase), reason in ALLOWED.items():
        assert reason
        assert phrase in text.get(name, ""), (name, phrase)


def test_no_curated_note_makes_a_safety_claim(catalog):
    found = [f"{name} {field}: {phrase!r} in {text!r}"
             for name, field, text in _prose(catalog)
             for phrase in claims(text, name)]
    assert not found, (
        f"{len(found)} safety claim(s) in species_catalog.json. Say it in the "
        "hazard sentence (app/services/toxicity.py) or not at all:\n"
        + "\n".join(found))
