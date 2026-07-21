# PlantAdvocate — Identification Strategy Revision

Implementation plan for Claude Code. Triggered by a real finding from a
TestFlight build on an iPhone 17 Pro Max: **on-device identification does not
reliably distinguish visually similar species.**

> **Correction, 2026-07-21.** An earlier draft of this plan said the catalog
> held 129 species and designed around that. It does not. `species_catalog.json`
> is the original *seed file*; the Perenual expansion wrote directly to the
> database, which holds **1,940 species** — and `identify_species` queries the
> database. Every design conclusion that followed from 129 was wrong and has
> been replaced. Count the DB, not the seed file.

## Two separate causes, one symptom

**Cause 1 — the on-device pipeline discards the image.**
`mobile/modules/plant-id/ios/PlantIdModule.swift`:

```
photo → VNClassifyImageRequest → ≤8 labels (confidence > 0.1) → Foundation Models → species name
```

Foundation Models (iOS 26) is a *text* model, so Vision turns the image into
labels first. `VNClassifyImageRequest` returns a coarse fixed taxonomy — a
Pothos and a Heartleaf Philodendron both reduce to roughly `plant`, `leaf`,
`houseplant`. Two species, identical model input. This is an **information
bottleneck**, so a better prompt or a better text model cannot fix it.

**Cause 2 — most of the catalog is unverified.**

| `source` | count | | `review_status` | count |
|---|---|---|---|---|
| curated | 129 | | **approved** | **252** |
| perenual | 1,811 | | **needs_review** | **1,688** |

87% of species carry unchecked care data, with `review_note` values like
*"no soil data — defaulted"* and *"near-duplicate of 'Anthurium andraeanum'"*.
Near-duplicate rows produce the *same user-visible symptom* as Cause 1.
**Neither cause can be ruled out without testing**, and Phase 3 exists to
separate them.

## Why open-world naming, not a candidate list

Handing the model all 1,940 species costs **~20,400 tokens (~$0.044) per
identify** and asks it to scan a long flat list — a *harder* task than naming
the plant, which vision models do well from pretraining.

So the model names the plant freely and grounding happens afterwards, in
`app/services/name_match.py`:

| | Tokens in | Cost/photo | Photos per $1 |
|---|---|---|---|
| Candidate list (rejected) | ~22,000 | $0.046 | ~22 |
| **Open-world + fuzzy match** | ~1,800 | **~$0.005** | **~200** |

Roughly 9× cheaper, and likely more accurate.

**Identity is the scientific name.** Per the policy in `admit_queue.py`
(2026-07-09), common names legitimately collide, so a binomial hit outranks a
common-name hit and ties break toward reviewed records.

## Ground rules

- **On-device is demoted, not deleted** — it becomes the offline path, the
  privacy-preserving option, and the fallback when the server is unreachable.
- **A weak match yields no species, never a forced nearest row.** Out-of-catalog
  plants get an honest "not in our catalog yet".
- **Unreviewed matches are flagged, not hidden.** `identify_species` returns
  `unreviewed_ids`; the client hedges rather than asserting.
- **Machine research never self-approves.** It drafts verdicts for a human.
- Every failure degrades to manual search, which always works.
- No schema migrations in this plan.

## Decisions made

| Question | Decision |
|---|---|
| Cloud model | **Sonnet 5** (~$0.005/photo open-world) |
| Routing | **Server first, on-device fallback** |
| Grounding | Open-world naming + Dice fuzzy match; no candidate list |
| Unreviewed species | Matched but flagged, ranked below reviewed |

---

## Phase 0 — Backend ✅ done on this branch

`VISION_BACKEND=anthropic` drives **both** identification and diagnosis.
`_anthropic_vision_chat` mirrors `_ollama_chat` (user-safe `VisionUnavailable`,
technical cause logged) on `AsyncAnthropic` — this module must not block the
event loop, so the sync client `advisor.py` uses would be wrong.

`app/services/name_match.py` is a faithful port of
`mobile/src/photoId/fuzzyMatch.ts` — **that file is the reference
implementation**. `PARITY_FIXTURES` pins shared expected scores; a jest test
asserting the same numbers should be added so the two can't silently diverge.

Sonnet 5 rejects `temperature`/`top_p`/`top_k`; a test asserts none are sent.
A test also asserts the catalog never re-enters the prompt.

**Care advice needed no code** — `advisor.py` already dispatches `"anthropic"`.

## Phase 1 — Mobile routing (server first)

`mobile/src/api/` has **no server identify call today**. Add one.

1. New API call against `POST /species/identify-photo`. It now returns
   `candidates`, `observation`, `tier`, and `unreviewed_ids`.
2. Rewrite `src/photoId/identify.ts` as a ladder, preserving the
   `IdentifyResponse` shape so `AddPlantScreen` needs no changes:
   - **Server** when reachable and `/ai/status` reports vision ready.
   - **On-device** when the server is unavailable and `isAvailable()` is true —
     existing path, still grounded through `fuzzyMatch.ts`.
   - **Manual search** otherwise.
3. Hedge the copy for anything in `unreviewed_ids` — the care data behind that
   match has not been checked by a human.

**Accept when:** a dev build identifies via the server, falls back with the
server stopped, and falls back to search with both unavailable — each verified
by turning that path off in turn.

## Phase 2 — Consent (blocks App Review)

Server-first means photos leave the device, and there is **no consent copy
anywhere in `mobile/src`** — nothing needed it while everything was on-device
or stubbed.

- First time a photo would upload: what is sent, where, why, and that it isn't
  retained. Store the choice on the profile.
- Declining is a first-class outcome — fall back to on-device/manual silently,
  reversible in Settings.
- On-device identification needs **no** consent. Don't prompt for it.

## Phase 3 — Separate the two causes

Run the same 20–30 photos through both paths, across at least 5 pairs of
visually similar catalog species:

- Server right / on-device wrong → **Cause 1** confirmed; the pivot is the fix.
- Both wrong on the *same* near-duplicate rows → **Cause 2**; the catalog needs
  review before more model spend.

This is also where `plantadvocate-vision-eval-plan.md` becomes runnable: with
one backend serving both features, its D-gates and I-gates now cover paths
users can reach.

## Phase 4 — Work down the review backlog

`app/data/expansion/research_review.py` researches `needs_review` species
against NC State Extension, Missouri Botanical Garden, and RHS, and drafts
verdicts into the file `apply_review.py` already consumes.

```bash
python -m app.data.expansion.research_review --limit 10       # start small
python -m app.data.expansion.research_review --mock-dir ...   # offline, free
python -m app.data.expansion.apply_review output/researched_review.json
```

Safety properties, all tested: a verdict without a real citation URL is
downgraded to `uncertain`; a `corrected` verdict with no corrections is
downgraded; correction fields outside `SPECIES_FIELDS` are stripped; every
entry is stamped machine-drafted. **The script never writes to the catalog** —
`apply_review.py` does, from a file a human has read.

Costs real money per record, so `--limit` defaults to 10 and the full backlog
needs an explicit `--all`. **Price a batch of 10 before running 1,688** — I was
unable to verify current web-search tool pricing, so the per-record cost is
genuinely unknown until measured.

## Phase 5 — Revisit triggers

- **Foundation Models gains image input** → on-device could return to primary,
  removing both the per-photo cost and the consent requirement. Re-check each
  iOS release.
- **Approved share rises well above 252** → tighten identification to prefer
  reviewed species more aggressively.
- **Cost becomes material** → try Haiku 4.5 against the Phase 3 photo set
  before assuming it's worse.

---

## Explicit non-goals

- Growing the catalog. It is already larger than its review capacity;
  Phase 4 is about trust, not breadth.
- Replacing `fuzzyMatch.ts` — still the on-device grounding layer, and the
  reference implementation for the Python port.
- Open-world identification of plants we don't stock.
- Android/Gemini Nano routing — same ladder, untested, out of scope.
- Re-tuning diagnosis prompts (that's the alignment plan).

## Suggested kickoff prompt

> Read plantadvocate-identify-strategy-plan.md. Implement Phase 1 only: the
> server identify API call and the routing ladder in identify.ts, preserving
> the IdentifyResponse shape and surfacing unreviewed_ids. Do not implement the
> consent sheet. Run the backend suite and mobile typecheck, then stop and
> report which ladder paths you could verify without a device.
