# Curated prose follows the file

Status: accepted 2026-10-30.

## Context

`garden-gnome/app/data/species_catalog.json` holds the 129 curated entries,
the ones with check schedules. `seed()` inserted each once and never rewrote
it, so a correction to the file never reached a database that already had
the row. Two corrections were waiting: 25 em dashes mis-decoded since the
first commit, and the safety claims and toxicity verdicts taken out of the
care notes. Production's rows were seeded long before either. The claim sync
doesn't help, because it writes resolved fields and leaves the legacy columns
alone (ADR 0005). The fallback was a one-off script run by hand on the Fly
machine. It would have needed rewriting for every later edit, and it had
never run on production.

## Decision

On every boot, `seed()` brings each curated row's prose into line with the
file, wherever the two differ:

- `care_notes` and `soil_type`, on every row of source `curated` whose
  scientific name is an entry's. That is the same exact-name match that
  decides an insert.
- `notes`, on each of that row's schedules.

The writes go through the ORM, so the commit stamps a new catalog generation
and the caches keyed on it rebuild. A boot that changes nothing stamps
nothing. The log line is `curated text refreshed N`.

Nothing else is touched:

- every other column on the row: the pet flag and the other harm-capable
  fields, every resolved field and its provenance, the legacy care values
  and the common name
- a schedule's intervals, and the traits
- rows another pipeline made, even under a curated name
- which schedules exist: none is added and none removed

These three fields are the prose the file states and no source does. No
claim backs them and the resolver never writes them, so the file overrules
nothing but its own earlier text. The other columns either belong to the
claim graph or decide what a caretaker is asked to check.

## Consequences

To change a curated note, edit the file, and the next boot carries the
change to every database. An edit made in a database to one of these fields
on a curated row, by hand or through `apply_review`, is overwritten at the
next boot, so corrections to curated prose go in the file. Two tests check
the file before it lands: `test_catalog_encoding` catches mis-decoding, and
`test_curated_notes` refuses safety claims, toxicity verdicts and edibility
claims.

The refresh is fenced like the claim sync. A failure rolls back its own
transaction, prints the traceback and `curated text refresh skipped`, and the
boot goes on to uvicorn. A stale note can be fixed later; an API that won't
start can't be used at all.
