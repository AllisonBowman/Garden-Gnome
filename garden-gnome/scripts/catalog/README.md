# Catalog landing tools

The three checks every research batch passes before it is copied into
`app/data/verified/`. They lived in a session scratchpad for b43–b68; they
live here so the next session does not have to rebuild them.

Run each from `garden-gnome/` with the project venv (`.venv/bin/python`).

- `covered.py "Genus species" ...` — exact-match dedup of candidate binomials
  against every landed batch, on the given *and* accepted names, cultivar and
  varietal tails stripped. Use it to pick a batch instead of a substring grep,
  which false-positives on citation quotes and misses reclassified names.
  Exit 1 on any `DUP`.
- `land_check.py bNN_records.json` — the per-batch landing review of a raw
  Workflow result: `name_note` implies a `name_note`-labelled citation, every
  non-null field traces to a citation through the real loader
  (`app.data.claims.tranche.claims_from_record`), exact dedup against the
  corpus, and dumps of every audit-flagged entry and every `toxic_to_pets`
  citation for the cat/dog-scoping check. Exit 1 on any problem, including an
  empty batch (an all-failed workflow returns `records: []` with no error).
- `verify_quotes.py path/to/batch.json ...` — fetches every cited page (raw
  HTML cached in `.quote_cache/`, one request per URL ever, throttled per
  host, browser UA), strips `aria-hidden` tooltips, and checks the quote is on
  the page after normalisation. `MISS` is the fabricated-or-paraphrased quote
  candidate; `INCONCLUSIVE` is a page-level failure; `SKIP` is a PDF or a host
  that refuses non-browser clients (`plantfinder.mobot.org`,
  `ask.ifas.ufl.edu`). Exit 1 on any `MISS`. The auditor's live fetch remains
  the final word for structured-field readbacks the page renders as separate
  elements.

The corpus-wide shape guards the loader cannot tolerate breaking (enum
tokens, stray keys, string-`"null"`, duplicate species) are a permanent
pytest, `tests/test_tranche_invariants.py`, not a script.
