# Size backfill, round 6 chunk 3 -- landing summary

Landed 2026-10-03 from `size-r6-chunk3-result.json`: 40 species over b8, b38, b39, b43, b44 and b76, with 0 unverified,
0 no_research, 4 fields already nulled on audit (all Freesia's) and 0 review lines. It followed
`BACKFILL_LANDING_BRIEF.md` (including the Round 5 additions) and the standing rules in the landing instructions. Not
committed.

Only four species carried a value. Three of them land. Mistletoe Cactus's is_edible true was nulled at landing. The
other 36 wrote nothing in the workflow itself: every field they were asked about came back null or was already
landed.

The untouched result file and the six batch files as they were at the start are kept in the session scratchpad
(`r6c37/orig/`). The result-file edits were made by a script there (`r6c37/fix_results.py`) that asserts each edited
entry's starting state.

## Result

- b38-beech-poplar-shrubs: 72 -> 77 claims (+5)
- b39-cherry-laurel-and-more: 86 -> 87 (+1)
- b76-native-wet-meadow-perennials: 69 -> 70 (+1)

That is +7 against HEAD. HEAD was 588d8ca when this landing started and has since moved to d0bac40. The commits in
between are the app team's, and none of them touches `app/data/verified/` or the two tests, so the per-file deltas
are the same against either. With only this chunk applied, the ingest test printed `assert 6996 == 6989`. With chunk
7 also applied, it prints `assert 7003 == 6989`. b8, b43 and b44 are unchanged.

## Merge plan totals

The plan printed "problems: none" and was applied once. It wrote 3 species, 7 fields and 6 citations, and named no
batch file outside this chunk's list.

- Thorny Elaeagnus (b38): attracts_pollinators true, mature_height_in 157.5-315 and mature_spread_in 157.5-315. There
  are 3 citations, all to RHS's species page, which is new to the record.
- Cherry Laurel (b39): is_edible false, with 2 citations (NC State and RHS, both already on the record).
- Purple-headed Sneezeweed (b76): is_edible false, with 1 citation (NC State, already on the record).

The other 37 species, Mistletoe Cactus now included, have nothing to write.

## Review lines

There were none. The only `applied` set is Freesia's four size fields (12-24 x 6-12 in). They were nulled on audit
because their only source is NC State's Freesia genus page, not a page for Freesia x hybrida. They stay null, and
Freesia writes nothing.

## Fields nulled at landing, and why

- Mistletoe Cactus (b44), is_edible: true was set to null and its one citation dropped. There are two reasons:
  - Standing rule 2. The only food wording on either page is NC State's Uses (Ethnobotany) field, "medical and
    environmental uses such as medicine, food, and animal food". It names no part eaten, no preparation and no
    grower's use, so it is not a food statement.
  - The record's existing unknowns already hold a deliberate null on that same line ("is_edible left null (corrected
    at landing): ... too vague to support true"). A backfill does not land true over that.

  As asked, the cached pages were checked for toxicity. NC State has no Poison or "Problem for" text, only the tags
  "#non-toxic for cats #non-toxic for horses #non-toxic for dogs". RHS has no harmful, poison, toxic, edible or eaten
  text. Both pages describe the berries only as fruit.

  With is_edible nulled, Mistletoe Cactus writes nothing. Its "is_edible removed on audit" line stays in the result
  file, and b44 is untouched.

## Edibility calls under standing rule 2

- Cherry Laurel, false. RHS's Potentially harmful field reads "Seed kernels harmful if eaten". NC State's Poisonous
  to Humans block gives severity High, cyanogenic glycosides and Poison Part Leaves, Seeds, Stems. The quoted text is
  "Stems, leaves, seeds contain cyanide, ...". No page offers a food use, and no page says whether the fruit pulp is
  eaten. The record's earlier null was a silence null ("no page ... addressed eating"), which the RHS sentence shows
  was mistaken. It was not a deliberate toxic or marginal null.
- Purple-headed Sneezeweed, false. NC State's Poisonous to Humans block (severity Low; Poison Part Flowers, Leaves,
  Seeds) has the Poison Symptoms text "... and convulsions if eaten in large quantities." That is the same kind of
  evidence on which Bush Lily, American Mistletoe and Buttercup already carry false. Its only food words are
  wildlife tags ("#food source nectar" and similar).
  - The record's older line kept is_edible null "rather than being inferred as false" from this same block.
  - Standing rule 2 bars landing true over a deliberate null, not false. A new line says this landing supersedes the
    older one.
- Mistletoe Cactus, null (above).

## Thorny Elaeagnus checks

- The size comes from rhs.org.uk/plants/6314, titled "Elaeagnus pungens | silverthorn". That is the species' own page
  on a registered domain, and new to this record. The record's earlier RHS URL, rhs.org.uk/plants/elaeagnus-pungens,
  had returned http-404.
- The quotes are the summary block's clean runs ("Max Height 4-8 metres"), not the Size panel, where the label and
  value are separate elements.
- The conversions are 4 m = 157.48 in, recorded as 157.5, and 8 m = 314.96 in, recorded as 315. The range is
  published as a range. It is not a cultivar's figure, and the plant is not a houseplant.
- climbs is already true on the record. NC State lists Vine among its Plant Types, calls it a "Vine-like shrub" and
  says it "is capable of climbing and can attach to overhead trees". So the size lands as reach.
- RHS's prose says "to 5m in height". The research unknowns record this.
- attracts_pollinators rests on RHS's species-level "Plants for pollinators" tag. 25 records in the corpus already
  rest on that tag alone. NC State's Attracts field lists only Songbirds, which is silence on pollinators, not a
  contradiction.

## Unknowns added at landing

Each ends "Noted at landing, verified against the cached copy". Three of these lines go into the batch files. The
Mistletoe Cactus line stays in the result file.

- Thorny Elaeagnus: the size lands as reach. This supersedes the older line saying "no reach figure is published, so
  no size is recorded".
- Cherry Laurel: false on RHS's "Seed kernels harmful if eaten" and NC State's poison block. This supersedes the older
  lines saying no page addressed eating and that is_edible is null.
- Purple-headed Sneezeweed: false on the Poisonous to Humans block's "if eaten" symptoms. This supersedes the older
  kept-null line.
- Mistletoe Cactus: "is_edible removed on audit (nulled at landing): ...", in the result file only.

## Stale size notes

Run on the whole result file, `strip_stale_size_notes.py` would have removed 10 lines. Only one was stale. The script
matches "left null", "withheld" and "suppress", and this chunk names 40 species, most of which already carried a
size. So it would have hit lines that are still true:

- Cherry Laurel, Firethorn, Virginia Sweetspire, Madagascar palm, Pygmy Date Palm and Great Blue Lobelia: "not a
  climber, so the size fields were populated normally". The script matched "suppression", "left null" or "withheld"
  inside the sentence.
- Lady Palm: two lines. Its min height and its spread are still null.
- Cat Palm: its mins are still null.

The script was therefore run, and applied, on a one-entry copy of the payload (`r6c37/strip-chunk3-size-only.json`).
That copy holds only Thorny Elaeagnus, the one species whose size this landing wrote. It removed one line: "mature_height_in and
mature_spread_in left null: NC State page ... no plant Height or Dimensions block." The research's new NC State line
keeps that finding.

## Asparagus (b8), outside the merge

The audit said Asparagus's landed is_edible true lacks NC State's toxicity condition. It does not. b8 has carried it
since round 3 chunk 3 (2bebc3d), in the line "is_edible is true, but the same NC State page that documents edibility
also names toxicity ...". That line quotes:

- Poison Symptoms: "Contact dermatitis from young, raw shoots; eating of berries may cause gastrointestinal problems".
- Poison Part: Fruits, Stems.
- The prose: "Low poisonous toxicity of the plant are the fruits and stems. Eating the berries may cause
  gastrointestinal problems." and "Contact dermatitis is likely from young, raw shoots, so wear gloves when
  handling."

All of this text is on the cached NC State page. Nothing was appended, because a second line would only repeat the
first. b8 is unchanged. If you want the line anyway, it is a one-line append.

## verify_quotes, per touched file (VQ_CACHE_ONLY=1)

- b38-beech-poplar-shrubs: 108 hit, 1 MISS, 0 inconclusive, 26 skipped (HEAD: 105 hit, 1 MISS, 26 skipped)
- b39-cherry-laurel-and-more: 131 hit, 0 MISS, 0 inconclusive, 23 skipped (HEAD: 129 hit, 23 skipped)
- b76-native-wet-meadow-perennials: 137 hit, 0 MISS, 0 inconclusive, 49 skipped (HEAD: 136 hit, 49 skipped)

Hits rose by exactly the 6 new citations (+3, +2, +1). Each file's MISS, SKIP and INCONCLUSIVE lines are identical to
HEAD's, and none names a backfill field, so there is no NEW-FIELD MISS, SKIP or INCONCLUSIVE. b38's one MISS predates
this landing. It is Chinese Fringe Flower's UF/IFAS landscape-uses quote (ask.ifas.ufl.edu/publication/ep562), which
belongs to no backfill field.

## Tests

- `tests/test_tranche_invariants.py`: 3,880 passed.
- The combined run with `test_claim_ingest.py` gave 3,886 passed and 1 failed. The failure is the expected count
  assert: `assert 6996 == 6989` with this chunk alone, and `assert 7003 == 6989` once chunk 7 landed too.
- The test was not edited.

## The quote cache

All 15 pages read for chunks 3 and 7 were already cached with status ok. Every qc.py and verify_quotes call ran with
`VQ_CACHE_ONLY=1`. Nothing was fetched live, and nothing in the cache was written, moved or deleted.

## Left for you

- Commit with commit_backfill.py. Pass b38, b39 and b76, plus `size-r6-chunk3-result.json` and this summary. The
  claim delta against HEAD is b38 +5, b39 +1, b76 +1, for a total of +7.
- A minor point: several research lines say a field was "already landed" when the record holds a deliberate null.
  An example is Thorny Elaeagnus's "is_edible and climbs already landed", where is_edible is null. That is the
  workflow's `have` wording, and it was left as written.
