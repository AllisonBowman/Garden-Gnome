# b94 landing: eight home-landscape shrubs and small trees (2026-10-03)

The landed file is `app/data/verified/b94-shrubs.json`. It is not committed. The repair script is `b94_repair.py` and
the scratch copy is `b94_landed_records.json`, both in this directory. All 8 species landed, none were withheld, and 0
were unverified.

## Checks
- `b94_repair.py`: generic_passes clean.
- `land_check.py b94_landed_records.json` ends `=== problems === none`. toxic_to_pets: Littleleaf Boxwood, Anglo-Japanese
  Yew, Cherry Plum and Yoshino Cherry are true on NC State's Problem for Cats / Problem for Dogs values or their
  `#problem for` tags (the boxwood also on its "Dogs and cats: vomiting, diarrhea" symptom clause, the yew on "seizures in
  dogs"); Shrubby Cinquefoil is false on `#non-toxic for cats #non-toxic for horses #non-toxic for dogs`. Chinese Juniper,
  Chinese Holly and Indian Hawthorn are null (no page names cats or dogs).
- `verify_quotes.py app/data/verified/b94-shrubs.json`: `215 hit, 0 MISS, 0 inconclusive, 0 skipped (pdf/http/error)`.
  No MoBot or Clemson citation is landed, so nothing SKIPs.
- Stricter check (scratchpad `b94_stack.py`): every quote line sits inside one rendered block and every newline-stacked
  quote is a run of consecutive blocks: 215 citations, 0 flagged. Each stacked list was also checked to be bounded by its
  own label and the next label (no truncated or over-extended list).
- `pytest tests/test_tranche_invariants.py tests/test_claim_ingest.py`: only the ingest count fails. After the
  coordinator's yew correction b94 adds exactly 85 claims (`batch_claims.py`: 8 records, 85 claims, none unsupported),
  so b94 alone on the committed 7,157 baseline makes 7,242. The final run printed `assert 7418 == 7157` (4126 passed)
  because other agents' uncommitted b90-houseplants.json (85) and b93-edibles.json (91) sit beside it. Before the
  correction b94 was 84 claims (`assert 7241 == 7157`).
  (Before the orchestrator committed b92 the same run printed `assert 7241 == 7080` = b94's 84 + b92's 77. A last run,
  after other agents left uncommitted b90-houseplants.json (85) and b93-edibles.json (91) beside it, printed
  `assert 7417 == 7157` with 4126 passed: b94 + b90 + b93, and no duplicate species across them.)
- Page cache: RHS 253106 (Prunus × yedoensis), 13582 (Potentilla fruticosa) and 25565 (Potentilla nepalensis, checked,
  not cited) were fetched through the normal verify_quotes fetch path with www.rhs.org.uk allowed. Nothing in the cache
  was edited or deleted. The one cited page that was not cached, MoBot kempercode=d956 (Taxus × media), is no longer cited.

## finish() table
```
Littleleaf Boxwood         acc=Buxus microphylla house=False toxic=True sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=33 unk=11
Chinese Juniper            acc=Juniperus chinensis house=False toxic=None sun=['full_sun'] drain=moderate water=None ph=5/None base=garden_bed cites=20 unk=11
Anglo-Japanese Yew         acc=Taxus × media house=False toxic=True sun=['full_sun', 'part_shade'] drain=None water=None ph=None/None base=garden_bed cites=28 unk=9
Cherry Plum                acc=Prunus cerasifera house=False toxic=True sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=None cites=19 unk=11
Yoshino Cherry             acc=Prunus × yedoensis house=False toxic=True sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=24 unk=11
Chinese Holly              acc=Ilex cornuta house=False toxic=None sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=31 unk=13
Indian Hawthorn            acc=Rhaphiolepis indica house=False toxic=None sun=['full_sun'] drain=moderate water=None ph=None/None base=garden_bed cites=28 unk=12
Shrubby Cinquefoil         acc=Dasiphora fruticosa house=False toxic=False sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=32 unk=11
```
Grown-schema fields as landed: Littleleaf Boxwood edible false, pollinators true, height 36-48 in, spread 24-48 in;
Chinese Juniper edible null, pollinators null, 600-720 / 120-240; Anglo-Japanese Yew edible false, pollinators null,
24-240 / 24-144; Cherry Plum edible true, pollinators true, 180-360 / 180-300; Yoshino Cherry edible null, pollinators
true, 360-480 / 240-600; Chinese Holly edible false, pollinators true, 96-180 / 96-180; Indian Hawthorn edible null,
pollinators true, 48-72 / 48-72; Shrubby Cinquefoil edible null, pollinators true, 24-48 / 36-60. Every size is the
taxon's own NC State Dimensions block (the yew's spans its cultivars, as its own page says); no climber in the batch.

## The rules that shaped this landing
- Standing rule 4 (MoBot/Clemson only on a cache HIT): MoBot refuses this machine, so no MoBot page is cached. The yew's
  three MoBot research citations were dropped, and the one value that rested on them alone was nulled (yew
  soil_drainage). Every MoBot statement the auditor read in a browser (lead names, sizes, Sun/Water fields, the
  boxwood's scorch warning) is carried in unknowns, marked as the auditor's reading and not cited; none sits in a
  name_note or toxicity_detail.
- Standing rule 2 (edibility): the app shows is_edible true as "grown to eat". Cherry Plum stays true (a real fruit with
  toxic pits, leaves and stems) and its unknowns now carry NC State's whole pit condition verbatim. Chinese Juniper goes
  to null; the yew stays false (no page for it mentions a food use, so its own Poison block decides); see below.

## Values changed or restored
- Chinese Juniper outdoor_sun_exposure: [full_sun, part_shade] -> [full_sun] (FLAGGED on audit). part_shade rested only
  on RHS's Position field; NC State's structured Light field lists only "Full sun (6 or more hours of direct sunlight a
  day)", and its partial-shade wording is a tolerance ("Most prefer sunny locations but will accept partial shade.").
  Same as Creeping Juniper (b85). The RHS citation is relabelled as full_sun support only.
- Chinese Juniper is_edible: true -> null (rule 2; not refuted by the audit). NC State: "The immature berries are often
  used in cooking for seasoning." / Edibility field 'immature cone "berry" used as seasoning'. RHS on the same species:
  "Harmful if eaten/skin allergen. Wear gloves and other protective equipment when handling". A seasoning use of the
  immature cones of an ornamental conifer that an admissible source calls harmful if eaten is marginal food use. The food
  sentence stays cited under toxicity_detail (which now quotes it); the condition and the RHS warning are in unknowns.
- Anglo-Japanese Yew is_edible: stays false (coordinator's correction of an earlier instruction to null it). Rule 2's
  null is for a poisonous plant whose pages mention a marginal food use, and no page for this hybrid mentions one (NC
  State says only "Birds eat the aril and disperse the seed."), so its own Poison block decides. The research
  citation (the single tag #poisonous if ingested) is replaced by NC State's whole Poisonous to Humans block, quoted as
  the page renders it, the way English Yew (b26) cites its source's toxicity text; the unknowns line says false rests
  on that block.
- Anglo-Japanese Yew soil_drainage: moderate -> null (rule 4). It rested on MoBot's "average, medium moisture,
  well-drained soils". NC State alone gives the bare Soil Drainage value Good Drainage, "These yews prefer sandy or loamy
  soils and do not tolerate wet conditions.", "They are drought tolerant." and "Failure to provide proper drainage can
  lead to root rot." -- wet intolerance, which supports neither moderate nor fast.
- is_houseplant: null -> false, cited (the landing gate refuses null), on Littleleaf Boxwood (Plant Type "Perennial /
  Shrub", USDA zones 6a-9b, RHS "H6") and Yoshino Cherry (Plant Type "Perennial / Tree", zones 5a-8b, RHS "H6").
- toxicity_detail restored in the audit's corrected wording (each removed on audit): Littleleaf Boxwood (adds RHS's
  dogs-only "Pets (dogs): Harmful if eaten", cited), Anglo-Japanese Yew (banner vs. human-scoped block, full 22-tag row,
  "#poisonous fruits" vs. Poison Part Bark/Leaves/Seeds; the closing MoBot clause moved to unknowns), Cherry Plum (six
  Problems values, separate Edibility line, RHS's edible-fruit description cited; the MoBot fruit quote moved to unknowns),
  Chinese Holly (verbatim; RHS's full Potentially harmful row incl. its Pets line now cited), Shrubby Cinquefoil
  (verbatim; RHS's "Fruit are ornamental - not to be eaten ..." row cited).
- Yoshino Cherry toxicity_detail: one sentence added -- RHS's dedicated profile carries no toxicity statement.
- name_note restored in the audit's corrected wording (each removed on audit): Littleleaf Boxwood (RHS "small-leaved
  box" cited; MoBot's "boxwood" moved to unknowns; the Boxwood contrast now cites NC State's Buxus sempervirens opener),
  Yoshino Cherry (RHS H1 / "Yoshino cherry" / Correct cited from the newly cached RHS page; adds that Japanese Flowering
  Cherry is this catalog's Prunus serrulata name), Shrubby Cinquefoil (RHS H1 Potentilla fruticosa + Correct, subtitle and
  other-names row cited; MoBot clauses dropped; adds why Golden Hardhack is not used, citing NC State's Spiraea tomentosa
  list, whose "Hardhack" names the landed Steeplebush).
- Cherry Plum name_note: adds RHS's lead "cherry plum" and its other common names (mirabelle, myrobalan, myrobalan plum,
  weeping plum), both cited. Indian Hawthorn name_note: the leading word "Trap:" removed; nothing else.
- Citation repairs, all as the audit prescribed and each re-read on the cached page: NC State label+value splices cut to
  values (Problems, Plant Type, Soil Drainage, Attracts); Poison-block severities re-quoted with their "Poisonous to
  Humans:" heading; truncated lists completed (Cherry Plum Problems x6, Yoshino often-confused module x5, Indian
  Hawthorn Previously-known-as x3, yew Tags row x22); bare "Correct" paired with an RHS H1 (Juniper, Yoshino; CORR
  labels on Juniper, Yoshino and Holly); claim labels that said more than their quote shows corrected (Juniper and
  Cinquefoil H1s said to carry the <title> parenthetical, Yoshino's title label asserting the list, the yew's Tags quote
  labelled as the Problems field, Holly's banner labelled as the Poison block, the boxwood soil_base "in-ground" label,
  Indian Hawthorn's single-entry Common Name(s) list now labelled for name_note); extractor
  spacing artifacts removed (yew "(Taxus baccata)", "Among the"; Indian Hawthorn "Rhaphiolepsis, is", "R. x delacouri,
  which"); RHS genus Cultivation boilerplate replaced by RHS's structured Position/Moisture fields (Holly, Indian
  Hawthorn); Indian Hawthorn's RHS-size disclosure citation no longer carries the mature_height_in stem.
- New corroborating RHS citations (verifiable, no value changed): Yoshino "Plants for pollinators"; Cinquefoil Position,
  Moisture and "Plants for pollinators"; Juniper subtitle "Chinese juniper".

## Common names
All eight kept as researched; none collides with a landed common_name, and covered.py finds each binomial only in b94.
- Littleleaf Boxwood: NC State's prose opener (its alphabetized list starts Littleleaf Box); RHS leads with small-leaved
  box; the bare Boxwood is b19's Buxus sempervirens.
- Anglo-Japanese Yew: RHS's lead. NC State lists only Foundation Yew and Yew; the requested "Anglojap Yew" is on no
  admissible page.
- Yoshino Cherry: NC State's prose opener and RHS's lead; NC State's first list entry, Japanese Flowering Cherry, is
  b26's Prunus serrulata.
- Shrubby Cinquefoil: NC State's prose opener and RHS's lead; not Golden Hardhack (hardhack is also a Steeplebush name).
- Chinese Juniper, Cherry Plum, Chinese Holly, Indian Hawthorn: every dedicated page agrees.

## Accepted names
- Taxus × media and Prunus × yedoensis keep the spaced U+00D7 (NC State writes "Taxus x media" / "Prunus x yedoensis"
  and lists "Taxus media" under Previously known as; RHS writes ×).
- Dasiphora fruticosa follows NC State's current title, as the batch brief and the audit's corrected name_note both say;
  RHS's dedicated page is Potentilla fruticosa with Name Status Correct, disclosed in name_note.

## Could not do / disclosed
- MoBot (all eight species) cannot be fetched here; nothing rests on it. Clemson returned 403 where tried; UF/IFAS ST523
  (Yoshino) and ST554 (Indian Hawthorn) return 410. All disclosed in unknowns.

## Decisions for the owner
1. Shrubby Cinquefoil's accepted name. It follows NC State (Dasiphora fruticosa) per the batch brief, but b72 (Hibiscus
   moscheutos) and b89 (Chrysanthemum × grandiflorum, Glandularia × hybrida) followed RHS's Correct name over NC State's
   title. Consequence: covered.py and the duplicate-species test key only on given and accepted names, so a future
   "Potentilla fruticosa" candidate would not be caught as a duplicate. Switching accepted to Potentilla fruticosa would
   match precedent and close that gap.
2. Chinese Juniper is_edible null rather than true (rule 2 judgment): NC State calls the immature cones a cooking
   seasoning; RHS calls the plant harmful if eaten. Eastern Redcedar (b42) is null; Creeping Juniper (b85) is false.
