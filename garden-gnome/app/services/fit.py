"""Does this species belong in this growing area?

Two questions, one answer shape. Forward: which species suit a space, so the
app can put candidates forward. Backward: how does a plant already standing
there fail to suit it, so the caretaker knows what to address. Both are the
same comparison read in opposite directions, which is why they are one module.

Pure, like `claims.resolve`: it takes a Species row and a GrowingArea row and
returns findings. No session, no queries, no I/O — the router does the fetching
and this does the judging, so the rules can be tested against constructed rows
and read without a database in your head.

THE RULE THE WHOLE THING RESTS ON
---------------------------------
`unknown` is not a pass. A species the catalog says nothing about on an axis
gets `unknown` there, and `unknown` never becomes a fit, never scores, and
never ranks a plant higher. This is the same discipline the rest of the
catalog already keeps -- a null `toxic_to_pets` is "no record", never "safe"
(ADR 0002) -- applied to space instead of harm. The failure it prevents is
concrete: read a missing mature height as "fits anywhere" and the app cheerfully
recommends a forty-foot tulip tree for a kitchen windowsill.

A borrowed value is still an answer, but a labelled one. Where the resolver
filled a field from the genus, the finding says so (ADR 0002), because "most
Hostas are this size" is a different sentence from "this Hosta is".

ENUMS ARRIVE SPELLED TWO WAYS
-----------------------------
A row loaded from the table carries enum members; a row built in code carries
raw strings, because table models do not validate on construction. Every
comparison below therefore goes through `care_facts.token`, which is the
existing answer to this and not a new one. Comparing an unwrapped member
against a string silently takes the else branch — a `SoilBase.garden_bed`
tested against `"garden_bed"` is not equal, and the plant that belonged in
the bed gets reported as a misfit.

WHAT IS DELIBERATELY NOT HERE
-----------------------------
Cold. Whether a plant survives a winter outdoors in a particular place is not
answerable from what this system holds: `outdoor_temp_min_f` has no rows, USDA
PLANTS is the only authority scoped to write it, and hardiness zones were
deliberately never mapped onto the temperature columns (ADR 0006). The only
temperature signal available is a ten-day forecast, which the advisor already
turns into per-plant nudges (`advisor._weather_nudges`). Answering "will this
survive here" from a ten-day forecast would be exactly the arithmetic-on-top-
of-misattribution ADR 0006 rejected, so this module does not answer it at all.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional

from app.models.models import (
    GrowingArea, GrowingGoal, GrowingSurface, Species, SunExposure,
    TempExposure,
)
from app.services.care_facts import length_said, token
from app.services.toxicity import cited_authority

#: Appended to a finding drawn from a value the resolver borrowed from the
#: genus. Mirrors care_facts.GENUS_LABEL in intent: a reader must never have to
#: guess whether a fact was said about this species or its cousins.
BORROWED_LABEL = " (from the genus, not this species)"


class Verdict(str, Enum):
    fits = "fits"
    misfits = "misfits"
    unknown = "unknown"


class Axis(str, Enum):
    """The comparisons the catalog can actually back, in reading order."""
    indoor_outdoor = "indoor_outdoor"
    sun = "sun"
    soil = "soil"
    footprint = "footprint"
    upkeep = "upkeep"
    goal = "goal"


@dataclass(frozen=True)
class Finding:
    """One axis's verdict, the sentence a person reads for it, and who said so."""
    axis: Axis
    verdict: Verdict
    sentence: str
    borrowed: bool = False
    #: The authorities whose pages settled, for this species itself, a value
    #: the finding rests on. It is what lets a misfit read as "NC State
    #: Extension records it for part shade" rather than as the app's opinion.
    #: Empty where nothing about this species was cited -- an unknown, or a
    #: value only the genus answered, since a genus page does not speak for
    #: the species (ADR 0002, `cited_authority`); `borrowed` says that part.
    authorities: tuple[str, ...] = ()
    #: Which of the gardener's goals this finding answers, where it answers
    #: one. Edible and pollinators share the `goal` axis, and a client that
    #: says "nothing here was checked for edibility" has to know which is
    #: which; low upkeep has an axis of its own and is tagged all the same.
    goal: Optional[str] = None


def _borrowed(species: Species, *fields: str) -> bool:
    provenance = species.care_provenance or {}
    return any(provenance.get(f) == "genus_inferred" for f in fields)


def _authorities(species: Species, *fields: str) -> tuple[str, ...]:
    names: list[str] = []
    for field in fields:
        name = cited_authority(species.care_provenance, species.care_sources, field)
        if name and name not in names:
            names.append(name)
    return tuple(names)


def _finding(axis: Axis, verdict: Verdict, sentence: str,
             species: Species, *fields: str, goal: Optional[str] = None) -> Finding:
    """A finding resting on `fields` -- only the ones its sentence actually
    used. A borrowed field the sentence never mentions must not label it,
    the same rule the care facts keep (mobile `careFactRows`)."""
    borrowed = _borrowed(species, *fields)
    return Finding(axis, verdict, sentence + (BORROWED_LABEL if borrowed else ""),
                   borrowed, _authorities(species, *fields), goal)


def _unknown(axis: Axis, sentence: str, goal: Optional[str] = None) -> Finding:
    return Finding(axis, Verdict.unknown, sentence, False, (), goal)


# --- indoor / outdoor ------------------------------------------------------
# The coarsest axis and by far the best covered: 474 of 600 researched records
# carry a cited `is_houseplant`. It answers "can this live here at all" before
# any of the finer comparisons are worth making.

def _indoor_outdoor(species: Species, area: GrowingArea) -> Finding:
    axis = Axis.indoor_outdoor
    if species.is_houseplant is None:
        return _unknown(axis, "No source says whether this is grown indoors.")

    indoors = token(area.temp_exposure) == TempExposure.indoor.value
    if species.is_houseplant and indoors:
        return _finding(axis, Verdict.fits, "Grown indoors, and this spot is indoors.",
                        species, "is_houseplant")
    if species.is_houseplant and not indoors:
        # Not a misfit. Plenty of houseplants summer outdoors; the sources say
        # it is grown indoors, not that it cannot go out, and asserting the
        # stronger claim from the weaker evidence is the whole failure mode.
        return _unknown(
            axis,
            "Sources describe this as a houseplant; none says whether it can "
            "live outdoors here.")
    if not species.is_houseplant and indoors:
        return _finding(
            axis, Verdict.misfits,
            "An outdoor plant, and this spot is indoors.", species, "is_houseplant")
    return _finding(axis, Verdict.fits, "An outdoor plant, and this spot is outdoors.",
                    species, "is_houseplant")


# --- sun -------------------------------------------------------------------
# `SunExposure` (the area) and `OutdoorSunExposure` (the species) are two
# scales of the SAME quantity -- hours of direct sun -- which is what makes
# comparing them legitimate. `light_need` and `light_fc_*` measure something
# else entirely: interior light intensity. Mapping intensity onto duration is
# what made 77% of the old import claim `direct` (models.OutdoorSunExposure),
# so nothing below ever reads `light_need`, not even as a fallback.

#: Which species sun tokens are satisfied by an area's own band. Keyed by the
#: enum's VALUE, so a member and a raw string land on the same entry.
_SUN_OK: dict[str, set[str]] = {
    SunExposure.full_sun.value:    {"full_sun", "part_sun"},
    SunExposure.partial_sun.value: {"part_sun", "part_shade"},
    SunExposure.shade.value:       {"part_shade", "full_shade"},
}

_SUN_WORDS = {
    "full_sun": "full sun", "part_sun": "part sun",
    "part_shade": "part shade", "full_shade": "full shade",
}

_AREA_SUN_WORDS = {
    SunExposure.full_sun.value: "6+ hours of direct sun",
    SunExposure.partial_sun.value: "3-6 hours of direct sun",
    SunExposure.shade.value: "under 3 hours of direct sun",
}


def _sun(species: Species, area: GrowingArea) -> Finding:
    axis = Axis.sun
    area_sun = token(area.sun_exposure)
    here = _AREA_SUN_WORDS[area_sun]

    if token(area.temp_exposure) == TempExposure.indoor.value:
        # Indoors the catalog is nearly silent. `light_fc_min` is cited on 3%
        # of rows, and the legacy `light_need` column is the known-bad one.
        # Saying "we cannot tell" is the honest answer and the useful one --
        # it stops the indoor case masquerading as a thin but confident list.
        if species.light_fc_min is None:
            return _unknown(
                axis,
                "Indoor light isn't comparable yet: no source gives this "
                "species a light level in footcandles.")
        return _finding(
            axis, Verdict.unknown,
            f"Wants at least {species.light_fc_min:g} footcandles; nothing "
            "measures how bright this spot actually is.",
            species, "light_fc_min")

    tokens = [token(t) for t in (species.outdoor_sun_exposure or [])]
    if not tokens:
        return _unknown(axis, "No source gives this species an outdoor sun range.")

    wanted = ", ".join(_SUN_WORDS.get(t, t.replace("_", " ")) for t in tokens)
    if set(tokens) & _SUN_OK[area_sun]:
        return _finding(axis, Verdict.fits, f"Recorded for {wanted}; this spot gets {here}.",
                        species, "outdoor_sun_exposure")
    return _finding(axis, Verdict.misfits,
                    f"This spot gets {here}; sources record it for {wanted}.",
                    species, "outdoor_sun_exposure")


# --- soil ------------------------------------------------------------------
# What the species wants to root in, against what the surface can give it.
# Only the contradictions worth acting on are flagged: a bed cannot be given a
# specialist potting mix, and a pot is not open ground.

_BEDS = {GrowingSurface.in_ground_bed.value, GrowingSurface.raised_bed.value}
_POTS = {GrowingSurface.containers.value, GrowingSurface.windowsill.value,
         GrowingSurface.shelf_or_floor.value, GrowingSurface.hanging.value,
         GrowingSurface.greenhouse_bench.value}

_SOIL_WORDS = {
    "standard_potting": "standard potting mix", "chunky_aroid": "a chunky aroid mix",
    "cactus_succulent": "a cactus and succulent mix", "ericaceous": "ericaceous soil",
    "orchid_bark": "orchid bark", "african_violet": "African violet mix",
    "semi_hydro": "semi-hydroponics", "garden_bed": "garden soil",
}


def _soil(species: Species, area: GrowingArea) -> Finding:
    axis = Axis.soil
    base = species.soil_base
    if area.surface is None:
        return _unknown(axis, "This area hasn't said what plants sit in.")
    if base is None:
        return _unknown(axis, "No source gives this species a growing medium.")

    base = token(base)
    wants = _SOIL_WORDS.get(base, base.replace("_", " "))
    surface = token(area.surface)

    if surface == GrowingSurface.pond_or_water.value:
        if base == "semi_hydro":
            return _finding(axis, Verdict.fits, "Grown in water, and so is this spot.",
                            species, "soil_base")
        return _finding(axis, Verdict.misfits,
                        f"This spot is water; this species wants {wants}.",
                        species, "soil_base")

    if surface in _BEDS:
        if base == "garden_bed":
            return _finding(axis, Verdict.fits, "Wants garden soil, which is what a bed is.",
                            species, "soil_base")
        # A bed is the soil it is. A specialist mix can be worked into a
        # raised bed but not into open ground, and either way it is a job, so
        # it is worth saying rather than scoring as a fit.
        return _finding(
            axis, Verdict.misfits,
            f"A bed gives it garden soil; this species wants {wants}.",
            species, "soil_base")

    if surface in _POTS:
        if base == "garden_bed":
            return _finding(
                axis, Verdict.misfits,
                f"Sources put this in open garden soil, not a container.",
                species, "soil_base")
        return _finding(axis, Verdict.fits, f"Wants {wants}, which a container can give it.",
                        species, "soil_base")

    return _unknown(axis, "This area hasn't said what plants sit in.")


# --- footprint -------------------------------------------------------------
# The axis the fit feature needed a research pass for: until the size backfill
# no record carried a mature size. Where one is still missing this returns
# `unknown` -- visibly, rather than silently passing the species through.
#
# A climber (0020) is compared the same way with a different meaning. Its
# height is reach -- how far it runs given support -- so a 40 ft wisteria
# against 7 ft of headroom is still a misfit, but the sentence says what that
# means for a vine: it will need a support and cutting back, every year.

def _ground_sqft(spread_in: float) -> float:
    """The ground a plant of this spread claims, in square feet: a square its
    own width on a side, the way plants are spaced at their mature spread.

    Compared with the area's square feet, and nothing else. The area alone
    cannot tell a 4 x 8 bed from a square one, so this catches the case that
    matters -- a plant that needs more ground than the space has -- and can
    still pass a spreader that overhangs a long, narrow bed. That is also why
    the sentence states only the two numbers somebody gave, the spread and the
    square feet, and never a width: "a space about 5.7 ft wide" was the square
    root of 32, a dimension nobody measured."""
    return (spread_in / 12) ** 2


def _footprint(species: Species, area: GrowingArea) -> Finding:
    axis = Axis.footprint
    height = species.mature_height_in_max
    spread = species.mature_spread_in_max

    climber = species.climbs is True
    if height is None and spread is None:
        if climber:
            return _unknown(axis, "A climber, but no source says how far it climbs.")
        return _unknown(axis, "No source gives this species a mature size yet.")

    # Each clause carries the field it was read from, so the finding is
    # labelled and credited by the measurements its sentence actually states:
    # a height-only misfit is not "from the genus" because the spread was.
    problems: list[tuple[str, str]] = []
    fits: list[tuple[str, str]] = []
    rises = "climbs to" if climber else "reaches"
    if height is not None and area.headroom_in is not None:
        tall, above = length_said(height), length_said(area.headroom_in)
        if height > area.headroom_in:
            problems.append((f"{rises} {tall} and there is {above} of headroom",
                             "mature_height_in_max"))
        else:
            fits.append((f"{rises} {tall}, under the {above} here",
                         "mature_height_in_max"))
    if spread is not None and area.area_sqft is not None:
        room = _sqft(area.area_sqft)
        if _ground_sqft(spread) > area.area_sqft:
            problems.append((
                f"spreads to {length_said(spread)} across and the space is {room}",
                "mature_spread_in_max"))
        else:
            fits.append((f"spreads to {length_said(spread)}, within the {room} here",
                         "mature_spread_in_max"))

    climbing = ("climbs",) if climber else ()
    if problems:
        tail = (" It would need a support, and hard cutting back every year, "
                "to stay in this space." if climber else "")
        return _finding(axis, Verdict.misfits,
                        "Outgrows this spot: " + "; ".join(t for t, _ in problems)
                        + "." + tail,
                        species, *(f for _, f in problems), *climbing)
    if fits:
        return _finding(axis, Verdict.fits,
                        "Fits the space: " + "; ".join(t for t, _ in fits) + ".",
                        species, *(f for _, f in fits), *climbing)
    return _unknown(axis, "This area hasn't been measured, so size isn't checked.")


def _sqft(area_sqft: float) -> str:
    """Square feet as the gardener gave them: "32 sq ft", "12.5 sq ft"."""
    text = f"{area_sqft:.1f}"
    return f"{text[:-2] if text.endswith('.0') else text} sq ft"


# --- upkeep ----------------------------------------------------------------
# Only asked when the gardener asked for it. A watering regime is not a defect;
# it becomes one only against a stated wish to be left alone.

_TOLERANT = {"dry_thoroughly_between", "dry_surface_between"}
_DEMANDING = {"keep_moist", "keep_barely_moist"}

_REGIME_WORDS = {
    "keep_moist": "wants its soil kept evenly moist",
    "keep_barely_moist": "wants its soil kept barely moist",
    "dry_surface_between": "likes the surface dry between waterings",
    "dry_thoroughly_between": "wants to dry out thoroughly between waterings",
}


def _upkeep(species: Species, area: GrowingArea) -> Optional[Finding]:
    axis = Axis.upkeep
    goal = GrowingGoal.low_upkeep.value
    if goal not in _goals(area):
        return None
    regime = species.water_regime
    if regime is None:
        return _unknown(axis, "No source gives this species a watering regime.", goal)
    regime = token(regime)
    words = _REGIME_WORDS.get(regime, regime.replace("_", " "))
    if regime in _TOLERANT:
        return _finding(axis, Verdict.fits, f"Low upkeep: {words}.",
                        species, "water_regime", goal=goal)
    if regime in _DEMANDING:
        return _finding(axis, Verdict.misfits,
                        f"Needs regular attention: {words}.", species, "water_regime",
                        goal=goal)
    return _unknown(axis, "No source gives this species a watering regime.", goal)


# --- goals -----------------------------------------------------------------

def _goals(area: GrowingArea) -> set[str]:
    return {token(g) for g in (area.goals or [])}


def _goal_findings(species: Species, area: GrowingArea) -> list[Finding]:
    """One finding per goal the gardener actually asked for.

    A goal narrows and never loosens: wanting something to eat cannot make an
    inedible plant fit, and not wanting one cannot rule an edible plant out.
    """
    out: list[Finding] = []
    goals = _goals(area)

    edible = GrowingGoal.edible.value
    if edible in goals:
        if species.is_edible is None:
            out.append(_unknown(
                Axis.goal, "No source says whether this is grown to eat.", edible))
        elif species.is_edible:
            out.append(_finding(Axis.goal, Verdict.fits, "Grown to eat.",
                                species, "is_edible", goal=edible))
        else:
            out.append(_finding(Axis.goal, Verdict.misfits,
                                "Not grown to eat, and you asked for edibles.",
                                species, "is_edible", goal=edible))

    pollinators = GrowingGoal.pollinators.value
    if pollinators in goals:
        if species.attracts_pollinators is None:
            out.append(_unknown(
                Axis.goal, "No source says whether this feeds pollinators.",
                pollinators))
        elif species.attracts_pollinators:
            out.append(_finding(Axis.goal, Verdict.fits,
                                "Recorded as feeding pollinators.",
                                species, "attracts_pollinators", goal=pollinators))
        else:
            out.append(_finding(
                Axis.goal, Verdict.misfits,
                "Not recorded as feeding pollinators, and you asked for those.",
                species, "attracts_pollinators", goal=pollinators))

    return out


# --- the assessment --------------------------------------------------------

def assess(species: Species, area: GrowingArea) -> list[Finding]:
    """Every axis's verdict on this species in this area, in reading order."""
    findings = [
        _indoor_outdoor(species, area),
        _sun(species, area),
        _soil(species, area),
        _footprint(species, area),
    ]
    upkeep = _upkeep(species, area)
    if upkeep is not None:
        findings.append(upkeep)
    findings.extend(_goal_findings(species, area))
    return findings


def misfits(findings: Iterable[Finding]) -> list[Finding]:
    """What needs addressing, for a plant already standing here."""
    return [f for f in findings if f.verdict == Verdict.misfits]


def confirmed(findings: Iterable[Finding]) -> list[Finding]:
    return [f for f in findings if f.verdict == Verdict.fits]


def score(findings: Iterable[Finding]) -> int:
    """How many axes actually confirmed a fit.

    Only `fits` counts. That single choice is what keeps a species nobody has
    researched from floating to the top of a recommendation list: it has no
    misfits to disqualify it and no evidence to rank it, so it sorts below
    anything with a real answer, without needing a penalty rule of its own.
    """
    return sum(1 for f in findings if f.verdict == Verdict.fits)


def is_candidate(findings: list[Finding]) -> bool:
    """Zero misfits AND at least one confirmed fit -- CONTEXT.md's Candidate.

    The second half is what keeps an unexamined row out: nothing against it
    because nothing is known about it is not a recommendation."""
    return not misfits(findings) and score(findings) > 0


@dataclass(frozen=True)
class Candidate:
    species: Species
    findings: list[Finding]

    @property
    def score(self) -> int:
        return score(self.findings)


def tie_order(species: Species) -> tuple[str, str, int]:
    """Where a species sits among candidates level with it: A to Z.

    A score counts confirmed axes and nothing finer, and the catalog holds no
    measure that would put one fully confirmed species above another without
    inventing one -- each settled field credits a single authority, so there
    is no corroboration to count. Within a tie the order therefore claims
    nothing, and the screens say what it is: alphabetical. That has to be
    true as a reader sees it, so case is folded ("aloe" is not filed after
    "Zinnia"), and two species sharing a common name -- Rubus allegheniensis
    and Rubus fruticosus are both "Blackberry" -- follow their scientific
    names, then their ids, instead of whatever order the database returned
    them in. Without that last part the list could reshuffle between
    requests, and a recommendation that moves on refresh reads as noise.
    """
    return ((species.common_name or "").casefold(),
            (species.scientific_name or "").casefold(),
            species.id or 0)


def candidates(species_list: Iterable[Species], area: GrowingArea) -> list[Candidate]:
    """Species with nothing against them here, best-evidenced first.

    "Nothing against them" is a zero-misfit rule, not a high-score rule: one
    real contradiction disqualifies, however well the rest reads. Among equal
    scores the order is `tie_order`'s, A to Z and stable between requests.
    """
    scored = []
    for species in species_list:
        findings = assess(species, area)
        if not is_candidate(findings):
            continue
        scored.append(Candidate(species=species, findings=findings))
    scored.sort(key=lambda c: (-c.score, *tie_order(c.species)))
    return scored
