# PlantAdvocate

A houseplant and garden care app whose central promise is that advice is never
reasoned from scratch: every recommendation traces to a catalog record, and
every catalog value traces to something a horticultural authority actually
published. This document fixes the language that promise depends on.

## Language

### Evidence

**Claim**:
One field's value for one species, as asserted by a single citation. The unit
of evidence — claims are collected, never edited, and a value nobody claimed
does not exist.

**Authority**:
An organisation whose publications count as evidence, such as NC State
Extension or the Royal Horticultural Society.
_Avoid_: source, provider, reference

**Citation**:
The specific document within an Authority that carries a Claim, together with
the passage that supports it.

**Authority tier**:
How much weight an Authority's claims carry when claims conflict. A property of
the organisation, not of any one document.

**Resolved value**:
The single value a Species presents for a field after all its Claims have been
reconciled. Always derivable from the Claims — never typed in by hand.

**Material disagreement**:
Two Claims for the same field that differ by more than that field's tolerance.
Distinct from ordinary imprecision, which resolves silently by tier.

**Genus-inferred**:
A Resolved value borrowed from the species' genus rather than asserted about
the species itself. Honest to show, dishonest to hide.

**Harm-capable field**:
A field where a wrong value can injure an animal or kill a plant — toxicity,
cold tolerance, watering regime. Harm-capable fields never resolve
automatically through disagreement and never accept an inferred value.

**Care data status**:
How well-backed a Species' care values are — `sourced`, `inferred`, or `none`.
A property of the data.
_Avoid_: verified

**Review status**:
Where a Species sits in the operator's review workflow. A property of the
process, not of the data, and deliberately not the same thing as Care data
status.

**Species source**:
Which pipeline produced a Species record. Says nothing about whether the values
are backed by evidence.

### Care

**Check**:
Looking at a plant to decide whether it needs anything. The unit of scheduled
work — the app schedules checks, never actions, because no calendar can know
what a plant needs.
_Avoid_: task, chore, watering

**Outcome**:
What a Check ended in. "Looked and it didn't need doing" is a complete,
successful outcome, not a skipped one.

**Care window**:
The span between the earliest and latest sensible interval for a care type. A
plant inside its window is on time; a single due date would be a false
precision.

**Observation**:
Something a gardener recorded about one specific plant at one moment. The only
data in the system that describes a real plant rather than a kind of plant.

**Growing area**:
A place someone has to grow in, described well enough to be matched against:
its light, its shelter, its surface and dimensions, and what the gardener wants
out of it. Care schedules and weather are per-area, because a windowsill and a
back garden are not the same place — and neither are the species that belong in
them.
_Avoid_: environment, which in this codebase now means only the one variables
are read from. The database table is `growingarea` and the API path
`/growing-areas`; `/environments` answers too, deprecated, until the shipped
build stops calling it.

**Fit finding**:
One axis's verdict on one Species in one Growing area — `fits`, `misfits`, or
`unknown` — with the sentence a person reads for it. Derived on every request,
never stored, so it stays honest as the catalog is corrected.

**Unknown**:
The verdict when the catalog says nothing on an axis. Never a pass: it does not
score, does not rank, and does not make a Candidate. The same rule as a null
toxicity — no record is not "safe" — applied to space instead of harm.

**Misfit**:
A Fit finding of `misfits` against a plant already standing in the area. The
unit of what needs addressing, and the only thing the "needs addressing" card
shows — a plant nobody can judge is absent from it, not listed as fine.

**Candidate**:
A Species put forward for a Growing area: zero Misfits *and* at least one
confirmed fit. The second half is what keeps an unresearched species — nothing
against it because nothing is known about it — out of a recommendation.
