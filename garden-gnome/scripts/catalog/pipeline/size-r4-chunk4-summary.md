# Size backfill, round 4 chunk 4 -- landing summary

Landed 2026-09-27 from `size-r4-chunk4-result.json` (36 species over b23, b24, b25, b26, b27, b29, b3, b30, b31, b32,
b33, b34, b35, b36 and b38; 0 unverified, 0 no_research; 9 fields already nulled on audit; 18 review lines on 6
species), following `BACKFILL_LANDING_BRIEF.md` and the coordinator's standing rules 1-6 for this round. Only those
fifteen batch files were touched, and the merge plan named no other. Not committed.

The untouched workflow output and the fifteen batch files as they were at the start (identical to HEAD) are kept in the
session scratchpad under `r4c4/orig/`. The repair was made by `r4c4/repair.py`, which rebuilds the result file from the
untouched copy and asserts that a landing only nulls values, drops citations, de-splices a quote to a substring of
itself, or (standing rule 6 only) lands an indoor figure in place of a refuted outdoor one with a new citation; that no
citation is left supporting nothing; and that every page quotation written at landing, in a citation or in unknowns
(59 of them), is present on the cached page.

## Verification basis

Every URL this chunk's citations point to (and every page quoted below) was cached with status ok when the landing
started (19:42 UTC). Nothing was fetched live and nothing in `.quote_cache` was written, edited, moved or deleted by
this landing: the cache held 1,728 entries at the start and at the end, with identical names and no entry modified
after the start snapshot. Every page read went through a guard (`r4c4/qcg.py`) that runs qc.py only on a URL already
cached with status ok, with `VQ_CACHE_ONLY=1`, and verify_quotes was run with `VQ_CACHE_ONLY=1`. Every citation was
also run through verify_quotes' own `present()` against its cached page, plus a stricter check that the quote sits
inside one rendered line, before and after the repair (`r4c4/cite_audit.py`): before, 63 of 72 passed and the 9
failures were the U+23CE splices behind 17 of the 18 review lines (the 18th, Bay Laurel's two glued badges, passed);
after, all 75 pass both checks.

No new value rests on Missouri Botanical Garden or Clemson. The 75 landed citations are NC State (63), RHS (11) and
UF/IFAS EP648 (1). The MoBot pages are not in the cache and the Clemson pages the researchers report refused are
cached as http-403; the five Clemson pages that did load (`hgic.clemson.edu/factsheet/tea-olive/`, `/gardenia/`,
`/hibiscus/`, `/indoor-palms/`, `/indoor-cacti/`) are cited by no new value.

## Merge plan totals (applied)

After the repair, `merge_backfill.py` printed "problems: none" and was applied. It wrote 35 species, 114 fields and 75
citations:

- 89 size bounds on 24 species. 19 have all four bounds. The partial ones: Chinese Hibiscus (height max and spread
  max, 78.7 in each), Parlor Palm (height max 60, spread 24-36), Crown of Thorns (height max 24, spread 3.9-19.7),
  Money Tree (height max 96, spread 3.9-19.7) and Weeping Fig (height 24-120, no spread).
- 14 is_edible: 8 true (Chinese Hibiscus, Money Tree, Norfolk Island Pine, Avocado, Bay Laurel, Ginger, Orange, Tea
  Olive), 6 false (Gardenia, Angel's Trumpet, Anthurium, Common Lantana, Crown of Thorns, Japanese Pittosporum).
- 11 attracts_pollinators, all true.

String of Bananas writes nothing: a vine by NC State ("a trailing, herbaceous, succulent, perennial vine", #vine), so no
size, and no page speaks to eating it or names a pollinator. Its unknowns stay in the result file.

Claims per file, against HEAD (2702094 by the end; none of the fifteen files had an uncommitted change before the
merge, and the round 4 chunk 6 commit that landed meanwhile touched none of them):

- b23-daylily-and-more-gaps: 69 -> 79 (+10)
- b24-trees-and-more: 81 -> 94 (+13)
- b25-more-trees-shrubs: 90 -> 96 (+6)
- b26-toxic-and-more-trees: 82 -> 86 (+4)
- b27-bulbs-and-more: 66 -> 72 (+6)
- b29-mistletoe-and-more: 68 -> 72 (+4)
- b3-humidity-lovers: 71 -> 103 (+32)
- b30-poison-ivy-and-more: 68 -> 72 (+4)
- b31-avocado-and-more: 71 -> 76 (+5)
- b32-weeping-fig-and-more: 80 -> 84 (+4)
- b33-belladonna-and-more: 76 -> 85 (+9)
- b34-hemlock-and-more: 75 -> 77 (+2)
- b35-ginkgo-and-more: 61 -> 72 (+11)
- b36-shrubs-vines-toxic-bulbs: 89 -> 91 (+2)
- b38-beech-poplar-shrubs: 69 -> 71 (+2)

That is +114, one claim per field. A semantic check against the start copies (`r4c4/post_check.py`) confirmed the merge
only added: every pre-existing value, citation, unknowns line and normalization is unchanged, each file gained the one
standard normalization line, and the only new keys are the six backfill fields. Every new value pairs to a citation
written with it, not to an older one (checked by running the loader on each merged record with only its new
citations; no pre-existing citation in these 36 records names any of the six fields). In the git diff the 71 deleted
lines are serialization only: each gained a trailing comma.

## The 18 review lines

The brief's rule was applied: a correction goes in only if the stored quote is spliced (it carries U+23CE, or a label
is glued to its value) and the correction is that same text as the page renders it, or a substring of the stored
quote. Each was confirmed with qc.py on the cached page first.

- Maidenhair Fern, 4 lines (mature_height_in_min/max, mature_spread_in_min/max): APPLIED. The stored quote "Dimensions:
  ⏎ Height: 1 ft. 0 in. - 2 ft. 0 in. ⏎ Width: 1 ft. 0 in. - 2 ft. 0 in." splices three rendered lines; the
  corrections "Height: 1 ft. 0 in. - 2 ft. 0 in." (height citation) and "Width: 1 ft. 0 in. - 2 ft. 0 in." (spread
  citation) are substrings, each on its own line on the page. No value changed (12-24 by 12-24 in).
- Ponytail Palm, 4 lines: APPLIED, the same way: "Height: 6 ft. 0 in. - 8 ft. 0 in." and "Width: 3 ft. 0 in. - 5 ft.
  0 in.". No value changed (72-96 by 36-60 in; the page's prose ties the height to pot growth, "in a pot it will grow
  6 to 8 feet tall").
- Nerve Plant, 4 lines: APPLIED: "Height: 0 ft. 3 in. - 0 ft. 8 in." and "Width: 0 ft. 6 in. - 1 ft. 6 in.". No value
  changed (3-8 by 6-18 in).
- Boston Fern, 4 lines: HELD. The proposed "It grows to 2 to 3 feet in height and width." is a different sentence (the
  description), not the stored Dimensions quote de-spliced. The stored quote was instead de-spliced to its own
  substrings, "Height: 2 ft. 0 in. - 3 ft. 0 in." and "Width: 2 ft. 0 in. - 3 ft. 0 in.", each on its own rendered
  line. The prose agrees; no value changed (24-36 by 24-36 in), and no field was left unsupported.
- Bay Laurel, attracts_pollinators: APPLIED. "Award of Garden Merit Plants for pollinators" glues two RHS badges; the
  correction "Plants for pollinators" is a substring and the pollinator badge on its own. attracts_pollinators true
  stands.
- Bougainvillea, attracts_pollinators: HELD. The proposed "Bougainvillea is attractive to bees, butterflies, and
  birds." is the Wildlife Value field, a different element from the stored quote (the Attracts field, "Attracts: ⏎ ...
  Bees ⏎ ... Butterflies ⏎ ... Songbirds"). The stored quote was de-spliced to its substring "Bees", the field's first
  value on its own rendered line (as Lemon's "Attracts: Bees" was in chunk 3). attracts_pollinators true stands.

No held correction left a field unsupported.

## Fields nulled, values landed, citations changed at landing

Nulled at landing (2):

- Money Tree, mature_height_in_min (72), scope. NC State's houseplant sentence, "In cultivation, it can grow up to 30
  feet, but it typically grows no more than 6 to 8 feet tall as a houseplant.", is a ceiling, not a range of mature
  heights, so it fills the max only, the reading Poinsettia's "rarely exceeds 2 to 3 feet" landed with (max only) in
  chunk 3. RHS's pot figure is lower still ("unlikely to exceed 1.5m in a pot", "Max Height 1-1.5 metres"), which a
  72 in minimum would contradict. The auditor passed 72-96; this overrides that and is easy to reverse.
- Parlor Palm, mature_height_in_min (24), standing rule 6, as instructed: it came only from the refuted outdoor
  Dimensions block.

Landed under standing rule 6 (6 values on 3 species; each audit refuted the outdoor sizes because a page the record
already cites gives an indoor figure, and quoted it):

- Chinese Hibiscus: mature_height_in_max 78.7 and mature_spread_in_max 78.7, mins null. See "Records to settle".
- Parlor Palm: mature_height_in_max 60, min null. See "Records to settle".
- Crown of Thorns: mature_height_in_max 24 (min null) and mature_spread_in 3.9-19.7. Not on the coordinator's list,
  but the audit refuted all four Dimensions-block sizes under check I on exactly rule 6's ground. NC State's own
  description, already cited for the record, gives the houseplant figure: "In its country of origin (Madagascar), the
  plant will grow to 5 or 6 feet tall; however, in the United States, it typically grows to 3 feet tall, or under 2
  feet when grown as a houseplant." That fills the height max (2 ft = 24 in). NC State gives no indoor width; the
  audit's spread refutation rests on RHS's "Max Spread 0.1-0.5 metres" for a plant RHS lists under "Conservatory
  Greenhouse Houseplants" and says to "Grow under glass", on an RHS page the record already cites, so that lands
  (3.9-19.7 in). RHS's height band, 0.5-1 metres (19.7-39.4 in), runs above NC State's houseplant ceiling; NC State's
  explicit houseplant sentence is the one used for the height, and the disagreement is in unknowns.

Citations dropped (3): Money Tree's second is_edible citation (the toxicity sentence, as instructed), Money Tree's
"mature_height_in 72-96" citation (replaced by a re-labelled one: same page, same quote, claim "mature_height_in max 96,
min null ..."), and Parlor Palm's Dimensions-block height citation (it supported nothing once both ends were null).

Citations added (6): Chinese Hibiscus height and spread (RHS growing guide), Parlor Palm height (NC State indoor
sentence), Crown of Thorns height (NC State) and spread (RHS), and Money Tree's re-labelled height citation. Each quote
was confirmed verbatim on the cached page, each claim names its stem, and each sits on one rendered line.

The nine fields nulled on audit stay null except where rule 6 put an indoor figure in their place: Chinese Hibiscus's
four NC State landscape sizes (48-120 by 60-96 in), Parlor Palm's 90 in height max, and Crown of Thorns' four
Dimensions-block sizes (36-72 by 18-36 in).

## Records the coordinator asked to settle

- Chinese Hibiscus (rule 6): the RHS growing guide is RHS's advice page for Hibiscus rosa-sinensis (title "Hibiscus
  rosa-sinensis | RHS Advice"; Quick facts "Botanical name - Hibiscus rosa-sinensis", "Group - Evergreen houseplant for
  warm greenhouse or conservatory"), and its introduction opens "Tropical hibiscus is native to China ..." before "It is
  tender in Britain and is grown as a pot plant indoors where it may reach 2m (6½ft)." That sentence landed as
  mature_height_in_max 78.7 (2 m x 39.37, the corpus's metre convention; RHS's own conversion is 6½ ft, 78 in). The
  Quick facts line "Height and spread - May reach 2m (6½ft)", on which the audit refuted the spread, landed as
  mature_spread_in_max 78.7. Both are single text nodes on the page; both minimums stay null. is_edible stays true on
  NC State's one-word "Edible" (Flower Value To Gardener, beside "Showy"; the Landscape Theme also lists "Edible
  Garden"), and the unknowns now say "part and preparation unspecified". No page names a toxic part. The tag-list quote
  behind attracts_pollinators is the complete Tags field, not a truncated one.
- Parlor Palm (rule 6): NC State's "Stems can grow up to 5 feet in indoor environments but usually are smaller." is on
  the Chamaedorea elegans species page; it landed as max 60 with a new citation, and the leftover 24 in min was nulled.
  The spread stays 24-36 in from the Dimensions block: the page gives no indoor spread, its only other spread figure is
  the outdoor "the leaf spread can be up to 3 feet wide", which matches the block's 36 in, and an outdoor figure at or
  under 120 in stands under rule 4.
- Money Tree: the "conflicting information regarding the possible toxicity of the seeds" citation was dropped; its
  words stay in the is_edible unknowns line, and a landing line says why. is_edible stays true on "The seeds or nuts
  are eaten raw, fried, or roasted."; the unknowns carry the page's Poison Part (Seeds, the eaten part), its toxic
  principle ("cyclopropenoid fatty acids--possibly toxic and carcinogenic"), the poison symptoms and "Research further
  before ingesting the seeds or nuts."

## Rules re-checked

- Climbers take no size: String of Hearts (Habit/Form Cascading, Climbing, Prostrate; #climber), Bougainvillea, Common
  Jasmine and Star Jasmine all carry none, and String of Bananas (a "vine" to NC State) writes nothing. Staghorn Fern
  keeps its size: NC State lists "Climbing Method: Clinging", but its Habit/Form is Cascading and Mounding with no Vine
  or Climbing tag; the line describes how an epiphyte attaches, not a climbing habit (the auditor's call, kept).
- Houseplant sizes (all 36 species are is_houseplant true). Every size that lands is an indoor, pot or houseplant
  figure, or a figure of 10 ft or under:
  - Indoor or pot figures: Money Tree (NC State ceiling; RHS pot spread), Ponytail Palm ("in a pot"), Anthurium ("As a
    houseplant"), Weeping Fig ("As a houseplant ... 2 to 10 feet"), Corn Plant (RHS, whose page calls it "a popular
    houseplant" and lists it under Houseplants), and the three rule-6 landings.
  - Published figures of 10 ft or under, which rule 4 lets stand where no indoor figure replaces them: Venus Flytrap,
    Maidenhair Fern, Gardenia, Staghorn Fern, Amaryllis, Golden Barrel Cactus, Boston Fern, Calathea, Dumb Cane, Moth
    Orchid, Nerve Plant, Prayer Plant, Brazilian Orchid, Air Plant, Ginger, Common Lantana, and Parlor Palm's spread.
    Where one of these pages also gives a pot figure (Amaryllis's RHS profile, "needs to be planted in a pot indoors",
    25-90 cm by 30 cm), it agrees. Gardenia and Common Lantana are noted under "For a person".
  - Left null because the only figures found are outdoor stature whose height or spread exceeds 120 in: Avocado, Bay
    Laurel, Orange, Japanese Pittosporum, Tea Olive and Weeping Fig's spread. Norfolk Island Pine and Angel's Trumpet
    also stay null although an indoor or container figure exists (see "For a person"). Nothing was nulled at landing
    under this rule.
- is_edible true: all eight rest on a food-use statement, none on a toxicity sentence (Money Tree's was dropped), and
  each condition is in unknowns: Chinese Hibiscus (part and preparation unspecified), Money Tree (seeds; toxicity
  unresolved on the page), Norfolk Island Pine (seeds only, "nut-like"), Avocado (fruit flesh; RHS pet warnings),
  Bay Laurel (leaves as a cooking flavouring, not eaten whole; RHS fruit "not to be eaten", added), Ginger (rhizomes and
  young sprouts; no toxicity on any page), Orange (fruit; skins and plant material cause problems), Tea Olive (dried
  flowers in tea). All are real foods or flavourings; none is a poisonous plant with only folk or survival use.
- is_edible false: all six rest on a page's own poison or not-to-eat statement (NC State's Edibility field for Angel's
  Trumpet and Crown of Thorns, "toxic if ingested by pets or humans" for Anthurium, the poison block for Gardenia,
  UF/IFAS EP648 for Common Lantana, "non-edible fruit capsules" for Japanese Pittosporum).
- attracts_pollinators true: all eleven name bees, butterflies, moths, hummingbirds or pollinators (Chinese Hibiscus's
  tags, "Hummingbirds", "Bees", "Attracts pollinators.", "pollinating moths", "Plants for pollinators", "attractive to
  butterflies, hummingbirds and other pollinators", "Attracts Pollinators", "Butterflies"). None rests on birds.

## Unknowns corrected or added at landing

Corrections are marked "corrected at landing"; added lines say "noted at landing, verified against the cached copy".
Every page quotation in them was read on the cached page.

- Chinese Hibiscus: the houseplant-sizing line and the RHS growing guide line ("0 hits ... no usable information")
  were corrected; a landing line explains the rule-6 sizes; the is_edible line gained "part and preparation
  unspecified"; the RHS details line notes its smaller figures are still unused.
- Parlor Palm: the "general Dimensions block ... no separate as-houseplant size" line was corrected; a landing line
  explains the rule-6 height and the nulled min.
- Crown of Thorns: the two size lines were corrected (the Dimensions block is outdoor and native stature by the page's
  own prose; what landed and why); Poison Part is now the page's full list (Bark, Flowers, Fruits, Leaves, Roots,
  Sap/Juice, Seeds, Stems; the note had "and other parts"); RHS's "Humans/Pets: IRRITANT to skin/eye; harmful if eaten."
  was added.
- Money Tree: the height line now says max 96, min null and why, with RHS's lower pot figure; "houseplants never flower"
  was corrected to the page's "houseplants are unlikely to flower"; a landing line records the dropped citation and adds
  Poison Part (Seeds) and the toxic principle.
- Norfolk Island Pine: the size line's "no page gives an indoor figure" is false. NC State reads "Indoors it prefers a
  bright, cool room (55-65 degrees F) and will reach heights of 9 feet." (108 in). Not landed; see "For a person".
- Angel's Trumpet: the size line's "no page gives a bounded ... container-specific size" is false. NC State reads "It is
  a small tree growing 6 to 15 feet in containers and up to 35 feet in the landscape." Not landed; see "For a person".
  Poison Part is Flowers, Leaves, Seeds (the note had Flowers only, with the others "elsewhere"); the RHS growing
  guide's "most species are pollinated by moths" was added against the note's "no RHS page carries ... any pollinator
  statement".
- Amaryllis: the RHS profile page (pID=118) does give a size, "Height & spread 25-90cm (10in-3ft) by 30cm (12in)", and
  says the bulb "needs to be planted in a pot indoors"; it agrees with NC State and was not used.
- Anthurium: Poison Part is Flowers, Fruits, Leaves, Roots, Sap/Juice, Seeds, Stems (the note had Flowers, Fruits).
- Maidenhair Fern: the deer note sits under "Particularly Resistant To", not a Wildlife Value field (there is none).
- Moth Orchid: the NC State page is the Phalaenopsis genus page (the note said "not a genus page"), which matches the
  genus-level record; added the page's prose, "Moth orchids can range from a few inches to 2 feet in height and up to 2
  feet (but usually less) in spread.", whose floor is lower than the Dimensions block's 18 in.
- Bay Laurel: added RHS's "Fruit are ornamental - not to be eaten." (people and pets), a part not to eat beside
  is_edible true.
- Weeping Fig: added RHS's "Humans/Pets (dogs): Skin allergen; harmful if eaten.", which the auditor flagged as
  missing.
- Common Lantana: the RHS page does carry toxicity language ("Harmful if eaten." for people; "Pets (dogs, rabbits,
  rodents): Harmful if eaten."), against the note's "no edibility or toxicity language".
- Tea Olive: not every figure exceeds 120 in (RHS's spread 59.1-98.4 in and Clemson's 8-foot width do not); every height
  does, so the nulls stand.

## verify_quotes, per touched file

`VQ_CACHE_ONLY=1 .venv/bin/python scripts/catalog/verify_quotes.py <file>`, after the merge (start/HEAD numbers in
brackets):

- b23-daylily-and-more-gaps: 132 hit, 1 MISS, 0 inconclusive, 19 skipped (124 / 1 / 0 / 19)
- b24-trees-and-more: 134 hit, 1 MISS, 4 inconclusive, 33 skipped (126 / 1 / 4 / 33)
- b25-more-trees-shrubs: 130 hit, 2 MISS, 0 inconclusive, 42 skipped (126 / 2 / 0 / 42)
- b26-toxic-and-more-trees: 133 hit, 4 MISS, 0 inconclusive, 34 skipped (131 / 4 / 0 / 34)
- b27-bulbs-and-more: 135 hit, 1 MISS, 0 inconclusive, 21 skipped (131 / 1 / 0 / 21)
- b29-mistletoe-and-more: 104 hit, 1 MISS, 0 inconclusive, 32 skipped (102 / 1 / 0 / 32)
- b3-humidity-lovers: 58 hit, 0 MISS, 0 inconclusive, 21 skipped (41 / 0 / 0 / 21)
- b30-poison-ivy-and-more: 126 hit, 6 MISS, 0 inconclusive, 24 skipped (124 / 6 / 0 / 24)
- b31-avocado-and-more: 129 hit, 3 MISS, 0 inconclusive, 13 skipped (126 / 3 / 0 / 13)
- b32-weeping-fig-and-more: 112 hit, 4 MISS, 0 inconclusive, 40 skipped (108 / 4 / 0 / 40)
- b33-belladonna-and-more: 124 hit, 2 MISS, 0 inconclusive, 30 skipped (119 / 2 / 0 / 30)
- b34-hemlock-and-more: 141 hit, 1 MISS, 0 inconclusive, 25 skipped (139 / 1 / 0 / 25)
- b35-ginkgo-and-more: 107 hit, 5 MISS, 0 inconclusive, 30 skipped (99 / 5 / 0 / 30)
- b36-shrubs-vines-toxic-bulbs: 122 hit, 0 MISS, 0 inconclusive, 55 skipped (118 / 0 / 0 / 55)
- b38-beech-poplar-shrubs: 104 hit, 1 MISS, 0 inconclusive, 26 skipped (102 / 1 / 0 / 26)

Hits rose by exactly the 75 new citations. No citation this chunk wrote is a MISS, SKIP or INCONCLUSIVE, and every MISS,
SKIP and INCONCLUSIVE line is identical to the start copies'. The 32 MISS lines all predate this landing. Twenty-nine
name none of the six fields (b23 Showy Stonecrop accepted name; b24 Money Tree names; b25 Apple accepted name, Border
Forsythia sun; b26 Castor Bean x3, Lily of the Valley toxicity; b27 Red Raspberry is_houseplant; b29 American
Mistletoe; b30 Poison Ivy x2, Brazilian Orchid toxic_to_pets; b31 Avocado names, Southern Live Oak x2; b32 Weeping Fig
x2, Prickly Pear x2; b33 Panicle Hydrangea, Kousa Dogwood; b34 Rose of Sharon; b35 Bougainvillea x3, Purple
Passionflower x2; b38 Chinese Fringe Flower).

Three do name backfill fields, all on b30's German Chamomile, which is not in this chunk (landed in round 2, 13368ca):
mature_height_in 6-24 ("Height: 0 ft. 6 in. - 2 ft. 0 in."), mature_spread_in 6-24 ("Width: 0 ft. 6 in. - 2 ft. 0
in.") and attracts_pollinators ("The flowers attract mostly bees and flies. ..."). The cached copy of
`plants.ces.ncsu.edu/plants/matricaria-chamomilla/common-name/german-chamomile/` (67,639 bytes, dated Sep 5, the same
file as the main checkout's cache) reads "Height: 1 ft. 1 in. - 2 ft. 6 in." and "Width: 0 ft. 8 in. - 0 ft. 1 in."
and has no "attract mostly" text, so the round-2 quotes came from a different version of the page. commit_backfill
counts any MISS naming a backfill stem as a NEW-FIELD MISS, so it will refuse to commit b30 until German Chamomile is
re-cited or the page is re-warmed. This landing did not touch that record or the cache.

## Tests

- `tests/test_tranche_invariants.py` passes on its own: 3,880 passed.
- The combined run with `test_claim_ingest.py` gave 3,886 passed and 1 failed, the expected count assert
  `assert 6607 == 6493`. HEAD (2702094) already includes chunk 6, and at the time of the run the only uncommitted
  verified files were this chunk's fifteen, so the +114 is exactly this chunk.
- `tests/test_claim_ingest.py` was not edited.

## For a person to decide

- Crown of Thorns was landed under rule 6 although it was not on the coordinator's list (see above). Reverse by
  restoring the result file from `r4c4/orig/` for that record if rule 6 was meant only for the listed records; the
  RHS spread is the more debatable of the two, since RHS's size is not tied to indoor growth by a sentence, only by
  the page's houseplant and under-glass framing.
- Money Tree's height min was nulled against the auditor's pass (ceiling reading). Reverse by restoring the 72 and the
  original citation from `r4c4/orig/`. The two indoor ceilings also disagree (NC State 6-8 ft, RHS unlikely over 1.5 m
  in a pot); NC State's 96 in max stands.
- Needs re-research (nothing written, because a landing does not set a value the research left null): Norfolk Island
  Pine (NC State's "Indoors ... will reach heights of 9 feet" would give mature_height_in max 108), Angel's Trumpet
  (NC State's "6 to 15 feet in containers" would give mature_height_in 72-180 under rule 4's container clause), and
  Weeping Fig's is_edible (RHS's "harmful if eaten" would support false).
- Gardenia and Common Lantana keep NC State's landscape Dimensions figures (48-96 in; 12-72 by 36-60 in), which are
  under 120 in. RHS gives smaller figures (1-1.5 m) on pages whose cultivation notes grow the plant outdoors only where
  frost-free and otherwise in containers or under glass; the auditors judged those not indoor figures, and nothing was
  refuted, so rule 6 did not apply.
- Moth Orchid keeps the Dimensions block's 18 in height minimum although the same page's prose says "from a few inches".
- Norfolk Island Pine's is_edible true rests on NC State's Edibility field, "Seeds are edible (nut-like)". Rule 2 allows
  it (a page states a food use, and the seeds-only condition is in unknowns), but the app will say "grown to eat" for a
  plant sold as a houseplant.
- b30's German Chamomile MISSes (above) will block commit_backfill on b30 regardless of this chunk.

Scratch work is in the session scratchpad under `r4c4/`: the untouched workflow output and batch files (`orig/`), the
repair script and its output, the cache-only qc guard, the citation audit before and after, the merge plans, the
post-merge check, the diff, verify_quotes output before and after (`vq_before/`, `vq_after/`) and the pytest output.
