# Candidate lists: harvest by part, not edible versus not

A proposal for 1.1.4, written 2026-11-01 from the ship branch at `65ecf93`. Allison said on 2026-11-01 that edibles versus non-edibles is an unclear line for the candidate lists and that a different categorization would be good. This is one recommended scheme. No code is written for it until she picks.

## Where the line is drawn today

A growing area can ask for "Something to eat". The fit rule (`garden-gnome/app/services/fit.py`, `_goal_findings`) answers from one boolean, `is_edible`, and one sentence, `edibility_note`. A species recorded as eaten with no note fits, "Grown to eat". A species recorded as eaten with a note sits as unknown, with the note. A species recorded as not eaten is a misfit, "Not grown to eat, and you asked for edibles". A species with no record is unknown.

On the catalog as seeded today, 997 species, that comes out like this. 45 species are never put forward at all: 40 because a source rates them a high-severity poison for people or calls them fatal, 5 because a source records them as an invasive species. With "Something to eat" ticked, the other 952 divide into 183 that fit, 105 recorded as eaten but held as unknown by a note, 155 misfits, and 509 with no record either way.

The line is unclear because the note, not the eating, decides which side a plant lands on:

- Every food crop the app keeps by name, tomato, potato, eggplant, rhubarb, tomatillo, peanut and butter beans, lands in the unknown bucket. A table names their eaten part and their poisonous parts (`toxicity.py`, `KNOWN_NUANCE`), so each one always has a note, and a note means unknown. The plants a vegetable bed is for are the ones the "Something to eat" list cannot confirm.
- Chives, oregano, catnip and lemongrass are unknown because a source records them as a problem for pets. Basil, dill, sage and thyme fit. Nothing about eating separates the two groups. The code's own comment on the note says a pet hazard "is a reason to keep scraps from the dog, not to doubt the orange", and then the fit rule doubts it anyway.
- Mint, parsley and lavender are unknown because a source records a low-severity hazard to people, usually a large-amount or skin-contact caution. They sit in the same bucket as monstera, whose unripe fruit and other parts are poisonous.
- Taro is eaten only after cooking, so it is unknown. NC State rates it medium, the same as tomato, and it is a staple crop where it is grown.
- "Not grown to eat" is not an ornamental category. Of the 190 records that say a plant is not eaten, 183 say it because the source calls the plant poisonous. The hazard sentence on the same row already says that. The misfit repeats the hazard in the voice of a preference.
- The goal does less than its chip suggests. An unknown never disqualifies, so with the goal ticked the list still carries every species that fits the space but has no eating record, under the caveat "Nothing here is filtered by what you asked for". The goal removes the 155 poisonous-by-record species and ranks the 183 plain fits first, and that is all.

## What the cited records can carry

The records do not hold a plant type, a life cycle or a habit. Nothing cited says "ornamental", "vegetable", "herb" or "annual", so a scheme built on those words would be the app's own opinion on every row. The fields with coverage are the ones the fit axes already use: grown indoors (938 of 999 records), outdoor sun (942), mature size (941), soil base (796), pollinators (654), watering regime (339).

What the records do say about eating is specific. 293 records say the plant is eaten. 266 of those quote the part: fruit for about 124, leaves 111, flowers 89, seeds 71, roots and tubers 37, stems 32, and 127 name more than one part. The same passages carry the conditions: cooked or otherwise prepared for about 133, other parts poisonous for 130, ripe only for 20, small amounts for 10. The crop table names the eaten part for its seven crops in its own words. That is the one categorization of eating the sources support at scale, and it is already in the quotes.

## The recommended scheme

Eating stops being a verdict and becomes a cited description. The question the list answers changes from "is this edible" to "what do you harvest from it, and how".

Each species gets a harm-capable field, `eaten_parts`, holding the parts a source names as eaten, from a fixed vocabulary: leaves, fruit, seeds, roots, flowers, stems. It is minted from the edibility citations the records already hold, so for 266 species the quote is there and no page is fetched; the 27 whose passage names no part stay null. Like `is_edible` it never borrows from the genus and never resolves through disagreement (ADR 0008). The conditions on eating stay what they are, the note built from the same passages and the crop table.

With "Something to eat" ticked, the candidate list becomes the species whose sources name an eaten part, grouped by that part, and nothing else. A row reads the part and the condition together, in one line that is never dropped for space, the way the hazard line already works:

- Leaves and herbs: "Leaves are eaten. Recorded as poisonous to pets, so keep scraps from them." (chives)
- Fruit: "Only the ripe fruit is eaten; the unripe fruit and the rest of the plant are poisonous. Check the source before eating any of it." (monstera)
- Roots and tubers: "Corms are eaten, only after cooking. Check the source for how they are prepared." (taro)
- Fruit: "The ripe fruit is eaten; the foliage is not." (tomato, from the table)

A species named for more than one part appears in each group its source names. The hazard sentence stays on every row, unchanged. A species with no eaten part on record is not on the list, and a count under the list says so: "N species fit this spot, but no source records any part of them as eaten." That replaces "Nothing here is filtered by what you asked for", which is true today and should not be.

Nothing loosens. A goal still narrows. The people's-severity rule and the crop exemption are untouched: mayapple's ripe fruit is eaten and mayapple is still never put forward; the seven table crops are still in. A species whose source calls it poisonous and names no eaten part is simply off the eat list, with its hazard line wherever it does appear. The "Not grown to eat" misfit goes, because the hazard sentence already carries that fact and a preference is not the place to repeat it.

Without the goal ticked, the list is as it is today, and each row that has an eaten part on record shows the same part-and-condition line in place of the bare "grown to eat".

## The cases that make the current line unclear, under this scheme

Taro: Roots and tubers, "eaten only after cooking", hazard line as today. It is a candidate for a bed that asked for something to eat, which is what the record supports and what ADR 0009 already says it should be.

Eaten in one part, hazardous in another: the row names both, as the source does. Tomato, potato and eggplant come from the table and lead with the eaten part. Monstera and the like come from the passage and say which part and what the rest does. Parsley reads "Leaves are eaten" with its low-severity caution on the same row, which is what NC State publishes, and stops sharing a bucket with monstera.

Herbs flagged for pets: on the list, in Leaves and herbs, with the pet line. The flag is about the dog, and the row says so.

The invasive-list species: never put forward, whatever part is eaten, exactly as today. Beefsteak plant, Perilla frutescens, is the one that shows why this is a list rule and not a category: its leaves are widely eaten and NC State tags it an invasive species, so it is off every list and stays off. Two things the records show are worth a decision alongside this proposal, because the rule reads only the safety passages (toxicity, pets and edibility) when it looks for the words "invasive species" and "noxious weed". The records cite "invasive species" for 13 species and the rule catches 5: Japanese and Chinese wisteria, English ivy, leatherleaf mahonia and beefsteak plant. It misses heavenly bamboo, Japanese privet, butterfly bush, maiden grass, bush honeysuckle, bittersweet nightshade, Indian shot and small-leaf spiderwort, whose citations say it in a passage on another field. The records cite "noxious weed" for 5 species and the rule catches none, for the same reason, so Bradford pear, water lettuce and woodland forget-me-not can be put forward. The recommendation is to read those two phrases from every passage cited about the species itself, still never from a genus page. That keeps 8 more species off every list and is a separate yes or no.

## How each existing list and its copy maps

- The goal chip (`mobile/src/growingAreas/realEstate.ts`, `GOALS`): keep "🥕 Something to eat" and its token `edible`, so older phones keep working. The hint becomes "Only species whose sources name a part that is eaten, grouped by the part, each with its conditions."
- The fit finding for the goal (`fit.py`, `_goal_findings`): fits become the part line with the citing authority; unknown becomes "No source names a part of this plant that is eaten."; the misfit is removed. The backward view on a plant already in the bed says the same unknown as information, not as something to address.
- The candidate list with the goal ticked (`GrowingAreaDetailScreen.tsx`, the "Good candidates here" list; `/growing-areas/{id}/candidates`): only species with an eaten part, grouped as Leaves and herbs, Fruit, Roots and tubers, Seeds and nuts, Flowers, Stems and shoots, alphabetical within a group as today. The part line sits under the name with the hazard line.
- The caveats (`realEstate.ts`, `uncheckedNotes`): the "not filtered" caveat for this goal becomes the count of species left off for want of a record.
- The finding label (`fitFindings.ts`): "Something to eat" stays as the goal's name; the confirmed line under a candidate's name reads the part line.
- The Care facts row and the advisor's fact line (`mobile/src/care/facts.ts`, `plainlyEdible`; `app/services/care_facts.py`): "grown to eat" becomes the same part line, from the same field, so the species page and the list never disagree.
- The listing, the product-truth sheet and the site: "A plant is shown as edible only with the conditions its source gives" stays true and stays. The three goals stay three. What's New for 1.1.4 says the eat list is grouped by the part that is eaten.
- `never_a_candidate` and the crop pin test: unchanged, unless the invasive-and-noxious read is widened, which gets its own test naming the 13 and the 5.

## What the honesty rules require of the new words

Every part line says what a source says and names it where the row rests on one, the way the fit sentences already credit "NC State Extension records it for part shade". The eaten part is harm-capable, so it is species-scoped only: no row can ever read "(from the genus, not this species)" on eating, because the resolver will not let a genus page fill it (ADR 0007, ADR 0008). Where there is no record, the row says there is no record, never that the plant is safe or edible.

The condition travels on the same line as the part, every time, and is never cut for space, because the part without its condition is the sentence the catalog exists to avoid: "fruit" without "ripe" is a different claim. The words come from the passage or the table, as the toxicity sentence does; where the app's own table supplies a word no passage holds, it is labelled "PlantAdvocate's own summary", as that sentence already does.

No row says "edible" as a verdict, "safe to eat", "harmless", or any grade. The curated-note regexes (`tests/test_curated_notes.py`: SAFETY_CLAIM, VERDICT, EATING) should run over the generated part lines in a test, since they are user-facing copy about eating. The hazard sentence and the line "These notes repeat what the sources publish. They are not medical or veterinary advice." stay under every row that carries a hazard. The leak scan and the caretaker voice apply as to any copy.

## What it takes, once she picks

Data first: a claims pass that mints `eaten_parts` from the existing edibility citations, audited the way every harm-capable field is, with the 27 partless passages left null and the crop table's parts carried as the table's own claims. The resolver adds the field to `HARM_CAPABLE`, `RESOLVER_VERSION` moves, and the catalog fingerprint changes, so this rides a normal 1.1.4 catalog sync and deploy. Then the fit rule, the router's grouping, the five mobile copy points above, and the tests. No research fetches are needed for the 266.

## What this does not change

The surfaces, the sun, soil, size and upkeep axes, the low-upkeep and pollinator goals, the people's-severity rule, the crop exemption and its pin test, the hazard sentence, the toxicity tables, and 1.1.3 as it ships. The ship branch is not touched by this proposal.
