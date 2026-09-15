# Claims mint species rows, and a null there is honest

The verified tranche covers species the catalog never had -- 342 of 469 when
this was decided -- and evidence about a plant with no row is evidence nobody
can see. So the claim sync (`app/data/claims/sync.py`) mints a `Species` row
for every species-level tranche subject the catalog lacks, and it is the only
path that does. Such a row has a name, a common name and `source = claims`;
every legacy care column is null, and so is `toxic_to_pets`.

## Considered options

Filling the legacy columns from the resolved values was rejected: it would
write a light label or a humidity band no source stated, which is the defect
the resolved columns exist to replace. Keeping `toxic_to_pets` NOT NULL with
its False default was rejected because 199 of the unmatched species have no
toxicity claim and 34 of those carry a cited description of harm -- a default
False there is an invented safety verdict, exactly what ADR 0002 forbids.
Minting rows for bare genus subjects was rejected: genus evidence feeds
congeners through the resolver and describes no plant of its own.

## Consequences

Every reader of the legacy columns must tolerate null, and a null
`toxic_to_pets` means "no record", never "safe" -- the toxicity sentence
already says so. Existing rows are not backfilled; their flags stay what they
were. A species the catalog already holds under an older name is linked by
`scientific_name_accepted`, never renamed, because plants and the toxicity
table key on `scientific_name`.
