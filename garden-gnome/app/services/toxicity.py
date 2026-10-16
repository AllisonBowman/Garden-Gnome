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

This module is descriptive, not veterinary or medical advice: serious cases
say to call Poison Control or a vet rather than implying the app can triage.
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
    # and who published it. Empty when no source rates it.
    rating: str = ""
    rated_by: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

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
_NOXIOUS_RE = re.compile(r"\bnoxious weed", re.I)
_CLAUSES_RE = re.compile(r"[.!?;\n]+")

#: An edibility passage that limits what is eaten or how: "edible when
#: cooked", "only the ripe fruit", "in small amounts", "the remainder of the
#: plant is poisonous". A passage that names a part ("leaves are edible") is
#: not a limit by itself; one that adds a condition to it is.
_EDIBLE_LIMIT_RE = re.compile(
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
    r"|\bpoison\w*|\btoxi\w*|\bcaution\b|\bwarning\b|\bharmful\b|\bdangerous\b"
    r"|\bnot (?:be )?eaten\b|\bshould not\b|\bdo not (?:eat|consume)\b"
    r"|\bnever (?:eat|consume)\b|\binedible\b|\bnot edible\b|\bnon-edible\b"
    r"|\b(?:un)?ripe\b"
    r"|\bremove (?:the )?(?:bristles|spines|glochids|seeds|skin|peel|pits?|stones?)\b"
    r"|\bpoisonous until\b",
    re.I)


#: A sentence about a look-alike or a comparison describes another plant:
#: "often confused with Conium maculatum (poison hemlock, rated high severity
#: on its own NC State page)" is the parsnip record talking about hemlock.
_ELSEWHERE_RE = re.compile(
    r"confused with|look-?alikes?|compar\w*|unlike\b|whereas\b|similar to", re.I)


def _negated(text: str, start: int) -> bool:
    """Whether what follows `start` is not this plant's own hazard: the
    clause before it negates it, or the sentence is about another plant."""
    window = text[max(0, start - 60):start]
    cut = max(window.rfind("."), window.rfind(";"))
    if cut >= 0:
        window = window[cut + 1:]
    if _NEGATION_RE.search(window):
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


def _noxious(text: str) -> bool:
    return any(not _negated(text, m.start()) for m in _NOXIOUS_RE.finditer(text or ""))


def read_evidence(detail: str | None, passages: Iterable[Any] = ()) -> Evidence:
    """The facts the cited passages state about harm to people and eating.

    `detail` is the row's `toxicity_detail`; `passages` are the claim
    passages on the safety fields (`claims.store.Passage`, or anything with
    `field`, `value`, `quote` and `authority`)."""
    people = grave = noxious = limited = False
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
        elif kind == "is_edible":
            named, gravely = _eating_harm(quote)
            people = people or named
            grave = grave or gravely
            if getattr(p, "value", None) is True and _EDIBLE_LIMIT_RE.search(quote):
                limited = True
        noxious = noxious or _noxious(quote)

    return Evidence(people=people, rating=best, rated_by=best_by, grave=grave,
                    noxious=noxious, edibility_limited=limited)


# --- putting a record together ----------------------------------------------

def _severity(table: str, evidence: Evidence) -> str:
    """The table's own severity, raised -- never lowered -- by the sources.

    A table's "severe" stands: it is the cautious direction. Anything a
    table says below that gives way to a cited rating, and a source calling
    it fatal to people makes it severe whatever the rating."""
    levels = [table] if table in ("moderate", "severe") else []
    if evidence.rating:
        levels.append(RATING_SEVERITY[evidence.rating])
    if evidence.grave:
        levels.append("severe")
    return max(levels, key=SEVERITY_ORDER.__getitem__) if levels else "unknown"


def from_legacy(toxic_to_pets: bool | None, scientific_name: str = "",
                cited_to: str = "", evidence: Evidence | None = None) -> Toxicity:
    """The flag, the tables and the cited evidence, as one record.

    A cited flag outranks the tables: an authority that says "non-toxic" is
    believed over a pattern typed into code. A stored `False` nobody cited
    is a catalog default and means 'nothing recorded' -- weaker than 'safe',
    and reported as such. `cited_to` names the authority whose claim settled
    the flag, when one did."""
    evidence = evidence or Evidence()
    known = lookup(scientific_name)
    if toxic_to_pets is False and cited_to:
        base = Toxicity(toxic=False, source="cited", cited_to=cited_to)
    elif known:
        base = replace(known, parts=list(known.parts),
                       edible_parts=list(known.edible_parts),
                       at_risk=list(known.at_risk), cited_to=cited_to)
    elif toxic_to_pets is True:
        # No parts: a bare flag says the plant is toxic, not which of it is.
        base = Toxicity(toxic=True, at_risk=["pets"],
                        source="catalog flag", cited_to=cited_to)
    elif toxic_to_pets is False:
        base = Toxicity(toxic=False, source="catalog (legacy flag)")
    else:
        base = Toxicity(toxic=None)
    return replace(base, severity=_severity(base.severity, evidence),
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
_SINGULAR_LABELS = {"the sap", "the fruit", "the ripe fruit", "the pollen",
                    "any green skin on the tubers"}


def _verb(label: str) -> str:
    return "is" if label in _SINGULAR_LABELS else "are"


def _capital(text: str) -> str:
    return text[:1].upper() + text[1:]


def _rating_sentence(tox: Toxicity) -> str:
    if not tox.rating:
        return ""
    if tox.rated_by:
        return f"{tox.rated_by} rates it {tox.rating} severity."
    return f"Its poison severity is rated {tox.rating}."


def _toxic_words(severity: str) -> str:
    return {"severe": "seriously toxic", "mild": "mildly toxic"}.get(severity, "toxic")


def _action(tox: Toxicity, *, animals: bool, people: bool,
            trimmings: bool = False) -> str:
    """What to do about it: keep it out of reach, and who to call."""
    severe = tox.severity == "severe"
    keep = ("Keep trimmings out of reach of pets and children."
            if trimmings else "Keep it out of reach of pets and children.")
    if people:
        call = (f"If you suspect poisoning, call {POISON_CONTROL}"
                + (" or a vet" if animals else "") + " right away.")
        return call if severe and not trimmings else f"{keep} {call}"
    if severe:
        call = ("If you think a pet ate some, contact a vet right away. "
                "Do not wait for symptoms.")
        return f"{keep} {call}" if trimmings else call
    return keep


def describe(tox: Toxicity, common_name: str = "This plant") -> str:
    """Two to four plain sentences a caretaker can act on.

    Leads with the distinction when a plant is both edible and toxic, because
    that is the case a flat label gets wrong and the reason people stop
    trusting warnings. Names people whenever a source records a hazard to
    them, and takes how bad it is from the source."""
    name = common_name.lower()
    people = tox.people_at_risk

    if tox.toxic is not True and not people:
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
    words = _toxic_words(tox.severity)

    if tox.toxic is not True:
        # A hazard to people, and none recorded (or none known) to pets.
        sentences = [f"{warn}{_capital(words)} to people."]
        rating = _rating_sentence(tox)
        if rating:
            sentences.append(rating)
        if tox.toxic is None:
            sentences.append("No verdict on pets is recorded yet, so treat it "
                             "as unknown for them, not safe.")
        elif tox.cited_to:
            sentences.append(f"{tox.cited_to} records no toxicity to pets, "
                             "which is not a guarantee of safety.")
        else:
            sentences.append("No toxicity to pets is recorded in our sources "
                             "yet, which is not a guarantee of safety.")
        sentences.append(_action(tox, animals=False, people=True))
        return " ".join(sentences)

    animals = tox.animals_at_risk
    # People join the list when the table names them, or when nothing more
    # specific is said: "toxic to pets and people". When the table carries
    # an animal-specific effect -- a cat's kidneys -- people get their own
    # sentence, so the effect is not read as theirs.
    people_in_clause = "humans" in tox.at_risk or (people and not tox.effect)
    who = _join(animals + (["people"] if people_in_clause else []))
    toxic_parts = _join([PART_LABELS.get(p, p) for p in tox.parts])
    agent = f" ({tox.agent})" if tox.agent else ""
    effect = f" — {tox.effect}" if tox.effect else ""

    if tox.is_contradictory:
        # The contradictory case first: say what is eaten before what is not,
        # so the reader's own experience ("I eat tomatoes") is confirmed, not
        # contradicted.
        eaten = _join([PART_LABELS.get(p, p) for p in tox.edible_parts])
        lead = (f"{warn}{_capital(eaten)} {_verb(eaten)} eaten, but "
                f"{toxic_parts} {_verb(toxic_parts)} {words} to "
                f"{who}{agent}{effect}.")
    else:
        parts = f": {toxic_parts}" if toxic_parts else ""
        lead = f"{warn}{_capital(words)} to {who}{parts}{agent}{effect}."

    sentences = [lead]
    if people and not people_in_clause:
        # Its own sentence, with the rating inside it: NC State's rating is
        # for people, and beside a cat's kidney failure it must not read as
        # the cat's.
        by = f" by {tox.rated_by}" if tox.rated_by else ""
        sentences.append(
            f"It is also poisonous to people, rated {tox.rating} severity{by}."
            if tox.rating else "It is also poisonous to people.")
    elif tox.rating:
        sentences.append(_rating_sentence(tox))
    sentences.append(_action(tox, animals=True, people=people,
                             trimmings=tox.is_contradictory))
    return " ".join(sentences)


def hazard_line(tox: Toxicity) -> str | None:
    """One short caution for a list row: who it is toxic to. None when no
    hazard is recorded -- which is "no record", never "safe", and the list
    row is not the place to say so at length."""
    who = tox.animals_at_risk + (["people"] if tox.people_at_risk else [])
    if not who:
        return None
    words = "Seriously toxic" if tox.severity == "severe" else "Toxic"
    return f"{words} to {_join(who)}."


def never_put_forward(tox: Toxicity, evidence: Evidence) -> bool:
    """Whether a growing area should never suggest planting this.

    A source rating it a high-severity poison for people, or calling it
    fatal to them, or a source recording it as a noxious weed. A Candidate
    is a recommendation, and nobody should be recommended poison hemlock
    for a sunny bed because its size and sun happen to fit."""
    if evidence.noxious:
        return True
    return tox.people_at_risk and (tox.rating == "high" or evidence.grave)


def edibility_note(is_edible: bool | None, tox: Toxicity,
                   evidence: Evidence) -> str | None:
    """The condition on "grown to eat", or None when there is none.

    Set when a plant recorded as eaten is also recorded as poisonous -- to
    pets or to people -- or when the cited edibility passage limits the
    parts or needs preparation ("edible when cooked", "only the ripe
    fruit"). The passage stays on the server (ADR 0003); the note says that
    there is a condition and sends the reader to the source for it."""
    if is_edible is not True:
        return None
    pets = tox.toxic is True
    people = tox.people_at_risk
    limited = evidence.edibility_limited
    check = "Check the source before eating any of it."
    if (pets or people) and limited:
        return ("Some parts are eaten, but only certain parts or after "
                f"preparation, and other parts are poisonous. {check}")
    if pets or people:
        who = _join((["pets"] if pets else []) + (["people"] if people else []))
        return (f"Some parts are eaten, but it is also recorded as poisonous "
                f"to {who}. {check}")
    if limited:
        return ("Some parts are eaten, but only certain parts or after "
                f"preparation. {check}")
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
