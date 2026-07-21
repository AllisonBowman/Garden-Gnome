# PlantAdvocate — Identification Strategy Revision

Implementation plan for Claude Code. Triggered by a real finding from a
TestFlight build on an iPhone 17 Pro Max: **on-device identification does not
reliably distinguish visually similar species.**

## Why it fails (this is not a tuning problem)

The current on-device pipeline, in `mobile/modules/plant-id/ios/PlantIdModule.swift`:

```
photo → VNClassifyImageRequest → ≤8 labels (confidence > 0.1) → Foundation Models → species name
```

**The photo is discarded before any reasoning happens.** Foundation Models
(iOS 26) is a *text* model — the module's own README says so — so Vision is
used to turn the image into labels first. But `VNClassifyImageRequest` returns
a fixed, coarse taxonomy. A Pothos and a Heartleaf Philodendron both reduce to
roughly `plant`, `leaf`, `houseplant`, `flowerpot`. Two different species,
identical model input.

This is an **information bottleneck, not a model-quality problem**, which is
why the usual levers won't move it: a better prompt, a better text model, or a
larger catalog all operate downstream of where the discriminating detail was
thrown away. The fix is a model that sees pixels.

## The catalog size is what makes the fix cheap

The catalog is **129 species**. The full name list is ~2,000 tokens, so every
identification request can carry *every* candidate and ask the model to pick.

That means **no embedding index, no vector store, no retrieval step** — brute
force is the correct design at this size, and it is strictly more accurate than
any pre-filter, because the model sees every option. `_build_identify_prompt`
in `app/services/vision.py` does exactly this, and `candidate_ids` maps the
model's answer back to real catalog rows so only records with real care data
are ever offered.

**Revisit this above roughly 1,000 species**, where the candidate list starts to
dominate the request and cost per call. Below that, adding retrieval machinery
would be pure complexity.

## Ground rules

- **On-device is demoted, not deleted.** It becomes the offline path, the
  privacy-preserving option, and the fallback when the server is unreachable.
  The EAS/native work is not wasted.
- **Never assert a species we can't back with care data.** Both paths already
  ground against the catalog; keep it that way. Out-of-catalog plants get an
  honest "not in our catalog yet", never a forced nearest match.
- **Every failure degrades to manual search**, which always works.
- No schema migrations in this plan.

## Decisions already made

| Question | Decision |
|---|---|
| Cloud model | **Sonnet 5** (~$0.008/photo at intro pricing, ~125 photos/dollar) |
| Routing | **Server first, on-device fallback** |
| Catalog strategy | Send all 129 candidates; revisit above ~1,000 |

---

## Phase 0 — Cloud vision backend ✅ done on this branch

`VISION_BACKEND=anthropic` now drives **both** identification and diagnosis
through one setting. `app/services/vision.py` gained `_identify_anthropic` and
`_diagnose_anthropic` over a shared `_anthropic_vision_chat`, using
`AsyncAnthropic` (the module promises never to block the event loop, so the
sync client `advisor.py` uses would be wrong here).

Notes for whoever picks this up: Sonnet 5 **rejects** `temperature`/`top_p`/
`top_k` — a test asserts they're never sent. Adaptive thinking is on with
`effort` configurable via `ANTHROPIC_VISION_EFFORT` (default `medium`);
raise it if similar species still confuse the model. `/ai/status` reports
readiness from key presence only — a live probe would cost tokens per poll.

**Care advice needs no code.** `advisor.py` already has `_advise_anthropic`;
`ADVISOR_BACKEND=anthropic` is a config change.

## Phase 1 — Mobile routing (server first)

`mobile/src/api/` has **no server identify call at all** today —
`identifySpeciesPhoto` in `src/photoId/identify.ts` goes straight to the native
module. Add one.

1. New `identifySpeciesPhoto` API call against `POST /species/identify-photo`
   (already implemented, `app/routers/species.py`). It returns ranked
   `candidates` already matched to catalog IDs plus `observation` text.
2. Rewrite `src/photoId/identify.ts` as a ladder, preserving the existing
   `IdentifyResponse` shape so `AddPlantScreen` needs no changes:
   - **Server** when reachable *and* `/ai/status` reports vision ready →
     use `candidates` directly (already grounded server-side; no fuzzy match).
   - **On-device** when the server is unreachable or not enabled, and
     `isAvailable()` is true → existing Vision + Foundation Models path,
     still grounded through `fuzzyMatch.ts` (`CONFIDENT` 0.6 / `PLAUSIBLE` 0.42).
   - **Manual search** otherwise — the current fallback, unchanged.
3. Surface which path answered, so the eval can tell them apart. `backend` is
   already on `IdentifyResponse`; keep it honest (`anthropic` /
   `apple-foundation-models` / `unavailable`).

**Accept when:** a dev build identifies via the server with the backend
enabled, falls back to on-device with the server stopped, and falls back to
search with both unavailable — verified by flipping each off in turn.

## Phase 2 — Consent (blocks App Review)

Server-first means **photos leave the device**, and there is currently **no
consent copy anywhere in `mobile/src`** — nothing needed it while everything
was on-device or stubbed.

- The **first** time a photo would be uploaded, show a consent sheet: what is
  sent (the photo), where (our server), why (to identify the plant), and that
  it isn't stored beyond the request. Store the choice on the user profile.
- Declining is a first-class outcome, not an error: the app silently uses the
  on-device path (or manual search) from then on, and the choice is reversible
  in Settings.
- On-device identification needs **no** consent — nothing leaves the phone.
  Don't prompt for it.

**Accept when:** a fresh install prompts once before the first upload, never
again; declining still yields a working identify flow; the setting is visible
and changeable in Settings.

## Phase 3 — Measure it

This is where `plantadvocate-vision-eval-plan.md` finally has something worth
measuring, and its scoping problem resolves: with `VISION_BACKEND=anthropic` driving
both features, its D-gates (diagnosis) and I-gates (identification) now cover
paths users can actually reach.

Minimum bar before trusting the pivot: **20–30 photos across at least 5 pairs
of visually similar catalog species** — the failure that started this. Compare
server vs on-device on the same photos; the delta is the whole justification
for the added cost and the consent prompt.

Record cost per identify from the `usage` line `_anthropic_vision_chat` logs,
and re-tune `ANTHROPIC_VISION_EFFORT` against it.

## Phase 4 — Revisit triggers

Write these down so future-you knows when this design expires:

- **Catalog > ~1,000 species** → the all-candidates prompt stops being cheap;
  add retrieval (or filter candidates by the on-device Vision labels first).
- **Foundation Models gains image input** → on-device could return to primary,
  which would remove both the per-photo cost and the consent requirement.
  Worth re-checking at each iOS release; the current README note is already
  stale-dated.
- **Cost becomes material** → try Haiku 4.5 against the Phase 3 photo set
  before assuming it's worse.

---

## Explicit non-goals

- Growing the catalog (a separate, larger effort; `app/data/expansion/` exists).
- Replacing `fuzzyMatch.ts` — still needed for the on-device path.
- Open-world identification. Out-of-catalog stays an honest "not in our
  catalog yet".
- Android/Gemini Nano routing — same ladder applies, but it's untested and
  out of scope here.
- Re-tuning diagnosis prompts (that's the alignment plan).

## Suggested kickoff prompt

> Read plantadvocate-identify-strategy-plan.md. Implement Phase 1 only: the
> server identify API call and the routing ladder in identify.ts, preserving
> the IdentifyResponse shape. Do not implement the consent sheet yet. Run the
> backend suite and mobile typecheck, then stop and report which of the three
> ladder paths you were able to verify without a device.
