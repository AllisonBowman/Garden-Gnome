# Size backfill, wave 1 chunk 3 -- landing summary

Landed 2026-09-27 from `size-w1-chunk3-result.json` (40 species over 9 batch files, 0 unverified, 0 no_research,
2 fields already nulled on audit, 31 review lines), following `BACKFILL_LANDING_BRIEF.md`. Not committed.

Because another session was merging a different chunk into `b34-hemlock-and-more.json` at the same time, the
corrected payload was split after review. `size-w1-chunk3-result.json` now holds the 37 entries for the other eight
batch files, and those were applied. `size-w1-chunk3-b34-result.json` holds the three b34 entries (Rose of Sharon,
Saucer Magnolia, Sweet Cherry). Those were reviewed and planned but NOT applied, and are waiting for that merge to finish.

## Verification basis

Every page was read from this worktree's `scripts/catalog/.quote_cache`, not fetched live: the sandbox proxy blocks
these hosts. Verification was therefore against the cached copies. The landing instructions say these were seeded
between early and mid September. The file dates show 2026-09-05 for 44 of the 45 pages this chunk cites; the 45th,
extension.psu.edu/strange-fruit, is dated 2026-09-27. So are several uncited UF and Clemson pages consulted for the
unknowns corrections below (FP370, ST358, FP214, FP351, FP457, FP189, Clemson Blackberry); this chunk's own agents
cached them earlier today. A page may have changed since its copy was taken. All 45 cited pages were cached with
status ok (44 remain cited once Blackberry's two citations were dropped), and no landed citation points at Missouri Botanical Garden, Clemson, or edis.ifas.ufl.edu/publication/ST295
(HTTP 410 Gone).

One cache anomaly matters. The entry for plants.ces.ncsu.edu/plants/dryopteris-erythrosora/ (Autumn Fern) is a
7.7 KB flattened, lower-cased text dump, not raw HTML. qc.py therefore cannot show element boundaries on it, and the
researcher's quote came back lower-cased. The b43 record's existing citations already rely on this entry. It is
worth re-warming with warm_cache.py outside the sandbox. The Autumn Fern de-splice below follows the NC State
Dimensions template, which renders "Height: ..." and "Width: ..." as separate lines on every other NC State page in
this chunk.

## Merge plan totals

For `size-w1-chunk3-result.json` (applied), the plan printed "problems: none". It wrote 36 species, 166 fields and
106 citations across 8 batch files. The 166 fields are 128 size bounds (32 species), 28 attracts_pollinators and
10 is_edible (6 true, 4 false). Blackberry wrote nothing: both its flags were nulled at landing (below). Claims per
file, measured against HEAD (none of these files changed in HEAD during the landing):

- b35-ginkgo-and-more: 47 -> 61 (+14)
- b37-sweetgum-and-more: 50 -> 92 (+42)
- b39-cherry-laurel-and-more: 45 -> 86 (+41)
- b4-tricky-cases: 65 -> 71 (+6)
- b40-gesneriads-and-annuals: 73 -> 83 (+10)
- b41-grasses-and-groundcovers: 44 -> 81 (+37)
- b43-ferns-succulents-and-more: 85 -> 93 (+8)
- b45-fruit-and-carnivores: 80 -> 88 (+8)

That is +166 claims in total, one per field. Every new value pairs to a citation.

A semantic check against HEAD confirmed that the merge only added: every pre-existing field value, citation,
unknowns line and normalization in the eight files is unchanged. The git diff also shows 357 deleted lines, which
are serialization only. Records whose last key was `water_regime` gained a trailing comma. Some strings the files
stored as JSON escapes (the six characters \u2014 for an em dash) are now written as the characters themselves, because merge_backfill writes with
`ensure_ascii=False`.

For `size-w1-chunk3-b34-result.json` (plan only, not applied), the plan printed "problems: none" against b34 as it
now stands, with the other session's uncommitted merge in it. It would write 3 species, 15 fields and 9 citations:
Rose of Sharon 5, Saucer Magnolia 4 and Sweet Cherry 6. That is +15 claims when applied.

## The 31 review lines

The rule applied is the brief's: a correction goes in only if the stored quote is spliced (it carries U+23CE, or a
label is glued to its value) and the correction is that same text as the page renders it, or a substring of the
stored quote. Every correction, held or applied, was confirmed against the cached page with qc.py. When a correction
was held, the stored spliced quote was de-spliced to its own value instead: a substring of the stored quote that is
its own rendered line on the page. The script asserted that mechanically for all 24 quote edits.

- Size de-splices, APPLIED (20 lines, 11 quotes): Ginkgo (4 lines), Bugleweed (4), Butterfly Bush (2), Cherry
  Laurel (4), Flowering Tobacco (2) and Moss Phlox (4). Each correction is NC State's "Height: ..." or "Width: ..."
  line. It is a substring of a stored "Dimensions: ⏎ Height: ... ⏎ Width: ..." quote (for Moss Phlox, the same
  labels glued together without the marker) and its own rendered line on the page. No value changed.
- Size corrections, HELD (2 lines): Rockspray Cotoneaster, mature_height_in and mature_spread_in. The correction
  "shrub that reaches 2-3 feet tall and 6-8 feet wide" is the page's description prose, which is a different element.
  The stored U+23CE quote was de-spliced to "Height: 2 ft. 0 in. - 3 ft. 0 in." and "Width: 6 ft. 0 in. - 8 ft. 0
  in.". The values stand (24-36 in by 72-96 in).
- Pollinator de-splice, APPLIED (1 line): Bugleweed. "Plants for pollinators" is a substring of the stored RHS quote,
  which glued two separate tags ("Plants for pollinators Herbaceous Perennial").
- Pollinator corrections, HELD (6 lines), each a different page element. Butterfly Bush's "Attracts Pollinators" is
  the Play Value field. Cherry Laurel's is a slice of the page's hashtag list. Rockspray Cotoneaster's "Attracts birds
  and bees" is Wildlife Value. Flowering Tobacco's moth sentence is description prose. Moss Phlox's "Flowers attract
  hummingbirds, butterflies, skippers, and bees." and Purple Passionflower's "This plant supports provides nectar
  for pollinators ..." are both Wildlife Value sentences. Each stored quote was NC State's "Attracts:" list, spliced
  with U+23CE or glued to its label, and was de-spliced to one list item: "Pollinators" for five, and "Bees" for
  Cotoneaster, whose list is only Bees and Songbirds. All six values stand.
- Edibility correction, HELD (1 line): Firethorn. The correction "Fruit are ornamental - not to be eaten." is RHS's
  "Potentially harmful" text. is_edible is null and has no citation to correct, so nothing was applied. The two
  unknowns lines that said no page addresses eating, and that no harm information exists, were rewritten to record
  the warning. is_edible stays null (see "left for you" below).
- Unknowns disclosure (1 line): Buttercup, "Sap/Juice". Confirmed. NC State's Poison Part list is Leaves, Roots,
  Sap/Juice and Stems, so the note was missing two parts, not one. The line was corrected, and it now also records
  the page's "Poisonous to Humans" heading and its self-contradiction ("Causes Contact Dermatitis: No" next to a
  "#contact dermatitis" tag).

## Other citation repairs (brief step 2, not review lines)

- Bugleweed, NC State: the stored quote "Attracts: ⏎ ... Bees ⏎ Hummingbirds ⏎ Moths ⏎ Songbirds" was de-spliced
  to "Bees". This left the review line's correction free to go to the RHS citation it actually fits.
- Climbing Hydrangea, RHS: "Award of Garden Merit Plants for pollinators Climber Wall Shrub" is a slice of RHS's run
  of separate tags. It was de-spliced to "Plants for pollinators", the same form as the Bugleweed correction.
- Autumn Fern, NC State: "dimensions: height: 1 ft. 6 in. - 2 ft. 0 in. width: 2 ft. 0 in. - 3 ft. 0 in." glues a
  label to two values and is lower-cased. It was de-spliced to "Height: 1 ft. 6 in. - 2 ft. 0 in." and "Width: 2 ft.
  0 in. - 3 ft. 0 in." (case-insensitive substrings; see the cache anomaly above).
- Cooper's Hardy Ice Plant: the spread claim label said "already in inches" for a feet figure; it now says
  "converted to inches". The value, 12-24, was already right.

All 74 size values were re-derived from their quotes and match. Madagascar palm's decimal inches (98.4-157.5 by
59.1-98.4, from RHS metres at 39.37) follow the 36 RHS-band conversions already in the corpus, and its "Max Height
2.5-4 metres" is a single run in RHS's summary block.

## Fields nulled at landing, and why

- is_edible on Sweetgum, Virginia Sweetspire and Switchgrass. The only support in each case is NC State's "Play
  Value: Edible fruit" and "Fruit Value To Gardener: Edible" tags, plus "#edible seeds" and an "edible garden"
  theme. Each page's own fruit description contradicts people eating the fruit. Sweetgum's is "the infamous gum
  ball", "hard, beak shaped, bristly fruiting capsules". Sweetspire's is "Woody capsules" whose "Seeds are eaten by
  songbirds". Switchgrass's is a 1/8-inch grain whose "Seeds are eaten by songbirds and small mammals". No page says
  any part is eaten by people, which rule 6 requires. This is the same evidence this chunk's own auditor ruled
  insufficient for Summersweet, and a catalog where one dry capsule is food and its twin is not would be
  inconsistent. The is_edible citation was dropped in each case, and a "removed on audit at landing" line was added.
- is_edible and attracts_pollinators on Blackberry (Rubus fruticosus). Both citations were to NC State's Rubus
  allegheniensis page, a different species. The researcher rejected that same page for size as "a different
  species", and the batch record cites it only for its name note. Rule 6 forbids inferring edibility from a genus of
  edibles. French marigold was held on the same wrong-taxon ground in wave 1. Both citations were dropped, so
  Blackberry writes nothing and its unknowns do not reach b45.
- The two fields nulled on audit stay null: Summersweet is_edible (a bare "Edible fruit" tag) and Switchgrass
  attracts_pollinators (larval-host prose, no pollinator named).

Lavender's is_edible true was kept. NC State types the whole plant "Plant Type: Edible" and gives "Flower Value To
Gardener: Edible", nothing on the page contradicts it, and its low-severity toxicity (Flowers, Leaves, Stems;
linalool) is already in unknowns.

## Left for you to decide (not done at landing, because no researcher proposed these values)

- Firethorn and Rockspray Cotoneaster could take is_edible false. On both, RHS reads "Fruit are ornamental - not to
  be eaten.", and NC State adds "If ingested, the fruits can cause stomach upset." for Cotoneaster. Both are now
  recorded in unknowns.
- Blackberry's is_edible can be re-cited properly. Clemson's Blackberry factsheet names Rubus fruticosus ("highly
  valued by wildlife and humans alike"), and RHS's grow-your-own guide gives "fruits to eat fresh, cook in desserts
  ... and make into jam". Neither is cited yet.

## Unknowns corrected (20 lines replaced, 3 disclosures added)

Six lines misstated why a page was not used. Each said an ask.ifas.ufl.edu page "refused this machine", but every
one is cached and readable:

- Saucer Magnolia, FP370: this is the 'Lennei' cultivar page ("Height: 20 to 25 feet", "Spread: 15 to 25 feet"),
  excluded by the cultivar rule.
- Purple Passionflower, FP457: it agrees with the recorded values (fruit "attractive and edible", attracts
  butterflies and hummingbirds, a vine).
- Sweetgum, ST358: it gives 60-75 ft by 35-50 ft, which overlaps NC State with a lower top height.
- Dwarf Fothergilla, FP214: it gives 4-6 ft by 4-6 ft. Together with NC State's own prose (3-6 by 2-6 ft), that
  makes the anchor block (18-36 by 24-48 in) the low outlier. This is now disclosed.
- Edging Lobelia, FP351: its 12-24 in spread is wider than NC State's 6-12 in. This is now disclosed.
- Blackberry, HS1352: a cultivar-choice guide with no size figures. This line does not land.

Other misstated facts corrected:

- Purple Passionflower: the RHS "(F)" page is the species profile, not a cultivar.
- Sweet Cherry: the UGA/PSU line said the pages were both unqueried and searched. It now records what they say.
- Blue False Indigo: Clemson does give a size, "3 to 4 feet tall by 3 to 4 feet wide".
- Heavenly Bamboo: two photo captions do name a bee.
- Bugleweed: RHS names no bee or moth.
- Cherry Laurel: Poison Part is Leaves, Seeds and Stems.
- Firethorn: two lines rewritten to record the RHS warning.
- Rockspray Cotoneaster: the harm statements from both pages are recorded, and RHS's spread (39-59 in) is noted as
  well below NC State's 72-96 in rather than "broadly consistent".
- Flowering Tobacco: RHS height agrees with NC State; only its spread is narrower.
- Pink Muhly Grass: UF gives ranges, not single values.
- Autumn Fern: IFAS's spread ("no more than 24 inches") conflicts with NC State's 24-36 in rather than corroborating
  it.
- Buttercup: the poison parts, as above.

Disclosures added:

- Ginkgo: RHS "Potentially harmful" ("Seeds harmful if eaten ... Seed TOXIC to pets"). The seed is the part NC State
  says is eaten after preparation.
- St. John's Wort: RHS's larger sizes ("Height is 60cm with a spread of 1.2m or more").
- Pink Muhly Grass: RHS's smaller sizes (0.5-1 m by 0.1-0.5 m).

## verify_quotes, per touched file

No MISS, SKIP or INCONCLUSIVE on any citation whose claim names one of the six backfill fields. All 106 new
citations are HITs.

- b35-ginkgo-and-more: 98 hit, 5 MISS, 0 inconclusive, 31 skipped
- b37-sweetgum-and-more: 118 hit, 0 MISS, 0 inconclusive, 28 skipped
- b39-cherry-laurel-and-more: 125 hit, 0 MISS, 0 inconclusive, 27 skipped
- b4-tricky-cases: 44 hit, 3 MISS, 0 inconclusive, 14 skipped
- b40-gesneriads-and-annuals: 106 hit, 1 MISS, 0 inconclusive, 39 skipped
- b41-grasses-and-groundcovers: 96 hit, 1 MISS, 0 inconclusive, 41 skipped
- b43-ferns-succulents-and-more: 106 hit, 0 MISS, 0 inconclusive, 48 skipped
- b45-fruit-and-carnivores: 242 hit, 0 MISS, 0 inconclusive, 108 skipped

The 10 MISSes all predate this landing and are on other fields:

- b35: Bougainvillea common_name, soil_drainage and water_regime; Purple Passionflower outdoor_sun_exposure and
  toxicity_detail.
- b4: the name notes for Bird of Paradise, Spiderwort / Inch Plant and Alocasia 'Polly'.
- b40: Florist's Gloxinia direct_sun_hours_max.
- b41: Pink Muhly Grass is_houseplant.

The skips are older citations to pages the cache lacks, mostly MOBOT, Clemson and UF. verify_quotes tried 31 of them
live, the sandbox denied them, and the 31 error entries that wrote to the cache were deleted. Fifteen other error
entries written today by other sessions' runs were left alone: 12 for b84-edibles URLs, 2 for b46 and 1 for b51. So
was a ProxyError entry for ST295, written earlier today by this chunk's auditor, which nothing cites.

## Tests

`tests/test_tranche_invariants.py` passes (3,826 passed on its own). The combined run with `test_claim_ingest.py`
gave 3,832 passed and 1 failed, and the one failure is the expected count assert. It prints claims_written = 5,451
against the test's 4,993 (HEAD, after the chunk 4 commit d08d1b3). 5,451 includes other sessions' uncommitted
landings in the working tree. This chunk's own delta is +166, with +15 more when the b34 file is applied.
`tests/test_claim_ingest.py` was not edited.
