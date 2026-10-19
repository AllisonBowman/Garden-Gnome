# b95 landing: bulbs, tubers, tender patio and Mediterranean plants (2026-10-03)

The landed file is `app/data/verified/b95-bulbs-patio.json`. It is not committed. The repair script is `b95_repair.py` and
the scratch copy is `b95_landed_records.json`, both in this directory. All 8 species landed, none were withheld, and
0 were unverified.

## Checks
- `b95_repair.py`: generic_passes held on the first run.
- `land_check.py b95_landed_records.json` ends `=== problems === none`. Every toxic_to_pets value (six true, two null)
  rests on a quote naming cats and dogs: NC State Problems values on five records and Cabbage Tree's own Poison Symptoms
  sentence ("Poisonous to dogs and cats. ...").
- `verify_quotes.py app/data/verified/b95-bulbs-patio.json`: `271 hit, 0 MISS, 0 inconclusive, 0 skipped (pdf/http/error)`.
- Rendered-element check (the b91 lander's chk.py, copied to this session's scratchpad, run cache-only): 0 flagged. Every
  quoted line sits in one rendered element and every stacked quote is consecutive elements.
- `batch_claims.py`: 8 records, 91 claims, nothing unsupported.
- pytest `test_tranche_invariants.py` + `test_claim_ingest.py`: only the count test fails.
  - Latest run, after b98 was committed at 7,491: 4312 passed, `assert 7745 == 7491`. The 254 extra claims are b95's
    91 plus 88 from b96 and 75 from b97, both uncommitted files from other agents.
  - Earlier run, before b98 was committed: `assert 7582 == 7416`, which was b95's 91 plus 75 from b98.
  - With b95 alone over the current baseline, the total is 7582.
- Page cache: every cited page was already warm except RHS 154520 (Iris × hollandica) and RHS 829 (Allium giganteum),
  both cited by the audit. I fetched each once through qc.py with www.rhs.org.uk allowed. I also requested NC State's
  `/plants/narcissus-papyraceus/` once, to settle the naming question; it returns 404, and that status is now cached.
  Nothing was deleted or edited.

## finish() table
```
Bunchflower Daffodil       acc=Narcissus tazetta house=False toxic=True sun=['full_sun', 'part_shade'] drain=moderate water=keep_moist ph=None/None base=garden_bed cites=36 unk=11
Cabbage Tree               acc=Cordyline australis house=True toxic=True sun=['full_sun', 'part_shade'] drain=moderate water=keep_moist ph=None/None base=garden_bed cites=36 unk=13
Persian Buttercup          acc=Ranunculus asiaticus house=False toxic=True sun=['full_sun'] drain=moderate water=None ph=None/None base=garden_bed cites=33 unk=12
Poppy Anemone              acc=Anemone coronaria house=False toxic=None sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=29 unk=11
Dutch Iris                 acc=Iris × hollandica house=False toxic=True sun=['full_sun'] drain=moderate water=keep_moist ph=None/None base=garden_bed cites=33 unk=12
Giant Ornamental Onion     acc=Allium giganteum house=False toxic=True sun=['full_sun'] drain=moderate water=keep_moist ph=None/None base=garden_bed cites=35 unk=10
Calamondin                 acc=Citrus × microcarpa house=True toxic=None sun=['full_sun'] drain=moderate water=None ph=None/8 base=None cites=35 unk=10
Blue Passionflower         acc=Passiflora caerulea house=False toxic=True sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=None cites=34 unk=10
```

## Fields nulled at landing
- Cabbage Tree is_edible: true -> null. It applies the edibility rule. NC State's Edibility field says "The stems and
  fleshy rhizomes of the tree are high in sugar and used as sweetener. The leaves are eaten raw." The same page lists
  Poison Part Fruits and Leaves, says "Poisonous to dogs and cats", and states "The plant is toxic for dogs and cats."
  The food statement stays in toxicity_detail and the reason is in unknowns.
- Blue Passionflower is_edible: true -> null. NC State says "The fruit, while edible, tastes bland." and adds a tea
  remark that names no part. RHS says "Fruits are edible but not particularly tasty". Neither says the fruit is grown
  or used for food. The plant's leaves and stems are poisonous: Poison Severity Medium, cyanogenic glycosides.
- Cabbage Tree mature_height_in_min: 72 -> null, and max 360 -> 180 (size rule, houseplant). The record is
  houseplant-framed: "grown indoors year-round as a houseplant". NC State gives a container height, "reach a height
  of 15 feet", so that lands as the max. The outdoor 6-30 ft and 30-60 ft figures are quoted in unknowns.
- Calamondin mature_height_in 120-240 -> null (same rule). It is a houseplant: "best grown in a container and
  overwintered indoors". No page gives an indoor or container height. NC State's outdoor Height of 10-20 ft and RHS's
  2.5-4 m are quoted in unknowns. The width, 72-120 in, stays.
- Calamondin outdoor_sun_exposure: ['full_sun','part_shade'] -> ['full_sun'], following the audit's flag. RHS's lone
  Partial shade is excluded by NC State's full-sun-only Light field, as Key Lime was in b89. The RHS citation was
  relabelled as an unlanded counterpoint.

## Values set or restored (each rests on page text verified in the cache)
- Bunchflower Daffodil (Narcissus tazetta)
  - name_note restored in the audit's wording, with all six of its citations. I added NC State's "Corona is yellow" and
    RHS's papyraceus "pure white flowers" contrast.
  - toxicity_detail restored in the audit's wording, including RHS's nominate-subspecies Potentially harmful row
    (skin irritant, gloves, "Pets (dogs, cats, tortoises)"). It is disclosed next to NC State's Causes Contact
    Dermatitis: No, as a disagreement, not as the record's own warning. Added citations for the Poison Severity run,
    Contact Dermatitis, the subspecies row and its page title.
  - Added RHS's Name Status (CORR) and H1 for the accepted name.
  - is_houseplant null -> false, cited with Plant Type, zones 7a-10b and Landscape Location Container/Lawn/Walkways.
- Cabbage Tree
  - name_note restored in the audit's wording. Its reason sentence now also names the NC State prose opener, and the
    stacked Common Name(s) list was added.
  - toxicity_detail gains "Causes Contact Dermatitis: No". The banner is described as unscoped.
- Persian Buttercup
  - name_note restored in the audit's wording, with the stacked list cited.
  - RHS's unscoped "Pets:" line was moved off toxic_to_pets. It is quoted as the full row under toxicity_detail, and
    the toxicity_detail RHS sentence was completed with it.
  - is_houseplant null -> false (Plant Type, zones 8a-10b, Landscape Location).
  - soil_base gains NC State's in-ground planting sentence as its stored evidence.
- Poppy Anemone
  - is_houseplant null -> false, using the audit's three citations and its replacement entry.
  - The stacked Common Name(s) list and the Description opener were added.
  - The two-part confusion-module citation was merged into its stacked form.
- Dutch Iris
  - toxicity_detail rebuilt. The researched text is not preserved in the post-audit records. The audit said it was
    verbatim-accurate, so it was rebuilt from the same page, with the audit's replacement closing on RHS's
    Potentially harmful row.
  - is_edible null -> false, as the audit asked. It rests on NC State's "CAUSES ONLY LOW TOXICITY IF EATEN" and RHS's
    "Harmful if eaten."
  - Size null -> RHS's dedicated-page Max Height 0.5-1 m and Max Spread 0.1-0.5 m (19.7-39.4 and 3.9-19.7 in). NC
    State has no Dimensions block.
  - New name_note: the names agree, RHS has Name Status Correct, and UGA's Field Report says "Iris hollandica" and
    "Iris x hollandica" are "not officially recognized". The hybrid's origin is cited from NC State and UGA.
  - is_houseplant null -> false.
- Giant Ornamental Onion
  - name_note restored in the audit's wording, with its three citations.
  - is_edible null -> false, as the audit asked: "Poisonous through ingestion. Symptoms may include: nausea, vomiting,
    and diarrhea." The quote is one rendered element, and its source CRLF renders as a space. African Blue Lily (b86)
    is the precedent.
  - toxicity_detail's last sentence was replaced as the audit asked.
  - RHS Moisture is now the stored soil_drainage evidence. The cropped "kept moist" quote was restored to its full
    sentence.
  - The Landscape Theme field was quoted whole. RHS's Plants for pollinators badge was added.
  - is_houseplant null -> false.
- Calamondin
  - The Soil pH quote was restored to its full two values.
  - Added: the stacked Common Name(s) list, NC State's Good Drainage + Moist, RHS's Conservatory Greenhouse type tag
    (is_houseplant), and "It can also be grown for its edible fruits" (is_edible).
  - is_edible stays true. The sour/acidic pulp and RHS's lemon/lime-only skin row are in unknowns.
- Blue Passionflower
  - name_note restored in the audit's wording, with the stacked list cited.
  - climbs = true (new key). It is cited to NC State's tendril sentence and RHS's "A large, vigorous evergreen climber
    to about 10m tall". The 120-480 in height is relabelled as its reach.
  - The whole Poison block was added as one label/value run.
  - is_houseplant null -> false.
- Citation repairs on every record (values unchanged):
  - NC State page banners were relabelled as unscoped and paired with the human-scoped `Poisonous to Humans:\nPoison
    Severity:\n...` run.
  - Single Problems picks were re-quoted as the whole field.
  - Bare RHS `Correct` quotes were relabelled CORR. Passionflower's label-glued "Name Status Correct" became `Correct`.
  - Passionflower's space-joined confusion module was re-quoted in its stacked form.
  - Cabbage Tree's ten-tag stack became one badge. The tags are inline badges in one row.
  - Passionflower's split RHS Position spans became the single card `Full sun, Partial shade`.
  - Cabbage Tree's container watering quote regained "If grown in a container,".

## Common names and accepted names
- Narcissus tazetta: Paperwhite Narcissus -> **Bunchflower Daffodil**.
  - The audit flagged the researched name, and the brief's naming rules decided it.
  - Bunchflower Daffodil leads NC State's alphabetized list and title parenthetical. RHS's dedicated N. tazetta (13)
    profile leads with bunch-flowered daffodil and carries no paper-white name.
  - RHS gives paper-white daffodil and paper-white narcissus to Narcissus papyraceus. RHS holds that as a separate
    species (Name Status Correct) and lists N. tazetta subsp. papyraceus as its synonym. That makes it a sibling's
    name, which the brief excludes.
  - The one-word "Paperwhite" is on neither page. Zenobia/Honeycup (b74) is the precedent.
  - The case the other way is disclosed in name_note and unknowns. NC State's description prose opens with "Paper White
    Narcissus", and the brief admits a prose opener as a lead (Siberian Iris kept that way in b91). NC State also has no
    papyraceus page (404).
  - No collision: grep finds no landed paperwhite or bunchflower name. Daffodil is N. pseudonarcissus.
- All other names are unchanged and none collides with the corpus: Cabbage Tree (NC State's prose lead; Cabbage Palm
  is Sabal palmetto's title name), Persian Buttercup, Poppy Anemone, Dutch Iris, Giant Ornamental Onion (RHS's "giant
  onion" disclosed), Calamondin and Blue Passionflower.
- No accepted-name change. Two hybrids keep the spaced U+00D7: Iris × hollandica and Citrus × microcarpa.

## Audit requests not done as written
- **MoBot.** Nothing rests on MoBot (standing rule 4; it is not in the cache).
  - Its audit-read content goes into unknowns, marked as audit-reported: Cabbage Tree's Common Name and size, Persian
    Buttercup's page, Poppy Anemone's page and its tuber-overwintering line.
  - The audit's MoBot sentence for Cabbage Tree's name_note was not added there.
- **Calamondin relabel.** The audit's relabel for the RHS Partial shade citation used "UK-calibrated", which is a
  banned claim phrase, and kept the outdoor_sun_exposure token. It now reads "sun counterpoint, not landed: ...". The
  replacement unknowns entry says RHS grows the plant under glass (Conservatory Greenhouse, H3) instead.
- **Dutch Iris tags.** The rebuilt toxicity_detail names all 13 tags in page order, as the audit says the researched
  text did. Only one badge is quoted as a citation, because the tags are inline badges in one row and a stacked run
  would misdescribe them.
- **Cabbage Tree size.** The audit's size wording kept the Dimensions height of 72-360 in. Standing rule 3 replaces
  it with the container figure. The new entry keeps the audit's two corrections: RHS's spread, not its height, is the
  larger figure, and NC State's "reach a height of 15 feet" is quoted without "about".

## Decisions for the owner
1. **Bunchflower Daffodil vs Paper White Narcissus** for Narcissus tazetta.
   - Both are defensible: the structured leads and RHS favor Bunchflower Daffodil, and US usage and NC State's prose
     favor Paper White.
   - Switching is a one-line change plus the name_note's last two sentences.
2. **Edibility nulls** on Cabbage Tree and Blue Passionflower under the "grown to eat" rule.
   - Both pages do call a part edible: Cabbage Tree's stems and rhizomes as sweetener and its leaves eaten raw;
     Passionflower's fruit, which is bland.
   - Cabbage Tree's own page lists Leaves as a poison part.
3. **Houseplant heights.**
   - Cabbage Tree's 180 in container height is a real NC State figure, but taller than a room.
   - Calamondin has no height at all, because no page gives an indoor size.
   - For comparison, Key Lime (b89, also houseplant-framed) carries NC State's outdoor 72-156 in Dimensions height.

NORMALIZATION string: written.
