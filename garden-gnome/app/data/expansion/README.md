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
