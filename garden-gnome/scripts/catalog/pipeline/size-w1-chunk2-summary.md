# Size backfill, wave 1 chunk 2 -- landing summary

Landed 2026-09-27 from `size-w1-chunk2-result.json` (40 species, 0 unverified, 0 no_research), after chunk 1 was
fully landed and verified, following `BACKFILL_LANDING_BRIEF.md`. Not committed.

**Verification basis.** Every page was read from this worktree's `.quote_cache`, not fetched live: the sandbox proxy
blocks these hosts. Per the seeding, those cached copies date from early to mid September 2026, so a page may have
changed since; everything below was checked against the cached copy. All 48 pages this chunk's citations point at
were cached with status ok (NC State 99 citations, RHS 16, UF/IFAS 4, Penn State 4). No landed citation points at
Missouri Botanical Garden or Clemson.

## Merge plan totals

40 species written (all 40), 189 fields, 123 citations, across 7 batch files. Claims +189 (every new value paired to
a citation).

| file | claims |
|---|---|
| b28-holly-and-nuts (also touched by chunk 1) | 56 -> 83 (+27) |
| b29-mistletoe-and-more | 41 -> 68 (+27) |
| b30-poison-ivy-and-more | 45 -> 69 (+24) |
| b31-avocado-and-more | 42 -> 71 (+29) |
| b32-weeping-fig-and-more | 49 -> 80 (+31) |
| b33-belladonna-and-more | 46 -> 76 (+30) |
| b34-hemlock-and-more | 39 -> 60 (+21) |

## The 13 review lines

Rule applied: a correction goes in only if the stored quote is spliced (U+23CE, or a label glued to its value) and
the correction is that same text as the page renders it, or a substring of the stored quote. Each applied or
substituted quote was confirmed with qc.py against the cached page.

- **Chinese Fountain Grass, mature_height_in_min / _max / mature_spread_in_min / _max (4 lines)** -- APPLIED: "Height:
  2 ft. 0 in. - 6 ft. 0 in." and "Width: 2 ft. 0 in. - 4 ft. 0 in." are substrings of the stored "Dimensions: ⏎
  Height: ... ⏎ Width: ..." and single lines on the NC State Cenchrus alopecuroides page.
- **Chinese Fountain Grass, attracts_pollinators** -- APPLIED: "Attracts Pollinators" is the stored "Play Value: ⏎
  Attracts Pollinators" without its label (same node).
- **Creeping Jenny, mature_height_in_min / _max / mature_spread_in_min / _max (4 lines)** -- APPLIED: "Height: 0 ft. 2
  in. - 0 ft. 4 in." and "Width: 1 ft. 0 in. - 2 ft. 0 in." are substrings of the stored U+23CE quote.
- **Creeping Jenny, attracts_pollinators** -- APPLIED: "Plants for pollinators" is a substring of the stored quote,
  which had glued the RHS badge to the next label ("Herbaceous Perennial").
- **Poison Ivy, attracts_pollinators** -- correction "The flowers are pollinated by and act as a food source for a
  wide variety of insects." HELD: the stored quote "Butterflies" is a clean single run (the Attracts field value),
  not spliced, and the correction is a different sentence. Stored quote kept; the value stands on NC State's
  Attracts field (Butterflies, Moths, Songbirds). No size: climber.
- **American Elm, attracts_pollinators** -- APPLIED: "Pollinators" is a substring of the stored "Attracts: |
  Butterflies | Pollinators" (a label joined to its values with pipes).
- **Eastern Columbine, attracts_pollinators** -- correction "Provides nectar to bumblebees, butterflies, hummingbirds
  and other pollinators." HELD: it is the Wildlife Value sentence, a different element from the stored "Attracts:
  Butterflies Hummingbirds Moths Pollinators Songbirds" (label glued to its values). That stored quote was de-spliced
  to "Pollinators" (substring; the Attracts field). Value stands.

## Fields nulled at landing, and why

None. No review line left a field unsupported, no rule check failed, and no chunk-2 species already held any of the
six fields. The 3 fields the audit had already nulled (in `applied`) stay null: Pecan attracts_pollinators (NC State
and UF/IFAS both say wind pollinated; the bare "Pollinators" tag is contradicted), American Sycamore is_edible (RHS's
fruit-hair irritant warning missing from unknowns), Celery is_edible (RHS "Harmful to skin with sunlight" and the
skin-rash warning missing from unknowns).

## Other fixes made in the result file

Unknowns lines that the auditors showed to be wrong about what a cited page says were corrected after re-reading the
cached page, and missing edibility conditions were added:

- Japanese Honeysuckle (is_edible true on flowers/nectar): the line saying RHS has no toxicity evidence was replaced --
  RHS reads "Fruit are ornamental - not to be eaten." with gloves advice and a pets warning.
- European Plum (is_edible true): added the toxicity from the NC State 'Stanley' page this record cites -- Poison Part
  Leaves, Seeds, Stems; "Stems, leaves, seeds contain cyanide, particularly toxic in the process of wilting".
- Pokeweed: "poisonous" and "death in rare cases" were attributed to UF/IFAS AG254 as well as EP631; only EP631 says
  them, and the attribution was fixed. The line claiming EP631, Penn State and RHS give no size was replaced with
  their actual figures (none used).
- American Persimmon: the UGA horse-pasture line said "(typically unripe)" and "fallen fruit", neither of which is on
  the page; reworded to what it says.
- Kousa Dogwood: "very tart until fully ripe" was credited to kousa but Penn State says it of Cornus mas; removed.
  The pollinator claim label named the Attracts field while its quote comes from Play Value; label corrected.
- Eastern Columbine: "zero hits for 'Problem for'" corrected (the one hit is a leaf-miner pest note).
- Burning Bush: RHS's 1.5-2.5 m was called "the same range" as NC State's 15-20 ft; replaced with the actual
  disagreement (plus Penn State "Up to 15 feet tall"). Poison Part corrected from "bark" to every part NC State lists.
- Catawba Rhododendron and Japanese Privet: "no page addresses eating" replaced -- RHS says "Harmful if eaten." for
  both. is_edible stays null (not re-proposed).
- Belladonna and Weeping Willow: the "NC State refused this machine" lines were rewritten. Their cached NC State pages
  give 3-4 ft by 3-4 ft (Belladonna, plus "Not edible, leaves, roots and fruits are highly toxic.") and 30-40 ft by
  30-40 ft (Weeping Willow), which disagree with the RHS and UF/IFAS figures that were landed. Values unchanged.
- Celery: added RHS's 0.1-0.5 m size, which disagrees with NC State's 18-36 in by 12-18 in.

## verify_quotes, per touched file

No MISS on any citation naming one of the six backfill fields, and no skip on one; all 123 new citations are HITs.

| file | result |
|---|---|
| b28-holly-and-nuts | 127 hit, 3 MISS, 0 inconclusive, 22 skipped |
| b29-mistletoe-and-more | 103 hit, 1 MISS, 0 inconclusive, 31 skipped |
| b30-poison-ivy-and-more | 127 hit, 4 MISS, 0 inconclusive, 24 skipped |
| b31-avocado-and-more | 130 hit, 3 MISS, 0 inconclusive, 9 skipped |
| b32-weeping-fig-and-more | 111 hit, 4 MISS, 0 inconclusive, 37 skipped |
| b33-belladonna-and-more | 119 hit, 2 MISS, 0 inconclusive, 30 skipped |
| b34-hemlock-and-more | 127 hit, 1 MISS, 0 inconclusive, 28 skipped |

All 18 MISSes predate this landing (the same ones appear when the HEAD copies are checked) and none touches a
backfill field: b28 Peach toxicity_detail and cool_rest_note, American Elderberry name_note; b29 American Mistletoe
is_houseplant/soil; b30 Poison Ivy name_note and toxicity_detail, Brazilian Orchid toxic_to_pets, German Chamomile
outdoor_sun_exposure; b31 Avocado names, Southern Live Oak scientific_name_given and chill_damage_f; b32 Weeping Fig
scientific_name_accepted and outdoor_sun_exposure, Prickly Pear common_name and is_houseplant; b33 Panicle Hydrangea
soil_base, Kousa Dogwood name_note; b34 Rose of Sharon is_houseplant. Skips are pages the proxy blocks with no cached
copy (MoBot, Clemson, some IFAS). The failed fetch entries these runs wrote were deleted; the main checkout's cache
had no ok copy of any of them.

## Invariants and count

`tests/test_tranche_invariants.py` passes. `test_the_whole_verified_tranche_lands_and_resolves` fails as expected;
the test was not edited. Right after this apply it printed `assert 5285 == 4840`. The 5,285 also counts another
session's wave-1 chunk 4 landing (+153 in b5, b46, b48, b50, b51), which was in the tree at the time and has since
been committed as d08d1b3, moving the assertion to 4,993. So: chunk 1 added +103 and this chunk +189, and HEAD plus
chunks 1 and 2 is **5,285 claims** (4,840 + 292 = 5,132 counting these two chunks alone). A later re-run printed
`assert 5451 == 4993`, because another session's chunk 3 landing is now in the working tree too; at that run it
had not changed any file this chunk wrote (its b34 part was still pending).

## Worth a human look

- Pokeweed lands is_edible true on UF/IFAS AG254's poke-salad text (young shoots and leaves, boiled at least twice
  with the water discarded), with NC State "All parts of this plant are poisonous" and Penn State "New leaves and
  roots, along with the berries, should not be eaten" in unknowns. Rule 6 prescribes a conditional true here, and
  the auditor passed it, but the sources disagree about the very leaves called edible.
- Belladonna and Weeping Willow took their sizes from RHS and UF/IFAS because NC State was unreachable at research
  time; NC State's figures differ and are now disclosed in unknowns.
- Catawba Rhododendron and Japanese Privet carry an RHS "Harmful if eaten." and could take is_edible false in a later
  pass.

## Landing decision added 2026-09-27 by the orchestrating session

Japanese Yew (b85) and Pokeweed (b30): is_edible cleared from true to null before commit. The app renders is_edible true as "grown to eat" with no condition; Yew's only support is a small-amount aril caveat inside a toxicity description, and Pokeweed is eaten only after preparation while every part is poisonous raw. Evidence kept in each record's unknowns.
