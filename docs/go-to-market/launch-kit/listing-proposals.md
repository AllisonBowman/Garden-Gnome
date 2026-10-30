# App Store listing proposals for 1.1.3

Written 2026-10-24 against the ship tip `3f6d7da`. These are proposals only. `docs/app-store/listing.md` is unchanged, and it stays the file you paste from in the handoff's step 4 until you decide otherwise. The first part is promotional text for three seasons. The second is the changes [aso.md](../research/aso.md) and [strategy.md](../strategy.md) recommend to the name, subtitle, keywords and the first lines of the description, each shown against what listing.md holds now.

Every count is exact: Python's `len()` on the text between the fences, which is all plain ASCII with straight quotes, so characters and bytes agree. Every claim was checked against [product-truth.md](../product-truth.md) and listing.md, and where a line rests on something else the paragraph under it says what.

## Promotional text

Apple says promotional text "appears at the top of the description and is up to 170 characters long", that it can be updated "at any time without having to submit a new version", and that it "doesn't affect your app's search ranking so it should not be used to display keywords" ([Apple, product page](https://developer.apple.com/app-store/product-page/), read 2026-10-24). So it is the one field that can follow the season, and none of these lines is written for search.

Each line below is true of 1.1.3 as it ships. None mentions frost, hardiness zones or planting dates, because the app answers none of them. None calls a plant safe, says "AI", or says every fact is cited. None names a holiday plant, a lily, a daylily or an aroid, because the strategy keeps those off the default page until the care-notes fix and the hazard-sentence work are done. The pets custom product page has its own lines in strategy.md's calendar, with their gates, and they aren't repeated here.

In each season the first line is the one strategy.md's calendar uses, except where the note under it says it was reworded. The others are alternatives with the same footing.

### At launch, from L to late November

```text
Describe each place you grow, then see what suits it, what doesn't, and why. More than 990 species, with care facts cited to the sources that published them.
```
Characters: 157 of 170.

This is listing.md's text today, and the strategy keeps it for launch. "More than 990 species" is the only species figure that may be quoted, and "care facts cited to the sources that published them" is the truth sheet's safe wording.

```text
Free, with no ads and no in-app purchases. Describe each place you grow, from a windowsill to a raised bed, and see what suits it, what doesn't, and why.
```
Characters: 153 of 170.

This leads with money, the subject of 29% to 59% of the plant-care leaders' 1 and 2 star reviews ([competitors.md](../research/competitors.md)). The first sentence is listing.md's own, and the surfaces are the app's (`mobile/src/growingAreas/realEstate.ts`). It gives up the species count and the sources line, and it partly repeats what the page already shows: a Get button with no price and no In-App Purchases label. Guideline 2.3.7 asks that no metadata be packed with "pricing information", and it gives "app names, subtitles, screenshots, and previews" only as examples of metadata that "should not include prices", so promotional text isn't exempt. Apple suggests promotional text for news "such as limited-time sales" ([Apple, product page](https://developer.apple.com/app-store/product-page/)), which is news, not a standing price. So don't submit 1.1.3 with this line; paste listing.md's line in step 4. If you want it later, switch to it after approval, since promotional text changes without a new version, knowing that the guideline still applies to it and App Review decides. The Get button and the description's FREE, WITH NO ADS paragraph already say the app is free.

```text
Each growing area lists what needs addressing among its plants, with the reason and the source. Where there is no record, PlantAdvocate says so.
```
Characters: 144 of 170.

Both sentences are listing.md's (the SEE WHAT SUITS IT paragraph and the opening paragraph). It matches screenshot 01, which the strategy puts first, and it says the app's stance on unknowns without a number. It has room to spare and no figure to go stale.

### The winter indoor season, late November to the end of February

```text
Feeding reminders rest from November to February. Describe each windowsill, see what suits it and what doesn't, and read the pet and people hazards that sources record.
```
Characters: 168 of 170.

The strategy's line for late November to the end of January, drafted in aso.md, reworded here. That version ended "read pet and people hazards, with sources named", which reads as if every plant has hazards and as if each hazard sentence names its source, and the pet verdict's source isn't yet named inside the hazard sentence (strategy, "The hazard sentences"). This one claims only the hazards that sources record, as listing.md's HAZARDS paragraph does ("If a source records a plant as harmful to people or pets, its page says so"). Since 2026-10-30, strategy.md's calendar and aso.md carry this wording too. The feeding rest comes from the reminder plan (`mobile/src/notifications/plan.ts`, feeding in months 3 to 10).

```text
Checks, not chores: when a plant comes due, feel the soil, then tap Watered or Still damp. Either keeps your streak. Feeding reminders rest from November to February.
```
Characters: 166 of 170.

Every clause is listing.md's CHECKS, NOT CHORES paragraph. It speaks to the indoor keepers the strategy puts first, the people who come back and who will one day be asked for a rating. It doesn't say every plant gets reminders, which only the 129 species with a check schedule do.

```text
Growing indoors this winter? Set up a windowsill or shelf as a growing area, then narrow the Species Almanac to what fits it. Each cited fact names the source behind it.
```
Characters: 169 of 170.

Windowsill and "shelf or floor" are two of the app's surfaces, "narrow it to what fits a growing area" is listing.md's Almanac line, and "Each cited fact names the source behind it." is the caption of the cited-care-facts screenshot (`docs/app-store/screenshots.md`, "5. Cited care facts"). It says "each cited fact", not "each species page", because production also keeps about 1,900 older uncited rows, listed in the catalog (handoff, "These can wait"); their pages show no Sources card (`SpeciesDetailScreen.tsx` hides it when there are no sources) and read "No care facts cited for this species yet". It matches screenshot 07 (the Almanac narrowed to "Fits Kitchen windowsill"). At 169 it leaves no room for an edit.

```text
February is repot-check month. Look at a plant's roots, then tap Repotted, Top-dressed or All fine. Each growing area shows what suits it and what doesn't, and why.
```
Characters: 164 of 170.

The strategy's line for February, drafted in aso.md. The repot check falls in February with those three endings (`plan.ts`, `REPOT_INSPECTION_MONTH = 2`; `mobile/src/care/CareTodos.tsx`). Like every reminder, it comes only for plants whose species has a check schedule, and the line doesn't claim more.

### Spring planting, 1 March to 31 May

```text
Planting this spring? Describe the bed once, then check each new plant against it before it goes in: sun, soil, space and headroom, with the reason and the source.
```
Characters: 163 of 170.

The strategy's line for March to mid-April. Sun, soil and space with headroom are real axes of the fit engine (`garden-gnome/app/services/fit.py`, `Axis`), and Add plant runs the check before saving (listing.md). "Planting this spring?" asks a question; it gives no date.

```text
A shade fern in full sun is flagged. So is a climber that will outgrow a 7 ft fence. Describe each bed once, and Add plant checks a new plant against it before you save.
```
Characters: 169 of 170.

The two examples are listing.md's, backed by real finding sentences from a scratch sync (listing.md, "Where each claim comes from"). They show the fit engine saying no, which is the app's difference from a list of plant ideas. At 169 it leaves no room for an edit.

```text
Looking for something for a bare bed? Each growing area puts forward candidates: species with nothing on record against the spot and at least 1 thing confirmed for it.
```
Characters: 167 of 170.

The strategy's line for mid-April to May, reworded here. That version, "Each growing area lists what needs addressing among its plants, and puts forward good candidates: nothing on record against the spot, at least 1 thing confirmed for it.", opened with plants already in an area, which a bare bed being filled in May doesn't have, and gave the candidate rule as a fragment. This one starts from the reader's question and gives the rule as listing.md does, in the truth sheet's exact numbers. It describes candidates by their rule and never as safe or guaranteed, which matters because candidates can carry hazard lines. Since 2026-10-30, strategy.md's calendar carries this wording too.

```text
Walk the garden and say what's there: "12 tomatoes along the south fence, a rosemary by the gate." Confirm each plant, then add them all at once.
```
Characters: 145 of 170.

The example sentence and the confirm-then-add flow are listing.md's WALK THE GARDEN paragraph. It suits May, when beds are being filled and people have many plants to add at once. It doesn't mention the photo suggestions, which exist only on iPhone models with Apple Intelligence.

## Name, subtitle and keywords

These three fields, with the primary category, are what App Store search reads, and they change only with a new version. A custom product page can use only keywords from the latest approved version, so the pet words the strategy's pets page needs have to be in 1.1.3's field ([aso.md](../research/aso.md)). 1.1.3 hasn't been submitted, which makes now, before pasting in step 4, the cheapest moment to change them. This is the strategy's "step zero".

Apple's rules that bear on every option: names are limited to 30 characters, subtitles to 30 and keywords to 100 in total, with commas and no spaces between terms. Leave out plurals of words already included, category names, the word "app", and duplicates ([Apple, product page](https://developer.apple.com/app-store/product-page/)). Guideline 2.3.7 says not to pack metadata with trademarked terms, popular app names, pricing information or irrelevant phrases. It adds that names and subtitles should not include prices, and that a subtitle must not "make unverifiable product claims" ([App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/), last updated October 16, 2026, read 2026-10-24). So "Free" stays out of the name and subtitle, and the cited organizations' names stay out of the keyword field.

### Name

| | Text | Characters |
|---|---|---|
| Now, in listing.md | `PlantAdvocate: Garden Care` | 26 of 30 |
| aso.md's alternative | `PlantAdvocate: Plant & Garden` | 29 of 30 |
| Fallback if App Store Connect refuses the name | `PlantAdvocate` | 13 of 30 |

Keep `PlantAdvocate: Garden Care`, as aso.md and the strategy both recommend. It follows the "Brand: descriptor" shape 63 of the 94 comparable apps use, and it puts "garden" and "care" in the strongest field. No released app on the US store carries the name, though at least five others have "Garden Care" in theirs; what makes it distinct is the first word ([competitors.md](../research/competitors.md)). Only App Store Connect can say whether it's free to use.

`PlantAdvocate: Plant & Garden` trades "care" for "plant". aso.md says that is worth it only if Apple doesn't already read "plant" out of the brand, which Apple doesn't document, and the keyword field can carry "plant" anyway. Not proposed.

`PlantAdvocate` alone is the fallback listing.md already names, and it is the name under the home-screen icon. It gives up two indexed words and nothing else, so the keyword field then has to carry "garden" and "care" itself (below).

### Subtitle

| | Text | Characters |
|---|---|---|
| Now, in listing.md | `What suits each spot you grow` | 29 of 30 |
| Proposed by aso.md and the strategy | `Plants that suit each spot` | 26 of 30 |
| Mine, an option that promises less (below) | `Plants checked for each spot` | 28 of 30 |
| aso.md's bolder version, held back | `Houseplants, beds, pet hazards` | 30 of 30 |

```text
Plants that suit each spot
```
Characters: 26 of 30.

The proposed subtitle keeps the product's own idea, the "suits" and the "spot", and puts "Plants" into an indexed, visible field. Apple treats a plural as a duplicate, so the standalone keyword "plant" can leave the keyword field, freeing six characters. The cost is the word "grow" and some of the current line's character: "What suits each spot you grow" reads as a sentence, which few competitors' subtitles do. Under 2.3.7, aso.md reads it as a description of what the fit engine does, not an unverifiable claim, since the app flags what doesn't suit a spot as well. App Review decides.

It has a cost beyond search, and it should be weighed. The current subtitle says the app judges a spot. This one reads as a promise of plants that suit it, and what the app puts forward are good candidates, which need only 1 confirmed thing and can carry hazard lines. Indoors the sun check always comes back unknown (`garden-gnome/app/services/fit.py`, `_sun`). With "cat", "dog" and "poison" in the keyword field, the subtitle will sit in results for pet searches, where "plants that suit" can be read as "plants that are safe", the misreading strategy.md avoided by moving screenshot 02 out of the first three. The truth sheet's row on "the perfect plant for any spot" is the rule it comes close to. If that weighs more than the search gain, two options keep the claim where the app is:

```text
Plants checked for each spot
```
Characters: 28 of 30.

It keeps "Plants" in an indexed field, so field A still pairs with it, and says what the app does, which is check, without promising a match. Or keep `What suits each spot you grow` and paste field C.

`Houseplants, beds, pet hazards` aims straight at the thin pet searches and pushes "houseplant" and "pets" out of the keyword field as duplicates. aso.md holds it for a later version, and the strategy's positioning argues against it for 1.1.3: hazards are a hook, not the headline, and nothing that leads with pets should go up before the 33 care notes are fixed. A subtitle can't be A/B tested, so the only way to compare would be before and after in App Analytics. Not proposed for 1.1.3.

### Keywords

The field depends on the name and subtitle beside it, because a word already in either is a duplicate and a word in neither has to be in the field. The table pairs each field with the name and subtitle it was built for. The first row is listing.md today. The second is the recommendation. The rest are fallbacks.

| Name | Subtitle | Field | Characters | From |
|---|---|---|---|---|
| `PlantAdvocate: Garden Care` | `What suits each spot you grow` | Now | 100 of 100 | listing.md |
| `PlantAdvocate: Garden Care` | `Plants that suit each spot` or `Plants checked for each spot` | A | 97 of 100 | aso.md and the strategy, recommended |
| `PlantAdvocate` | `Plants that suit each spot` | B | 99 of 100 | The strategy's fallback |
| `PlantAdvocate: Garden Care` | `What suits each spot you grow` | C | 93 of 100 | Mine, if you keep the current subtitle |
| `PlantAdvocate` | `What suits each spot you grow` | D | 98 of 100 | Mine, if the name is refused and the subtitle stays |

Now, in listing.md:

```text
plant,houseplant,watering,reminder,raised bed,herb,vegetable,perennial,shrub,toxic,pets,weather,yard
```
Characters: 100 of 100.

A, recommended, with `Plants that suit each spot`:

```text
houseplant,watering,reminder,raised bed,herb,vegetable,gardening,toxic,pets,cat,dog,poison,indoor
```
Characters: 97 of 100.

It drops "plant" (now in the subtitle), "perennial", "shrub", "weather" and "yard", and adds "gardening", "cat", "dog", "poison" and "indoor". The aim is the two thin searches aso.md measured: the median rating count in the first ten results is 6.5 for "toxic plants pets" and 182 for "plant watering reminder", against about 80,600 for "plant care". "Cat", "dog" and "poison" are how people phrase the pet question, "indoor" matches the app's indoors-or-outdoors setting, and "gardening" is the word people type for the whole topic.

The costs are aso.md's and the strategy's. "Weather" and "yard" may carry traffic nobody can see from outside. "Gardening" is wasted if Apple stems it to "garden", which is already in the name. The largest cost is that "cat" and "dog" may bring people who want to point a camera at a plant and get a verdict, which the app doesn't give. The pet words stay honest only if the 33 "Pet-safe" care notes are corrected in production before release; on four of those pages, Parsley, Catnip, Nasturtium and Gourds, the hazard sentence says the opposite of the note (strategy, "The 'Pet-safe' care notes"). Paste this field, or B, C or D, which carry the same words, only if that fix will be live before you press Release, and hold the manual release until a page such as Catnip's or Parsley's no longer shows a "Pet-safe" note. If that can't be promised at step 4, paste listing.md's current field instead. "Identify" stays out, as listing.md decides, and so does "planner", because the app has no planting calendar or bed layout, and Apple warns that "improper use of keywords is a common reason for App Store rejections".

B, if the name is refused, with `PlantAdvocate` and `Plants that suit each spot`:

```text
houseplant,watering,reminder,raised bed,herb,vegetable,garden,care,toxic,pets,cat,dog,poison,indoor
```
Characters: 99 of 100.

The name no longer supplies "garden" and "care", so the field carries them, and "gardening" goes, since "garden" covers it if Apple stems.

C, if you keep `What suits each spot you grow`:

```text
plant,houseplant,watering,reminder,raised bed,herb,vegetable,toxic,pets,cat,dog,poison,indoor
```
Characters: 93 of 100.

This is my derivation, not aso.md's. The current subtitle has no "plant", so "plant" has to stay in the field. To make room, it keeps A's pet and indoor words and drops "gardening", the addition whose value is least certain, because Apple may stem it to "garden" in the name. It leaves 7 characters unused. It keeps the subtitle's character and still reaches the pet and watering searches, but it puts no searchable word in the subtitle.

D, if the name is refused and you keep the current subtitle:

```text
plant,houseplant,watering,reminder,raised bed,herb,vegetable,garden,care,toxic,pets,cat,dog,poison
```
Characters: 98 of 100.

Also mine. It has to carry "plant", "garden" and "care" itself, so "indoor" goes.

One pairing to avoid: field A with the current subtitle. That would leave "plant" in no field but the brand, and whether Apple splits "PlantAdvocate" into two words is undocumented. Whichever subtitle you paste in step 4, paste the field from its row.

## The first lines of the description

Apple says "The first sentence of your description is the most important — this is what users can read without having to tap to read more", and that the description changes only with a new version ([Apple, product page](https://developer.apple.com/app-store/product-page/)). The promotional text sits above it. So what a person reads without tapping is the promotional line and this first sentence:

```text
PlantAdvocate helps you look after the places you grow, from a windowsill to a back bed.
```
Characters: 88.

Keep it. That is aso.md's advice ("Description: leave it") and the strategy's. The first sentence says plainly what the app is for, and the rest of the opening paragraph already names its sources and says that a missing record is never treated as safe, and the description ends with the independence line. Neither file proposes a new first sentence, and I don't either.

Keep the rest of the description too, with one small change. In WALK THE GARDEN and ASK THE GNOME, change "On iPhones with Apple Intelligence" to "On iPhone models with Apple Intelligence", because Apple's trademark guidelines say its marks should not be plural, and launch-playbook.md names this listing and gives that fix ([launch-playbook.md](../research/launch-playbook.md), "Apple's names in marketing copy"). That makes the description 3,804 of 4,000, up from 3,792.

aso.md makes one point that touches the opening, and it applies only if the pet keywords go in: people who search "cat" or "dog" should meet "not medical or veterinary advice" before they install. Today that sentence sits in the HAZARDS, STATED PLAINLY paragraph, the fifth block. If you want it earlier, append it to the opening paragraph, which would then read:

```text
PlantAdvocate helps you look after the places you grow, from a windowsill to a back bed. Its advice is never made up on the spot. Care facts come from the organizations that publish them, such as NC State Extension, the Royal Horticultural Society and Missouri Botanical Garden, and each species page names its sources. Where there is no record, PlantAdvocate says so. A missing record is never treated as safe. Hazard notes are not medical or veterinary advice.
```
Characters: 462 for the paragraph, up from 411. With the iPhone change, the description would be 3,855 of 4,000; without it, 3,843.

The added sentence is the HAZARDS paragraph's last one, with "Hazard notes" in place of "They" so it stands on its own. It leaves out the sentence before it, "These notes repeat what the sources publish", on purpose. Some hazard clauses come from tables in the code, not from a cited page: the lily and daylily kidney-failure wording is sourced as "widely documented feline lily toxicosis" (`SPECIES_SPECIFIC_RISK` in `garden-gnome/app/services/toxicity.py`), and the arum family's calcium oxalate wording as "characteristic of Araceae" (`AROID_TOXICITY`). strategy.md ("The hazard sentences") plans to cite or label them by the end of February. Until then, the HAZARDS paragraph's own "These notes repeat what the sources publish" has the same gap. Replacing its last two sentences with "Hazard notes are not medical or veterinary advice." closes it and takes 37 characters off the count: 3,767 with the iPhone change, or 3,818 with the opening addition as well. Whether to change the HAZARDS paragraph for 1.1.3 is your call.

The tradeoff of moving the not-advice sentence earlier is modest either way. The addition sits at the end of the opening paragraph, well past the first sentence, so it reaches only people who tap "more", who would otherwise meet the same words three blocks later. It repeats a sentence the description already has, and it makes the opening more cautionary. The searcher who never taps "more" is better served by screenshot 06 among the first three, which the strategy's upload order provides, and by the pets custom product page's own promotional text. My view: worth doing only if field A, B, C or D goes in with the pet words, and harmless to skip.

## What this doesn't settle

Only App Store Connect can say whether the name is available. No keyword popularity data was available from outside: Apple shows its 1-to-5 scores only inside Apple Ads Advanced, so "thin" means thin competition, not proven volume. Apple doesn't publish how it weights the name, subtitle and keywords, whether it combines words across fields, or how it stems ([aso.md](../research/aso.md)). App Review has the last word on the subtitle. If the strategy's spring Apple Ads test shows popular search terms these fields miss, change the field in the next version; that is the one thing the paid test is for.
