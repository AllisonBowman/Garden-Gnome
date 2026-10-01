# Landing brief for one research batch (bNN)

You are landing one batch of a cited plant-care catalog. Work ONLY inside
the checkout's garden-gnome/ directory (run every command from there
with `.venv/bin/python`). Never cd into /Users/allisonbowman/Developer/Garden-Gnome. Do not commit; the orchestrator commits.

## Inputs (all under SCRATCH = this pipeline directory, garden-gnome/scripts/catalog/pipeline/ -- use its absolute path)
- SCRATCH/bNN_records.json  -- the post-audit workflow result: records[], audit_summary[], unverified[]. Every audit finding is in
  each record's `unknowns` as a line containing " on audit" (refuted fields already nulled; common_name and outdoor_sun_exposure
  only FLAGGED; citation-level findings marked "CITATION-LEVEL").
- SCRATCH/bNN_dump.txt and SCRATCH/bNN_audit.txt -- the same, laid out for reading (make them: `.venv/bin/python SCRATCH/dump_batch.py bNN`).
- SCRATCH/repair_lib.py -- helpers: cite/edit/drop_cite/replace_unknown/drop_audit/url_of/src_of, generic_passes (assertions), finish().
- SCRATCH/example_repair_b74.py -- the exemplar: one block per species, auditor's CORRECTED WORDING used verbatim, then `finish(res, OUT, NORMALIZATION, scratch_path)`.
- SCRATCH/qc.py "<URL>" "<regex>" -- prints the page <title> and context windows from the SAME fetch+extract path
  the quote checker uses (newlines render as U+23CE). Use it to ground-truth every substitute quote before applying it.
- scripts/catalog/land_check.py <records.json>, scripts/catalog/verify_quotes.py <batch.json>, scripts/catalog/covered.py "Genus species".
- The rules the researcher and auditor were given are in the batch script SCRATCH/bNN-catalog-research.js (or bNN-resume.js) (researchPrompt / verifyPrompt).
  Read them: they define the enum tokens, the quote-provenance rules, the naming rules, the sun-list rules.

## What a landing does
Write SCRATCH/bNN_repair.py in the shape of b74_repair.py, run it, and iterate until all three checks are clean:
1. `.venv/bin/python SCRATCH/bNN_repair.py` -- generic_passes asserts must hold (they name the defect and the species).
2. `.venv/bin/python scripts/catalog/land_check.py SCRATCH/bNN_landed_records.json` -- must end "=== problems === none";
   read its toxic_to_pets dump: every true/false must rest on a quote that names cats and/or dogs.
3. `.venv/bin/python scripts/catalog/verify_quotes.py app/data/verified/bNN-<slug>.json` -- 0 MISS. SKIP is a host that refuses
   this machine (MoBot, ask.ifas) and is fine; INCONCLUSIVE is a page-level fetch failure -- say so in the note.
Then `.venv/bin/python -m pytest tests/test_tranche_invariants.py tests/test_claim_ingest.py -p no:cacheprovider -W ignore -o addopts="" -q`
(the ingest count test WILL fail with the new total; report the number `assert NEW == OLD` prints, do not edit the test).

## Rules that decide repairs (all from this catalog's history; break none)
- A refuted field is already null. Restore a value ONLY when the audit's own reasoning confirms the value and supplies verbatim
  page text; cite that text. Where the audit says a citation is defective but the value stands (CITATION-LEVEL), fix the citation
  (quote/claim/url) and keep the value. Where the audit says a sub-claim is WRONG, drop the sub-claim; never invent a citation.
- Every non-null field except scientific_name_given needs a citation whose claim contains the field name literally. name_note needs
  one per sub-claim. A bare RHS "Correct" needs a second citation naming the taxon (page title or H1) -- use CORR from repair_lib.
- Quotes: verbatim rendered text only. No markup, no entity text, no MoBot overlib/tooltip popup text (the "Common Names • a • b"
  form), no " | " pipe strings unless the claim calls it the page title, no NC State <dt> label glued to its <dd> value (quote the
  value; the Poison block is the one exception, quoted as the page's contiguous label/value run), no space-joined runs of stacked
  list items (newline-stack them), no truncated or extended tag lists ("Woody Plant" is the next label, not a Plant Type value).
  MoBot's "Sun: Part shade" / "Water: Medium" are single rendered nodes and are fine.
- common_name: the name a DEDICATED single-species page leads with (H1/title lead, first list item when the list order matches
  the page-title parenthetical, MoBot's Common Name: field, NC State body prose opener); never a sibling's name, an umbrella, or an
  "other names" entry. NC State's Common Name(s) lists are alphabetized -- never write that a list "marks no primary" or call an
  order an "artifact". Title-case the landed name (apostrophes kept). Check `grep -il "<name>" app/data/verified/*.json` for a
  collision with an already-landed common_name; on a collision, land under the next dedicated-page lead and say so in name_note.
- Species names: no author abbreviations; "Genus epithet", or "Genus × epithet" for a hybrid (U+00D7 MULTIPLICATION SIGN, space either
  side -- repair_lib normalises a source's "Genus ×epithet" to that form). Never strip the hybrid sign and never land a parent
  species in its place. scientific_name_accepted follows RHS Name Status Correct / NC State's
  current title; a reclassification is followed and disclosed. RHS URLs must have the epithet in the slug, never /wd/.
- outdoor_sun_exposure: keep only values a structured field or unconditional statement supports; drop a value one source lists
  when the other North American structured field excludes it or a species scorch/flop warning contradicts it; disclose in unknowns.
- soil_drainage: moderate = "moist but well-drained" / NC State Good Drainage + Moist / tags spanning both Occasionally Dry AND
  Occasionally Wet; moisture_retentive only for an explicit consistently-wet cultivation REQUIREMENT (a rain-garden siting label is
  not one); fast only for sharp/sandy with no wet tolerance. Cite NC State's structured Soil Drainage field before any wet token.
- water_regime: from a WATERING statement or structured moisture field, never a soil adjective, habitat sentence, or drought trait;
  MoBot "Water: Medium" never supports keep_moist; "Medium to wet" is the second-wettest band and is consistent with it.
- toxic_to_pets: true/false only on a statement naming cats and/or dogs (NC State Problem for Cats/Dogs values or #problem-for tags;
  RHS "Pets (dogs, cats)"; explicit non-toxic-for-dogs/cats tags for false). Unscoped "Pets:" lines and horse/livestock/human blocks
  support neither. toxicity_detail reproduces the FULL poison block (parts, severity + heading, symptoms, principle, handling
  warning, co-listed tags) in the source's words and discloses any source disagreement.
- Nulls are JSON null. No key outside the 35-field schema. is_houseplant false for landscape plants unless a source frames it as one.
- The `unknowns` array keeps the researcher's non-audit entries (fix any the audit corrected), then drop_audit() strips audit lines.

## Before you start
Generate the dumps yourself: `.venv/bin/python SCRATCH/dump_batch.py bNN` (needs SCRATCH/bNN_records.json).

## Report back (this is all the orchestrator reads -- keep it UNDER 40 LINES; put the long version in SCRATCH/bNN_summary.md)
1. The final `finish()` table (one line per species) verbatim.
2. Every value you changed or restored, one line each: species, field, old -> new, and the page text it rests on.
3. Every common_name decision (researched name -> landed name, why), and any accepted-name change.
4. Anything the audit asked for that you could NOT do (page unreachable, substitute not on the page) and how the record discloses it.
5. The verify_quotes summary line and the land_check tail, verbatim, and the new claim count from the ingest test.
6. The NORMALIZATION string you wrote into the batch file: say only 'written' -- it is in the file.
One line per species for items 2-4; no prose paragraphs; no restating the brief.
