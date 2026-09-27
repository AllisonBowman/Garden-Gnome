# Size backfill, round 4 chunk 3 -- landing summary

Landed 2026-09-27 from `size-r4-chunk3-result.json` (39 species over b1, b11, b13, b14, b15, b19, b2, b20, b21 and
b22; 0 unverified, 0 no_research; 10 fields already nulled on audit; 6 review lines), following
`BACKFILL_LANDING_BRIEF.md` and the coordinator's standing rules for this round. Only those ten batch files were
touched, and the merge plan named no other. Not committed.

The untouched workflow output and the ten batch files as they were at the start are kept in the session scratchpad
under `r4c3/orig/`. The repair was made by `r4c3/repair.py`, which rebuilds the result file from the untouched copy
and asserts that a landing only nulls values, only drops citations or de-splices a quote to a substring of itself, and
leaves no citation supporting nothing.

## Verification basis

All 43 URLs the chunk's citations point to were cached with status ok when the landing started (18:26 UTC), after the
coordinator's re-seed. Nothing was fetched live and nothing in `.quote_cache` was written, edited, moved or deleted by
this landing: the cache held 1,700 entries at the start and at the end. Every page read went through a guard
(`r4c3/qcg.py`) that runs qc.py only on a URL already cached with status ok, and verify_quotes was run with
`VQ_CACHE_ONLY=1` (c113cd2). Every citation was also run through verify_quotes' own `present()` against its cached page,
plus a stricter check that the quote occurs inside one rendered line, before and after the repair (`r4c3/cite_audit.py`).

The auditors of this chunk ran before f6d0044. By their own summaries, 28 of them deleted the ProxyError or 403
entries their sandboxed fetches had cached, one restored two ok pages from the main checkout's cache (Peace Lily) and
one moved an entry into the scratchpad (Spanish Moss). None of that was done by this landing; it is recorded
here because it happened in the shared cache.

## Merge plan totals (applied)

After the repair, `merge_backfill.py` printed "problems: none" and was applied. It wrote 33 species, 124 fields and 81
citations:

- 91 size bounds on 25 species. 21 have all four bounds. Fiddle Leaf Fig, Rubber Plant and Majesty Palm have a height
  only (indoor figure; no indoor spread on any page), and Poinsettia has a height maximum only ("rarely exceeds 2 to 3
  feet").
- 19 is_edible: 6 true (Monstera, Pepper, Cockscomb, Lemon, Yucca Cane, Voodoo Lily), 13 false.
- 14 attracts_pollinators: 13 true, 1 false (Rubber Plant).

Six species write nothing: Heart Leaf Philodendron, Wax Plant and Mini Monstera (climbers with no edibility or
pollinator value), Peace Lily (all four sizes nulled on audit), Dragon Tree and String of Pearls (their researchers
could not read the anchor pages). Their unknowns stay in the result file.

Claims per file, against HEAD (c151052; none of the ten files had an uncommitted change before the merge):

- b1-foliage-core: 106 -> 118 (+12)
- b11-veg-round4: 82 -> 88 (+6)
- b13-annual-flowers1: 69 -> 79 (+10)
- b14-annual-flowers2: 59 -> 70 (+11)
- b15-perennials1: 73 -> 79 (+6)
- b19-toxic-ornamentals: 72 -> 83 (+11)
- b2-figs-and-succulents: 65 -> 84 (+19)
- b20-common-ornamentals: 68 -> 85 (+17)
- b21-houseplant-gaps: 67 -> 92 (+25)
- b22-aroid-genus-gaps: 43 -> 50 (+7)

That is +124, one claim per field. A semantic check against the start copies confirmed the merge only added: every
pre-existing value, citation, unknowns line and normalization is unchanged, each file gained the one standard
normalization line, and the only new keys are the six backfill fields. Every new value pairs to a citation written
with it, not to an older one (checked by running the loader on each merged record with only its new citations). In the
git diff the 69 deleted lines are serialization only: 68 gained a trailing comma, and b21, which had no final newline
at HEAD, now ends with one.

## The 6 review lines

The brief's rule was applied: a correction goes in only if the stored quote is spliced (it carries U+23CE, or a label
is glued to its value) and the correction is that same text as the page renders it, or a substring of the stored
quote. Each was confirmed with qc.py on the cached page first.

- Heart Leaf Philodendron, "REFUTED but unmapped field unknowns (toxicity note)": worked. The note now gives NC State's
  Poison Part in full (Flowers, Fruits, Leaves, Roots, Sap/Juice, Stems; it had Flowers and Fruits) and the Problems
  field with Poisonous to Humans. Its two Clemson lines had the pages reversed and were corrected. Moot for the catalog:
  the species writes nothing, so its unknowns do not travel.
- Spider Plant, "REFUTED but unmapped field unknowns (refused-pages statement)": worked. The line saying all three pages
  fetched ok now records that the Clemson indoor-plants factsheet returned 403 to the auditor and is cached as
  http-403. No field depends on it.
- Sago Palm, 2 lines (mature_spread_in_min/max): APPLIED. The stored quote "⏎Max Spread⏎   1-1.5 metres ... ⏎Max
  Height⏎ ..." is a U+23CE splice of RHS's stacked Size panel. The correction "Max Spread         1-1.5 metres" is the
  same label and value as RHS renders them in one run in its summary block, and qc.py shows it there. No value changed
  (39-59 in).
- Fiddle Leaf Fig, is_edible: HELD. The proposed "This plant is toxic to humans, cats, and dogs if ingested." is a
  different sentence (the description), not the stored quote de-spliced. The stored "Edibility: Toxic if ingested."
  glues the field label to its value across boundaries, so it was de-spliced to the value, "Toxic if ingested.", a
  substring on its own rendered line. is_edible false stands.
- Lemon, attracts_pollinators: APPLIED. "Attracts: Bees" glued the label to the field's value; the correction "Bees" is
  a substring and the field's only value on its own line. attracts_pollinators true stands.

No held correction left a field unsupported.

## Fields nulled at landing (9), and why

- Chinese Evergreen, all four size fields (24-36 in by 18-24 in), standing rule 1. They rested on Clemson HGIC alone
  ("Ribbon Aglaonema grows 2 to 3 feet tall and 18 to 24 inches wide, ..."). The page happens to be cached ok and the
  quote checks, but the rule is that no new value rests on Clemson alone. NC State's page is the Aglaonema genus page,
  whose Dimensions block is not a species figure. The citation was dropped; is_edible false (NC State) still lands.
- Sago Palm, is_edible (true -> null), standing rule 2, as instructed. See "Records the coordinator asked to settle".
- Aloe Vera, is_edible (true -> null), standing rule 2, as instructed.
- Purple Shamrock, is_edible (true -> null), standing rule 2, as instructed: the page names toxicity and pet problems.
- Rex Begonia, mature_spread_in_min/max (12-18 in), scope. The audit nulled the height because NC State's "Begonia –
  Rex Types" Dimensions block describes "This informal group includes the species Begonia rex and the many hybrids
  derived from it", not the species. The spread came from the same block, so it has the same defect; the auditor kept
  it only because no species-level spread contradicts it. The Width citation was dropped. Rex Begonia now writes only
  is_edible false. This overrides the auditor's keep and is easy to reverse if the group figure is acceptable.

The five dropped citations are Chinese Evergreen's Clemson size quote, the is_edible citations of Sago Palm, Aloe Vera
and Purple Shamrock, and Rex Begonia's Width quote.

The ten fields nulled on audit stay null: Peace Lily's four sizes (genus-level Clemson line), Rubber Plant is_edible
(sap warning missing; fruit "barely edible"), Persian Cyclamen is_edible (Poison Part stems missing; RHS "not to be
eaten"), Poinsettia's spread (outdoor figure) and Rex Begonia's height (group figure). Rubber Plant and Persian
Cyclamen would land null under standing rule 2 anyway.

## Records the coordinator asked to settle

- Sago Palm: is_edible null, the FR316 citation dropped. The researcher's two edibility lines became one line with the
  pages' words: FR316's famine line and "powerful neurotoxin that can cause paralysis or even death if it is not
  prepared properly", NC State's Edibility field ("The pith contains edible starch ... carefully washed to remove the
  toxins"), NC State's high-severity poison fields (cycasin; "Ingestion of any part of this plant may cause permanent
  internal damage or death.") and RHS's "Harmful if eaten; skin irritant." / "TOXIC to pets (dogs, cats)".
- Aloe Vera: is_edible null, citation dropped. The unknowns line quotes both halves of the Edibility field: "Causes low
  toxicity if eaten." and "Used medicinally and in drinks when properly prepared." The Poison-fields line stays, with
  its "required alongside is_edible=true" lead removed.
- Purple Shamrock: the page names toxicity ("All parts of the plant have toxic potential ...", "Soluble calcium
  oxylates", #problem for dogs/horses/cats, #poisonous), so is_edible is null with an unknowns line carrying the
  Edibility sentence and that text. Citation dropped.
- Monstera: stays true. The unknowns now carry every toxic part (Poison Part lists every part, fruit included; the
  note's "i.e. unripe fruit" gloss is not on the page and was corrected), the ripeness condition ("Only ripe fruits are
  edible" and the Fruit Description's "the fruit is ripe once the scale covering it falls off naturally ... Rarely
  produces fruit as a houseplant."), the allergy text ("Some people are allergic.") and Clemson's "All parts of
  monsteras and pothos also contain calcium oxalate crystals, and are toxic to pets and children."
- Voodoo Lily: stays true. Added the full Edibility field ("... Can be toxic if eaten raw."), Poison Part (Leaves,
  Roots), the toxic principle, #poisonous, and RHS's "Harmful if eaten; skin/eye irritant" for people and pets, which
  disagrees with NC State's "Causes Contact Dermatitis: No". Neither page has allergy text. The raw condition and the
  rheumatism/gout/kidney-stone caution were already there.
- Rubber Plant attracts_pollinators false: stands. The quote checks verbatim on the cached page: "Because the flowers
  require a particular species of fig wasp to pollinate them, the rubber plant does not produce highly colorful or
  fragrant flowers to attract other pollinators."

## Rules re-checked

- Climbers take no size: Heart Leaf Philodendron, Monstera, Pothos, Wax Plant, Arrowhead Plant and Mini Monstera all
  carry none. String of Pearls (trailing, not climbing) would keep a size but has no data. Spanish Moss hangs and does
  not climb, so it keeps NC State's 10-36 in by 6-24 in.
- Houseplant sizes (all 39 species are is_houseplant true). Every size that lands is an indoor or container figure, or
  a figure of 10 ft or under:
  - Indoor figures: Fiddle Leaf Fig ("As a houseplant, it will grow 2 to 10 feet tall"), Rubber Plant ("When grown
    indoors ... usually kept to 2 to 10 feet"), Majesty Palm ("As an indoor plant reaching 5 to 10 feet"), Poinsettia
    ("typically grown as a potted plant, and it rarely exceeds 2 to 3 feet"), Indian Azalea (RHS Azaleas Indoors, 45-60
    cm) and Lemon (UMD, "3- to-6-foot tall houseplants").
  - Container or under-glass figures: Sago Palm, Voodoo Lily and Lemon's spread (RHS, 1-1.5 m).
  - The rest are published figures well under 120 in.
  - Outdoor-only figures over 120 in stay null: Oleander, Yucca Cane, and the spreads of Rubber Plant, Fiddle Leaf Fig
    and Majesty Palm. Nothing was nulled at landing under this rule.
- is_edible true: all six are real foods with their conditions in unknowns. Monstera (ripe fruit only; every part
  listed as a poison part), Pepper (fruit; Longum Group capsaicin record; three ornamental cultivars "not edible",
  added), Cockscomb (leaves and young shoots cooked; "picked young"), Lemon (fruit; peel and plant material cause
  problems), Yucca Cane (flowers; saponins in leaves and roots; RHS skin allergen, added), Voodoo Lily (cooked corm
  only). No toxicity sentence is cited for a true.
- is_edible false: all 13 rest on a page's own poison or not-to-be-eaten statement, the same standard earlier chunks
  landed (Chinese Evergreen, Pothos, ZZ Plant, Annual Geranium, Vinca, Indian Azalea, Oleander, Fiddle Leaf Fig,
  Poinsettia, Arrowhead Plant, Kalanchoe, Rex Begonia, Queen of Hearts).
- attracts_pollinators true: all 13 name bees, butterflies, hummingbirds, moths or pollinators (Pepper's "May attract
  masked bees." included). None rests on birds eating seed.

## Unknowns corrected or added at landing

Corrections are marked "corrected at landing"; added lines say "noted at landing, verified against the cached copy".
Every page quotation in them was read on the cached page.

- Chinese Evergreen: the size lines now explain the nulling; the "all three pages fetched ok" line was corrected.
- Monstera, Voodoo Lily, Sago Palm, Aloe Vera, Purple Shamrock: as above.
- Pothos: the two Clemson lines were reversed (the how-to-grow page is readable and says "All parts of a pothos are
  mildly toxic if ingested."). Added NC State's description, "It grows only 6 to 8 feet as a horizontal groundcover",
  which disagrees with its 6-8 in Dimensions height.
- Pepper: added the three "Ornamental, not edible" cultivars ('Aurora', 'Candelabra', 'Chilly Chili'); the Clemson
  fetch line was corrected.
- Annual Geranium: EDIS FP459 is readable and is the cultivar 'Orange Appeal' (1 to 2 feet); the Clemson
  growing-geraniums-indoors page the researcher said was read is cached as http-403.
- Vinca: the Clemson annual-vinca figures the researcher quoted cannot be verified (cached http-403).
- Indian Azalea: the RHS species page does carry "Harmful if eaten." for people and pets, which the researcher's
  search missed; the fetch line was corrected.
- Oleander, Spanish Moss, Arrowhead Plant, Impatiens: pages the researcher reported refused are cached ok now
  (Oleander's Clemson warning and EP244's "herbaceous vine" quoted).
- Rubber Plant: the two lines written for is_edible true now say it is null, quote the fruit's "barely edible", and
  add Clemson's "The sticky white sap may irritate skin or the stomach if eaten."
- Persian Cyclamen: the true-framed lines now say null; Poison Part (Roots, Stems) and RHS's "Ornamental bulbs, not
  to be eaten" were added; "#problem for children" is in the Problems field, not the tags.
- Poinsettia: the stale spread line now says both ends were nulled on audit; the RHS poinsettia page is a genus guide
  that lists E. pulcherrima itself at 0.1–0.5 m, not a genus-wide range.
- Majesty Palm: NC State's Ethnobotany field says "In Madagascar, the palm heart is eaten by local people."; the note
  had said no page mentions eating. It stays null (native-range folk use; a landing does not set a value).
- Yucca Cane: RHS's "Skin allergen" and pets warning added; the two RHS pages are separate pages, not a redirect.
- Queen of Hearts: Poison Part is Flowers, Fruits, Leaves and Sap/Juice; "Available Space To Plant: 12 inches-3 feet"
  is a spacing field, not a size.
- Cast Iron Plant, Fiddle Leaf Fig: their Clemson readings are flagged as unverifiable (cached http-403); Fiddle Leaf
  Fig also notes "pollinated by fig wasps" / "Houseplants rarely bloom."
- Heart Leaf Philodendron and Spider Plant: the review lines above.

## verify_quotes, per touched file

`VQ_CACHE_ONLY=1 .venv/bin/python scripts/catalog/verify_quotes.py <file>`, after the merge (HEAD numbers in brackets):

- b1-foliage-core: 69 hit, 0 MISS, 0 inconclusive, 7 skipped (59 / 0 / 0 / 7)
- b11-veg-round4: 82 hit, 0 MISS, 0 inconclusive, 27 skipped (78 / 0 / 0 / 27)
- b13-annual-flowers1: 100 hit, 1 MISS, 0 inconclusive, 24 skipped (94 / 1 / 0 / 24)
- b14-annual-flowers2: 107 hit, 1 MISS, 0 inconclusive, 44 skipped (100 / 1 / 0 / 44)
- b15-perennials1: 99 hit, 0 MISS, 0 inconclusive, 27 skipped (95 / 0 / 0 / 27)
- b19-toxic-ornamentals: 123 hit, 0 MISS, 0 inconclusive, 31 skipped (116 / 0 / 0 / 31)
- b2-figs-and-succulents: 52 hit, 3 MISS, 0 inconclusive, 30 skipped (41 / 3 / 0 / 30)
- b20-common-ornamentals: 110 hit, 1 MISS, 0 inconclusive, 22 skipped (99 / 1 / 0 / 22)
- b21-houseplant-gaps: 119 hit, 1 MISS, 0 inconclusive, 23 skipped (103 / 1 / 0 / 23)
- b22-aroid-genus-gaps: 76 hit, 0 MISS, 0 inconclusive, 24 skipped (71 / 0 / 0 / 24)

Hits rose by exactly the 81 new citations. No new-field citation is a MISS, SKIP or INCONCLUSIVE, and every MISS and
SKIP line is identical to HEAD's. No pre-existing SKIP names a backfill field, so commit_backfill's untested check will
not trip on them. The seven MISS lines predate this landing and name none of the six fields:

- b13 Coleus is_houseplant (EDIS fp136 "Coleus may be used as a potted plant indoors ...").
- b14 Common Morning Glory common_name ("Ipomoea purpurea (Common Morning Glory, Japanese Morning Glory)").
- b2 Aloe Vera accepted name (the "previously known as ..." synonym list).
- b2 String of Pearls and Dragon Tree soil_ph_max (NC State soil pH tag quotes).
- b20 Lemon common_name ("Common Name(s): Lemon Scientific Name: Citrus x limon", labels glued to values).
- b21 Scarlet Star chill_damage_f (an RHS " ... " hardiness composite).

## Tests

- `tests/test_tranche_invariants.py` passes on its own: 3,880 passed.
- The combined run with `test_claim_ingest.py` gave 3,886 passed and 1 failed, the expected count assert
  `assert 6393 == 6269`. HEAD already includes chunks 1 and 2, and the only uncommitted verified files are this
  chunk's ten, so the +124 is exactly this chunk.
- `tests/test_claim_ingest.py` was not edited.

## For a person to decide

- Rex Begonia's spread was nulled at landing against the auditor's keep (see above). Reverse by restoring the two
  values and the Width citation from `r4c3/orig/` if a group-level figure is acceptable for the species record.
- Lemon's height (36-72 in) comes from UMD's statement about dwarf citrus in general ("Many dwarf citrus varieties
  ranging from lemons and limes to mandarins and kumquats ... can be maintained as 3- to-6-foot tall houseplants").
  That is a group-level line like the Peace Lily one the audit nulled, but it is the only indoor height on any page
  and the auditor passed it, so it lands. Its spread is RHS's container figure (1-1.5 m), while RHS's own container
  height (2.5-4 m, up to 157 in) was not used.
- Indian Azalea's is_edible false rests on UF/IFAS EP648's genus-level Rhododendron statement (ask.ifas.ufl.edu, cached
  ok). RHS's species page says "Harmful if eaten." and would be a sturdier citation in a follow-up.
- Pothos keeps a corroborating Clemson citation (cached ok, HITs) beside its two NC State citations. The value does
  not rest on Clemson, but if that cache entry is ever lost, commit_backfill will call the citation untested.
- Needs re-research (nothing written): Dragon Tree (its NC State page is readable now; the auditor found "as
  houseplants, they grow to 6 feet" and a poison section), String of Pearls (NC State page now cached, never read),
  Peace Lily (NC State's species line "up to 12 inches tall" would give a height maximum), Heart Leaf Philodendron and
  Mini Monstera (NC State poison sections could support is_edible false).
- Oleander: RHS's 1.5-2.5 m by 1-1.5 m may be an under-glass figure a re-research could land; this landing did not
  add it.
- Sizes disclosed but not changed: Spider Plant (Clemson's houseplant figure is wider, 2 to 2½ feet, and cannot be the
  sole support), Coleus (RHS spread 0.1-0.5 m vs NC State 6-36 in), Annual Geranium (height NC State, spread RHS, which
  disagree on height), Sago Palm (NC State 3-10 ft; RHS container figure used; RHS rounded to 39/59 in whole inches).
- Poinsettia: UF/IFAS says "Poinsettias are not poisonous", NC State says "Toxic if ingested."; is_edible false
  stands on NC State and the conflict is in unknowns.

Scratch work is in the session scratchpad under `r4c3/`: the untouched workflow output and batch files (`orig/`), the
repair script, the cache-only qc guard, the citation audit, the merge plan, and verify_quotes output before and after.
