# Hybrid binomials, end to end (2026-09-13)

The pipeline dropped hybrid names because "the landing pass needs a bare binomial". Nine common garden
plants were lost to that rule: Chrysanthemum × morifolium, Nepeta × faassenii, Calibrachoa × hybrida,
Verbena × hybrida, Fuchsia × hybrida, Citrus × aurantiifolia, Spiraea × vanhouttei, Canna × generalis,
Crocosmia × crocosmiiflora. `Genus × epithet` (U+00D7) is now a first-class name everywhere.

## The decision that everything else follows

**One normaliser, in `app/data/claims/names.py`.** Four private copies of "what makes two names the same
name" existed (`sync.binomial_key`, `covered.norm`, `test_tranche_invariants._binomial`,
`validate._name_key`) and no two agreed. They now all call one module:

- `canonical(name)` — the stored spelling: the marker spaced, whitespace collapsed.
  `"Nepeta ×faassenii"` → `"Nepeta × faassenii"`.
- `key(name)` — the matching key: canonical, marker folded to `x`, case-folded.
  `"Nepeta × faassenii"` = `"Nepeta ×faassenii"` = `"Nepeta x faassenii"` = `"Nepeta  X faassenii"`.
- `words(name)` — the words with the marker set aside, so a shape check counts a hybrid as the two-word
  binomial it is. `"× Fatshedera"` is still **one** word, i.e. still a bare genus.
- `genus_token(name)` — the genus word, marker excluded (`"× Fatshedera lizei"` → `Fatshedera`).

**The marker stays significant in a key.** `Citrus × aurantiifolia` and `Citrus aurantiifolia` remain two
keys. Folding the marker away (the other option on the table) would merge a nothospecies with a
same-epithet species on the assumption they are one taxon; that is a guess about which plant the evidence
describes, and the sync would then quietly pour two plants' claims into one row. Only the three
*spellings* of one marker are folded. A leading ASCII `x` counts as a marker only where it already stands
alone as a word, so `Solanum xanti` and `Xanthosoma sagittifolium` are untouched.

**Where a name is normalised: at landing.** `repair_lib.generic_passes` rewrites `scientific_name_given`
and `scientific_name_accepted` to the canonical spelling before asserting, so the corpus holds one
spelling. Verified: no landed record contains a spaceless marker today, so this is a no-op over the
existing 80 batches and needs no data migration. The corpus does hold both the `×` and the ASCII `x`
spelling (`Fragaria x ananassa`, `Abelia × grandiflora`); those already keyed alike and still do — the
landing pass does not rewrite an ASCII marker, it only fixes spacing.

## What changed

| File | Change |
| --- | --- |
| `app/data/claims/names.py` | NEW. The one normaliser (above). |
| `app/data/claims/sync.py` | `binomial_key` delegates to `names.key`; `_subject_of` canonicalises; the genus gate counts `names.words`, so `× Fatshedera` is still refused as a bare genus. |
| `app/data/claims/tranche.py` | `Claim.subject` canonicalised — the same expression as `_subject_of`, so stored subjects and matched keys cannot drift. |
| `app/data/claims/ingest.py` | the unsupported-field report keys by the same canonical subject. |
| `app/data/claims/resolve.py` | `genus_of` reads the first *word*: `Clematis × jackmanii` → `Clematis`, `× Fatshedera lizei` → `Fatshedera` (was `×`, one phantom genus shared by every nothogenus). |
| `app/data/expansion/validate.py` | `_name_key` folds the marker — it was the only key that did not fold it at all. |
| `scripts/catalog/covered.py` | `norm` = `names.key`; genus near-miss hint skips a leading marker; docstring. |
| `scripts/catalog/pipeline/repair_lib.py` | THE blocker. The two-token assert now counts `names.words` after canonicalising. Also renamed a local `names` list to `commons` — it shadowed the module for the whole function. |
| `scripts/catalog/pipeline/harvest.py` | the auditor-prompt regex admits all four spellings, still anchored to the first parenthetical so one species' findings cannot be keyed onto another. |
| `scripts/catalog/pipeline/gap-finders.js` | criterion 2 admits garden-origin hybrids; criteria 3 and (b) keep the marker as an `x` slug segment (`nepeta-x-faassenii`; stripping it 404s); the `latin` spec and clause (c) accept `Genus × epithet` and forbid parent substitution; `norm` folds `/×/g` to `' x '`. |
| `scripts/catalog/pipeline/template-research.js` | rule 14 rewritten (the sign is part of the name; never substitute a parent; never re-file as a cultivar); `common_name` tie-break and the auditor's "dedicated page" both say *taxon*, hybrid or species; the provenance checklist forbids refuting a name merely for carrying `×`; check 5 names the parent species as the primary bleed risk. |
| `README.md`, `LANDING_BRIEF.md` | the "bare binomial" rule restated so it still bans authorship and keeps the marker. |
| `batches-b89-hybrids.json` | NEW. The nine, back in the candidate pool with research notes in house style, ready for `gen_batch.py` (step 2). No research launched. |

## Tests

`tests/test_hybrid_names.py` (new) pins the rules and, more importantly, that all four gates key a name
identically. Added elsewhere: the landing gate accepts the nine and still refuses authorship / cultivar
tails / a bare genus / an upper-case epithet (`test_catalog_scripts.py`, which also now covers the
harvester regex and the prompt wording); a hybrid mints a row, two spellings become one row holding all
the evidence, and a bare nothogenus is still a genus (`test_claim_sync.py`); a hybrid inherits from its
genus and not from the marker (`test_claim_resolution.py`); the duplicate-check key (`test_tranche_invariants.py`);
the expansion admit path (`test_expansion_guards.py`). Every ordinary-binomial and cultivar-suffix
behaviour is pinned unchanged alongside.

`.venv/bin/python -m pytest -q` → **4011 passed, 0 failed** (3941 before this change; 70 new tests),
run at 21:05. A later run reports `1 failed, 4106 passed`: while this work was in progress another
process landed `b82-perennials.json` and `b83-annuals.json` into `app/data/verified/` (21:18, 21:19),
which is the documented mid-landing state -- `test_claim_ingest` pins the corpus claim count and now
reads `3049 == 2989`. `commit_batch.py` bumps that number when the batch commits. Neither new batch
contains a hybrid, and the whole suite minus that one count test is green (4100 passed).
`land_check.py` re-run over the landed hybrid batches b42 and b37: `problems: none` — the respacing
introduces no spurious DUP.

## Known, deliberately not done

- **Mobile search will not find a hybrid.** Four hand-rolled substring filters (`mobile/src/almanac/tier.ts`,
  `screens/SpeciesScreen.tsx`, `screens/AddPlantScreen.tsx`, `screens/CaptureGardenScreen.tsx`) compare
  `scientific_name.toLowerCase().includes(query)`, so typing "nepeta faassenii" or "nepeta x faassenii"
  returns nothing for `Nepeta × faassenii` (and U+00D7 is not on the iOS keyboard). The real matchers
  (`photoId/fuzzyMatch.ts`, `app/services/name_match.py`) already handle it. Fix is to route all four
  through one helper built on `fuzzyMatch.normalize`. Out of this change's scope (backend pipeline), but
  it should land before the nine do, or they will be researched and unusable in the add-a-plant picker.
- **`sync._mint_and_link` indexes only the accepted name** of a row it mints, so a later batch citing the
  *given* name mints a second, claim-less row. The hybrid instance of this disappears with the key fix;
  the synonym instance (Dypsis → Chrysalidocarpus) remains. Left alone: general defect, not hybrid-specific.
- **A claim filed under a bare nothogenus subject** (`× Fatshedera`) will not be inherited by its
  nothospecies, because `genus_of` returns `Fatshedera`. No such claim exists in the corpus.
