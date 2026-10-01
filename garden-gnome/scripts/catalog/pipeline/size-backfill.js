export const meta = {
  name: 'size-backfill',
  description: 'Backfill mature size, edibility and pollinator value onto already-landed species, with cited quotes and an adversarial audit',
  phases: [
    { title: 'Research', detail: 'one agent per species, reading only the pages that species is already cited to' },
    { title: 'Verify', detail: 'adversarial audit: inches not feet, silence is null, no invented ranges' },
  ],
}

const REPO = '/Users/allisonbowman/Developer/Garden-Gnome/garden-gnome'
const SPECIES = args

const FIELDS = [
  'is_edible', 'attracts_pollinators', 'climbs',
  'mature_height_in_min', 'mature_height_in_max',
  'mature_spread_in_min', 'mature_spread_in_max',
]

const RECORD_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    common_name: { type: 'string' },
    scientific_name_accepted: { type: 'string' },
    is_edible: { type: ['boolean', 'null'] },
    attracts_pollinators: { type: ['boolean', 'null'] },
    climbs: { type: ['boolean', 'null'] },
    mature_height_in_min: { type: ['number', 'null'] },
    mature_height_in_max: { type: ['number', 'null'] },
    mature_spread_in_min: { type: ['number', 'null'] },
    mature_spread_in_max: { type: ['number', 'null'] },
    unknowns: { type: 'array', items: { type: 'string' } },
    citations: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          claim: { type: 'string' }, source: { type: 'string' },
          url: { type: 'string' }, quote: { type: 'string' },
        },
        required: ['claim', 'source', 'url', 'quote'],
      },
    },
  },
  required: ['common_name', 'scientific_name_accepted', 'is_edible', 'attracts_pollinators', 'climbs',
    'mature_height_in_min', 'mature_height_in_max', 'mature_spread_in_min',
    'mature_spread_in_max', 'unknowns', 'citations'],
}

const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    common_name: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          field: { type: 'string' },
          refuted: { type: 'boolean' },
          reason: { type: 'string' },
          corrected_quote: { type: ['string', 'null'] },
        },
        required: ['field', 'refuted', 'reason'],
      },
    },
    summary: { type: 'string' },
  },
  required: ['common_name', 'findings', 'summary'],
}

// A houseplant's size is its size indoors. The fit engine checks mature height against a room's headroom,
// and an extension page's Dimensions block for a tropical tree grown as a houseplant is its native stature:
// NC State gives the rubber plant 50-100 ft, which would tell every owner it outgrows their living room.
// Same spirit as the climber rule -- where the field cannot say which size it means, it says nothing.
function houseplantRule(s) {
  if (s.is_houseplant !== true) return ''
  return `12. THIS SPECIES IS CATALOGUED AS A HOUSEPLANT, and the app checks its mature height against a room's headroom. If a page gives a size for the plant grown indoors, as a houseplant or in a container, record THAT figure and say so in the claim ("mature_height_in 72-120 (NC State: as a houseplant 6-10 ft, converted to inches)"), even where the page's Dimensions block is bigger. If the only figure on the pages is the plant's outdoor, landscape or native-habitat stature and its height or spread exceeds 120 inches (10 ft), leave ALL FOUR size fields null and quote that figure in unknowns: a rubber plant recorded at 100 ft would tell every owner it will outgrow their living room. A figure of 10 ft or under is recorded as published.
`
}

function houseplantAudit(s) {
  if (s.is_houseplant !== true) return ''
  return `I. HOUSEPLANT SCALE. This species is catalogued as a houseplant. Refute every size value taken from the plant's outdoor, landscape or native-habitat stature when its height or spread exceeds 120 inches, unless the page ties that figure to indoor or container growth. Where a page gives an indoor or container figure, refute a size taken from a larger outdoor figure instead.

`
}

// Round 5 (s.newPages): these species were already asked against their cited
// pages and came back with nothing usable -- re-asking the same pages returns
// the same nothing. So the researcher may also use the species' OWN page on a
// registered authority; a domain outside the registry resolves to nothing at
// load (authorities.py), so a page anywhere else would be wasted work.
const REGISTERED = [
  'plants.ces.ncsu.edu (NC State Extension Gardener Plant Toolbox)',
  'www.rhs.org.uk (Royal Horticultural Society)',
  'edis.ifas.ufl.edu (UF/IFAS Extension -- strong on houseplants and tropicals)',
  'hgic.clemson.edu (Clemson HGIC)',
  'extension.umd.edu (University of Maryland Extension)',
  'extension.psu.edu (Penn State Extension)',
  'fieldreport.caes.uga.edu (UGA Extension)',
]

function pageScope(s) {
  const cited = s.urls.map((u) => '  ' + u).join('\n')
  if (!s.newPages) {
    return `READ ONLY THESE PAGES -- they are the exact pages this record is already cited to, so its evidence stays anchored to the same authorities:
${cited}`
  }
  return `START WITH THESE PAGES -- the ones this record is already cited to:
${cited}
An earlier pass read exactly these and found no usable size. So you MAY ALSO find and read this species' OWN page on one of these registered authorities, and on no other site (a page anywhere else is discarded at load):
${REGISTERED.map((d) => '  ' + d).join('\n')}
Find a page with WebSearch or by its site's species URL pattern; it must be about ${s.latin} itself -- not a genus page, not a cultivar page, not a different species. Before you quote a new page, load it through qc.py (below) so it lands in the shared cache the quote checker reads; a quote from a page qc.py cannot load is unusable. If qc.py fails on a registered host with a ProxyError or a sandbox denial, re-run that same command with the host in the Bash tool's allowed_domains. For a houseplant, an indoor or container figure is exactly what you are looking for (UF/IFAS houseplant and foliage-plant sheets often give one).`
}

function researchPrompt(s) {
  return `You are adding SEVEN fields to an already-landed record in an evidence-backed plant-care catalog (PlantAdvocate). The species is "${s.common}" (${s.latin}). Everything else about this record is already researched and cited; you are not re-doing it and must not touch it.

THE ONLY FIELDS YOU RESEARCH: ${FIELDS.filter((f) => !(s.have || []).includes(f)).join(', ')}.${(s.have || []).length ? `
ALREADY LANDED, return as null and do not research: ${s.have.join(', ')}. A backfill never overwrites a landed value.` : ''}

${pageScope(s)}

HOW TO READ THEM. Run, from ${REPO}:
  .venv/bin/python scripts/catalog/pipeline/qc.py "<URL>" "<regex>" "<regex>" ...
It prints the page <title> and context windows from the SAME fetch-and-extract path the quote checker uses, so text you copy from its output is text the checker will find. A newline renders as the character U+23CE -- never copy that character into a quote; it marks where the page stacks separate elements. Useful patterns: 'Dimensions', 'Height:', 'Width:', 'Max Height', 'Max Spread', 'Ultimate height', 'Attracts', 'Edible', 'Pollinator', 'butterfl', 'bee', 'hummingbird', 'Wildlife'. Try several. A host that refuses this machine (plantfinder.mobot.org, ask.ifas.ufl.edu) prints a non-ok status -- skip it and say so in unknowns; do not guess what it would have said. The page cache in scripts/catalog/.quote_cache is SHARED by every agent running right now: never delete, move or edit anything in it -- not one entry, never a glob. On 2026-09-27 two agents ran 'rm -f .quote_cache/*.json' and wiped the pages forty other agents were reading. A page that will not load is reported in unknowns, not repaired; a failed fetch is no longer cached, so simply retrying is safe.

NC State's Plant Toolbox is the anchor: it carries a structured "Dimensions:" block reading "Height: 60 ft. 0 in. - 80 ft. 0 in." and "Width: ...". Where the species has no NC State page -- and a GENUS page is NOT a substitute, its range spans every species in the genus -- RHS is the source. RHS labels those fields "Max Height" and "Max Spread", in METRES, NOT "Ultimate height": "Max Height         0.5-1 metres" is 19.7-39.4 inches (x 39.37). Search for BOTH wordings before concluding a page carries no size, and never record your own failed search as a property of the page -- say what you searched for. An open-ended RHS value ("wider than 8 metres") gives no usable bound; leave that end null.

THE RULES.

1. MATURE SIZE IS IN INCHES. Convert yourself: 3 ft = 36, "60 ft. 0 in." = 720, "2 ft. 6 in." = 30. Put the published LOW end in mature_height_in_min and the HIGH end in mature_height_in_max; same for spread/width. Getting this wrong by a factor of twelve is the single likeliest defect in this task, so state the conversion in the citation's claim text.
2. ONE FIGURE FILLS ONE END. A page that says only "to 6 ft" gives you a max of 72 and a min of null. NEVER centre a single figure into an invented range, and never make up the other end.
3. A CULTIVAR'S SIZE IS NOT THE SPECIES'. If the figure is given for a named cultivar, it does not go in. Say so in unknowns.
4. A CLIMBER'S HEIGHT IS ITS REACH. If a page describes the plant as a vine, liana or climber (NC State "Habit/Form: Climbing" or "Plant Type: Vine", RHS "Habit: Climbing", or prose such as "a twining vine", "climbs by tendrils", "self-clinging"), set climbs TRUE with a citation whose claim contains the word "climbs" and whose quote is that habit text. Then record the size the page publishes AS PUBLISHED: for a climber, mature_height_in is how far it climbs given support -- "Height: 30 ft. 0 in. - 50 ft. 0 in." is a reach of 360-600 inches, and that is exactly what this field now means for a climber. Say "reach" in the size citation's claim text. Never set climbs FALSE: a plant no page calls a climber is null. A sprawling groundcover, a trailing basket plant or an arching bramble is NOT a climber unless a page says it climbs.
5. BEFORE you set is_edible at all, search the anchor page for "Poison", "Toxic" and "Problem for" and read what comes back. Every edible-plant record in the last run that lost its value lost it because a toxic part was named on the very page the researcher cited and never reached unknowns. If the page names a poisonous part, a severity, a toxic principle, a preparation requirement or a pets warning, that text goes in unknowns WHENEVER is_edible is true -- all of it, not a summary.
6. is_edible is TRUE only where a page states the plant or a named part of it is grown or used for food. FALSE only where a page states it is not edible or is poisonous to eat. Where no page addresses eating at all, NULL. Null is "no record" here, exactly as with toxicity -- never infer edibility from a genus of edibles. If edibility is CONDITIONAL (cooked only, ripe fruit only, one part edible while another is toxic), set true and put the whole condition in unknowns: a bare true on a plant with a poisonous part is the dangerous half-truth this field must not tell.
7. attracts_pollinators is TRUE where a structured attracts/wildlife field or an unconditional statement names bees, butterflies, moths, hummingbirds or other pollinators. NC State's "Attracts" field and RHS's "attractive to pollinators" tag both count. Birds eating the SEED, or deer browsing the foliage, is NOT pollination -- do not read it as support. No mention at all is NULL, not false.
8. EVERY non-null field needs a citation whose "claim" text CONTAINS THE FIELD NAME LITERALLY. For size, use the STEM so one citation covers both ends of a range: write the claim as "mature_height_in 720-960 (NC State Height 60 ft. 0 in. - 80 ft. 0 in., converted to inches)" and "mature_spread_in 480-960 (...)". For the three flags, the claim must literally contain "is_edible", "attracts_pollinators" or "climbs".
9. QUOTES ARE VERBATIM RENDERED TEXT, copied from qc.py's output. Never fabricated, never paraphrased, never a label glued to its value across a U+23CE boundary, never a truncated or extended tag list. Every quote is mechanically re-fetched and checked after you finish; one that is not on the page WILL be found.
10. All nulls are real JSON null, never the string "null".
11. unknowns: one line for anything decision-relevant that does not fit a field, one line for every field you deliberately left null and why, and one line for every page that refused this machine.
${houseplantRule(s)}
common_name must be exactly "${s.common}" and scientific_name_accepted exactly "${s.latin}" -- this record already exists under those names and you are merging into it, not creating one.

NEVER return a citation whose source, url or quote is a placeholder, a stub, or a description of a citation you meant to fill in later. A record with no real citation for a field must set that field null instead. One run returned an array of literal 'placeholder' strings and the whole species had to be thrown away.

Return ONLY the JSON.`
}

function verifyPrompt(record, s) {
  return `You are an adversarial auditor. A researcher has proposed seven new field values for the already-landed catalog record "${s.common}" (${s.latin}). Find what is wrong. Do not rubber-stamp; a finding of "everything is fine" is only acceptable after you have actually re-read the pages.

The proposed record:
${JSON.stringify(record, null, 2)}

Re-read the pages yourself from ${REPO}:
  .venv/bin/python scripts/catalog/pipeline/qc.py "<URL>" "<regex>" ...
Pages: ${s.urls.join(' , ')}${s.newPages ? ' -- plus any page the record above newly cites. A new page must be the species\' own page on a registered authority (plants.ces.ncsu.edu, www.rhs.org.uk, edis.ifas.ufl.edu, ask.ifas.ufl.edu, hgic.clemson.edu, extension.umd.edu, extension.psu.edu, fieldreport.caes.uga.edu); refute every value whose only support is a page on any other domain, a genus page, or another species\' page.' : ''}
The page cache in scripts/catalog/.quote_cache is SHARED by every agent running right now: never delete, move or edit anything in it -- not one entry, never a glob. On 2026-09-27 two agents ran 'rm -f .quote_cache/*.json' and wiped the pages forty other agents were reading. A page that will not load is reported in unknowns, not repaired; a failed fetch is no longer cached, so simply retrying is safe.

CHECK EVERY ONE OF THESE, and emit a finding per field you examined (refuted true or false):

A. UNIT CONVERSION. Is a size value plainly the page's FEET figure left unconverted? A 60-80 ft tree recorded as 60-80 inches, or a 2 ft perennial as 2, is the defect this audit exists for. Re-derive every number from the quoted page text yourself.
B. RANGE INTEGRITY. min <= max. A single published figure must NOT have become a range. Both ends must trace to text actually on the page.
C. SCOPE. Is the size a cultivar's rather than the species'? Is an RHS "ultimate height" for a different taxon on a shared page? Is it from a GENUS page or a different species' page? Refute any of those.
C2. CLIMBERS. climbs TRUE needs a page that says the plant climbs (a habit field or prose: vine, liana, twining, tendrils, self-clinging). Refute it for a sprawler, trailer or arching bramble no page calls a climber, and refute climbs FALSE outright (it is never set false). A climber's size is its published reach and IS allowed -- do not refute a climber's height for being a vine.
D. SILENCE IS NULL. Refute any is_edible or attracts_pollinators set to FALSE where the pages are simply silent. False is a claim that a source denied it; silence is null.
E. POLLINATOR EVIDENCE. Refute attracts_pollinators true if its support is seed-eating birds, deer browsing, or general "wildlife value" prose that names no pollinator.
F. EDIBILITY SAFETY. If is_edible is true and any page names a toxic part or a required preparation, the condition MUST appear in unknowns. Refute if it does not.
G. CITATION LABELS. Every non-null field needs a citation whose claim contains the field name literally -- "mature_height_in" for the height pair, "mature_spread_in" for the spread pair, "is_edible", "attracts_pollinators", "climbs". Refute a field whose citation is missing or mislabelled.
H. QUOTE PROVENANCE. Is each quote really on the page, verbatim, as one rendered run? Refute a quote containing U+23CE, a label glued to a value across a newline boundary, or text you cannot find with qc.py. When the value stands but the quote is defective, set refuted false and supply corrected_quote with page text you verified.

${houseplantAudit(s)}Set refuted TRUE to null the field. Use corrected_quote ONLY when the value survives and just its quote needs replacing. Be specific in reason: name the number, the page, and what it actually says.`
}

log(`Backfilling size, edibility and pollinator value on ${SPECIES.length} already-landed species.`)

const results = await pipeline(
  SPECIES,
  (s) => agent(researchPrompt(s), {
    label: `research:${s.common}`, phase: 'Research',
    schema: RECORD_SCHEMA, model: 'sonnet', effort: 'medium',
  }),
  (record, s) => {
    if (!record) return null
    return agent(verifyPrompt(record, s), {
      label: `verify:${s.common}`, phase: 'Verify',
      schema: VERDICT_SCHEMA, model: 'opus', effort: 'high',
    }).then((verdict) => ({ species: s, record, verdict }))
  },
)

// Apply the audit mechanically.
//
// Two rules, both learned the hard way on this pilot:
//
// 1. An auditor names a field the way a person would -- sometimes one field,
//    sometimes a pair ("mature_height_in_min / mature_height_in_max"), sometimes
//    a stem. A strict equality check silently dropped a refutation written as a
//    pair, and two genus-scoped values survived into the merge as though they
//    had passed. So the match is fuzzy, and anything that matches NOTHING is
//    surfaced in `review` rather than ignored: a refutation this script cannot
//    understand must never look like a refutation that did not happen.
//
// 2. A corrected quote is NOT swapped in automatically. Swapping by field name
//    put an auditor's toxicity line into the citation that was supposed to
//    support edibility, leaving a claim and a quote that contradicted each
//    other. Quote repairs go to `review` for the landing step to ground-truth
//    with qc.py, which is what the landing brief has always prescribed.
const landed = []
// An audit that never came back (usage limit, network, a crashed agent) is NOT an audit
// that found nothing. Before this guard, a null verdict fell through `verdict?.findings || []`
// as zero refutations and the unaudited record landed as if it had passed.
const unverified = []
for (const r of results.filter(Boolean)) {
  if (!r.verdict || !Array.isArray(r.verdict.findings)) {
    unverified.push(r.species.latin)
    continue
  }
  const { species, record, verdict } = r
  const rec = { ...record }
  const applied = []
  const review = []

  const fieldsNamed = (name) => {
    const n = String(name || '')
    return FIELDS.filter((f) => n.includes(f) || f.startsWith(n.trim()))
  }

  for (const f of (verdict?.findings || [])) {
    const targets = fieldsNamed(f.field)
    if (f.refuted) {
      if (!targets.length) {
        review.push(`REFUTED but unmapped field ${JSON.stringify(f.field)}: ${f.reason}`)
        continue
      }
      for (const field of targets) {
        if (rec[field] !== null && rec[field] !== undefined) {
          applied.push(`${field}: ${rec[field]} -> null (${f.reason})`)
          rec[field] = null
        }
        rec.unknowns = [...(rec.unknowns || []), `${field} removed on audit: ${f.reason}`]
      }
      continue
    }
    if (f.corrected_quote) {
      review.push(`quote correction proposed for ${JSON.stringify(f.field)} -- NOT applied, ground-truth it: ${JSON.stringify(f.corrected_quote)}`)
    }
  }

  // A citation left supporting nothing is dropped, so no page is credited for
  // a value that is no longer there.
  rec.citations = rec.citations.filter((c) =>
    FIELDS.some((f) => {
      const stem = f.replace(/_(min|max)$/, '')
      return c.claim.includes(stem) && (rec[f] !== null && rec[f] !== undefined)
    }))
  landed.push({ batch: species.batch, record: rec, applied, review, summary: verdict?.summary || '' })
}

const nulled = landed.reduce((n, e) => n + e.applied.length, 0)
const flagged = landed.reduce((n, e) => n + e.review.length, 0)
log(`${landed.length} species; ${nulled} field(s) nulled on audit, ${flagged} item(s) for landing review.`)
if (unverified.length) log(`UNVERIFIED, held back (audit missing): ${unverified.join(', ')}`)
const noResearch = SPECIES.filter((s) => !results.some((r) => r && r.species.latin === s.latin)).map((s) => s.latin)
if (noResearch.length) log(`NO RESEARCH, held back: ${noResearch.join(', ')}`)
return { landed, unverified, no_research: noResearch }
