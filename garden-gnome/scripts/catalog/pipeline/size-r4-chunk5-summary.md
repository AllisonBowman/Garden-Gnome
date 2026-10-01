# Size backfill, round 4 chunk 5 -- landing summary

Landed 2026-09-27 from `size-r4-chunk5-result.json` (37 species over b4, b40, b43, b44, b45, b46, b47 and b49; 0
unverified, 0 no_research; 11 fields already nulled on audit; 5 review lines), following `BACKFILL_LANDING_BRIEF.md`
and the coordinator's standing rules for this round. The merge wrote seven of the eight files; b49 is untouched because
its one species, Mandarin orange, now writes nothing. The merge plan named no file outside the list. Not committed.

The untouched workflow output and the eight batch files as they were at the start are kept in the session scratchpad
under `r4c5/orig/`. The repair was made by `r4c5/repair.py`, which rebuilds the result file from the untouched copy
and asserts that a landing only nulls values, lands a rule-6 indoor height with a new citation naming the stem, drops a
citation left supporting nothing, or de-splices a quote to a substring of itself (plus the one re-cite, one claim-label
fix and one reorder listed below), and that no citation is left supporting nothing.

## Verification basis

All 33 URLs the chunk's citations point to were cached with status ok when the landing started (19:42 UTC). Nothing
was fetched live and nothing in `.quote_cache` was written, edited, moved or deleted by this landing: the cache held
1,728 entries at the start and at the end, and its newest entry predates the landing. Every page read went through
cache-only tools: `r4c5/qcg.py` runs qc.py only on a URL already cached ok, and `allhits.py` / `ctx.py` read the
cached text through verify_quotes' own `extract()`. verify_quotes was run with `VQ_CACHE_ONLY=1`. Every citation was
run through verify_quotes' `present()` on its cached page, plus a stricter check that the quote sits inside one
extracted line, before and after the repair (`r4c5/cite_audit.py`). The 60 page quotations the repair wrote into new
quotes and unknowns lines were each checked on the cached page with `present()` inside the repair script.

One cache anomaly matters. Ten of the 33 cited pages are cached as flattened, lower-cased text rather than HTML: UF/IFAS
mg040 and EP009, and NC State's Adenium obesum (desert-rose), Asplenium nidus, Cyperus alternifolius, Epiphyllum
oxypetalum (orchid-cactus), Euphorbia tirucalli, Freesia, Phoenix roebelenii and Rhipsalis baccifera pages. qc.py
cannot show element boundaries on them, which is why the researchers' quotes from them came back lower-cased and why
a label glued to its value there shows no U+23CE. The de-splices on those pages follow NC State's field layout as the
HTML-cached NC State pages in this chunk render it ("Dimensions: ⏎ Height: ... ⏎ Width: ..." on Croton, "Attracts: ⏎
Bees ⏎ Pollinators" on Sarracenia purpurea, "Edibility:" apart from its value), the way chunk w1-3 handled Autumn Fern,
and keep the cached text's lower case so each new quote is an exact substring of the stored one. These entries are
worth re-warming with warm_cache.py outside the sandbox.

Other landers were working at the same time. Chunks 6 and 4 were committed during this landing (HEAD moved from
58ec827 to 2702094, then to fca3861); chunk 4's changes to b3, b23-b27, b29-b36 and b38 were still uncommitted when
the merge was applied. Neither commit touched this chunk's files, and the eight files were byte-identical to the start
copies (and to HEAD) when the merge was applied.

## Merge plan totals (applied)

After the repair, `merge_backfill.py` printed "problems: none" and was applied. It wrote 30 species, 100 fields and 62
citations:

- 85 size bounds on 23 species. 19 have all four bounds. Alocasia 'Polly' and Croton have a height maximum only (24 and
  36 in, each a single indoor or cultivar figure) beside a full spread; Small Bi-coloured Ox Tongue has a height maximum
  only (6 in, pot-grown); Cat Palm has both maxima only (96 in, UF/IFAS's single "8 x 8 ft").
- 9 is_edible: 5 true (Banana, Orchid Cactus, Pygmy Date Palm, Common Olive, Pineapple), 4 false (Croton, Desert Rose,
  Indian tree spurge, Satin Pothos).
- 6 attracts_pollinators, all true (Lipstick Plant, Desert Rose, Freesia, Orchid Cactus, Purple Pitcher Plant,
  Japanese Aralia).

Seven species write nothing: Bird of Paradise (is_edible nulled on audit; its only sizes are outdoor stature over 120
in), Goldfish Plant (only a cultivar has a size), Lady Palm (both size minimums nulled on audit), Sweetheart Hoya,
Winged Tropical Pitcher Plant and Swiss Cheese Vine (climbers with no edibility or pollinator value), and Mandarin
orange (is_edible nulled at landing, below). Their unknowns stay in the result file.

Claims per file, against HEAD (2702094, and the same at fca3861; none of the eight files had an uncommitted change
before the merge):

- b4-tricky-cases: 71 -> 90 (+19)
- b40-gesneriads-and-annuals: 83 -> 97 (+14)
- b43-ferns-succulents-and-more: 93 -> 120 (+27)
- b44-palms-and-more: 84 -> 103 (+19)
- b45-fruit-and-carnivores: 88 -> 98 (+10)
- b46-herbs-aquatics-and-companions: 100 -> 106 (+6)
- b47-shade-shrubs: 65 -> 70 (+5)
- b49-fruit-trees-and-native-perennials: 60 -> 60 (not written)

That is +100, one claim per field. A semantic check against the start copies (`r4c5/post_merge_check.py`) confirmed
the merge only added: every pre-existing value, citation, unknowns line and normalization is unchanged, each written
file gained the one standard normalization line, the only new keys are the six backfill fields, and the written values,
citations and unknowns are exactly the result file's. Every new value pairs to a citation written with it, not to an
older one: no existing citation in these records names a backfill field, the loader was run on each merged record to
confirm which quote each claim carries, and again with only the new citations. In the git diff (770 insertions, 62
deletions) the deletions are serialization only: 61 lines gained a trailing comma, and b44, which had no final newline
at HEAD, now ends with one.

## The 5 review lines

The brief's rule was applied: a correction goes in only if the stored quote is spliced (it carries U+23CE, or a label
is glued to its value) and the correction is that same text as the page renders it, or a substring of the stored
quote. Each was checked with qc.py on the cached page first.

- Alocasia 'Polly', mature_spread_in: APPLIED. The stored "Dimensions: Height: 1 ft. 0 in. - 4 ft. 0 in. Width: 1 ft.
  0 in. - 2 ft. 0 in." glues the Dimensions label to both lines; the correction "Width: 1 ft. 0 in. - 2 ft. 0 in." is a
  substring and its own rendered line. The value (12-24 in) is unchanged.
- Alocasia 'Polly', mature_height_in: NOT APPLIED, moot. The hybrid-level "Height: 1 ft. 0 in. - 4 ft. 0 in." would
  support the 12-48 in the audit nulled, and no height citation was left. The height re-landed from 'Polly''s own line
  instead (below).
- Croton, mature_spread_in_min and _max (2 lines, one quote): APPLIED. The stored quote carried U+23CE across
  "Dimensions: ⏎ Height: ... ⏎ Width: ..."; the correction "Width: 2 ft. 0 in. - 6 ft. 0 in." is a substring on its own
  line. The value (24-72 in) is unchanged.
- Purple Pitcher Plant, attracts_pollinators: HELD. The stored quote "Attracts: ⏎ ⏎ Bees ⏎ ⏎ Pollinators" is the
  Attracts field spliced to its two values; the proposed "Attracts Pollinators" is the page's Play Value tag, a
  different field, so it is not the same evidence de-spliced (earlier landings held the same kind of correction,
  including Butterfly Bush's "Attracts Pollinators" in chunk w1-3). As in chunk r3-1, the stored quote was de-spliced
  instead, to its first value, "Bees" (substring, own line). The two
  pollinator citations were then swapped so the Attracts citation comes first: the loader pairs a field with the first
  citation naming it, and the other one, "A nectar source for insects." (Wildlife Value), names no pollinator and on a
  pitcher plant could describe the pitchers' prey lure. attracts_pollinators true stands and now carries "Bees".

No held correction left a field unsupported.

## Fields nulled at landing (9), and why

- Japanese Aralia, all four size fields (72-120 in by 72-120 in), standing rule 1. They rested on Clemson HGIC alone
  ("Fatsia typically grows 6 to 10 feet tall by 6 to 10 feet wide."). The page happens to be cached ok, but no new
  value may rest on Clemson alone. The other figures are outdoor stature over 120 in and would stay null under the
  houseplant rule anyway (NC State's 6 ft - 19 ft 6 in and "at maturity, reaches a height of 19 feet"; RHS 2.5-4 m).
  Both Clemson citations were dropped; attracts_pollinators true (NC State's Attracts field) still lands.
- Freesia, all four size fields (12-24 in by 6-12 in), scope. NC State's page is the Freesia GENUS page ("freesia is a
  genus of fragrant, herbaceous perennials ... there are 16 accepted species, but hybrids are the most common forms."),
  and the research rules say a genus page is not a substitute for a species size. Freesia x hybrida has no NC State
  species page and neither RHS page gives it a size. The researcher had called the page species-level; the auditor
  noted it is a genus page but let the figures stand. This overrides the auditor's keep, as chunk r4-3 did for Rex
  Begonia's group-level spread, and is easy to reverse. Both size citations were dropped; attracts_pollinators true
  still lands.
- Mandarin orange, is_edible (true -> null), as instructed. See "Records the coordinator asked to settle".

The six dropped citations are Japanese Aralia's two Clemson size quotes, Freesia's two NC State size quotes, Mandarin
orange's RHS tag-list quote, and Common Olive's NC State fruit-description quote (replaced by the re-cite below).

The 11 fields nulled on audit stay nulled as the audit left them, except where standing rule 6 re-landed an indoor
figure in their place: Alocasia 'Polly''s height (hybrid figure; the max re-landed at 24 from the cultivar's own line),
Bird of Paradise is_edible (the seeds called edible are also a listed poison part), Croton's height (max re-landed at
36), Bloody Stromanthe's height (re-landed at 24-36), Lady Palm's two size minimums ("can grow to be more than 8 feet
tall" read as a floor) and Pygmy Date Palm's height (re-landed at 60-72).

## Heights landed at landing under standing rule 6 (6 bounds on 4 species)

In each case the audit refuted the height because a page the record already cites gives an indoor or cultivar figure,
and quoted it. The sentence was confirmed verbatim on the cached page with qc.py, it is about the record's own taxon,
and a new citation naming `mature_height_in` was written. Ends that came only from the refuted figure stay null.

- Alocasia 'Polly' (coordinator's instruction): "'Polly' compact, up to 2 feet tall" in the NC State Cultivars list of
  the Alocasia x mortfontanensis page. Max 24, min null. The hybrid-level spread stands.
- Croton: "It is more common to see these plants grown indoors, where they can attain a height of 3 feet." (NC State,
  Codiaeum variegatum). Max 36, min null (the 24 in minimum came only from the refuted Dimensions height).
- Bloody Stromanthe: "The plant grows up to 5 feet tall and 3 feet wide when grown outdoors, but as a houseplant, it is
  usually only 2 to 3 feet tall." (NC State, Stromanthe thalia). 24-36, a published range.
- Pygmy Date Palm: "as an indoor plant, it typically reaches only 5 to 6 feet tall." (NC State, Phoenix roebelenii,
  flat-cached). 60-72, a published range.

## Records the coordinator asked to settle

- Mandarin orange (b49): is_edible null, its citation dropped. The only readable page the record cites is RHS's
  Citrus reticulata (F) page (the Cleopatra mandarin). Searched for 'edible|eaten|culinary|oil|preserv|fresh' with word
  boundaries: besides the "Suggested planting locations and garden types" tag list it has only the genus line "This
  genus produces fruit, but not necessarily edible fruit", and its description ends "... followed by slightly flattened,
  spherical, orange fruit." No statement that the fruit is eaten. The two Missouri Botanical Garden pages refuse this
  machine. The species now writes nothing.
- Common Olive (b45): re-cited, stays true. NC State's own Olea europaea page, already cited, says in its description
  "The fruits can be harvested at either stage and are important commercially as edible fruit, for making olive oil,
  and fuel." That replaced the fruit-description quote. The RHS "need special preparation to make them edible"
  citation stays. The whole preparation condition is now in unknowns: EP515's "Olives typically are not eaten raw from
  the tree and are considered unpalatable as they contain an alkaloid that makes them bitter." and RHS's salted-water and
  dry-curing instructions. No page names a toxic part.
- Japanese Aralia (b47): standing rule 1, all four sizes null, figure quoted in unknowns (above).
- Bloody Stromanthe, Pygmy Date Palm, and Croton (the one other size refuted under check I): rule 6 (above).
- Alocasia 'Polly': height max 24, min null, under rule 6's procedure; the hybrid-level spread stands (above).

## Other citation repairs (brief step 2, no review line)

Each is a substring of the stored quote on its own element, checked on the cached page. No value changed.

- Height and width glued (NC State, flat-cached): Bird's Nest Fern, Umbrella Plant, Mistletoe Cactus (the last two also
  glued the "dimensions:" label) each became "height: ..." and "width: ..."; Pygmy Date Palm's spread became "width: 3
  ft. 0 in. - 5 ft. 0 in." (its quote also carried the refuted height).
- Height and spread glued (RHS summary cards, one extracted line but two cards): Elephant Bush and Cape Sundew each
  became "Max Height ... metres" and "Max Spread ... metres", the form this chunk's other RHS citations use.
- Label glued to its value: Desert Rose "attracts: butterflies hummingbirds" -> "butterflies"; Freesia "attracts: bees
  butterflies" -> "bees"; Orchid Cactus "attracts: moths" -> "moths"; Indian tree spurge "edibility: toxic sap" -> "toxic
  sap"; Pygmy Date Palm "edibility: drupes are edible." -> "drupes are edible.".
- Table row spliced across cells (UF/IFAS EP009, flat-cached): Cat Palm's size quote became its size cell, "8 x 8 ft",
  and its column-header quote "typical size (h x w)", matching the record's existing one-cell EP009 quotes ("Cat palm",
  "Grows best in shade. No major problems.").
- Claim label: Small Bi-coloured Ox Tongue's "mature_height_in 0-6" now reads "mature_height_in max 6" (min is null,
  not 0).

All 85 size values were re-derived from their quotes and match. The decimal inches (Elephant Bush 59.1-98.4 by
39.4-59.1, Rabbit's Foot Fern 19.7-39.4, Watermelon Begonia and Cape Sundew 3.9-19.7) are RHS metres at 39.37, like
the RHS-band conversions already in the corpus.

## Rules re-checked

- Climbers take no size: Lipstick Plant (NC State Plant Type Vine), Orchid Cactus (#climber, climbing), Sweetheart Hoya,
  Winged Tropical Pitcher Plant, Satin Pothos and Swiss Cheese Vine carry none. A sweep of every size-bearing species'
  habit fields found no climber: Mistletoe Cactus (cascading, weeping), Christmas Cactus (arching, weeping) and
  Spiderwort (creeping) trail or hang and keep their sizes.
- Houseplant sizes (all 37 species are is_houseplant true). Every size that lands is an indoor, pot or cultivar figure,
  or a published figure of 120 in or under:
  - Indoor or pot figures: Croton, Bloody Stromanthe and Pygmy Date Palm heights (rule 6), Indian tree spurge ("if
    grown indoors, it will range from 2 to 6 feet tall and 1 to 3 feet wide"), Small Bi-coloured Ox Tongue ("Grown in a
    pot, it generally stays 6 inches tall"), Mistletoe Cactus (NC State: "hanging indoor houseplant where it will grow up
    to 6 feet in length and 2 feet wide"), and 'Polly''s own cultivar line.
  - The rest are figures under the ceiling; the largest are Japanese Aucuba (120 in, at it), Desert Rose (108), Elephant
    Bush (98.4) and Cat Palm (96).
  - Outdoor-only figures over 120 in stay null: Banana, Bird of Paradise, Common Olive, Mandarin orange and, after the
    Clemson null, Japanese Aralia.
- is_edible true: all five are food plants, and every condition a page names is in unknowns. Banana (fruit eaten
  fresh; no condition applies: the page's cooking requirement is for plantains, which UF/IFAS treats as hybrids), Orchid
  Cactus (fruit only; "not known to have edible flowers"), Pygmy Date Palm (drupes only; spines), Common Olive (cured,
  not raw), Pineapple (ripe fruit; NC State's poison fields, bromelin, calcium oxalate, overconsumption and sap
  dermatitis). No toxicity sentence is cited for a true.
- is_edible false: all four rest on a page's own poison statement: Croton (Poison Symptoms), Desert Rose ("all parts of
  the plant are poisonous if ingested."), Indian tree spurge (Edibility field "toxic sap"), Satin Pothos (Plant Type
  "Poisonous"). RHS's page for the cultivar 'Argyraeus', already cited by the record, also says "Harmful if eaten;
  skin/eye irritant."; it is not in the record's unknowns and was not added, since false needs no toxicity note.
- attracts_pollinators true: all six name hummingbirds, butterflies, bees, moths or pollinators, and none rests on
  birds eating seed. Freesia's comes from the same genus page as its nulled sizes; the research rules restrict genus
  pages for size and edibility, not for pollinators, so it stands.

## Unknowns corrected or added at landing

Corrections are marked "corrected at landing"; added lines say "noted at landing, verified against the cached copy".
Every page quotation in them was read on the cached page.

- Alocasia 'Polly': Poison Part is Flowers, Fruits, Leaves, Roots, Sap/Juice, Seeds, Stems (the note had two) plus "All
  parts of this plant are toxic ..."; the size and "no cultivar-substitution concern" lines rewritten; the rule-6 line
  added.
- Croton: the full Poison Part list (Bark through Stems; the note had two from a cut-off window); the size line
  rewritten; the rule-6 line added.
- Bloody Stromanthe and Pygmy Date Palm: the "no indoor/outdoor distinction needed" size lines rewritten; rule-6 lines
  added. Pygmy's Clemson line now quotes the page's pygmy date palm section ("it can eventually become a 12-foot tree").
- Bird's Nest Fern: "five readable pages" is four; Clemson's indoor frond length added (see below).
- Desert Rose: RHS does have a species page (plants/426), with 1-1.5 m by 1-1.5 m and "Harmful if eaten.".
- Rabbit's Foot Fern: Clemson (rabbits-foot-fern) is cached http-403 and was not read.
- Freesia: the size line now explains the null; the RHS line no longer says size was taken from NC State.
- Mistletoe Cactus: NC State's "uses (ethnobotany): medical and environmental uses such as medicine, food, and animal
  food" was missed; too vague for true, so null stands.
- Orchid Cactus: Clemson does say "Orchid cacti have flattened, fleshy stems, often deeply toothed, with a trailing
  growth habit."
- Watermelon Begonia: NC State's description says "the plant grows up to 8 inches tall" (see below).
- Common Olive: the preparation condition completed; EP515 does give a size ("canopies up to 30 ft") and does address
  eating; RHS's spread is under 120 in; the re-cite line added.
- Purple Pitcher Plant: the de-splice, the held correction and the reorder.
- Pineapple: FP039 is UF/IFAS, not "FDA/IFAS"; NC State's one pollination mention is fruit-set biology.
- Satin Pothos: Clemson has a short Scindapsus pictus subsection; its toxicity sentence is about pothos generally.
- Japanese Aralia: the size line now explains the null. Japanese Aucuba: NC State's "They are pollinated by small
  flies." is genus-level text, not an Attracts field; null stands.
- Mandarin orange: the true-framed harm line reworded for null; the missed "A spiny, evergreen tree to 3m tall" noted;
  the null line added.
- Non-writing species, whose unknowns do not travel: Bird of Paradise (its stale "is_edible set TRUE" line now says
  null; Poison Part is Flowers, Fruits, Leaves, Seeds), Sweetheart Hoya ("Vine" is NC State's Plant Type, not its Life
  Cycle), Swiss Cheese Vine (the two fruit quotes' pages were reversed; Poison Part adds Roots, Sap/Juice, Stems).

## verify_quotes, per touched file

`VQ_CACHE_ONLY=1 .venv/bin/python scripts/catalog/verify_quotes.py <file>`, after the merge (HEAD numbers in brackets):

- b4-tricky-cases: 60 hit, 3 MISS, 0 inconclusive, 9 skipped (49 / 3 / 0 / 9)
- b40-gesneriads-and-annuals: 114 hit, 1 MISS, 0 inconclusive, 39 skipped (106 / 1 / 0 / 39)
- b43-ferns-succulents-and-more: 136 hit, 0 MISS, 0 inconclusive, 33 skipped (121 / 0 / 0 / 33)
- b44-palms-and-more: 150 hit, 0 MISS, 0 inconclusive, 10 skipped (137 / 0 / 0 / 10)
- b45-fruit-and-carnivores: 248 hit, 0 MISS, 0 inconclusive, 110 skipped (240 / 0 / 0 / 110)
- b46-herbs-aquatics-and-companions: 182 hit, 0 MISS, 0 inconclusive, 34 skipped (178 / 0 / 0 / 34)
- b47-shade-shrubs: 99 hit, 0 MISS, 0 inconclusive, 29 skipped (96 / 0 / 0 / 29)
- (b49-fruit-trees-and-native-perennials, not written: 79 hit, 1 MISS, 0 inconclusive, 23 skipped, as at HEAD)

Hits rose by exactly the 62 new citations. NEW-FIELD MISS, SKIP and INCONCLUSIVE are zero, and every MISS and SKIP line
is identical to HEAD's; none names a backfill field, so commit_backfill's untested check will not trip on them. The
five MISS lines predate this landing and name none of the six fields:

- b4 Bird of Paradise, Spiderwort / Inch Plant and Alocasia 'Polly' name citations (NC State "— previous names"
  composite quotes).
- b40 Florist's Gloxinia direct_sun_hours_max (UGA "Avoid high-intensity, direct sunlight.").
- b49 White Mulberry common_name (RHS common-names list).

## Tests

- `tests/test_tranche_invariants.py` passes on its own: 3,880 passed.
- The combined run with `test_claim_ingest.py` gave 3,886 passed and 1 failed, the expected count assert. First run:
  `assert 6707 == 6493`, at HEAD 2702094 with chunk 4's +114 still uncommitted in the tree (+100 this chunk, +114
  chunk 4). Chunk 4 was then committed (fca3861), and the re-run printed `assert 6707 == 6607`: the +100 is exactly
  this chunk, whose seven files are now the only uncommitted verified files.
- `tests/test_claim_ingest.py` was not edited.

## For a person to decide

- Freesia's sizes were nulled at landing against the auditor's keep (genus page, see above). Reverse by restoring the
  four values and the two NC State size citations from `r4c5/orig/` if the genus page's figure is acceptable for the
  hybrid complex; NC State's description does describe "the plant" as "growing 1 to 2 feet tall".
- Spreads that are the page's outdoor width beside an indoor height: Bloody Stromanthe's 36 in max is the page's "3 feet
  wide when grown outdoors", Pygmy Date Palm's 60 in max its "5 feet wide" outdoors, and Croton's 24-72 in comes from the
  same Dimensions block as the refuted native-habitat height. No page gives an indoor width and each is under 120 in, so
  they land as the audit left them.
- Bird's Nest Fern: Clemson's how-to-grow page gives an indoor frond length, "When grown indoors as a houseplant, the
  fronds typically grow 18 to 24 inches long.", and outdoors "fronds 4 to 5 feet tall"; the landed NC State 36-60 in is
  close to the outdoor figure. Not changed: frond length, Clemson alone, and not refuted on audit (RHS 1-1.5 m indoors,
  UF/IFAS 2-4 ft).
- Watermelon Begonia: NC State says "the plant grows up to 8 inches tall" (a max of 8 in, agreeing with Clemson);
  RHS's 0.1-0.5 m (3.9-19.7 in) landed. A re-research could prefer NC State.
- Umbrella Plant ("as a houseplant, the size can be cut in half") and Rabbit's Foot Fern (RHS: "as a houseplant it is
  much more compact") land general figures that their own pages say run smaller indoors, with no indoor number.
- Mistletoe Cactus: the 48 in height minimum comes from the Dimensions block; the indoor sentence gives only a maximum
  ("up to 6 feet in length"), and for a hanging plant "height" is really trailing length.
- Cat Palm: 8 x 8 ft is UF/IFAS's South Florida landscape "typical size"; Clemson's indoor-palms page gives Cat Palm no
  number.
- Mandarin orange: RHS's "A spiny, evergreen tree to 3m tall" (about 118 in), beside greenhouse or conservatory
  growing, could give a height max in a re-research; is_edible needs a page that says the fruit is eaten.
- Japanese Aralia needs a size from a page other than Clemson; NC State and RHS give outdoor stature over 120 in.
- One-word quotes ("Bees", "bees", "butterflies", "moths", "Pollinators", "Poisonous", "toxic sap") follow earlier
  landings' precedent but verify weakly, since the word can appear elsewhere on the page.
- Re-warm the ten flat-cached pages listed above.

Scratch work is in the session scratchpad under `r4c5/`: the untouched workflow output and batch files (`orig/`), the
HEAD copies, the repair script and its output, the cache-only qc guard and page readers, the citation audit before and
after, the climber and indoor-size sweep, the merge plan and apply output, the post-merge check, verify_quotes output
before and after, and the test output.
