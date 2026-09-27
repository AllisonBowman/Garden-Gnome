# Size backfill, round 3 chunk 1 -- landing summary

Landed 2026-09-27 from `size-r3-chunk1-result.json` (40 species over b51-b58, 0 unverified, 0 no_research,
4 fields already nulled on audit, 45 review lines), following `BACKFILL_LANDING_BRIEF.md`. Not committed;
`tests/test_claim_ingest.py` not edited.

Another session was merging a different chunk into `b58-native-prairie-2.json` while this one ran, and
merge_backfill rewrites whole files, so the corrected payload was split after review.
`size-r3-chunk1-result.json` now holds the 37 entries for b51-b57, and those were applied.
`size-r3-chunk1-b58-result.json` holds the three b58 entries (Big Bluestem, Canada Anemone, Prairie Smoke).
They were reviewed and planned but NOT applied; they wait for the other session's b58 work to be committed.
The `review`, `applied` and `summary` keys of every entry are left exactly as the workflow wrote them; only
`record` was edited.

## Verification basis

Every page was read from this worktree's `scripts/catalog/.quote_cache`, not fetched live, because the sandbox
proxy blocks these hosts. Verification was therefore against the cached copies. All 43 pages this chunk
cites are cached with status ok and a file date of 2026-09-05, so a page may have changed since its copy was
taken. No landed citation points at Missouri Botanical Garden or Clemson. Four Clemson pages that unknowns lines
quote (woodland-phlox, bluestar, factsheet/echinacea, factsheet/baptisia-false-or-wild-indigo) are cached ok from
2026-09-05 and were used only to check those lines. Every other MOBOT and Clemson URL in these records is an
error entry written earlier today, before this landing began. Those were left alone.
No fetch happened during landing. The cache listing was identical at the start and at the end of the session
(1,977 entries), so there were no error entries to delete.

## Merge plan totals

For `size-r3-chunk1-result.json` (applied), the plan printed "problems: none". It wrote 36 species,
179 fields and 115 citations across 7 batch files. Queen of the Prairie wrote nothing: all six fields were null
and it had no citations. The 179 fields are 138 size bounds, 34 attracts_pollinators and 7 is_edible. The size
bounds are height on 35 species and spread on 34, because Rough Goldenrod has no spread. The is_edible values
are 3 true (Blunt Mountain Mint, Wild Bergamot, Purple Prairie Clover) and 4 false (Blue Cohosh, Dwarf Crested
Iris, Goldenseal, White False Indigo). Claims per file, as the loader counts them:

- b51-native-woodland-2: 61 -> 66 (+5)
- b52-native-woodland-3: 29 -> 61 (+32)
- b53-native-woodland-and-wet-meadow: 31 -> 57 (+26)
- b54-native-meadow: 27 -> 51 (+24)
- b55-native-meadow-2: 25 -> 55 (+30)
- b56-native-meadow-3: 30 -> 62 (+32)
- b57-native-prairie: 27 -> 57 (+30)

That is +179 claims, one per field. Each new value pairs to its own new citation, not to an older citation
that happens to name the field. A semantic check against pre-apply copies confirmed that the merge only added.
Only the six fields changed, from null to a value. Citations and unknowns were only appended, and each file got
one new normalization line. Untouched records are byte-identical, and so is every top-level key. The git diff is
much larger than the change. b52-b57 were stored with indent 1 and merge_backfill writes indent 2, so those six
files are reflowed whole: 7,111 insertions and 6,021 deletions in all. With whitespace ignored, the diff is
+1,168/-78 lines.

For `size-r3-chunk1-b58-result.json` (plan only, NOT applied), the plan printed "problems: none" against b58
as it now stands, with the other session's uncommitted merge in it. It would write 3 species, 15 fields and
9 citations: Big Bluestem 6, Canada Anemone 4 and Prairie Smoke 5. That is +15 claims when applied. To apply it:
`.venv/bin/python scripts/catalog/pipeline/merge_backfill.py scripts/catalog/pipeline/size-r3-chunk1-b58-result.json --apply`,
then run verify_quotes on b58.

## The 45 review lines

The rule applied is the brief's. A correction goes in only if the stored quote is spliced (it carries U+23CE, or
a label is glued to its value) and the correction is that same text as the page renders it, or a substring of
the stored quote. Every correction, held or applied, was confirmed against the cached page first. When a
correction was held, the stored splice was de-spliced to one of its own values instead. The repair script
asserted three things for every quote edit: the new quote is a literal substring of the stored one, it sits
inside one rendered line of the cached page, and it carries no U+23CE.

- Size de-splices, APPLIED (32 lines): Woodland Phlox (4), Golden Ragwort (4), Large-flowered Bellwort (4),
  White Turtlehead (2), New York Ironweed (4), Oxeye Sunflower (4), Swamp Milkweed (2), Golden Alexanders (4)
  and Golden Crown (4). In every case the stored quote was NC State's "Dimensions: ⏎ Height: ... ⏎ Width: ...",
  and the correction is the "Height: ..." or "Width: ..." line. Each is a literal substring of the stored quote
  and its own rendered line on the page. Bellwort, Ironweed and Oxeye had one spliced citation covering both
  stems, so it was split into a height citation and a width citation (+3 citations). No value changed.
- Label glued to its value, APPLIED (2 lines). For Golden Alexanders attracts_pollinators, "This plant attracts
  butterflies and bees." is the stored "Wildlife Value: ⏎ ... This plant attracts butterflies and bees." without
  its label. For Big Bluestem is_edible, "non-edible" is the stored "Edibility: non-edible" without its label;
  the page renders the label and the value on separate lines.
- Pollinator corrections, HELD, stored splice de-spliced (9 lines). In each, the auditor offered a different
  page element for a stored NC State "Attracts:" list spliced across U+23CE (or, for Sneezeweed, glued to four
  stacked values):
  - The offered text was a Wildlife Value or prose sentence for Golden Ragwort, Joe Pye Weed, White Turtlehead,
    Oxeye Sunflower, Swamp Milkweed and Golden Crown.
  - For New York Ironweed it was "Attracts Pollinators", which is the Play Value field.
  - For Sneezeweed it was "#pollinator plant #NC native #NC Native Pollinator Plant", a slice of a much longer
    Tags list.
  - For Woodland Phlox it was "Its flowers attract hummingbirds, butterflies, and bees, The foliage attracts
    rabbits.", which is already citation 0's quote, word for word.

  Each stored list was cut to one of its own stacked values. That is "Pollinators" for eight of them and "Bees"
  for Woodland Phlox, whose list is Bees, Butterflies, Hummingbirds, Small Mammals. Every one was checked to be
  a value of that page's Attracts field. All nine values stand.
- Pollinator corrections, HELD, stored quote kept (2 lines): Goat's Beard ("Pollinators") and Cup Plant
  ("Hummingbirds"). Both stored quotes are clean, each is a stacked value of the page's Attracts field, and the
  offered prose sentences are different elements.

No held correction left a field unsupported.

## Other citation repairs (brief step 2, not review lines)

- Oxeye Sunflower, RHS: "Other common names⏎ North American ox-eye ⏎ Plants for pollinators" was de-spliced to
  "Plants for pollinators", the same form as earlier chunks' RHS tag quotes.
- Golden Alexanders, NC State: its second attracts citation, the spliced Attracts list, was de-spliced to
  "Pollinators".
- Big Bluestem (b58 file): the citation whose quote was the bare label "Attracts:" was dropped. A label with no
  value is evidence of nothing, and the loader would have paired attracts_pollinators to it because it came
  first. The field stays supported by the next citation, "Pollinators", a value of the same Attracts field
  (Butterflies, Pollinators).
- Canada Anemone (b58 file): mature_height_in_min and mature_spread_in_min were rounded from 3.94 to 3.9, and
  the two claim labels and the conversion note were updated to match. This chunk rounds the same RHS 0.1-metre
  bound to 3.9 for Prairie Smoke and Grey-head Coneflower. Before this landing the corpus held sixteen 3.9 values and no
  3.94. This is a harmonisation, not a correction of a wrong number.

After the repairs, a checker ran over all 124 citations, 115 in the applied file and 9 in the b58 file. Every
quote is present on its cached page, inside one rendered line, with no U+23CE. All 75 height and spread pairs
were re-derived from their quotes and match both the values and the claim labels. For NC State, that means feet
and inches converted to inches. For RHS, it means metres times 39.37 at one decimal. For Rough Goldenrod, it
means "2-5 foot stems".

## Fields nulled at landing, and why

None were nulled at landing. The 4 fields nulled on audit stay null: Celandine Poppy's
mature_height_in_min/max and mature_spread_in_min/max. The height citation was an empty placeholder and the
spread had none. The workflow had already dropped both, and their "removed on audit" unknowns lines land with
the record. The auditor confirmed the values themselves (12-14 in by 9-12 in, on clean single-line quotes).
See "left for you".

## Rules re-checked

- Inches: see the re-derivation above. No climbers, and no cultivar figures.
- is_edible true, safety sweep: every readable assigned page for the three edible-true species was searched for
  harmful, poison, toxic and eaten text. That covered NC State, RHS and PSU for the mountain mint, NC State,
  RHS and UMD for bergamot, and NC State plus both RHS pages for prairie clover. None names a toxic part or a
  required preparation. All three rest on tea use, and the prairie clover also on roots "palatable when
  chewed". That matches the corpus's existing trues that rest on tea use alone: Purple Coneflower, German
  Chamomile and Wild Geranium.
- is_edible false rests on explicit page statements:
  - Blue Cohosh: Edibility field "Seeds are toxic." and "Poisonous to Humans".
  - Dwarf Crested Iris: NC State "It causes only low toxicity if eaten.", and now also RHS "Harmful if eaten."
  - Goldenseal: "The inedible fruit is berry-like, crimson."
  - White False Indigo: "Poisonous through ingestion. All parts are poisonous."
  - Big Bluestem: Edibility "non-edible".
- The coordinator's corrected edibility rule was checked after landing. A food commonly grown or sold but
  cooked first stays true with the condition in unknowns; only poisonous plants with marginal or folk food use
  land null. Nothing in this chunk changes. No is_edible was nulled or changed at landing or on audit. No cited
  or consulted page names a cooking or preparation requirement for any of the 40 species: the three trues are
  tea uses with no condition, and every null is a silence-null.
- attracts_pollinators: every true names bees, butterflies, hummingbirds or "Pollinators", and none rests on
  seed-eating birds. There is no false in this chunk. Early Meadow-rue stays null although NC State says it
  "is pollinated by the wind": that is not a denial that pollinators visit.

## Unknowns corrected or added at landing

Corrections end "Corrected at landing: ..." and additions end "Noted at landing, verified against the cached
copy." Every page quotation in them was asserted present on the cached page. In the applied file, 16 lines
were rewritten, 3 patched, 3 added and 1 dropped. In the b58 file, 1 line was patched.

- Woodland Phlox: the RHS range was called "narrower". It is wider (3.9-19.7 in both ways against 6-12 by
  10-20), and RHS's own prose "to 30cm in height" matches NC State's top.
- Dwarf Crested Iris: the line said RHS makes no statement about edibility or toxicity. RHS's "Potentially
  harmful" field reads "Harmful if eaten ... Pets: Harmful if eaten." Also added NC State's own prose, "reaches
  only 4-9 inches tall", against its 6-9 in Dimensions block.
- Fringed Bleeding Heart: RHS was called "roughly consistent". Its height (19.7-39.4 in) does not overlap NC
  State's 6-18 in; only the spread overlaps.
- Goat's Beard: "four cited" pages were really three. The RHS figures called "genus-adjacent" come from the
  species page. Added RHS's pollinator caveat: "Great for pollinators, but only of you get a male form" [sic].
- Cardinal Flower: the line said RHS is silent on eating. It reads "Harmful if eaten; skin irritant ...".
  The Poison Part list had Flowers only; it is Flowers, Fruits, Leaves, Roots, Sap/Juice, Seeds and Stems. RHS
  size had been called "consistent", but its height (19.7-39.4 in) is below NC State's 48-60 in.
- Celandine Poppy: dropped the literal unknowns line "placeholder".
- Early Meadow-rue: "three reachable pages" were really two (fixed twice). Added NC State's "This plant is
  pollinated by the wind."
- New York Ironweed: RHS had been called "consistent in range". The height is close, but the spread (19.7-39.4
  in) only overlaps the bottom of 36-48 in.
- Swamp Milkweed (safety): the Poison Part list had been cut off at "Flowers, Fruit..."; it is Flowers, Fruits,
  Leaves, Roots, Seeds and Stems. Added the Poison Symptoms text and RHS's "Harmful if eaten ..." warning.
  Removed the claim that toxicity is recorded only when is_edible is true.
- False Aster: the UMD "18 -36 inches ... Blue Star, Esther, Golden Spray, and Pink Cloud" sentence ends the
  Aster paragraph, so it describes aster cultivars. The Boltonia paragraph gives no size.
- Sneezeweed: Seeds was added to the Poison Part list. The NC State sizes, misquoted as "60 in.; 36-72 in.",
  are now the page's 3-5 ft by 2-3 ft, which its prose repeats.
- Indian Grass (added): the flag rests on the Attracts field's "Butterflies" alone. The page also tags the grass
  "#larval host plant", and its Wildlife Value text names no pollinator.
- Purple Prairie Clover: the line called the edibility "conditional" and "not ... eaten as food". No page
  states a condition. Because the app shows true as "grown to eat" with no condition, the line now states the
  basis plainly (tea from the leaves, roots chewed) and records that no page names a preparation or toxic part.
- Rough Goldenrod: the line had said the page's "grows to 4 feet" raised no contradiction. It sits below the
  60-in top taken from "2-5 foot stems", and it is in a later paragraph, not the same one.
- White False Indigo: the full Poison Part list is Bark, Flowers, Fruits, Leaves, Roots, Sap/Juice, Seeds and
  Stems.
- Canada Anemone (b58 file): the conversion note now matches the 3.9 rounding.

One auditor note was checked and NOT applied. Golden Crown's auditor said qc.py shows 2 "Toxic" hits, not the 6
the researcher reported. qc.py shows 6: the three "non-toxic for ..." tags appear twice, so the line stands.

## verify_quotes, per touched file

- b51-native-woodland-2: 107 hit, 0 MISS, 0 inconclusive, 30 skipped
- b52-native-woodland-3: 101 hit, 0 MISS, 0 inconclusive, 16 skipped
- b53-native-woodland-and-wet-meadow: 113 hit, 0 MISS, 0 inconclusive, 36 skipped
- b54-native-meadow: 92 hit, 0 MISS, 0 inconclusive, 25 skipped
- b55-native-meadow-2: 108 hit, 0 MISS, 0 inconclusive, 27 skipped
- b56-native-meadow-3: 104 hit, 0 MISS, 0 inconclusive, 33 skipped
- b57-native-prairie: 102 hit, 0 MISS, 0 inconclusive, 29 skipped

There is no MISS anywhere, and no SKIP or INCONCLUSIVE on any citation whose claim names one of the six fields.
Run on the new citations alone, verify_quotes gives 115 hit, 0 MISS, 0 skipped for the applied file and 9 hit,
0 MISS, 0 skipped for the b58 file. The 196 skips are all older citations: 193 to MOBOT or Clemson pages cached
as ProxyError entries (166 plantfinder.mobot.org, 22 missouribotanicalgarden.org, 5 hgic.clemson.edu), and 3 to PDFs.

## Tests

`pytest tests/test_tranche_invariants.py tests/test_claim_ingest.py` gave 3,886 passed and 1 failed. The
invariants all pass. The one failure is the expected ingest count assert: claims_written = 5,978 against the
test's 5,558 (HEAD). The 5,978 is a whole-tree count. It includes the other session's uncommitted landings,
+241 in b58, b59, b7, b71, b72, b75-b79 and b8. This chunk's own delta is +179, so it would read 5,737 with
nothing else in the tree, and +15 more once the b58 file is applied.

## Left for you to decide

- Cardinal Flower and Swamp Milkweed could take is_edible false. Each has RHS "Harmful if eaten" plus NC State
  "Poisonous to Humans", the same evidence that made Black Cohosh false in wave 1. Fringed Bleeding Heart,
  Sneezeweed and Golden Ragwort have NC State poison blocks only. No researcher proposed false, so all five
  landed null, with the toxicity text in unknowns.
- Celandine Poppy's size can be landed on a re-run: Height 1 ft. 0 in. - 1 ft. 2 in. (12-14) and Width 0 ft. 9
  in. - 1 ft. 0 in. (9-12), both clean single-line quotes on the cached NC State page.
- Rough Goldenrod keeps 24-60 in from "2-5 foot stems". The same page's "grows to 4 feet" would cap it at 48.
- Indian Grass keeps attracts_pollinators true on a structured "Butterflies" alone. It meets the rule, but it is
  weak, and it is disclosed.
- Goat's Beard is true with RHS's male-form caveat disclosed.
- The 11 held corrections leave bare structured values as quotes where the auditors offered fuller sentences.
  All of those sentences are on the pages.
- Queen of the Prairie landed nothing. Its anchor page (MOBOT) is unreadable from this machine, so retry it when
  MOBOT is reachable.
- merge_backfill always writes indent 2, so every indent-1 batch file (b52 onward here) gets a whole-file
  reflow. A change that preserves each file's own indent would make these diffs readable.

Scratch work is in the session scratchpad under `r3c1/`, not in the repo. That includes the repair script
(`repair.py`, which reads the untouched workflow output and asserts every edit), the checker, the record-level
diff, and the verify_quotes outputs.
