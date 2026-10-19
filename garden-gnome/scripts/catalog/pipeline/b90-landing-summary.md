# b90 (houseplants) -- landing summary

Landed 2026-10-03 from `b90_records.json` (8 species, 0 unverified, 0 agents failed) by `b90_repair.py`, following
LANDING_BRIEF.md and the orchestrator's four standing rules. Output: `app/data/verified/b90-houseplants.json`; the
full repaired result is in `b90_landed_records.json`. Not committed.

All eight landed; none withheld.

## finish() table

```
Thanksgiving Cactus        acc=Schlumbergera truncata house=True toxic=False sun=['part_shade'] drain=moderate water=None ph=None/8 base=cactus_succulent cites=25 unk=13
African Milk Tree          acc=Euphorbia trigona house=True toxic=True sun=['part_shade'] drain=None water=dry_surface_between ph=None/None base=cactus_succulent cites=33 unk=12
Kentia Palm                acc=Howea forsteriana house=True toxic=False sun=['part_shade'] drain=None water=None ph=None/None base=standard_potting cites=16 unk=11
Chinese Banyan             acc=Ficus microcarpa house=True toxic=None sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=None cites=17 unk=12
Queensland Umbrella Tree   acc=Heptapleurum actinophyllum house=True toxic=True sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=None cites=40 unk=16
Rattlesnake Plant          acc=Goeppertia insignis house=True toxic=False sun=['part_shade', 'full_shade'] drain=moderate water=keep_moist ph=None/None base=standard_potting cites=26 unk=14
African Spear              acc=Dracaena angolensis house=True toxic=True sun=['part_shade'] drain=None water=None ph=None/None base=cactus_succulent cites=43 unk=14
Bunny Ears Cactus          acc=Opuntia microdasys house=True toxic=True sun=['full_sun', 'part_shade'] drain=fast water=dry_thoroughly_between ph=None/None base=cactus_succulent cites=34 unk=10
```

## Checks

- `land_check.py b90_landed_records.json`: ends `=== problems ===` / `none`. Every toxic_to_pets citation names cats
  and/or dogs (Bunny Ears Cactus's names dogs only, RHS's "Pets (dogs): Skin/eye irritant." line).
- `verify_quotes.py app/data/verified/b90-houseplants.json`: `226 hit, 0 MISS, 0 inconclusive, 8 skipped
  (pdf/http/error)`. The 8 SKIPs are all Missouri Botanical Garden on African Spear (ConnectError; the sandbox first
  denied the host, and the re-run with it allowed failed at TLS, as MoBot always does from this machine). No value rests
  on MoBot alone: scientific_name_accepted, is_houseplant and outdoor_sun_exposure each lead with an NC State citation;
  the MoBot-only quotes are name_note sub-claims about MoBot's own naming (the b87-b89 practice), all re-read in a
  browser by the audit.
- `pytest tests/test_tranche_invariants.py tests/test_claim_ingest.py`: 4126 passed, 1 failed -- the expected count
  assert, `assert 7416 == 7333`. The difference, 83, is exactly b90's claims (all eight records fully supported,
  nothing unsupported); b93 and b94 were committed in the meantime and are in the 7333. The test was not edited.
- The repair script's own self-check re-ran verify_quotes' present() on every landed quote against the cached page and
  asserted that no citation is left naming only null fields.

Page cache: nothing deleted, moved or edited. One entry was added the normal way: RHS's Opuntia microdasys profile
(plant 11881), which no record cited and the audit relied on, fetched through qc.py (the sandbox denied www.rhs.org.uk
on the first try; re-run with the host allowed).

## Values changed or restored at landing

- African Spear (Dracaena angolensis), common_name: Cylindrical Snake Plant -> African Spear. See "Common names".
- African Spear, outdoor_sun_exposure: ['full_sun', 'part_shade'] -> ['part_shade'] (the audit's FLAG: NC State's
  Light field carries no full sun, and NC State says "If taken outdoors in the summer, only give it morning sun to avoid
  sunburn."; MoBot says "Protect from hot afternoon sun."). NC State's Light field, which the record described but never
  cited, now leads: "Dappled Sunlight (Shade through upper canopy all day)" / "Partial Shade (Direct sunlight only part
  of the day, 2-6 hours)".
- Bunny Ears Cactus, toxic_to_pets: false (removed on audit) -> true, on RHS's dedicated profile: "Pets (dogs):
  Skin/eye irritant. For further information and contact numbers regarding pets, see the HTA guide to potentially
  harmful plants". The audit's recommended repair, and b32 landed Opuntia ficus-indica true on the identical RHS entry.
  NC State's "#non-toxic for cats" / "#non-toxic for dogs" tags stay as the disclosed counterpoint (relabelled for
  toxicity_detail so the loader shows RHS's dog line as the evidence). toxicity_detail says the hazard is contact
  injury from the glochids, not poisoning, and that no source names cats.
- Restored in the audit's corrected wording: name_note on Chinese Banyan, Rattlesnake Plant, African Spear and Bunny
  Ears Cactus; toxicity_detail on Chinese Banyan, Queensland Umbrella Tree, Rattlesnake Plant and Bunny Ears Cactus.
- Thanksgiving Cactus, is_edible: stays null (removed on audit; NC State's bare "Used for medicine, has environmental
  uses, and for food." is too vague, the Mistletoe Cactus precedent). Its citation was dropped and the unknowns line
  replaced with the audit's wording.

Houseplant size rule (standing rule 3: a page's indoor or container figure lands; an outdoor stature over 120 in with
no indoor figure stays null, quoted in unknowns):

- African Milk Tree, all four sizes (72-144 by 60-120 in) -> null. NC State's only figure is "It can grow up to 6 to
  12 feet tall, 5-10 feet wide" (Dimensions: Height 6 ft. 0 in. - 12 ft. 0 in.; Width 5 ft. 0 in. - 10 ft. 0 in.).
  RHS's "stems and branches to 1.8m (6ft) high" is a general description that the same paragraph sets apart from plants
  "grown in the home", so it is not an indoor figure. The spread was first kept as at the 120 in line; on the
  coordinator's ruling it is nulled with the height, since both come from the one outdoor Dimensions block (the rule:
  when the only figure is the outdoor stature and its height or spread exceeds 120 in, all four stay null). Both size
  citations were dropped; the unknowns line quotes the figures.
- Kentia Palm, all four sizes (315-472 by 157-315 in) -> null. RHS "Max Height 8-12 metres" / "Max Spread 4-8 metres"
  and UF/IFAS "can reach 40 feet in height with a spread of 6–10 feet" are outdoor; NC State has no Dimensions block.
  RHS's description "A single-stemmed evergreen palm to 2m in height ... Flowers seldom produced under glass" is not tied
  to indoor growing by its sentence; Penn State's indoor "typically stays around 2-3 feet high indoors" is on a
  multi-species page.
- Chinese Banyan, mature_height_in 24-600 -> min null, max 157.5; mature_spread_in 24-480 -> null. RHS's species
  description gives a container figure: "A bushy evergreen shrub to 4m when grown in a container, with glossy dark green,
  ovate leaves; in warm climates grows into a large tree with abundant aerial roots" (4 m x 39.37; checked to be
  species text: RHS's F. benjamina and F. pumila descriptions differ). NC State's 2-50 ft by 2-40 ft and "it can reach
  40 feet high with a 40 foot crown" are outdoor; RHS's Max fields are open-ended.
- Rattlesnake Plant, mature_height_in 9-20 -> min null, max 18. NC State: "This plant typically grows to 1 1/2 feet tall
  indoors but can reach up to 2 1/2 feet tall outdoors." The width stays 9-18 in from the Dimensions block (no indoor
  width; under 120 in).
- Queensland Umbrella Tree: 48-72 by 36-72 in unchanged, now cited first to NC State's "Indoor plant size ranges from 4
  to 6 feet tall and 3 to 6 feet wide."
- Thanksgiving Cactus (9-12 by 12-24), African Spear (6-84 by 6-24) and Bunny Ears Cactus (24-36 by 48-60): no page
  gives a separate indoor figure and all are under 120 in, so they stand; each record's size line says so.

Fields nulled at landing, in all: 12 (African Milk Tree 4, Kentia Palm 4, Chinese Banyan 3, Rattlesnake Plant 1), plus
two maxima changed (Chinese Banyan 600 -> 157.5, Rattlesnake Plant 20 -> 18).

## Common names

- Dracaena angolensis: researched "Cylindrical Snake Plant" (the batch's working name) -> landed "African Spear". The
  audit FLAGGED the researched value: no admissible dedicated page leads with it. It is the third entry of NC State's
  alphabetized list (African Spear, Brazil Saint Bárbara Sword, Cylindrical Snake Plant, Spear Sansevieria) and the
  second of RHS's Other common names, and the research had cited NC State's per-name alias page
  (/common-name/cylindrical-snake-plant/), whose H1 is only the name in its own URL. African Spear is NC State's lead by
  both tests (first list item in page-title order; the Description opens "African spear is an easy-to-grow, succulent
  herbaceous perennial native to Africa."). b85 (Wintercreeper -> Climbing Euonymus) and b88 (Lima Bean -> Butter
  Beans) switched flagged names the same way. All NC State citations moved from the alias pages to the canonical
  /plants/dracaena-angolensis/ and /plants/dracaena-trifasciata/ pages (same text; every quote re-checked there).
- Heptapleurum actinophyllum: researched and landed "Queensland Umbrella Tree", RHS's lead (rendered beneath its H1;
  the audit passed it). The batch note's "Umbrella Tree" is the last entry of NC State's alphabetized list, and NC
  State's own description opens with the bare genus name "Schefflera", so neither is a lead. Distinct from the landed
  Dwarf Umbrella Tree (H. arboricola).
- Thanksgiving Cactus, African Milk Tree, Kentia Palm, Chinese Banyan, Rattlesnake Plant, Bunny Ears Cactus: kept.
  Thanksgiving Cactus is NC State's description lead; RHS's lead, "Christmas cactus", is the common_name already landed
  for Schlumbergera × buckleyi (b4), noted in unknowns. African Milk Tree gained a citation to NC State's description
  opener ("The African milk tree is a succulent shrub or tree ...").
- No landed name collides with an already-landed common_name (checked against every app/data/verified file's
  common_name). No accepted-name change: all eight accepted names equal the given names.

## Citation repairs (each substitute read on the cached page first)

- Thanksgiving Cactus: the cropped "hence its most popular common name" -> the full Thanksgiving sentence (twice);
  Soil Drainage "Good Drainage" -> "Good Drainage\nMoist\nOccasionally Dry" (the lone "Occasionally Dry" dropped);
  Previously known as -> all three stacked names; the RHS <title> citation relabelled to carry name_note; bare "Correct"
  -> CORR; RHS Other common names relabelled; a rendered Common Name(s) list citation added beside the title string.
  name_note: the closing research-process remark ("The Missouri Botanical Garden page could not be loaded.") dropped,
  as the audit ruled on Rattlesnake Plant's note; it remains in unknowns.
- African Milk Tree: claim "(the cactus names are trade names)" dropped from a label and "so it is not a cactus" from
  name_note (no page says either); the spurge sentence un-cropped; 'Rubra' stacked; the two "#problem for" tag quotes
  that claimed to be the Problems field -> the six-value Problems stack plus a relabelled Tags-row citation; the
  severity banner re-quoted without scrape spaces and relabelled as the banner, with the Poison block run "Poisonous to
  Humans:\nPoison Severity:\nMedium", Poison Part, Causes Contact Dermatitis and Plant Type added; the is_edible label
  fixed and "#poisonous if ingested" added; the uncited ASPCA sentence moved from toxicity_detail to unknowns.
- Kentia Palm: bare "Correct" -> CORR; size citations dropped with the sizes; unknowns 0, 5 and 8 replaced with the
  audit's wording, the size line rewritten.
- Chinese Banyan: "Name Status Correct" (label glued to value) -> CORR + "Correct"; "Good Drainage" -> "Good
  Drainage\nMoist"; two claim labels de-scoped (the RHS skin-allergen field names no animal; the pavement/invasive
  hedges restored); four name_note citations added (rendered list, Description opener, RHS Other common names, NC
  State's F. benjamina title); unknowns 0, 1, 3, 5 and 8 replaced with the audit's wording.
- Queensland Umbrella Tree: the NC State <title> parenthetical labelled common_name dropped (the name_note copy stays);
  the banner relabelled as the banner, with the Poison block run and Causes Contact Dermatitis added; the Uses
  (Ethnobotany) line cited; RHS synonyms and UF/IFAS's heading cited; Soil Drainage -> the three-value stack, which now
  leads the soil_drainage citations ("Occasionally Wet" alone dropped). The audit's citation indices here ran one high;
  its claim-text identifiers were followed.
- Rattlesnake Plant: three RHS genus-boilerplate Cultivation citations dropped (humidity, compost, watering; identical
  on RHS's other Goeppertia profiles per the audit); "Soil Drainage:\nGood Drainage\nMoist" -> the values only; the
  page-heading claim -> the H1 "Goeppertia insignis" plus CORR; two labels corrected; Plant Type cited; unknowns 2, 3,
  5, 6, 8 and 10 replaced with the audit's wording.
- African Spear: the audit's five name_note citations added; Boncel stacked with its cultivar name; the trifasciata
  alias-page heading -> its Description opener on the canonical page; both "often confused with" modules quoted with
  their items; banner relabelled and the Poison block run, Problems, Poison Part, Causes Contact Dermatitis and Plant
  Type added; unknowns 3, 4 and 11 replaced with the audit's wording.
- Bunny Ears Cactus: RHS's dedicated profile cited for the first time (page title, CORR, rendered name, Name Status,
  both Potentially harmful lines); NC State's rendered Common Name(s) list, full Tags list, Stem Description and Plant
  Type added; the cool_rest_note quote extended to the frost sentence; unknowns 0, 1, 4 and 6 replaced with the audit's
  wording. In unknowns 0 the phrase "UK-calibrated Position field" was replaced with the Chinese Banyan audit's own
  form ("RHS is not a North American source, so it does not exclude NC State's Partial Shade").

## What the audit asked for that was not done

Nothing. Every audit substitute was found on its cached page, including the three optional ones (African Milk Tree's
extra poison-block citations, Rattlesnake Plant's CORR, Bunny Ears Cactus's RHS page title). Missouri Botanical Garden
could not be read from this machine; its quotes stand on the audit's browser reading and SKIP, as disclosed in African
Spear's unknowns.

## For the owner

- African Spear vs Cylindrical Snake Plant. The batch note asked for "Cylindrical Snake Plant"; the brief's
  dedicated-page rule, the audit and the b85/b88 precedent give African Spear. To reverse: set common_name back and use
  the audit's alternate name_note sentence ("Cylindrical Snake Plant, the third entry of NC State's alphabetized list
  and the second of RHS's other common names, is used here so the record never lands under the bare 'Snake Plant' ...").
- Houseplant sizes that are judgment calls: Kentia Palm now has no size (RHS's "to 2m in height", beside "Flowers seldom
  produced under glass", would give a 78.7 in height max if read as the under-glass figure); African Milk Tree has no
  size (outdoor 6-12 ft by 5-10 ft only); Chinese Banyan's container height is 157.5 in (13 ft), large for a houseplant
  but what RHS says for a container.
- Bunny Ears Cactus is toxic_to_pets true on a dog skin/eye-irritant line (contact injury from glochids) while NC State
  tags it non-toxic for cats and dogs; consistent with Prickly Pear (b32).

## Files

`b90_repair.py`, `b90_landed_records.json`, `b90_dump.txt`, `b90_audit.txt`, this summary, and
`app/data/verified/b90-houseplants.json`. The NORMALIZATION string is written into the batch file.
