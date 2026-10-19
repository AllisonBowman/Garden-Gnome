# b92 landing: eight annuals, bedding and container plants (2026-10-03)

The landed file is `app/data/verified/b92-annuals.json`. It is not committed. The repair script is `b92_repair.py` and
the scratch copy is `b92_landed_records.json`, both in this directory. All 8 species landed, none were withheld, and
0 were unverified.

## Checks
- `b92_repair.py`: generic_passes clean.
- `land_check.py b92_landed_records.json` ends `=== problems === none`. toxic_to_pets: Barberton Daisy and Spider Flower
  are false on the tag run `#non-toxic for cats #non-toxic for horses #non-toxic for dogs`; Chinese Pink is true on the
  separate `Problem for Cats` and `Problem for Dogs` values. The other five are null (no source names cats or dogs).
- `verify_quotes.py app/data/verified/b92-annuals.json`: `190 hit, 0 MISS, 0 inconclusive, 0 skipped (pdf/http/error)`.
  No MoBot or Clemson citation was landed, so nothing SKIPs.
- Stricter check (scratchpad): every quote is a whole normalized substring of its page (not just the 80% run test), and
  every newline-stacked quote matches consecutive rendered lines. 190 citations, 0 flagged.
- `pytest tests/test_tranche_invariants.py`: 4024 passed.
- `pytest ... test_claim_ingest.py`: only the count test fails. b92 adds 77 claims (`batch_claims.py`: 8 records, 77
  claims, none unsupported).
  - First run (baseline 7003): `assert 7157 == 7003` = b92's 77 + another agent's b91 (77).
  - After the orchestrator committed b91 (baseline 7080): `assert 7241 == 7080` = b92's 77 + another agent's uncommitted
    `b94-shrubs.json` (84). With b92 alone on the current baseline the total is 7157.
- Page cache: fetched at landing through qc.py (normal fetch path, www.rhs.org.uk / edis.ifas.ufl.edu allowed): RHS 70682
  (Gerbera), 74267 (Dianthus chinensis (p,a)), 11156 (Mirabilis) and UF/IFAS FP465 (Pentas). Nothing in the cache was
  edited or deleted. Clemson (403) and MoBot (connection failure) were probed with curl only, which writes nothing.

## finish() table
```
Barberton Daisy            acc=Gerbera jamesonii house=True toxic=False sun=['full_sun', 'part_shade'] drain=moderate water=keep_moist ph=None/None base=garden_bed cites=23 unk=9
Mealycup Sage              acc=Salvia farinacea house=False toxic=None sun=['full_sun'] drain=moderate water=None ph=None/None base=garden_bed cites=16 unk=11
Egyptian Starcluster       acc=Pentas lanceolata house=True toxic=None sun=['full_sun', 'part_shade'] drain=None water=dry_surface_between ph=None/None base=None cites=22 unk=12
Chinese Pink               acc=Dianthus chinensis house=False toxic=True sun=['full_sun', 'part_shade'] drain=moderate water=None ph=6/None base=garden_bed cites=35 unk=11
Spider Flower              acc=Cleome houtteana house=False toxic=False sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=33 unk=11
Four-o'clock               acc=Mirabilis jalapa house=False toxic=None sun=['full_sun', 'part_shade'] drain=moderate water=None ph=None/None base=garden_bed cites=29 unk=12
Treasure Flower            acc=Gazania rigens house=False toxic=None sun=['full_sun'] drain=None water=dry_surface_between ph=None/None base=None cites=18 unk=11
Fan Flower                 acc=Scaevola aemula house=False toxic=None sun=['full_sun', 'part_shade'] drain=None water=None ph=None/None base=None cites=14 unk=14
```

## The rule that shaped this landing
Standing rule 4: a value may rest on Clemson or Missouri Botanical Garden only if verify_quotes HITs its quote in the
cache. Neither can be fetched from this machine (MoBot fails TLS; Clemson answers 403, and the Fan Flower factsheet is
already cached as http-403, which may not be removed). So no MoBot or Clemson citation was landed, no value or name_note
sentence rests on them, and every auditor browser reading of them is disclosed in unknowns as the auditor's reading.

## Values changed or restored
- Fan Flower water_regime: keep_moist was refuted on audit and stays null. The audit's repair, dry_surface_between, rested
  only on Clemson's "Allow the soil to dry out slightly before watering again to prevent root rot." The NC State citation
  ("Water regularly throughout growing season.") is relabelled as not evidence for keep_moist.
- Four-o'clock is_edible: null -> false, on RHS's Potentially harmful field "Harmful if eaten.  Wear gloves and other
  protective equipment when handling" and NC State's human-scoped Poison Symptoms for Roots and Seeds. No admissible page
  describes any part as food, so rule 2's true/null question never arises. The audit's MoBot citation was not landed.
- Four-o'clock toxicity_detail (removed on audit) restored in the audit's corrected wording, minus MoBot. It now cites
  NC State's whole Poison block as one run, plus RHS's Potentially harmful field. It says the sources differ on scope:
  NC State names only Roots and Seeds, and RHS names no part. MoBot's "All parts of this plant are poisonous if
  ingested." is disclosed in its own unknowns line.
- Chinese Pink toxicity_detail (removed on audit) restored in the audit's corrected wording. It adds RHS's handling
  warning "Humans/Pets: Skin allergen; wear gloves and other protective equipment when handling. ...", whose Pets
  scope names no animal. It also cites Poison Severity Low, Causes Contact Dermatitis Yes, the Plant Type values and the
  Ethnobotany harvest note.
- name_note restored in the audit's corrected wording for Barberton Daisy, Egyptian Starcluster, Chinese Pink, Spider
  Flower, Treasure Flower and Fan Flower, with one name_note citation per sub-claim. MoBot and Clemson sentences were
  dropped from the wording (Pentas, Chinese Pink, Treasure Flower, Fan Flower), as the audit allowed when they are not
  cited. Treasure Flower's note now grounds the name on NC State's list instead of MoBot. African Daisy (the list's first
  entry) also opens Gerbera's NC State list, which is cited, and Gazania is the bare genus.
- Four-o'clock name_note: new. NC State leads with Four-o'clock; RHS's page title and subtitle lead with marvel of Peru,
  and RHS lists "four o'clock flower" and "four o'clock plant" among its other names. The research rules want a
  name_note when sources split, and the audit's own wording refers to one.
- is_houseplant: null -> false, citing NC State's Plant Type or Landscape Location values (the landing gate refuses
  null). This applies to Mealycup Sage, Chinese Pink, Four-o'clock, Treasure Flower and Fan Flower.
- scientific_name_accepted: an RHS Name Status Correct + H1 pair was added for Barberton Daisy, Egyptian Starcluster,
  Four-o'clock, Treasure Flower and Fan Flower. Chinese Pink's RHS page, Dianthus chinensis (p,a), reads Name Status
  Unresolved, so that name rests on NC State's H1, and name_note says so.

## Common names
- Pentas lanceolata: researched as Egyptian Star Cluster, landed as **Egyptian Starcluster**. The audit flagged that no
  dedicated page leads with the spaced form. Egyptian Starcluster is the first entry of NC State's Common Name(s) list
  (in page-title order) and UF/IFAS FP465's species name ("pentas, Egyptian starcluster"). The researched spelling is
  NC State's second entry and RHS's second other common name. This overrides the batch note's spelling.
- The other seven keep their researched names: Barberton Daisy, Mealycup Sage, Chinese Pink, Spider Flower,
  Four-o'clock, Treasure Flower and Fan Flower. None collides with a landed common_name; covered.py finds each binomial
  only in b92.

## Audit repairs not applied, and how each record discloses it
- Fan Flower attracts_pollinators true and soil_drainage moderate: both rested only on the Clemson factsheet. Both stay
  null, and unknowns quotes Clemson's sentences as the auditor's reading, cached 403.
- Mealycup Sage part_shade: the audit counted MoBot's "Sun: Full sun to part shade" as a second structured field
  alongside RHS's "Full sun, Partial shade". Without MoBot, part shade is listed only by RHS, and NC State's North
  American Light field excludes it. So the value stays full_sun only, using the audit's fallback wording plus the reason.
- Every MoBot citation the audit proposed was left out: Salvia sun and size, Pentas name and sun, Dianthus name,
  Mirabilis toxicity and edibility, Gazania name, and Fan Flower name. Each reading is quoted in unknowns and attributed
  to the auditor.

## Other landing fixes (quotes and labels)
- Values replace label+value splices: Previously known as (Salvia, Cleome), Plant Type and Landscape Location (Cleome),
  Design Feature (Cleome), Soil Drainage (Cleome), and Attracts (Cleome). Dianthus's bare `Poison Part:` became
  `Poison Part:\nLeaves`. Dianthus's single "Good Drainage" now quotes both values of the two-value field.
- Four-o'clock: the prose drainage citation ("moist to occasionally wet, well-drained") now sits ahead of the bare
  "Occasionally Wet" value, so the loader pairs soil_drainage=moderate with the prose.
- Fan Flower's body-prose citation now quotes the Description's first sentence. Gerbera's size quotes carry their
  Height/Width words.
- Labels that claimed more than their quotes were narrowed. Four claims called the H1 the "page title" or "titled"
  (Gerbera, Dianthus, Pentas, Cleome). Two added an "in-ground" scope the quote lacks (Gerbera, Dianthus soil_base),
  and Mirabilis's soil_base label did the same.
- Stale research unknowns were rewritten wherever an RHS, UF/IFAS or MoBot page had been called unreadable or missing.

## Decisions for the owner
- Rule 4 cost three Fan Flower values and Mealycup Sage's part_shade. If MoBot/Clemson browser readings ever become
  admissible, the audit's repairs are ready: Fan Flower water_regime dry_surface_between, soil_drainage moderate and
  attracts_pollinators true; Mealycup Sage part_shade.
- Egyptian Starcluster versus the batch's Egyptian Star Cluster (see above).
- Four-o'clock is_edible false (not null), per the research rule and the corpus's "Harmful if eaten" landings.
- Pentas soil_drainage stays null though RHS's Moisture field reads "Moist but well–drained or Well–drained". The audit
  proposed no token, and NC State reads Good Drainage + Occasionally Dry. This is disclosed in unknowns.

NORMALIZATION: written.
