"""Part-aware toxicity, and plain-language descriptions built from it.

WHY A BOOLEAN IS NOT ENOUGH

`toxic_to_pets: true` is the wrong shape for the truth, and on several common
plants it is actively misleading:

  * Tomato. The fruit is food. The leaves and stems carry tomatine and are
    toxic. "Tomato: toxic" is contradictory to anyone holding a tomato
    sandwich, so they stop believing the label — including on the plants where
    it matters.
  * Rhubarb. Stalks are a dessert; leaves cause oxalate poisoning.
  * True lilies. Severely toxic to CATS — a few petals or even pollen can cause
    acute kidney failure — while dogs typically get an upset stomach. One
    boolean either terrifies dog owners or fatally under-warns cat owners.
  * Pothos and the other aroids. Calcium oxalate: genuinely unpleasant, mouth
    irritation and drooling, but rarely serious. Flagged identically to a lily
    by a boolean.

So toxicity is stored as structure — which parts, to whom, how bad, and by what
agent — and the reader-facing sentence is generated from it. The goal is a
caretaker who trusts the warning because it matches what they already know.

This module is descriptive, not veterinary advice: severe cases say to call a
vet rather than implying the app can triage.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

SEVERITY_ORDER = {"none": 0, "mild": 1, "moderate": 2, "severe": 3}

PART_LABELS = {
    "all": "all parts",
    "foliage": "leaves and stems",
    "leaf": "leaves",
    "stem": "stems",
    "sap": "the sap",
    "fruit": "the fruit",
    "seed": "the seeds",
    "pit": "the pits",
    "bulb": "the bulbs",
    "root": "the roots",
    "tuber": "the tubers",
    "flower": "the flowers",
    "pollen": "the pollen",
}


@dataclass
class Toxicity:
    """What is toxic about a plant, to whom, and how badly."""
    toxic: bool | None = None                 # None = unknown, not "safe"
    parts: list[str] = field(default_factory=list)        # toxic parts
    edible_parts: list[str] = field(default_factory=list)  # explicitly safe
    at_risk: list[str] = field(default_factory=list)      # cats / dogs / humans
    severity: str = "unknown"
    effect: str = ""                          # "mouth irritation", "kidney failure"
    agent: str = ""                           # "calcium oxalate", "tomatine"
    source: str = ""
    # The authority whose claim settled the flag, when one did. A False an
    # extension service stated is a different fact from a False the legacy
    # catalog defaulted to, and the sentence has to say which.
    cited_to: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def is_contradictory(self) -> bool:
        """True when the plant is both edible and toxic depending on the part.

        These are exactly the records a flat label gets wrong, so they are
        worth naming."""
        return bool(self.parts and self.edible_parts)


# A small, deliberately conservative set of the part-specific cases a boolean
# gets wrong. These are long-established and uncontroversial; the point is to
# encode the PATTERN (toxicity is part-specific) rather than to be exhaustive.
KNOWN_NUANCE: dict[str, Toxicity] = {
    "solanum lycopersicum": Toxicity(
        toxic=True, parts=["foliage"], edible_parts=["fruit"],
        at_risk=["cats", "dogs"], severity="moderate",
        effect="drooling and stomach upset", agent="tomatine",
        source="well-established Solanaceae chemistry",
    ),
    "solanum tuberosum": Toxicity(
        toxic=True, parts=["foliage", "sprout"], edible_parts=["tuber"],
        at_risk=["cats", "dogs", "humans"], severity="moderate",
        effect="stomach upset; green or sprouted tubers too", agent="solanine",
        source="well-established Solanaceae chemistry",
    ),
    "rheum rhabarbarum": Toxicity(
        toxic=True, parts=["leaf"], edible_parts=["stem"],
        at_risk=["cats", "dogs", "humans"], severity="severe",
        effect="oxalate poisoning", agent="oxalic acid",
        source="well-established",
    ),
}

# Genera where the risk differs sharply by animal — the case a boolean is
# least able to express, and the one with the worst downside.
SPECIES_SPECIFIC_RISK: dict[str, Toxicity] = {
    "lilium": Toxicity(
        toxic=True, parts=["all", "pollen"], at_risk=["cats"], severity="severe",
        effect="acute kidney failure — a few petals or even pollen can be fatal",
        source="widely documented feline lily toxicosis",
    ),
    "hemerocallis": Toxicity(
        toxic=True, parts=["all"], at_risk=["cats"], severity="severe",
        effect="acute kidney failure", source="widely documented",
    ),
}

# The aroids, which dominate houseplant catalogs and are uniformly over-warned.
AROID_GENERA = {
    "anthurium", "philodendron", "epipremnum", "monstera", "dieffenbachia",
    "spathiphyllum", "aglaonema", "alocasia", "colocasia", "caladium",
    "syngonium", "zantedeschia", "scindapsus",
}
AROID_TOXICITY = Toxicity(
    toxic=True, parts=["all"], at_risk=["cats", "dogs", "humans"],
    severity="mild", effect="mouth irritation, drooling, and swelling if chewed",
    agent="calcium oxalate crystals", source="characteristic of Araceae",
)


def lookup(scientific_name: str) -> Toxicity | None:
    """Known part-specific or animal-specific toxicity for a name, if any."""
    name = (scientific_name or "").strip().lower()
    if not name:
        return None
    if name in KNOWN_NUANCE:
        return KNOWN_NUANCE[name]
    genus = name.split()[0] if name.split() else ""
    if genus in SPECIES_SPECIFIC_RISK:
        return SPECIES_SPECIFIC_RISK[genus]
    if genus in AROID_GENERA:
        return AROID_TOXICITY
    return None


# --- reading toxicity out of prose ------------------------------------------

_PART_PATTERNS = [
    (r"\ball parts?\b", "all"),
    (r"\bfoliage\b|\bleaves and stems\b", "foliage"),
    (r"\bleaf|\bleaves\b", "leaf"),
    (r"\bsap\b|\bjuice\b|\blatex\b", "sap"),
    (r"\bberries\b|\bberry\b|\bfruit\b", "fruit"),
    (r"\bseeds?\b", "seed"),
    (r"\bbulbs?\b", "bulb"),
    (r"\broots?\b", "root"),
    (r"\bpollen\b", "pollen"),
]
_ANIMALS = [(r"\bcats?\b", "cats"), (r"\bdogs?\b", "dogs"),
            (r"\bhumans?\b|\bchildren\b|\bpeople\b", "humans"),
            (r"\bpets?\b", "pets")]
# "Fatal if eaten" is a toxicity statement that never uses the word "toxic".
# Missing those would drop precisely the most severe warnings, so the trigger
# list covers outcome words as well as hazard words.
_TOXIC_WORDS = (
    r"toxic|poison|irritant|harmful|noxious|fatal|deadly|lethal"
    r"|kidney failure|kills|death"
)


def parse_toxicity(text: str, source: str = "") -> Toxicity | None:
    """Read a toxicity statement out of prose. None when nothing is stated.

    Silence is never read as safety — an absent mention leaves `toxic` unknown,
    which the renderer reports honestly rather than as 'pet-safe'."""
    low = (text or "").lower()
    if not re.search(_TOXIC_WORDS, low):
        return None

    parts = [label for pat, label in _PART_PATTERNS if re.search(pat, low)]
    if "all" in parts:
        parts = ["all"]
    at_risk = [label for pat, label in _ANIMALS if re.search(pat, low)]

    severity = "moderate"
    if re.search(r"\bfatal\b|\bdeadly\b|\bdeath\b|\bkidney failure\b|\bsevere", low):
        severity = "severe"
    elif re.search(r"\bmild\b|\birritat|\bunpleasant\b", low):
        severity = "mild"

    agent = ""
    for known in ("calcium oxalate", "oxalic acid", "solanine", "tomatine",
                  "saponin", "alkaloid", "cyanide", "cardiac glycoside"):
        if known in low:
            agent = known
            break

    return Toxicity(toxic=True, parts=parts or ["all"], at_risk=at_risk or ["pets"],
                    severity=severity, agent=agent, source=source)


def from_legacy(toxic_to_pets: bool | None, scientific_name: str = "",
                cited_to: str = "") -> Toxicity:
    """Upgrade the existing boolean, consulting known nuance first.

    A stored `False` means 'no toxicity recorded', which is weaker than 'safe' —
    it is reported as such rather than promoted to a guarantee. `cited_to`
    names the authority whose claim settled the flag, when one did."""
    known = lookup(scientific_name)
    if known:
        return known
    if toxic_to_pets is True:
        return Toxicity(toxic=True, parts=["all"], at_risk=["pets"],
                        severity="unknown", source="catalog (legacy flag)",
                        cited_to=cited_to)
    if toxic_to_pets is False:
        return Toxicity(toxic=False, source="catalog (legacy flag)",
                        cited_to=cited_to)
    return Toxicity(toxic=None)


def cited_authority(provenance: dict | None, sources: list | None,
                    field: str = "toxic_to_pets") -> str:
    """The authority whose page settled `field`, or "" when nothing cited it.

    Read off the row's `care_sources` (recompute.py: name, link and field
    names, sorted) and only when the provenance says the value was sourced:
    a genus page never speaks for a species on toxicity (ADR 0002), and a
    row resolved before sources were materialised has provenance but no
    page to credit."""
    if (provenance or {}).get(field) != "sourced":
        return ""
    for entry in sources or []:
        if field in (entry.get("fields") or []) and not entry.get("inferred"):
            return entry.get("authority") or ""
    return ""


# --- the reader-facing sentence ---------------------------------------------

def _join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


# Labels that take a singular verb. Everything else in PART_LABELS is plural,
# so agreement is decided by the label rather than assumed — "stems is edible"
# reads as broken English and undermines the trust this nuance exists to build.
_SINGULAR_LABELS = {"the sap", "the fruit", "the pollen"}


def _verb(label: str) -> str:
    return "is" if label in _SINGULAR_LABELS else "are"


def describe(tox: Toxicity, common_name: str = "This plant") -> str:
    """One or two plain sentences a caretaker can act on.

    Leads with the distinction when a plant is both edible and toxic, because
    that is the case a flat label gets wrong and the reason people stop
    trusting warnings."""
    if tox.toxic is None:
        # "No information" would be untrue of a row whose cited description
        # of harm sits server-side with no verdict yet (ADR 0003 keeps the
        # passage there). What is missing is the verdict.
        return (
            f"No toxicity verdict recorded for {common_name.lower()} yet — "
            f"treat it as unknown rather than safe, and keep it away from pets "
            f"that chew plants."
        )
    if tox.toxic is False and tox.cited_to:
        # An authority said so. "Nothing noted" would undersell that, and for
        # a plant whose hazard is to people rather than pets it is untrue.
        return (
            f"{tox.cited_to} records no toxicity to pets for "
            f"{common_name.lower()}. That is not a guarantee of safety — keep "
            f"it away from pets that chew plants."
        )
    if tox.toxic is False:
        return (
            f"No toxicity is recorded for {common_name.lower()}. That is not a "
            f"guarantee of safety — it means nothing harmful has been noted."
        )

    who = _join([a for a in tox.at_risk]) or "pets"
    toxic_parts = _join([PART_LABELS.get(p, p) for p in tox.parts]) or "the plant"
    agent = f" ({tox.agent})" if tox.agent else ""
    effect = f" — {tox.effect}" if tox.effect else ""

    # The contradictory case first: say what is safe before what is not, so the
    # reader's own experience ("I eat tomatoes") is confirmed, not contradicted.
    # "You can eat X" sidesteps number agreement on the edible side entirely.
    if tox.is_contradictory:
        safe = _join([PART_LABELS.get(p, p) for p in tox.edible_parts])
        return (
            f"You can eat {safe}, but {toxic_parts} {_verb(toxic_parts)} toxic "
            f"to {who}{agent}{effect}. Keep trimmings and prunings out of reach."
        )

    if tox.severity == "severe":
        return (
            f"⚠️ Seriously toxic to {who}: {toxic_parts}{agent}{effect}. "
            f"If ingestion is suspected, contact a vet immediately — do not "
            f"wait for symptoms."
        )
    if tox.severity == "mild":
        return (
            f"Mildly toxic to {who} if chewed: {toxic_parts}{agent}{effect}. "
            f"Unpleasant rather than dangerous, but worth placing out of reach."
        )
    return (
        f"Toxic to {who}: {toxic_parts}{agent}{effect}. Keep it where curious "
        f"pets and children can't chew it."
    )


def describe_for_species(scientific_name: str, common_name: str,
                         toxic_to_pets: bool | None, cited_to: str = "") -> str:
    """The entry point the app uses: best available nuance for a catalog row."""
    return describe(from_legacy(toxic_to_pets, scientific_name, cited_to),
                    common_name)
