# Size backfill, round 3 chunk 3 -- landing summary

Landed 2026-09-27 from `size-r3-chunk3-result.json` (20 species over b77, b78, b79 and b8; 0 unverified, 0 no_research;
1 field already nulled on audit; 18 review lines), following `BACKFILL_LANDING_BRIEF.md`. Not committed.

Another session was merging a different chunk into `b77-native-wetland-ferns-and-rushes.json` at the same time, and
merge_backfill rewrites whole files. So all 20 species were reviewed and corrected first, and then the payload was
split. `size-r3-chunk3-result.json` now holds the 16 entries for b78, b79 and b8, and those were applied.
`size-r3-chunk3-b77-result.json` holds the four b77 entries (Ebony Spleenwort, Marsh Fern, Netted Chain Fern, Royal
Fern). They were reviewed and planned but NOT applied, to wait for the other session's b77 work to be committed. That
work has since been committed (a084d50, round 3 chunk 2), and the b77 payload plans clean against it. Both files keep
the workflow's `{"landed", "unverified", "no_research"}` shape. The untouched workflow output was kept in the session
scratchpad while the repair ran.

## Verification basis

Every page was read from this worktree's `scripts/catalog/.quote_cache`, not fetched live: the sandbox proxy blocks
these hosts. Verification was therefore against the cached copies, and a page may have changed since its copy was
taken. The 18 pages the new citations point at are all cached with status ok and are real HTML, not text dumps. Ten
are dated 2026-09-27 (cached today by this chunk's agents), seven 2026-09-14 and one 2026-09-05 (Asparagus). No new
citation points at Missouri Botanical Garden or Clemson. Every value this chunk lands rests on NC State or RHS, so
nothing needed re-basing under the MOBOT/Clemson rule.

verify_quotes tried 8 older, uncached MOBOT and Clemson URLs in b78/b79/b8 live. The sandbox denied them, and the 8
error entries that wrote to the cache were deleted, and nothing else. The MOBOT and Clemson error entries this chunk's
research and audit agents wrote before this landing (12:57-13:00 today) were left alone.

## Merge plan totals

For `size-r3-chunk3-result.json` (applied), the plan printed "problems: none". It wrote 14 species, 70 fields and 42
citations across 3 batch files. The 70 fields are 56 size bounds (14 species), 10 attracts_pollinators (all true) and
4 is_edible (all true). American Spatterdock and Swamp Loosestrife wrote nothing, because their pages have no size,
edibility or pollinator data. Their unknowns do not travel, because merge_backfill appends unknowns only when it writes
a field. Claims per file, measured against HEAD (the two commits other sessions made during this landing, a084d50
and b5538c6, did not touch these three files):

- b78-native-aquatics-and-emergents: 39 -> 67 (+28)
- b79-native-dry-and-rocky: 45 -> 82 (+37)
- b8-veg-round1: 43 -> 48 (+5)

That is +70 claims, one per field. All 70 pair to the new citation written with them, not to an older citation. A
semantic check against HEAD confirmed that the merge only added: every pre-existing field value, citation, unknowns
line and normalization in the three files is unchanged, and each file gained the one standard normalization line. The
git diff also shows 32 deleted lines, which are serialization only: a record's last line (usually `water_regime`) or a
list's last line gains a trailing comma when something is appended after it.

For `size-r3-chunk3-b77-result.json` (plan only, not applied), the plan printed "problems: none" three times. The
first run was against b77 with the other session's uncommitted merge (+13 claims) in it, and the second was after the
tests. The last was against b77 as committed in a084d50, which is the state it will be applied to. It would write 4
species, 16 fields (all size bounds) and 8 citations: Ebony Spleenwort 8-20 by 8-20 in,
Marsh Fern 12-36 by 24-36, Netted Chain Fern 18-24 by 12-24, Royal Fern 60-72 by 24-36. That is +16 claims when
applied. None of the four holds any of the six fields in the working tree.

## The 18 review lines

The rule applied is the brief's: a correction goes in only if the stored quote is spliced (it carries U+23CE, or a
label is glued to its value) and the correction is that same text as the page renders it, or a substring of the stored
quote. Every correction was confirmed on the cached page with qc.py first, and the repair script asserted the
substring relation mechanically.

- Size de-splices, APPLIED (16 lines; 8 stored quotes became 10 single-line quotes). Each correction is NC State's
  "Height: ..." or "Width: ..." line, its own rendered line on the page and a substring of the stored quote. No value
  changed.
  - Golden Club (2 lines). The stored "Dimensions: Height: ... Width: ..." glued a label to two separate lines.
  - Southern Blue Flag Iris (4 lines). One U+23CE citation covered both stems, and it was split into a height
    citation and a spread citation (2 -> 3 citations).
  - Scaly Blazing-star (4 lines) and Threadleaf Coreopsis (4 lines). Each had a U+23CE "Dimensions:" splice.
  - Yellow Wild Indigo (2 lines). "Height: 2 ft. 0 in. - 3 ft. 9 in. Width: 2 ft. 0 in. - 3 ft. 0 in." glued two
    rendered lines without the marker, and was the only size citation for both stems. It was split in two (2 -> 3
    citations).
- Pollinator corrections, HELD (2 lines). Scaly Blazing-star's "This plant attracts hummingbirds, moths, butterflies,
  and other pollinators." is the description paragraph. Threadleaf Coreopsis's "Its nectar are attractive to
  butterflies and other pollinators." is the Wildlife Value field. Both are real page text but different elements from
  the stored quote, which was NC State's "Attracts:" list spliced with U+23CE. Each stored quote was de-spliced to its
  stacked value "Pollinators", as earlier chunks did. Both values stand; Blazing-star's list also names Bees,
  Butterflies, Hummingbirds and Moths, and Coreopsis's names Bees and Butterflies.

No held correction left a field unsupported.

## Other citation repairs (brief step 2, not review lines)

- Southern Blue Flag Iris, pollinators. The quote "butterfly friendly #Audubon" was a slice across two separate tag
  badges, with the first badge's "#" cut off. It was de-spliced to that first badge as rendered, "#butterfly friendly",
  which is the tag the claim names. The page also carries "#NC Native Pollinator Plant".
- Common Harebell, size. "Max Height 0.1-0.5 metres Max Spread 0.1-0.5 metres" glued RHS's Max Height card to its Max
  Spread card, and both citations used it. Each now quotes its own card: "Max Height         0.1-0.5 metres" and "Max
  Spread         0.1-0.5 metres". Both are substrings of the stored quote, in the per-field form the recent backfill
  landings use (b14, b27, b29, b30, b43). The values are unchanged at 3.9-19.7 in, from the metre band at 39.37 in/m,
  and RHS's prose "A perennial to 30cm in height" agrees.
- Round-headed Bush Clover, pollinators. The claim label credited "Bees, Butterflies, Pollinators, Small Mammals,
  Songbirds" to the Attracts field / Play Value, but its quote "Attracts Pollinators" comes from Play Value. The label
  now names each field separately, as chunk 2 did.

After the repair, all 50 citations in the two payloads (42 + 8) are present on their cached pages, checked with
verify_quotes' own presence test. None carries U+23CE, a label glued across a boundary, or height and width glued
together. All 72 size values (56 + 16) were re-derived from their quotes and match.

## Fields nulled at landing, and why

The brief first gave the edibility rule as "a plant poisonous raw and edible only after preparation lands null". The
coordinator narrowed it during the landing. is_edible goes null only for a plant that is poisonous AND whose food use is
marginal or folk: pokeweed shoots, marsh marigold, yew arils. A plant commonly grown or sold as food that must be
cooked first stays true on its own audited citation, with the cooking or toxic-part condition in unknowns: elderberries,
fiddleheads, dry beans, rhubarb stalks, potatoes. Both nulls below were re-checked under the narrower rule and stay
null. Neither is a food crop.

- is_edible on Golden Club (Orontium aquaticum).
  - Poisonous: NC State types it both "Edible" and "Poisonous". Its Poisonous-to-Humans block lists every part as
    poisonous, the roots and seeds it calls edible included: calcium oxalate, "easily destroyed by thoroughly cooking
    or drying the plant". Contact dermatitis is Yes.
  - Folk food use: the Edibility field is foraging advice for a wild bog plant ("Only collect roots and seeds from
    areas you know have NOT been treated with pesticides"). The parts are eaten only after boiling ("NEVER eat roots
    raw"; roots at least 30 minutes and seeds at least 45, changing the water). No readable page mentions it as a crop
    or as food for sale.
- is_edible on Green Arrow-arum (Peltandra virginica).
  - Poisonous: Medium severity (calcium oxylate; Flowers, Leaves, Stems).
  - Marginal food use: NC State does not type it Edible. The only edibility text on any page is "Plant is toxic, but
    cooking eliminates the toxic element.", which names no part people eat.

In each record the is_edible citation was dropped and a "removed on audit at landing" line was added. It gives the
reason under the narrower rule, cites Pokeweed (b30) and Japanese Yew (b85) as the same ground, and records the dropped
quote. The researcher's line that began "is_edible is TRUE" / "is_edible set true" was reworded to point at that
removal line, and its evidence was kept word for word.

The first version of both removal lines, already applied to b78, stated the broad rule as catalog policy: "A plant
poisonous raw and edible only after preparation lands null in this catalog". Anyone who later read that as precedent
would null elderberries, for example. So the result file was corrected and b78 was re-merged:

- Before the re-merge, b78 was checked to be byte-identical to HEAD plus this landing's merge, so nobody else had
  written to it.
- b78 was then restored from HEAD and re-applied with merge_backfill, which printed "problems: none".
- The re-merged b78 differs from the first apply only in those four unknowns lines. The claims and citations are
  unchanged.
- All three landed files are byte-identical to HEAD plus the final result file.

The one field nulled on audit stays null: Marsh Fern attracts_pollinators. NC State's "Attracts: Moths" is the larval
host entry for the Marsh Fern Moth, and the page says "No flowers."

Kept as true, re-checked under the narrower rule:

- Asparagus: a crop ("Plant Type: Cool Season Vegetable, Edible"), true under either wording. NC State's low-severity
  block is recorded in full in unknowns: contact dermatitis from handling raw young shoots, stomach trouble from the
  berries, and Poison Part Fruits and Stems.
- Broadleaf Arrowhead: not poisonous. "The tubers may be cooked or served raw", and no page has a poison or harm
  statement.
- Eastern Prickly Pear: not poisonous. The pads "can be eaten raw or cooked" once the bristles are removed, and the
  fruit is used for candies and jams. There is no Poisonous-to-Humans block, and the tags say non-toxic for cats, dogs
  and horses. The bristle and contact-dermatitis cautions are in unknowns.
- Three-leaved Stonecrop: the closest call.
  - Its food use is marginal: young stems and leaves "may be eaten raw", and later growth is briefly cooked.
  - No page classes it as poisonous. NC State has no Poisonous-to-Humans block and 0 hits for "poison" or "toxic".
  - Its cautions are in unknowns: large quantities upset the stomach, and the sap can irritate skin.
  - It would go null only if "can cause stomach upset" counts as poisonous.

## Marsh Fern's size (b77 payload)

The size comes from NC State's page for Thelypteris palustris subsp. pubescens ("Previously known as: Thelypteris
palustris var. pubescens"), the North American subspecies. The page gives its range as eastern Canada and the USA,
Bermuda, Cuba and parts of Mexico. A subspecies is not a cultivar, so the values were kept (12-36 by 24-36 in). The
researcher's line calling the page "species-specific" was replaced with a disclosure that names the subspecies and
notes that RHS's page for the species as a whole (0.5-1 m, about 19.7-39.4 in) broadly agrees. The citation's source
field already named the subspecies.

## Unknowns corrected (12 lines) and added (5)

Corrections are marked "corrected at landing". Added lines end "noted at landing, verified against the cached copy",
or are the two removal lines above. Each was checked on the cached page.

b77 payload:

- Ebony Spleenwort (the two lines the auditors flagged). NC State's "Deer, Heavy Shade" is its "Particularly
  Resistant To (Insects/Diseases/Other Problems)" field, not an Attracts field; the page has none. RHS's garbled
  conversion now reads 0.1-0.5 m, about 3.9-19.7 in.
- Marsh Fern: the subspecies line, as above.
- Netted Chain Fern. The line said "three cited pages" and named two; the third, MOBOT, refused this machine. UGA's
  "Size:" label had been run into its value, which the page renders on a separate line. The UGA figures are now given
  in inches (12-28 by 24-36), a wider height range and a wider spread than NC State's.

Applied payload:

- Golden Club and Green Arrow-arum: the reworded "is TRUE" lines, as above.
- Scarlet Rose Mallow. RHS's page has no size data at all (its Size section holds only "Time to Maturity: No
  preference"); the note had guessed the data was in a tab the fetch missed. UF/IFAS's spread (3-4 ft, 36-48 in)
  meets NC State's 24-36 in only at 36, so it is no longer called consistent. UF's height (4-8 ft) does contain
  NC State's 72-96 in.
- Southern Blue Flag Iris. NC State's Poison Part is Roots, Sap/Juice and Seeds; the note had left out Seeds. Its
  "Causes Contact Dermatitis: No" contradicts its own "#contact dermatitis" tag.
- Eastern Prickly Pear. The line said neither RHS nor MOBOT refused the fetch. MOBOT did refuse when the auditor tried
  it, and RHS has no size, edibility or pollinator field.
- Asparagus. The note said the "mature stems" are the poisonous part. The page says "Low poisonous toxicity of the
  plant are the fruits and stems." without separating young from mature, and advises gloves when handling raw shoots.
  The page's own words are now quoted.

Disclosures added:

- Round-headed Bush Clover: NC State's prose width, "1 to 3 feet wide" (12-36 in), is wider than the Dimensions
  block's 1-2 ft used here.
- Threadleaf Coreopsis: RHS gives 0.5-1 m by 0.1-0.5 m (about 19.7-39.4 by 3.9-19.7 in). The heights agree and RHS's
  spread is narrower. RHS also tags the species "Plants for pollinators".
- Three-leaved Stonecrop: NC State's "The sap can irritate the skin of some people and the leaves, eaten in quantity,
  can cause stomach upsets."

## verify_quotes, per touched file

There is no MISS, SKIP or INCONCLUSIVE on any citation whose claim names one of the six backfill fields. All 42 new
citations are HITs. Against the HEAD copies, the hit counts rose by exactly the new citations (b78 +16, b79 +23,
b8 +3), and the skip counts are unchanged.

- b78-native-aquatics-and-emergents: 129 hit, 1 MISS, 0 inconclusive, 27 skipped
- b79-native-dry-and-rocky: 142 hit, 0 MISS, 0 inconclusive, 28 skipped
- b8-veg-round1: 73 hit, 0 MISS, 0 inconclusive, 22 skipped

The one MISS predates this landing and appears identically on HEAD's b78. It is Broadleaf Arrowhead is_houseplant,
whose quote lists hardiness zones "3a, 3b, ... 11a, 11b"; the cached NC State page reads "5a, 5b, 6a, 6b, 7a, 7b, 8a,
8b, 9a, 9b, 10a, 10b". The 77 skips are older MOBOT and Clemson citations on other fields. b78 was run again after
the re-merge and gave the same result. Every URL it cites was already cached by then, so that run wrote no cache
entries.

b77 was not run through verify_quotes, because this landing did not touch it. The 8 citations in the b77 payload were
checked with the same presence test against the cached pages, and all 8 are HITs.

## Tests

`tests/test_tranche_invariants.py` passes. The final combined run with `test_claim_ingest.py`, after the b78 re-merge,
gave 3,886 passed and 1 failed. The one failure is the expected count assert: `assert 5994 == 5924`.

- Two sessions committed during this landing: a084d50 (round 3 chunk 2, which includes b77) and b5538c6 (round 3
  chunk 1). Their commits moved the test's expected count to 5,924.
- The only uncommitted verified files now in the working tree are this chunk's b78, b79 and b8, so the +70 difference
  is exactly this chunk.
- Applying the b77 payload adds 16 more, for 6,010.
- An earlier run, before those commits, printed `assert 5978 == 5558`, with other sessions' uncommitted work in the
  tree.

`tests/test_claim_ingest.py` was not edited.

## Left for you

- The b77 payload is ready to apply. b77 is committed (a084d50), and the plan prints "problems: none" against it.
  Run `.venv/bin/python scripts/catalog/pipeline/merge_backfill.py scripts/catalog/pipeline/size-r3-chunk3-b77-result.json --apply`,
  then verify_quotes on b77 and the two tests (+16 claims).
- Three-leaved Stonecrop's is_edible true is the one judgment call under the narrower edibility rule (see above).
- Broadleaf Arrowhead's pre-existing is_houseplant quote no longer matches NC State's zone list (see above).
