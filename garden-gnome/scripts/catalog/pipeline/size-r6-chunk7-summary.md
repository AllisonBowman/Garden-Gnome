# Size backfill, round 6 chunk 7 -- landing summary

Landed 2026-10-03 from `size-r6-chunk7-result.json`: 40 species over b9, b13, b28, b65, b79, b85, b86 and b89, with 0
unverified, 0 no_research, 2 fields already nulled on audit and 0 review lines. It followed
`BACKFILL_LANDING_BRIEF.md` (including the Round 5 additions) and the standing rules in the landing instructions. It
was landed after chunk 3, as a separate merge. Not committed.

Four species carried a value, and all four land. American Holly's is_edible false was re-cited at landing. The other
36 species wrote nothing in the workflow itself.

The untouched result file and the batch files as they were at the start are kept in the session scratchpad
(`r6c37/orig/`). The result-file edit was made by `r6c37/fix_results.py`, which asserts each edited entry's starting
state.

## Result

- b9-veg-round2: 96 -> 101 claims (+5)
- b13-annual-flowers1: 79 -> 80 (+1)
- b28-holly-and-nuts: 83 -> 84 (+1)

That is +7 against HEAD. HEAD was 588d8ca when this landing started and is now d0bac40. The commits in between are
the app team's and touch neither `app/data/verified/` nor the two tests. With chunk 3 already applied, the ingest test
prints `assert 7003 == 6989`: chunk 3's +7 plus this chunk's +7. b65, b79, b85, b86 and b89 are unchanged.

## Merge plan totals

The plan printed "problems: none" and was applied once. It wrote 4 species, 7 fields and 7 citations, and named no
batch file outside this chunk's list.

- Cabbage (b9): mature_height_in 3.9-19.7 and mature_spread_in 3.9-19.7. The source is RHS's Brassica oleracea
  Capitata Group page, which gives Max Height and Max Spread as 0.1-0.5 metres. There are 2 citations, to a page new
  to the record.
- Cauliflower (b9): attracts_pollinators true, from NC State's "Bees will visit the flowers". There is 1 citation, to
  a page new to the record.
- Coleus (b13): attracts_pollinators true. There are 3 citations: two to UF/IFAS FP136 and one to Clemson HGIC, both
  pages already on the record.
- American Holly (b28): is_edible false, from NC State's "Poisonous to Humans" after the re-cite. There is 1
  citation.

The other 36 species have nothing to write.

## Review lines

There were none. Two fields were nulled on audit (the `applied` lines). They stay null, and neither species writes
anything.

- Black Walnut, attracts_pollinators. NC State's "Attracts: Moths" entry is about larval hosts, and the same page says
  the flowers "are wind pollinated".
- Pecan, attracts_pollinators. NC State's bare "Pollinators" sits beside its "#wind pollinated" tag, and UF/IFAS
  HS229 says "Pecan trees are wind pollinated."

## Fields nulled at landing

None. One citation was re-cited instead.

- American Holly, is_edible false. The citation quoted only NC State's Poison Symptoms list, "Nausea, vomiting (not
  in horses), diarrhea, depression.", which does not itself say the plant is poisonous to eat.
  - It now quotes the page's Problems value, "Poisonous to Humans". That is a single rendered element. The Poisonous
    to Humans block under it gives Poison Part "Fruits" and severity Low, but "Poison Part:" and "Fruits" are
    separate elements, so they cannot be quoted as one run.
  - The claim now reads "is_edible false (NC State Problems field lists American holly as Poisonous to Humans; its
    Poisonous to Humans block gives Poison Part: Fruits, severity Low)".
  - The same quote already supports false for Annual Geranium, Panicle Hydrangea, Climbing Hydrangea, Dwarf Umbrella
    Tree and Fetterbush.
  - RHS's Potentially harmful field reads "Fruit are ornamental - not to be eaten." That sentence is noted in the
    record's unknowns (an earlier landing's line and this one's), not added as a second citation, because the loader
    pairs a field to its first supporting citation only.

## Points checked with care

- Cabbage's size. RHS publishes 0.1-0.5 m in both its summary block and its Size panel. Nowhere else on the page is
  there a larger figure: there are no cm, in or ft figures and no "Ultimate height", only Time to Maturity "1 year".
  The size is kept as published, and no unknowns line was needed for a larger figure. The research's own line already
  says the band looks small for large-headed types.
  - The page is the record's own taxon (Capitata Group), on a registered domain. The quotes are the summary block's
    clean runs.
  - The conversion matches the same RHS band already landed on Cauliflower in this file (3.9-19.7).
- Cauliflower's new page is NC State's combined "Brassica oleracea Cauliflower & Broccoli Group" entry. It was
  accepted as Cauliflower's own NC State page, for these reasons:
  - its title lists Cauliflower, and its prose and cultivar list ('Cheddar', 'Graffiti') are cauliflower's;
  - NC State has no Botrytis Group page (it is cached as http-404);
  - b8's Broccoli already rests its attracts_pollinators on this same sentence from this same entry.

  The research unknowns carry the caveat that the sentence is stated for the combined group.
- Coleus. UF/IFAS FP136 is now cached under its edis URL, with the title "FPS136/FP136: Coleus scutellarioides:
  Coleus". Both its quotes are clean runs. The Clemson quote HITs, which meets standing rule 5. "Pollinators" and
  "pollinating insects" are named on the pages.

## Unknowns added at landing

One line, for American Holly. It explains the re-cite and supersedes the record's older lines saying is_edible is or
stays null. It ends "Noted at landing, verified against the cached copy".

## Stale size notes

Run on the whole result file, `strip_stale_size_notes.py` would have removed 5 lines. Only Cabbage's was stale. The
others:

- Coleus, Scaly Blazing-star and Japanese Yew. Each says "not a climber, so the size fields were recorded normally
  rather than left null". That is still true.
- Flowering Quince (b85). It reads "mature_height_in_min/max and mature_spread_in_min/max are not carried on this
  record ... left to the size backfill". That first clause has been stale since an earlier round landed its size
  (72-144 x 72-120 in). The rest of the line, which records NC State's, MoBot's and RHS's figures disagreeing at the
  top end, is still true and useful. This landing wrote nothing to that record, so the line was left in place. It is
  your call.

The script was run, and applied, on a one-entry copy of the payload (`r6c37/strip-chunk7-size-only.json`). The copy
holds only Cabbage, the one species whose size this landing wrote. It removed Cabbage's "mature_height_in and
mature_spread_in left null: none of the four cited pages publish ...". The research's new lines keep its substance:
Clemson and UMD give only planting spacing, and no other registered page gives a size.

## verify_quotes, per touched file (VQ_CACHE_ONLY=1)

- b9-veg-round2: 92 hit, 2 MISS, 0 inconclusive, 18 skipped (HEAD: 89 hit, 2 MISS, 18 skipped)
- b13-annual-flowers1: 107 hit, 1 MISS, 0 inconclusive, 20 skipped (HEAD: 104 hit, 1 MISS, 20 skipped)
- b28-holly-and-nuts: 128 hit, 3 MISS, 0 inconclusive, 22 skipped (HEAD: 127 hit, 3 MISS, 22 skipped)

Hits rose by exactly the 7 new citations (+3, +3, +1). Each file's MISS, SKIP and INCONCLUSIVE lines are identical to
HEAD's, and none names a backfill field, so there is no NEW-FIELD MISS, SKIP or INCONCLUSIVE.

These MISS lines predate this landing:

- b9: Carrot toxic_to_pets (the tags quoted out of page order) and Cowpea scientific_name_accepted (a label glued to
  its value).
- b13: Coleus is_houseplant. "Coleus may be used as a potted plant indoors in a sunny window or outdoors in part sun."
  is not on the cached FP136 page, which now says "it may be a houseplant".
- b28: Peach toxicity_detail (glued labels), Peach cool_rest_note (an HS1492 sentence) and American Elderberry
  name_note (glued labels).

## Tests

- `tests/test_tranche_invariants.py`: 3,880 passed.
- The combined run with `test_claim_ingest.py` gave 3,886 passed and 1 failed. The failure is the expected count
  assert, `assert 7003 == 6989`, which covers both chunks.
- The test was not edited.

## The quote cache

Every qc.py and verify_quotes call ran with `VQ_CACHE_ONLY=1`, against pages already cached with status ok. Nothing
was fetched live, and nothing in the cache was written, moved or deleted.

## Left for you

- Commit with commit_backfill.py. Pass b9, b13 and b28, plus `size-r6-chunk7-result.json` and this summary. The claim
  delta against HEAD is b9 +5, b13 +1, b28 +1, for a total of +7.
- Flowering Quince's half-stale size line (above).
- Coleus's pre-existing is_houseplant MISS. Its FP136 quote is no longer on the page, so it is a candidate for a
  re-cite to "it may be a houseplant".
