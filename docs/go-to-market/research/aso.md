# App Store optimization and Apple launch mechanics

This file reviews PlantAdvocate's App Store listing text (name, subtitle, keywords, promotional text and description in `docs/app-store/listing.md`) against how comparable apps word theirs. It then sets out what Apple's own developer pages say about Featuring Nominations, in-app events, product page optimization, custom product pages, campaign links, the ratings prompt, Apple Ads, the badge and marketing guidelines and the Smart App Banner. It ends with what the seasonal pattern of gardening searches means for a launch in late October 2026. It was checked on 2026-10-23: the Apple pages were fetched that day, the App Store data came from iTunes Search API calls made that day, and the repository was at `3f6d7da`. PlantAdvocate is not live yet. The [iTunes lookup for app id 6792203800](https://itunes.apple.com/lookup?id=6792203800&country=us) returned no results today and [its product page](https://apps.apple.com/us/app/id6792203800) answered 404, so everything below that needs a live app (custom product pages, product page optimization, campaign links, Apple Ads, the badge) is for after release.

## How the comparison was made

I ran the six terms through the public iTunes Search API with `entity=software`, `country=us` and `limit=50`: [plant care](https://itunes.apple.com/search?term=plant%20care&entity=software&country=us&limit=50), [garden planner](https://itunes.apple.com/search?term=garden%20planner&entity=software&country=us&limit=50), [houseplant](https://itunes.apple.com/search?term=houseplant&entity=software&country=us&limit=50), [plant watering reminder](https://itunes.apple.com/search?term=plant%20watering%20reminder&entity=software&country=us&limit=50), [toxic plants pets](https://itunes.apple.com/search?term=toxic%20plants%20pets&entity=software&country=us&limit=50) and [vegetable garden](https://itunes.apple.com/search?term=vegetable%20garden&entity=software&country=us&limit=50). The tables show the first eight results for each. The counts in the next section use the first twenty for each term, which come to 94 distinct apps. The API does not return subtitles, so for the 30 distinct apps with at least one rating among the first eight results of each term I read the product page on apps.apple.com (for example [Planta](https://apps.apple.com/us/app/id1410126781)).

Two cautions. The order is the endpoint's order. [Apple's documentation of the Search API](https://performance-partners.apple.com/search-api) describes its parameters and a limit of about 20 calls a minute, and says nothing about the order matching what a person sees in the App Store app. Read the tables as who shows up for each phrase, not as a guaranteed rank. The order also shifts between calls: a re-run of the garden planner call later the same day put Veggie Garden Planner fourth rather than sixth, and the plant care call returned a different ninth and tenth app. Second, I have no keyword popularity figures. Apple shows them only inside Apple Ads Advanced, on a scale of [1 to 5](https://ads.apple.com/app-store/help-glossary). So "winnable" below means thin competition, not high volume. Average ratings are Apple's all-time US figures from the same calls.

Apps in the tables carry their App Store names. I left out seller names, because many are individuals.

### plant care

From the [plant care call](https://itunes.apple.com/search?term=plant%20care&entity=software&country=us&limit=50):

| # | App | Average rating | Ratings | Primary category |
|---|---|---|---|---|
| 1 | Plant Identifier, Care: Planty | 4.7 | 37,973 | Education |
| 2 | PictureThis - Plant Identifier | 4.8 | 1,120,755 | Education |
| 3 | Planta: Plant & Garden Care | 4.8 | 114,294 | Lifestyle |
| 4 | Plant Parent: Plant Care Guide | 4.7 | 92,518 | Lifestyle |
| 5 | Blossom - Plant Care Guide | 4.6 | 68,770 | Education |
| 6 | PlantIn: Plant Identifier・Care | 4.6 | 230,175 | Education |
| 7 | Greg: Plant Identifier & Care | 4.6 | 20,698 | Education |
| 8 | Plant Identifier, Plant Care | 4.4 | 6,559 | Education |

### garden planner

From the [garden planner call](https://itunes.apple.com/search?term=garden%20planner&entity=software&country=us&limit=50):

| # | App | Average rating | Ratings | Primary category |
|---|---|---|---|---|
| 1 | Planter: Garden Planner | 4.7 | 2,349 | Lifestyle |
| 2 | GrowIt: Garden Planner | 4.7 | 14,175 | Lifestyle |
| 3 | Seedtime: Garden Planner App | 4.7 | 448 | Lifestyle |
| 4 | Seed to Spoon - Garden Planner | 4.8 | 9,290 | Health & Fitness |
| 5 | Garden Planner: Landscape AI | 4.7 | 7 | Reference |
| 6 | Veggie Garden Planner | 4.3 | 3,875 | Lifestyle |
| 7 | iScape: Landscape Design | 4.6 | 28,866 | Lifestyle |
| 8 | AI Garden Design: Landscape AI | 4.6 | 8,174 | Graphics & Design |

### houseplant

From the [houseplant call](https://itunes.apple.com/search?term=houseplant&entity=software&country=us&limit=50):

| # | App | Average rating | Ratings | Primary category |
|---|---|---|---|---|
| 1 | Planta: Plant & Garden Care | 4.8 | 114,294 | Lifestyle |
| 2 | Plant Parent: Plant Care Guide | 4.7 | 92,518 | Lifestyle |
| 3 | Blossom - Plant Care Guide | 4.6 | 68,770 | Education |
| 4 | PictureThis - Plant Identifier | 4.8 | 1,120,755 | Education |
| 5 | Plantminder | 4.6 | 42 | Lifestyle |
| 6 | Greg: Plant Identifier & Care | 4.6 | 20,698 | Education |
| 7 | Blackthumb: Houseplant care | 3.8 | 5 | Lifestyle |
| 8 | Rare Plant Fairy | 4.9 | 256 | Shopping |

### plant watering reminder

From the [plant watering reminder call](https://itunes.apple.com/search?term=plant%20watering%20reminder&entity=software&country=us&limit=50):

| # | App | Average rating | Ratings | Primary category |
|---|---|---|---|---|
| 1 | Planta: Plant & Garden Care | 4.8 | 114,294 | Lifestyle |
| 2 | Plant Watering Reminder | 4.6 | 90 | Productivity |
| 3 | Plant Parent: Plant Care Guide | 4.7 | 92,518 | Lifestyle |
| 4 | Plant Daddy — Water Reminders | 4.8 | 318 | Lifestyle |
| 5 | Plant Watering Reminder: Care For Indoor Plants | 4.2 | 275 | Utilities |
| 6 | PictureThis - Plant Identifier | 4.8 | 1,120,755 | Education |
| 7 | Siram: Plant Watering Reminder | none | 0 | Utilities |
| 8 | Wety – Plant Watering Reminder | 5.0 | 4 | Utilities |

### toxic plants pets

From the [toxic plants pets call](https://itunes.apple.com/search?term=toxic%20plants%20pets&entity=software&country=us&limit=50):

| # | App | Average rating | Ratings | Primary category |
|---|---|---|---|---|
| 1 | Toxic Plant: Pet Poison Guide | 2.0 | 26 | Utilities |
| 2 | Toxic Plants for Cats & Dogs | none | 0 | Reference |
| 3 | Pet Safety: Toxic Plant Check | none | 0 | Lifestyle |
| 4 | Pet Toxic | 5.0 | 7 | Reference |
| 5 | Pet Safe Plant Identifier | 5.0 | 5 | Reference |
| 6 | PlantSnap Pro: Identify Plants ($199.99) | 4.5 | 44,697 | Education |
| 7 | Plant Identifier: ChatPlant AI | 4.5 | 4,743 | Education |
| 8 | PlantLush: Plant ID & Care Pro | 4.0 | 8,168 | Education |

### vegetable garden

From the [vegetable garden call](https://itunes.apple.com/search?term=vegetable%20garden&entity=software&country=us&limit=50):

| # | App | Average rating | Ratings | Primary category |
|---|---|---|---|---|
| 1 | GrowIt: Garden Planner | 4.7 | 14,175 | Lifestyle |
| 2 | Planter: Garden Planner | 4.7 | 2,349 | Lifestyle |
| 3 | Seed to Spoon - Garden Planner | 4.8 | 9,290 | Health & Fitness |
| 4 | Farm Your Yard: Gardening App | 4.6 | 399 | Food & Drink |
| 5 | Seedtime: Garden Planner App | 4.7 | 448 | Lifestyle |
| 6 | Planta: Plant & Garden Care | 4.8 | 114,294 | Lifestyle |
| 7 | Veggie Garden Planner | 4.3 | 3,875 | Lifestyle |
| 8 | GrowPlan - Garden Planner | none | 0 | Lifestyle |

## What the comparison shows

The terms fall into three tiers of competition. "Plant care" and "houseplant" are held by apps with tens of thousands to over a million ratings: the median rating count across the first ten results is about 80,600 for [plant care](https://itunes.apple.com/search?term=plant%20care&entity=software&country=us&limit=50) and 44,734 for [houseplant](https://itunes.apple.com/search?term=houseplant&entity=software&country=us&limit=50). A new app with no ratings will not displace them soon. "Garden planner" and "vegetable garden" are middle-sized, with medians of about 6,000 and 1,400 ratings across the first ten results ([garden planner](https://itunes.apple.com/search?term=garden%20planner&entity=software&country=us&limit=50), [vegetable garden](https://itunes.apple.com/search?term=vegetable%20garden&entity=software&country=us&limit=50)). Those results are planners, with layouts and planting calendars. PlantAdvocate is not one, so chasing the term would mean attracting people who want something it does not do.

The two thin tiers are the useful finding. For ["plant watering reminder"](https://itunes.apple.com/search?term=plant%20watering%20reminder&entity=software&country=us&limit=50) the median across the first ten is 182 ratings and five of the ten have under 100. For ["toxic plants pets"](https://itunes.apple.com/search?term=toxic%20plants%20pets&entity=software&country=us&limit=50) the median is 6.5 and seven of the ten have under 100. The first result there has 26 ratings averaging 2.0. In the watering list, the second result has 90 ratings and sits above an app with 92,518, and its name is the search phrase. So in this endpoint's order, a name that matches the phrase counts for a great deal. That fits [Apple's own description](https://developer.apple.com/app-store/search/) of search results as based on text relevance (title, subtitle, keywords and primary category) as well as user behavior such as downloads and ratings. Apple does not say how the factors are weighted, and I found no public statement of it.

How the comparable apps word things, from the first twenty results of each term (94 distinct apps):

- Names: 63 of 94 use a "Brand: descriptor" or "Brand - descriptor" shape, the shape PlantAdvocate uses. The median name is 26.5 characters and only one exceeds Apple's [30-character limit](https://developer.apple.com/app-store/product-page/) (a 47-character name I cannot explain). "Plant" appears in 56 names, "garden" in 31, "care" in 20, "identif-" in 17 and "planner" in 17.
- Subtitles, from the 30 product pages I read (the four quoted here were re-checked; the other 26 were not re-checked): almost all are keyword lists in 25 to 30 characters, such as "Identify, Diagnose & Reminders", which appears on two different apps ([Plant Parent](https://apps.apple.com/us/app/id1612792132) and [Greg](https://apps.apple.com/us/app/id1512912236)), and [Seedtime's "Gardening & Planting Calendar"](https://apps.apple.com/us/app/id6496536815). A few are imperatives ([Planter's "Plan your vegetable garden!"](https://apps.apple.com/us/app/id1542642210)). PlantAdvocate's "What suits each spot you grow" is one of the few that reads as a sentence.
- Descriptions: the median is 1,958 characters (quartiles 1,240 and 2,867), so PlantAdvocate's 3,795 is long. 29 of 94 use an all-caps heading line as PlantAdvocate does. 6 open with a question. By a rough word search, 41 of 94 mention a subscription, trial, premium or pro tier, and 21 mention AI, while only 9 mention sources, citations, extension services or botanical gardens. At least 16 of the 30 product pages I read show "In-App Purchases" under the name (not re-checked beyond the four pages above, all of which do). Free, no ads, no purchases and named sources are therefore real differences in this set, though I did not read all 94 descriptions in full.
- Categories: Lifestyle is primary for 40 of the 94, Education for 25 (where the identifier apps sit). Planta and Plant Parent are Lifestyle, as is PlantAdvocate.

## Where the current listing stands

The counts below are exact, taken from the blocks in `docs/app-store/listing.md` (each counted with `len()` on the text between the fences; the file's own figures agree).

| Field | Limit | Now | Proposed |
|---|---|---|---|
| Name | 30 | 26 | unchanged (26) |
| Subtitle | 30 | 29 | 26 |
| Keywords | 100 | 100 | 97 |
| Promotional text | 170 | 157 | unchanged for launch (157) |
| Description | 4,000 | 3,795 | unchanged |

Mapped word by word, the current fields already cover five of the six terms. The name supplies "garden" and "care". The keyword field supplies "plant", "houseplant", "watering", "reminder", "vegetable", "toxic" and "pets". That leaves "garden planner" without "planner", which is right: the app has no planting calendar or bed layout, and Apple lists [terms not relevant to the app](https://developer.apple.com/app-store/product-page/) among the common reasons for rejection. The weakness is the subtitle. Apart from "grow" and "spot" it adds no searchable word, while the keyword field is full to the last character. Whether Apple splits the one-word brand "PlantAdvocate" into "plant" and "advocate" is not documented, which is a reason to keep "plant" somewhere indexed.

A note on method: Apple says to leave out words already in the name, subtitle or category, and to leave out plurals of words already included, which it treats as [duplicates](https://developer.apple.com/app-store/search/). It also says the field is 100 characters in total, with terms separated by commas and no spaces. Whether Apple combines words across fields to match a two-word query is the working assumption of most ASO practice, but I found no Apple statement of it.

### Name: keep it

`PlantAdvocate: Garden Care` (26 of 30) follows the pattern 63 of the 94 comparables use and puts two of the most common descriptive words in the strongest field. The alternative is `PlantAdvocate: Plant & Garden` (29), which trades "care" for "plant". That is only worth it if Apple does not already index "plant" from the brand, and the keyword field can carry "plant" anyway. If the name is refused at save, `PlantAdvocate` alone gives up two indexed words and nothing else. I cannot check availability from outside: the iTunes API shows no app called [PlantAdvocate](https://itunes.apple.com/search?term=PlantAdvocate&entity=software&country=us&limit=15), but other apps already carry the descriptor, such as two with "Garden Care" in their names ([garden care search](https://itunes.apple.com/search?term=garden%20care&entity=software&country=us&limit=15)). Names only have to be unique as whole strings, and App Store Connect is the real check.

### Subtitle: change it

Proposed:

```text
Plants that suit each spot
```
Characters: 26 of 30.

It keeps the product's own word ("spot") and the "suits" idea, and puts "Plants" into an indexed, visible field. Because Apple treats "plants" and "plant" as duplicates, the standalone keyword "plant" can go, which frees 6 characters. The cost is the word "grow" and some of the sentence's distinctiveness. Apple's [App Review Guidelines (2.3.7)](https://developer.apple.com/app-store/review/guidelines/) ask that a subtitle not make unverifiable product claims. "Plants that suit each spot" is a description of what the fit engine does, and the app flags what does not suit a spot as well, so I think it is safe, but App Review decides.

A bolder version is `Houseplants, beds, pet hazards` (30 of 30). It gives up the "suits" message to put "houseplants" and "pet" into the visible line, aimed at the thin pets niche above. If it were used, "houseplant" and "pets" would leave the keyword field as plural duplicates. I would hold it for 1.1.4. Apple's [product page guidance](https://developer.apple.com/app-store/product-page/) lets a subtitle change with any new version, and product page optimization tests only icons, screenshots and previews, so a subtitle cannot be A/B tested. The only comparison available is before and after in App Analytics, which a new app may not have the volume to read.

### Keywords: swap five weak words for five relevant ones

Now (100 of 100): `plant,houseplant,watering,reminder,raised bed,herb,vegetable,perennial,shrub,toxic,pets,weather,yard`

Proposed, with the subtitle above:

```text
houseplant,watering,reminder,raised bed,herb,vegetable,gardening,toxic,pets,cat,dog,poison,indoor
```
Characters: 97 of 100.

Dropped: "plant" (covered by "Plants" in the subtitle), "perennial", "shrub", "weather" and "yard". Added: "gardening", "cat", "dog", "poison" and "indoor". The reasoning is that "toxic plants pets" is the thinnest competition measured, that "cat" and "dog" are how people phrase it, that "indoor" matches the app's indoors-or-outdoors setting and a common word in watering-reminder apps, and that "gardening" is the form people type when they mean the whole topic. The costs are real. "Weather" and "yard" may carry traffic I cannot see, though "weather" draws people who want a weather app and the listing already says the app is not one. "Gardening" is wasted if Apple stems it to "garden", which is already in the name. And "cat" and "dog" may attract people who want to point a camera at a plant and get a verdict, which PlantAdvocate offers only on iPhones with Apple Intelligence. The honest description ("not medical or veterinary advice", named sources) belongs in the screenshots and the first lines of the description, so those searchers know before they install.

The bolder subtitle would pair with `plant,watering,reminder,raised,herb,vegetable,gardening,toxic,cat,dog,poison,indoor` (83 of 100, leaving 17 characters spare).

"Identify" stays out, as `listing.md` already decides. 17 of the 94 comparable names contain it, but the leaders have 20,000 to over a million ratings, and photo matching exists only on Apple Intelligence phones. There is also a plumbing reason to settle it now: a custom product page can only use [keywords from the latest approved app version](https://developer.apple.com/help/app-store-connect/create-custom-product-pages/configure-multiple-product-page-versions/), so a word missing from the keyword field cannot later be assigned to a page.

### Promotional text: keep it, then rotate it

The launch text (157 of 170) is accurate and plain. Apple says promotional text sits above the description and [can change at any time without a new version](https://developer.apple.com/app-store/product-page/), and that it [does not affect search ranking](https://developer.apple.com/app-store/search/). That makes it a free, safe place for seasonal lines. Two drafts that use only facts in `listing.md`:

```text
Feeding reminders rest from November to February. Describe each windowsill, see what suits it and what doesn't, and read pet and people hazards, with sources named.
```
Characters: 164 of 170.

```text
February is repot-check month. Look at a plant's roots, then tap Repotted, Top-dressed or All fine. Each growing area shows what suits it and what doesn't, and why.
```
Characters: 164 of 170.

### Description: leave it

By Apple's own list, [search relevance comes from title, subtitle, keywords and primary category](https://developer.apple.com/app-store/search/), and Apple tells developers not to [add unnecessary keywords to the description](https://developer.apple.com/app-store/product-page/). The description is for conversion, and what most people read is the promotional text plus the first lines. The first sentence is already clear. At 3,795 characters it is long next to the median of 1,958, but length costs nothing when the part people read is short. One low-risk point: the opening paragraph names NC State Extension, the Royal Horticultural Society and Missouri Botanical Garden. [Guideline 2.3.7](https://developer.apple.com/app-store/review/guidelines/) warns against packing metadata with trademarked terms to game search. These names appear once, as attribution, and the last line of the description says the organizations have not reviewed or endorsed the app. If App Review asks, that is the answer.

### Screenshots: the first three show in search

Apple says the [first one to three screenshots appear in search results](https://developer.apple.com/app-store/product-page/) when there is no app preview. The planned order in `docs/app-store/screenshots.md` leads with what doesn't suit a spot, good candidates and the check before planting, with hazards at number 6. That order sells the fit engine. If the pets niche matters more, moving the hazards shot up to third costs "The check before planting" (now third) its place in the first three. A custom product page (below) lets both work without choosing.

## Featuring Nominations

Read on [Apple's nomination help page](https://developer.apple.com/help/app-store-connect/manage-featuring-nominations/nominate-your-app-for-featuring/), [the CSV template reference](https://developer.apple.com/help/app-store-connect/reference/nominations/nominations-template) and [Getting featured on the App Store](https://developer.apple.com/app-store/getting-featured/).

Who can submit: the Account Holder, Admin, App Manager or Marketing role. The path is App Store Connect, the app, Featuring in the sidebar, Nominations. There are three nomination types: New Content, App Enhancements and App Launch, which Apple describes as covering the launch or pre-order of a new app. A nomination is saved as a draft until submitted, and it can be edited after submission, except the type and the related apps.

What to include. The name is up to 60 characters. The description is up to 1,000 characters. Apple asks for a detailed description, and for new content or enhancements it should state the purpose and priority and the specifics of the update. The form asks for a publish date or a date range (the date is taken from the device's time zone), the countries and regions (3-letter ISO codes in the CSV), platforms, localizations, and optionally an in-app event. It takes up to 5 supporting URLs, which can include TestFlight public links, and a "helpful details" field of up to 500 characters for accessibility, inclusivity, priority or what is unusual about the app or team. Up to 10 apps from one account can be related to one nomination. A CSV import can submit up to 50 nominations at once, but each is submitted immediately and cannot be a draft.

Lead time, where the sources disagree. The App Store Connect help says to submit as early as possible with a minimum of 3 weeks, and the template page repeats the 3 weeks. The Getting featured page says a minimum of 2 weeks, and up to 3 months in advance for wider consideration. Apple's help pages are the more specific, so plan on 3 weeks as the floor. A nomination filed on Monday 2026-10-26 meets that floor for any release on or after 2026-11-16. For a spring slot such as mid-April, the 3-month figure would mean filing by about mid-January 2027.

What happens next: the template page says Apple will reach out to the email address given if the plan is a fit, and the Getting featured page says Apple may email team members with the Admin, App Manager and Marketing roles to ask for promotional artwork. Whoever holds those roles has to watch that inbox. Apple lists what it considers (user experience, UI design, innovation, uniqueness, accessibility, localization, and the product page including screenshots, previews, descriptions and positive ratings and reviews) and says there is no checklist. I found no published acceptance rate.

Two things Apple's pages do not say. They do not say whether a nomination can be filed before an app's first approval. The form asks for the app's Apple id, and the app record already has one, so it may well work, but I have not seen it stated. And they give no guidance on how a brand-new app with no ratings is weighed against one with them. My inference is that a nomination aimed at spring, once there are some ratings, may read better than one at launch. It costs nothing to file both, as far as I can tell, and the help page shows no limit on the number of nominations.

Drafts for Allison to paste, if they choose. Nothing has been submitted. I did not verify any accessibility support in the app, so none is claimed.

```text
PlantAdvocate 1.1.3: first App Store release
```
Characters: 44 of 60 (nomination name).

```text
PlantAdvocate is a free app for iPhone, with no ads and no in-app purchases, for looking after the places you grow. Version 1.1.3 is its first App Store release. Each growing area, from a windowsill to a raised bed, is described once, and a fit check says what suits that spot, what doesn't and why, naming the source. The Species Almanac covers more than 990 researched species with cited care facts. Where a source records a plant as harmful to people or pets, the app says so plainly. Care checks are gentle: feel the soil, then tap Watered or Still damp. The release date is flexible within the window given.
```
Characters: 612 of 1,000 (nomination description).

```text
Made and maintained by one independent developer. A first launch, with a flexible date. Sign in with Apple or Google only; no ads, no tracking, no in-app purchases. Sources are named on each species page, and anything not yet cited says so. The check schedules for 129 common plants were written by PlantAdvocate and are not cited. Hazard notes repeat what sources publish and are not medical or veterinary advice.
```
Characters: 414 of 500 (helpful details).

## In-app events

Read on [Apple's In-App Events page](https://developer.apple.com/app-store/in-app-events/), the [overview in App Store Connect help](https://developer.apple.com/help/app-store-connect/offer-in-app-events/overview-of-in-app-events/) and [how to submit one](https://developer.apple.com/help/app-store-connect/manage-submissions-to-app-review/submit-an-in-app-event/).

An event is a timely happening inside the app. Apple names challenges, competitions and special content launches as good candidates. It says repetitive activities such as daily tasks, price promotions that add nothing new, and general promotion of the app are not. An event can run up to 31 days, can be promoted up to 14 days before it starts, and an app can have up to 10 published at a time, with up to 15 approved. The roles are the same four as for nominations. Metadata limits: name 30 characters (title case), short description 50, long description 120 (both sentence case); media at 16:9 for the card and 9:16 for the details page. Prices in the metadata lead to rejection. Events are reviewed apart from app versions, and if the app has not yet been approved, an event goes in the same submission as the first version. There are seven badges: Challenge, Competition, Live Event, Major Update, New Season, Premiere and Special Event. [Guideline 2.3.13](https://developer.apple.com/app-store/review/guidelines/) adds that the event must fit one of the types App Store Connect offers, and that its metadata must be about the event, not the app in general.

Does PlantAdvocate have anything that qualifies? Not today. The launch itself is general promotion of the app, which Apple excludes. Care checks are daily tasks, which Apple also excludes, and the Watered streak is a repetitive mechanic rather than a challenge with a goal and an end. The closest thing is the February repot check, a once-a-year moment tied to a month, and the November to February feeding rest. Both are existing features rather than new content, and the Special Event badge is described as for events that provide new content, features or goods. So a "February Repot Check" event might be refused, and I would treat it as a maybe, not a plan. An event would qualify more clearly if a future version shipped something new with a date on it, which would suit the Major Update badge.

There is a practical gap too. Apple tells developers to provide a deep link (a universal link, or a custom URL) that opens the event in the app, and to test it. The app has nothing to give: `mobile/app.json` has no `scheme` and no associated domains (the only URL scheme in it is the Google sign-in redirect), and nothing in `mobile/src` handles an incoming link. Until a build adds one, an event's Open button could only open the app at its default screen. Deep links from custom product pages (iOS 18 and later) and the Smart App Banner's optional `app-argument` have the same dependency.

## Product page optimization and custom product pages

Read on the Apple pages for [product page optimization](https://developer.apple.com/app-store/product-page-optimization/) and [custom product pages](https://developer.apple.com/app-store/custom-product-pages/), and the help pages for [PPO](https://developer.apple.com/help/app-store-connect/create-product-page-optimization-tests/overview-of-product-page-optimization/), [creating a test](https://developer.apple.com/help/app-store-connect/create-product-page-optimization-tests/create-a-test/) and [custom product pages](https://developer.apple.com/help/app-store-connect/create-custom-product-pages/configure-multiple-product-page-versions/).

Product page optimization tests different app icons, screenshots and app previews on the live product page, against the original, on iOS and iPadOS 15 and later. A test can have up to three treatments, a chosen share of traffic, and runs for up to 90 days or until stopped. Only one test runs at a time, and a test cannot be changed once started. It tests creative only, not the name, subtitle, keywords or description. If a treatment includes an alternate icon, every icon variant has to be in the app binary. For a new app the catch is availability and traffic. The app must be live on the App Store, and Apple's duration estimate relies on the app's existing impressions and downloads, so on the first day there is nothing to estimate from. Apple's own example tests came from large apps. I found no minimum traffic Apple recommends. My view is not to start one until the estimator in App Store Connect says a test would finish inside 90 days.

Custom product pages are different, and available from release. Up to 70 extra versions of the product page can exist per app, each with its own screenshots, promotional text and previews, a unique URL, and optionally a deep link. An app qualifies once it is Ready for Distribution in at least one country or region, or on pre-order. Each page must be approved by App Review, separately from app updates. A page is shown only to people who follow its link, or in search for keywords assigned to it. Per-page numbers in App Analytics appear only after the page has 5 first-time downloads. Apple says developers see an average increase of 2.5 percentage points in conversion when sending people to a custom page. That figure is Apple's, for all developers, and says nothing about an app with no ratings.

For PlantAdvocate, three pages come to mind. One would be for pets: hazard screenshots first, linked from anywhere people ask about toxic plants. One would be for edible beds, and one for windowsill houseplants. Each can start from a blank page or a copy of the default page, so the cost is mostly swapping the first three screenshots and the promotional text. The screenshot set is the real work: `docs/app-store/screenshots.md` describes a demo garden that takes two days to prepare. The tradeoff is that every page needs its own review and its own upkeep for one person. I would build one, for pets, after launch if the pet searches show up, and no more until there are numbers.

## Campaign links and App Analytics

Read on [Apple's campaign links help page](https://developer.apple.com/help/app-store-connect-analytics/acquisition/campaign-links/) and the [App Analytics page](https://developer.apple.com/app-store/app-analytics/).

A campaign link is the app's product page URL with parameters added: `pt=` (the provider token), `ct=` (the campaign token) and `mt=`. Apple's example is `https://apps.apple.com/app/apple-store/id123456789?pt=123456&ct=test1234&mt=8`. The provider token identifies the developer account and stays the same across all campaigns, and only `ct` changes. A campaign token can be up to 30 characters from a stated set of letters, digits, spaces and punctuation, with no space first or last. Links are made in App Store Connect under Analytics, Acquisition, Campaigns.

This is the measurement that fits PlantAdvocate's privacy position. Apple describes it as privacy-friendly. It needs no SDK in the app, no tracking prompt and no identifier, so nothing changes in the privacy manifest, which already declares no tracking (`NSPrivacyTracking` is false in `mobile/app.json`). Apple reports impressions, product page views and downloads per token. A metric appears only if it reaches 5 in the date range chosen, and campaign data in the dashboard appears only after the campaign has had first-time downloads from at least 5 individual users. Apple says very small groups may be withheld in the detailed reports as well.

Two consequences for launch. First, the Campaigns tab, and the add button, may not appear until the app has been live for at least 24 hours and has had downloads, so a link with a campaign token cannot be made on release day. Anything shared in the first day has to be a plain product URL. Second, with the 5-user floor and the low volumes of a first winter, most per-channel tokens will show nothing. Use few tokens and group channels. A naming plan inside the 30 characters: `site_hero`, `site_footer`, `extension_pages`, `social`, `press`, `email_update`.

Thin evidence: I did not find whether campaign links can be created through Apple's API (a forum thread I could not read in full suggests not; not re-checked), though the help page does say campaign data can be exported in bulk through the Analytics reports API, and whether a custom product page link can also carry `pt` and `ct` is not stated on the pages I read.

## The ratings prompt

Read on Apple's [RequestReviewAction documentation](https://developer.apple.com/documentation/storekit/requestreviewaction), [Requesting App Store reviews](https://developer.apple.com/documentation/storekit/requesting-app-store-reviews), the [Ratings and reviews human interface guideline](https://developer.apple.com/design/human-interface-guidelines/ratings-and-reviews), [App Review Guidelines 5.6.1](https://developer.apple.com/app-store/review/guidelines/) and [expo-store-review](https://docs.expo.dev/versions/latest/sdk/storereview/).

The rules. If the person has not rated or reviewed on this device, StoreKit shows the request at most 3 times in 365 days. If they have, it asks again only for a new app version and more than 365 days later. The call may show nothing, so it must not be tied to a button. In development it always shows, and in TestFlight builds it has no effect, so it cannot be tested before release. People can turn the prompts off for all apps. Apple's guidance is to ask after a task completed successfully or after real engagement, never at first launch or in onboarding, never mid-task, and with at least a week or two between asks. Guideline 5.6.1 says to use the provided API and that custom review prompts are disallowed. [Guideline 3.2.2(x)](https://developer.apple.com/app-store/review/guidelines/) bars forcing a rating, and the business section bars paid, incentivized, filtered or fake feedback. expo-store-review adds that no question should come before the prompt, which rules out the "are you enjoying it?" screen that filters unhappy people away. On iOS, [Expo's module](https://github.com/expo/expo/blob/main/packages/expo-store-review/ios/StoreReviewModule.swift) (main branch today) calls `AppStore.requestReview(in:)` on iOS 16 and later and `SKStoreReviewController` before that. `SKStoreReviewController.requestReview(in:)` is [deprecated from iOS 18](https://developer.apple.com/documentation/storekit/skstorereviewcontroller), with `AppStore.requestReview(in:)` as the replacement. Expo's docs currently recommend version ~58.0.2, and the app is on Expo SDK 57, so the package would be added with `npx expo install expo-store-review`, which picks the matching release.

Does the app ask now? No. A search of `mobile/` (outside `node_modules`) for `StoreReview`, `requestReview`, `write-review`, `apps.apple.com` and `itms-apps` finds nothing, `expo-store-review` is not in `mobile/package.json`, and there is no App Store link anywhere in `mobile/`, `site/` or `docs/app-store/`. There is also no "Rate PlantAdvocate" row in Settings.

Why it matters: Apple lists ratings and reviews among the user-behavior signals in [search](https://developer.apple.com/app-store/search/), and the featuring factors mention positive ratings. Every app in the tables above beats PlantAdvocate on count by a long way. Recommendation, for 1.1.4 rather than 1.1.3 (adding a native module to a build that has never run on a phone adds risk): add the system prompt after the third distinct day on which the person has completed a check, shown a few seconds after the check finishes, and only on the next app launch after that. Apple's sample gives a similar pattern, and it leaves the choice of conditions to the developer. Separately, a "Rate PlantAdvocate" row in Settings that opens `https://apps.apple.com/app/id6792203800?action=write-review` is something Apple's own documentation suggests (a persistent link to the product page with that parameter). It is a link, not a custom prompt. The id comes from App Store Connect and is worth confirming after release. The cost of the prompt is one more native dependency and, for some people, one more interruption. The system also decides whether it shows at all.

## Apple Ads

Read on [Ads on the App Store](https://ads.apple.com/app-store), [Apple Ads Basic](https://ads.apple.com/app-store/basic), [Compare Apple Ads solutions](https://ads.apple.com/app-store/help/apple-ads-basic/0001-compare-apple-ads-solutions), [Promote an app with Basic](https://ads.apple.com/app-store/help/apple-ads-basic/0039-promote-an-app-with-basic), [Solve setup and access issues](https://ads.apple.com/app-store/help/get-started/0052-solve-setup-and-access-issues) and [View Basic performance](https://ads.apple.com/app-store/help/apple-ads-basic/0044-view-basic-app-promotion-performance).

Basic runs ads in App Store search results only. You choose the app, the countries, a monthly budget (up to $10,000 per app per month) and a maximum cost per install. Apple suggests the maximum. There are no keywords or audience settings. You pay per install. Basic's reporting counts downloads and redownloads within a 30-day window from when the person engages with the ad. Basic has the AdServices Attribution API but no keyword data. Advanced runs on the Today tab, the Search tab, search results and other apps' product pages. It prices per tap with a daily budget, lets you choose keywords, align ads with custom product pages, and read search term reports. Its keyword tools show the 1 to 5 popularity score. Both need the app to be live: Apple says an app must be available for purchase or download on the App Store to run ads. Both pages say eligible developers who sign up get a $100 credit, with full terms I did not read.

Is a small budget worth it? [AppTweak's 2025 US figures](https://www.apptweak.com/en/aso-blog/apple-ads-benchmarks) for search results ads give Lifestyle a median cost per tap of $1.18, a median cost per install of $2.62, a 54.8 percent conversion rate and a 7.4 percent tap-through rate (about 2,800 advertisers, January to December 2025, medians across monthly rows). At $2.62 an install, $100 buys on the order of 38 installs. That is a measurement budget, not a growth budget, and a first-week app with no ratings may convert worse than the median (my inference). These are one vendor's numbers, and other vendors publish different ones; I could not verify a second set from page text.

My view is $0 at launch. If Allison wants data, the one thing paid search gives that nothing else does is the popularity score and the search terms people used, which only Advanced shows. Apple's glossary adds that a search term needs at least 10 impressions before it shows as anything but "low volume", so a small budget will reveal few of them. So the credit is better spent there, on three or four exact keywords from the list above, for two weeks, with daily budgets low enough to cap spend. Basic is simpler for someone short of time, but it would show only that installs happened, not why. Apple does not say whether paid installs help organic ranking, and I would not assume they do.

## The App Store badge and marketing guidelines

Read on [App Store marketing guidelines](https://developer.apple.com/app-store/marketing/guidelines/), [Apple's trademark guidelines](https://www.apple.com/legal/intellectual-property/guidelinesfor3rdparties.html) and [App Store Marketing Tools](https://toolbox.marketingtools.apple.com/en-us/app-store/us).

The badge. Use Apple's own artwork only. The preferred badge is black, with the gray border as part of the artwork. The white alternative is for when a black badge looks too heavy and only one badge appears. If badges for other platforms appear, use black and put the App Store badge first. One badge per layout, in a subordinate position. Do not modify, angle or animate it, and do not make your own localized version (the words "App Store" always stay in English). Minimum size is 40 px on screen and 10 mm in print, with clear space equal to a quarter of the badge height. Do not add trademark symbols to it, and keep photos and text out of its clear space. The Marketing Tools page generates links, badges, app icon buttons and QR codes for an app from its store listing. The artwork license covers use only in connection with apps available for download on the App Store, so the badge cannot go on the site before release. The pre-order badge exists for pre-orders, and has to be replaced on release.

Words. Say "available on the App Store" or "downloaded from the App Store", never "at the App Store", "Apple App Store" or "downloadable". Write "App Store", "iPhone" and the other names exactly as in Apple's trademark list, singular, never all capitals. Use Apple names in a referential phrase: "PlantAdvocate for iPhone", or "works with iPhone", and Apple says not to put the product name first ("iPhone app name"). The trademark guidelines add that a mark may not be part of your product name and that nothing may suggest Apple's endorsement or sponsorship. Avoid "iOS" in marketing copy. Include an Apple credit line wherever the site gives legal information, once, listing the Apple marks used; for a site read worldwide, Apple's international form is "[marks] are trademarks of Apple Inc., registered in the U.S. and other countries." Apple also says that when the App Store badge is used, the credit covers both Apple and the Apple logo. For this site, once the badge is on it, that would read:

```text
Apple, the Apple logo, iPhone and App Store are trademarks of Apple Inc., registered in the U.S. and other countries.
```

Apple's [trademark list](https://www.apple.com/legal/intellectual-property/trademark/appletmlist.html) shows iPhone® and App Store® as registered marks. The symbols are for U.S.-only material, and Apple says not to add them to headlines or to the badge. At the moment no page in `site/` has a credit line, and `site/support.html` calls the app "the PlantAdvocate iPhone app", which sits awkwardly with Apple's preference for "PlantAdvocate for iPhone". Both are small fixes for the launch-day site edit.

Text links: I found no separate rule for plain text links in Apple's guidelines. What applies is the naming rules above and the use of Apple's artwork for the call to action, which Apple says belongs in all digital and printed marketing. A text link to the product page, or to a campaign link, is the safe form.

## The Smart App Banner

[Apple's Smart App Banner documentation](https://developer.apple.com/documentation/webkit/promoting-apps-with-smart-app-banners) gives the tag. It goes in the `head` of each page where the banner should show:

```html
<meta name="apple-itunes-app" content="app-id=6792203800">
```

`app-id` is required and is the number after `id` in the product page URL, also shown as the Apple ID in App Store Connect under App Information. An optional `app-argument` passes a URL so that an installed app can open to the matching place, which needs link handling the app does not have. Apple describes the banner as a consistent, unobtrusive one at the top of the page with a large Close button, which does not return once dismissed. If the app is installed, it offers Open. If not, it takes the person to the App Store. It does not appear if the device cannot run the app or the app is not offered where the person is, it cannot be shown inside a frame, and it does not appear in the iOS simulator. It adds no script, cookie or third party to the site, which suits the privacy policy.

Apple's campaign links page says tokens can be added to a banner, and that the provider token has to be made first from a campaign link. It does not show the syntax, and Apple's current banner page lists only `app-id` and `app-argument`. Older tutorials show an `affiliate-data` parameter, and one Apple forum post uses `affiliate-data=ct=...`, but I could not read Apple's answer, so I treat the syntax as unverified (the tutorials and the forum post were not re-checked). The safe route is a banner with only `app-id` and campaign links on the site's own buttons.

The 13 pages in `site/` are static, so this is one line per page, added at the same time as the badge. It must wait for release: before then the banner would point at a page that returns 404. Apple says a released version [may take up to 24 hours to appear](https://developer.apple.com/help/app-store-connect/manage-your-apps-availability/select-an-app-store-version-release-option) on the App Store, so check that the product page loads before the site goes live with the banner. The desktop site generator mentioned in the handoff would overwrite these edits if it were run before it is reconciled with `site/`.

## Release options and timing

Version release options, from [Apple's help](https://developer.apple.com/help/app-store-connect/manage-your-apps-availability/select-an-app-store-version-release-option): release automatically after approval, automatically but no earlier than a date, or manually. A manually released version waits in Pending Developer Release, and Apple sends a reminder email if it waits more than 30 days. The finish-line handoff already recommends the manual option. [Apple says](https://developer.apple.com/distribute/app-review/) App Review typically reviews at least half of submissions in under 24 hours and 90 percent in under 48. The last holiday notice I could find is [from 2 December 2024](https://developer.apple.com/news/?id=iwvebnw2), saying submissions stay open and reviews may take longer from December 20 to 26. I found no 2026 notice yet.

Pre-order is the other lever, and the only one that has to be decided before the first release. [It is available in any country or region where the app has not yet been released](https://developer.apple.com/help/app-store-connect/manage-your-apps-availability/publish-for-pre-order/), which for PlantAdvocate is every one of them; free apps are eligible, the release date must be 2 to 180 days out, and the product page is public from the day the approved version is released into pre-order. Custom product pages work with pre-orders, and Apple's featuring page lists pre-orders as a way it highlights launches. For PlantAdvocate it would mean approval in November, a public page, and a release in, say, late February. The cost is that people who pre-order get nothing until then, no ratings accumulate, and the app sits idle during the quiet months. The benefit is a dated spring moment. With the app complete, the site ready and no marketing machinery, I would not use pre-order. The decision is Allison's, and my evidence on how pre-orders perform for a small free app is nil.

## Seasonality and a late-October launch

Direct data on plant-care apps is the missing piece. I found no published monthly download series for gardening or plant-care apps. I tried to read Google Trends itself, and its explore page answered HTTP 429 from this machine today, so I did not get a series from it. What exists is about gardening searches in general.

- [Google's own Trends page for US gardening](https://trends.withgoogle.com/trends/us/gardening/) says interest rises every spring. It names April as the peak only for "native plants nursery", and gives no index values in the text.
- [Jayson Lusk's 2022 analysis](https://jaysonlusk.com/blog/2022/5/16/interest-in-gardening) of the US "gardening" term across Google Trends since 2004 finds peaks in April and May each year, a long downward drift, and April and May 2020 at levels not seen for at least a decade.
- [Greenhouse Grower, 29 March 2016](https://www.greenhousegrower.com/?p=129165) reports that most garden-related terms peak in April or May and bottom out in December or January, with "growing food" the exception, interested throughout the year. It is a trade-magazine reading of Google Trends since 2004 and is a decade old.
- For indoor plants, [BookNet Canada's 2019 analysis](https://booknetcanada.ca/blog/2019/8/2/the-growth-of-houseplant-culture-and-books-about-indoor-plants) of Canadian Google searches found "plant*" peaking around Victoria Day in late May, while "indoor plant*" showed no seasonal pattern. That is Canada, 2019, and the only houseplant-specific seasonality I found.

As a rough cross-check I pulled English Wikipedia's monthly pageviews for [Gardening](https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Gardening/monthly/20180101/20260930), [Houseplant](https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Houseplant/monthly/20180101/20260930) and [Vegetable garden](https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Vegetable_garden/monthly/20180101/20260930) and divided each month by its year's average, across 2018, 2019 and 2021 to 2025 (2020 left out). This is global and not a search measure, so treat it as a weak proxy. March to May ran about 1.04 to 1.22 times the year's mean (May highest for Vegetable garden at 1.22), and December ran lowest, at about 0.75 to 0.80, with November at 0.88 to 0.93. January, which Greenhouse Grower calls a low, came out near average (1.02 to 1.03 for two of the three). That is a conflict I cannot resolve. Absolute pageviews also fell over the period, for example Gardening from about 16,500 a month in 2018 to about 5,200 in 2025, so these are shapes, not volumes.

What this means for a launch in late October, with the calendar below as suggestion:

- A launch now lands about six months before the April and May peak and about two months before the December low. Expect little organic search volume through the winter. That is a guess from the shape of the data, not a measured figure.
- The houseplant half of the app is probably less seasonal than the garden half, on thin Canadian evidence. The vegetable and bed half is the seasonal one, and "vegetable garden" is the term PlantAdvocate has least reason to chase anyway.
- A quiet winter is not a bad time for a first release. It lets the first ratings and reports come in while volume is low and fixes are cheap, ahead of the spring push. The cost is a product page with no ratings through the months when nobody is looking.
- The app has its own calendar: feeding reminders rest from November to February and the repot check falls in February. The promotional text drafts above are written for those moments.

| Month | What the sources say | Suggested use |
|---|---|---|
| Nov 2026 | Falling toward the December low; no app data | Release after approval, or hold (see above). Send nothing mass on day one. |
| Dec 2026 | Lowest month in the proxy and in Greenhouse Grower. Apple review may be slower from December 20 to 26 (2024 notice) | Fix anything the first reports show. Submit any update before mid-December. Add the first campaign links once they are available. |
| Jan 2027 | Conflicting: low in Greenhouse Grower, near average in the proxy | File the spring featuring nomination: 3 months ahead of mid-April is mid-January. |
| Feb 2027 | Rising toward spring | Switch promotional text to the repot-check line. Consider a pets custom product page if the pet searches have shown up. |
| Mar to May 2027 | The peak (Google's page, Lusk, Greenhouse Grower; proxy 1.04 to 1.22) | The one season to spend effort or credit. Run the Apple Ads credit then if at all. |

## Where the evidence is thin or conflicting

The iTunes API order is not documented as the in-store ranking. I have no keyword popularity data, so the "thin competition" reading of the pets and watering terms rests on rating counts alone. Apple does not publish how name, subtitle and keywords are weighted, and does not say whether it combines words across fields or stems words. Whether "PlantAdvocate" is split into two words is unknown. I cannot see App Store Connect, so name availability is unconfirmed. The featuring lead time is 3 weeks on the help pages and 2 weeks (with up to 3 months for wider consideration) on the featuring page. I did not find whether a nomination can be filed before first approval, or any acceptance rate. The syntax for campaign tokens in a Smart App Banner is not in Apple's current banner page. Whether a custom product page link can carry `pt` and `ct`, and whether campaign links can be created through the API, are unconfirmed. Apple's 2.5 point conversion figure for custom pages is Apple's own average across developers. The Apple Ads cost figures are one vendor's medians, and I could not verify a second vendor's. The $100 credit's terms were not read. For seasonality there is no published app download series, Google Trends returned 429, the houseplant evidence is one Canadian analysis from 2019, and the Wikipedia proxy is global and disagrees with Greenhouse Grower about January. The 2024 holiday review notice may not apply in 2026. Text-link rules for the badge: none found.

## Fact-check, 2026-10-23

Every Apple page cited above was fetched again on 2026-10-23, along with the AppTweak benchmarks, the Expo docs and module source, Apple's trademark guidelines and list, the four seasonality sources, the Wikipedia pageview series and the iTunes Search and Lookup calls. The repository claims (no review prompt, no `scheme`, no associated domains, `NSPrivacyTracking` false, 13 site pages, no credit line, the listing's field lengths, the screenshot order) were checked against `3f6d7da`. Most of the file held up: the nomination roles, types, field limits and the 3-week and 2-week lead times; the in-app event limits (31 days, 14 days ahead, 10 published, 15 approved), the poor-candidate list and the rule that a first event goes in with the first version; the custom product page rules (70 pages, Ready for Distribution, keywords from the latest approved version, 5 first-time downloads, 2.5 points); the product page optimization rules (live app, 3 treatments, 90 days, icons, screenshots and previews only); the campaign link rules (no link before the app has data, about 24 hours live, 30-character tokens, a threshold of 5); the StoreKit limits (3 times in 365 days, not from a button, no effect in TestFlight); Guidelines 2.3.7, 2.3.13, 3.2.2(x) and 5.6.1, which say what the file says; Apple Ads Basic and Advanced as described, including the $10,000 cap and "no budget maximum"; the AppTweak Lifestyle medians ($1.18, $2.62, 54.8 percent, 7.4 percent, about 2,800 advertisers, 2025); the badge rules; the Smart App Banner tag and its frame and simulator limits; the search-relevance factors and the promotional text rule; and the toxic plants pets median of 6.5 with seven of ten under 100.

What changed, and why:

- The plant care median was 62,168. Two re-runs of the same call returned the same first eight apps but a different ninth and tenth, and gave a median of 80,634.5, so the text now says about 80,600 and notes that the order shifts between calls. The other medians reproduced (44,734; about 6,000; 1,398.5; 182.5; 6.5).
- Keywords: Apple says the field is 100 characters in total, with commas and no spaces. It does not separately say that commas count toward the 100, so that wording was replaced with Apple's own.
- Description: Apple's advice is not to add "unnecessary" keywords to the description, not a ban on keywords there. The word was restored.
- Screenshots: moving the hazards shot to third would push out "The check before planting" (shot 3 in `docs/app-store/screenshots.md`), not the "checks" shot, which is already fourth.
- Nominations: the "purpose and priority" instruction is Apple's guidance for new-content and enhancement nominations. An App Launch nomination is asked only for a detailed description.
- The helpful-details draft said anything not yet cited says so, which could read as if every other fact is cited. It now also says the check schedules for 129 common plants were written by PlantAdvocate and are not cited. Recounted at 414 of 500.
- Custom product pages: Apple lets a page start blank or from a copy of an existing page, not only from a copy.
- Apple Ads Basic: Apple's reporting window runs 30 days from when the person engages with the ad, not from the tap, and it counts redownloads too. A clause was added saying that Advanced's search terms show as "low volume" below 10 impressions, which matters for a $100 test.
- Credit line: the draft added "and regions" to Apple's international form, and it left out Apple and the Apple logo, which Apple says to credit whenever the badge is used. Both are fixed. The trademark list, which the file said it had not fetched, was fetched, and it shows iPhone® and App Store®.
- Pre-order: Apple makes pre-order available in any country or region where the app has not yet been released, not "only for apps never published". For PlantAdvocate the effect is the same.
- The deep-link paragraph now notes that `mobile/app.json` does carry one URL scheme, the Google sign-in redirect, which is not a deep link.

Not re-checked, and marked so in the text: the 26 subtitles beyond the four quoted (Plant Parent, Greg, Seedtime and Planter were re-read and match, and all four show In-App Purchases); the forum thread on creating campaign links through the API; the older `affiliate-data` tutorials and the forum post about banner syntax. The name and description statistics come from rough word searches over a result set that shifts. A re-run of the first twenty results per term gave 93 distinct apps, 60 "Brand: descriptor" names, a median name length of 26, a median description of 1,939 characters, 41 mentioning a subscription or similar, 20 mentioning AI and 40 Lifestyle apps. These are close to the figures above but not identical, so treat those counts as approximate. The App Store Marketing Tools page was not re-opened, though the marketing guidelines page describes the same tools.
