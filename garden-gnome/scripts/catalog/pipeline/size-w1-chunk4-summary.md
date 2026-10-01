# Size backfill, wave 1 chunk 4 -- landing summary (2026-09-27)

Input: `size-w1-chunk4-result.json` (wave-1 groups 15-18: 30 species, 0 unverified, 0 no-research;
4 fields already nulled on audit; 38 review lines). Landed per `BACKFILL_LANDING_BRIEF.md` into
b46, b48, b5, b50 and b51 only. Nothing committed; `tests/test_claim_ingest.py` not edited.

All page reads (qc.py and verify_quotes) were against the cached copies in `scripts/catalog/.quote_cache`,
not live pages: the sandbox proxy blocks live fetches. Every one of the 35 pages this chunk cites is cached
with status ok and a file date of 2026-09-05. Missouri Botanical Garden (plantfinder.mobot.org,
missouribotanicalgarden.org) and Clemson HGIC refuse this machine and are cached only as error entries,
so nothing from them was read or used.

## Result

`merge_backfill.py` plan: 30 species, 153 fields, 102 citations, problems `none`; applied.

- b46-herbs-aquatics-and-companions: 5 species, 28 fields, 20 citations
- b48-hollies-camellia-dogwood-and-more: 6 species, 31 fields, 20 citations
- b5-edible-and-garden: 8 species, 34 fields, 24 citations
- b50-native-woodland: 6 species, 31 fields, 19 citations
- b51-native-woodland-2: 5 species, 29 fields, 19 citations

By field: is_edible 21 (18 true, 3 false), attracts_pollinators 25, size on 27 species (107 size fields;
Fragrant Water Lily has a max height only). No size on Melon and Pumpkin (climbers) or on Common Peony
(nulled on audit).

Post-merge check, pre vs post per record: only the six fields changed (null -> value), citations and
unknowns only appended, untouched records byte-identical, one normalization line per file. All 153
new claims pair to their own new citations (none to an older citation that happens to name a field).
The loader counts +153 claims from these five files (b46 +28, b48 +31, b5 +34, b50 +31, b51 +29).

## The 38 review lines

Rule applied: a correction goes in only when the stored quote carries U+23CE (or a label glued to its
value) and the correction is that same text as rendered, or when it is a substring of the stored quote.
All 38 corrections were confirmed on the cached pages with qc.py first. Held corrections are real page
text too; they were held for provenance, not because they are wrong.

**Applied, 22 lines: same text de-spliced.** In each case the stored quote glued `Dimensions:` to both the Height
and Width lines (or `Edibility:` to its value) across U+23CE, and the correction is one of those lines
exactly as rendered, a literal substring of the stored quote.
- Japanese Holly: height min/max, spread min/max (4) and is_edible (the Edibility value
  "Use caution. Human ingestion of berries can cause minor toxic reaction.", which supports is_edible **false**).
- Kale: height and spread (4).
- Myrtle: height and spread (4) and is_edible ("The fruits are edible.").
- Canadian Wild Ginger: height and spread (4).
- Great White Trillium: height and spread (4).

**Held, 13 lines: the stored quote was a splice, but the correction is different page text.** The stored
quote was de-spliced here instead, to one of its own rendered runs (a substring of it). The claim is unchanged.
- attracts_pollinators, auditor offered Wildlife Value / prose sentences: Apricot, Japanese Holly,
  Canadian Wild Ginger, Great White Trillium -> `Pollinators` (the Attracts field's stacked value);
  Kale, Myrtle -> `Bees` (the Attracts field's only value).
- Sasanqua Camellia attracts_pollinators: auditor offered the Play Value item "Attracts Pollinators" -> the
  stored Attracts splice was de-spliced to `Pollinators`.
- Sasanqua Camellia size (4 lines): auditor offered the prose sentence "...will reach 6 to 14 feet high and 5
  to 7 feet wide." Instead, the one spliced citation covering both stems was split into two citations,
  `Height: 6 ft. 0 in. - 14 ft. 0 in.` (mature_height_in) and `Width: 5 ft. 0 in. - 7 ft. 0 in.`
  (mature_spread_in). Citations 2 -> 3.
- Fennel is_edible: auditor offered "#edible seeds #edible leaves #edible flowers", which is a slice of a much
  longer tag list (a truncated tag list, a defect in its own right). The page has no Edibility field, so the
  stored `Plant Type:` splice was de-spliced to its rendered stacked value `Edible`.
- Kale is_edible: auditor offered "Kale can be eaten raw or cooked into various dishes." (the preceding sentence).
  The stored quote spliced two paragraphs; kept its first run,
  `varieties such as Russian kale do best in stir fries with very little cooking required.`

**Held, 3 lines: the stored quote was clean and the correction was longer or different text.** The stored quote was kept.
- Papaya is_edible: the correction completes the MG054 sentence. The stored quote stopped mid-word at "develo".
  It was trimmed to its last whole word ("...yellow to orange color"), a substring of itself.
- Yaupon Holly and Foamflower attracts_pollinators: prose sentences offered for `Pollinators`. The bare value
  is genuine: it is a stacked value of each page's Attracts field (checked with qc.py).

No held correction left a field unsupported, so none was nulled for that reason.

## Fields nulled at landing

None. The 4 fields nulled on audit stay null: Common Peony mature_height_in_min/max and
mature_spread_in_min/max. Their source is NC State's "Paeonia - Herbaceous Types" group page, which never names
P. officinalis. The workflow had already dropped their citations.

## Citation check beyond the review lines

Before the repair, 22 of 101 stored quotes carried U+23CE; all were spans across page boundaries, and all 22 are
covered above. After the repair all 102 citations are present on their cached page as single rendered runs:
no U+23CE, no label glued across a boundary, nothing qc.py cannot find. Tarragon's tag-list quote is the
page's complete Tags list, not a truncation. The bare quotes (`Pollinators`, `Bees`, `Edible`,
`Attracts Pollinators`) are each a stacked value of a structured field on that page.

## Rules re-checked

- Inches: all 48 NC State Height/Width pairs re-derived from the quotes and match the values. Papaya
  (FP106 10-15 ft / 5-7 ft -> 120-180 / 60-84) and Fragrant Water Lily (PSU 5 ft -> max 60; RHS 1-1.5 m ->
  39.4-59.1) were checked by hand. One published figure fills one end (Water Lily min height is null).
- Climbers: Melon and Pumpkin carry no size. Tomato keeps its size. NC State's structured Plant Type and
  Habit/Form have no vine or climbing entry; only the prose calls indeterminate types "vine-like".
- is_edible true, safety sweep: every readable assigned page for the 18 edible-true species was searched for
  poison/toxic/harmful/problem for/caution/preparation text and compared with unknowns. Gaps are fixed below.
- is_edible false rests on explicit denials: Japanese Holly (NC State Edibility warning; RHS "not to be
  eaten"), Canadian Wild Ginger (UMD "Not grown for human consumption."; NC State "Do not consume any part of
  this plant."), Black Cohosh (RHS "Harmful if eaten.").
- attracts_pollinators true: every one names bees, butterflies, moths or "Pollinators"; none rests on
  seed-eating birds.

## Unknowns corrected or added at landing

Corrections are marked "corrected at landing". Added lines end "noted at landing, verified against the cached
copy." Every page quotation in them was re-checked against the cached pages.
- Apricot: the line claiming the RHS species page added nothing was corrected. Added the size disagreement:
  RHS Max Height/Spread 4-8 m (about 157-315 in), "A small, round-headed tree to 8m", against NC State's
  20-40 ft (240-480 in); the NC State values are kept. Added RHS "Seed kernels harmful if eaten..." plus its pets
  line. The cyanogenic pits/seeds/leaves/stems condition from NC State is kept unchanged.
- Tarragon (safety): Poison Part corrected from "Bark, Flowers, Fruits" to all seven listed parts (Bark,
  Flowers, Fruits, Leaves, Roots, Seeds, Stems, so including the leaves eaten as the herb). Added Poison
  Severity and the Poison Symptoms text. The "Net" sentence now names the leaves only (the page tags
  #edible leaves), not "leaves/seeds".
- Mayapple (safety): added RHS "Harmful if eaten..." / "Pets (dogs): Harmful if eaten" (no ripe-fruit
  exception). Added NC State's CAUTION / HARVEST TIME (pesticide-free areas) / SAFE HANDLING text and "the tan
  seeds are inedible". Added the RHS size disagreement: Max Spread 1-1.5 m vs NC State's 9-12 in.
- Yaupon Holly (safety): added RHS "Fruit are ornamental - not to be eaten..." plus its pets line.
  The auditor had said RHS carries no toxicity text; the cached page does.
- Tomato: added NC State's Problems list (Poisonous to Humans; Problem for Cats, Children, Dogs, Horses).
- Melon: gloss corrected. The page says plainly "Avoid the seeds", not "once they have sprouted".
- Japanese Holly: added RHS "Fruit are ornamental - not to be eaten..." as a second source for false.
- Canadian Wild Ginger: Poison Part corrected to Leaves, Roots and Stems.
- Black Cohosh: the gloss "a pets/handling-adjacent caution" was corrected, because the RHS field names no pets.
- Fennel: removed the claim that NC State's /common-name/fennel/ URL describes var. azoricum. It is the same
  Foeniculum vulgare page with an identical Dimensions block.
- Sacred Lotus: removed the attribution of PSU's "Max Growth Height (ft): 5" to sacred lotus. On that page it
  sits under the Native Replacement, Fragrant Water Lily.
- Northern Sea Oats: disclosed that the same page says the flowers "are wind pollinated", tags #wind
  pollinated, and names only larval-host butterflies. The flag rests on the structured Attracts field, as rule 7
  allows (same pattern as the b27 Water Lily note).
- Fragrant Water Lily: disclosed that PSU's 5 ft "Max Growth Height" is printed for a floating-leaved plant,
  with no statement of what it measures.

## verify_quotes (per touched file)

- b46: 178 hit, 0 MISS, 0 inconclusive, 34 skipped
- b48: 96 hit, 0 MISS, 0 inconclusive, 11 skipped
- b5: 56 hit, 1 MISS, 0 inconclusive, 6 skipped
- b50: 97 hit, 1 MISS, 0 inconclusive, 24 skipped
- b51: 103 hit, 0 MISS, 0 inconclusive, 30 skipped

No new citation is a MISS, SKIP or INCONCLUSIVE; all 102 HIT. The two MISSes predate this chunk: the same
MISS appears on the HEAD version of each file, and both sit on old name citations, not on any of the six fields.
- b5 Melon name_note "Flexuosus group (American cucumber)" (NC State cucumis-melo)
- b50 Foamflower common_name "foam flower, coolwort, false mitrewort, white coolwort" (RHS 18215)

Skips are the pre-existing MOBOT/Clemson/PDF citations. verify_quotes tried three older, uncached MOBOT URLs
(b46 kempercode=d168 and taxonid=297512, b51 taxonid=285428), which wrote error entries; those three entries
were deleted.

## Tests

`pytest tests/test_tranche_invariants.py tests/test_claim_ingest.py`: 3832 passed, 1 failed. The failure is
the expected ingest count assert, which printed `assert 5096 == 4840`. The 5096 is a whole-tree snapshot and
includes sibling agents' in-progress merges into b12, b14, b23, b27, b28, b66, b68, b73 and b85. This chunk
alone is +153, so it would read 4,993 with nothing else in the tree.

## For a person to decide

- The 13 held corrections leave bare structured-field values as quotes (`Pollinators`, `Bees`, `Edible`) where
  auditors offered fuller sentences. All of those sentences are on the pages, if the rule is ever relaxed for
  same-claim, different-field evidence.
- Tomato keeps 12-120 in height. The 10-ft top end reflects staked indeterminate growth, but NC State does not
  classify the plant as a climber.
- Common Peony keeps attracts_pollinators true from the herbaceous-group page. The record already carries a
  "SCOPE DISCLOSURE" that all its NC State data is group-level, and its toxic_to_pets comes from the same page.
  (French marigold's flags were withheld in chunk 4 of the earlier run, but that was a genus page quoting a
  different species' cultivars.)
- Northern Sea Oats (wind-pollinated grass) is flagged true on NC State's Attracts field; this is disclosed.
- Size disagreements that auditors noted but that were not added to unknowns (only Apricot's, which was
  requested, and Mayapple's, which the auditor said to add, were recorded):
  - Fennel: RHS 1.5-2.5 m / 0.1-0.5 m; NC State prose 3-5 ft
  - Doghobble prose 3-6 ft; Red-osier prose 6-9 ft; Myrtle prose "5-6 ft" typical
  - Trillium: RHS 0.1-0.5 m
  - Wild Geranium: NC State prose 1-2 ft
  - Canadian Wild Ginger: UMD up to 12 in spread
- Sasanqua's unknowns still say EDIS ep002 refused this machine. An ok cache entry for it was written
  2026-09-27 11:51, after the research run. It is a Camellia overview with no height text, and nothing
  uses it.

Scratch work (repair script, checker, qc.py outputs) is in the session scratchpad under `c4/`, not in the repo.
