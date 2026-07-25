# Catalog expansion pipeline

Expands the species catalog (~129 curated → ~1,900) with tiered sourcing,
mandatory validation, and a weighted manual-review workflow. Everything runs
offline against the local DB — the running app is untouched until records are
imported.

## Provenance model

Every species row carries:

| field | values | meaning |
|---|---|---|
| `source` | `curated` / `perenual` / `llm_generated` | where the record came from |
| `source_ref` | Perenual species id | traceability back to the source |
| `review_status` | `approved` / `needs_review` / `verified` | validation → manual review ladder |
| `review_note` | free text | citation from manual verification (source + URL) |

The original 129 hand-written records are `curated`/`approved` (set by the
DB migration). `llm_generated` records are the heavier-review tier.

## Runbook

```bash
cd garden-gnome
export PERENUAL_API_KEY=sk-...        # Premium tier — care guides + indoor filter

# 1. Build the nursery-common target list (~1,900 indoor species)
python -m app.data.expansion.fetch_targets --from-perenual --count 1900

# 2. Rehearse without touching the DB
python -m app.data.expansion.run_expansion --dry-run --limit 50

# 3. Real run. Tier 1: Perenual; tier 2: LLM fallback for misses
#    (fallback needs ADVISOR_BACKEND=anthropic, else misses are
#    reported and skipped); tier 3: validation on everything.
python -m app.data.expansion.run_expansion

# 4. Manual review pass: fill in the `review` block of each entry in
#    output/review_sample.json (cross-check against NC State Extension
#    Plant Toolbox or Missouri Botanical Garden Plant Finder), then:
python -m app.data.expansion.apply_review app/data/expansion/output/review_sample.json
```

Outputs (in `app/data/expansion/output/`, gitignored):

- `review_queue.json` — records that failed validation (missing fields,
  implausible values, near-duplicate names) **plus** records built on mapper
  defaults (e.g. no soil data). These are *not* imported. Fix and re-import
  via `POST /species/bulk`, or drop them.
- `review_sample.json` — the weighted 5–10% manual-review sample. All
  top-houseplant matches are guaranteed a slot; the rest is a uniform draw.
- `expansion_report.json` — full run report including Perenual misses and
  LLM failures.

## Working down the `needs_review` backlog

Run the free passes first, then pay for only what's left. **None of these write
to the catalog** — they draft verdicts into the file `apply_review.py` consumes,
for a human to read.

```bash
# 1. Genus inference — FREE, OFFLINE, no network at all.
#    Fills defaulted care data from human-approved siblings in the same genus.
#    Usually the biggest single win, and it costs nothing.
python -m app.data.expansion.genus_fill --all

# 2. Wikipedia triage — FREE (MediaWiki).
#    Finds synonym/duplicate rows and corrects names to accepted binomials.
python -m app.data.expansion.wiki_enrich --all
python -m app.data.expansion.wiki_enrich --mock-dir fixtures/wiki   # offline

# 3. Merge both + see exactly what's left
python -m app.data.expansion.populate_catalog --dry-run   # report only
python -m app.data.expansion.populate_catalog             # write merged file

# 4. Horticultural research — COSTS MONEY per record. Only for what survives.
python -m app.data.expansion.research_review --limit 10

# 5. Apply, after reading the file
python -m app.data.expansion.apply_review output/populate_review.json
```

Why this order:

- **Genus inference first** because it is free, offline, and care attributes are
  largely conserved within a genus — an approved *Anthurium* sibling is a far
  better estimate than a mapper default.
- **Then dedup**, because near-duplicate rows are what make *identification*
  ambiguous. Removing them is an ID fix, not tidying.
- **Then pay**, over a set that is now smaller and deduplicated.

`populate_catalog` reports coverage: duplicates to remove, records now complete,
partially filled, and how many still need a paid horticultural source.

Coverage depends entirely on **genus overlap** — how many `needs_review` rows
share a genus with one of the approved species. Run step 1 and read the report
before assuming a number.

Safety properties (shared with `research_review`, tested): a verdict without a
citation URL is downgraded to `uncertain`; corrections outside the allowed field
set are stripped; every entry is stamped machine-drafted. Toxicity is only ever
proposed non-toxic → toxic — clearing a warning because an article didn't
mention it would be an unsafe inference, so that direction is refused.

## Field-mapping notes (Perenual → our schema)

- **Water schedule**: `watering_general_benchmark` ("5-7 days") when present,
  else a fallback by watering category (Frequent 3–7d, Average 7–14d,
  Minimum 14–30d, None 30–60d). Provenance goes in the schedule note.
- **Light**: first recognized `sunlight` term (full shade→low,
  part shade→medium, sun-part shade→bright_indirect, full sun→direct).
- **Temperature**: derived from the coldest USDA hardiness zone (+15 °F,
  clamped to 40–65 °F floor; 85/90 °F ceiling). Raw zones kept as a trait.
- **Humidity**: Perenual has no humidity field — derived from the watering
  category and recorded as a `humidity_source` trait so reviewers know.
- **Fertilize/repot**: sensible defaults (30–60d growing season / 1–2 years);
  Perenual care guides rarely give explicit intervals.
- **Toxicity**: `poisonous_to_pets` → `toxic_to_pets`.

Re-running is safe: species already in the catalog (by scientific name) are
skipped, and validation gates everything else.

## Tests

```bash
python -m app.data.expansion.selftest   # no network, no key needed
```

26 checks: mapper fixtures, validator (synthetic bad records + the real
curated catalog must pass clean), near-duplicate detection including
cultivar variants, and sampler weighting.
