export const meta = {
  name: 'b80-catalog-research',
  description: 'Research + adversarially verify 8 species for the plant-care claim catalog (b80, native coastal dune and salt-marsh plants)',
  phases: [{ title: 'Research', model: 'sonnet' }, { title: 'Verify', model: 'opus' }],
}

const DOMAINS = [
  'plants.ces.ncsu.edu', 'hgic.clemson.edu', 'plantfinder.mobot.org',
  'www.missouribotanicalgarden.org', 'edis.ifas.ufl.edu', 'ask.ifas.ufl.edu',
  'www.rhs.org.uk', 'extension.psu.edu', 'extension.umd.edu',
  'fieldreport.caes.uga.edu',
]

const SPECIES = [
  { common: "Sea Oats", latin: "Uniola paniculata", note: "this catalog's first Uniola; a protected dune grass in several states -- capture any harvest or protection statement exactly as stated; salt tolerance captured exactly as stated. Confirm species-specific content on a dedicated single-species page, never a genus-level, cultivar, or multi-species page." },
  { common: "American Beachgrass", latin: "Ammophila breviligulata", note: "this catalog's first Ammophila; a dune stabilizer -- soil_drainage fast only on sharp/sandy drainage with no moisture span. Confirm species-specific content on a dedicated single-species page, never a genus-level, cultivar, or multi-species page." },
  { common: "Seaside Goldenrod", latin: "Solidago sempervirens", note: "confirm species-specific content, not S. canadensis or the ragweed confusion; salt tolerance captured exactly as stated. Confirm species-specific content on a dedicated single-species page, never a genus-level, cultivar, or multi-species page." },
  { common: "Bushy Seaside Oxeye", latin: "Borrichia frutescens", note: "this catalog's first Borrichia; a salt-marsh subshrub -- moisture_retentive only on a cultivation REQUIREMENT, and a salt-flat habitat sentence is not a drainage value. Confirm species-specific content on a dedicated single-species page, never a genus-level, cultivar, or multi-species page." },
  { common: "Smooth Cordgrass", latin: "Spartina alterniflora", note: "this catalog's first Spartina; some sources file it as Sporobolus alterniflorus -- disclose any synonymy exactly as the source states it; an intertidal species, so a tidal-inundation statement is not a watering instruction. Confirm species-specific content on a dedicated single-species page, never a genus-level, cultivar, or multi-species page." },
  { common: "Groundsel Tree", latin: "Baccharis halimifolia", note: "this catalog's first Baccharis; naming may split between Groundsel Tree, Eastern Baccharis and Sea Myrtle; it is regulated as invasive in parts of Europe -- capture that only as the admissible sources state it. Confirm species-specific content on a dedicated single-species page, never a genus-level, cultivar, or multi-species page." },
  { common: "Dwarf Palmetto", latin: "Sabal minor", note: "this catalog's first Sabal; confirm species-specific content, not Sabal palmetto (the tree-form state tree) or Serenoa repens. Confirm species-specific content on a dedicated single-species page, never a genus-level, cultivar, or multi-species page." },
  { common: "Saw Palmetto", latin: "Serenoa repens", note: "this catalog's first Serenoa (a monotypic genus); confirm species-specific content, not Sabal minor; sharp petiole spines are a handling hazard -- reproduce any handling warning exactly as stated, and any medicinal-extract statement only as an admissible source frames it. Confirm species-specific content on a dedicated single-species page, never a genus-level, cultivar, or multi-species page." },
]

const FIELD_LIST = [
  'common_name', 'scientific_name_given', 'scientific_name_accepted', 'name_note',
  'is_houseplant', 'toxic_to_pets', 'toxicity_detail',
  'chill_damage_f', 'cool_rest_note', 'day_f_min', 'day_f_max', 'night_f_min', 'night_f_max',
  'humidity_need', 'humidity_pct_min', 'humidity_pct_max',
  'light_fc_min', 'light_fc_good', 'direct_sun_hours_max', 'outdoor_sun_exposure',
  'soil_base', 'soil_drainage', 'soil_ph_min', 'soil_ph_max',
  'water_regime', 'water_dry_down_target', 'water_check_depth_cm',
  'water_growing_days_est', 'water_dormant_days_est', 'water_estimate_basis',
  'fertilize_interval_days', 'fertilize_active_months', 'fertilize_strength',
  'unknowns', 'citations',
]

const RECORD_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    common_name: { type: 'string' }, scientific_name_given: { type: 'string' },
    scientific_name_accepted: { type: ['string', 'null'] }, name_note: { type: ['string', 'null'] },
    is_houseplant: { type: ['boolean', 'null'] }, toxic_to_pets: { type: ['boolean', 'null'] },
    toxicity_detail: { type: ['string', 'null'] }, chill_damage_f: { type: ['number', 'null'] },
    cool_rest_note: { type: ['string', 'null'] },
    day_f_min: { type: ['number', 'null'] }, day_f_max: { type: ['number', 'null'] },
    night_f_min: { type: ['number', 'null'] }, night_f_max: { type: ['number', 'null'] },
    humidity_need: { type: ['string', 'null'], enum: ['low', 'average', 'high', null] },
    humidity_pct_min: { type: ['number', 'null'] }, humidity_pct_max: { type: ['number', 'null'] },
    light_fc_min: { type: ['number', 'null'] }, light_fc_good: { type: ['number', 'null'] },
    direct_sun_hours_max: { type: ['number', 'null'] },
    outdoor_sun_exposure: { type: ['array', 'null'], items: { type: 'string', enum: ['full_sun', 'part_sun', 'part_shade', 'full_shade'] } },
    soil_base: { type: ['string', 'null'], enum: ['standard_potting', 'chunky_aroid', 'cactus_succulent', 'ericaceous', 'orchid_bark', 'african_violet', 'semi_hydro', 'garden_bed', null] },
    soil_drainage: { type: ['string', 'null'], enum: ['fast', 'moderate', 'moisture_retentive', null] },
    soil_ph_min: { type: ['number', 'null'] }, soil_ph_max: { type: ['number', 'null'] },
    water_regime: { type: ['string', 'null'], enum: ['keep_moist', 'keep_barely_moist', 'dry_surface_between', 'dry_thoroughly_between', null] },
    water_dry_down_target: { type: ['string', 'null'] }, water_check_depth_cm: { type: ['number', 'null'] },
    water_growing_days_est: { type: ['number', 'null'] }, water_dormant_days_est: { type: ['number', 'null'] },
    water_estimate_basis: { type: ['string', 'null'] },
    fertilize_interval_days: { type: ['number', 'null'] },
    fertilize_active_months: { type: ['array', 'null'], items: { type: 'number' } },
    fertilize_strength: { type: ['string', 'null'], enum: ['full', 'half', 'quarter', null] },
    unknowns: { type: 'array', items: { type: 'string' } },
    citations: { type: 'array', items: { type: 'object',
      properties: { claim: { type: 'string' }, source: { type: 'string' }, url: { type: 'string' }, quote: { type: 'string' } },
      required: ['claim', 'source', 'url', 'quote'] } },
  },
  required: FIELD_LIST,
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: { findings: { type: 'array', items: { type: 'object',
    properties: { field: { type: 'string' }, refuted: { type: 'boolean' }, reasoning: { type: 'string' } },
    required: ['field', 'refuted', 'reasoning'] } } },
  required: ['findings'],
}

function researchPrompt(s) {
  return `You are researching a single plant species for a plant-care app's evidence-backed catalog. Research ONLY "${s.common}" (${s.latin}).

${s.note}

Use ONLY these admissible authority domains -- no other source may be cited, no matter how reputable it seems:
${DOMAINS.map(d => `- ${d}`).join('\n')}

Produce a single JSON record with EXACTLY these fields and no others: ${FIELD_LIST.join(', ')}. Do not add any extra field, placeholder, or scaffolding key beyond this exact list, even if empty or null. common_name must always be a real, non-null, well-supported name for this exact species -- never invent or guess it, but also never leave it blank; if two admissible sources differ on which name is primary, pick the one led by the source(s) with a dedicated page for this exact taxon (for a hybrid, the hybrid's own page counts; a parent species' page does not) (its actual title/H1/lead name, or the FIRST item of its common-name list), never a name the page assigns to a sibling species, never one that only appears inside a multi-species umbrella term or a secondary "other common names" field. Say so in name_note when sources split.

Rules, all mandatory:
1. EVERY non-null field except scientific_name_given must be supported by at least one citation in the citations array whose "claim" text literally contains that field's name as a substring -- including scientific_name_accepted (cite RHS's "Name Status Correct" or the dedicated page's binomial). If name_note is non-null, it MUST have its own citation whose claim label contains the literal string "name_note" for EVERY distinct sub-claim bundled into its prose, each citation's quote actually saying what that sub-claim says (a Position-field quote does not support a common-name claim); a cross-species contrast needs a citation to the other species' page too. Quote a source's structured "is often confused with:" module exactly as the page renders it (it begins with the binomial). Describe a source's structure accurately -- if a page carries both a single Common Name line and a longer Common Names list, say so. Never restate a source's fact in a way that changes its direction (a hedge must survive; a relationship must not be inverted; "two of three sources" must actually be two of three).
2. toxic_to_pets tracks risk to CATS and/or DOGS specifically. A citation naming only a different animal (rabbits, birds, horses, livestock) or a wholly unscoped "keep away from pets" mention naming no animal at all does NOT support toxic_to_pets=true. A citation naming only one of cats/dogs (not both) is still sufficient. If the only toxicity evidence you find is scoped to non-cat/dog animals, leave toxic_to_pets null and explain in unknowns. toxicity_detail must reproduce a source's symptom list completely, quote the FULL poison-part list (never truncate "Leaves, Roots, Stems" to "Leaves"), carry every co-listed tag and plant-type trait in the same block, carry any handling warning, reproduce preparation/edibility instructions with their exact times or conditions rather than paraphrasing them away, state which source and which heading a severity rating comes from (NC State's Poison block is human-scoped; its Problem-for-Cats/Dogs tags are separate), use the source's own words for a hazard, never add a scope the source does not state, and disclose it when admissible sources disagree on scope (fruit-only vs. unrestricted) or edibility.
3. If you cannot find admissible-source support for a field, leave it null. Do not guess, infer from general plant knowledge, or borrow from a related species/genus.
4. THESE FIELDS ARE STRICT ENUMS -- the value must be EXACTLY one of the listed tokens, never a sentence or paraphrase:
   - soil_base: standard_potting | chunky_aroid | cactus_succulent | ericaceous | orchid_bark | african_violet | semi_hydro | garden_bed
   - soil_drainage: fast | moderate | moisture_retentive. "Moist but well-drained" is the MIDDLE of this scale (moderate), not the wet end. fast = sharp/sandy drainage, dry-tolerant, no wet-tolerance described. moderate = "moist but well-drained", NC State's bare Good Drainage + Moist pair, tags spanning BOTH occasionally-dry AND occasionally-wet, or UF/IFAS "well-drained to occasionally wet". moisture_retentive = a source explicitly wants consistently wet/boggy soil. A bare "well-drained" alone is ambiguous -- leave null. If a same-source root-rot or waterlogging warning contradicts a wet reading, the warning wins. If two admissible sources genuinely disagree, leave null and say so.
   - water_regime: keep_moist | keep_barely_moist | dry_surface_between | dry_thoroughly_between. Read a WATERING statement or a structured moisture field, not a bare soil adjective, not a wild-habitat description, and not a drought-tolerance trait. A structured "Water: Medium" is mid-scale and never supports keep_moist -- cite it only as a disclosed counterpoint. Prefer the species-specific page over a genus-level guide and disclose any conflict in unknowns.
   - humidity_need: low | average | high
   - fertilize_strength: full | half | quarter (a dilution/strength fraction, NOT an NPK formulation or per-area application rate)
5. outdoor_sun_exposure is a list of zero or more of: full_sun, part_sun, part_shade, full_shade. NC State's "Dappled Sunlight" tag maps to part_shade; "light shade" maps to part_shade or part_sun, never brighter than the source says. Include only values a source's structured field or an UNCONDITIONAL statement supports; a conditional or tolerance aside does not add a value; a value listed by one source but excluded by the structured sun fields of the other two (typically a UK-calibrated RHS full sun for a North American woodland plant) is left out and disclosed in unknowns. direct_sun_hours_max must come from species-specific prose, never from the generic hour range inside NC State's site-wide light-category legend.
6. Soil pH: NC State's "Alkaline (>8.0)" and "Acid (<6.0)" bands are open-ended -- do not set a ceiling or floor from them. A ceiling read off the closed top of a "Neutral (6.0-8.0)" band must be checked against RHS's pH field; if RHS lists alkaline soils as acceptable, leave soil_ph_max null and say so. For an in-ground shrub, tree or perennial, leave water_dry_down_target and the day-interval fields null unless a source frames watering that way.
7. All null values must be real JSON null -- never the literal string "null" or an empty string "".
8. Every citation's "quote" must be a real, verbatim excerpt you can point to on the source page -- never fabricated, never paraphrased-as-verbatim (copy the page's own sentence, not a restatement of it), never a synthesized label presented in quotation marks, never a list of structured tags the page does not actually carry, never cropped so that a handling warning, a dose sentence, a poison part or a contradicting clause is dropped, and never containing stray separator characters. Every quote is mechanically checked against the live page after you finish: a quote that is not on the page will be found.
9. Never derive a numeric day-interval from named calendar dates or word-based cadences unless the source states the number literally. For chill_damage_f, a regional growing-range limit or a hardiness-zone/survival rating is NOT a damage-onset temperature -- if no source states an onset figure, leave null.
11. NEVER attribute an editorial convention to a source. NC State's Common Name(s) lists are alphabetized and rank nothing -- never write that a list "marks no primary", "designates no primary", or that its first entry is "an ordering artifact". State only what the page shows: the list is alphabetized, and whether its order matches the page-title parenthetical.
12. QUOTE PROVENANCE, mechanically checked at landing. (a) MoBot's "Common Names" popup text lives only inside an overlib onmouseover attribute as entity-encoded markup -- NEVER quote it, however cleaned up, and never call it "rendered". MoBot's Noteworthy Characteristics prose carries the same alternate names and IS quotable. (b) A pipe-joined "Binomial | common name" string is the browser <title>/og:title metadata, not a rendered subtitle: quote it only when your claim calls it the page title, and quote the bare subtitle text when your claim says subtitle. (c) Never concatenate a label and its value into one quoted string when the page renders them as separate elements -- and a bare one-word value like RHS's Name Status "Correct" evidences nothing alone, so pair it with a second citation whose quote names the taxon (the page title or H1). (d) Never join separately-stacked list items into one space-joined run; quote the stacked field with newlines between values, or quote the page-title parenthetical that renders them comma-separated.
13. NEVER truncate a structured tag list, and never extend one either. NC State's "Plant Type" field is followed immediately by a DIFFERENT label, "Woody Plant Leaf Characteristics" -- a naive text scrape merges them, so "Woody Plant" is usually NOT a Plant Type value. Count the values as the page renders them.
14. A scientific name carries no authorship. It is either a bare binomial "Genus epithet" or, for a hybrid, "Genus × epithet" written with U+00D7 MULTIPLICATION SIGN and a space either side. RHS renders author abbreviations in its H1 (e.g. "Adiantum pedatum L."); the abbreviation is authorship, not part of the name, so never copy it into scientific_name_accepted. The hybrid sign IS part of the name: normalise a source's "Genus ×epithet" to "Genus × epithet" and a source's ASCII "Genus x epithet" to the multiplication sign, but NEVER drop the sign, never replace the hybrid with one of its parent species, and never re-file it as a cultivar of a parent. If the admissible sources genuinely disagree about whether the taxon is a hybrid, record the given name unchanged and say so in name_note.
15. SCOPE DISCIPLINE. A sentence you rule inadmissible for one field (RHS's "Under glass grow in..." run, a genus-level Cultivation paragraph, a site-wide Hardiness-ratings legend) cannot supply the next field either. Before using an RHS Cultivation paragraph, ask whether the same text appears on a sibling species' RHS page -- genus boilerplate is not species evidence. Quote the species page's bare hardiness rating (e.g. "H6"), never the shared ratings legend. A conditional clause ("foliage stays evergreen when grown indoors as a houseplant") is not a culture recommendation.
16. NC State renders "Landscape Location" and "Landscape Theme" as SEPARATE fields -- never merge them into one quoted list, and never drop an entry from either.

10. Use the unknowns array for anything decision-relevant that doesn't fit a schema field, and to explain any field deliberately left null.

Return ONLY the JSON record.`
}

function verifyPrompt(record, s) {
  return `You are an adversarial auditor reviewing a researched plant-care record for "${s.common}" (${s.latin}) before it is landed as cited evidence in a plant-care app. Your job is to find and refute anything wrong -- do not rubber-stamp.

Here is the record to audit:
${JSON.stringify(record, null, 2)}

First, check the record's own field names against this exact allowed list: ${FIELD_LIST.join(', ')}. Flag any stray key as its own finding with refuted: true.

Second, sanity-check common_name: is it the name an admissible source's DEDICATED page for this exact taxon, hybrid or species, actually leads with (H1/title, or the first item of its common-name list), not a name the page assigns to a sibling species, not one bundled inside a multi-species umbrella term, and not a later entry in an "other common names" list? If not, refute it and say which name the dedicated source(s) actually lead with (common_name must never land null). A hybrid's own page IS the dedicated page for that taxon; do not demand a parent species' page in its place.

Third, for outdoor_sun_exposure (a list field), if only some entries are well-supported, refute and identify ONLY the specific bad entry/entries -- say which should stay and which should go. A value resting on a conditional or tolerance clause, contradicted by a species-specific scorch/burn warning, or excluded by the structured sun fields of the other sources, should go.

Fourth, for chill_damage_f and soil_ph_min/max: refute a survival/range/zone figure used as a damage onset; refute a ceiling or floor read off an open-ended NC State band; and check a closed-band ceiling against RHS's pH field.

Fifth, for EVERY citation whose quote is load-bearing (numeric values, enum-defining tag lists, toxicity claims, anything in quotation marks), fetch the live URL and compare the quote against the actual page content. A synthesized label presented as a quote, a paraphrase of the page's sentence, a truncated poison-part list, or a list of structured tags the page does not carry is a defect even when the underlying facts are true -- call these out explicitly, and where the facts ARE true, quote the page's real sentence in your reasoning so it can be substituted at repair time.

Sixth, VERIFY YOUR OWN SUBSTITUTES. When you propose replacement text for a defective quote, you must have seen that exact string on the live page yourself. A previous audit insisted an NC State Plant Type field carried a fifth value "Woody Plant"; it does not -- that string begins the NEXT label, "Woody Plant Leaf Characteristics". Count a structured field's values as the page renders them, and quote your substitute verbatim in your reasoning so it can be applied mechanically.

Seventh, emit CITATION-LEVEL findings. When a citation is defective but the field's VALUE stands, do not refute the field -- emit a separate finding whose "field" is "citations[N]" (the array index) with refuted: true, so the defect is repaired at landing without nulling a good value. Use the same form for a defective unknowns entry ("unknowns[N]").

Eighth, check the record against the quote-provenance rules the researcher was given: no overlib/tooltip text, no <title> metadata presented as a rendered subtitle, no label+value concatenation, no bare one-word field value standing alone for a name claim, no space-joined run of separately-stacked list items, no truncated or over-extended structured tag list, no author abbreviation inside scientific_name_accepted, no genus-level RHS Cultivation boilerplate read as species text, and no site-wide legend text quoted as species evidence. For a hybrid: no dropped or ASCII-substituted multiplication sign, and no parent species standing in for the hybrid in scientific_name_given or scientific_name_accepted. NEVER refute a name merely for carrying "×" -- the sign is part of the name. DO refute scientific_name_accepted when the sign has been stripped, when a parent species has been substituted, or when the hybrid has been re-filed as a cultivar of a parent.

For EVERY non-null field (except scientific_name_given), check:

1. STRUCTURAL CHECK: Does at least one citation's "claim" label literally contain this field's name, and does that citation's quote actually bear on the field? (scientific_name_accepted included.) For name_note, check EACH bundled sub-claim individually; if refuting, say which sub-claims are covered/accurate, which are uncited-but-true (quote the live page text), and which are WRONG (drop, don't re-cite), and supply corrected wording. Check any "N of M sources" count and any description of a source's structure.
2. STRUCTURAL CHECK -- STRICT ENUM FIELDS: soil_base, soil_drainage, water_regime, humidity_need, fertilize_strength must be exactly one valid token. For soil_drainage: "moist but well-drained" and NC State's Good Drainage + Moist pair are moderate in this catalog, not moisture_retentive. For water_regime: refute a cadence read off a soil adjective, a wild-habitat sentence, a drought-tolerance trait, or a structured "Water: Medium" presented as support for keep_moist.
3. Does the citation's "quote" actually say what the claim asserts? A verbatim quote whose claim LABEL or whose field prose asserts something the quote does not say -- inverts a relationship, drops a hedge, adds a scope, relabels habitat prose as culture guidance, or mis-describes a source's structure -- is a defect: say so and give the corrected wording.
4. For toxic_to_pets: does at least one supporting citation explicitly name CATS and/or DOGS? Refute if every citation is scoped to a non-cat/dog animal or is unscoped. For toxicity_detail: check the field reproduces the source's symptom list and FULL poison-part list completely, carries any handling warning, reproduces preparation instructions with their exact times, includes every co-listed tag and plant-type trait, states the scope of a severity rating, uses the source's own words for a hazard, and discloses source disagreement on scope or edibility; a trimmed or softened safety field is a defect.
5. Is the VALUE itself correct? Watch for content bled in from a same-genus sibling in this batch (no two species here share a genus) or already in this catalog (Uniola paniculata is new to this catalog; Ammophila breviligulata is new to this catalog; Solidago sempervirens vs. Solidago canadensis (Canada Goldenrod), Solidago rugosa (Rough Goldenrod); Borrichia frutescens is new to this catalog; Spartina alterniflora is new to this catalog; Baccharis halimifolia is new to this catalog; Sabal minor is new to this catalog; Serenoa repens is new to this catalog), Iris cristata (Dwarf Crested Iris), Iris versicolor (Blue Flag); Sagittaria latifolia is new to this catalog; Nuphar advena is new to this catalog; Peltandra virginica is new to this catalog; Orontium aquaticum is new to this catalog; Acorus americanus is new to this catalog; Decodon verticillatus is new to this catalog; Hibiscus coccineus vs. Hibiscus rosa-sinensis (Chinese Hibiscus), Hibiscus syriacus (Rose of Sharon), Hibiscus moscheutos (Common Rose Mallow)), and for values read off a site-wide legend rather than species-specific prose. For a hybrid, treat its PARENT species as the primary bleed risk: a value sourced from a parent's page rather than the hybrid's own page is a refutation even when the number looks plausible.
6. Refute a field only when the VALUE is genuinely in doubt -- not when one of several citations has a defect but another cleanly supports the same value.
7. STRUCTURAL CHECK: scan for the literal string "null" or an empty string "" where real JSON null was intended, and for stray separator characters inside quotes.
8. Check any numeric day-interval field for silent computation from named dates or word-cadences.

For each field examined, include a finding with "field", "refuted", and "reasoning". Only include entries worth commenting on, but examine every non-null field per the checklist first.

Return ONLY the JSON verdict.`
}

const results = await pipeline(
  SPECIES,
  s => agent(researchPrompt(s), { label: `research:${s.common}`, phase: 'Research', schema: RECORD_SCHEMA, model: 'sonnet', effort: 'medium' }),
  (record, s) => agent(verifyPrompt(record, s), { label: `verify:${s.common}`, phase: 'Verify', schema: VERDICT_SCHEMA, model: 'opus' })
    .then(verdict => {
      const refuted = new Set((verdict.findings || []).filter(f => f.refuted).map(f => f.field))
      const removed = []
      for (const field of Object.keys(record)) {
        if (refuted.has(field) && !FIELD_LIST.includes(field)) { delete record[field]; removed.push(field); continue }
        if (field === 'common_name' || field === 'outdoor_sun_exposure') continue
        if (refuted.has(field) && record[field] !== null && field !== 'citations' && field !== 'unknowns') {
          const reason = (verdict.findings.find(f => f.field === field) || {}).reasoning || 'refuted by audit'
          record.unknowns = record.unknowns || []
          record.unknowns.push(`${field} — removed on audit: ${reason}`)
          record[field] = null
          removed.push(field)
        }
      }
      for (const f of (verdict.findings || [])) {
        if (f.refuted && !FIELD_LIST.includes(f.field) && !(f.field in record)) {
          record.unknowns = record.unknowns || []
          record.unknowns.push(`${f.field} — CITATION-LEVEL finding on audit (repair at landing): ${f.reasoning || ''}`)
        }
      }
      for (const flagField of ['common_name', 'outdoor_sun_exposure']) {
        if (refuted.has(flagField)) {
          const reason = (verdict.findings.find(f => f.field === flagField) || {}).reasoning || 'refuted by audit'
          record.unknowns = record.unknowns || []
          record.unknowns.push(`${flagField} — FLAGGED on audit (left as-is, needs manual review before landing): ${reason}`)
          removed.push(`${flagField} (flagged, not auto-modified)`)
        }
      }
      return { species: s.latin, record, fields_removed: removed.length }
    })
)

const ok = results.filter(Boolean)
const failed = SPECIES.length - ok.length
if (failed) log(`WARNING: ${failed} of ${SPECIES.length} species produced no record (agent failure) -- do not land this batch as complete`)
if (!ok.length) log('ALL agents failed -- empty batch, likely a session/usage limit; retry after the reset')

return {
  unverified: SPECIES.filter(sp => !ok.some(r => r.species === sp.latin)).map(sp => sp.latin),
  batch: 'b80-native-coastal',
  agents_failed: failed,
  records: ok.map(r => r.record),
  audit_summary: ok.map(r => ({ species: r.species, fields_removed: r.fields_removed })),
}
