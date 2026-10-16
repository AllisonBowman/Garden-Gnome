# Edibility, the survival floor and the watering estimates are harm-capable

Status: accepted 2026-10-16. Extends ADR 0007, whose rule it applies to
four more fields.

## Context

ADR 0007 made the resolver follow the glossary: a harm-capable field never
resolves through a material disagreement and never borrows from the genus.
The set it barred was the glossary's three examples, `toxic_to_pets`,
`chill_damage_f` and `water_regime`. The 2026-10-15 ship audit found fields
outside that set that can do the same damage, and one of them doing it.
Nymphaea odorata resolved `is_edible` true from the Nymphaea genus page ("in
some parts of the world the leaves and flowers are eaten in moderation"), and
the app showed it as "grown to eat" with a genus-inferred label. No source
had said that about this water lily.

The glossary defines a harm-capable field as one where a wrong value can
injure an animal or kill a plant. Edibility is the case where a wrong value
injures a person, which that definition did not think to name.

## Decision

`HARM_CAPABLE` now also holds:

- `is_edible`. Telling someone a plant is food is the one statement in the
  catalog a person acts on by putting the plant in their mouth.
- `outdoor_temp_min_f`. It is the survival floor USDA PLANTS publishes
  (ADR 0006). It is cold tolerance under another name, which the glossary
  already lists.
- `water_growing_days_est` and `water_dormant_days_est`. They are the
  watering regime said as a number of days. A cousin's cadence drowns a
  plant that wants to dry out as surely as a cousin's regime does.

`water_check_depth_cm` stays inheritable. It says where to feel the soil, and
the feel decides; a wrong depth misleads a check rather than replacing it.

Because `NEVER_INHERIT` is derived from `HARM_CAPABLE`, these fields stopped
borrowing in the same change that made them refuse to resolve through
disagreement. `RESOLVER_VERSION` moved to "6".

## Consequences

Nymphaea odorata's `is_edible` goes back to null, and the app says it has no
record, which is true. No other row in the tranche (134 batches, 10,679
claims, 997 species) borrowed any of the four fields or held disagreeing
species-level claims on them, so nothing else moved. Future batches that
disagree on a day estimate will now leave it null instead of letting tier pick
a winner. That costs coverage and avoids a confident wrong number.

The glossary entry in CONTEXT.md still lists three examples. It should say
"injure a person or an animal, or kill a plant" and name edibility, so the
next reader of the glossary arrives at this set without reading the resolver.
