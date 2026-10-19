# b93 landing: eight vegetables, herbs and fruit (2026-10-03)

The landed file is `app/data/verified/b93-edibles.json`. It is not committed. The repair script is `b93_repair.py` and
the scratch copy is `b93_landed_records.json`, both in this directory. All 8 species landed, none were withheld, and
0 were unverified.

## Checks
- `b93_repair.py`: generic_passes clean.
- `land_check.py b93_landed_records.json` ends `=== problems === none`. toxic_to_pets is true for Peppermint, Roman
  Chamomile, Japanese Plum and Borage on NC State's separate `Problem for Cats` / `Problem for Dogs` Problems values
  (Chamomile and Borage also on the `#problem for cats #problem for dogs #problem for horses` tag run), and for Runner
  Bean on RHS's Potentially harmful line `Pets (dogs): Raw pods/beans harmful if eaten`. Lemon Thyme, Broad Bean and
  Asian Pear stay null: no page names cats or dogs.
- `verify_quotes.py app/data/verified/b93-edibles.json`: `238 hit, 0 MISS, 0 inconclusive, 0 skipped (pdf/http/error)`.
  No MoBot or Clemson citation was landed, so nothing SKIPs.
- Stricter checks (scratchpad `b93land/`): every quote is a punctuation-preserving, whitespace-collapsed substring of
  its page text, except three whose only difference is the extractor's spacing around inline `<em>` elements
  ("(M. aquatica)", "(Vicia faba)"); each was confirmed against the raw HTML. All 54 newline-stacked quotes match
  consecutive rendered nodes, except the two "is often confused with:" modules, whose header line is one `<dt>`
  holding an `<em>` binomial (confirmed in the HTML).
- pytest invariants + ingest: 4126 passed, 1 failed, `assert 7417 == 7157`. b93 adds 91 claims (`batch_claims.py`:
  8 records, 91 claims, none unsupported). The other 169 come from two concurrent, uncommitted landings,
  `b90-houseplants.json` (85) and `b94-shrubs.json` (84). With b93 alone the total is 7248. A replica of the ingest on
  a scratch database shows only the count line fails: no unsupported field and no refusal for any b93 species, 8
  authorities, and the Dracaena check passes.
- Page cache: RHS 11050 (Mentha × piperita) and 105463 (Vicia faba), which the audit read but the records never
  cited, were fetched through qc.py's normal path (www.rhs.org.uk allowed). Nothing in the cache was edited, moved
  or deleted. MoBot's Borago page failed (ProxyError, then ConnectError with the host allowed), and failed fetches
  are not cached.

## finish() table
```
Peppermint                 acc=Mentha × piperita house=False toxic=True sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=35 unk=12
Lemon Thyme                acc=Thymus × citriodorus house=False toxic=None sun=['full_sun'] drain=None water=None ph=None/None base=garden_bed cites=24 unk=12
Runner Bean                acc=Phaseolus coccineus house=False toxic=True sun=['full_sun'] drain=moderate water=keep_moist ph=None/None base=garden_bed cites=37 unk=11
Broad Bean                 acc=Vicia faba house=False toxic=None sun=['full_sun'] drain=moderate water=None ph=None/None base=garden_bed cites=41 unk=10
Roman Chamomile            acc=Chamaemelum nobile house=False toxic=True sun=['full_sun', 'part_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=36 unk=8
Japanese Plum              acc=Prunus salicina house=False toxic=True sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=22 unk=10
Asian Pear                 acc=Pyrus pyrifolia house=False toxic=None sun=['full_sun', 'part_shade'] drain=None water=None ph=None/None base=garden_bed cites=16 unk=14
Borage                     acc=Borago officinalis house=False toxic=True sun=['full_sun', 'part_shade'] drain=None water=None ph=None/None base=garden_bed cites=27 unk=12
```

## The standing rules, as applied
- Rule 2 (edibility). All eight are real food plants and land is_edible true, each with the whole condition its
  pages give in unknowns. Runner bean: RHS "Raw pods/beans harmful if eaten." and NC State "In large amounts, the raw
  or undercooked beans can cause severe nausea, vomiting, and diarrhea." -- eat no raw pods or raw or undercooked
  beans. Broad bean: favism in genetically predisposed people, with NC State's two differently scoped statements
  (eating the beans or walking a flowering field; excessive raw seed or pollen) and Flowers and Fruits (the pod) as
  poison parts. Borage: "should only be usred sparingly as liver damage can occur", PA-free seed oil only, and the
  Poison Symptoms' pyrrolizidine alkaloids. Roman chamomile: dried flowers for tea, one cup a day, not in pregnancy.
  Peppermint: vomiting and diarrhea with large ingestions. Japanese plum and Asian pear: no page names a toxic part,
  seed or kernel hazard, and no cyanide wording was imported from the landed Prunus, Pyrus or Malus records. No
  citation labelled is_edible quotes a toxicity sentence; each is_edible record's first citation is its food
  statement.
- Rule 3 (size). Runner Bean lands `climbs: true` (NC State: "because it is a vine, provide poles or other support for
  the plant to climb on", Climbing Method Twining; RHS: "a green-leaved twining climber reaching 3m"), so its NC State
  height of 96-144 in lands as reach. No other species climbs. All sizes are inches from the species' own page.
- Rule 4 (MoBot/Clemson only on a cache HIT). Only Borage cited MoBot, eight times. MoBot refuses this machine, so all
  eight citations were removed, Borage's water_regime (which rested on MoBot alone) was nulled, the MoBot sentences
  left name_note and toxicity_detail, and the page's content as the researcher and auditor read it is disclosed in one
  unknowns line.

## Values changed or restored
- Peppermint: name_note (removed on audit) restored in the audit's wording, with five new name_note citations (RHS
  11050's H1, Name Status, page title and Other common names; NC State's list). soil_ph_min/max stay null (RHS pH
  "Acid or Alkaline or Neutral"); the old pH citation is relabelled "soil pH disclosure" beside RHS's and NC State's
  pH fields. is_houseplant null -> false (zones 5a-9b, Landscape Theme, RHS locations). toxicity_detail's last
  sentence now says RHS 11050 has no toxicity field and files it under "Herbs - Culinary" (cited). RHS Correct + page
  title added for the accepted name. Quotes: the parentage sentence re-quoted as rendered; "Attracts:" cut to
  "Pollinators". unknowns 0, 2, 5 and 9 replaced with the audit's wording; an is_edible condition line added.
- Lemon Thyme: name_note restored in the audit's wording plus its optional Previously known as sentence (cited).
  soil_drainage stays null; the three "soil_drainage fast" citations were dropped, among them RHS's stock Thymus
  Cultivation paragraph. is_houseplant null -> false. NC State's Edibility field became the first is_edible citation;
  two is_edible labels were corrected. The RHS accepted-name pair is relabelled to say RHS writes the binomial
  without the sign. unknowns 2 and 7 replaced; a no-parent-page line added.
- Runner Bean: name_note restored in the audit's wording, its last sentence ("Nothing is taken from the vulgaris
  record.") moved to unknowns as a record-sourcing remark, plus the RHS Other common names citation. toxicity_detail
  (removed on audit; the original text did not survive the audit step) rebuilt in the sources' words from the cited
  RHS and NC State text, ending in the audit's corrected sentences. climbs absent -> true (above). water_regime
  keep_moist kept but re-cited from NC State's soil adjective to RHS's guide: "Runner beans are thirsty plants and crop
  best when their roots have plenty of moisture, so regular watering is usually required, especially once they start
  to flower and form pods."; the RHS Moisture citation for it was dropped. is_houseplant null -> false. soil_base adds
  RHS's "do best in the ground". Quotes: Plant Type, Attracts, Soil Drainage and RHS Position and Moisture splices cut
  to values; the NC State <title> parentheticals behind two "Common Name(s) list" claims swapped for the stacked lists
  (coccineus and vulgaris). unknowns 0, 1, 4, 6 and 7 replaced.
- Broad Bean: name_note and toxicity_detail (both removed on audit) restored in the audit's wording with their 16
  verified citations; the favism quote extended to the full Description run. soil_drainage null -> moderate on RHS
  105463: "Does best in a sunny, sheltered position with fertile, moist but well drained soil, though most soils will
  produce an adequate crop." and Moisture "Moist but well–drained or Well–drained" (the audit's verified reading;
  NC State's Good Drainage / Occasionally Dry with clay and saline tolerance is not fast). mature_spread_in null ->
  3.9-19.7 on RHS Max Spread "0.1-0.5 metres" (NC State gives no spread). is_houseplant null -> false. Accepted name:
  RHS 105463 page title + Correct added. Added corroboration: RHS Position "Full sun", NC State Attracts "Bees /
  Pollinators", RHS's in-ground row spacing. unknowns rewritten in the audit's wording (edibility, spread, pages read,
  the 24-72 in height against RHS's lower figures, houseplant/fertilize).
- Roman Chamomile: toxicity_detail (removed on audit) restored in the audit's exact value, plus RHS's "Herbs -
  Culinary". The common_name citation that quoted RHS's Other common names was replaced by NC State's Description
  opener "Roman chamomile is a low growing herbaceous perennial in the Asteraceae (daisy) family.", and name_note (not
  removed) now rests the lead on it instead of "appears in both". is_houseplant null -> false. Quotes: the truncated tag
  run restored to all 31 tags; the often-confused module quoted whole; the title parenthetical behind a "Common Name(s)
  list" claim swapped for the stacked list; RHS Synonyms and Position labels cut; the soil_base quote replaced by the
  groundcover sentence (page typo "children's grade" kept). unknowns 1 replaced; edibility and houseplant lines updated.
- Japanese Plum: name_note restored in the audit's wording, citing RHS 147706's page title and NC State's Description
  opener. common_name had no citation labelled with it; RHS's page title now carries it. Accepted name: RHS Correct +
  page title added. is_houseplant null -> false. toxicity_detail's last sentence "No other admissible source was
  consulted for toxicity." -> "RHS's dedicated Prunus salicina page (plant 147706) carries no toxicity or pet-hazard
  field." soil_base adds Plant Type "Edible / Tree". unknowns 0 and 4 replaced; an is_edible line added.
- Asian Pear: name_note restored in the audit's wording plus the stacked Common Name(s) citation. The accepted-name
  quote (an insect-module heading) replaced by the H1 "Pyrus pyrifolia". is_houseplant null -> false (Plant Type,
  zones, spacing sentence). soil_base relabelled and given the spacing sentence. unknowns 10-13 replaced.
- Borage: name_note restored in the audit's wording minus its MoBot sentence, plus the stacked list citation.
  soil_drainage moderate -> null and water_regime dry_surface_between -> null (decisions below). Accepted name: the
  label-glued, space-joined synonym quote replaced by the H1 "Borago officinalis" and the stacked synonyms. is_edible
  adds "The stems and tender leaves are edible and taste and smell like cucumber although the leaves lose their flavor
  when they are dried."; is_houseplant false kept with a zones citation added. Quotes: Plant Type and Soil Texture
  labels cut; the Problems field moved ahead of the tag run for toxic_to_pets. unknowns rewritten without MoBot.

## Common names and accepted names
- All eight researched names were kept: Peppermint, Lemon Thyme, Runner Bean (RHS's lead; NC State's list opens on
  Aztec Bean and its prose says Snap Beans, the Green Beans name), Broad Bean (both RHS pages lead with it; Fava Bean
  is an alternate in NC State's list), Roman Chamomile (NC State's Description opener), Japanese Plum (RHS's lead and
  NC State's Description), Asian Pear (NC State's Description; Apple Pear opens its list) and Borage. None collides with
  a landed common_name or with b90, b91, b92 or b94; covered.py reports every binomial clean.
- No accepted-name change. Thymus × citriodorus keeps its hybrid sign on NC State's title; RHS writes Thymus
  citriodorus (two profiles, Name Status Correct) and NC State's own prose says "DNA testing has now determined it to
  be a distinct species." Disclosed in name_note.

## Could not do
- Missouri Botanical Garden refuses this machine, so its Borago, Thymus, Mentha and Chamaemelum pages are not cited;
  the figures the researcher and auditor read there appear only as disclosed readings in unknowns.
- Asian Pear rests on NC State alone. The researcher's RHS attempts were slug URLs that 404; no RHS id-based search was
  run at landing (Japanese plum's RHS page turned out to exist only under its id).
- No page says broad beans must be cooked. The record carries what the pages say (favism wording, the raw seed, RHS's
  young pods "for cooking and eating whole"); no cooking instruction was added beyond them.

## Decisions for the owner
- Borage soil_drainage landed null although the audit let moderate stand. NC State's Good Drainage + Occasionally Dry,
  with clay accepted and no moist wording, meets neither the brief's moderate nor its fast; the same batch's Lemon
  Thyme audit ruled exactly that. Note the corpus already lands that NC State pair as fast six times (b23 Showy
  Stonecrop, b79 Scaly Blazing-star, b82 Lamb's Ear, b84 Lemon Balm, b87 Bush Lily and Cheddar Pink), while the b93
  batch notes call a
  clay-tolerant plant with it not fast. One rule for this pair would settle both.
- Thymus × citriodorus: if RHS's Name Status and NC State's DNA sentence should win over NC State's title, the accepted
  name would become Thymus citriodorus.
- Broad Bean soil_drainage moderate and spread 3.9-19.7 in were added at landing from the audit's verified RHS 105463
  text; the research record had both null.

NORMALIZATION: written.
