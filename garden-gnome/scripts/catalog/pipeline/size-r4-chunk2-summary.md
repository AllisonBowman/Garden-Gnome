# Size backfill, round 4 chunk 2 -- landing summary

Landed 2026-09-27 from `size-r4-chunk2-result.json` (23 species over b86, b87, b88 and b9; 0 unverified, 0
no_research; 2 fields already nulled on audit; 12 review lines), following `BACKFILL_LANDING_BRIEF.md`. Not
committed.

The landing went in two passes because the quote cache was wiped partway through (see "The quote cache" below).

- First pass: 19 species, from `size-r4-chunk2-result.json`.
- Second pass: the four b86 bulbs (Calla Lily, Common Snowdrop, Grape Hyacinth, Tiger Lily), from
  `size-r4-chunk2-b86-held-result.json`. It ran after the cache was restored, since their pages had never been cached
  before. That file stays as the record of that payload.
- Also: one correction outside the backfill that the coordinator authorized, to Creeping Fig's is_edible in b87.

The untouched workflow output, the four batch files as they were at the start and the intermediate states are kept in
the session scratchpad. The two repairs were done by scripts there. They asserted that every edited quote is a
substring of the quote it replaces, and re-derived every size value from its quote.

## Result

- b86-bulbs-patio: 63 -> 90 claims (+27)
- b87-mixed: 55 -> 74 (+19; +20 from the backfill, -1 for Creeping Fig's is_edible)
- b88-mixed: 41 -> 48 (+7)
- b9-veg-round2: 56 -> 83 (+27)

That is +80 claims against HEAD (f6d0044). The ingest test now prints `assert 6090 == 6010`, and nothing else was
uncommitted in `app/data/verified/`.

## Merge plan totals

Both payloads printed "problems: none" and were applied. Together they wrote 19 species, 81 fields and 55 citations:

- `size-r4-chunk2-result.json`: 15 species, 60 fields, 41 citations.
- `size-r4-chunk2-b86-held-result.json`: 4 species, 21 fields, 14 citations. Calla Lily's size citation was split in
  two, so it lands 14 citations rather than the 13 it arrived with.

The 81 fields are 56 size bounds (14 species), 14 is_edible (11 true, 3 false) and 11 attracts_pollinators (all
true). Four species wrote nothing. Cape Leadwort and Blushing Philodendron are climbers with no edibility or
pollinator statement. Creeping Fig and Boston Ivy are covered in "Fields nulled at landing".

A semantic check against HEAD confirmed the merge only added, apart from the Creeping Fig correction. Every
pre-existing value, citation, unknowns line and normalization in the four files is unchanged, and the only new keys
are the six backfill fields (the written records had never carried them). Every new value pairs to a citation written
with it. Each apply added merge_backfill's standard normalization line, so b86 carries it twice, as 21 committed
files already do after more than one backfill landing. In the git diff, the lines shown as deleted are serialization
only. They are lines that gained a trailing comma, plus the four files' last line: at HEAD they had no final newline,
and now they end with one.

## The 12 review lines

The rule applied is the brief's. A correction goes in only if the stored quote is spliced (it carries U+23CE, or a
label is glued to its value) and the correction is that same text as the page renders it, or a substring of the
stored quote. Every correction was confirmed on the cached page with qc.py first.

- Yellow Cosmos and Calla Lily, 4 size lines each: APPLIED, but not as proposed. Both stored quotes were U+23CE
  "Dimensions:" splices. Yellow Cosmos's proposed correction was itself a " ... " composite joining two rendered
  lines. Each species' one citation was split into a height citation and a spread citation. Each is its own rendered
  line on the page and a substring of the stored quote: "Height: 2 ft. 0 in. - 3 ft. 0 in." / "Width: 1 ft. 0 in. -
  3 ft. 0 in." (Yellow Cosmos) and "Height: 2 ft. 0 in. - 3 ft. 3 in." / "Width: 1 ft. 0 in. - 2 ft. 0 in." (Calla
  Lily). No value changed.
- Yellow Cosmos, attracts_pollinators: HELD. "Attracts pollinators and butterflies" is NC State's Wildlife Value
  field, a different element from the stored U+23CE Attracts quote. The stored quote was de-spliced to its stacked
  value "Pollinators", and the claim now reads "NC State structured Attracts field lists Butterflies and Pollinators".
- Calla Lily, attracts_pollinators: HELD. "Beetles and bees pollinate the flowers." is also the Wildlife Value field.
  The stored "Attracts: ⏎ ⏎ ⏎ Bees" was de-spliced to the field's single value, "Bees".
- Tiger Lily, attracts_pollinators: HELD. The stored quote "Butterflies" is a clean value of the Attracts field
  (Butterflies, Hummingbirds), not a splice. The proposed "Flowers attract swallowtail butterflies." is the Wildlife
  Value field. The stored quote stays.
- Boston Ivy, "REFUTED but unmapped field unknowns": worked. The two lines the auditor named were dropped: one framed
  is_edible as true on NC State's "#edible fruits" / "Edible fruit" tags, and one said RHS carries no harm or pets
  warning. RHS reads "Harmful if eaten; skin irritant." and "Pets: Harmful if eaten; skin irritant". The audit's own
  removal line stays. This is moot for the catalog, because Boston Ivy writes nothing.

No held correction left a field unsupported.

## Fields nulled at landing, and why

- Creeping Fig, is_edible, under standing rule 2 at the coordinator's instruction. NC State's Edibility field reads
  "Not usually grown for edible fruit, but properly prepared it is popular in Asian countries." That is a marginal
  food use, and the app shows is_edible true as "grown to eat". b87 already held is_edible true from the original b87
  landing (67b7c8b), on the same quote, so the backfill could not change it. Two things were done:
  - In the result file, the proposal was nulled and its citation dropped. Creeping Fig therefore writes nothing: it is
    a climber, so no size, and attracts_pollinators is null.
  - In b87, the coordinator authorized one direct correction outside the backfill. Three changes were made and
    nothing else in the record was touched:
    - is_edible true -> null;
    - the one citation that supported only is_edible ("is_edible — NC State's Edibility field states") was removed;
    - one unknowns line was appended. It quotes the Edibility text, "They are insipid and not worth eating.",
      "Inedible figs appear after the spring flowers on plants grown outdoors", and the tags "#problem for dogs
      #problem for horses #problem for cats", and says it supersedes the older line that sets is_edible true. That
      older line was left in place, as instructed.
  The record lost one claim (9 -> 8). The toxicity_detail citations to the same page, including the insipid and
  Inedible figs quotes, stay. No normalization line was added to b87 for this.
- Boston Ivy, attracts_pollinators: moot. b88 already holds it true on the same two citations, and a backfill never
  overwrites. Both duplicate citations were dropped (the wave 1 chunk 1 precedent). With is_edible nulled on audit and
  sizes null (climber), Boston Ivy writes nothing.

The two fields nulled on audit stay null.

- Boston Ivy is_edible. RHS's "Harmful if eaten; skin irritant." is set against NC State's play-value "Edible fruit".
- Tiger Lily is_edible. NC State's Edibility field reads "The bulbs are said to be edible.", while RHS reads
  "Ornamental bulbs - not to be eaten. ... TOXIC to pets if eaten (cats)".
  - The auditor nulled it partly because the RHS page could not be read then. It is cached now and the line is
    confirmed.
  - It stays null on the pages' conflict and on standing rule 2: a poisonous plant whose only food mention is hedged.

Nothing was nulled under the houseplant size rule (standing rule 4). The houseplants that write a size are Bush Lily
(18-24 by 24-36 in) and Calla Lily (24-39 by 12-24 in), both well under 120 in. The six climbers' sizes were null
already under standing rule 3: Cape Leadwort, Blushing Philodendron, Creeping Fig, Boston Ivy, Butter Beans and
Cowpea.

## Edibility calls under standing rule 2

- Kept true, with the condition in unknowns:
  - Butter Beans: raw mature seed is poisonous (hydrocyanic acid, high severity). The Edibility field's full
    preparation was added: a 12-hour soak and thorough cooking.
  - Parsnip: only the first-year taproot is eaten. The furanocoumarin skin hazard was corrected (below).
  - Swiss Chard: oxalic acid (UMD).
  - Cowpea: pods are eaten immature.
  - Habanero Pepper: NC State's bare "Problem for Children".
  - Brussels Sprouts and Collard Greens: "Problem for Horses".
- False, each on a page's own statement:
  - African Blue Lily: "Poisonous through ingestion and dermatitis."
  - Bush Lily: NC State's "Poisonous to Humans" block and its ingestion symptoms.
  - Common Snowdrop: its Edibility field, "Bulbs are toxic if eaten".
- Plain true: Cabbage, Carrot, Cauliflower, Sweet Corn.
- Null: Calla Lily and Grape Hyacinth (no food use; RHS warns against eating both), Tiger Lily and Boston Ivy (above),
  and Cape Leadwort, Blushing Philodendron and Creeping Fig.

## Unknowns corrected and added

Corrections are marked "corrected at landing". Added lines end "noted at landing, verified against the cached copy".
What each one states was read on the cached page.

- Bush Lily:
  - NC State's Poison Part is Flowers, Fruits, Leaves, Roots, Seeds and Stems; the note had only Flowers and Fruits.
  - RHS's Potentially harmful field reads "All parts may cause a stomach upset if ingested; sap may irritate skin.
    ...". That disagrees with NC State's "Causes Contact Dermatitis: No".
  - "Vomiting, salvation, diarrhea" in the is_edible quote is the page's own typo, quoted verbatim.
- Parsnip. Poison Part is Flowers, Fruits, Leaves, Sap/Juice, Seeds and Stems. The note's "exposure to the sap
  combined with sunlight ..." is not on the page, so the line now quotes the Poison Symptoms field and the
  Description's furocoumarin gloves warning.
- Cabbage. UMD's spacing is "15\" - 18\" in-row x 30\" - 36\" between rows"; 12 in is its "close spacing" example.
  HGIC could not be re-checked from here.
- Carrot. RHS gives 0.1-0.5 m for both height and spread (about 3.9-19.7 in). Its height band sits inside NC State's
  3-36 in, but its spread band does not overlap NC State's 2-3 in. The note had called RHS "not needed". An added
  line says carrots flower only in their second year, so a crop pulled for its root does not flower.
- Cowpea. The note's literal searches missed UMD's "on the bush, vining, or semi-vining plants" and its fresh-pea and
  dried-pea harvesting lines.
- Sweet Corn. UGA's "ft" figures also include the 500 ft isolation distance and 3 ft row spacing. The Clemson line
  was corrected: qc.py returned a ProxyError for Clemson to the auditor.
- Butter Beans, added: NC State's Edibility field in full, and its Plant Type listing the species as both Edible and
  Poisonous.
- Calla Lily:
  - RHS's "Harmful if eaten; skin/eye irritant." (people and pets) was added to the edibility line, which had said
    no page addressed eating.
  - The poison line now gives Poison Part as Flowers, Leaves, Roots, Sap/Juice and Stems (it had Flowers and Leaves),
    and restores the symptoms' opening words, "Oral irritation, pain, and".
  - Plant Type gains its missing "Poisonous".
- Grape Hyacinth. The note said neither page addresses eating. RHS reads "Ornamental bulbs - not to be eaten" for
  people and pets. is_edible stays null, as Dutch Crocus did in wave 1: the research did not propose false.
- Tiger Lily. The edibility line still said is_edible "was set false"; it now says the audit nulled it, and why it
  lands null. The fetch line said both pages fetched ok; it now records that the auditor could not read RHS and that
  the cached copy was confirmed at landing.
- Creeping Fig and Boston Ivy in the result file: as above. Neither travels, because neither writes a field.

## Other flags

- Blushing Philodendron. Its auditor raised two points, and I changed neither.
  - NC State gives an explicit indoor size ("When grown indoors, It typically grows 3 ft. tall and 16 inches wide").
    Standing rule 3 (climbers take no size) wins.
  - Its "#poisonous if ingested" tag could support is_edible false. A landing can only null, not set.
- b9 has four pre-existing is_houseplant values the loader cannot pair to a citation: Brussels Sprouts, Cauliflower,
  Swiss Chard and Sweet Corn. They are identical at HEAD, and this landing did not touch them.

## verify_quotes, per touched file

verify_quotes.py fetches any uncached URL live and still caches http-403 responses, so it was not run as is. Instead,
its own `check()` was run unchanged, with `fetch` replaced by a read of the cache entry for the exact URL. That means
no network and no writes, and an uncached page counts as SKIP, exactly as a failed fetch does. Final run, after both
payloads and the Creeping Fig correction:

- b86-bulbs-patio: 213 hit, 0 MISS, 0 inconclusive, 40 skipped (HEAD: 195 hit, 40 skipped)
- b87-mixed: 146 hit, 0 MISS, 0 inconclusive, 25 skipped (HEAD: 135 hit, 25 skipped)
- b88-mixed: 114 hit, 0 MISS, 0 inconclusive, 5 skipped (HEAD: 109 hit, 5 skipped)
- b9-veg-round2: 77 hit, 2 MISS, 0 inconclusive, 23 skipped (HEAD: 57 hit, 2 MISS, 23 skipped)

Under commit_backfill's rule, there is no NEW-FIELD MISS, SKIP or INCONCLUSIVE in any of the four files, and all 55
new citations HIT. Hits rose by the new citations: +18, +12 less the removed Creeping Fig citation, +5 and +20. Each
file's SKIP lines are identical to HEAD's. They are the Missouri Botanical Garden and Clemson pages that refuse this
machine, plus one UGA PDF.

b9's two MISS lines predate this landing, appear identically on HEAD, and name none of the six fields:

- Carrot toxic_to_pets. Its quote "#non-toxic for cats #non-toxic for dogs #non-toxic for horses" is not in the
  page's tag order.
- Cowpea scientific_name_accepted. "Scientific Name: Vigna unguiculata" glues a label to its value.

## Tests

- `tests/test_tranche_invariants.py` passes on its own: 3,880 passed.
- The combined run with `test_claim_ingest.py` gave 3,886 passed and 1 failed. The one failure is the expected count
  assert, `assert 6090 == 6010`, which is exactly this landing's +80.
- `tests/test_claim_ingest.py` was not edited.

## The quote cache during this landing

- At the start (13:58-14:03), 20 of the chunk's 25 cited URLs were cached. The four b86 bulbs' five pages never were.
- Between about 14:08 and 14:12 the cache was wiped twice. The coordinator traced it to two research agents in
  another workflow running `rm -f scripts/catalog/.quote_cache/*.json`. The first pass was reviewed and repaired from
  qc.py reads made before the wipe, and applied while the cache was empty.
- The coordinator then re-seeded the cache from main and re-fetched every page round 4 cites. Commit f6d0044 stops
  verify_quotes from caching a failed fetch.
- Every verify_quotes figure above, and the whole bulb review, comes from the restored cache.
- This session never fetched live, and never deleted or wrote a cache entry. Every qc.py call went through a guard
  that ran it only on a URL already cached with status ok.

## Left for you

- Commit when ready. commit_backfill.py takes the four batch files plus the two result files and this summary.
- Claim delta per file against HEAD: b86 +27, b87 +19, b88 +7, b9 +27, total +80. The Creeping Fig correction's -1
  is inside b87's +19, and commit_backfill measures per file against HEAD, so its count bump will come out right.
