# Landing brief for one size-backfill chunk

A size-backfill chunk adds six fields -- `is_edible`, `attracts_pollinators`, `mature_height_in_min/max`,
`mature_spread_in_min/max` -- to species that are ALREADY landed. It never creates a record and never changes a
field that already holds a value. Work in the checkout's `garden-gnome/` with `.venv/bin/python`. Do not commit.

## Input

`scripts/catalog/pipeline/<chunk>-result.json`: the workflow's own result, `{"landed": [...], "unverified": [...],
"no_research": [...]}`. Each landed entry is `{batch, record, applied, review, summary}`. `applied` lists what the
audit already nulled. `review` lists what the workflow could NOT decide mechanically and a person (you) must:
"REFUTED but unmapped field" lines and "quote correction proposed ... NOT applied" lines. Species in `unverified`
or `no_research` are held back -- do not land them.

## What landing does

1. **Work every `review` line.** Read the page with
   `.venv/bin/python scripts/catalog/pipeline/qc.py "<URL>" "<regex>"`.
   - An unmapped refutation that is really about one of the six fields: null that field, add an unknowns line
     "`<field>` removed on audit: <reason>", and drop any citation left supporting nothing.
   - A proposed corrected quote is applied ONLY when it is demonstrably the SAME evidence de-spliced: the stored
     quote contains U+23CE (qc.py's boundary marker) or a label glued to its value across a boundary, and the
     correction is that same text as the page renders it -- or the correction is a substring of the stored quote.
     Confirm the correction on the page with qc.py first. Anything else is NOT applied: an auditor once supplied a
     toxicity sentence as the "correction" for an edibility quote, and swapping it in would have cited a poison
     warning as proof a plant is food. If a held correction leaves the field unsupported, null the field.
2. **Check every citation you are about to land.** Any quote containing U+23CE, a label glued to its value
   ("Height:\n6 ft."), a truncated tag list, or text qc.py cannot find: de-splice it under the rule above, or drop it
   and null the field(s) it alone supports.
3. **Hold the rules the research agents were given.** Sizes are INCHES (a 6-ft shrub is 72, never 6). One published
   figure fills one end; never centre it into a range. A cultivar's size is not the species'. A climber (vine, liana,
   anything a page says climbs) sets `climbs` true and lands its published size AS REACH (since 0020_climbs; before
   that it took no size). `climbs` is never false; a sprawler, trailer or bramble no page calls a climber stays null. `is_edible` true
   needs a page saying it is grown or used for food, and if any page names a toxic part or a required preparation,
   that condition must be in unknowns. False needs a page denying it; silence is null. `attracts_pollinators` true
   needs bees, butterflies, moths, hummingbirds or other pollinators named -- seed-eating birds are not pollinators.
4. **Merge.** `.venv/bin/python scripts/catalog/pipeline/merge_backfill.py <result.json>` prints the plan and every
   problem; fix problems in the result file (never in the batch files by hand) until it prints `none`, then run it
   again with `--apply`. The merge only adds; it refuses to overwrite, refuses unknown species, and refuses a value
   the loader could not pair to a citation.
5. **Verify.** `.venv/bin/python scripts/catalog/verify_quotes.py <each touched app/data/verified/b*.json>` -- no
   MISS on any citation whose claim names one of the six fields (a pre-existing MISS elsewhere in an old file is
   not yours; report it separately). Then
   `.venv/bin/python -m pytest tests/test_tranche_invariants.py tests/test_claim_ingest.py -p no:cacheprovider -W ignore -o addopts="" -q`
   -- the ingest count assert WILL fail; report the new total it prints. Do not edit the test.

## Report (under 30 lines; the long version goes in `<chunk>-summary.md` beside the result)

The merge_backfill plan totals (species written, fields written), every `review` line and what you did with it,
every field you nulled at landing and why, the verify_quotes summary line per touched file, the invariants result
and the new claim total.

## Round 5 additions (species already asked once; `newPages`)

- **New pages.** A citation URL the record did not already carry must be on a registered domain
  (`app/data/claims/authorities.py` REGISTRY) and must be the species' OWN page -- not a genus page, a cultivar page
  or another species'. Drop a citation that fails this and null what it alone supported. The orchestrator warms the
  cache for new URLs before you start; a new-page citation verify_quotes SKIPs was never checked -- drop it.
- **Stale notes.** After `--apply`, run
  `.venv/bin/python scripts/catalog/pipeline/strip_stale_size_notes.py <result.json> [--apply]`: for every species
  that now carries a size, it removes the earlier unknowns lines that said the size was deliberately left null
  (the old climber rule, the indoor rule). It prints every line it removes; read them.
- `have` fields were already landed and are skipped by the merge if re-reported unchanged; a DIFFERENT value for a
  landed field is a merge problem -- null it in the result file (a backfill never overwrites).
