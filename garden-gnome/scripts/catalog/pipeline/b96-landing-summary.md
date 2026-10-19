# b96 landing: eight mixed species (2026-10-03)

The landed file is `app/data/verified/b96-mixed.json`. It is not committed. The repair script is `b96_repair.py` and
the scratch copy is `b96_landed_records.json`, both in this directory (`b96_dump.txt` and `b96_audit.txt` were generated
with dump_batch.py). All 8 species landed, none were withheld, and 0 were unverified.

## Checks
- `b96_repair.py`: generic_passes clean.
- `land_check.py b96_landed_records.json` ends `=== problems === none`. toxic_to_pets: Mother Of Thousands is true on
  NC State's Problems field values (Problem for Cats, Problem for Dogs); Oyster Plant on its `#problem for cats` and
  `#problem for dogs` tags (the Problems field is cited under toxicity_detail); Carnation on the tag run
  `#problem for cats #problem for dogs #problem for horses`; August Lily on "All parts of this plant are toxic to cats,
  dogs, and horses."; Urn Plant is false on `#non-toxic for cats` and `#non-toxic for dogs`. Chin Cactus, Caucasian
  Stonecrop and New York Aster are null (no page names cats or dogs).
- `verify_quotes.py app/data/verified/b96-mixed.json`: `266 hit, 0 MISS, 0 inconclusive, 0 skipped (pdf/http/error)`.
  No MoBot or Clemson citation is landed, so nothing SKIPs.
- Stricter checks (scratchpad `b96land/chk.py --file` and `bounds.py`): every quote line sits inside one rendered block
  and every newline-stacked quote is a run of consecutive blocks (266 citations, 0 flagged); every stacked list runs from
  its own label to the next label, so none is truncated or over-extended (Phedimus's Plant Type stops before "Woody Plant
  Leaf Characteristics:").
- `pytest tests/test_tranche_invariants.py tests/test_claim_ingest.py`: only the ingest count fails, `assert 7745 ==
  7582` (4312 passed). b96 adds exactly 88 claims (`batch_claims.py`: 8 records, 88 claims, none unsupported); the other
  75 are another agent's uncommitted `b97-mixed.json`. b96 alone on the 7582 baseline makes 7670.
- Page cache: nothing was fetched into it, edited or removed. Every cited NC State, RHS and UF/IFAS page was already
  cached. The one uncached cited page, MoBot kempercode=h120 (August Lily), was retried through qc.py with the MoBot hosts
  allowed and failed with ConnectError (not cached); it is no longer cited.

## finish() table
```
Chin Cactus                acc=Gymnocalycium mihanovichii house=True toxic=None sun=['part_shade'] drain=None water=dry_thoroughly_between ph=None/None base=cactus_succulent cites=21 unk=11
Mother Of Thousands        acc=Kalanchoe daigremontiana house=True toxic=True sun=['part_shade'] drain=None water=dry_thoroughly_between ph=None/None base=cactus_succulent cites=38 unk=13
Oyster Plant               acc=Tradescantia spathacea house=True toxic=True sun=['part_shade'] drain=moderate water=dry_surface_between ph=None/None base=standard_potting cites=52 unk=9
Urn Plant                  acc=Aechmea fasciata house=True toxic=False sun=['part_shade'] drain=moderate water=None ph=None/None base=orchid_bark cites=33 unk=9
Carnation                  acc=Dianthus caryophyllus house=False toxic=True sun=['full_sun', 'part_shade'] drain=moderate water=None ph=6/None base=garden_bed cites=34 unk=11
Caucasian Stonecrop        acc=Phedimus spurius house=True toxic=None sun=['full_sun'] drain=fast water=dry_thoroughly_between ph=None/None base=None cites=33 unk=13
August Lily                acc=Hosta plantaginea house=False toxic=True sun=['part_shade', 'full_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=31 unk=11
New York Aster             acc=Symphyotrichum novi-belgii house=False toxic=None sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=24 unk=9
```
Grown-schema fields as landed: Chin Cactus edible null, pollinators null, height 2-3 in, spread 2-3 in; Mother Of
Thousands edible false, pollinators null, 12-36 / 12-24; Oyster Plant edible false, pollinators null, 6-12 / 12-24; Urn
Plant edible null, pollinators null, 12-36 / 12-24; Carnation edible null, pollinators true, 12-48 / 6-12; Caucasian
Stonecrop edible null, pollinators true, 2-6 / 24-36; August Lily edible null, pollinators true, 12-24 / 36-48; New York
Aster edible null, pollinators true, 36-60 / 12-24. Every size is the species' own NC State Dimensions block. No climber
is in the batch. The four houseplants' sizes are their NC State figures, all well under 120 in.

## The rules that shaped this landing
- Standing rule 4 (MoBot/Clemson only on a cache HIT): MoBot refuses this machine. August Lily's seven MoBot research
  citations were dropped, and the one value that rested on them alone, water_regime keep_moist, went to null. Its
  common_name, name_note, sun and soil_base citations now rest on NC State and RHS. Every MoBot statement the auditor or
  researcher read in a browser (lead names, Sun/Water fields, sizes, culture sentences) is in unknowns, attributed as such;
  none sits in a name_note or toxicity_detail. The audit's corrected name_note and toxicity_detail wording was used
  verbatim minus its MoBot sentences (Oyster Plant, Urn Plant, August Lily, New York Aster).
- Standing rule 2 (edibility): Carnation and Caucasian Stonecrop go true -> null; Mother Of Thousands and Oyster Plant
  stay false (no page mentions a food use, and NC State calls each toxic if ingested). See below.

## Values changed or restored
- Chin Cactus outdoor_sun_exposure: [full_sun, part_shade] -> [part_shade] (FLAGGED). NC State: "Overexposure to direct
  sun can cause scorching, particularly in grafted varieties." and "These plants prefer bright, indirect sunlight ..."
- Mother Of Thousands outdoor_sun_exposure: [full_sun, part_shade] -> [part_shade] (FLAGGED). NC State: "Leaf scorch can
  result if the plant receives prolonged direct sunlight or intense afternoon sun." RHS's Position "Full sun" is
  disclosed as a counterpoint.
- Oyster Plant outdoor_sun_exposure: [full_sun, part_shade] -> [part_shade] (FLAGGED). RHS's species-level Cultivation
  text: "Direct sunshine may scorch the leaves." (checked against the cached RHS T. zebrina and T. pallida pages, which
  carry different text), and NC State: "If kept outdoors in the summer, provide it with afternoon shade."
- Carnation outdoor_sun_exposure: kept [full_sun, part_shade]; the FLAGGED drop of part_shade was declined. The audit's
  case was RHS's Position "Full sun", RHS's "Grow in a well-drained soil in a sunny position" and NC State's "preferring
  sun" / "the sunny border". Under the landing brief, a value goes only when the other North American structured field
  excludes it or a scorch/flop warning contradicts it. Neither applies: RHS is the only excluding field, MoBot cannot be
  read, and NC State's heat warning is a climate caution. Chinese Pink (b92) landed the same pair on the same pattern.
- Carnation is_edible: true -> null (rule 2). The page says "Flowers are edible." (Edibility field, Edible Garden theme,
  #edible flowers). The same page has a low-severity Poisonous to Humans block naming no poison part ("Mild
  gastrointestinal signs, mild dermatitis"), and RHS calls the plant a skin allergen. The sentence stays cited under
  toxicity_detail.
- Caucasian Stonecrop is_edible: true -> null (rule 2). The page says "Stems and leaves, when very young and tender, may
  be eaten raw. Later, until they flower, they may be briefly cooked." The same page lists Poisonous under Plant Type and
  Flowers, Leaves, Roots, Stems under Poison Part. Its toxicity_detail no longer says "must not be read as a bare yes";
  it says the record leaves is_edible null.
- August Lily water_regime: keep_moist -> null (rule 4; it rested only on MoBot's "Plants need consistent moisture during
  the growing season.").
- is_houseplant: null -> false, cited, for Carnation (Plant Type "Annual / Herbaceous Perennial / Perennial", Landscape
  Location "Container / Patio / Small Space / Walkways") and New York Aster (Plant Type "Herbaceous Perennial / Native
  Plant / Wildflower", Landscape Location "Lawn / Meadow / Naturalized Area").
- Refuted fields left null: Chin Cactus soil_drainage (fast had no sharp/sandy requirement), Urn Plant water_regime
  (keep_moist was read off a potting-medium adjective; the cup routine stays in water_estimate_basis).
- name_note restored in the audit's corrected wording for Mother Of Thousands, Oyster Plant, Urn Plant, Carnation,
  Caucasian Stonecrop, August Lily and New York Aster, with one name_note citation per sub-claim. Additions beyond the
  audit's text: Carnation and Caucasian Stonecrop each gained the closing sentence naming the landed choice, as the audit
  asked. Stonecrop also gained "its body prose uses the bare name Stonecrop" and RHS's Sedum spurium page (H1 + Correct),
  both cited. One wording change: Oyster Plant's "so do not merge those entries" became "this record takes nothing from
  either".
- toxicity_detail restored in the audit's corrected wording for Mother Of Thousands (adds the keep-away sentence and the
  whole Poison block, quoted as rendered), Oyster Plant (adds RHS's "Skin allergen." hazard, Toxic Principle Unidentified,
  Contact Dermatitis Yes and the toxicity tags), Urn Plant (RHS-only, MoBot clause dropped) and Carnation (adds RHS's
  "Humans/Pets: Skin allergen ..." row and the disagreement with NC State's "Causes Contact Dermatitis: No"). August Lily
  gained one sentence: RHS's page carries no toxicity statement.
- scientific_name_accepted: an RHS H1 + Name Status Correct (CORR) pair was added for Chin Cactus, Mother Of Thousands,
  Urn Plant, Carnation and New York Aster. Oyster Plant and August Lily already cited RHS's bare "Correct"; it now
  carries the CORR label, and each is paired with the RHS H1.

## Common names
- Phedimus spurius: Two-row Stonecrop -> **Caucasian Stonecrop** (FLAGGED; the audit's recommendation). No checkable
  dedicated page leads with Two-row Stonecrop: it is the third of NC State's three alphabetized names, and NC State's prose
  uses the bare "Stonecrop". RHS's Phedimus spurius and Sedum spurium pages both lead with Caucasian stonecrop (subtitle
  and title). MoBot leads with it too, per the auditor's reading. Creeping Stonecrop, NC State's first entry, is the
  alternative. No collision with Showy Stonecrop, Three-leaved Stonecrop or Burro's Tail.
- Dianthus caryophyllus: kept **Carnation**, although the audit FLAGGED it. NC State's Description opens "Carnations are a
  herbaceous perennial ...", which the brief admits as a lead (precedent: b91 Siberian Iris, b84 Tomatillo), and the
  batch asked for it. Both pages put Border Carnation first (NC State's list; RHS's subtitle and title), and this is
  disclosed in name_note and unknowns.
- Kalanchoe daigremontiana: lands as **Mother Of Thousands**. NC State's Description opens with the name, and its list
  carries "Mother of Thousands". repair_lib.title_ok makes every word capitalised, small words included, and this is the
  first post-gate landed name with an "of".
- Gymnocalycium mihanovichii: the batch's "Moon Cactus" landed as **Chin Cactus**, as researched. It is NC State's first
  list entry and its description name, and NC State says the grafted cultivars are the ones "known as 'moon cactus.'"
- Kept as researched: Oyster Plant, Urn Plant, August Lily, New York Aster. New York Aster is NC State's Description
  opener, while NC State's list and RHS both put Michaelmas Daisy first; disclosed in name_note. No landed name collides
  with an existing common_name (grep of app/data/verified), and covered.py finds each binomial only in b96.

## Accepted names
- All eight equal the given names. Phedimus spurius follows NC State's dedicated page, as the batch brief and the audit's
  corrected name_note say. RHS treats the plant as Sedum spurium: its Phedimus spurius page reads Synonym with a Sedum
  Genus field, and its Sedum spurium page reads Correct. This is disclosed in name_note and unknowns.

## Audit requests not applied, and how each record discloses it
- Every MoBot citation the audit proposed was left out: Oyster Plant Common Name and prose plus a sun counterpoint, Urn
  Plant Common Name, New York Aster prose. So were August Lily's MoBot research citations. Their readings are quoted in
  unknowns and attributed to the auditor or researcher.
- Carnation part_shade drop declined (see above). Its unknowns entry gives both sides.
- Oyster Plant's optional part_sun was not added. The audit called it optional, and it rested partly on MoBot.

## Decisions for the owner
1. Mother Of Thousands: title_ok forces "Of". The older Lily of the Valley, Rose of Sharon and Queen of the Prairie
   predate the gate. Relaxing title_ok for small words, then relanding, would give "Mother of Thousands".
2. is_edible null, not true, for Carnation and Caucasian Stonecrop (rule 2 judgment). Three-leaved Stonecrop (b79, Sedum
   ternatum) landed true on the identical NC State Edibility wording before this rule. Its page has no Poison block;
   Phedimus's has one.
3. Carnation part_shade kept against the audit's flag. Dropping it would match RHS and NC State's prose. Keeping it
   matches the brief's drop conditions and Chinese Pink.
4. August Lily: full_sun stays out on RHS's Position ("Full shade, Partial shade") plus NC State's own condition ("in
   cooler climates, providing proper moisture is maintained"). It was not counted against MoBot. water_regime is null
   only because MoBot cannot be checked here.
5. Phedimus spurius vs Sedum spurium. The accepted name follows NC State (as b94 did for Dasiphora), but RHS calls
   Sedum spurium Correct. covered.py reports "Sedum spurium" as clean (genus note only). A future batch researching it
   under that name would not be caught as a duplicate.

NORMALIZATION: written.
