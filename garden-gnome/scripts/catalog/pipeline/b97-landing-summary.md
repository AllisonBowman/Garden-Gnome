# b97 landing: eight mixed species (2026-10-03)

The landed file is `app/data/verified/b97-mixed.json`. It is not committed. The repair script is `b97_repair.py` and
the scratch copy is `b97_landed_records.json`, both in this directory. All 8 species landed, none were withheld, and 0
were unverified.

## Checks
- `b97_repair.py`: generic_passes clean.
- `land_check.py b97_landed_records.json` ends `=== problems === none`. toxic_to_pets: only Dragon Fruit carries a
  value, false, on NC State's tag run `#non-toxic for cats #non-toxic for horses #non-toxic for dogs`. The other seven
  are null: no admissible page names cats or dogs (Persian Lime's contact dermatitis and RHS fruit-skin warning name no
  animal).
- `verify_quotes.py app/data/verified/b97-mixed.json`: `197 hit, 0 MISS, 0 inconclusive, 0 skipped (pdf/http/error)`.
  No MoBot or Clemson citation is landed, so nothing SKIPs.
- Stricter check (scratchpad `b97land/chk.py`, verify_quotes' own extractor with each text node kept apart): every
  newline-stacked quote is a run of consecutive rendered nodes, bounded by its own label and the next one. Six
  single-line quotes span inline elements, each confirmed in the raw HTML to sit in one block: the Thunbergia
  no-relation sentence (inline `<a><em>Rudbeckia hirta</em></a>`), the RHS Synonyms lines for Chaenostoma and Citrus
  (one `<p>` with `<i>`), the Helianthus often-confused `<dt>` (with `<em>`), and the two dragon fruit tag runs (inline
  `<a class="badge">` elements in one `<dd class="tags">`).
- `pytest tests/test_tranche_invariants.py tests/test_claim_ingest.py`: 4312 passed, 1 failed, `assert 7745 == 7582`.
  b97 adds exactly 75 claims (8 records, none unsupported by `claims_from_record`), so b97 alone on the committed 7,582
  baseline (b95 was committed during this landing) makes 7,657. The other 88 are the uncommitted
  `b96-mixed.json` beside it. The run before b95's commit printed `assert 7745 == 7491` (b95 91 + b96 88 + b97 75).
- Page cache: RHS 143110 (Citrus × latifolia (F/S), cited) and RHS 48650 (Citrus × latifolia 'Tahiti', read to confirm
  its Name Status Synonym, not cited) were fetched through qc.py's normal path with www.rhs.org.uk allowed. MoBot's
  California poppy page (kempercode=b753) was tried once with the host allowed: ConnectError, so nothing was cached.
  Nothing in the cache was edited, moved or deleted. The one cited page that was not cached ok, Clemson's Mexican
  sunflower article (cached http-403), is no longer cited.

## finish() table
```
Black-Eyed Susan Vine      acc=Thunbergia alata house=True toxic=None sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=24 unk=15
California Poppy           acc=Eschscholzia californica house=False toxic=None sun=['full_sun'] drain=None water=None ph=None/None base=garden_bed cites=18 unk=12
Bacopa                     acc=Chaenostoma cordatum house=False toxic=None sun=['part_shade'] drain=moderate water=None ph=None/None base=None cites=18 unk=13
Mexican Sunflower          acc=Tithonia rotundifolia house=False toxic=None sun=['full_sun'] drain=None water=None ph=None/None base=garden_bed cites=13 unk=13
Persian Lime               acc=Citrus × latifolia house=True toxic=None sun=['full_sun'] drain=moderate water=None ph=6/None base=garden_bed cites=34 unk=11
Black Raspberry            acc=Rubus occidentalis house=False toxic=None sun=['full_sun', 'part_shade'] drain=None water=None ph=None/None base=garden_bed cites=28 unk=9
Jerusalem Artichoke        acc=Helianthus tuberosus house=False toxic=None sun=['full_sun', 'part_sun', 'part_shade'] drain=None water=keep_moist ph=None/None base=garden_bed cites=29 unk=11
Dragon Fruit               acc=Selenicereus undatus house=True toxic=False sun=['full_sun'] drain=moderate water=None ph=None/None base=cactus_succulent cites=33 unk=14
```
Grown-schema fields as landed: Black-Eyed Susan Vine edible null, pollinators true, climbs true, height 36-96 (reach),
spread 36-72; California Poppy edible true, pollinators true, 12-24 / 12-24; Bacopa edible null, pollinators null,
3-6 / 12-24; Mexican Sunflower edible null, pollinators true, 36-72 / 24-36; Persian Lime edible true, pollinators
true, size null; Black Raspberry edible true, pollinators true, 36-72 / 48-96; Jerusalem Artichoke edible true,
pollinators true, 72-120 / 36-60; Dragon Fruit edible true, pollinators true, climbs true, size null.

## The standing rules, as applied
- Rule 1 (shared cache): see Checks. Only normal-path fetches of two RHS pages were added.
- Rule 2 (edibility). The four real foods stay true with each page's conditions in unknowns: Persian Lime (fruit and
  juice; the hazards on the pages are skin hazards, NC State's contact dermatitis and RHS's "Fruit harmful to skin with
  sunlight/skin allergen ... Wear gloves"), Black Raspberry (fruit raw or cooked with no condition; young shoots peeled
  and harvested tender; tea from leaves or root bark), Jerusalem Artichoke (tubers only; NC State's Flower Value
  "Edible" tag disclosed, no page says how or that flowers are eaten), Dragon Fruit (fruit and flowers; possible
  allergy and interaction with blood-pressure or anti-hyperglycemic medication; gloves for the spines). California
  Poppy stays true on NC State's Edibility field "The leaves and stems can be eaten.", scoped to leaves and stems; no
  page calls it harmful or not to be eaten (RHS has no Potentially harmful row). No is_edible citation quotes a
  toxicity sentence; each record's first is_edible citation is its food statement.
- Rule 3 (size). Black-Eyed Susan Vine and Dragon Fruit land `climbs: true`, each cited to its NC State Climbing
  Method / Habit/Form fields and prose (and RHS's "perennial twining climber" for the vine). The vine's NC State
  Height 3-8 ft lands as reach; it is a houseplant (#houseplant, #interiorscape) but no page gives an indoor figure
  and 36-96 / 36-72 are under 120 in, so they stand. Persian Lime and Dragon Fruit are houseplants whose only figures
  are outdoor statures over 120 in with no indoor or container figure (Persian Lime NC State 8-20 ft by 8-20 ft, UF/IFAS
  about 20 ft, RHS 2.5-4 m by 1-1.5 m; Dragon Fruit NC State 8-20 ft by 3-10 ft with 33-ft stems, RHS 2.5-4 m by
  2.5-4 m), so all four size fields of each are null (the b90 ruling: when the outdoor block's height or spread exceeds
  120 in, all four stay null), their size citations dropped and the figures quoted in unknowns. No RHS figure was
  treated as indoor: none is tied to indoor or container growing by its own sentence (b90's Kentia Palm test).
- Rule 4 (Clemson/MoBot only on a cache HIT). Mexican Sunflower's Clemson citation (cached http-403) was dropped;
  common_name stands on NC State's description, and the audit's substitute, also Clemson, could not be used. No MoBot
  citation was added. The audit's MoBot readings went into unknowns only, marked as browser reads: California Poppy's
  "Sharp soil drainage is essential." (so its soil_drainage stays null rather than fast), and the name, size, sun,
  water and culture rows the auditor read for Black-Eyed Susan Vine, California Poppy, Mexican Sunflower and
  Jerusalem Artichoke. The MoBot sentences in the audit's corrected name_note wording for California Poppy and
  Jerusalem Artichoke were left out of name_note.

## Values changed or restored
- Black-Eyed Susan Vine: name_note restored in the audit's wording, with the stacked Common Name(s) list cited.
  climbs absent -> true. Claim labels that called the <title> parenthetical a heading relabelled; the no-relation
  quote extended to carry "(Rudbeckia hirta)" (page spelling "Dispite" kept); the cropped soil_base sentence completed
  through "hanging basket"; the RHS Cultivation sentence no longer labelled as the Position field; RHS Correct paired
  under CORR. Added: NC State description opener for common_name, RHS's full Suggested planting locations list.
  unknowns 0 and 10 replaced (no "other page unreadable"; size line rewritten for reach and the houseplant rule).
- California Poppy: name_note restored in the audit's wording without its MoBot sentence; RHS subtitle, Other common
  names and the stacked NC State list cited. soil_ph_min stays null (removed on audit; RHS pH "Acid or Alkaline or
  Neutral"); its citation became a "soil pH disclosure" of both stacked NC State values beside RHS's pH field.
  attracts_pollinators null -> true on RHS's "Plants for pollinators" badge. is_houseplant null -> false (Plant Type
  Annual / Wildflower, zones 6a-10b). RHS page title + Correct added for the accepted name. toxicity_detail gains one
  sentence: RHS has no Potentially harmful or other toxicity entry. unknowns 0, 1, 2, 4, 5, 7, 9 replaced; size and
  "nothing from Corn Poppy / Oriental Poppy" lines added.
- Bacopa: name_note restored in the audit's wording plus two cited sentences (Bacopa leads NC State's title
  parenthetical and alphabetized list; the description opens "Ornamental bacopa"; RHS's dedicated page gives no common
  name and lists "Bacopa misapplied, Sutera cordata" as Synonyms). is_houseplant null -> false ("In North Carolina, it
  is best grown as an annual in hanging baskets or containers or as a ground cover along borders."; zones 9a-11b). RHS
  page title + Correct added. The water-hyssop label regains "somewhat"; "still" dropped from the phonetic label.
  unknowns 0, 2, 4, 5 replaced; a "nothing from the Phlox records" line added.
- Mexican Sunflower: Clemson citation dropped (above). soil_base relabelled and the back-of-border sentence cited.
  is_houseplant null -> false (NC State back-of-border sentence; RHS's five garden-type planting locations). RHS
  Correct under CORR. unknowns 0 and 6 replaced in the audit's wording, the size line's "looks like a data error"
  replaced with the figures, and a Clemson line added (http-403; its readings in the notes are browser reads).
- Persian Lime: name_note restored in the audit's wording (RHS 143110 page title, subtitle, Correct, Other common
  names and Synonyms; UF/IFAS CH093 Common Names; the stacked NC State list), plus one sentence on why the bare Lime is
  not the landed name (it would not distinguish the plant from the landed Key Lime). toxicity_detail restored in the
  audit's wording with RHS's Potentially harmful field and #edible fruits cited. chill_damage_f null -> 28 on UF/IFAS
  CH093: "In general, damage to 'Tahiti' lime leaves occurs at temperatures below 28°F (-2°C); wood damage occurs below
  about 26°F (-3°C), and severe damage or death occurs below 24°F (-4°C)." (the same paragraph ranks it hardier than
  Key lime, so it is not parent bleed). Size 96-240 / 96-240 -> null (rule 3). is_houseplant's first citation was the
  overwintering sentence; it is now the Plant Type field "Edible / Houseplant / Perennial / Shrub / Tree".
  soil_drainage's first citation was a poor-drainage sentence; it is now the Soil Drainage field "Good Drainage /
  Moist". The "hybrid tree" accepted-name quote now carries "hybrid tree"; RHS's H1 "Citrus × latifolia (F/S)" and
  Correct added. UF/IFAS bee-visit sentence added for attracts_pollinators. unknowns 0, 2, 3, 5, 6, 9 replaced.
- Black Raspberry: name_note and toxicity_detail restored in the audit's wording, with the stacked list and the
  seven verified toxicity_detail citations (tea, fruit quality, Edibility field, Plant Type, #edible fruits, Appendage,
  Stem Description). The is_edible quote ends at the first of the page's doubled period. attracts_pollinators: the
  Attracts field "Bees / Butterflies / Pollinators / Small Mammals / Songbirds" now leads, and the Wildlife Value quote
  is labelled as that field. RHS Correct under CORR. unknowns 2, 4, 7 replaced (7 adds that the arching canes are not
  described as climbing, so climbs stays null).
- Jerusalem Artichoke: name_note restored in the audit's wording without its MoBot clause; the stacked list, RHS
  subtitle and RHS Other common names cited. soil_ph_min stays null (removed on audit); its citation became a pH
  disclosure beside RHS's "Acid or Alkaline or Neutral". The second is_edible quote extended to the two-sentence
  "Fresh Jerusalem artichoke tubers are edible ..." run. is_houseplant null -> false (Plant Type, zones 3a-9b). RHS
  page title + Correct added. attracts_pollinators: the Attracts field leads and the Play Value quote is the whole
  three-value field, not one value. unknowns 0, 2, 4, 5, 6, 8, 9 replaced (MoBot parts marked as browser reads).
- Dragon Fruit: name_note and toxicity_detail restored in the audit's wording; RHS 8965's H1 "Hylocereus undatus (F)",
  Correct and subtitle "dragon fruit" cited; Previously known as quoted whole (three names); the four-name slice of
  the title parenthetical replaced by the whole fourteen-name stacked list; toxicity_detail gains "Spines/Thorns", the
  five Plant Type values and RHS's "If pollinated, these are followed by reddish pink edible fruits". humidity_need,
  water_regime and water_dry_down_target stay null (removed on audit: NC State moderate humidity and near-complete
  dry-down vs RHS high humidity and "Water freely when in growth ... keep just moist in winter"); their citations
  became humidity and watering disclosures beside RHS's sentences, and the duplicate dry-down citation was dropped.
  fertilize_strength null -> half on RHS's "apply a half-strength liquid feed monthly" (species text: RHS's Epiphyllum
  oxypetalum page prescribes a different feed). climbs absent -> true. Size 96-240 / 36-120 -> null (rule 3). The Soil
  Drainage run newline-stacked; attracts_pollinators now leads with the Attracts field "Bees / Moths" and quotes the
  whole six-value Play Value field. unknowns 0, 2, 4-9 replaced; humidity and Orchid Cactus name-overlap lines added.

## Common names and accepted names
- All eight researched names were kept; none collides with a landed common_name or with b95, b96 or b98, and
  covered.py reports every binomial clean (Hylocereus undatus and Sutera cordata too).
  - Black-Eyed Susan Vine: NC State's title lead and list; RHS says "black-eyed Susan", the name b15's Rudbeckia hirta
    carries, so "Vine" is kept.
  - California Poppy: RHS's lead; NC State's alphabetized list opens with Bottlestopper.
  - Bacopa: NC State's title and list lead (its description opens "Ornamental bacopa"); RHS gives no common name.
  - Mexican Sunflower: NC State's only name and RHS's lead.
  - Persian Lime: RHS's lead; NC State and its prose lead with the bare umbrella Lime; UF/IFAS leads with 'Tahiti'
    lime.
  - Black Raspberry: NC State's description and RHS's lead; NC State's list opens with Blackberry (b12, b45).
  - Jerusalem Artichoke: NC State's description and RHS's lead; NC State's list opens with Earth Apple.
  - Dragon Fruit: NC State's description and RHS's subtitle; NC State's list opens with Belle-Of-The-Night.
- Persian Lime keeps the spaced U+00D7 (NC State "Citrus x latifolia", RHS "Citrus × latifolia (F/S)", Correct).
- Dragon Fruit follows NC State's current Selenicereus undatus, as the batch brief and the audit's corrected
  name_note say; RHS files it as Hylocereus undatus (F) with Name Status Correct. Disclosed in name_note.

## Could not do / disclosed
- MoBot refuses this machine (ConnectError again at landing), so no MoBot page could be cached or cited; every MoBot
  reading in the records is the auditor's browser read, marked as such in unknowns.
- Clemson's Mexican sunflower article is cached as http-403; its readings stay in unknowns as browser reads.

## Decisions for the owner
1. Dragon Fruit size. It climbs (reach rule) and it is a houseplant; under the standing instruction that the houseplant
   rule applies to every is_houseplant species, its outdoor 96-240 in reach and 36-120 in spread are null, so the app
   will show a climber with no stated reach. Under the reach rule alone it would land 96-240 / 36-120.
2. Dragon Fruit's accepted name follows NC State (Selenicereus undatus) over RHS's Correct Hylocereus undatus, the same
   choice and the same consequence as b94's Dasiphora: covered.py and the duplicate-species test key on given and
   accepted names only, so a future "Hylocereus undatus" candidate would not be caught as a duplicate.
3. Values added at landing from the audit's verified text, none in the research record: Persian Lime chill_damage_f 28
   (UF/IFAS leaf-damage onset), California Poppy attracts_pollinators true (RHS badge), Dragon Fruit fertilize_strength
   half (RHS). Each is easy to revert in `b97_repair.py`.
4. California Poppy is_edible true rests on NC State's "The leaves and stems can be eaten." for an ornamental wildflower;
   it matches the corpus (English Daisy, Primrose, Lilac) and rule 2's letter, but the app shows it as "grown to eat".
5. California Poppy soil_drainage is null only because MoBot's "Sharp soil drainage is essential." cannot be checked
   from here; with MoBot reachable it would land fast.

NORMALIZATION: written.
