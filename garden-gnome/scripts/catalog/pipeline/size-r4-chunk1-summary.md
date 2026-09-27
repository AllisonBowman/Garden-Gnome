# Size backfill, round 4 chunk 1 -- landing summary

Landed 2026-09-27 from `size-r4-chunk1-result.json` (39 species over b8, b80, b82, b83 and b84; 0 unverified,
0 no_research; 1 field already nulled on audit; 37 review lines), following `BACKFILL_LANDING_BRIEF.md` and the
coordinator's standing rules for this round. Only those five batch files were touched; the merge plan named no other.
Other sessions were merging chunk 2 into b86, b87, b88 and b9 at the same time. Not committed.

## Verification basis, and the cache incident

The worktree's `scripts/catalog/.quote_cache` was emptied twice while this landing was under way (the coordinator
traced it to two research agents in another workflow running `rm -f` on the cache at 18:08 and 18:12 UTC). When this
landing started, none of the 45 pages this chunk cites was in the cache. Before the coordinator's all-clear arrived, I
fetched the 105 fetchable pages cited by the five batch files into a private snapshot in the session scratchpad,
through the sandbox with those hosts approved for the one command. Nothing was written to `.quote_cache`. One earlier
attempt at a script that would also have added the fetched pages to the shared cache was refused by the permission
classifier and never ran.

The coordinator then re-seeded the cache from the main checkout and re-fetched today's pages, and asked for no live
fetching. From that point every check was re-run against the shared cache, read-only. By the end, all 105 fetchable
pages the five files cite were cached with status ok. The 32 that are not cached are the ones this machine cannot
read: 20 Missouri Botanical Garden pages, 11 Clemson HGIC pages and one UMD PDF. The citation check gave identical
results on the shared cache and on the snapshot.

19 of the 105 pages differ between the two copies, but only in page furniture: the RHS membership discount, tag lists
and related-plant lists. One difference matters for a reader. The cached NC State Snapdragon page is the 2026-09-13
copy, which lacks the "Edibility: Flowers are edible" field and the edible-flower tags that today's page carries. The
sentence Snapdragon's is_edible citation quotes is on both copies.

No value in this chunk rests on Missouri Botanical Garden or Clemson alone except American Beachgrass's size (see
below), and that was nulled. Nothing in `.quote_cache` was written, edited or deleted by this landing: every read went
through a cache-only wrapper, or through qc.py on URLs already confirmed cached.

## Merge plan totals

After the repairs below, `merge_backfill.py` printed "problems: none" and was applied. It wrote 36 species, 178 fields
and 117 citations. The 178 fields are:

- 132 size bounds, on 34 species.
  - 31 species have all four bounds.
  - Seaside Goldenrod has no spread minimum, because EDIS gives one spread figure.
  - Sour Cherry has no height minimum, because NC State gives one height figure.
  - Garlic Chives has no height at all (nulled at landing).
- 27 attracts_pollinators, all true.
- 19 is_edible: 18 true, and 1 false (Silver Ragwort, on NC State's "Toxic if ingested.").

Some species wrote less than the full set:

- Green Beans and Butternut Squash wrote is_edible only. Both are climbers, so they take no size.
- American Beachgrass wrote nothing (nulled at landing).
- Sea Ox-eye and Smooth Cord Grass wrote nothing. Their proposals were all null, so their unknowns do not travel.

Claims per file, measured with the loader against HEAD:

- b8-veg-round1: 48 -> 81 (+33); 7 species, 23 citations
- b80-native-coastal: 21 -> 45 (+24); 5 species, 16 citations
- b82-perennials: 34 -> 74 (+40); 8 species, 25 citations
- b83-annuals: 42 -> 84 (+42); 8 species, 26 citations
- b84-edibles: 48 -> 87 (+39); 8 species, 27 citations

That is +178, one claim per field, and all 178 pair to the new citation written with them, not to an older citation.
A semantic check against HEAD found the merge purely additive. On the 36 touched records, only the six fields changed,
each from null to its proposed value, and citations and unknowns were only appended. The 4 untouched records are
unchanged, and each file gained the one standard normalization line. The loader reports no new unsupported field.
The git diff's 80 deleted lines are serialization only: a last list item gaining a trailing comma, plus the four files
that had no final newline gaining one.

## The 37 review lines

The rule applied is the brief's. A correction goes in only if the stored quote is a splice (it carries U+23CE, or a
label is glued to its value) and the correction is that same text as the page renders it, or a substring of the stored
quote. Every correction was confirmed on the cached page with qc.py (one hit each), and the repair script asserted the
substring relation mechanically.

**Applied, 31 lines.** Each correction is one rendered line of the page and a literal substring of a U+23CE splice.

- Size lines: NC State's "Height: ..." or "Width: ..." line. No value changed.
  - Lemongrass: 4 lines
  - Stevia: 4
  - Dwarf Palmetto: 1 (height)
  - Eastern Baccharis: 4
  - Anise Hyssop: 2 (height)
  - Spotted Dead Nettle: 4
  - Pot Marigold: 4
  - Lemon Balm: 2
  - Sweet Marjoram: 2 (height; its stored quote glued "Dimensions:" to the line)
- Lemongrass is_edible: "Leaves for flavoring", the Edibility field's value.
- Stevia is_edible: the Edibility field's full value, "Leaves are highly edible and used as a sweetener. ...".
- Eastern Baccharis attracts_pollinators: its Wildlife Value, "Nectar attracts pollinators and insects, provides
  cover, and seeds are enjoyed by birds."
- Pot Marigold attracts_pollinators: "Attracts butterflies and pollinators".

**Held, 6 lines.** The auditor's text is real page text, but it comes from a different element than the stored quote,
so it is not the same evidence.

- Five were pollinator corrections offering description prose or a Wildlife Value sentence. The stored splice of NC
  State's "Attracts:" list was de-spliced to one of its own stacked values, confirmed with qc.py:
  - Dwarf Palmetto -> `Pollinators`
  - Anise Hyssop -> `Bees` (the list is Bees, Butterflies, Hummingbirds, Songbirds)
  - New Guinea Impatiens -> `Butterflies` (the stored quote was 'Attracts: ... Butterflies', a label joined to its
    value by an ellipsis)
  - Lemon Balm -> `Pollinators`
  - Sweet Marjoram -> `Bees` (stored 'Attracts: Bees', a label glued to its value)
- The sixth was Sweet Marjoram's is_edible correction, which offered the Edibility field. The stored quote was kept:
  it is one rendered run of the description paragraph ("Sweet Marjoram is an edible, herbaceous perennial sub-shrub
  ... The aromatic leaves are edible ..."), and it verifies. The "non-standard whitespace" the auditor hit is a
  no-break space, which verify_quotes normalises.

No held correction left a field unsupported.

## Other citation repair (brief step 2)

Spotted Dead Nettle's pollinator quote, 'Plants for pollinators            Herbaceous Perennial       Buy this from
Plant Nurseries 3 Suppliers', glued three separate RHS elements together: the badge's image alt text, the plant-type
span and the buy link. It was de-spliced to `Plants for pollinators`.

After the repair, all 117 citations are present on their cached page as single rendered runs: no U+23CE, no label
glued across a boundary, and nothing qc.py cannot find. RHS's "Fruit Edible" (Green Beans) was checked in the raw HTML
and is a single plant-type span. All 67 size citations were re-derived from their quotes and match:

- NC State ft/in lines by script.
- RHS metre bands at 39.37 in/m.
- By hand: EDIS's 1.3-6.6 ft and 1.6 ft for Seaside Goldenrod; NC State's 30 ft for Sour Cherry; Ivy Geranium's
  0.1-0.5 m.

## Fields nulled at landing (7), and why

- **American Beachgrass**, all four size fields (24-36 in by 72-120 in).
  - They rested on Clemson HGIC alone ('2 to 3 ft. tall x 6 to 10 ft. wide'). Clemson refuses this machine, and the
    page is not in the cache.
  - RHS has no size data and NC State has no page for the species.
  - Both citations were dropped and an unknowns line records the reason. The species now writes nothing, so that line
    stays in the result file.
- **Oriental Poppy is_edible** (coordinator's rule 2: a poisonous plant with only a marginal food use).
  - The only food mention is NC State's "Even though oriental poppies have some toxicity, condiments have been made out
    of seed heads when they are young."
  - The same page says "All parts are poisonous including the juice." Its Poison Part lists every part, the fruits and
    seeds included.
  - The citation was dropped. The researcher's two lines, the conditional-true line and the toxicity line, became one
    removal line in the Pokeweed / Marsh Marigold / Japanese Yew style, with the page's words.
- **Garlic Chives mature_height_in_min/max**.
  - NC State prints "Height: 0 ft. 6 in. - 0 ft. 4 in.", a reversed range. That is a data-entry error, not a published
    4-6 in. The same page gives leaves "up to 12 inches long", and RHS gives "to 50cm tall".
  - No other page's figure was substituted. The citation was dropped, and the researcher's line explaining the swap was
    replaced by a removal line quoting the page.
  - The spread (12-12, "Width: 1 ft. 0 in. - 1 ft. 0 in.") verifies and stands.

The one field nulled on audit, Globe Artichoke is_edible, stays null. Its unknowns were corrected so they no longer
read as though the value were true (see below).

## Records the coordinator asked to settle

- Oriental Poppy and Garlic Chives: as above.
- Saw Palmetto: is_edible stays true on NC State's "The fruits are edible but foul-tasting."
  - "foul-tasting" was already in unknowns, with the medicinal extract note.
  - A safety sweep of every readable page (NC State, UF/IFAS FP547, RHS) found no toxic part and no preparation
    requirement. FP547 treats the fruit as medicinal ("Medicinal uses: Fruits are used to prevent and treat an enlarged
    prostate.") and lists only a physical hazard ("Hazard: spines on petioles"; "Human hazards: spiny").
  - One added line records all of this. It also notes FP547's "Attractant: bees, ...", which the researcher's FP547
    line called absent.

## Rules re-checked

- **Climbers.**
  - Green Beans (NC State Climbing Method: Twining; RHS Habit Climbing) and Butternut Squash (NC State Habit/Form
    Climbing, tendrils) carry no size.
  - Ivy Geranium is trailing and cascading, not climbing (RHS Habit Bushy, "bushy evergreen trailing perennial"), so it
    keeps its size.
  - Tomatillo keeps its size. Its "sprawling habit needs support like a tomato cage or trellis", but NC State has no
    climbing field and says "vining habit" only of the cultivar 'Toma Verde'.
  - Snapdragon keeps its size. RHS mentions "upright or scrambling stems", but FP044 gives "Plant habit: upright" and
    RHS's Habit is Bushy.
- **Houseplants** (is_houseplant true: Lemongrass, Stevia, African Marigold, Ivy Geranium).
  - No page gives a separate indoor or container figure. RHS says pot-grown lemongrass is "unlikely to reach this
    size" but gives no number.
  - Every landed size is at most 48 in, far under the 120 in cutoff, so the published figures stand.
  - No houseplant in this chunk carries an outdoor-only figure over 10 ft.
- **is_edible true, rule 2.** Every true is a common food or culinary plant, and its condition is in unknowns:
  - Green Beans: raw or undercooked beans toxic.
  - Tomatillo: all parts poisonous except the ripe fruit.
  - Sour Cherry: cyanide in the pits.
  - Garlic Chives: low-severity sulfides.
  - Snapdragon: flowers only, bitter, garnish.
  - Pot Marigold: petals only; unsprayed, handled properly.
  - Catnip: cat reaction.
  - Lemongrass: pet and horse problems.
  - Sweet Marjoram: toxic for pets.
  - Brown Mustard: young versus older leaves, horses, skin irritant.
  - Butternut Squash: a bitter crop is not to be eaten.
  - Saw Palmetto: foul-tasting.
  - Broccoli: problem for horses.

  Beets, Stevia, Anise Hyssop, Arugula and Lemon Balm have no condition on any readable page. No toxicity sentence is
  cited as support for a true.
- **attracts_pollinators.** All 27 trues name bees, butterflies, hummingbirds or pollinators. None rests on
  seed-eating birds.

## Unknowns corrected or added at landing

Every page quotation in these lines was checked against the cached copy.

- Globe Artichoke: the line calling is_edible conditional now says it is null (removed on audit) and quotes the whole
  Edibility field, 'once cooked' included. "(which sets is_edible=true)" was reworded in the toxicity line.
- Lemongrass: the line saying RHS grow-your-own contributed nothing was corrected. That page gives "Plants can reach
  1.5m (5ft) tall and 1m (3ft) wide, although are unlikely to reach this size when grown in a pot in the UK." The
  corrected line also records its culinary text and its glove caution about sharp leaf blades.
- Eastern Baccharis: RHS does give a size, "A fast-growing deciduous shrub with a height and spread of about 3m." (about
  118 in, above NC State's 84 in spread).
- Anise Hyssop: RHS, which the researcher did not query, gives Max Height 0.5-1 m and Max Spread 0.1-0.5 m and tags the
  species "Plants for pollinators".
- Spotted Dead Nettle: UGA's "8- to 12-inch tall plant that spreads up to 24 inches" and RHS's 0.1-0.5 m by 0.5-1 m.
- Snapdragon: FP044, which the researcher reported refused, is readable in the cache. It gives "Height: .5 to 3 feet"
  and "Spread: .5 to 3 feet" (both cultivar-dependent), which is a wider spread than NC State's 6-10 in, and says
  nothing on edibility.
- Pot Marigold: FP087's handling condition, "culinary (when properly handled and no pesticides have been applied)".
- Brown Mustard: RHS's "Skin irritant/allergen. Wear gloves and other protective equipment when handling".
- Sour Cherry: two lines.
  - RHS's "Seed kernels harmful if eaten; ..." and its pets line.
  - A height note: RHS's own Max Height (4-8 m, 157.5-315 in) and "to around 5m" are both below NC State's 30 ft
    used for the max, and only RHS's spread is used. The researcher's lines read as though RHS's height were used.
- Broccoli: the Italica page's prose "The plants can grow 1-4 feet tall and wide." against its structured 1-2 ft width.
- Saw Palmetto: as above.

## verify_quotes, per touched file (run last, against the shared cache, no network)

The last step was `VQ_CACHE_ONLY=1 .venv/bin/python scripts/catalog/verify_quotes.py <file>`, using the cache-only mode
the coordinator committed during this landing (c113cd2). An uncached URL reads as a SKIP, nothing is fetched and
nothing is written: the cache held 1,700 entries before and after. Earlier, before that mode existed, the same
`check()` was run through an equivalent read-only wrapper, on each file and on its HEAD copy, and gave identical
numbers.

- b8-veg-round1: 96 hit, 0 MISS, 0 inconclusive, 22 skipped (HEAD 73 / 0 / 0 / 22)
- b80-native-coastal: 88 hit, 0 MISS, 0 inconclusive, 21 skipped (HEAD 72 / 0 / 0 / 21)
- b82-perennials: 148 hit, 0 MISS, 0 inconclusive, 33 skipped (HEAD 123 / 0 / 0 / 33)
- b83-annuals: 163 hit, 0 MISS, 0 inconclusive, 15 skipped (HEAD 137 / 0 / 0 / 15)
- b84-edibles: 185 hit, 0 MISS, 0 inconclusive, 4 skipped (HEAD 158 / 0 / 0 / 4)

The hit counts rose by exactly the 117 new citations. No new-field citation is a MISS, SKIP or INCONCLUSIVE. The 95
skips are unchanged from HEAD, and all are older citations on other fields: 92 uncached MOBOT and Clemson pages, one
cached Clemson http-403 entry and two PDFs. No file has a MISS, before or after.

## Tests

`tests/test_tranche_invariants.py` passes. The final combined run gave 3886 passed and 1 failed, the expected count
assert `assert 6268 == 6090`.

- Chunk 2 was committed during this landing (11d765a, +80), which moved the expected count from 6,010 to 6,090.
- The only uncommitted verified files now in the tree are this chunk's five, so the +178 difference is exactly this
  chunk.
- An earlier run, before that commit, printed `assert 6268 == 6010` with chunk 2's then-uncommitted +80 in the tree.
- `tests/test_claim_ingest.py` was not edited.

## For a person to decide

- **Globe Artichoke is_edible.** The audit nulled it only because the cooking condition was missing from unknowns.
  Under rule 2, a common food plant that needs cooking lands true with the condition in unknowns, and the unknowns now
  quote the whole Edibility field with "once cooked". Re-proposing true, citing NC State's full Edibility sentence, is a
  one-record follow-up. It was not done here, because a landing does not restore a value the audit removed.
- **Bare stacked-value quotes.** Eight pollinator citations quote a bare value of NC State's Attracts field
  (`Pollinators`, `Bees`, `Butterflies`). Five were de-spliced to that form here; Globe Artichoke, Woodland Sage and
  Ivy Geranium arrived that way. Auditors offered fuller sentences for the five, as in earlier chunks, and those
  sentences are all on the pages.
- **Ivy Geranium.** Its RHS size citations quote the bare value '0.1-0.5 metres' for both height and spread (both cards
  read the same). The brief allows no extension to 'Max Height ...', so they were left as they are.
- **Snapdragon's cached NC State copy** is older than today's page (see verification basis).
- **Sizes disclosed but not changed.**
  - Sea Oats: UF/IFAS height 5-8 ft.
  - Balloon Flower, Siberian Bugloss, Spiked Speedwell, Woodland Sage, Pot Marigold, Brown Mustard, Arugula, Sweet
    Marjoram, Garlic Chives and Dwarf Palmetto: RHS bands.
  - Snapdragon: RHS 1.5-2.5 m.
  - Catnip has only an RHS size, because NC State has no Dimensions block.
- **Saw Palmetto's Clemson line.** It says ProxyError; the auditor saw http-403. Either way the page is unreadable and
  nothing rests on it.

Scratch work is in the session scratchpad under `r4c1/`: the untouched workflow output, the repair script, the
cache-only qc and verify wrappers, the safety and climber sweeps, and the snapshot fetch log.
