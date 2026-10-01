# Harm-capable fields never inherit from the genus

Status: accepted 2026-09-10. Extends ADR 0002, whose genus bound still holds.

## Context

ADR 0002 lets a gap be filled from the species' genus, labelled
genus-inferred, and excludes toxicity alone. The glossary in CONTEXT.md was
written wider than that: a harm-capable field — toxicity, cold tolerance,
watering regime — "never accepts an inferred value". The resolver followed
the ADR, not the glossary: `NEVER_INHERIT` held `toxic_to_pets`, and a
genus-level `water_regime` or `chill_damage_f` resolved onto the species and
reached the advisor, the vision prompt and the mobile Care facts card with a
genus-inferred label on it. The 2026-09-05 wiring review left the gap as an
open policy question.

## Decision

The code follows the glossary. Every field in `HARM_CAPABLE` refuses genus
inference: `NEVER_INHERIT` is derived from it rather than listed beside it,
so a field that becomes harm-capable is barred from borrowing at the same
moment it starts refusing to resolve through disagreement. A species-level
claim on any of these fields resolves exactly as before, and still outranks
the genus. Fields that cannot hurt anything — humidity, drainage, light, the
temperature bands — inherit as they always have.

The reasoning is the one ADR 0002 gave for toxicity, and it applies just as
well to the other two. A watering regime is the instruction a caretaker acts
on most often, and genera are not uniform about it: borrowed from a cousin
that likes wet feet, it rots a plant that wants to dry out, and the other way
round desiccates one. A cold-damage figure decides whether a plant is left
outside on a given night, and a genus figure that is thirty degrees off for
this species is a plant lost in one evening. The label "genus-inferred" tells
the reader that nobody said this about their plant; it does not make the
number any safer to act on. Coverage on these fields therefore grows only by
species-level citation, and stays null otherwise — the app says it has no
record, which is true.

## Considered options

Keeping the borrowed value and leaning on the label was the status quo, and
what the review found: honest at the level of provenance, but a wrong
instruction with a caveat attached is still a wrong instruction. Refusing
inference only when the genus disagreed internally was rejected because a
genus with one confident page is the case that misleads most. Widening the
tolerance on `chill_damage_f` so that borrowing looked safer was rejected on
the same grounds as the original harm-capable rule: being confidently wrong
is the expensive outcome.

## Consequences

Some species will show no watering regime and no cold figure where a genus
page could have supplied one. When this was decided the verified tranche
(73 batches, 2,807 claims, 523 species) had no species borrowing either
field, so nothing visible was lost; the cost is future coverage that would
have come cheaply and now has to be cited. `RESOLVER_VERSION` moved to "3"
so a row resolved under the older rules is stale by the usual query, not by
memory.

Display code keeps its field-agnostic labelling — a borrowed humidity still
says so — but no longer needs a per-field defence on the harm-capable ones.
The advisor stub's regime line dropped its borrowed label because the case
cannot arise, and test fixtures that modelled a genus-borrowed regime or cold
figure now model a state the resolver can produce. A future reader who finds
`toxic_to_pets`, `water_regime` and `chill_damage_f` all null on a species
with a well-covered genus should read this before filling them in.
