# b91 landing: eight popular garden perennials (2026-10-03)

The landed file is `app/data/verified/b91-perennials.json`. It is not committed. The repair script is `b91_repair.py` and
the scratch copy is `b91_landed_records.json`, both in this directory. All 8 species landed, none were withheld, and
0 were unverified.

## Checks
- `b91_repair.py`: generic_passes was clean on the first run.
- `land_check.py b91_landed_records.json` ends `=== problems === none`. The only non-null toxic_to_pets is Large-flowered
  Tickseed = false. It rests on the single tags `#non-toxic for cats` and `#non-toxic for dogs`.
- `verify_quotes.py app/data/verified/b91-perennials.json`: `222 hit, 0 MISS, 0 inconclusive, 0 skipped (pdf/http/error)`.
- Extra structure check (scratchpad `b91land/chk.py`) found 0 problems. It checks that each quoted line sits in one
  rendered element and that stacked lines are consecutive elements. It caught the glued quotes listed below.
- pytest `test_tranche_invariants.py` + `test_claim_ingest.py`: only the count test fails.
  - With b91 alone in the tree: `assert 7080 == 7003`, which is b91's 77 claims.
  - On a later run: `assert 7157 == 7003`, after another agent's `b92-annuals.json` (also 77 claims) landed. Every other
    test passed (3982 passed).
- `batch_claims.py`: 8 records, 77 claims. Every field the loader stores is supported (none unsupported).
- Page cache: every cited page was already warm except RHS 16336 (Salvia guaranitica). I fetched it once through qc.py
  with www.rhs.org.uk allowed, which added one entry. Nothing was deleted or edited.

## finish() table
```
Lavandin                   acc=Lavandula × intermedia house=False toxic=None sun=['full_sun'] drain=None water=None ph=None/None base=None cites=25 unk=9
Spanish Lavender           acc=Lavandula stoechas house=False toxic=None sun=['full_sun'] drain=fast water=None ph=None/None base=garden_bed cites=25 unk=10
Large-flowered Tickseed    acc=Coreopsis grandiflora house=False toxic=False sun=['full_sun', 'part_shade'] drain=None water=None ph=None/None base=garden_bed cites=24 unk=12
Siberian Iris              acc=Iris sibirica house=False toxic=None sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=39 unk=10
Autumn Sage                acc=Salvia greggii house=False toxic=None sun=['full_sun', 'part_shade'] drain=None water=None ph=None/None base=garden_bed cites=25 unk=8
White Gaura                acc=Oenothera lindheimeri house=False toxic=None sun=['full_sun'] drain=moderate water=None ph=None/None base=garden_bed cites=28 unk=10
Anise-scented Sage         acc=Salvia guaranitica house=False toxic=None sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=22 unk=9
Japanese Anemone           acc=Eriocapitella × hybrida house=False toxic=None sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=34 unk=14
```
No field was nulled at landing. One list entry was dropped: White Gaura's part_shade. The audit removed name_note on all
eight records and toxicity_detail on three; all of those were restored with citations.

## Values changed or restored (each rests on page text verified in the cache)
- Lavandin
  - name_note restored in the audit's wording, with the RHS page title `Lavandula × intermedia | lavandin` added.
  - toxicity_detail restored in the audit's wording, citing `Poisonous to Humans:` and `This plant has low severity
    poison characteristics.`
  - is_houseplant null -> false, citing `Herbaceous Perennial\nShrub` and `5a, 5b, 6a, 6b, 7a, 7b, 8a, 8b`.
- Spanish Lavender
  - name_note restored. It now discloses that RHS leads with French lavender (`Lavandula stoechas | French lavender`),
    the Other common names line, and RHS's `Lavandula dentata | French lavender`.
  - is_houseplant null -> false, citing the mass-planting sentence and Landscape Location
    `Coastal\nContainer\nPatio\nSlope/Bank\nSmall Space\nWalkways`.
  - Added the RHS page title + CORR, RHS Position `Full sun`, and the RHS pollinator badge.
- Large-flowered Tickseed
  - common_name changed. name_note restored.
  - toxicity_detail rewritten with no value change. It had quoted the whole tag row as a space-joined string, but the
    page renders each tag as its own badge. It now names the three non-toxic tags singly, as b89 did.
- Siberian Iris
  - name_note restored (the audit's Siberian Iris version), citing the stacked list `Siberian Flag\nSiberian Iris` and
    the RHS subtitle `Siberian flag`.
  - toxicity_detail restored in the audit's wording. Added the audit's citations (a)-(e), the Poison block heading and
    `#contact dermatitis`. Completed the RHS Pets sentence.
  - is_houseplant null -> false, citing zones 3a-8b and nine Landscape Location values.
  - is_edible false also cites RHS `Harmful if eaten.`
- Autumn Sage
  - name_note restored in the audit's wording with its five new citations. Added the RHS page title + CORR and the RHS
    subtitle `autumn sage`.
  - is_houseplant null -> false.
- White Gaura
  - outdoor_sun_exposure `['full_sun','part_shade']` -> `['full_sun']`, following the audit's flag. The drop rests on:
    - RHS Position `Full sun` only.
    - RHS Cultivation `Best grown in fertile, moist but well-drained soil in full sun; but dry soils and partial shade
      tolerated`.
    - NC State's `#partial shade tolerant` tag.
    - NC State's `It prefers full sun and will tolerate heat and humidity.`
    - MoBot `Sun: Full sun`, audit-reported and disclosed only.
  - name_note restored, citing the RHS subtitle `white gaura`, `Lindheimer's beeblossom`, `Gaura lindheimeri`, `This
    genus has changed from Gaura to Oenothera`, and NC State's 11-item stacked list.
  - is_houseplant null -> false. Added the RHS page title + CORR.
- Anise-scented Sage
  - common_name changed. name_note restored in the audit's wording.
  - is_houseplant null -> false. Added the RHS page title + CORR and RHS Moisture.
- Japanese Anemone
  - name_note restored in the audit's wording.
  - toxicity_detail restored in the audit's wording, with all seven Poison Part values (Bark kept) and the added
    sentence `#poisonous` tag.
  - Citations added: `Poison Severity:\nHigh` and `Causes Contact Dermatitis:\nYes`.
  - is_houseplant null -> false.
- Citation repairs (values unchanged)
  - NC State quotes with the label glued to the value were trimmed to the value:
    - Lavandin: Edibility, Attracts, Wildlife Value.
    - Anise-scented Sage: Soil Drainage, Attracts.
  - Single picks from multi-value fields were re-quoted as the whole field:
    - Iris: Soil Drainage (3 values); Play Value replaced by the Attracts field.
    - Spanish Lavender: Play Value (4 values).
    - Japanese Anemone: Soil Drainage (2 values).
    - White Gaura: Previously known as (2 values).
    - Coreopsis: two one-value RHS Position quotes merged into `Full sun, Partial shade`.
  - Quotes that glued separate elements were replaced:
    - RHS `Coreopsis grandiflora RHS Plant Profile` -> the page title.
    - RHS `Synonyms Lavandula hybrida ...` -> the whole Synonyms paragraph.
    - Gaura `'Whirling Butterflies' White sterile blooms` -> stacked on two lines.
  - Bare RHS `Correct` was relabelled CORR (Coreopsis, Iris).
  - soil_base claim labels that asserted an "in-ground" scope their quote lacked were relabelled, with a supporting
    citation added (Spanish Lavender, Iris, White Gaura).
  - Lavandin: the Wildlife Value sentence was ordered ahead of the one-word Attracts value, so the loader stores the
    sentence.

## Common names and accepted names
- Coreopsis grandiflora: Largeflower Tickseed -> **Large-flowered Tickseed**.
  - The audit flagged the researched name. It is the third entry of NC State's alphabetized list and no page leads
    with it.
  - RHS leads with large-flowered tickseed in both the subtitle and the page title. This follows the b87 Cosmos
    pattern, and the casing matches the landed Large-flowered Bellwort.
- Salvia guaranitica: Anise Sage -> **Anise-scented Sage**.
  - The audit flagged the researched name. RHS's subtitle and page title lead with anise-scented sage, which is also
    the name the batch asked for. NC State lists it second.
- Iris sibirica: kept **Siberian Iris**, although the audit flagged it.
  - NC State's Description opens with it, and the brief admits an NC State body-prose opener as a lead (precedent: b84
    Tomatillo, b89 Million Bells). The batch asked for this name.
  - Both pages' lists and titles put Siberian Flag first. That is disclosed in name_note and unknowns.
- Unchanged: Lavandin, Spanish Lavender, Autumn Sage, White Gaura, Japanese Anemone.
- No collisions with landed common names, checked by grep.
- No accepted-name change. Eriocapitella × hybrida keeps NC State's current name. RHS's `Anemone × hybrida` (Correct)
  genus split is disclosed in name_note.

## Audit requests I could not do
- **MoBot citations.** The audit proposed MoBot citations for Coreopsis (`Common Name: large-flowered tickseed`) and
  White Gaura (`Common Name: Lindheimer's beeblossom`, the "commonly called gaura" prose, and `Sun: Full sun`).
  - MoBot is not cached and refuses this machine. Under standing rule 4, nothing rests on it.
  - Their content appears only as audit-reported text in unknowns. The audit's White Gaura name_note clause about
    MoBot moved to unknowns.
- **Iris RHS Position quote.** The audit offered `Full sun\nPartial shade`. Those are two inline spans inside one
  element, not stacked elements, so I used the single-element card `Full sun, Partial shade` instead.
- **Iris flag-name contrast.** The optional sub-claim (citing Iris versicolor/virginica) was dropped, as the audit
  preferred.
- **Small fixes to the audit's own wording:**
  - Anise-scented Sage: "sizes the plant smaller" became "size figures differ". RHS's 39-59 in height sits inside NC
    State's 24-60 in.
  - Lavandin unknowns[5]: no longer lists is_houseplant as unsupported, since it is now false and cited.

## Decisions for the owner
1. **Siberian Iris vs Siberian Flag.** Both are defensible, and the audit left it to the lander. Switching to Siberian
   Flag is a one-line change.
2. **Japanese Anemone keeps "Bark" in the Poison Part list.** The batch note told the researcher to drop it. The audit
   and the brief's full-poison-block rule overrule that, and the corpus keeps Bark for other herbaceous plants. The
   mismatch is disclosed.
3. **The Eriocapitella / Anemone genus split** between NC State (current name) and RHS (Correct) is disclosed, not
   resolved.

NORMALIZATION string: written.
