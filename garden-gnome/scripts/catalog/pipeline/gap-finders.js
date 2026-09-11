// Reference: the 6-lens candidate finder that produced batches-b81-b88.json (run wf_284c3342-86c).
// Update REPO and SP below to this checkout and pipeline directory before re-running it.
export const meta = {
  name: 'catalog-gap-finders-2026-09-10',
  description: 'Find the next 6-9 research batches of species for the plant-care claim catalog: six category lenses, dedup against the corpus, NC State page check, batches of eight',
  phases: [
    { title: 'Find', detail: 'six category lenses, each returning up to 12 clean candidates with research notes', model: 'opus' },
    { title: 'Check', detail: 'mechanical re-check: covered.py dedup + NC State page exists', model: 'sonnet' },
    { title: 'Write', detail: 'save batches.json to the scratchpad' },
  ],
}

const REPO = '/Users/allisonbowman/Developer/Garden-Gnome/.claude/worktrees/database-build-goals-e548af/garden-gnome'
const SP = '/private/tmp/claude-501/-Users-allisonbowman-Developer-Garden-Gnome--claude-worktrees-database-build-goals-e548af/e53f91e1-ddb2-4d9f-8694-1b687525a69c/scratchpad'

const LENSES = [
  { key: 'houseplants', title: 'common houseplants', lens: 'Houseplants a North American or UK plant owner is likely to have on a windowsill or shelf today that the catalog still lacks: think Hoya, Peperomia, Goeppertia/Calathea, Philodendron, Anthurium, Begonia, Tradescantia, Pilea, Ficus, Dracaena, Epipremnum, Scindapsus, Syngonium, Aglaonema, indoor ferns, Chlorophytum, Schlumbergera, Kalanchoe, Crassula, Haworthia, Echeveria, Sansevieria/Dracaena, Zamioculcas. Prefer species with a dedicated NC State Plant Toolbox page (it covers many houseplants).' },
  { key: 'perennials', title: 'popular garden perennials', lens: 'Herbaceous perennials sold at every garden center that home gardeners plant in beds and borders: Echinacea, Rudbeckia, Salvia, Hosta, Paeonia, Phlox, Heuchera, Lavandula, Nepeta, Geranium, Achillea, Monarda, Aster/Symphyotrichum, Sedum, Dianthus, Delphinium, Digitalis, Alcea, Astilbe, Hemerocallis, Iris, Penstemon, Gaillardia, Leucanthemum, Veronica, Perovskia/Salvia yangii, Agastache. Check each against the corpus first; many are already landed.' },
  { key: 'annuals', title: 'annuals, bedding and container plants', lens: 'Annual and bedding plants grown in pots, baskets and beds each summer: Zinnia, Petunia, Calibrachoa, Tagetes, Impatiens, Begonia (semperflorens/tuberous groups only if a species page exists), Pelargonium, Antirrhinum, Cosmos, Helianthus annuus, Celosia, Lobularia, Viola, Verbena, Ipomoea, Tropaeolum, Nicotiana, Salvia splendens, Coleus (already landed), Ageratum, Gomphrena, Portulaca (Rose Moss landed), Dahlia (check). Species pages only, no seed-mix or cultivar-only entries.' },
  { key: 'edibles', title: 'vegetables, herbs and fruit', lens: 'Edibles a home grower raises in a garden, raised bed or pot: tomato, pepper, cucumber, squash, beans, peas, lettuce, spinach, kale, broccoli, carrot, beet, onion, garlic, potato, sweet potato, okra, eggplant, corn, basil, mint, rosemary, thyme, oregano, sage, parsley, cilantro, dill, chives, strawberry, blueberry, raspberry, blackberry, grape, fig, lemon, lime, apple, peach, pear, plum, cherry. Many are landed already (the corpus has b5, b9 vegetable batches and fruit batches): check every one with covered.py and only return the gaps. Cultivar groups (Brassica oleracea groups) count as distinct entries only if the corpus lacks that group.' },
  { key: 'shrubs', title: 'home-landscape shrubs, hedges, small trees and climbers', lens: 'Woody plants in a typical suburban yard: Hydrangea species (macrophylla, paniculata, arborescens, quercifolia), Buxus, Syringa, Spiraea, Weigela, Viburnum, Ilex, Taxus, Thuja, Juniperus, Rosa species, Acer palmatum (check), Cornus, Magnolia, Lagerstroemia (landed), Camellia (check), Rhododendron/azalea species, Pieris, Abelia, Nandina (check), Euonymus, Ligustrum, Clematis, Wisteria sinensis, Lonicera japonica, Parthenocissus, Hedera helix, Campsis. Check each against the corpus first.' },
  { key: 'bulbs-patio', title: 'bulbs, tubers, tender patio and Mediterranean plants', lens: 'Bulbs and tubers (Dahlia, Canna, Lilium species, Crocus, Hyacinthus, Narcissus (landed), Tulipa (landed), Allium, Muscari, Galanthus, Colchicum (landed), Caladium, Begonia tuberous, Zantedeschia) and tender patio or Mediterranean plants overwintered indoors (Olea europaea, Citrus species, Bougainvillea, Mandevilla, Nerium (landed), Plumbago, Brugmansia species, Fuchsia, Abutilon, Cestrum, Jasminum, Passiflora, Musa, Ensete, Cycas (landed), Agave, Aloe species, Yucca). Check each against the corpus first.' },
]

const CAND_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    category: { type: 'string' },
    candidates: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: { common: { type: 'string' }, latin: { type: 'string' }, note: { type: 'string' }, why: { type: 'string' } },
      required: ['common', 'latin', 'note', 'why'] } },
  },
  required: ['category', 'candidates'],
}

function finderPrompt(L) {
  return `You are choosing the next species to research for an evidence-backed plant-care catalog (the PlantAdvocate app). The catalog holds 568 species already; the list is in ${SP}/corpus_species.txt (given -> accepted name | common name | batch). Read it first.

YOUR LENS: ${L.title}. ${L.lens}

Return up to 12 candidate species, ranked by how commonly a home plant owner actually grows them (most common first), that meet ALL of these:
1. NOT already in the corpus. Check EVERY candidate mechanically before returning it: run
   cd ${REPO} && .venv/bin/python scripts/catalog/covered.py "Genus species" "Genus species" ...
   (it prints clean/DUP per name and matches given AND accepted names with cultivar tails stripped). Also think about reclassified synonyms yourself (Sansevieria trifasciata is landed as Dracaena trifasciata; Saintpaulia as Streptocarpus ionanthus; Schefflera arboricola as Heptapleurum arboricola) and check the currently accepted name too. Return only names covered.py reports clean.
2. A single species or a named natural hybrid with its own pages (no 'Various spp.', no seed mixes, no cultivar-only entries).
3. Has a dedicated single-species page on NC State's Plant Toolbox: check https://plants.ces.ncsu.edu/plants/<genus>-<species>/ (lowercase, hyphenated) returns HTTP 200 (curl -sI -o /dev/null -w '%{http_code}'). NC State is the anchor source of nearly every record; a species without it usually cannot be landed. If the obvious slug 404s, try the page's search once; otherwise drop the candidate.
4. Not a near-duplicate of a landed entry (do not propose a second cultivar group of a landed species, or a sibling that would land under the same common name).

For each candidate write:
- common: the common name you expect the dedicated pages to lead with (Title Case).
- latin: the currently accepted bare binomial (no author abbreviations).
- note: one to three sentences of research guidance in this exact style, ending with the fixed sentence: "this catalog's first <Genus>" if the genus is new to the corpus (check the corpus file), naming traps (synonyms, sibling confusions, a common name shared with a landed species), toxicity specifics to capture exactly (cat/dog scoping, handling warnings, edibility statements with their conditions), any enum trap (soil_drainage fast only for sharp/sandy drainage with no wet tolerance; moisture_retentive only on a cultivation REQUIREMENT), and always finish with: "Confirm species-specific content on a dedicated single-species page, never a genus-level, cultivar, or multi-species page."
- why: one sentence on why home growers commonly have it.

Return ONLY the JSON: {category: '${L.key}', candidates: [...]}. Fewer than 12 is fine if the lens is nearly exhausted; say so in the last candidate's why field is NOT allowed -- just return fewer.`
}

const CHECK_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    ok: { type: 'array', items: { type: 'string' } },
    dropped: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: { latin: { type: 'string' }, reason: { type: 'string' } }, required: ['latin', 'reason'] } },
  },
  required: ['ok', 'dropped'],
}

function checkPrompt(latins) {
  return `Mechanically re-check these candidate species for a plant catalog. For EVERY name:
(a) run: cd ${REPO} && .venv/bin/python scripts/catalog/covered.py ${latins.map(l => JSON.stringify(l)).join(' ')}
    and treat any line reporting DUP as a drop (reason: 'already in corpus').
(b) check https://plants.ces.ncsu.edu/plants/<genus>-<species>/ (lowercase, hyphenated; drop any 'x ' or '×' hybrid marker from the slug) with: curl -sI -o /dev/null -w '%{http_code}' <url>. A 200 or a 301/302 that lands on a plants.ces.ncsu.edu/plants/ page is a pass; 404 is a drop (reason: 'no NC State page').
(c) drop any name that is not a bare two-word binomial (author abbreviations, cultivar quotes, 'spp.').
Names: ${latins.join('; ')}
Return ONLY the JSON {ok: [...], dropped: [{latin, reason}]} with every input name in exactly one list.`
}

const norm = l => l.toLowerCase().replace('×', 'x').replace(/\s+/g, ' ').trim()

const found = await parallel(LENSES.map(L => () =>
  agent(finderPrompt(L), { label: `find:${L.key}`, phase: 'Find', schema: CAND_SCHEMA, model: 'opus' })))
const byKey = {}
const seen = new Set()
for (const f of found.filter(Boolean)) {
  byKey[f.category] = []
  for (const c of f.candidates) {
    const k = norm(c.latin)
    if (seen.has(k)) continue
    seen.add(k)
    byKey[f.category].push(c)
  }
}
log(`finders: ${Object.entries(byKey).map(([k, v]) => `${k}=${v.length}`).join(', ')}`)

const checks = await parallel(Object.entries(byKey).map(([key, cands]) => () =>
  cands.length ? agent(checkPrompt(cands.map(c => c.latin)), { label: `check:${key}`, phase: 'Check', schema: CHECK_SCHEMA, model: 'sonnet', effort: 'low' })
    .then(v => ({ key, ok: (v && v.ok || []).map(norm), dropped: v ? v.dropped : [] })) : Promise.resolve({ key, ok: [], dropped: [] })))
const kept = {}
let dropped = []
for (const ch of checks.filter(Boolean)) {
  kept[ch.key] = byKey[ch.key].filter(c => ch.ok.includes(norm(c.latin)))
  dropped = dropped.concat(ch.dropped)
}
log(`after check: ${Object.entries(kept).map(([k, v]) => `${k}=${v.length}`).join(', ')}; dropped ${dropped.length}: ${dropped.map(d => `${d.latin} (${d.reason})`).join('; ')}`)

// batches of eight per category; short tails pooled into mixed batches
const batches = []
let n = 81
const tail = []
for (const L of LENSES) {
  const list = (kept[L.key] || []).slice()
  while (list.length >= 8) {
    batches.push({ n: n++, slug: L.key, title: L.title, species: list.splice(0, 8) })
  }
  if (list.length >= 5) batches.push({ n: n++, slug: L.key, title: L.title, species: list.splice(0) })
  else tail.push(...list.map(c => ({ ...c, from: L.key })))
}
while (tail.length >= 5) batches.push({ n: n++, slug: 'mixed', title: 'mixed gaps across lenses', species: tail.splice(0, 8) })
if (tail.length) log(`left over (too few for a batch): ${tail.map(c => c.latin).join(', ')}`)
log(`batches: ${batches.map(b => `b${b.n} ${b.slug} x${b.species.length}`).join(', ')}`)

phase('Write')
const payload = JSON.stringify(batches.map(b => ({ n: b.n, slug: b.slug, title: b.title, species: b.species.map(c => ({ common: c.common, latin: c.latin, note: c.note })) })), null, 1)
await agent(`Write the following JSON EXACTLY (byte for byte, no commentary, no reformatting) to the file ${SP}/batches.json using your Write tool, then reply with the single word DONE.\n\n${payload}`, { label: 'write:batches.json', phase: 'Write', model: 'sonnet', effort: 'low' })
return { batches: batches.map(b => ({ n: b.n, slug: b.slug, count: b.species.length, latins: b.species.map(c => c.latin) })), dropped, leftover: tail.map(c => c.latin) }