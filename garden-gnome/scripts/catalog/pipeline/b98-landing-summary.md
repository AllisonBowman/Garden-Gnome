# b98 landing: seven mixed species (2026-10-03)

The landed file is `app/data/verified/b98-mixed.json`. It is not committed. The repair script is `b98_repair.py` and
the scratch copy is `b98_landed_records.json`, both in this directory. All 7 species landed, none were withheld, and
0 were unverified.

## Checks
- `b98_repair.py`: generic_passes holds. The script also asserts that `drop_audit` strips exactly the audit's own
  lines. That guard caught a real bug on the first run: rewritten unknowns lines that said "read on audit" were being
  silently stripped (Purple Leaf Sand Cherry lost 7 lines, Japanese Banana 1). They now say "read at audit".
- `land_check.py b98_landed_records.json` ends `=== problems === none`. Its toxic_to_pets dump has three trues, and
  every one rests on a quote naming cats and/or dogs:
  - Japanese Clematis: NC State's `Toxic to dogs, cats, horses` and its Problem for Cats and Problem for Dogs values.
  - Purple Leaf Sand Cherry: NC State's Problems field (Problem for Cats, Problem for Dogs, Problem for Horses).
  - Spanish Bluebell: RHS's `Pets (dogs, cats, rabbits): Harmful if eaten.`
- `verify_quotes.py app/data/verified/b98-mixed.json`: `216 hit, 0 MISS, 0 inconclusive, 0 skipped (pdf/http/error)`.
- Structure check (`chk.py`, from the b91 lander): 0 flagged. It checks that every citation HITs and that each quoted
  line sits in one rendered element, with stacked lines in consecutive elements.
- pytest `test_tranche_invariants.py` + `test_claim_ingest.py`: 4216 passed, 1 failed. The failure is the count test,
  `assert 7582 == 7416`. That +166 is b98's 75 claims plus 91 from another agent's `b95-bulbs-patio.json`, which
  landed in the tree meanwhile. `batch_claims.py` gives b98 7 records and 75 claims, with no unsupported field.
  Before the spread change below, b98 alone was 77 claims and the test read `assert 7493 == 7416`.
- Page cache: every cited page was warm except the three named below. I added one page, RHS's Lycoris aurea profile,
  through qc.py's normal fetch, to confirm an unknowns line the audit asked for. Nothing was deleted, moved or edited.

## finish() table
```
Carolina Jessamine         acc=Gelsemium sempervirens house=False toxic=None sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=34 unk=18
Japanese Clematis          acc=Clematis terniflora house=False toxic=True sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=38 unk=14
Purple Leaf Sand Cherry    acc=Prunus × cistena house=False toxic=True sun=['full_sun'] drain=moderate water=None ph=None/None base=garden_bed cites=19 unk=12
Japanese Euonymus          acc=Euonymus japonicus house=False toxic=None sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=29 unk=14
Spanish Bluebell           acc=Hyacinthoides hispanica house=False toxic=True sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=34 unk=14
Japanese Banana            acc=Musa basjoo house=False toxic=None sun=['full_sun', 'part_shade'] drain=moderate water=keep_moist ph=None/None base=None cites=23 unk=14
Red Spider Lily            acc=Lycoris radiata house=False toxic=None sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=39 unk=12
```
One pair was nulled at landing, on the coordinator's call: Carolina Jessamine's mature_spread_in_min/max (see
below). The audit removed seven fields, and all seven were restored with citations: name_note on three records and
toxicity_detail on four. It flagged an eighth, Japanese Banana's sun list, which was kept.

## Standing rule 4 (Clemson and MoBot)
- Uncached pages:
  - Missouri Botanical Garden refuses this machine (`error:ConnectError`), so no MoBot page is cached.
  - Clemson's Carolina jessamine factsheet is cached as `http-403`.
  - Clemson's other three pages (wood hyacinth, spider lilies, sweet autumn clematis) are cached, and every quote from
    them HITs, so they stay.
- 19 research citations dropped:
  - Carolina Jessamine: 5 Clemson and 5 MoBot.
  - Spanish Bluebell: 9 MoBot.
- Two values rested on those pages alone. Both were re-cited to text that HITs, with no value change:
  - Carolina Jessamine `soil_base` garden_bed: from Clemson's planting sentence to NC State's Landscape Location field,
    `Naturalized Area\nVertical Spaces\nWoodland`, which has no container entry.
  - Carolina Jessamine `is_edible` false: from MoBot to RHS's `Harmful if eaten. Wear gloves and other protective
    equipment when handling`.
- What MoBot and Clemson say is kept in unknowns, marked "read in a browser … not cited". It is never in a citation,
  name_note or toxicity_detail. This is the b91/b94 practice.
- No MoBot citation the audit proposed was added.

## Values changed or restored (each rests on page text verified in the cache)
- Carolina Jessamine
  - name_note restored in the audit's wording, without its Clemson and MoBot clauses.
    - Added NC State's stacked Common Name(s) list and its Description opener, `Carolina jessamine is a member of the
      yellow-jessamine family (Gelsemiaceae).`
    - Added the audit's two RHS citations: the title `Gelsemium sempervirens | evening trumpet flower` and the Other
      common names line.
  - toxicity_detail restored in the audit's wording. Its Clemson sentences moved to unknowns, among them
    "Children can be poisoned by sucking the nectar from the flowers". Its MoBot sentence ("Flowers and foliage")
    moved too. The audit's four citations were added: `Poisonous to Humans:\nPoison Severity:\nHigh`,
    `Causes Contact Dermatitis:\nNo`, RHS's handling warning, and RHS's `Pets (poultry): Harmful if eaten.`
  - climbs null -> true:
    - `Thin, wiry, evergreen vine that climbs by twining` (NC State Quick ID).
    - `It may grow from 12 to 20 feet as a twining vine trained to an arbor or trellis after three to four growing
      seasons.`
  - Size:
    - Height 120-240 in now lands as reach (NC State Dimensions).
    - Spread 240-360 -> null on the coordinator's call. NC State's `Width: 20 ft. 0 in. - 30 ft. 0 in.` reads as the
      vine's sprawl. RHS (`0.5-1 metres`) and MoBot (3-6 ft, browser-read) disagree by an order of magnitude, and
      landed, it would tell a fence-grown vine it spreads to 30 ft.
    - One unknowns line quotes all three figures, and the Width citation, which supported only this pair, was
      dropped.
  - is_houseplant null -> false, citing the Plant Type field (5 values) and zones 6a-10b.
  - Added: RHS Position `Full sun, Partial shade`, CORR, and the RHS page title.
  - Relabelled: the banner citation and the soil-drainage citation.
  - The honeybee-toxic-pollen warning sits in unknowns[0], beside attracts_pollinators true.
- Japanese Clematis
  - name_note restored in the audit's wording.
    - The Previously known as list is now one stacked quote of three names, replacing two bare splinters.
    - The RHS Synonyms citation quotes the whole paragraph rather than the splinter `Clematis paniculata Thunb.`
  - climbs null -> true: `It climbs other vegetation, forming dense blankets that block sunlight to the plants
    underneath.` and Habit/Form `Climbing\nDense\nSpreading`. Height 180-360 in lands as reach. Spread is NC State's
    own Width.
  - soil_base re-cited from Soil Texture `Loam (Silt)` (truncated, and no evidence of bed versus pot) to RHS's
    planting-locations list, which has no container entry. This is the audit's substitute.
  - Citation fixes: [4] label, [5] quote, [9] quote, [16] (now the Poison-block run), [24] and [26] labels, and CORR.
    The two one-value Light picks became one stacked quote, and `Causes Contact Dermatitis:\nYes` was added.
  - is_houseplant null -> false.
  - toxicity_detail: one clarification. The handling warning is the closing sentence of the Poison Symptoms value.
- Purple Leaf Sand Cherry
  - toxicity_detail restored in the audit's wording. Its MoBot clause was replaced by RHS's genus-level line `Some have
    edible fruit in autumn` (cited), which supports nothing here.
  - Added NC State's structured Problems field (6 values), placed first for toxic_to_pets.
  - Re-quoted [4] to the full 14-tag Tags line, the b94 form.
  - Added for the name and accepted name: NC State's Common Name(s) list, its prose opener, CORR, and the RHS title
    `Prunus × cistena | purple-leaf sand cherry`.
  - Added the Soil Drainage field `Good Drainage\nMoist` (first) and RHS Moisture.
  - is_houseplant null -> false, citing `Shrub\nTree`, as the audit specified.
- Japanese Euonymus
  - Every audit citation fix was applied:
    - [3] now also carries common_name. Before this, no citation named common_name.
    - [5] relabelled.
    - [17] became `Full sun, Partial shade`.
    - [18] relabelled.
  - A hedge/border sentence now leads soil_base.
  - Dimensions-block citations now lead size.
  - Added: the Poison-block severity run, `Causes Contact Dermatitis:\nNo`, and CORR.
  - name_note: one sentence corrected. The RHS title "pairs the binomial with 'evergreen spindle'".
  - is_houseplant null -> false.
- Spanish Bluebell
  - toxic_to_pets null -> true on RHS's `Harmful if eaten. Wear gloves and other protective equipment when handling.
    Pets (dogs, cats, rabbits): Harmful if eaten.` This is the audit's finding.
  - toxicity_detail restored in the audit's wording, ending "while NC State gives Asparagaceae". The MoBot family
    clause was dropped.
  - name_note rewritten without MoBot:
    - RHS's title `Hyacinthoides hispanica | Spanish bluebell` is now the second lead.
    - The synonym sub-claim now rests on RHS's own Synonyms field (Scilla hispanica, Scilla campanulata). Endymion
      hispanicus is MoBot-only and moved to unknowns.
  - Citation fixes: [6] became the stacked list, [10] lost its stray separator, [11] became the full Poison-block run,
    and [18] was relabelled, with NC State's family sentence added.
  - Reordering and additions:
    - The structured Light field now leads sun.
    - `Good Drainage\nMoist` now leads soil_drainage.
    - Clemson's woodland-areas sentence was added for soil_base.
    - RHS's page title and CORR were added.
  - is_houseplant null -> false.
- Japanese Banana
  - is_houseplant null -> false, the audit's recommendation (see decisions).
  - The Light field was re-quoted whole and put first.
  - The two one-value Soil Drainage picks became `Good Drainage\nMoist`.
  - Added CORR.
  - outdoor_sun_exposure was kept as researched (see decisions).
- Red Spider Lily
  - name_note restored in the audit's wording, without MoBot. Added the audit's citations (a), (c) and (d): the NC
    State Description opener, the Clemson H1 `Spider Lilies`, and the Clemson caption.
  - toxicity_detail restored in the audit's wording, with citations (A)-(D).
  - Added the unknowns line on RHS's shared Lycoris wording, verified on the aurea page.
  - The flowerbed sentence was added and put first for soil_base. [20] and [22] were relabelled.
  - attracts_pollinators: the Wildlife Value sentence now leads, and Play Value was re-quoted as its whole field.
  - is_houseplant null -> false. Added CORR.

## Common names and accepted names
- All seven were kept as researched: Carolina Jessamine, Japanese Clematis, Purple Leaf Sand Cherry, Japanese
  Euonymus, Spanish Bluebell, Japanese Banana and Red Spider Lily.
- No collision with a landed common_name, and covered.py is clean for all seven binomials.
- No accepted-name change.
- The disclosed splits:
  - RHS leads Gelsemium with "evening trumpet flower".
  - Clemson and RHS lead Clematis with "sweet autumn clematis".
  - RHS leads Euonymus with "evergreen spindle".
  - Clemson heads its Lycoris page "Spider Lilies".

## Audit requests I could not do
- Every MoBot citation or quote substitute the audit offered was skipped under rule 4. That covers:
  - Japanese Clematis' optional sun citation.
  - Purple Leaf Sand Cherry's `Type: Deciduous shrub`.
  - Spanish Bluebell's [1], [3], [7]-[9], [22] and [31] substitutes, plus the MoBot Common Name, Sun and Family lines.
  - Japanese Banana's `Sun: Full sun`.
  - Red Spider Lily's (b) and (e).
  Their content is in unknowns, marked as browser-read.
- Japanese Banana: the audit's drop of part_shade was not applied (decision 1).

## Decisions for the owner
1. **Japanese Banana part_shade.** I kept it, against the audit's flag.
   - Why I kept it: NC State's structured Light field lists Partial Shade, and its Description says "prefers full sun
     to partial shade". The only North American structured field that excludes it is MoBot's `Sun: Full sun`, which
     can't be checked from here. RHS's UK Position (Full sun) alone does not exclude a North American value.
   - If you accept the auditor's browser read of MoBot, dropping it is a one-line change.
2. **Japanese Banana is_houseplant false.** NC State tags it #interiorscape and gives indoor-pest advice. The only
   species-specific indoor guidance is overwintering in a sunny room, read here as winter protection (the b86
   precedent).
3. **Carolina Jessamine spread.** Resolved: the coordinator had it nulled before commit (see above).
4. **Carolina Jessamine's child warning.** Clemson's "Children can be poisoned by sucking the nectar from the
   flowers" is a real safety line, but it lives only in unknowns because the page returns 403 here. It can be cited
   once someone fetches the page from a machine Clemson accepts.

NORMALIZATION string: written.
