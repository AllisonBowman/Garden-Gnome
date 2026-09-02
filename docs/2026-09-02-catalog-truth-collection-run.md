# Catalog-truth collection run — b19 through b46, and the tooling it produced

For the next session. Follows `docs/2026-08-03-catalog-truth-handoff.md`. The
plan is still `~/.claude/plans/the-app-needs-a-twinkling-crown.md`; this is the
state of the evidence-collection half of it as of 2026-09-02.

## Where things are

Branch `care-advice-honesty`, pushed with this note. The claim graph
(`Authority` + `Claim` tables, resolved into `Species` columns by an idempotent
`recompute`, ADRs 0001–0004) is built, tested, and populated from
`garden-gnome/app/data/verified/b1..b46.json`:

- **52 batches, 2,322 claims, 397 species, 8 authorities** (b47–b52 landed
  after this note was first written, at the overnight throttle described
  below; the per-batch breakdown in the test comment is current). The running total
  is asserted in
  `tests/test_claim_ingest.py::test_the_whole_verified_tranche_lands_and_resolves`,
  with a per-batch breakdown in the comment above it. (b1–b18 covered the
  original 129-species curated catalog; b19 onward is a "blind spots" pass —
  toxic ornamentals, trees, shrubs, vines, bulbs, fruit and nut crops, grasses,
  groundcovers, ferns, succulents, palms, gesneriads, conifers, carnivores.)
- Every batch was produced by a research → adversarial-verify Workflow (one
  extraction agent and one auditor per species, the auditor instructed to
  live-fetch and refute), then re-verified locally before landing. Each batch
  file carries a `normalizations` entry saying what that pass caught.
- **Nothing in the claim graph is wired into `SpeciesRead` or the mobile
  `Species` type.** None of this is visible to a user yet. That is the next
  phase, and the reason no TestFlight build has been cut since 1.1.2 (Aug 2) —
  the user chose to wait until the database is closer to complete.

## What was added this run besides data

1. **`tests/test_tranche_invariants.py`** — corpus-wide shape guards the
   pipeline genuinely cannot tolerate: the five strict-enum columns
   (`SoilBase`, `SoilDrainage`, `WaterRegime`, `HumidityNeed`,
   `FertilizeStrength`) hold a token from the model's own enum,
   `outdoor_sun_exposure` items are `OutdoorSunExposure` members, no keys
   outside the 35-field research schema, no string-`"null"`, non-null
   `common_name`, every citation has claim/source/url/quote, and no species
   appears in more than one batch. `recompute.py` writes with a bare
   `setattr` — no enum coercion — so a sentence in `soil_drainage` would land
   in the column silently; this is what stops it. Its first run over b1–b45
   found 7 legacy records (b6, b16, b17, b18) with free-text sun-exposure
   phrases from before the token convention settled; they were normalized in
   place (values only, quotes untouched, dated note in each file).
2. **A mechanical citation verifier** (session scratchpad, not in the repo —
   see below): fetches every cited URL (cached raw HTML, throttled per host,
   browser UA), strips `aria-hidden` tooltips, and checks the quote is on the
   page. Proven on b43–b45 at 0 misses across every reachable quote, and it
   independently caught the one synthesized quote the b44 auditor also caught.
   ~19% of citations can't be checked from here: `plantfinder.mobot.org` and
   `ask.ifas.ufl.edu` refuse non-browser clients, and 31 citations are PDFs.
   A corpus-wide backfill was run at the end of this session; its findings are
   in the "Verifier backfill" section below.
3. **Model split** (from b46): research agents on Sonnet, verify agents on
   Opus, orchestration on Fable 5.1 — after b46's first attempt died on a
   session limit with all eight research agents refused. From b47 the loop
   ran at an overnight throttle the user asked for: six species per batch,
   research at medium effort, one batch in flight at a time, a checkpoint
   push every batch or two (`80e420e`, `51714e7`, `feb62e3`). Audit quality
   went up, not down, on the split — the Opus auditor's findings come with
   corrected wording and it caught a wrong-species common name (b46), a
   truncated poison-part list on a plant people dig up as a ginger
   substitute (b50), and several safety fields trimmed of a co-listed tag or
   a dose sentence. Two usage-limit incidents: b46's research stage (all
   agents refused → empty batch; `land_check.py` now exits 1 on zero
   records) and b51's verify stage (four of six audits refused; the fix is
   a resume, which replays the cached research and re-runs only the failed
   audits). b52's verify stage then failed on a DNS outage rather than a
   limit, and the null-verdict guard added to that batch's script did its
   job: every record came back flagged UNVERIFIED in the output's
   `unverified` list instead of the pipeline throwing, and a plain resume
   re-ran only the six audits. Keep that guard in every script from here.
   The recurring defect themes across b47–b52, each now guarded in
   the prompts: "moist but well-drained" read as the wet end of the drainage
   scale rather than the middle; a watering cadence read off a soil
   adjective or a drought-tolerance trait; a shade token added from a
   conditional clause or a UK-calibrated RHS tag that both North American
   structured fields exclude; an open-ended NC State pH band read as a
   ceiling; a name_note that calls RHS's botanical-name H1 a common-name
   lead, or MoBot's displayed Common Name field "single" when a longer
   list sits behind it; and — found by the mechanical check, missed by the
   Opus auditor — raw `</dt> <dd><span class=…>` markup pasted into quotes
   around NC State field values (b52, six quotes). Landing review also
   has to check common_name collisions across batches: b52's Dicentra
   eximia came back as "Bleeding-heart", which b36 already uses for
   Lamprocapnos spectabilis, and landed as "Fringed Bleeding Heart"
   (RHS's lead name, attested by all three sources).

## Defect classes found and closed (each now guarded in the prompts or tests)

- `toxic_to_pets` asserted from evidence scoped to rabbits/birds/horses or an
  unscoped "pets" — the field tracks cats and/or dogs only (b31/b32).
- Prose landing in strict-enum columns (b36) — invariant test.
- Stray scaffolding keys in a record (b38) — `additionalProperties: false`
  plus the invariant test.
- `common_name` and list fields nulled wholesale when one entry or one
  citation was refuted (b39/b40) — the script now flags these for review
  instead of nulling.
- Fabricated citations: an invented NC State poisoning entry and invented
  drainage tags (b42), a synthesized RHS "Winter resting period:" label
  presented as a quote (b44) — caught by the auditor's live fetch, now also
  by the verifier.
- Freeze-survival threshold conflated with chill-damage onset (b43) —
  prompts now state the distinction; Pomegranate in b45 is the model record.
- HTML markup pasted into quotes (b52) — the verifier catches it (the
  page's rendered text never contains the tags); prompts now forbid it.
- A label+value concatenation quoted as if contiguous ("Name Status
  Correct", b52) — the value alone is the quote; prompts now say so.

## Do next, in order

1. **Wire the claim graph into the app.** `SpeciesRead`, the mobile `Species`
   type, and the advice fact block should read resolved values with their
   provenance. Until then the 2,000+ claims are review artifacts.
2. **Decide the verifier's home.** It lives in the session scratchpad
   (`verify_quotes.py`, `covered.py`, `land_check.py`), which is
   session-scoped. If the collection run continues, move them under
   `garden-gnome/evals/` or a `scripts/` dir so they survive; the invariant
   test already holds the half that matters most.
3. **Rename `hardiness_zones`** (Species column, migration 0013) to what USDA
   PLANTS actually publishes — still open from the previous handoff.
4. **Phase 4.1 name resolution** for the 2 skipped curated-catalog mismatches
   — still open.
5. **Then plan the next TestFlight build** — see
   `docs/2026-08-08-testflight-1.1.3-handoff.md` for the ship sequence; 1.1.3
   was never built or submitted.

## Verifier backfill (2026-09-02, all batches through b45)

Of 5,309 citations: **3,752 verified verbatim on the live page, 52 could not
be settled mechanically, 1,505 unreachable** from the sandbox (MOBOT and Ask
IFAS refuse non-browser clients; 31 are PDFs).

The 52 are all readbacks of structured fields — NC State tag lists and
`Common Name(s): … Scientific Name: …` label composites, RHS `Synonyms … Name
Status` blocks, UGA table coding keys — where every word is on the page but
the page renders them as separate elements, often in another order. A
substring check can't confirm or refute those; the b19+ auditors' live
fetches remain the check for that class. Nothing in the 52 is a prose
sentence.

What the backfill actually changed:
- **1 fabricated citation removed** — Leyland Cypress (b42) drainage tags the
  page doesn't carry; the value was already nulled at landing but the citation
  had been left behind.
- **1 fabricated-tag citation found, field nulled** — Common Morning Glory
  (b14) `soil_drainage` cited `Occasionally Dry Occasionally Wet` tags; the
  page has only `Good Drainage` and `Moist`. Same shape as Leyland Cypress,
  from before the fabrication check existed. Claim count 2086 → 2085.
- **3 unverifiable corroborating quotes dropped, values kept** — Bloodroot
  (Penn State), Bay Laurel (a UGA guide-scope sentence that isn't on the
  page; NC State's own `Problem for Cats / Problem for Dogs` tags carry the
  cat/dog scoping), African Violet (Penn State). Each value has an
  independent, verified primary citation.
- **5 lightly paraphrased quotes replaced with the page's verbatim sentence** —
  Butterfly Bush, Beets, Cowpea, Angel's Trumpet, Castor Bean. Facts
  unchanged; the quotes had been rewritten as if verbatim.

Every change carries a dated line in the record's `unknowns`.
