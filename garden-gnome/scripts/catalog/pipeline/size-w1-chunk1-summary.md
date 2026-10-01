# Size backfill, wave 1 chunk 1 -- landing summary

Landed 2026-09-27 from `size-w1-chunk1-result.json` (40 species, 0 unverified, 0 no_research), following
`BACKFILL_LANDING_BRIEF.md`. Not committed.

**Verification basis.** Every page was read from this worktree's `.quote_cache`, not fetched live: the sandbox proxy
blocks these hosts. Per the seeding, those cached copies date from early to mid September 2026, so a page may have
changed since; everything below was checked against the cached copy. All 45 pages this chunk's citations point at
were cached with status ok. None of the landed citations points at Missouri Botanical Garden or Clemson.

## Merge plan totals

25 species written, 103 fields, 71 citations, across 9 batch files. Claims 4,840 -> 4,943 (+103; every new value
paired to a citation). 15 species wrote nothing: 13 whose only proposed values were already landed (see "nulled at
landing"), plus Thorny Elaeagnus (a climbing shrub; no edibility or pollinator statement) and Tannia (no usable page).

| file | claims |
|---|---|
| b12-fruit-and-flowers1 | 78 -> 79 (+1) |
| b14-annual-flowers2 | 53 -> 59 (+6) |
| b23-daylily-and-more-gaps | 64 -> 69 (+5) |
| b27-bulbs-and-more | 37 -> 66 (+29) |
| b28-holly-and-nuts | 40 -> 56 (+16) |
| b66-native-trees-4 | 57 -> 63 (+6) |
| b68-native-vines-and-a-rhododendron | 39 -> 45 (+6) |
| b73-native-wetland-shrubs | 56 -> 62 (+6) |
| b85-shrubs | 55 -> 83 (+28) |

## The 18 review lines

Rule applied: a correction goes in only if the stored quote is spliced (U+23CE, or a label glued to its value) and
the correction is that same text as the page renders it, or a substring of the stored quote. Each applied or
substituted quote was confirmed with qc.py against the cached page.

- **American Bittersweet, is_edible** -- correction "Vomiting, diarrhea, loss of consciousness, seizures" HELD: a
  poison-symptom line in place of the Edibility field is different evidence. The stored "Edibility: Poison" glues
  the label to its value across a boundary, so it was de-spliced to its own value, "Poison" (substring; the NC State
  Edibility field). is_edible false stands on that plus RHS "Harmful if eaten." (verbatim). The poisonous parts
  (Bark, Flowers, Fruits, Leaves, Roots, Sap/Juice, Seeds, Stems) were already named in unknowns. No size: climber.
- **American Wisteria, attracts_pollinators** -- correction "Attracts Pollinators" HELD: on the page that is the
  *Play Value* field, not the stored quote de-spliced. The stored "Attracts: Bees Butterflies Pollinators" was
  de-spliced to "Pollinators" (substring; the Attracts field). Value stands. No size: climber.
- **Crossvine, attracts_pollinators** -- same as American Wisteria: "Attracts Pollinators" (Play Value) HELD; the
  stored "Attracts: ... Bees ... Butterflies ... Hummingbirds ... Pollinators" (label glued to its values with
  ellipses) de-spliced to "Pollinators". Value stands. No size: climber.
- **Trumpet Honeysuckle, attracts_pollinators** -- correction (a Wildlife Value sentence about hummingbirds, bees,
  butterflies and moths) HELD: a different sentence. The stored U+23CE quote was de-spliced to "Pollinators"
  (substring; Attracts field). Value stands. No size: climber.
- **Oakleaf Hydrangea, mature_height_in_min / _max / mature_spread_in_min / _max (4 lines)** -- APPLIED: "Height:
  4 ft. 0 in. - 8 ft. 0 in." and "Width: 4 ft. 0 in. - 10 ft. 0 in." are substrings of the stored spliced
  "Dimensions: Height: ... Width: ..." and single lines on the page.
- **Oakleaf Hydrangea, attracts_pollinators** -- correction (Wildlife Value "Its flowers are attractive to
  butterflies and other insects.") HELD: different sentence. Stored "Attracts: Butterflies Pollinators Songbirds"
  de-spliced to "Pollinators". Value stands.
- **Moonflower, attracts_pollinators** -- moot. The field already holds true in b14 (landed in wave 1 chunk 4), and
  a backfill never overwrites, so the proposed value was nulled and Moonflower wrote nothing. (The correction, a
  prose line about moths pollinating, would have been held anyway: it is not the stored quote de-spliced.)
- **Sweet Pea, attracts_pollinators** -- moot for the same reason (already true in b15). The correction "Butterflies"
  was a valid de-splice (substring, confirmed on the page) but there is nothing to write it to.
- **Water Lily, all six fields (6 lines)** -- APPLIED: "Height: 0 ft. 6 in. - 0 ft. 10 in.", "Width: 2 ft. 0 in. -
  12 ft. 0 in.", "In some parts of the world the leaves and flowers are eaten in moderation." and "Bees" are each a
  substring of a stored U+23CE quote and a single run on the NC State Nymphaea page (the record is the genus, so
  the genus page is in scope). Added an unknowns line: the page explains its "Attracts: Bees" as the leaves being
  "a landing pad for thirsty bees" and never says bees visit the flowers.
- **American Holly, attracts_pollinators** -- correction "This plant provides nectar for pollinators." HELD: the
  stored quote "Pollinators" is not spliced (a clean single run, the Attracts field value), so there is nothing to
  de-splice, and the correction is a different sentence. Stored quote kept; value stands.

## Fields nulled at landing, and why

No field was nulled for a rule violation at landing; every held correction left its field supported by the stored
quote de-spliced. 22 proposed values were nulled because the batch record **already holds** that field from wave 1
chunks 4-5 (these 15 species were re-researched because they still had no size). merge_backfill refuses any
overwrite, so the result file had to drop them:

- is_edible: Muscadine Grape, Cucumber, Gourds, Garden Pea, Squash, Grape, Sweet Pea, Dahlia, Primrose, Chinese
  Wisteria, Jackman's Clematis (11)
- attracts_pollinators: Muscadine Grape, Gourds, Watermelon, Common Morning Glory, Moonflower, Nasturtium, Sweet Pea,
  Dahlia, Primrose, Chinese Wisteria, Jackman's Clematis (11)

Of those 15, only Watermelon (is_edible true, now with the cooked-rind condition that chunk 4 nulled it for) and
Common Morning Glory (is_edible false, RHS "Harmful if eaten.") had anything new. For those two, the citation
behind the already-landed pollinator flag was dropped and unknowns were trimmed to the lines explaining is_edible,
so the record does not collect duplicate disclosures. The other 13 wrote nothing and still have no size (climbers,
genus-only pages, or sizes the audit refuted again).

For reference, the 11 fields the audit had already nulled (in `applied`) stay null: Flowering Quince is_edible (RHS
seed toxicity and remove-the-seeds preparation missing from unknowns), Oakleaf Hydrangea is_edible (only a
"Play Value: Edible fruit" tag on a page typed Poisonous), French marigold is_edible (a genus-level denial contradicted
by the same genus's NC State page), Nasturtium is_edible (NC State's pets warnings and "with exception of the
roots" missing from unknowns), Primrose all four sizes (NC State's 3-72 in by 48-96 in
contradicts its own "less than 12 inches" and RHS), Showy Stonecrop is_edible (Poison Part includes the stems and
leaves called edible), Dutch Crocus mature_spread_in_min (RHS band floor 0), Black Walnut attracts_pollinators (wind
pollinated; "Attracts: Moths" is a larval host).

## Other fixes made in the result file

- Dutch Crocus: spread claim label "mature_spread_in 0-3.9" corrected to "mature_spread_in_max 3.9" (min was nulled
  on audit); the unknowns line saying RHS never addresses eating was replaced -- RHS reads "Ornamental bulbs - not to
  be eaten." is_edible stays null (not re-proposed).
- American Holly: added an unknowns line for RHS "Fruit are ornamental - not to be eaten." is_edible stays null.
- Black Walnut: height claim label cleaned of a stale "600-960" fragment (value is 600-900); added an unknowns line
  with the eating conditions on pages the record cites (UGA: safe only if the nutmeat is not moldy, rotten or
  bad-smelling; hulls irritate; "Juglone can harm animals and humans"; ingesting pure juglone can seriously poison;
  PSU: fallen walnuts may become moldy).
- American Elderberry: unknowns misstated NC State's Poison Part as "fruits and leaves (unripe)"; corrected to
  Fruits, Leaves, Roots and Stems.

## verify_quotes, per touched file

No MISS on any citation naming one of the six backfill fields; all 71 new citations are HITs.

| file | result |
|---|---|
| b12-fruit-and-flowers1 | 95 hit, 2 MISS, 0 inconclusive, 31 skipped |
| b14-annual-flowers2 | 95 hit, 1 MISS, 0 inconclusive, 49 skipped |
| b23-daylily-and-more-gaps | 114 hit, 1 MISS, 0 inconclusive, 29 skipped |
| b27-bulbs-and-more | 121 hit, 1 MISS, 0 inconclusive, 31 skipped |
| b28-holly-and-nuts | 110 hit, 3 MISS, 0 inconclusive, 22 skipped |
| b66-native-trees-4 | 135 hit, 0 MISS, 0 inconclusive, 30 skipped |
| b68-native-vines-and-a-rhododendron | 114 hit, 0 MISS, 0 inconclusive, 33 skipped |
| b73-native-wetland-shrubs | 116 hit, 0 MISS, 0 inconclusive, 38 skipped |
| b85-shrubs | 137 hit, 0 MISS, 0 inconclusive, 48 skipped |

The 8 MISSes all predate this landing (the same 8 appear when the HEAD copies of those files are checked) and none
touches a backfill field: Blackberry is_houseplant and Grape cool_rest_note (b12); Common Morning Glory common_name
(b14); Showy Stonecrop scientific_name_accepted (b23); Red Raspberry is_houseplant (b27); Peach toxicity_detail,
Peach cool_rest_note, American Elderberry name_note (b28). Skips are pages the proxy blocks with no cached copy
(MoBot, Clemson, some IFAS). Five of them sit on b85's pre-existing size/flag citations for Smooth Hydrangea and
Koreanspice Viburnum (landed with b85, not here); no copy of those four pages exists in either cache. The failed
fetch entries these runs wrote were deleted; the main checkout's cache had no ok copy of any of them.

## Invariants and count

`tests/test_tranche_invariants.py` passes. `test_the_whole_verified_tranche_lands_and_resolves` fails as expected:
`assert 4943 == 4840`, run right after this apply and before any other landing reached the working tree. New
total: **4,943 claims** (+103). The test was not edited.

## Worth a human look

- Japanese Yew lands is_edible true on NC State "The red arils, in small amounts, are edible. The green seed is
  toxic.", with high-severity toxicity, the toxic parts and RHS "TOXIC if eaten" in unknowns. That is what rule 6
  prescribes (one part edible, another toxic), and the auditor passed it, but English Yew (b26) sits at false on RHS.
- Water Lily's attracts_pollinators rests on bees that, per the page, come to drink from the leaves.
- American Holly and Dutch Crocus both have an RHS "not to be eaten" line and could take is_edible false in a later
  pass; this landing did not add values the researcher did not propose.
- American Elderberry (landed in b28): Penn State's "Native Plant Spotlights" page, which the record cites, says
  all parts are "somewhat poisonous to people when ingested, including the seeds inside raw fruit. The ripe fruit
  should only be eaten cooked". The unknowns carry NC State's cooked-only condition and its poison parts, but not
  this sentence, and they also quote UGA's "eaten raw when fully ripe". I found this after the apply;
  merge_backfill cannot append to a record whose fields are already set, so it needs a hand decision.

## Landing decision added 2026-09-27 by the orchestrating session

Japanese Yew (b85) and Pokeweed (b30): is_edible cleared from true to null before commit. The app renders is_edible true as "grown to eat" with no condition; Yew's only support is a small-amount aril caveat inside a toxicity description, and Pokeweed is eaten only after preparation while every part is poisonous raw. Evidence kept in each record's unknowns.
