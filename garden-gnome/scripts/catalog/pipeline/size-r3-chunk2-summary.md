# Size backfill, round 3 chunk 2 -- landing summary

Landed 2026-09-27 from `size-r3-chunk2-result.json` (40 species over 8 batch files: b7, b58, b59, b71, b72, b75, b76,
b77; 0 unverified, 0 no_research; 2 fields already nulled on audit; 43 review lines), following
`BACKFILL_LANDING_BRIEF.md`. The whole chunk was applied. No other session was writing these batch files. Not committed.

## Verification basis

Every page was read from this worktree's `scripts/catalog/.quote_cache`, not fetched live, because the sandbox proxy
blocks these hosts. **Verification was therefore against cached copies**, and a page may have changed since its copy was
taken. All 42 pages this chunk cites were cached with status ok. Each was checked to be real HTML, because chunk 3 found
one page cached as a lower-cased text dump. By file date, 25 were cached on 2026-09-05 and 15 on 2026-09-17. The other 2
were cached today at 12:48-12:49 by this chunk's own agents: NC State's Dryopteris cristata page and RHS's Eleocharis
palustris page. No landed citation points at Missouri Botanical Garden or Clemson, so no value rests on a host that
refuses this machine.

qc.py and the checks behind this landing never fetched anything, because every page they read was already cached.
verify_quotes did try nine uncached URLs, all belonging to older citations in the touched files. Seven were b7 herb
citations: six MOBOT pages and Clemson's cilantro page. The other two were NC State's and RHS's Drosera rotundifolia
pages, for b75's Round-leaved Sundew. The sandbox denied all nine, and each denial wrote a ProxyError entry. Exactly those
nine entries were deleted afterwards, and the cache's file set is back to the 1,977 entries it held before. Older error
entries for URLs these files cite (42 ProxyError, 2 ConnectError) were left alone.

## Merge plan totals

After the repairs below, `merge_backfill.py` printed "problems: none". It also printed none on the unrepaired file,
because what it cannot see are quote-level defects. It wrote 37 species, 171 fields and 102 citations across all 8 files.
The 171 fields are:

- 142 size bounds: 35 species with all four, plus Sideoats Grama with the two maxes only.
- 22 attracts_pollinators: 21 true, 1 false.
- 7 is_edible: 6 true, 1 false.

Royal Catchfly, Tall Meadow Rue and Tussock Sedge wrote nothing. Their researchers found no value on any readable page,
so their unknowns do not reach b59 or b76. Claims per file, measured with the loader against HEAD:

- b7-culinary-herbs: 49 -> 55 (+6)
- b58-native-prairie-2: 24 -> 37 (+13)
- b59-native-prairie-3: 23 -> 51 (+28)
- b71-native-ferns-and-a-sedge: 30 -> 54 (+24)
- b72-native-wetland-perennials: 34 -> 62 (+28)
- b75-native-bog-and-orchids: 35 -> 64 (+29)
- b76-native-wet-meadow-perennials: 39 -> 69 (+30)
- b77-native-wetland-ferns-and-rushes: 28 -> 41 (+13)

That is +171 claims, one per field, and no file has an unsupported field. Every new field pairs to one of its own new
citations; none was captured by an older citation. A semantic check confirmed that each file equals its HEAD version
plus exactly this chunk's additions: the new field values, the appended citations and unknowns, and one "size backfill"
normalization line. Nothing that was already there changed.

The git diff is bigger than the change. b58 and b59 were stored with one-space indentation, and merge_backfill always
writes two-space, so both files were reflowed top to bottom (about 1,950 changed lines each). `git diff -w` shows the
real change: 1,083 insertions and 82 deletions across the 8 files, where each deletion is a line that gained a trailing
comma. The instructions say not to edit app/data/verified by hand, so the two files were left as the merge wrote them.
Six more files (b52 to b57) use one-space indentation and will reflow the same way the first time a backfill touches
them.

## The 43 review lines

All 43 were "quote correction proposed ... NOT applied" lines. There were no "REFUTED but unmapped field" lines. The rule
applied is the brief's: a correction goes in only if the stored quote is spliced (it carries U+23CE or glues a label to
its value) and the correction is the same text as the page renders it, or a substring of the stored quote. Every
correction was found on its page with qc.py (1 hit each). Each was also placed mechanically in its NC State page field,
the `<dt>` label its `<dd>` sits under.

- **Size de-splices, APPLIED (34 lines, 18 quotes).** Wild Quinine (4 lines), New Jersey Tea (4), Rough Blazing Star
  (2), Pennsylvania Sedge (2), Sensitive Fern (4), Blue Flag (2), Orange Fringed Orchid (4), Allegheny Monkey Flower (4),
  American Blue Vervain (4) and Broadleaf Cattail (4). Each stored quote was NC State's "Dimensions: ⏎ Height: ... ⏎
  Width: ...", or the label plus one line. Each correction is its own "Height: ..." or "Width: ..." element and a
  substring of the stored quote. No value changed. Wild Quinine had one citation covering both dimensions, so it became
  two citations, one per dimension.
- **Edibility de-splices, APPLIED (2 lines).** New Jersey Tea ("Tea can be made from the dried leaves.") and Broadleaf
  Cattail (the full four-sentence Edibility text). Each stored quote glued the "Edibility:" label to its value across
  U+23CE, and each correction is the value element alone.
- **Pollinator corrections, HELD (7 lines).** Each proposed quote comes from a different page field than the stored one.
  Six are Wildlife Value text:
  - Wild Quinine: "Attracts bees, wasps, and beetles."
  - New Jersey Tea: its nectar sentence.
  - Rough Blazing Star: "Attracts pollinators."
  - Allegheny Monkey Flower: "Pollinated by bumblebees."
  - American Blue Vervain: the long- and short-tongued bees sentence.
  - Purple-headed Sneezeweed: "Flowers attract pollinators and butterflies."

  The seventh, Orange Fringed Orchid's nectar-spur sentence, is Description text. Six of the stored quotes were NC
  State's "Attracts:" list spliced with U+23CE. Each was de-spliced to one list item that is its own element on the
  page. That item is "Pollinators" for five of them. For Orange Fringed Orchid it is "Butterflies", because its list is
  only Butterflies and Moths and its Wildlife Value reads "Butterflies and moths pollinate the flowers." Sneezeweed's
  stored quote was already a clean "Pollinators" element and was left alone. All seven values stand.

## Other citation checks (brief step 2)

All 102 citations were checked against their cached pages three ways: for U+23CE, with verify_quotes' own presence test,
and for whether each lies inside one block element. After the repairs, no quote carries U+23CE and all are present. The
review lines had covered all 25 spliced quotes in the chunk.

Seven RHS size quotes keep the form "Max Height         1-1.5 metres": Common Rush's spread, plus both dimensions for Bog
Myrtle, Leatherleaf and Common Spike-rush. RHS's summary card puts the label in an `<h2>` and the value in a `<p>` in a
sibling div. But qc.py shows the pair as one run with no U+23CE, chunk 3 accepted Madagascar palm's quote on that ground,
and 31 RHS size citations at HEAD use the same form. They were kept for consistency. If they should be the bare value
("1-1.5 metres", as b89 did for Montbretia), the swap is mechanical, and the claim text already names the dimension.

The UGA quote for Sideoats Grama, "Size:  3 feet tall and 2 feet wide", is one paragraph (`<p><strong>Size:</strong> 3
feet tall and 2 feet wide</p>`) inside the Side Oats Grama entry. The same line also appears under other grasses on that
page.

All 72 size ranges were re-derived from their quotes and match:

- NC State feet-and-inches, converted to inches.
- RHS metres at 39.37, rounded to one decimal (the corpus convention).
- Common Rush: NC State's "12 - 36 inches in height", as given.
- Sideoats Grama: UGA's single figure, filling the max only (one published figure fills one end).

No species in the chunk is a climber, and no cultivar figure was used. The RHS 'Spiralis' page for Common Rush was read
and set aside.

## Fields nulled at landing, and why

- **is_edible on Marsh Marigold (Caltha palustris).** NC State's Edibility field says "Spring greens, in small quantities
  and properly prepared, for salads." The same page's Poison Symptoms end "No part of this plant should ever be eaten
  raw." The toxic principle is protoanemonin, and the poison part is the leaves, which are the greens. It is poisonous
  raw and edible only after preparation, so under the Pokeweed ruling it lands null, not true. The citation was dropped
  and an "is_edible -- null at landing" line added. b72's existing toxicity_detail already carries the poison block.
- **is_edible on Ostrich Fern (Matteuccia struthiopteris).** NC State says "Fiddleheads can be cooked and consumed".
  Penn State Extension, already cited in the b71 record, says "CAUTION: Tender fiddleheads of ostrich fern are TOXIC if
  not fully cooked." The fiddleheads are the only part any page calls food, so the same rule applies: null, citation
  dropped, null-at-landing line added.
- **The two fields nulled on audit stay null.** Ostrich Fern attracts_pollinators rested on PSU's "Pollinator species
  are attracted to the nectar found on the fronds.", said of a fern, which does not flower. Pennsylvania Sedge
  attracts_pollinators rested on NC State's "Attracts: Butterflies", which is larval hosting.

This follows the Pokeweed and Japanese Yew precedent. The researchers' "is_edible is true but conditional" lines stay in
unknowns, and the null-at-landing line that supersedes them follows directly.

## Values kept that deserve a look

- **Tea-only edibility.** Lead Plant and New Jersey Tea land is_edible true on tea alone. NC State's Edibility field
  reads "Dried leaves make a yellow-colored tea." for one and "Tea can be made from the dried leaves." for the other.
  Neither page names a poison. This matches the corpus, where Purple Coneflower (b16, "Herbaceous parts may be steeped as
  a tea"), Yaupon Holly (b48), Balsam Fir (b69) and Mugo Pine (b88) are true on tea. If tea should not count as "grown to
  eat", all six should change together.
- **Nodding Onion** lands true on "The bulb is edible but is rarely used as better plants exist for this purpose."
  RHS's "TOXIC to pets" is in unknowns.
- **American Boneset** lands is_edible false on NC State's Edibility field, "Toxic and bitter". That is a page denying
  food use.
- **Sideoats Grama** lands attracts_pollinators false on Penn State's "Grasses do not have nectar to attract
  pollinators.", on a page that lists sideoats grama in its tables.
- **Sage, Pickerelweed and Broadleaf Cattail** are true with no preparation condition on any page. Sage's flower caution
  ("should not be eaten in large amounts") is in unknowns.

## Unknowns corrected (9 lines, each now marked "corrected at landing")

- **Sideoats Grama, New Jersey Tea and Nodding Ladies' Tresses.** Each line said RHS's missing size was probably
  JS-rendered or not captured by the fetch. The cached pages are complete. RHS simply publishes no size for these species:
  the Size block holds only "Time to Maturity: No preference", as on its Royal Catchfly and Tussock Sedge pages.
- **Northern Maidenhair Fern.** The line called RHS's smaller range "likely-cultivar-influenced". The page is the
  species profile (Adiantum pedatum L.) and names no cultivar.
- **Sensitive Fern and Allegheny Monkey Flower.** Each counted Missouri Botanical Garden among the pages read or found
  silent. It refused this machine and was never read, as each record's own later line says.
- **Woolgrass.** The line said "four cited pages" but listed three. The fourth, MOBOT, was unreadable.
- **Blue Flag.** Poison Part is Roots, Sap/Juice and Seeds, not Roots alone.
- **Great Blue Lobelia.** Poison Part is Flowers, Fruits, Leaves, Roots, Sap/Juice, Seeds and Stems, not Flowers alone.

The other unknowns claims about pages were checked against the cache and stand:

- every RHS size figure the lines quote
- the UF FP055 and FP490 figures
- UMD's sage, lobelia and wool-grass lines
- the NC State poison blocks for Moccasin-flower, Sneezeweed and Marsh Marigold
- NC State's vervain ethnobotany text
- the PSU fiddlehead caution

## Left for you to decide

- **Conditionally edible plants.** Ostrich Fern is the poisonous-raw rule at its sharpest: fiddleheads are sold as a
  vegetable, but the only food statement comes with "TOXIC if not fully cooked". Ostrich Fern, Marsh Marigold, Pokeweed
  and Japanese Yew now all wait on one catalog decision about how a conditionally edible plant should read.
- **Two candidates for is_edible false.** Blue Flag and Great Blue Lobelia could take false. RHS's Potentially harmful
  field reads "Harmful if eaten." for Blue Flag and "Harmful if eaten; skin irritant." for the lobelia, and NC State lists
  both as poisonous. Painted Buckeye (b74) is false on similar evidence. No researcher proposed false, so both stay null.
- **Crested Woodfern's size** follows NC State (12-36 in by 24-72 in). RHS gives 0.1-0.5 m by 0.5-1 m, about 4-20 in by
  20-39 in. The unknowns record both, and the anchor rule chose NC State.
- **The seven RHS label-and-value quotes**, above.
- **Order of commits.** Two other sessions have split out entries for these files and are holding them until this
  landing is committed: `size-r3-chunk1-b58-result.json` (b58) and `size-r3-chunk3-b77-result.json` (b77).
  merge_backfill rewrites whole files, so those should be applied only after this chunk's commit.

## verify_quotes, per touched file

There is no MISS, SKIP or INCONCLUSIVE on any citation whose claim names one of the six backfill fields. All 102 new
citations are HITs.

- b7-culinary-herbs: 99 hit, 1 MISS, 0 inconclusive, 26 skipped
- b58-native-prairie-2: 72 hit, 0 MISS, 0 inconclusive, 42 skipped
- b59-native-prairie-3: 87 hit, 0 MISS, 0 inconclusive, 25 skipped
- b71-native-ferns-and-a-sedge: 109 hit, 0 MISS, 0 inconclusive, 20 skipped
- b72-native-wetland-perennials: 121 hit, 0 MISS, 0 inconclusive, 36 skipped
- b75-native-bog-and-orchids: 103 hit, 0 MISS, 0 inconclusive, 22 skipped
- b76-native-wet-meadow-perennials: 136 hit, 0 MISS, 0 inconclusive, 49 skipped
- b77-native-wetland-ferns-and-rushes: 122 hit, 0 MISS, 0 inconclusive, 34 skipped

The one MISS predates this landing and is on another field: b7 Basil's cold-qualitative citation, which quotes RHS as
'H1C" (can be grown outside in summer, 5-10°C minimum)'. The 254 skips are all older citations whose pages are error
entries (250 ProxyError, 4 ConnectError). They are mostly MOBOT and Clemson, plus the two uncached Round-leaved Sundew
pages.

## Tests

`tests/test_tranche_invariants.py` passes on its own (3,880 passed). The combined run with `test_claim_ingest.py` gave
3,886 passed and 1 failed. The failure is the expected count assert: claims_written = 5,729 against the test's 5,558
(HEAD), which is exactly this chunk's +171. A re-run a few minutes later printed 5,799, because other sessions had by
then landed uncommitted claims into b8, b78 and b79 (+70). `tests/test_claim_ingest.py` was not edited.

## Landing decision added 2026-09-27 by the orchestrating session

Ostrich Fern (b71): is_edible restored to true. The brief's poisonous-raw rule was stated too broadly; the catalog nulls is_edible only for a poisonous plant with a marginal or folk food use (pokeweed, marsh marigold, yew arils), and keeps cook-before-eating foods such as elderberry and fiddleheads true with the condition in unknowns. Marsh Marigold stays null under that rule.
