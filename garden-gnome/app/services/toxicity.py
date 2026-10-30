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
  * Poison ivy. NC State tags it non-toxic for cats and dogs, and rates it a
    high-severity hazard to people. A pets-only flag reads as "harmless".

So toxicity is stored as structure — which parts, to whom, how bad, and by what
agent — and the reader-facing sentence is generated from it. The goal is a
caretaker who trusts the warning because it matches what they already know.

WHERE THE STRUCTURE COMES FROM

The cited evidence first. The flag is a claim; the hazard to people, and how
severe it is, are read out of the passages behind the safety claims
(`claims.store.safety_passages`) and the researcher's restatement of them
(`toxicity_detail`). Those stay on the server (ADR 0003); what reaches a
reader is the fact -- "NC State Extension rates it high severity" -- with the
authority's name on it.

The small tables below come second. They encode the part-specific and
animal-specific patterns a flag cannot carry (tomato fruit, lily and cats),
and they never overrule a source: a cited "non-toxic" beats them, and a cited
severity is never talked down by them. They hold no "mild" of their own,
because calling something mild is a judgement only a source gets to make.

WHOSE SEVERITY IT IS

NC State's Poison Severity sits under its "Poisonous to Humans" heading, apart
from the Problem for Cats and Problem for Dogs tags, which carry no severity
at all. So a rating is a fact about people, and the word it gives --
"seriously", "mildly" -- goes on the people half of a sentence only. The
animals are "toxic to pets" (or to cats, or dogs) unless a table or a source's
own grave words about them say more. "Mildly toxic to pets" from a rating
nobody gave for pets would understate garlic, azaleas and daffodils.

FOOD CROPS

A crop is named by what is eaten. Where a table knows the eaten part, the
sentence leads with it ("The tubers are the crop; ...") so that a warning
about the foliage is never read as a warning about dinner, and the eaten part
is what keeps a crop NC State rates highly on a growing area's candidate list
(fit.never_a_candidate).

This module is descriptive, not veterinary or medical advice: serious cases
say to call Poison Control, a local poison centre or a vet rather than
implying the app can triage.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Iterable

SEVERITY_ORDER = {"unknown": 0, "none": 0, "mild": 1, "moderate": 2, "severe": 3}

#: NC State's "Poison Severity" scale, onto the one used here.
RATING_SEVERITY = {"low": "mild", "medium": "moderate", "high": "severe"}

#: Where a caretaker in the US reaches poison help. The app is built for US
#: growers (its weather falls back to the National Weather Service), so the
#: one number given is that one, and it says whose number it is.
POISON_CONTROL = "Poison Control (US 1-800-222-1222)"
#: And everyone else. No one number serves every country, so the sentence
#: names the service, after the US number, for a reader who is not in the US.
LOCAL_POISON_CENTRE = "your local poison centre"

PART_LABELS = {
    "all": "all parts",
    "foliage": "the leaves and stems",
    "leaf": "the leaves",
    "stem": "the stems",
    "stalk": "the stalks",
    "sap": "the sap",
    "fruit": "the fruit",
    "ripe_fruit": "the ripe fruit",
    "berry": "the berries",
    "seed": "the seeds",
    "pit": "the pits",
    "bulb": "the bulbs",
    "root": "the roots",
    "tuber": "the tubers",
    "green_tuber": "any green skin on the tubers",
    "sprout": "the sprouts",
    "flower": "the flowers",
    "pollen": "the pollen",
    "unripe_fruit": "the unripe fruit",
    # Crop-specific parts: the eaten part named the way a grower names it,
    # and the condition its source puts on it when that is part of the name.
    "peanut": "the peanuts",
    "cooked_bean": "the cooked beans",
    "raw_bean": "the raw mature beans",
}


@dataclass
class Toxicity:
    """What is toxic about a plant, to whom, and how badly."""
    toxic: bool | None = None                 # None = unknown, not "safe"
    parts: list[str] = field(default_factory=list)        # toxic parts
    edible_parts: list[str] = field(default_factory=list)  # explicitly safe
    at_risk: list[str] = field(default_factory=list)      # cats / dogs / humans / pets
    severity: str = "unknown"
    effect: str = ""                          # "mouth irritation", "kidney failure"
    agent: str = ""                           # "calcium oxalate", "tomatine"
    source: str = ""
    # The authority whose claim settled the flag, when one did. A False an
    # extension service stated is a different fact from a False the legacy
    # catalog defaulted to, and the sentence has to say which.
    cited_to: str = ""
    # A hazard to people that a cited passage records, apart from the pet
    # flag -- NC State's "Poisonous to Humans" block, RHS's "TOXIC if eaten".
    people: bool = False
    # NC State's Poison Severity for this species ("high", "medium", "low"),
    # and who published it. Empty when no source rates it. A fact about
    # people: see "Whose severity it is" above.
    rating: str = ""
    rated_by: str = ""
    # `severity` split by who it is about. `severity` is the higher of the
    # two, and decides how urgent the advice is; each half decides only its
    # own words. An animal's comes from a table or a source's grave words
    # about animals; a person's from a table that names people, the rating,
    # or a source calling it fatal to them.
    animal_severity: str = "unknown"
    people_severity: str = "unknown"
    # Who "people" are, when a source narrows it: NC State's peanut rating is
    # an allergy, and saying "people" alone would warn everyone off peanuts.
    people_label: str = "people"

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def is_crop(self) -> bool:
        """Whether a table names the part of this plant that is eaten."""
        return bool(self.edible_parts)

    @property
    def is_contradictory(self) -> bool:
        """True when the plant is both edible and toxic depending on the part.

        These are exactly the records a flat label gets wrong, so they are
        worth naming."""
        return bool(self.parts and self.edible_parts)

    @property
    def people_at_risk(self) -> bool:
        return self.people or "humans" in self.at_risk

    @property
    def animals_at_risk(self) -> list[str]:
        """The animals the toxic flag (or a table) names, in their words."""
        if self.toxic is not True:
            return []
        return [a for a in self.at_risk if a != "humans"] or ["pets"]


# A small, deliberately conservative set of the part-specific cases a boolean
# gets wrong. These are long-established and uncontroversial; the point is to
# encode the PATTERN (toxicity is part-specific) rather than to be exhaustive.
# Severity here is a floor the tables were written with, never a ceiling: a
# cited rating above it wins.
#
# Every entry with `edible_parts` is a food crop, and the parts on both sides
# are the ones its cited passages name. Those entries are also the only
# edible plants a high-severity rating for people does not take off a
# candidate list (`is_food_crop`), so a new one is a deliberate decision:
# test_candidates_on_the_real_catalog pins the set.
KNOWN_NUANCE: dict[str, Toxicity] = {
    "solanum lycopersicum": Toxicity(
        toxic=True, parts=["foliage"], edible_parts=["ripe_fruit"],
        at_risk=["cats", "dogs"], severity="moderate",
        effect="drooling and stomach upset", agent="tomatine",
        source="well-established Solanaceae chemistry",
    ),
    "solanum tuberosum": Toxicity(
        toxic=True, parts=["foliage", "sprout", "berry", "green_tuber"],
        edible_parts=["tuber"],
        at_risk=["cats", "dogs", "humans"], severity="moderate",
        agent="solanine",
        source="well-established Solanaceae chemistry",
    ),
    "rheum rhabarbarum": Toxicity(
        toxic=True, parts=["leaf"], edible_parts=["stalk"],
        at_risk=["cats", "dogs", "humans"], severity="severe",
        effect="oxalate poisoning", agent="oxalic acid",
        source="well-established",
    ),
    # NC State: "The fruits and seeds are edible; however, the remainder of
    # the plant is poisonous"; flowers, leaves, roots and stems carry
    # solanine; a problem for cats and dogs. No severity of the table's own.
    "solanum melongena": Toxicity(
        toxic=True, parts=["foliage", "flower", "root"], edible_parts=["fruit"],
        at_risk=["cats", "dogs", "humans"], agent="solanine",
        source="NC State Extension",
    ),
    # NC State: "All parts are toxic except the ripe fruits." Human-scoped;
    # the page tags no pet, so the table says nothing about pets either.
    "physalis philadelphica": Toxicity(
        toxic=None, parts=["foliage", "flower", "unripe_fruit"],
        edible_parts=["ripe_fruit"], at_risk=["humans"],
        agent="solanine", source="NC State Extension",
    ),
    # NC State: "The raw mature seed is poisonous ... destroyed by thoroughly
    # cooking the seed"; Poison Part: Roots, Seeds.
    "phaseolus lunatus": Toxicity(
        toxic=None, parts=["raw_bean", "root"], edible_parts=["cooked_bean"],
        at_risk=["humans"], agent="hydrocyanic acid",
        source="NC State Extension",
    ),
    # NC State's high rating is the allergy: "Peanut-allergic reactions";
    # the eaten part is the hazard, to the people allergic to it.
    "arachis hypogaea": Toxicity(
        toxic=None, parts=["peanut"], edible_parts=["peanut"],
        at_risk=["humans"], agent="seed storage proteins",
        people_label="people with a peanut allergy",
        source="NC State Extension",
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

# The aroids, which dominate houseplant catalogs. The pattern -- calcium
# oxalate in every part, to every animal that chews -- is the family's; how
# bad it is varies by species, and NC State rates them anywhere from low
# (Monstera) to high (Dieffenbachia, airway swelling). So the table states
# the pattern and leaves severity to the source.
AROID_GENERA = {
    "anthurium", "philodendron", "epipremnum", "monstera", "dieffenbachia",
    "spathiphyllum", "aglaonema", "alocasia", "colocasia", "caladium",
    "syngonium", "zantedeschia", "scindapsus",
}
AROID_TOXICITY = Toxicity(
    toxic=True, parts=["all"], at_risk=["cats", "dogs", "humans"],
    effect="mouth irritation, drooling and swelling if chewed",
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


def is_food_crop(scientific_name: str) -> bool:
    """Whether a table names the eaten part of this species (KNOWN_NUANCE).

    By name, not through a Toxicity record, so a pet verdict that replaces
    the table's (a cited "non-toxic to pets") does not stop a crop being one."""
    known = lookup(scientific_name)
    return bool(known and known.edible_parts)


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


# --- reading the cited evidence ---------------------------------------------
#
# The passages behind the safety claims are verbatim extension text, and the
# researcher's `toxicity_detail` restates them. Neither is structured, so the
# reading below is deliberately narrow: it takes only statements that say
# outright who is at risk or how severe it is, and a negation anywhere in the
# clause before a match ("the page carries no Poisonous to Humans block")
# discards it. Missing a hazard here leaves the sentence where it was; reading
# one in that the source did not state would put words in its mouth.

_RATING_RE = re.compile(
    r"(?:poison\s+severity|severity)\W{0,4}(?:is|rated|as|of|:)?\W{0,4}"
    r"(high|medium|moderate|low)\b"
    r"|\b(high|medium|moderate|low)\b\W{0,3}(?:poison\s+)?severity",
    re.I)
_NEGATION_RE = re.compile(
    r"\b(?:no|not|non|without|nothing|neither|nor|never|lacks?|absent|none)\b"
    r"|non-",
    re.I)
#: Statements that name people as the ones at risk. NC State's poison block
#: sits under a "Poisonous to Humans" heading, and its Problems field lists
#: "Problem for Children".
_PEOPLE_RE = re.compile(
    r"poisonous[- ]to[- ]humans|problem for children"
    r"|\b(?:toxic|poisonous|harmful|dangerous|fatal|deadly|lethal)\b[^.;]{0,30}?"
    r"\b(?:to|for)\s+(?:[\w/]+,?\s+(?:and\s+)?){0,4}?(?:humans?|people|children)\b",
    re.I)
_HARM_RE = re.compile(
    r"\b(?:toxic|poison\w*|harmful|dangerous|fatal|deadly|lethal)\b", re.I)
_GRAVE_RE = re.compile(
    r"\b(?:highly|extremely|very|seriously)\s+(?:toxic|poisonous)\b"
    r"|\bfatal\b|\bdeadly\b|\blethal\b|\bdeath\b",
    re.I)
_ANIMAL_RE = re.compile(
    r"\b(?:cats?|dogs?|pets?|horses?|livestock|animals?|cattle|sheep|goats?"
    r"|birds?|rabbits?|tortoises?)\b",
    re.I)
_PERSON_RE = re.compile(r"\b(?:humans?|people|children|child|persons?|kids)\b", re.I)
#: Pets as the app names them. Horses and livestock are not, and a source's
#: "fatal to horses" does not make a plant seriously toxic to a cat.
_PET_RE = re.compile(r"\b(?:cats?|kittens?|dogs?|pupp(?:y|ies)|pets?)\b", re.I)
_NOXIOUS_RE = re.compile(r"\bnoxious weed", re.I)
#: NC State's Problems field lists "Invasive Species" beside the pet tags.
_INVASIVE_RE = re.compile(r"\binvasive species\b", re.I)
_CLAUSES_RE = re.compile(r"[.!?;\n]+")

#: A condition an edibility passage puts on eating what is eaten: "edible
#: when cooked", "only the ripe fruit", "in small amounts", "should not be
#: eaten raw". A passage that names a part ("leaves are edible") is not a
#: condition by itself; one that adds a condition to it is.
_EDIBLE_CONDITION_RE = re.compile(
    r"\bonly\b"
    r"|\b(?:edible|eaten|eat|consumed|safe)\b[^.]{0,25}?"
    r"\b(?:once|when|after|until|if|unless)\s+(?:\w+\s+){0,2}?"
    r"(?:cooked|boiled|ripe(?:ned)?|dried|processed|leached|fermented|peeled"
    r"|soaked|prepared|roasted|blanched)\b"
    r"|\b(?:must|should|needs? to|has to|have to)\s+(?:first\s+)?be\s+(?:\w+\s+)?"
    r"(?:cooked|boiled|peeled|soaked|processed|leached|removed|dried|blanched)\b"
    r"|\bin (?:small|limited|moderate) (?:amounts?|quantit(?:y|ies))"
    r"|\bin moderation\b|\blarge (?:amounts?|quantit(?:y|ies))|\bsparingly\b"
    r"|\blimited quantit"
    r"|\bcaution\b|\bwarning\b"
    r"|\bshould not\b|\bdo not (?:eat|consume)\b|\bnever (?:eat|consume)\b"
    r"|\b(?:un)?ripe\b"
    r"|\bremove (?:the )?(?:bristles|spines|glochids|seeds|skin|peel|pits?|stones?)\b"
    r"|\bpoisonous until\b",
    re.I)
#: An edibility passage that says some other part is not eaten: "the
#: remainder of the plant is poisonous", "all green parts ... are inedible".
#: That limits the parts, and is a hazard statement, but sets no condition on
#: the part that is eaten.
_EDIBLE_HAZARD_RE = re.compile(
    r"\bpoison\w*|\btoxi\w*|\bharmful\b|\bdangerous\b"
    r"|\bnot (?:be )?eaten\b|\binedible\b|\bnot edible\b|\bnon-edible\b",
    re.I)


#: A sentence about a look-alike or a comparison describes another plant:
#: "often confused with Conium maculatum (poison hemlock, rated high severity
#: on its own NC State page)" is the parsnip record talking about hemlock.
_ELSEWHERE_RE = re.compile(
    r"confused with|look-?alikes?|compar\w*|unlike\b|whereas\b|similar to", re.I)


#: Where a negation stops reaching. "(human-scoped, not a cat/dog rating)
#: gives Poison Severity Low" negates the cat tag, not the rating; a tag list
#: "#non-edible berries #problem for children" negates only its own tag.
_CLAUSE_EDGES = ".;:()#—"
#: Negations of scope rather than of harm: "states no scope", "not a pet tag".
_SCOPE_NEGATION_RE = re.compile(
    r"\b(?:no|not)\s+(?:a\s+|the\s+|any\s+)?(?:scope|cat|dog|pet)s?\b", re.I)


def _negated(text: str, start: int) -> bool:
    """Whether what follows `start` is not this plant's own hazard: the
    clause before it negates it, or the sentence is about another plant."""
    window = text[max(0, start - 60):start]
    cut = max(window.rfind(edge) for edge in _CLAUSE_EDGES)
    if cut >= 0:
        window = window[cut + 1:]
    if _NEGATION_RE.search(_SCOPE_NEGATION_RE.sub(" ", window)):
        return True
    sentence = text[max(0, start - 160):start]
    cut = sentence.rfind(". ")
    if cut >= 0:
        sentence = sentence[cut + 2:]
    return bool(_ELSEWHERE_RE.search(sentence))


@dataclass(frozen=True)
class Evidence:
    """What the cited passages say about harm to people, and about eating."""
    #: A source states a hazard to people.
    people: bool = False
    #: NC State's Poison Severity, the highest given: "high" | "medium" | "low".
    rating: str = ""
    rated_by: str = ""
    #: A source calls it highly toxic or fatal to people.
    grave: bool = False
    #: A source records it as a noxious weed.
    noxious: bool = False
    #: An edibility passage limits the parts eaten or needs preparation.
    edibility_limited: bool = False
    #: A source calls it fatal or highly toxic to pets in words of its own --
    #: the only thing besides a table that makes a pet's half "serious".
    animals_grave: bool = False
    #: A source records it as an invasive species.
    invasive: bool = False
    #: Narrower than `edibility_limited`: the passage puts a condition on the
    #: eaten part itself (cooked, ripe, in small amounts), rather than only
    #: saying the rest of the plant is not eaten.
    edibility_conditional: bool = False


_RATING_RANK = {"low": 1, "medium": 2, "moderate": 2, "high": 3}


def _ratings(text: str) -> list[str]:
    found = []
    for m in _RATING_RE.finditer(text or ""):
        if not _negated(text, m.start()):
            level = (m.group(1) or m.group(2)).lower()
            found.append("medium" if level == "moderate" else level)
    return found


def _names_people(text: str) -> tuple[bool, bool]:
    """(people named at risk, gravely) in a passage that names its subject."""
    people = grave = False
    for m in _PEOPLE_RE.finditer(text or ""):
        if _negated(text, m.start()):
            continue
        people = True
        if _GRAVE_RE.search(m.group(0)):
            grave = True
    return people, grave


def _eating_harm(text: str) -> tuple[bool, bool]:
    """(harm stated, gravely) in an edibility passage.

    An edibility passage is about people eating the plant, so a harm word in
    it is a hazard to people -- unless the clause names an animal and no
    person, as in "toxic to horses"."""
    people = grave = False
    for clause in _CLAUSES_RE.split(text or ""):
        for m in _HARM_RE.finditer(clause):
            if _negated(clause, m.start()):
                continue
            if _ANIMAL_RE.search(clause) and not _PERSON_RE.search(clause):
                continue
            people = True
            if _GRAVE_RE.search(clause):
                grave = True
    return people, grave


def _names_pets_gravely(text: str) -> bool:
    """Whether a passage calls the plant fatal or highly toxic to pets.

    A clause that names a pet and no person, with a grave word in it: "toxic
    to cats and can be fatal", "ingestion by livestock or pets may cause
    death". Not a bare "possible death" in a pet flag's citation: NC State
    quotes its human-scoped symptom list there too ("difficulty speaking"),
    and a grave word that names nobody is not the pets' to take. Nor a
    clause that mentions pets only to say it does not name them."""
    for clause in _CLAUSES_RE.split(text or ""):
        if _PERSON_RE.search(clause) or _PEOPLE_RE.search(clause):
            continue
        if not any(not _negated(clause, m.start()) and not _a_tag(clause, m)
                   for m in _PET_RE.finditer(clause)):
            continue
        if any(not _negated(clause, m.start()) for m in _GRAVE_RE.finditer(clause)):
            return True
    return False


#: NC State's pet tags -- "Problem for Cats", "the cat/dog tags" -- carry no
#: severity of their own, so a grave word beside one ("ingestion may be
#: fatal, and it is separately tagged a problem for cats") is not about pets.
_TAG_BEFORE_RE = re.compile(r"problem for\W+(?:\w+\W+){0,3}$", re.I)
_TAG_AFTER_RE = re.compile(r"^\W*(?:\w+\W+){0,1}tags?\b", re.I)


def _a_tag(text: str, match: re.Match) -> bool:
    return bool(_TAG_BEFORE_RE.search(text[max(0, match.start() - 40):match.start()])
                or _TAG_AFTER_RE.search(text[match.end():match.end() + 20]))


def _noxious(text: str) -> bool:
    return any(not _negated(text, m.start()) for m in _NOXIOUS_RE.finditer(text or ""))


def _invasive(text: str) -> bool:
    return any(not _negated(text, m.start()) for m in _INVASIVE_RE.finditer(text or ""))


def read_evidence(detail: str | None, passages: Iterable[Any] = ()) -> Evidence:
    """The facts the cited passages state about harm to people and eating.

    `detail` is the row's `toxicity_detail`; `passages` are the claim
    passages on the safety fields (`claims.store.Passage`, or anything with
    `field`, `value`, `quote` and `authority`)."""
    people = grave = noxious = limited = False
    pets_grave = invasive = conditional = False
    best_rank, best, best_by = 0, "", ""

    def rate(levels: list[str], by: str) -> None:
        nonlocal best_rank, best, best_by
        for level in levels:
            if _RATING_RANK[level] > best_rank:
                best_rank, best, best_by = _RATING_RANK[level], level, by

    if detail:
        levels = _ratings(detail)
        # "Poison Severity" is NC State's field; the restatement names it.
        rate(levels, "NC State Extension"
             if re.search(r"NC State|ncsu", detail, re.I) else "")
        named, gravely = _names_people(detail)
        people = people or named or bool(levels)
        grave = grave or gravely
        noxious = noxious or _noxious(detail)
        invasive = invasive or _invasive(detail)
        pets_grave = pets_grave or _names_pets_gravely(detail)

    for p in passages:
        quote = getattr(p, "quote", "") or ""
        kind = getattr(p, "field", "")
        if kind in ("toxic_to_pets", "toxicity_detail"):
            # The pet flag's citation is about pets unless it names people
            # outright, or carries NC State's poison block, which is the
            # page's human-scoped section.
            levels = _ratings(quote)
            rate(levels, getattr(p, "authority", "") or "")
            named, gravely = _names_people(quote)
            people = people or named or bool(levels)
            grave = grave or gravely
            pets_grave = pets_grave or _names_pets_gravely(quote)
        elif kind == "is_edible":
            named, gravely = _eating_harm(quote)
            people = people or named
            grave = grave or gravely
            if getattr(p, "value", None) is True:
                if _EDIBLE_CONDITION_RE.search(quote):
                    limited = conditional = True
                elif _EDIBLE_HAZARD_RE.search(quote):
                    limited = True
        noxious = noxious or _noxious(quote)
        invasive = invasive or _invasive(quote)

    return Evidence(people=people, rating=best, rated_by=best_by, grave=grave,
                    noxious=noxious, edibility_limited=limited,
                    animals_grave=pets_grave, invasive=invasive,
                    edibility_conditional=conditional)


# --- putting a record together ----------------------------------------------

def _highest(levels: list[str]) -> str:
    return max(levels, key=SEVERITY_ORDER.__getitem__) if levels else "unknown"


def _floor(table: str) -> list[str]:
    """A table's severity, as a floor: "moderate" and "severe" stand, and
    anything below gives way to the sources."""
    return [table] if table in ("moderate", "severe") else []


def from_legacy(toxic_to_pets: bool | None, scientific_name: str = "",
                cited_to: str = "", evidence: Evidence | None = None) -> Toxicity:
    """The flag, the tables and the cited evidence, as one record.

    A cited flag outranks the tables: an authority that says "non-toxic" is
    believed over a pattern typed into code. A stored `False` nobody cited
    is a catalog default and means 'nothing recorded' -- weaker than 'safe',
    and reported as such. `cited_to` names the authority whose claim settled
    the flag, when one did.

    Severity is worked out for each half. A table's "severe" stands -- it is
    the cautious direction -- for whoever the table names; a rating, or a
    source calling it fatal to people, raises the people's half only; a
    source's grave words about pets raise theirs."""
    evidence = evidence or Evidence()
    known = lookup(scientific_name)
    table = known
    if toxic_to_pets is False and cited_to:
        base = Toxicity(toxic=False, source="cited", cited_to=cited_to)
        if known is not None and known.edible_parts:
            # A crop stays a crop: what is eaten, and what harms the people
            # eating it, are not the pet verdict's to erase.
            table = replace(known, toxic=False,
                            at_risk=[a for a in known.at_risk if a == "humans"])
            base = replace(table, parts=list(known.parts),
                           edible_parts=list(known.edible_parts),
                           effect="", source="cited", cited_to=cited_to)
        else:
            table = None
    elif known:
        base = replace(known, parts=list(known.parts),
                       edible_parts=list(known.edible_parts),
                       at_risk=list(known.at_risk), cited_to=cited_to)
        if toxic_to_pets is True and base.toxic is not True:
            # The table speaks for people only; the flag still speaks for pets.
            base = replace(base, toxic=True, at_risk=base.at_risk + ["pets"])
    elif toxic_to_pets is True:
        # No parts: a bare flag says the plant is toxic, not which of it is.
        base = Toxicity(toxic=True, at_risk=["pets"],
                        source="catalog flag", cited_to=cited_to)
    elif toxic_to_pets is False:
        base = Toxicity(toxic=False, source="catalog (legacy flag)")
    else:
        base = Toxicity(toxic=None)

    animal_levels: list[str] = []
    if base.toxic is True:
        if (table is not None and table.toxic is True
                and any(a != "humans" for a in table.at_risk)):
            animal_levels += _floor(table.severity)
        if evidence.animals_grave:
            animal_levels.append("severe")
    people_levels: list[str] = []
    if evidence.people or "humans" in base.at_risk:
        if table is not None and "humans" in table.at_risk:
            people_levels += _floor(table.severity)
        if evidence.rating:
            people_levels.append(RATING_SEVERITY[evidence.rating])
        if evidence.grave:
            people_levels.append("severe")
    animal_severity = _highest(animal_levels)
    people_severity = _highest(people_levels)
    return replace(base, severity=_highest(animal_levels + people_levels),
                   animal_severity=animal_severity,
                   people_severity=people_severity,
                   people=evidence.people, rating=evidence.rating,
                   rated_by=evidence.rated_by)


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
_SINGULAR_LABELS = {"the sap", "the fruit", "the ripe fruit", "the unripe fruit",
                    "the pollen", "any green skin on the tubers"}


def _verb(label: str) -> str:
    return "is" if label in _SINGULAR_LABELS else "are"


def _pronoun(label: str) -> str:
    return "it" if label in _SINGULAR_LABELS else "they"


def _capital(text: str) -> str:
    return text[:1].upper() + text[1:]


def _labels(parts: list[str]) -> str:
    return _join([PART_LABELS.get(p, p) for p in parts])


def _rating_sentence(tox: Toxicity) -> str:
    """The rating on its own, saying whose it is: NC State rates people."""
    if not tox.rating:
        return ""
    if tox.rated_by:
        return f"{tox.rated_by} rates its poison severity for people {tox.rating}."
    return f"Its poison severity for people is rated {tox.rating}."


def _rating_tail(tox: Toxicity, whose: str = "its") -> str:
    """The rating after a clause that already names people."""
    if not tox.rating:
        return ""
    if tox.rated_by:
        return f": {tox.rated_by} rates {whose} poison severity {tox.rating}"
    return f": {whose} poison severity is rated {tox.rating}"


def _toxic_words(severity: str) -> str:
    return {"severe": "seriously toxic", "mild": "mildly toxic"}.get(severity, "toxic")


def _short_words(severity: str) -> str:
    """A list row's words: serious or not, never "mildly", which a row too
    short to say whose rating it is would let a reader take as all-clear."""
    return "seriously toxic" if severity == "severe" else "toxic"


def _who(tox: Toxicity, animals: list[str], people: bool,
         words=_toxic_words) -> str:
    """'toxic to cats and dogs', 'toxic to pets and people', or, when the
    two halves differ, each with its own words: 'seriously toxic to people,
    and toxic to pets'. The worse half leads when it is the people's."""
    animal_words = words(tox.animal_severity)
    people_words = words(tox.people_severity)
    if animals and people:
        if animal_words == people_words:
            return f"{animal_words} to {_join(animals + [tox.people_label])}"
        animal_part = f"{animal_words} to {_join(animals)}"
        people_part = f"{people_words} to {tox.people_label}"
        if tox.people_severity == "severe" and tox.animal_severity != "severe":
            return f"{people_part}, and {animal_part}"
        return f"{animal_part}, and {people_part}"
    if animals:
        return f"{animal_words} to {_join(animals)}"
    return f"{people_words} to {tox.people_label}"


def _action(tox: Toxicity, *, animals: bool, people: bool,
            trimmings: bool = False) -> str:
    """What to do about it: keep it out of reach, and who to call."""
    severe = tox.severity == "severe"
    keep = ("Keep trimmings out of reach of pets and children."
            if trimmings else "Keep it out of reach of pets and children.")
    if people:
        call = (f"If you suspect poisoning, call {POISON_CONTROL}"
                + (f", {LOCAL_POISON_CENTRE} or a vet" if animals
                   else f" or {LOCAL_POISON_CENTRE}")
                + " right away.")
        return call if severe and not trimmings else f"{keep} {call}"
    if severe:
        call = ("If you think a pet ate some, contact a vet right away. "
                "Do not wait for symptoms.")
        return f"{keep} {call}" if trimmings else call
    return keep


def _pets_source(tox: Toxicity) -> str:
    """Whose verdict the pets' half is, when an authority's claim settled it.

    The people's rating already names who gave it, and a "records no
    toxicity" names who recorded that. A pet verdict of "toxic" named no
    one, so the source was true of the page (its Sources card) but not of
    the sentence. Said as the source rather than as "it is toxic to pets",
    because on a crop "it" would read as the fruit just called food, and
    the lead has already said which parts and which animals."""
    if tox.toxic is True and tox.cited_to:
        return f"For pets, the source is {tox.cited_to}."
    return ""


def _pets_unrecorded(tox: Toxicity) -> str:
    """What is on record for pets when nothing says they are at risk."""
    if tox.toxic is None:
        return ("No verdict on pets is recorded yet, so treat it as unknown "
                "for them, not safe.")
    if tox.cited_to:
        return (f"{tox.cited_to} records no toxicity to pets, which is not a "
                "guarantee of safety.")
    return ("No toxicity to pets is recorded in our sources yet, which is not "
            "a guarantee of safety.")


def describe(tox: Toxicity, common_name: str = "This plant") -> str:
    """A few short, plain sentences a caretaker can act on.

    Leads with what is eaten when a table knows a food crop's eaten part,
    because that is the case a flat label gets wrong and the reason people
    stop trusting warnings. Names people whenever a source records a hazard
    to them, and takes how bad it is from the source -- for people. Pets get
    a severity word only from a table or a source's own grave words about
    them. Each verdict says whose it is: the pets' source, the people's
    rating, or that nobody is on record."""
    name = common_name.lower()
    people = tox.people_at_risk
    animals = tox.animals_at_risk

    if not animals and not people:
        if tox.toxic is None:
            # "No information" would be untrue of a row whose cited
            # description of harm sits server-side with no verdict yet
            # (ADR 0003 keeps the passage there). What is missing is the
            # verdict.
            return (
                f"No toxicity verdict recorded for {name} yet — treat it as "
                f"unknown rather than safe, and keep it away from pets that "
                f"chew plants."
            )
        if tox.cited_to:
            # An authority said so. "Nothing noted" would undersell that.
            return (
                f"{tox.cited_to} records no toxicity to pets for {name}. That "
                f"is not a guarantee of safety — keep it away from pets that "
                f"chew plants."
            )
        # A catalog default, not a verdict: nobody is on record saying it.
        return (
            f"No toxicity is recorded for {name} in our sources yet. That is "
            f"not a guarantee of safety — keep it away from pets that chew "
            f"plants."
        )

    warn = "⚠️ " if tox.severity == "severe" else ""
    # People join the animals' clause when the table names them, or when
    # nothing more specific is said: "toxic to pets and people". When the
    # table carries an animal-specific effect -- a cat's kidneys -- people
    # get their own sentence, so the effect is not read as theirs.
    people_in_clause = people and (
        not animals or "humans" in tox.at_risk or not tox.effect)
    who = _who(tox, animals, people_in_clause)
    toxic_parts = _labels(tox.parts)
    agent = f" ({tox.agent})" if tox.agent else ""
    effect = f" — {tox.effect}" if tox.effect else ""
    # The peanut case: the part eaten is itself the hazard, to some people.
    eaten_is_hazard = tox.is_contradictory and set(tox.parts) == set(tox.edible_parts)

    if tox.is_contradictory:
        # The crop first: say what is eaten before what is not, so the
        # reader's own experience ("I eat tomatoes") is confirmed, not
        # contradicted.
        eaten = _labels(tox.edible_parts)
        if eaten_is_hazard:
            lead = (f"{warn}{_capital(eaten)} {_verb(eaten)} the crop, and "
                    f"{_pronoun(eaten)} {_verb(eaten)} {who}{agent}{effect}.")
        else:
            lead = (f"{warn}{_capital(eaten)} {_verb(eaten)} the crop; "
                    f"{toxic_parts} {_verb(toxic_parts)} {who}{agent}{effect}.")
    else:
        parts = f": {toxic_parts}" if toxic_parts else ""
        lead = f"{warn}{_capital(who)}{parts}{agent}{effect}."

    sentences = [lead]
    if animals and _pets_source(tox):
        sentences.append(_pets_source(tox))
    if people and not people_in_clause:
        # Its own sentence, with the rating inside it: NC State's rating is
        # for people, and beside a cat's kidney failure it must not read as
        # the cat's. On a crop the subject is the parts, never "it", which
        # would read as the fruit just called food.
        if tox.is_contradictory:
            subject = f"{_capital(toxic_parts)} {_verb(toxic_parts)}"
            whose = "the plant's"
        else:
            subject, whose = "It is", "its"
        sentences.append(
            f"{subject} also {_toxic_words(tox.people_severity)} to "
            f"{tox.people_label}{_rating_tail(tox, whose)}.")
    elif people and tox.rating:
        sentences.append(_rating_sentence(tox))
    if not animals:
        sentences.append(_pets_unrecorded(tox))
    sentences.append(_action(
        tox, animals=bool(animals), people=people,
        trimmings=tox.is_contradictory and not eaten_is_hazard))
    return " ".join(sentences)


def hazard_line(tox: Toxicity) -> str | None:
    """One short caution for a list row: who it is toxic to. None when no
    hazard is recorded -- which is "no record", never "safe", and the list
    row is not the place to say so at length. A rating's "serious" is the
    people's, as in the sentence."""
    animals, people = tox.animals_at_risk, tox.people_at_risk
    if not animals and not people:
        return None
    return f"{_capital(_who(tox, animals, people, words=_short_words))}."


def never_put_forward(tox: Toxicity, evidence: Evidence) -> bool:
    """Whether a growing area should never suggest planting this.

    A source rating it a high-severity poison for people, or calling it
    fatal to them, or a source recording it as a noxious weed or an invasive
    species. A Candidate is a recommendation, and nobody should be
    recommended poison hemlock for a sunny bed because its size and sun
    happen to fit, or Chinese wisteria for a fence because NC State's own
    page says it escapes. fit.never_a_candidate keeps food crops whose eaten
    part a table names."""
    if evidence.noxious or evidence.invasive:
        return True
    return tox.people_at_risk and (tox.rating == "high" or evidence.grave)


def edibility_note(is_edible: bool | None, tox: Toxicity,
                   evidence: Evidence) -> str | None:
    """The condition on "grown to eat", or None when there is none.

    A food crop's note names the part eaten and the parts that are not, the
    same parts its toxicity sentence names, so the two never disagree. Any
    other plant recorded as eaten gets one when it is also recorded as
    poisonous to people, or when the cited edibility passage limits the
    parts or needs preparation ("edible when cooked", "only the ripe
    fruit") -- and then it sends the reader to the source, since the passage
    stays on the server (ADR 0003). A hazard to pets alone is a reason to
    keep scraps from the dog, not to doubt the orange."""
    if is_edible is not True:
        return None
    pets = tox.toxic is True
    people = tox.people_at_risk
    if tox.is_crop:
        eaten = _labels(tox.edible_parts)
        if set(tox.parts) == set(tox.edible_parts):
            note = (f"{_capital(eaten)} {_verb(eaten)} eaten, but not by "
                    f"{tox.people_label}.")
        else:
            harmful = _labels(tox.parts)
            note = (f"{_capital(eaten)} {_verb(eaten)} eaten; {harmful} "
                    f"{_verb(harmful)} not.")
        if evidence.edibility_conditional:
            note += (f" Check the source for how {_pronoun(eaten)} "
                     f"{_verb(eaten)} prepared.")
        return note
    limited = evidence.edibility_limited
    check = "Check the source before eating any of it."
    pet_scraps = ("it is recorded as poisonous to pets, so keep scraps and "
                  "trimmings away from them.")
    if people and limited:
        return ("Some parts are eaten, but only certain parts or after "
                f"preparation, and other parts are poisonous. {check}")
    if people:
        return ("Some parts are eaten, but it is also recorded as poisonous "
                f"to people. {check}")
    if limited:
        note = ("Some parts are eaten, but only certain parts or after "
                f"preparation. {check}")
        return f"{note} {_capital(pet_scraps)}" if pets else note
    if pets:
        return f"Some parts are eaten, and {pet_scraps}"
    return None


# --- a catalog row ------------------------------------------------------------

@dataclass(frozen=True)
class Safety:
    toxicity: Toxicity
    evidence: Evidence


def _passages_for(species: Any) -> list:
    """The species' own cited safety passages, when it sits in a session.

    A row built in code, or one whose session is gone, has none to offer,
    and is described from its columns alone -- the flag, the detail and the
    tables -- which is what the sentence was before the passages were read."""
    try:
        from sqlalchemy.exc import SQLAlchemyError
        from sqlalchemy.orm import object_session
        session = object_session(species)
    except Exception:  # not a mapped instance
        return []
    if session is None:
        return []
    from app.data.claims.store import safety_passages
    subject = (getattr(species, "scientific_name_accepted", None)
               or getattr(species, "scientific_name", "") or "")
    try:
        return safety_passages(session, subject)
    except SQLAlchemyError:
        # A session mid-failure must not 500 a species list over a warning
        # it can still give from the row's own columns.
        return []


def safety_of(species: Any) -> Safety:
    """The toxicity record and the evidence behind it, for a catalog row."""
    evidence = read_evidence(getattr(species, "toxicity_detail", None),
                             _passages_for(species))
    tox = from_legacy(
        species.toxic_to_pets, species.scientific_name,
        cited_to=cited_authority(species.care_provenance, species.care_sources),
        evidence=evidence)
    return Safety(toxicity=tox, evidence=evidence)


def describe_for_species(scientific_name: str, common_name: str,
                         toxic_to_pets: bool | None, cited_to: str = "",
                         detail: str | None = None,
                         passages: Iterable[Any] = ()) -> str:
    """Best available sentence for a flag, a name and whatever evidence is
    to hand. Catalog rows go through `safety_of`; this is the same thing for
    callers holding the pieces."""
    evidence = read_evidence(detail, passages)
    return describe(from_legacy(toxic_to_pets, scientific_name, cited_to, evidence),
                    common_name)
