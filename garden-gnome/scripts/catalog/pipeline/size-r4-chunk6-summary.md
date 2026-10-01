# Size backfill, round 4 chunk 6 -- landing summary

Landed 2026-09-27 from `size-r4-chunk6-result.json` (24 species over b6, b7, b75 and b81; 0 unverified, 0
no_research; 2 fields already nulled on audit; 22 review lines), following `BACKFILL_LANDING_BRIEF.md` and the
coordinator's standing rules for this round. Only those four batch files were touched, and the merge plan named no
other. Not committed.

The untouched workflow output and the four batch files as they were at the start (byte-identical to HEAD, 58ec827)
are kept in the session scratchpad under `r4c6/orig/`. The repair was made by `r4c6/repair.py`, which rebuilds the
result file from the untouched copy and asserts that a landing only nulls values, only drops citations or de-splices
a quote to a substring of one of the record's original quotes (a split keeps each claim a substring of the original
claim), and leaves no citation supporting nothing.

Other landing agents were working at the same time: `size-r4-chunk4-result.json` and `size-r4-chunk5-result.json`
appeared in this directory during the landing. Neither touched these four files; each was confirmed byte-identical
to its start copy immediately before `--apply`.

## Verification basis

All 27 URLs the chunk's citations point to were cached with status ok when the landing started (19:39 UTC). Nothing
was fetched live and nothing in `.quote_cache` was written, edited, moved or deleted by this landing: the cache held
1,728 entries at the start and at the end, with the same file list. Every qc.py read went through a guard
(`r4c6/qcg.py`) that runs qc.py only on a URL already cached with status ok, with `VQ_CACHE_ONLY=1`; longer context
reads used `r4c6/ctx.py`, which reads cache entries only. verify_quotes was run with `VQ_CACHE_ONLY=1`. Every
citation was also run through verify_quotes' own `present()` against its cached page, plus a stricter check that the
quote sits inside one rendered line, before and after the repair (`r4c6/cite_audit.py`: 11 flagged before, all of
them the review-line quotes; 0 after). None of this chunk's auditor summaries reports touching the cache.

## Merge plan totals (applied)

After the repair, `merge_backfill.py` printed "problems: none" and was applied. It wrote 22 species, 100 fields and
60 citations:

- 81 size bounds on 21 species. 19 have all four. Dwarf Umbrella Tree has a height only (36-72 in; its spread was
  nulled on audit) and Mexican Snowball has a height maximum only (RHS "Up to 10 cm") plus a spread.
- 10 is_edible: 7 true (Basil, Chives, Cilantro, Dill, Oregano, Parsley, Thyme), 3 false (Dwarf Umbrella Tree,
  English Ivy, Lucky Bamboo).
- 9 attracts_pollinators, all true (Mexican Snowball, the seven herbs, Burro's Tail).

Two species write nothing: Areca Palm (its height was nulled at landing under standing rule 1) and Ti Plant (its
is_edible was nulled at landing under standing rule 2; its sizes were already null). Their unknowns stay in the
result file.

Claims per file, against HEAD (58ec827; none of the four files had an uncommitted change before the merge):

- b6-core-gaps: 89 -> 114 (+25)
- b7-culinary-herbs: 55 -> 97 (+42)
- b75-native-bog-and-orchids: 64 -> 68 (+4)
- b81-houseplants: 79 -> 108 (+29)

That is +100, one claim per field. A semantic check against the start copies confirmed the merge only added: every
pre-existing value, citation, unknowns line and normalization is unchanged, each file gained the one standard
normalization line, the only new keys are the six backfill fields, and the two species that write nothing are
untouched. Every new value pairs to a citation written with it, not an older one (checked by running the real loader
on each merged record and matching the chosen citation; no older citation in these records names any of the six
fields). In the git diff the 48 deleted lines are serialization only: 46 gained a trailing comma, and b6 and b81,
which had no final newline at HEAD, now end with one.

## The 22 review lines

The brief's rule was applied: a correction goes in only if the stored quote is spliced (it carries U+23CE, or a label
is glued to its value) and the correction is that same text as the page renders it, or a substring of the stored
quote. Each was confirmed with qc.py on the cached page first.

- African Violet, 4 size lines: APPLIED. The stored "Dimensions: Height: 0 ft. 6 in. - 0 ft. 9 in. Width: 0 ft. 6
  in. - 0 ft. 9 in." glued the label to two separately rendered lines. The corrections "Height: 0 ft. 6 in. - 0 ft. 9
  in." and "Width: 0 ft. 6 in. - 0 ft. 9 in." are each their own rendered line and a substring of the stored quote.
  No value changed (6-9 in by 6-9 in).
- Round-leaved Sundew, 4 size lines: APPLIED. "Height: 0 ft. 2 in. - 0 ft. 10 in. Width: 0 ft. 4 in. - 0 ft. 6 in."
  glued two rendered lines and was the only size citation for both stems, so it was split into a height citation and
  a spread citation (1 -> 2). Each quote is its own rendered line and a substring of the stored quote; each claim is
  the matching half of the original claim. No value changed (2-10 in by 4-6 in).
- Peacock Plant (4 lines) and Polka Dot Plant (4 lines): APPLIED. Both stored quotes were U+23CE "Dimensions:"
  splices. The corrections are NC State's Height and Width lines, each its own rendered line and a substring:
  "Height: 1 ft. 0 in. - 2 ft. 0 in." / "Width: 0 ft. 8 in. - 1 ft. 0 in." (Peacock) and "Height: 1 ft. 0 in. - 2
  ft. 0 in." / "Width: 0 ft. 9 in. - 1 ft. 0 in." (Polka Dot). No value changed.
- Oregano, 4 size lines and is_edible: APPLIED. All three stored quotes were U+23CE splices. "Height: 1 ft. 0 in. - 3
  ft. 0 in.", "Width: 1 ft. 0 in. - 2 ft. 0 in." and "Leaves and flowers for tea, flavoring." are each their own
  rendered line and a substring. No value changed.
- Oregano, attracts_pollinators: HELD. The proposed "#butterfly friendly #moth friendly #bee friendly" is a piece of
  the page's tag list, a different element from the stored U+23CE "Attracts:" quote and not a substring of it. The
  stored quote was de-spliced to its stacked value "Pollinators", as earlier chunks did; the claim still reads "NC
  State Attracts: Bees, Butterflies, Moths, Pollinators", which is what the page's Attracts field lists.
  attracts_pollinators true stands.

No held correction left a field unsupported.

## Fields nulled at landing (4), and why

- Areca Palm, mature_height_in_min/max (72-84 in), standing rule 1, as instructed. The pair rested on Clemson HGIC's
  Indoor Palms factsheet alone. That page happens to be cached ok and the quote checks, but no new value may rest on
  Clemson alone. The citation was dropped and the unknowns line now quotes Clemson's indoor figure as cached ("this
  very popular palm grows 6 to 7 feet tall indoors", "arecas grow 6 to 10 inches a year and often outgrow their
  allotted space"). The only other heights are outdoor statures over 120 in (NC State 10-30 ft, RHS 4-8 m), so Areca
  Palm now writes nothing.
- Burro's Tail, is_edible (true -> null), standing rule 2, as instructed. The citation was dropped. The researcher's
  "set to true (conditional)" line was replaced by one line with the page's words: NC State's Edibility field, "Stems
  and leaves can be eaten, but when ingested in large quantities, can cause stomach upset.", and the fact that the
  page's only toxicity wording is its non-toxic-for-pets tags.
- Ti Plant, is_edible (false -> null), standing rule 2. This one was not on the coordinator's list; it came out of the
  check that no false contradicts its own page. The NC State page cited for false has a Uses (Ethnobotany) field
  reading "Used as a medicine, fuel, and food. The leaves are used as a food wrapper in Hawaiian cooking.", and the
  cited sentence is a toxicity statement ("The Ti plant is considered to have a low toxicity in humans and can cause
  gastro-intestinal discomfort, if ingested."), not a denial. A poisonous plant whose only food mention is folk use
  goes to null, with the food mention and the toxicity in unknowns. The citation was dropped; the unknowns line gives
  the Ethnobotany text, the dropped sentence and the poison fields (Severity Low, Symptoms, Saponins, Contact
  Dermatitis Yes, Poison Part Sap/Juice, tags). Its four sizes were already null (NC State's only figure is the
  outdoor 9-15 ft), so Ti Plant now writes nothing. Easy to reverse from `r4c6/orig/`.

Three citations were dropped: Areca Palm's Clemson height quote and the is_edible citations of Burro's Tail and Ti
Plant.

The two fields nulled on audit stay null: Dwarf Umbrella Tree's spread pair (48-96 in, from the Dimensions block
whose height is the 10-25 ft outdoor stature).

## Records the coordinator asked to settle

- Burro's Tail: is_edible null, citation dropped, one unknowns line with the page's words (above). Its sizes and
  attracts_pollinators true stand; Habit/Form is Creeping, Prostrate, Spreading, a trailing plant that does not climb.
- Horsehead Philodendron: NC State's Habit/Form reads "Ascending" and "Erect", and its Plant Type "Houseplant",
  "Perennial", "Poisonous" and "Shrub". Neither says climbing or vine, so standing rule 3 does not apply and the four
  sizes stand (48-120 in by 72-120 in; the maximum is exactly 120 in, which does not exceed the houseplant cap). The
  description does say "It can grow 4 to 10 feet tall and 6 to 10 feet wide and reclines or creeps with age. It will
  climb with adventitious roots if given support"; that is now quoted in a "Climber check" unknowns line and listed
  below for a person.
- Areca Palm: height pair nulled, Clemson's indoor figure quoted in unknowns (above).

## Rules re-checked

- Climbers take no size. English Ivy (Habit/Form Ascending, Climbing, Creeping) carries none. Every one of the 21
  species that lands a size was checked on its NC State page: none has a Climbing habit, a Vine plant type or a
  Climbing Method field. Trailing, creeping or cascading plants keep their size: Burro's Tail, Purple Heart
  (Cascading, Clumping, Spreading), Round-leaved Sundew (Prostrate), Zebra Plant (Clumping, Creeping, Erect).
- Houseplant sizes (all 24 species are is_houseplant true). Every size that lands is 120 in or under; the largest is
  Horsehead Philodendron's 120 in. The one indoor-labelled figure is Dwarf Umbrella Tree's height ("3 to 6 feet tall,
  smaller ornamental when grown as a houseplant"); the rest are published general figures well under 120 in.
  Outdoor-only figures over 120 in stay null: Areca Palm's spread (NC State 8-15 ft, RHS 2.5-4 m) and Ti Plant's
  sizes (NC State 9-15 ft). Nothing was nulled at landing under this rule.
- Units and ends. All sizes are inches; RHS metres were converted at 39.37 (Lucky Bamboo 19.7-39.4 by 3.9-19.7,
  Mexican Snowball 3.9 and 3.9-19.7). Mexican Snowball's single "Up to 10 cm" fills the height maximum only.
- is_edible true: all seven are common culinary herbs with an NC State Edibility statement. Conditions are in
  unknowns: Chives (the Edibility field's "small quantities" and poisonous-characteristics sentences, Problem for
  Cats/Dogs/Horses, and EP631's Allium toxicity for dogs, cats and cattle, added), Parsley (furanocoumarins,
  photosensitization "large amounts are needed", Problem for Cats/Dogs/Horses, "The fruit and seeds are poisonous to
  birds"), Oregano (the subspecies page's pet tags, added). For Basil, Cilantro, Dill and Thyme every cached page the
  record cites was scanned for toxicity, poison, harm, irritant and allergy wording: none names a toxic part or a
  preparation. No toxicity sentence is cited for a true.
- is_edible false: all three rest on a page's own denial or poison statement: English Ivy (Edibility field "Leaves and
  berries are toxic to humans."), Lucky Bamboo ("Humans should not eat this plant.") and Dwarf Umbrella Tree ("Poisonous
  to Humans" in its Problems field). None of those pages mentions a food use (their Ethnobotany fields were read).
- attracts_pollinators true: all nine name bees, butterflies, moths, hummingbirds or pollinators. Mexican Snowball
  (Attracts: Bees, Butterflies, Hummingbirds; "Bees" occurs once on the page), Basil (Penn State "Nectar-bearing flowers
  attract bees, butterflies, and other pollinators."), Chives, Dill and Thyme (NC State prose), Oregano (Attracts list),
  Parsley (Attracts: Butterflies; the description says the flowers "attract butterflies"), Cilantro (Attracts:
  Butterflies, Predatory Insects; the larval-host context is now disclosed) and Burro's Tail (Play Value "Attracts
  Pollinators"; Attracts: Pollinators, Songbirds). None rests on birds eating seed or fruit.

## Unknowns corrected or added at landing

Corrections are marked "corrected at landing"; added lines say "noted at landing, verified against the cached copy".
Every page quotation in them was read on the cached page, and the 42 verbatim quotations were also run through
verify_quotes' `present()` against their cached pages (0 misses).

- Areca Palm: the height line now explains the nulling and quotes Clemson's indoor figure (moot for the catalog).
- Burro's Tail: the edibility line (above).
- Ti Plant: the toxicity line became the is_edible-null line (above; moot for the catalog).
- Dwarf Umbrella Tree: the size line had recorded the audited 48-96 in spread as a "houseplant/general" figure; it now
  says the pair was nulled on audit, gives the outdoor figures that were not used, and quotes the uncited container
  sentence ("will only get from 4 to 6 feet high and wide in a container").
- Lucky Bamboo: Poison Part is Flowers, Fruits, Leaves, Roots, Sap/Juice and Stems (the line had Flowers and Fruits,
  as the auditor noted); RHS's "Pets (dogs, cats, rabbits, rodents): Harmful if eaten." added. The size line had
  called the RHS page a cultivar page; it is "Dracaena sanderiana green-leaved | Belgian evergreen green-leaved", an
  informal descriptor with no quoted cultivar name and "Name Status Unresolved".
- Basil: UMD does give a size ("matures about 18 inches tall", worded for Ocimum species) and the cited Penn State page
  gives "Height is 12 to 24 inches; width is 12 to 24 inches."; the line had said neither contributed size data (the
  auditor's note).
- Chives: the Edibility field points at a "Poisonous to Humans" section the cached page does not carry (no Poison
  fields at all), now said. The line listing EP631 among pages "not separately queried" and saying no page returned a
  non-ok status was corrected (the MOBOT page is not readable), and EP631's wild garlic entry was added ("Dogs, cats,
  and cattle are highly susceptible to Allium toxicity." ... "and chives ( Allium schoenoprasum ), have a similar
  effect on dogs, cats, and cattle."), as the auditor asked.
- Cilantro: the Attracts field's other value (Predatory Insects), the Pollinator Garden theme and the larval-host text
  ("Larval host plant to swallow-tailed butterflies", "#butterfly caterpillar host") added.
- Dill: Penn State's figure is "Height is 1-4 feet; width is 12-24 inches." (12-48 in; the line had "12 ft-48 in");
  RHS's figures are smaller than NC State's, not "in the same range" (the auditor's note).
- Oregano: the "not queried ... no page contradicted these values" line now gives Penn State's and RHS's figures and
  the unreadable Clemson and MOBOT pages; the subsp. hirtum page's "#problem for dogs #problem for horses #problem for
  cats" added (the auditor's note).
- Thyme: the Clemson herbs factsheet is cached as http-403 and was not read either (the auditor's note); Penn State's
  and RHS's agreeing figures added.
- Horsehead Philodendron: "four designated pages" listing three is corrected (MOBOT is the fourth); the climber-check
  line added.
- Panda Plant: Poison Part is Flowers, Fruits, Leaves, Roots, Sap/Juice, Seeds and Stems (the line had Flowers and
  Fruits).
- Purple Heart: Poison Part is Flowers, Leaves, Roots, Sap/Juice and Stems (the line had Flowers and Leaves), the
  Poison Symptoms text added, and RHS's "Potentially harmful Skin allergen. Wear gloves and other protective
  equipment when handling" added (the auditor's note).

## verify_quotes, per touched file

`VQ_CACHE_ONLY=1 .venv/bin/python scripts/catalog/verify_quotes.py <file>`, after the merge (HEAD numbers in brackets):

- b6-core-gaps: 131 hit, 3 MISS, 0 inconclusive, 33 skipped (116 / 3 / 0 / 33)
- b7-culinary-herbs: 127 hit, 1 MISS, 0 inconclusive, 26 skipped (99 / 1 / 0 / 26)
- b75-native-bog-and-orchids: 117 hit, 0 MISS, 0 inconclusive, 10 skipped (115 / 0 / 0 / 10)
- b81-houseplants: 192 hit, 0 MISS, 0 inconclusive, 18 skipped (177 / 0 / 0 / 18)

Hits rose by exactly the 60 new citations. No new-field citation is a MISS, SKIP or INCONCLUSIVE, and every MISS and
SKIP line is identical to HEAD's. No pre-existing SKIP names a backfill field, so commit_backfill's untested check will
not trip on them. The four MISS lines predate this landing and name none of the six fields:

- b6 Mexican Snowball, a UGA B1318 "Table 3 coding key" composite.
- b6 Areca Palm, two UGA B1318 composites (light/water/soil codes; the humidity-code conflict).
- b7 Basil, RHS's hardiness composite ('H1C" (can be grown outside in summer, 5-10°C minimum)').

## Tests

- `tests/test_tranche_invariants.py` passes on its own: 3,880 passed.
- The combined run with `test_claim_ingest.py` gave 3,886 passed and 1 failed, the expected count assert
  `assert 6493 == 6393`. When it ran, the only uncommitted verified files were this chunk's four, so the +100 is
  exactly this chunk; if another chunk's merge lands before this one is committed, the total will include it.
- `tests/test_claim_ingest.py` was not edited.

## For a person to decide

- Ti Plant's is_edible was nulled at landing on standing rule 2 without being on the coordinator's list (see above).
  Reverse by restoring false and the NC State citation from `r4c6/orig/` if the Ethnobotany note is not taken as a
  food use.
- Horsehead Philodendron keeps 48-120 in by 72-120 in on the Habit/Form test the coordinator set, but its description
  says it "will climb with adventitious roots if given support". If "anything that climbs" should take that in, null
  all four.
- Burro's Tail keeps NC State's 12-48 in height (trailing plants keep their size, and the auditor passed it), but the
  same page says the stems trail "up to 24 inches long" and RHS gives 0.1-0.5 m, so the 48 in maximum probably
  measures hanging stem length rather than height.
- Lucky Bamboo's four sizes come from RHS's "green-leaved" page. It reads as the plain green form of the species, not
  a named cultivar, so they land; if it is taken as below species level, null all four.
- Needs re-research (a landing does not set values): Areca Palm (an indoor height from a page other than Clemson);
  Dwarf Umbrella Tree's spread (NC State's container sentence would give 48-72 in); Panda Plant, Purple Heart and
  Horsehead Philodendron is_edible, still null although their NC State pages carry poison statements ("This plant is
  poisonous if ingested.", "Ingestion of the plant can cause mouth and stomach irritation for humans and pets.",
  "#poisonous if ingested") of the kind earlier chunks landed as false; Ti Plant's sizes (UF/IFAS FP141 gives a
  landscape "Height: 3 to 10 feet" and "Spread: 2 to 4 feet", which the researcher set aside on anchor precedence).
- Weak single-word quotes, disclosed rather than changed: Mexican Snowball "Bees" (occurs once on its page, in the
  Attracts field), Cilantro's "Butterflies" (also in its larval-host text) and Parsley's "Butterflies" (also in its
  description, "attract butterflies"). Oregano's de-spliced "Pollinators" also occurs in its Play Value field and
  description.
- Sizes disclosed but not changed: Basil (Penn State's 12-24 in width is wider than NC State's 4-14 in; RHS gives
  0.1-0.5 m both ways), Dill (Penn State and RHS run lower than NC State's 30-60 in by 24-36 in), and RHS's metre
  bands, which differ from the NC State blocks that landed: Burro's Tail, Purple Heart, Peacock Plant and Polka Dot
  Plant (0.1-0.5 m both ways), Panda Plant (0.5-1 m by 0.1-0.5 m) and Horsehead Philodendron (2.5-4 m both ways,
  over the cap, like UF/IFAS's 6-12 ft by 10-15 ft on its P. selloum page).

Scratch work is in the session scratchpad under `r4c6/`: the untouched workflow output and batch files (`orig/`), the
repair script, the cache-only qc guard, the context reader, the citation audit, the merge plan and apply output,
verify_quotes output before and after, and the pytest output.
