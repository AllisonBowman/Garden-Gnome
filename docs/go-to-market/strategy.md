# PlantAdvocate go-to-market strategy, October 2026 to June 2027

Written 2026-10-24 against the ship tip `3f6d7da` (branch `care-advice-honesty`, PR #22), for PlantAdvocate 1.1.3's first trip to App Review and the eight months after it. It argues that the App Store itself should carry the launch, paced by the gardening season: fix the product page before Submit, release quietly into the low season, gather honest ratings over the winter, and spend the heavier effort in March to May, when gardening searches peak.

Everything here is a draft and a recommendation. Nothing was posted, sent, filed, submitted or signed up for while writing it, and every outward step is Allison's to take or leave. Every product claim and every line of public copy was checked against [product-truth.md](product-truth.md); where this file and that sheet disagree, the sheet wins. The research is cited by link: [competitors.md](research/competitors.md), [channels.md](research/channels.md), [aso.md](research/aso.md), [review-risk.md](research/review-risk.md) and [launch-playbook.md](research/launch-playbook.md). "The handoff" is [docs/2026-10-16-app-store-finish-line-handoff.md](../2026-10-16-app-store-finish-line-handoff.md), and its numbered steps and decisions are the ones meant here. Paths in backticks are relative to the repository root. Where a number, a threshold or an estimate of Allison's time is my own judgement, the text says so.

## The plan in brief

Let the App Store do most of the work, because it is the one channel that keeps working in the weeks Allison is on other projects. The clearest recent picture of a launch with essentially no marketing is 97 downloads in the first month, 90.6% of them from App Store search ([launch-playbook.md](research/launch-playbook.md), Habit Doom). Almost everything else the research looked at is closed or a lottery. Promotion is banned in nearly every Reddit community where PlantAdvocate's audiences gather ([channels.md](research/channels.md)). A 2023 indie launch pitched about 20 journalists and got no coverage. About 3% of Show HN posts reach 50 points ([launch-playbook.md](research/launch-playbook.md)).

This week, export the July waitlist from Cloudflare before the step 3 site deploy, and file the App Launch featuring nomination. Have the 33 curated care notes that call a plant "Pet-safe" or "harmless" rewritten, and production's existing rows updated to match; this is an honesty fix, and it has to be live before release. Let five small site copy fixes ride with step 3. In step 4, paste a new subtitle and keyword field, upload the screenshots in a new order, and set the app to the United States only, with a manual release.

At launch, release quietly. Check a clean install from the store, then put the App Store badge and two privacy clauses on the site. On L+1 or L+2, send one email to the waitlist with a campaign link, and reply to everyone who emailed for early access. From then on, reply to every written review within 2 business days. Once the holiday plants' pages have been read against their sources, add a pets custom product page with a holiday line.

Through the winter, spend about an hour a week. Read the numbers on Mondays. Make three backend changes to the hazard sentences before spring. Build the scene-adopted 1.1.4 that Apple's April 2027 SDK rule forces anyway, and put Apple's ratings prompt in it with a "Rate PlantAdvocate" row in Settings. Submit it around 1 February; the end of March is the latest safe approval date. A small December build with the prompt is worth it only if L comes by mid-November and the first two weeks are clean.

For spring, rotate the promotional text toward the fit engine, and never mention frost, zones or planting dates. If the ratings and conversion justify it, run one small Apple Ads test for keyword data. If Allison wants, publish one lily of the valley write-up. If the spring hours don't come, the store-only spring still works.

It is worth the effort because the product page is where PlantAdvocate's real differences sit, beside the app a searcher was about to install. Between 29% and 59% of the plant-care leaders' 1 and 2 star reviews are about money, none of their listings names a source, and eight of the 18 product pages checked declare data used to track ([competitors.md](research/competitors.md)). Two searches close to what the app does are nearly empty: the median rating count in the first ten results is 6.5 for "toxic plants pets" and 182 for "plant watering reminder", against about 80,600 for "plant care" ([aso.md](research/aso.md)). Once it ships, the prompt keeps paying without Allison's time. The plan runs at $0, in roughly 70 hours over eight months (my estimate). The price is a slow first winter, which the plan accepts and measures.

## Why the App Store carries this launch

Apple describes search results as based on text relevance (the name, subtitle, keywords and primary category) and on user behavior such as downloads and ratings ([aso.md](research/aso.md)). It lists "positive ratings and reviews" among the product page factors its editors weigh for featuring ([Apple, Getting featured](https://developer.apple.com/app-store/getting-featured/)). So this plan treats the product page as the shop window and search as the main road in. Everything else is fuel for the two signals Apple names, downloads and ratings.

The store is also where PlantAdvocate's differences are visible at the moment of choice. Its page will show no in-app purchases. Its privacy label will read "Data Linked to You: Contact Info, Identifiers, Location, User Content", with nothing under Data Used to Track You ([product-truth.md](product-truth.md), section 5). Its description names its sources and says what isn't cited. No podcast or post puts those facts beside the competitor a searcher was about to install.

The season sets the pace. US gardening search interest peaks in April and May and bottoms out in December or January. In a Wikipedia pageview proxy, March to May ran 1.04 to 1.22 times the year's average and December ran lowest, at 0.75 to 0.80 ([aso.md](research/aso.md)). A November release lands in the quietest stretch. That is also the safest time for a build nobody has run on a phone: 140 commits, a first production boot with twelve migrations, and a first request after idle that took 6.7 seconds on 15 October (the handoff; [launch-playbook.md](research/launch-playbook.md)). A rough first week costs little in November. The winter's users then build the rating line the page needs by March.

The weak point is plain. Search ranks what is already downloaded and rated, a new app has neither, and 1.1.3 has no way to ask for a rating ([aso.md](research/aso.md)). The plan answers that in four parts. Step zero fixes the search-facing metadata before Submit, because it then stays fixed until the next version. The one move is a ratings prompt in a build Allison has to make anyway. The seed is the July waitlist. And the timing gives the first ratings the winter to gather.

## Positioning

PlantAdvocate is for people who keep plants in particular places, a windowsill, a shelf, a raised bed, a bed along a fence, and want to be told plainly what suits each spot, what doesn't and which published source says so, for free and with no ads. It is not for someone who wants to point a camera at any plant for an instant verdict, a planner with sowing dates, frost dates or bed layouts, a plant doctor, a verdict that a plant is safe for a pet, or an app for Android or iPad.

Each "not for" is a fact, not a style choice. Photo matching appears only on iPhones with Apple Intelligence, suggests catalog species to confirm, and has no measured accuracy. Apple's own Visual Look Up already identifies plants in Photos from iOS 15 ([product-truth.md](product-truth.md), section 1; [competitors.md](research/competitors.md)). There is no sowing calendar or bed layout, and the fit engine deliberately doesn't judge cold, so it never says whether a plant will survive a winter outdoors (`garden-gnome/app/services/fit.py:41-49`). Photo check-ups and symptom reading are switched off in 1.1.3. The app never calls a plant safe. It is iPhone only, and on iPad it runs in an iPhone-shaped window ([product-truth.md](product-truth.md), section 2).

In the store, that sentence becomes the subtitle and the first three screenshots, which are what a searcher sees in the results list before tapping ([aso.md](research/aso.md)). Step zero below sets both.

## Who it is for, in order

The order follows the store's own logic: who searches for something the app answers, and who comes back, because the people who come back are the ones who will be asked for a rating.

Indoor keepers come first: the person with a basil on the kitchen windowsill, a fern on a shelf and a snake plant in the corner. They are there in November, and they come back. A watering check asks them to feel the soil and tap Watered or Still damp, and either keeps the streak ([product-truth.md](product-truth.md), section 1). A screenshot can show that difference, since competitors' reminders simply say to water ([competitors.md](research/competitors.md)). They type words the keyword field can hold, "houseplant", "watering" and "reminder", and the watering-reminder search is thin even though "houseplant" is not ([aso.md](research/aso.md)). Houseplant interest looked unseasonal in the one study found, a 2019 Canadian analysis, which is thin evidence but fits a winter release. The honest limit is that reminders exist only for the 129 species with a check schedule, which PlantAdvocate wrote and which are not cited. Between 3% and 5% of competitors' low-star reviews complain that a plant wasn't in the app, a complaint a 995-species catalog will meet more often ([competitors.md](research/competitors.md)).

Pet owners checking a plant come second, at the two moments they bring plants home: the holidays and the spring nursery trip. Theirs is the thinnest search measured, and none of the dedicated pet-toxicity apps has more than 30 ratings ([aso.md](research/aso.md), [competitors.md](research/competitors.md)). The app's hazard sentences say what the source records for people and pets, give the US Poison Control number, and never read a missing record as safe, which is the opposite of a scan-to-know-if-it's-safe promise. The limits are real. Of the 999 researched records, 561 carry no pets verdict, so a pet owner will often read "no record". The pet hazard sentence says to contact a vet and names no animal poison line ([competitors.md](research/competitors.md)). And until the care-notes fix below lands, 33 species pages contradict the app's own rule. This audience is a seasonal hook reached through the store, not the headline.

Spring bed growers come third, including new homeowners with a garden they don't yet know. The fit engine's best demonstrations are outdoors: a shade fern flagged in full sun, a climber that will outgrow a 7 ft fence (`docs/app-store/listing.md`). Of the 999 researched records, 690 are marked not a houseplant, 248 a houseplant and 61 are unmarked (the `is_houseplant` field in `garden-gnome/app/data/verified/*.json`, counted 2026-10-24), so most of the catalog is theirs. But they arrive with the April and May peak. The "vegetable garden" and "garden planner" searches are held by planners selling what the app doesn't do ([aso.md](research/aso.md)). And r/vegetablegardening has barred app developers from promoting their work since March 25, 2025 ([channels.md](research/channels.md)). They are the spring audience, reached through the store in spring, and the copy must say plainly what the app checks and what it doesn't.

Makers and early adopters come last, and only as an optional seed. Product Hunt describes its community as makers, product people and early adopters ([channels.md](research/channels.md)). They are not the market, and the evidence that a maker day moves a consumer iPhone app is one retrospective that saw no clear benefit ([launch-playbook.md](research/launch-playbook.md)).

The plan does not target native-plant and pollinator gardeners. Their values match, but the app has no field for their first question, whether a plant is native where they live ([channels.md](research/channels.md)). It does not target parents. No parent channel publishes a route, a hazard tool should not be marketed to parents, and the app is not directed at children under 13 ([product-truth.md](product-truth.md), section 5). Master Gardener programs, community gardens, garden clubs and nurseries are left out as planned channels. The programs bar anything that implies Extension endorses a product, the community-garden and garden-club bodies publish no route, and the nursery program doesn't exist yet ([channels.md](research/channels.md)).

## Fixes the marketing depends on

Four groups of fixes come before the copy that leans on them. None is marketing in itself, but each closes a gap between what the store page will say and what the app shows.

### The "Pet-safe" care notes, before release

`garden-gnome/app/data/species_catalog.json` holds 129 curated entries, the ones with check schedules. At `3f6d7da`, and in today's working tree, 33 of their care notes say "Pet-safe", "harmless to them" or "safe for most pets". A species page shows those notes in its Care notes card, and a plant's own page shows them in its Care guide (`mobile/src/screens/SpeciesDetailScreen.tsx`, `mobile/src/screens/PlantDetailScreen.tsx`). On four of them, Parsley, Catnip, Nasturtium and Gourds, the hazard sentence on the same page says the opposite. That was found on 2026-10-24 by running the server's hazard function over a scratch catalog built from the tip. On the other 29, among them Spider Plant, Boston Fern and Sunflower, the hazard sentence says either that a source records no toxicity to pets, which is "not a guarantee of safety", or that nothing is recorded. Either way the note breaks the listing's "A missing record is never treated as safe" (`docs/app-store/listing.md`) and product-truth.md's rule that the app never calls a plant safe. It does so on exactly the pages that the keywords "cat", "dog" and "poison" will send people to.

Rewrite the 33 notes without any safety claim, keeping the care advice in them. Editing the JSON alone won't reach production. `seed()` skips any species that already exists (`garden-gnome/app/data/seed.py`, "existing species are skipped"), so production's rows need a one-off update by whatever route the working tree's mojibake fix takes. Treat this as a fix to 1.1.3's honesty, not as marketing. It needs no app build, only data and a deploy. It must be live before Allison presses Release, and ideally before Submit, since App Review can open these pages. Nothing that names a holiday plant or leads with pets goes up until it is done.

The same row problem applies to the encoding fix. The screenshot shoot found 25 garbled sequences across 14 species, among them Boston Fern and Dumb Cane. It also found a temperature that read "60–85°f" (`docs/screenshots/1.1.3/README.md`). The working tree fixes both (`garden-gnome/tests/test_catalog_encoding.py`; `mobile/src/care/facts.ts`, `mobile/src/components/CareFacts.tsx`). In an App Store-first plan these matter more than they look, because the first ratings are written by people looking at exactly those pages. Check that both are on the tip EAS builds from, and that the deploy corrects the rows production already holds, since the encoding test's own note says a seeded row is never rewritten.

### The hazard sentences, before the spring hazard lines

Three backend-only changes need no build and ship with a deploy. All three should land by the end of February, before any spring promotional line leads with hazards and before availability widens beyond the US.

The first is to add "or your local poison centre" after the US number, which the handoff recommends ("These can wait"). The second is to name the source of the pet verdict inside the sentence, as the people rating already is. Today it appears only in the page's Sources card, among every other fact's sources, so "with the source named" is true of the page but not of the sentence.

The third is to cite or label the effect clauses that come from code tables rather than a cited page. In `garden-gnome/app/services/toxicity.py`, the lily and daylily wording ("acute kidney failure — a few petals or even pollen can be fatal") is sourced as "widely documented feline lily toxicosis" (`SPECIES_SPECIFIC_RISK`). The arum family's "calcium oxalate crystals" and "mouth irritation, drooling and swelling if chewed" are sourced as "characteristic of Araceae" (`AROID_TOXICITY`). The listing says hazard notes "repeat what the sources publish". So either a research-loop pass finds a cited passage for each clause, species by species, or the sentence labels the clause as PlantAdvocate's summary. Until then, store copy and promotional text don't name lilies, daylilies or any aroid. For Pothos, whose page is screenshot 06, the research record quotes NC State's page on calcium oxalate and on oral irritation, swelling and drooling (`garden-gnome/app/data/verified/b1-foliage-core.json`). So that frame matches its source in substance, but Allison should still read the in-app sentence against NC State's page before the pets page leads with it.

Any hazard copy also waits for its plant's facts to be re-checked if they rest on one of the 47 harm-capable values that only Missouri Botanical Garden backs (the handoff, "These can wait").

### The site, riding along with step 3

Five copy fixes in `site/` touch no build and can go out with the handoff's step 3 deploy. Allison's part is a 30-minute read.

1. Add the independence line, "PlantAdvocate is independent. The organizations it cites have not reviewed or endorsed it.", to `resources.html`, `index.html`, `faq.html` and `about.html`, which name the organizations and don't carry it today ([product-truth.md](product-truth.md), section 4).
2. Replace `about.html:272`'s "Species data comes from vetted horticultural sources". A truthful version is "Researched species data is cited to the organizations that published it, and older data says it isn't cited yet."
3. Replace `about.html:282`'s "Every piece of advice can be traced back to a specific fact in the database". "Traced to the catalog" is true; "traced to a cited source" isn't always ([product-truth.md](product-truth.md), loose ends). `how-it-works.html:303` has the same reach and can change in the same pass.
4. Replace `recommendations.html:281`'s pothos note, "a safe bet for most rooms", with something like "Adaptable across light levels, and easy in most rooms". It means light, but it puts "safe" beside a plant the app records as toxic.
5. Reconsider `index.html:298`'s "NO GUESSWORK" and `:324`'s "Most plant apps guess." now, not later. [competitors.md](research/competitors.md) verified only that competitors' listings name no source, not that their advice is a guess, and the strip repeats a promise two competitors make. "Sources named" and "an unknown is never a pass" are claims the product can stand behind.

Until `site/` is deployed, the live homepage still says "EVERY FACT CITED" ([product-truth.md](product-truth.md), section 6). So nobody is pointed at the live site until the step 3 check block prints `ok` on every line.

### In the app: one line in 1.1.3, one link in 1.1.4

Two small additions were planned for the next build. The first is the line "These notes repeat what the sources publish. They are not medical or veterinary advice." under the hazard sentence. [review-risk.md](research/review-risk.md) found it in the listing and the review notes but on no app screen, and on 2026-10-24 a search of `mobile/src` for "medical or veterinary" found nothing. On 2026-10-30 it was moved into 1.1.3 instead: the app shows it under the hazard note on species pages, plant pages and Add plant (`mobile/src/care/notAdvice.ts`), and the listing and the review notes now say so. The second is a "Report a fact" link on species pages, built like the existing "Report this result" link that opens a prefilled email (`mobile/src/components/ReportResult.tsx`). It gives a reader who finds a wrong fact a one-tap way to say so, which matters most for an app whose pitch is that it names its sources. It still goes into the next build, alongside the ratings prompt.

## The one move: a ratings prompt in the build Apple already requires

Add Apple's own review request to 1.1.4, asked once a person has come back and completed checks on three different days, and add a "Rate PlantAdvocate" row in Settings that opens Apple's write-a-review page. Build 1.1.4 in January and submit it around 1 February, so it is live by mid-February, ahead of the spring peak. The end of March is the latest safe approval date. The rules are in the ratings section below.

It beats every alternative for one reason above the others: it is the only move that keeps paying without Allison's weekly time. Once it ships, every person who comes back to look after a plant during the spring peak is asked once, by Apple's sheet, at a good moment, for as long as the app exists. Those ratings feed search and featuring, which both weigh ratings ([aso.md](research/aso.md); [Apple, Getting featured](https://developer.apple.com/app-store/getting-featured/)). They also feed conversion for the people who read stars. A survey summarized by Alchemer says 46% of US smartphone owners want at least four stars and 77% read at least one review before downloading, though the survey is undated and the page is from 2016 ([launch-playbook.md](research/launch-playbook.md)). Without a prompt, 1.1.3 gets ratings only from people who go to the store on their own.

It rides on a build Allison has to make anyway. Apple has said that from April 2027 every upload must be built with the iOS 27 SDK. An Expo SDK 57 app built that way crashes at launch unless it adopts the scene life cycle, so a scene-adopted 1.1.4 has to exist, pass a device test and be approved by the end of March (`docs/2026-10-24-ios27-scene-lifecycle.md`). By my estimate, adding the prompt and the Settings row to that build costs half a day to a day of work and tests, not a separate release.

There is one case for a second, earlier build. If L comes by about 15 November and the first two weeks after it are clean, a small December build is worth considering, submitted by Friday 11 December. It would carry only the prompt, the Settings row and fixes for whatever the first users hit, on the pinned Xcode 26.6 image like 1.1.3, so the winter's returning users can rate. The scene-adopted build then becomes 1.1.5. Apple's last holiday notice said reviews may take longer from 20 to 26 December ([aso.md](research/aso.md)). Each build costs Allison an Apple sign-in and phone checks. So if L is later than mid-November, or the first weeks bring bugs, skip the December build and ship the prompt with the scene work.

| Move | Allison's time (my estimate) | What it buys | Evidence |
|---|---|---|---|
| Ratings prompt in 1.1.4 | Half a day to a day, inside a build already required | A rating request to every returning person, indefinitely | Apple's search and featuring factors ([aso.md](research/aso.md)) |
| Metadata before Submit (step zero) | About 30 minutes | Which searches the app can appear in at all | Apple's relevance factors ([aso.md](research/aso.md)) |
| Featuring Nominations | About an hour each | A chance that Apple alone decides | No published acceptance rate ([aso.md](research/aso.md)) |
| Waitlist email | 2 to 3 hours once | The likeliest first ratings | [launch-playbook.md](research/launch-playbook.md) |
| Apple Ads with $100 | 2 hours to set up, then 15 minutes a week | About 38 installs at the Lifestyle median, plus keyword data | AppTweak's 2025 medians ([aso.md](research/aso.md)) |
| Product Hunt day | About 6 hours around one day | A burst of maker installs, maybe a few ratings | Söka saw no clear benefit ([launch-playbook.md](research/launch-playbook.md)) |
| Press pitches | Several hours | Probably nothing for a plant app | Söka; Muck Rack's surveys ([launch-playbook.md](research/launch-playbook.md)) |
| Reddit | Ongoing participation | One megathread post in r/iosapps; banned almost everywhere else | [channels.md](research/channels.md) |

Step zero is not a rival to the prompt. It is half an hour that has to happen before Submit, because the name, subtitle and keywords then stay fixed until a new version ([aso.md](research/aso.md)).

The prompt has limits, and the plan is built around them. It multiplies people; it doesn't bring them, so with few winter users it yields few ratings, which is why the waitlist seed matters. Apple decides whether the sheet appears at all, and people can turn the prompts off for every app. The sheet does nothing in TestFlight builds, so the trigger can only be unit-tested until the build is on the store ([aso.md](research/aso.md)). And a prompt surfaces unhappy ratings as readily as happy ones, which is the reason to fix what the first users hit before asking them.

## Step zero: the product page, before you press Submit

Search reads the name, the subtitle, the keyword field and the primary category. They change only with a new version, and a custom product page can only use keywords from the latest approved version ([aso.md](research/aso.md)). 1.1.3 hasn't been submitted, so this is the cheapest moment there will be. Everything here is an edit to what gets pasted from `docs/app-store/listing.md` in step 4 of the handoff. Nothing in the build changes.

Keep the name `PlantAdvocate: Garden Care` (26 of 30). It follows the "Brand: descriptor" shape 63 of 94 comparable apps use, and it puts "garden" and "care" in the strongest field ([aso.md](research/aso.md)). If App Store Connect refuses it, the fallback is `PlantAdvocate`, and the keyword field then has to carry "garden" and "care" itself (the fallback string below).

Change the subtitle from "What suits each spot you grow" to this, as [aso.md](research/aso.md) proposes:

```text
Plants that suit each spot
```

That is 26 of 30. It keeps the product's own idea, puts "Plants" into an indexed field, and frees the keyword field of "plant", because Apple treats a plural as a duplicate. It costs the word "grow" and some of the old sentence's character. Guideline 2.3.7 asks that a subtitle make no unverifiable claim. [aso.md](research/aso.md) reads this one as a description of what the fit engine does, and App Review decides.

Change the keywords to [aso.md](research/aso.md)'s proposal, 97 of 100:

```text
houseplant,watering,reminder,raised bed,herb,vegetable,gardening,toxic,pets,cat,dog,poison,indoor
```

It drops "plant", "perennial", "shrub", "weather" and "yard", and adds "gardening", "cat", "dog", "poison" and "indoor", aiming at the two thin searches. If the long name is refused, use this instead, 99 of 100:

```text
houseplant,watering,reminder,raised bed,herb,vegetable,garden,care,toxic,pets,cat,dog,poison,indoor
```

The costs are the ones [aso.md](research/aso.md) names. "Weather" and "yard" may carry traffic nobody can see from outside, and "gardening" is wasted if Apple stems it to "garden". The bigger cost is that "cat" and "dog" may bring people who want to point a camera at a plant and get a verdict. The screenshots and the description's "They are not medical or veterinary advice" are there so those people know before they install. The pet words stay honest only because the care-notes fix above lands before release. The cited organizations' names stay out of the keyword field, as guideline 2.3.7 requires ([launch-playbook.md](research/launch-playbook.md)), and "identify" stays out, as listing.md already decides.

Change the screenshot upload order. Apple shows the first one to three screenshots in search results when there is no app preview ([aso.md](research/aso.md)), and the planned order spends all three on the fit engine. Upload 01 (what doesn't suit a spot), 04 (checks, not chores) and 06 (hazards, Pothos), then 02, 03, 05, 07 and 08. The three frames a searcher sees then each answer one thing the metadata aims at. The fit engine leads, as the app's own idea. The watering check speaks to the indoor keepers who will come back. The hazard frame speaks to the pet searches. Good candidates (02) moves out of the first three on purpose, because a pet owner can read a list of candidates as a list of safe plants, and candidates can carry hazard lines ([product-truth.md](product-truth.md), section 2). Hazards come third, not second: they are a hook, not the headline. `docs/screenshots/1.1.3/CHECK.md`, rewritten on 2026-10-24 after seven frames were retaken, reports all 16 files passing. If any retake is still in progress at step 4, use whatever CHECK.md says then.

Keep the promotional text for launch (157 of 170). Apple lets it change at any time without review, and it doesn't affect ranking ([aso.md](research/aso.md)), so it is the place for the seasonal lines in the timeline below. Keep the description (3,792 of 4,000). It ends with the independence line ([listing.md](../app-store/listing.md), [product-truth.md](product-truth.md) section 4).

Make 1.1.3 available in the United States only. listing.md says Free in every territory. The handoff recommends keeping the US-labelled number for this submission and names US-only availability as the alternative. The app is in English only, in feet, inches and Fahrenheit, and the hazard sentences print only the US Poison Control number ([product-truth.md](product-truth.md), section 2). The review notes already tell App Review it is made for the US (`docs/app-store/review-notes.md`). Apple's summary rating is also specific to each territory ([launch-playbook.md](research/launch-playbook.md)), so the few early ratings should land on the one page the keyword research was done for. US-only costs the UK gardeners who might want an app that cites the RHS; product-truth.md is clear that the RHS is a source, not a market. Widen availability once "or your local poison centre" ships.

Release manually, as the handoff recommends, and don't use pre-order. Pre-order would give a public page with no ratings accumulating through the quiet months, and both [aso.md](research/aso.md) and [launch-playbook.md](research/launch-playbook.md) advise against it.

In-app events are not part of this plan. The launch itself is general promotion, which Apple excludes. Care checks are daily tasks, which it also excludes. And the app has no deep link for an event's Open button: `mobile/app.json` has no scheme or associated domains beyond the Google sign-in redirect ([aso.md](research/aso.md)). Revisit them if a future version ships something new with a date on it and a link to open it.

## Featuring Nominations

Apple's featuring page asks for a minimum of two weeks' notice and recommends up to three months for wider consideration. App Store Connect's help pages ask for three weeks, so plan on three. Apple says there is no checklist and names the factors it weighs, including the product page's "positive ratings and reviews". It may email people in the Admin, App Manager and Marketing roles to ask for promotional artwork. A nomination can be edited after submission, except its type and related apps. No acceptance rate is published ([aso.md](research/aso.md)).

File the App Launch nomination this week, from App Store Connect's Featuring section, using the drafts in [aso.md](research/aso.md): a 44-character name, a 612-character description and 414 characters of helpful details. A nomination filed on Monday 26 October meets the three-week floor for any date from 16 November. Don't aim the window at the release day itself. Set a date range that starts about two weeks after the expected release, so that if Apple picks the app up, the first week's fixes are already out. For a release expected around 16 to 20 November, that means something like 30 November to 31 January. If L moves, edit the range. List the United States as the country. If Allison has checked the Observatory theme on a phone, the helpful details can add that the app has a dark, colorblind-safe theme, which is how Settings describes it ([product-truth.md](product-truth.md), section 1). Nothing else about accessibility has been checked, so claim nothing else.

[aso.md](research/aso.md) found no Apple statement on whether a nomination can be filed before an app's first approval. If App Store Connect refuses it now, file it on the day approval comes, with the range starting at least three weeks out. Don't hold an approved build to wait for the window. Nobody knows how Apple treats a nomination for an app that is already live, and a hold postpones the ratings this plan needs.

File the spring nomination by Friday 15 January 2027 for a window from mid-April to mid-May, three months ahead, which is what Apple calls wider consideration. Nominate only something new. The ratings prompt, the Settings row and the report link don't count. A signed-out door into the Almanac would count, and so would Add plant saying that a species has no check schedule before you add it (handoff, engineering leftovers). If the researched catalog has grown by then, it is New Content, and "more than 990" stays true as batches land. If nothing is new, skip the spring nomination rather than dress it up. By then the helpful details can mention ratings, but only as the store shows them.

Whoever holds the roles has to watch that inbox. Keep the icon's source file and the screenshot sets where they can be found within a day.

## The ratings plan

### What 1.1.3 can do without a prompt

Until the prompt ships, the likeliest first ratings come from people who chose to hear about the app. That means the July waitlist, which [launch-playbook.md](research/launch-playbook.md) calls the audience most likely to leave the first ratings, and the people who emailed support for early access. The waitlist email carries one plain line, sent to everyone on the list in the same words, so it can't be read as asking only the people who liked the app: "once you've used it for a while, a rating or review on the App Store, whatever you make of it, helps other people decide whether it's for them" ([launch-kit/waitlist-email.md](launch-kit/waitlist-email.md)).

Reply to every written review in App Store Connect, inside the published promise of a reply "usually within 2 business days" ([product-truth.md](product-truth.md), section 3). Apple says that when a developer responds, the reviewer is notified and can update their review ([Apple, ratings, reviews and responses](https://developer.apple.com/app-store/ratings-and-reviews/)). That makes replies the one ratings lever 1.1.3 has after launch. Write them in the caretaker voice: thank the person, say what was fixed or what the app can't check, and never argue, promise a feature or soften a hazard. The likeliest complaints are known: the sign-in wall, a missing species, a pet plant with no record ([competitors.md](research/competitors.md)). A reply to "it wouldn't tell me if it's safe" is where the no-record-is-never-safe stance gets explained to the next reader.

Some things are off limits whatever the pressure for early stars. There is no round of ratings from friends and family. Apple's guidelines say a developer who inflates rankings with paid, incentivized, filtered or fake feedback can be expelled from the Developer Program, and the FTC's rule asks insiders such as relatives to disclose their relationship. There is no incentive of any kind. Nobody asks only the people who seem happy, which the FTC says "could violate the FTC Act" ([launch-playbook.md](research/launch-playbook.md)). There is no custom "rate us" screen in the app, which guideline 5.6.1 disallows ([aso.md](research/aso.md)). And no rating, review or download figure is quoted anywhere until the store shows it ([product-truth.md](product-truth.md), section 2).

### The prompt in 1.1.4, and the rules

1. Use Apple's sheet and nothing else: `StoreReview.requestReview()` from `expo-store-review`, which calls `AppStore.requestReview(in:)` on iOS 16 and later. There is no question before it, no star picker and no "Enjoying PlantAdvocate?" screen. Guideline 5.6.1 disallows custom prompts, Expo's documentation says no question should come before the sheet, and a filtering question is the practice the FTC warns about ([aso.md](research/aso.md), [launch-playbook.md](research/launch-playbook.md)). Add the package with `npx expo install`, which picks the release that matches the app's Expo SDK. From the repo root:

   ```bash
   cd mobile && npx expo install expo-store-review
   ```

2. Ask after the third distinct day on which the person has completed a check (Watered, Still damp, or a repot ending), a few seconds after a check finishes, on the next app launch after that condition is met. That is [aso.md](research/aso.md)'s recommendation, and it follows Apple's guidance to ask after a completed task and not to interrupt.
3. Never ask on the first day, during sign-in or the welcome cards, or mid-task. Never ask on or right after a screen that shows a hazard sentence or a "Needs addressing" finding, or an error or a "couldn't reach the server" message. Nobody should be asked for stars while reading a poison warning or learning that a plant doesn't suit its spot. Never wire the sheet to a button whose job is rating, because the sheet may not appear at all; that is what the Settings row is for.
4. Ask at most once per app version, and no sooner than 60 days after the last request. Those numbers are mine. Apple's own cap is three requests in 365 days, and its guidance is at least a week or two between asks ([aso.md](research/aso.md)).
5. Keep the counters on the phone: the days a check was completed, and the date and version of the last request. Apple's App Privacy definition of "collect" is transmitting data off the device ([Apple, App Privacy details](https://developer.apple.com/app-store/app-privacy-details/)), so a local counter changes neither the App Privacy answers nor the privacy policy. Check that the package brings no analytics or tracking code, because the policy promises there is none ([product-truth.md](product-truth.md), section 5).
6. Add a Settings row, "Rate PlantAdvocate", that opens `https://apps.apple.com/app/id6792203800?action=write-review`, the persistent link Apple's documentation suggests. Confirm the id once the store page answers. Keep it out of 1.1.3, because before release that link answers 404, and guideline 2.1(a) asks for working URLs ([aso.md](research/aso.md), [review-risk.md](research/review-risk.md)).
7. Unit-test the trigger. The sheet always shows in development and does nothing in TestFlight, so nothing else can test it before release.
8. Give nothing for rating: no badge, no streak credit, no unlock.

### Resetting the summary rating

Apple lets a developer reset the summary rating with a new version, recommends doing it sparingly, and keeps written reviews either way ([launch-playbook.md](research/launch-playbook.md)). Don't reset at 1.1.4 unless the 1.1.3 ratings are dominated by a bug that 1.1.4 demonstrably fixes. A young app needs every honest rating it has.

## The waitlist

### Before the site deploy

The July site posted early-access emails to a Cloudflare Pages Function at `/api/waitlist`, which wrote them to KV or D1. Step 3 of the handoff drops the endpoint, and the addresses stay in Cloudflare until exported (handoff, decision 9). [product-truth.md](product-truth.md) adds that the live homepage already uses a mailto link instead, and that nobody can tell from outside whether the Function still answers. The addresses are there either way, so export them this week, whatever date step 3 ends up on. The full steps, with the check that prints no address and the removal list, are in [launch-kit/waitlist-email.md](launch-kit/waitlist-email.md); follow that file where it and this short version differ. Run this first, because the handoff found Wrangler's token on this Mac expired:

```bash
npx wrangler login
```

Then, in the Cloudflare dashboard, open Workers & Pages, the site's project, and Settings, then Bindings, to see whether the store is a KV namespace or a D1 database. For KV, this lists the keys, and if each key is an address that is the export:

```bash
npx wrangler kv key list --namespace-id=NAMESPACE_ID --remote
```

If the addresses sit in the values instead, Wrangler's `kv bulk get` command reads many at once. Read its `--help` first, because Cloudflare's page doesn't describe its key file. For D1, this writes the schema and data to a file outside the repository:

```bash
npx wrangler d1 export DATABASE_NAME --remote --output="$HOME/PlantAdvocate-private/waitlist.sql"
```

Then check the export: how many rows, whether any carry a date, a source or a consent field, duplicates, junk, and addresses ending in `.ca`, `.uk` or an EU country code. Leave those out of the first send unless the July form clearly covered them, because Canada's CASL and the UK's rules differ from US law ([launch-playbook.md](research/launch-playbook.md)). Keep the file out of the repository and out of git, in the private folder waitlist-email.md makes; it is personal data. Don't delete anything in Cloudflare until the launch email has gone and any removal requests are on a suppression list that outlives the source. waitlist-email.md's list, `removed-hashes.txt`, holds only a fingerprint of each removed address.

Three things have to be in hand before anything is sent. The first is the July form's wording, because what it promised decides what the list may be used for. The best copy is in git: commit `25f370f` holds the homepage as Cloudflare served it on 19 July, whose form promised "Just an update when the beta opens" (waitlist-email.md). Check it against a July deployment in Cloudflare's history if one can be opened. The second is a postal address. CAN-SPAM requires a valid physical postal address in every commercial email: a street address, a USPS box, or a private mailbox registered with a commercial mail receiving agency. The site lists none today, and a home address should not go into anyone's inbox ([launch-playbook.md](research/launch-playbook.md)). The third is a clause in the privacy policy. Its account paragraph says "we don't send marketing email" (`site/privacy.html:138`), and a recipient could quote that back at a launch note, so add a clause that points to the early-access paragraph. Do it in the launch-day site edit, below.

The opt-out can be as simple as replying to the email, as long as it keeps working for at least 30 days after sending and is honored within 10 business days ([launch-playbook.md](research/launch-playbook.md)). How to send depends on the count, which nobody knows until the export; the split below is my judgement. If the export holds a few dozen addresses, separate individual emails from support@plantadvocate.ai are manageable and keep removals simple. If it holds more, use a mailing service that adds the unsubscribe link and the postal address and handles opt-outs. Buttondown is free for up to 100 subscribers, and MailerLite's free plan allows 250 subscribers and 2,500 emails a month, both read on 2026-10-24 ([Buttondown pricing](https://buttondown.com/pricing), [MailerLite pricing](https://www.mailerlite.com/pricing)); check before choosing. Turn off open and click tracking. The note has no need for it, and a list built on a no-tracking promise shouldn't be tracked.

### At launch

Send one email, on L+1 or L+2, as soon as App Store Connect lets you make a campaign link. Apple says that needs the app live and getting downloads for at least 24 hours ([aso.md](research/aso.md)). Use the token `waitlist`. Waiting a day for it is worth it, because this is the cleanest experiment in the plan: one audience, one link, one number. Send it after the clean-install check passes, and don't hold it for a press cycle, because the list was promised this news ([launch-playbook.md](research/launch-playbook.md)).

The email to send, with its subject lines, footer and sending steps, is in [launch-kit/waitlist-email.md](launch-kit/waitlist-email.md). It replaced the draft this section first carried, and where the two differed, that file is the one to follow. It says why the person is getting it: the July form promised an update when the beta opened, and no beta ever opened to the list, so this is that update. It asks everyone for a rating in the same words. Its hazard paragraph keeps the not-advice sentence. Its footer carries CAN-SPAM's advertisement label, reason, opt-out and postal address. Every claim in it is from listing.md or product-truth.md. It names no organization, so it doesn't need the independence line, and it follows Apple's naming ("PlantAdvocate for iPhone", "available on the App Store", "iPhone models with Apple Intelligence"; [launch-playbook.md](research/launch-playbook.md)).

It also tells the list that PlantAdvocate won't write to it again. The July form promised one update, and a recurring newsletter would stretch the policy's "only to tell you about PlantAdvocate" ([launch-playbook.md](research/launch-playbook.md)). So the one later note, about a genuine release, goes only to the people who reply asking for news of later releases (waitlist-email.md, "The spring note"). Never add the addresses of people who signed in to the app to any list, because the policy says account information is used only to run the app ([product-truth.md](product-truth.md), section 5).

## Channels

Each row gives the honest way in and the rule that governs it. Every Reddit rule comes from archived copies and should be re-read on the live sidebar before posting ([channels.md](research/channels.md)).

| Channel | Honest way in | The rule that governs it | When |
|---|---|---|---|
| App Store search | A relevant name, subtitle and keyword field, then ratings and downloads over time | Relevance from title, subtitle, keywords and primary category, plus user behavior; irrelevant terms are a common rejection reason; no packing with trademarks (guideline 2.3.7) ([aso.md](research/aso.md)) | From L; matters most March to May |
| Promotional text | Seasonal lines built only from facts in listing.md | Changes at any time without review; no effect on ranking ([aso.md](research/aso.md)) | Rotated as in the timeline |
| Featuring Nominations | App Launch now, with a range starting about two weeks after release; spring only for something new | Three weeks minimum in the help pages, up to three months for wider consideration; no checklist ([aso.md](research/aso.md)) | Week of 26 October; by 15 January |
| Custom product page for pets | Screenshots 06, 03 and 04 first, the holiday line, the pet keywords assigned to it | Each page is reviewed by App Review; keywords only from the latest approved version; the app must be Ready for Distribution; per-page numbers after 5 first-time downloads ([aso.md](research/aso.md)) | After L, once its gates are met |
| Ratings and review replies | The waitlist line, a reply to every review, then the prompt and the Settings row | Guidelines 5.6.1 and 3.2.2(x) and section 3; the FTC's review rule ([launch-playbook.md](research/launch-playbook.md)) | From L |
| July waitlist | One launch email with the `waitlist` token | The policy's "only to tell you about PlantAdvocate"; CAN-SPAM's address and opt-out; CASL for Canadian addresses ([launch-playbook.md](research/launch-playbook.md)) | L+1 or L+2 |
| Early-access emailers | An individual reply to each | The policy uses an address from a message only to reply ([launch-playbook.md](research/launch-playbook.md)) | L+1 to L+3 |
| plantadvocate.ai | Apple's badge, a Smart App Banner with only the app id, buttons with the `site` token, Apple's credit line, the independence line on pages that name sources | Badge only after release, Apple's artwork unmodified, at least 40 px; the site promises no analytics ([aso.md](research/aso.md), [product-truth.md](product-truth.md) section 5) | Step 3, then L |
| Podcasts and editors | At most one short note each through their own contact pages, asking for nothing, with the independence line, a postal address and a one-line opt-out | No pitch policies published; irrelevance, a promotional tone and unverifiable claims are why pitches get deleted; CAN-SPAM makes no exception for business email ([channels.md](research/channels.md), [launch-playbook.md](research/launch-playbook.md)) | Optional, March and April |
| The American Gardener (American Horticultural Society) | A proposal for an article, not about the app: two cited sources disagree on how poisonous lily of the valley is | Proposal before writing, no simultaneous submissions; features pay $300 to $700 ([channels.md](research/channels.md)) | Optional, January |
| Hacker News, ordinary submission | The lily of the valley write-up on plantadvocate.ai | "It's ok to post your own stuff part of the time, but the primary use of the site should be for curiosity" ([HN guidelines](https://news.ycombinator.com/newsguidelines.html)); never solicit votes | Optional, April |
| Show HN | Not with the app | Must be easy to try, ideally with no sign-up ([launch-playbook.md](research/launch-playbook.md)) | Not recommended |
| Product Hunt | One launch from Allison's personal maker account, asking for feedback | No asking for upvotes; company accounts can't post; 12:01 am Pacific suggested; tagline up to 60 characters; at least two gallery images ([launch-playbook.md](research/launch-playbook.md)) | Optional; a weekend between L+14 and L+21, or 9 and 10 January |
| r/iosapps | One post in the monthly App Shelf megathread, with the relationship disclosed | 10 karma earned there first; once per developer in 30 days; App Store or TestFlight links only; no generative-AI apps, so don't lead with photo matching ([channels.md](research/channels.md)) | Optional, first 30 days |
| Apple Ads | One small national Advanced test in spring, if the conditions in the budget hold | The app must be live; the $100 credit's terms weren't read; search terms below 10 impressions show as low volume ([aso.md](research/aso.md)) | Mid-March to early April |

### The pets custom product page

The pets custom product page is the store's own way to use the holiday-plant hook without putting hazards at the head of the default page. It costs a reordered copy of the existing screenshots and a line of promotional text. Lead with 06 (the Pothos hazard sentence), then 03 (Add plant, where Lady Fern shows its no-toxicity-verdict note before saving), then 04 (whose plant cards carry a "Pet caution" chip). Keep 02 out of its first three. Assign it "toxic", "pets", "cat", "dog" and "poison". Its own impressions, once it passes five first-time downloads, show whether anyone searches those words, which App Analytics won't otherwise tell you ([aso.md](research/aso.md)).

It has three gates. The 33 care notes must be corrected in production, which the plan already requires before release. Allison must read the in-app pages for poinsettia, English and American holly and American mistletoe, the holiday plants the researched data holds ([channels.md](research/channels.md)), against their cited sources, and check that none rests on one of the 47 harm-capable values only Missouri Botanical Garden backs. And Allison must read the Pothos sentence in shot 06 against NC State's page. Lilies stay out of its copy until the lily clause is cited or labelled. If the page reaches the five-download floor by February, make a second one in March for spring beds, built around shots 01 and 03. If it doesn't, make no more. Each page needs its own review and its own upkeep.

### The one editorial piece: lily of the valley

The app's own data holds one honest story. NC State Extension rates lily of the valley's poison severity low, Missouri Botanical Garden calls all its parts very poisonous, and the app had to decide what one hazard sentence should say (handoff, decision 6). Write it up once, in Allison's own words. Say what each source records, in paraphrase, and quote no source's prose. Say what the app shows, after whatever decision 6 settles. End with the independence line. Re-read both source pages the day it goes out. By my estimate it costs three or four hours.

Use it in at most two places. The first is a proposal to The American Gardener in January, with the author's interest in the app disclosed. Its guidelines ask for a proposal before writing and no simultaneous submissions. My reading is that publishing the piece on the site first would end the proposal, so wait for an answer. The second, if AHS declines or never answers, is a page on plantadvocate.ai in April, offered to Hacker News as an ordinary submission and linked with the `writeup` token. It would bring few installs and some credibility. A plant page that anyone can open without signing in is the kind of plant post that did well on Hacker News, where store and sign-in links mostly scored 1 to 4 ([launch-playbook.md](research/launch-playbook.md)). Lily of the valley stays out of all store copy, because its whole interest is the disagreement.

### Product Hunt, optionally

A maker day is the cheapest way to put a burst of installs into one day in the quiet season, but the evidence for its effect on a consumer iPhone app is weak. Söka saw no clear download benefit, and its comments filled with spam from new accounts ([launch-playbook.md](research/launch-playbook.md)). Do it only if Allison wants to, once, on a weekend between L+14 and L+21 after a clean first week. Product Hunt's own figures say weekend launches got 15% more "Visit" clicks, which is descriptive, not a promise. If L+14 falls after Sunday 13 December, use 9 and 10 January 2027 instead of launching into the holidays. Have the step 3 site live first, because Product Hunt visitors open the website.

The tagline, 52 of 60 characters:

```text
What suits each spot you grow, with the source named
```

The gallery can be the App Store screenshots in the new order. Link with the `ph` token. A maker's first comment, which Product Hunt says 70% of winners had, could read:

```text
Hi, I'm Allison, and I build PlantAdvocate on my own. It's a free app for iPhone with no ads and no in-app purchases. You describe each place you grow, a windowsill or a raised bed, and it says which plants suit that spot, which don't, and why, naming the source. Researched care facts are cited; older ones say they aren't cited yet, and the check schedules for 129 common plants are my own and not cited. Hazard notes repeat what sources publish and aren't medical or veterinary advice. Photo matching works only on iPhone models with Apple Intelligence, and you sign in with Apple or Google. I'd value feedback on anything that reads wrong.
```

It asks for feedback and nothing else; there is no rating ask in a community that bans vote solicitation. Don't call the app AI anywhere: the care advice is rule-based, and the house rule is "care engine" ([product-truth.md](product-truth.md), section 2). Don't write "Garden Gnome". Success is modest: the `ph` token clears Apple's five-download floor, and the comments turn up anything that reads wrong. If the token never clears the floor, maker venues are finished for this app.

### Left out on purpose

Most Reddit communities are left out for the app: r/houseplants, r/plantclinic, r/gardening, r/vegetablegardening, r/plants, r/NoLawns, r/dogs, r/cats, r/Mommit and r/homeowners all ban promotion. r/AppHookup excludes always-free apps. BetaList charges submitters and refuses direct app-store links. The Xerces Society takes no publicity for commercial products. The nursery trade is out because the nursery program doesn't exist. Safety organizations are not pitched at all, including during Poison Prevention Week ([channels.md](research/channels.md)).

Organizations are not a planned channel this season. That includes Extension Master Gardener programs (more than 76,500 volunteers), the American Community Gardening Association (2,100 gardens) and National Garden Clubs (5,000 clubs). Their rules make polite awareness the best outcome, and writing to them is a lot of Allison's time for that ([channels.md](research/channels.md)). If Allison does write to one, make it information only, with the independence line, a postal address and a one-line opt-out, and no follow-up. Keep a do-not-contact list. Leave the cited institutions' own Master Gardener programs out entirely: NC State, Clemson, UF/IFAS, UGA, Penn State and Maryland. A note to a cited source's program can read as a request for endorsement ([channels.md](research/channels.md)).

An open web edition of the Almanac is deferred to after spring, as a later and smaller project. It would make Show HN honest and put the reference content outside the sign-in wall. But it needs the 47 harm-capable values re-checked, a careful read of the UK database right for RHS-derived values, and real engineering, and there is no evidence yet that it moves installs.

The people who sign in are a channel this plan can never use. The policy says account information is used only to run the app and that PlantAdvocate doesn't send marketing email, and reminders are local notifications with no push token ([product-truth.md](product-truth.md), section 5). Existing users hear about a new version through the version itself and its What's New text.

## Measurement without adding trackers

The app has no analytics, ad, crash-reporting or attribution SDK, the privacy manifest declares no tracking, and the site promises "plantadvocate.ai has no analytics, ads or tracking." Adding any of those would make the privacy policy false ([product-truth.md](product-truth.md), section 5). Everything here comes from App Store Connect, which needs no code in the app. Production's database is not mined for marketing numbers either. The policy says account information is used "only to run the App", and App Privacy declares Analytics only for the opt-in census.

App Analytics reports impressions, product page views, downloads, a conversion rate, and downloads by source, such as App Store Search, App Store Browse, app referrers and web referrers. It also offers peer group benchmarks of conversion and retention against apps of similar download volume, which is the yardstick the thresholds below use. Usage and retention data cover only people who agreed to share diagnostics with developers, so don't steer by them ([Apple, App Analytics](https://developer.apple.com/app-store/app-analytics/)). Apple's page names App Store Search as a source but says nothing about search terms. The only keyword data comes from Apple Ads Advanced, whose popularity scores run from 1 to 5 ([aso.md](research/aso.md)).

Campaign links add `pt`, `ct` and `mt` to the product page URL. A metric shows only once it reaches 5 in the chosen range, a campaign shows only after first-time downloads from at least five people, and no link can be made until the app has been live with downloads for about 24 hours ([aso.md](research/aso.md)). With winter volumes most tokens will show nothing, so use five, grouped:

| Token | Where it goes | What it answers |
|---|---|---|
| `waitlist` | The launch email | How many of the people who asked actually installed |
| `site` | Every App Store button on plantadvocate.ai | Whether the website sends anyone |
| `outreach` | Any podcast, editor, AHS or Reddit link, grouped | Whether talking to people sends anyone |
| `ph` | The optional Product Hunt post | Whether the maker day cleared the floor |
| `writeup` | Links from the lily of the valley piece | Whether the write-up sends anyone |

On L itself only the site's plain link goes out. The Smart App Banner carries only `app-id=6792203800`, because the syntax for tokens in a banner isn't confirmed. Whether a custom product page's URL can also carry a token is unconfirmed too, so use the custom page's plain URL ([aso.md](research/aso.md)).

For candour, add one clause to the privacy page's website paragraph in the launch-day site edit. It could say: "Links from this site to the App Store carry a campaign label, so Apple can tell us in aggregate how many downloads came from the site." Put it in the same edit as the early-access clause, with one new effective date and "What changed" line, as `site/README-SITE.md` requires. Update the `Effective Date: October 20, 2026` check line in `site/README-SITE.md` (and the copy in the handoff's step 3 block) in the same change, or the check will fail.

If a public page beyond the site's current 13 goes up, such as the lily of the valley write-up or a corrections page, verify plantadvocate.ai in Google Search Console as a Domain property, by DNS. That adds nothing to the pages and leaves the no-tracking sentence true.

Start a public corrections log from the first confirmed correction. It can be a plain page on the site listing the date, the species, the field, the old value, the new value and the source. It costs almost nothing, a competitor that doesn't cite sources can't copy it, and it turns a wrong fact, the biggest risk for an app that names its sources, into evidence that the method works.

### The weekly read and the checkpoints

The weekly read takes about 15 minutes, on a Monday (my estimate). In App Analytics, look at unique impressions, conversion against the peer group's median, first-time downloads, and downloads by source and by campaign. In Ratings and Reviews, look at the US count and average, and reply to anything new. Once it qualifies, look at the pets page. Keep a one-line private note of each number and a tally of support mail by theme.

| By | What to look at | What it decides |
|---|---|---|
| L+14 | Crash rate against the peer benchmark, support themes, whether sign-in and growing areas work for real people | Whether a December build is worth it, and whether it is fixes first or the prompt first |
| 31 January | Ratings count and average; downloads from December into January | Whether the winter built a base (below) |
| End of February | The pets page against the default page, if each passed 5 first-time downloads; conversion and ratings against the Apple Ads conditions | A second custom page; whether to run the ads test |
| End of April | App Store Search impressions against January | Whether the keyword set reaches people |
| 30 June | The season: ratings, conversion, sources, which tokens showed anything | What fall looks like |

The 31 January check is the one that can change the winter. If ratings are near zero while downloads are in the hundreds, look at the ask first. If a December build shipped, check the prompt's condition: either it isn't firing or people aren't reaching a third day of checks. If no build shipped, the waitlist line and review replies are all there is, and the scene build's prompt is the fix. If downloads themselves are only a few dozen, the winter didn't build a base. Then pull the optional outreach earlier, the podcast notes and the AHS proposal, and run the Apple Ads credit in February instead of March, even before the ratings condition is met, treating it purely as keyword research.

These thresholds are mine, and they are where the numbers would change what happens next. If conversion sits below the peer group's median for four straight weeks, change the screenshots or the promotional text before spending anything or pushing anywhere. If the US average is below 4.0 after the first 20 ratings, stop every push, read the reviews, and fix what they say in the next version. If App Store Search impressions in April are no higher than in January, the keyword set isn't reaching people, so revise it in the next version and use the Apple Ads data to choose. If a campaign token never clears five, treat that channel as having produced nothing.

## Timeline, 2026-10-24 to June 2027

L is the day Allison releases after approval. Dates hang on the handoff's steps. Allison's time is my estimate of the go-to-market work only. It sits on top of the handoff's own steps and of the engineering the builds need anyway, which Claude sessions can write; the hours count Allison's reading, builds, phone checks and sends.

| Phase | Dates | Ship step it hangs on | Store and launch work | Allison's time |
|---|---|---|---|---|
| Pre-submission | Now to Submit, probably early to mid-November (my guess) | Decisions, the EAS build, merging PR #22, the Fly deploy, the site deploy, App Store Connect, TestFlight | Export the waitlist before step 3; file the App Launch nomination; read the 33 rewritten care notes and confirm production's rows; read the five site fixes that ride with step 3; in step 4, paste the new subtitle and keywords, upload screenshots in the new order, set US-only and manual release; check the encoding and °F fixes are in the build and in production's rows; start on a postal address | About 5 to 6 hours in all |
| Review | Submit to approval; Apple reviews at least half of submissions in under 24 hours and 90% in under 48; allow a week for a rejection round ([aso.md](research/aso.md)) | Step 6 | Watch the inbox with `docs/app-store/review-replies.md` ready; prepare the launch-day site edit, the waitlist email and the mailing route | About 4 hours, plus checking email |
| Launch day L | One day | The manual release | Release; wait for the product page to load, which can take up to 24 hours; install from the store on a clean phone and check sign-in, a growing area, the Almanac and a hazard note; deploy the site edit (badge, banner, credit line, both privacy clauses, the check line); send nothing in bulk | About 3 hours |
| First 30 days | L+1 to L+30 | None | Campaign links on L+1 or L+2; the waitlist email; replies to early-access emailers; reply to every review; the pets custom product page once its gates are met, with the holiday line; the L+14 check; optionally r/iosapps and Product Hunt; the weekly read | 2 to 3 hours a week, plus about 6 hours if Product Hunt happens |
| Optional December build | Submit by Friday 11 December | L by about 15 November and two clean weeks | The prompt, the Settings row and fixes, on the Xcode 26.6 image | About 4 to 6 hours of builds and phone checks |
| Winter | Mid-December to the end of February | 1.1.4 (or 1.1.5) | Hands off from about 20 December to 3 January; the feeding-rest line through January; the optional AHS proposal; the spring nomination by 15 January if there is something new; the 31 January check; the three hazard-sentence changes shipped by the end of February; the scene-adopted build in January (scene life cycle, Xcode 27 image, prompt, Settings row, Report a fact), submitted by about 1 February, approved by the end of March at the latest; the repot line in February; the Apple Ads decision at the end of February | About 1 hour a week, plus about a day for the build's phone checks |
| Spring push | 1 March to 31 May | The scene-adopted build live | The spring promotional lines; the Apple Ads test from mid-March to early April if the conditions hold; the Poison Prevention Week line on the pets page; a second custom page for beds only if the pets page qualified; optionally one note each to two or three podcasts; the optional lily of the valley write-up and Hacker News submission in April | 1.5 to 2 hours a week, plus about 2 hours to set up the ads test and 3 to 4 hours for the write-up |
| Early summer | June | None | The pollinator line for Pollinator Week; read the season; decide what fall looks like | 2 to 3 hours in all |

That comes to roughly 70 hours across eight months, about 2 hours a week on average, more if the December build or Product Hunt happens (my estimate). The heaviest weeks are around Submit and L.

If Allison has less time than that, keep six things: step zero, the care-notes fix, the nomination, the waitlist email, the review replies and the prompt in the required build. Those are the plan. If March and April turn out to have no spare hours, drop to a store-only spring: the promotional text, the nomination and the default page, with the replies, at an hour or two a week. In the one no-marketing launch with published numbers, 90.6% of downloads came from search ([launch-playbook.md](research/launch-playbook.md)), so a store-only spring is smaller, not empty. Choose it at the end of February if the hours can't be promised, so the winter work isn't aimed at a push that won't happen.

### The promotional text calendar

The promotional text rotates on facts the app already states. Each line is under Apple's 170-character limit and needs no review ([aso.md](research/aso.md)). Spring lines describe what the app checks. They never mention frost, hardiness zones or planting dates, because the app answers none of those and saying so plainly is cheaper than a one-star review from someone who wanted a planner.

| From | Page | Text | Characters |
|---|---|---|---|
| L | Default | Describe each place you grow, then see what suits it, what doesn't, and why. More than 990 species, with care facts cited to the sources that published them. | 157 |
| Late November to the end of January | Default | Feeding reminders rest from November to February. Describe each windowsill, see what suits it and what doesn't, and read the pet and people hazards that sources record. | 168 |
| Its approval to the end of December | Pets | Bringing home a poinsettia, holly or mistletoe? Its page says what its sources record about harm to people and pets, and says so plainly where there is no record. | 162 |
| January to mid-March | Pets | Before a plant comes home, look it up. If a source records it as harmful to people or pets, its page says so. A missing record is never treated as safe. | 152 |
| February | Default | February is repot-check month. Look at a plant's roots, then tap Repotted, Top-dressed or All fine. Each growing area shows what suits it and what doesn't, and why. | 164 |
| March to mid-April | Default | Planting this spring? Describe the bed once, then check each new plant against it before it goes in: sun, soil, space and headroom, with the reason and the source. | 163 |
| Poison Prevention Week, probably 21 to 27 March | Pets | Where a source records harm to people or pets, the species page says so. Where there is no record, it says that too. A missing record is never treated as safe. | 159 |
| Mid-April to May | Default | Looking for something for a bare bed? Each growing area puts forward candidates: species with nothing on record against the spot and at least 1 thing confirmed for it. | 167 |
| June, around Pollinator Week (21 to 27 June) | Default | Give a bed the goal Feeds pollinators, and its fit check asks of each plant whether a source records it as feeding them. Where no source says, the app tells you so. | 164 |

The feeding and repot lines are [aso.md](research/aso.md)'s drafts. The feeding line and the mid-April line are worded as [launch-kit/listing-proposals.md](launch-kit/listing-proposals.md) reworded them: the feeding line claims only the hazards sources record, and the mid-April line starts from a bare bed and gives the candidate rule in full. The feeding months come from the app's reminder plan ([product-truth.md](product-truth.md), section 1). The March line names real fit-engine axes, and the pollinator line describes what the fit engine does with that goal (`garden-gnome/app/services/fit.py`, the pollinators branch of the goal axis). The holiday line goes up only once the pets page's gates are met. The Poison Prevention Week line waits for the three hazard-sentence changes. If there is no pets page, it can sit on the default page for that week. The 2027 date of Poison Prevention Week is uncertain; the 21 to 27 March reading is [channels.md](research/channels.md)'s, and it should be checked in February. Pollinator Week's dates come from Pollinator Partnership ([channels.md](research/channels.md)).

## Budget

At $0 the whole plan runs. The nominations, custom product pages, campaign links, App Analytics, promotional text, review replies, the write-up and the ratings prompt cost nothing but time. Three costs sit outside the marketing budget, and Allison should know them. The developer membership already exists. Keeping the Fly machine awake through review bills it all day instead of only while it answers (handoff, decision 1). And a postal address for the waitlist email costs whatever a USPS box or a registered private mailbox costs locally, which the research didn't price ([launch-playbook.md](research/launch-playbook.md)). If no address is available, the waitlist email doesn't go.

| Item | Cost | When | Condition (my thresholds) | What it buys |
|---|---|---|---|---|
| Postal address | Local USPS box or private mailbox price, not researched | Before L | Required for any commercial email | The waitlist email, and any note to a podcast or editor |
| Mailing service | $0 on Buttondown (to 100) or MailerLite (to 250), checked 2026-10-24 | L+1 or L+2 | Only if the list is more than a few dozen | Unsubscribe handling, footer, removals |
| Apple Ads Advanced, three or four exact-match keywords from the keyword field, national, a daily cap | The $100 credit Apple offers eligible developers who sign up, whose terms weren't read, plus at most $100 of Allison's money | Mid-March to early April, about three weeks (February if the 31 January check says so) | At least 10 US ratings averaging 4.0 or more, and conversion at or above the peer group's median | At AppTweak's 2025 Lifestyle median of $2.62 an install, about 38 installs per $100, probably fewer for a young app; the popularity scores and search terms nothing else gives ([aso.md](research/aso.md)) |

Use Advanced, not Basic, because Basic shows only that installs happened, while Advanced shows keywords and search terms. If Advanced shows the 1-to-5 popularity score before a campaign spends anything, which I couldn't confirm, a $0 look in January is the cheapest keyword research there is, and it should come before the next build's keywords are set. Stop the test early if the cost per install runs past $5 after the first week (my threshold). Apple doesn't say whether paid installs help organic ranking, so the plan assumes they don't ([aso.md](research/aso.md)).

Spending I would not do: GardenComm's professional membership ($165), National Garden Bureau membership ($100 to $5,750 a year), Wild Ones sponsorship (from $5,000), and BetaList ([channels.md](research/channels.md), [launch-playbook.md](research/launch-playbook.md)). None reaches people searching the store. No paid social or influencer deals either. A pixel would break the site's privacy promise, and an influencer deal needs FTC disclosure and a program to monitor it ([launch-playbook.md](research/launch-playbook.md)).

## Risks, and what would change course

### App Review

[review-risk.md](research/review-risk.md) puts the chance of at least one rejection of 1.1.3 at roughly one in three, a judgement from thin evidence. Most of the risk is in technical and metadata items rather than the sign-in wall. The components are about 10 percent for a reviewer's path breaking if the checks are done, about 8 percent for the login before the Almanac under 5.1.1(v), about 7 percent for incomplete notes, about 5 percent for having no demo account, and about 3 percent for hazard notes read as health content. The one near-certain failure is submitting before production serves the 1.1.3 backend; production still answered version 0.2.0 with no `/growing-areas` routes when last checked ([product-truth.md](product-truth.md), section 6). The review notes, rewritten on 24 October, ask for a first sign-in rehearsal with an Apple ID that has never used the app, and for a check that Google sign-in admits an account that isn't a listed tester (`docs/app-store/review-notes.md`). The iOS 27 launch crash doesn't touch 1.1.3 as long as it is built on EAS with the pinned Xcode 26.6 image and no locally built binary is uploaded (`docs/2026-10-24-ios27-scene-lifecycle.md`).

For this plan, the consequences are these. The nomination's range starts weeks after the expected release and can be edited, so a rejection round costs nothing there. Nothing outward happens before L, so a rejection breaks no public promise. Marketing must never mention photo check-ups or symptom reading, and the server must never switch them on after approval without a stated update, because guideline 2.5.19 is about exactly that. If App Review rejects under 5.1.1(v), the signed-out Almanac door becomes the next build's first job. That is an estimated half day of backend work and one to three days in the app ([review-risk.md](research/review-risk.md)). It would still have to fit the end-of-March deadline, and it must not crowd out the prompt. The step zero metadata adds little review risk; the subtitle is the only piece [aso.md](research/aso.md) flags, under 2.3.7.

### Accuracy and hazards

The worst outcome for an app whose pitch is that it names its sources is a wrong or overstated hazard statement in front of someone who acted on it. The 33 care notes are the live example. Every hazard-led line in this plan is gated, as set out above: on the care-notes fix, on reading each named plant's page against its source, on the table clauses being cited or labelled, and on the 47 Missouri Botanical Garden-only values being re-checked where a plant leans on one. If anyone reports a wrong hazard statement, pause every hazard-led line and the pets page. Fix it in the catalog and in production, re-check other values that rest on the same source page, and log the correction before resuming.

### In the store

The first ratings will come from first impressions, and the first impression has rough edges. The server can take 6.7 seconds to answer after idling. Sign-in comes before anything else. A new account opens to an empty My Home and the welcome cards. A searched plant may not be among the 995, and a pet owner's plant often has no pets record. The plan's answers are the review replies, asking only returning users, and fixing what the first weeks show before the prompt asks anyone. It can't remove the risk.

The thin searches may be thin because few people make them. No popularity data was available from outside, so "winnable" means thin competition, not volume. Apple doesn't publish how it weights its ranking factors, whether it combines words across fields, or how it stems ([aso.md](research/aso.md)). App Analytics' floors will hide most small channels. Featuring is Apple's decision alone. And after the April 2027 date every upload has to be built with the iOS 27 SDK, which crashes at launch until the scene work is done, so no update at all can ship without it. Nothing else in that build may delay the scene work.

### Where the angle itself is weak

App Store first is slow to start, because the store rewards what already has momentum, and it puts a great deal of faith in ranking rules Apple doesn't publish. A product page can't carry the app's careful distinctions, between cited and not yet cited, between "no record" and "safe", as well as a conversation can. It leaves the communities where trust in gardening advice is built, Master Gardeners and community gardens, almost untouched this season. It can't fix the sign-in wall, which leaks people after they install. And the winter premise is thin. The only houseplant-specific seasonality found is one 2019 Canadian analysis, and December is the lowest month even in the proxy that includes the Houseplant article ([aso.md](research/aso.md)). So the winter audience may be small, not just steady. If the winter looks like Habit Doom's first month, my guess is that the March rating line will be a few dozen ratings, not a few hundred.

### What would make me change course

If a featuring email arrives, drop everything else and supply the artwork. If Apple features the app in the winter, or a podcast mention lands early, the winter is no longer quiet. Ride it: ship the prompt build, swap the promotional text to the fit-engine line, and pull the spring work forward. If the waitlist export is empty, or its consent can't support a launch note, the seed is gone. Then Product Hunt and the r/iosapps megathread move from optional to worth doing, on L+7 to L+21. If conversion stays below the peer group's median through January even after the screenshots or text have changed, the page isn't the problem; the product's first minute is. The signed-out Almanac door then moves into the scene build for that reason alone. If App Store Search impressions don't rise from January into April, the store isn't going to carry this app by itself, and next season's effort should move to the editorial channels in [channels.md](research/channels.md) and the open web Almanac. If spring reviews ask for planting dates or frost answers, change the copy before the next push, not the product, and say even more plainly what it checks: sun, soil, space and headroom. If the first 20 ratings average under 4.0, stop pushing and fix things. And if the Apple Ads test shows popular search terms the keyword field misses, change the field in the next version. That is the one thing the paid test is for.

## Decisions only Allison can make

| Decision | My recommendation | By when |
|---|---|---|
| The 33 "Pet-safe" and "harmless" care notes | Rewrite all 33 without any safety claim, and update production's existing rows to match | Before Release; ideally before Submit |
| Export the waitlist | This week, whatever date step 3 ends up on | Now |
| App Launch nomination | File it the week of 26 October, with a range starting about two weeks after the expected release (for example 30 November to 31 January); edit it if L moves; don't hold an approved build for it | This week |
| Site copy fixes | Let the five fixes ride with the step 3 deploy | Before step 3 |
| Subtitle and keywords | "Plants that suit each spot" and [aso.md](research/aso.md)'s 97-character field; the fallback field if the name is refused | Before pasting in step 4 |
| Screenshot order | 01, 04, 06, then 02, 03, 05, 07, 08 | Before uploading in step 4 |
| Territories | United States only for 1.1.3; widen once "or your local poison centre" ships | Pricing and Availability, step 4 |
| Release and pre-order | Manual release; no pre-order | Before Submit |
| Postal address | A USPS box or a private mailbox at a commercial mail receiving agency, not a home address | Before L |
| Waitlist email | One email on L+1 or L+2 with the `waitlist` token, once the form wording and an address are in hand; individual sends for a short list, otherwise Buttondown or MailerLite with tracking off | L+1 or L+2 |
| Privacy policy clauses | The early-access clause and the campaign-label clause, with one new effective date and "What changed" line, and the check line updated | Launch-day site edit |
| A December build | Only if L comes by about 15 November and the first two weeks are clean; prompt, Settings row and fixes, submitted by 11 December | L+14 |
| Scope of the scene-adopted build | Scene life cycle, Xcode 27 image, the ratings prompt and Settings row, a Report a fact link (the not-advice line went into 1.1.3); the signed-out Almanac door only if App Review asks or conversion says the first minute is the problem | Build in January, submit by about 1 February, approved by the end of March |
| Prompt trigger | The third distinct day of completed checks; never near a hazard sentence or a Needs addressing finding; once per version; at least 60 days apart | With that build |
| Hazard sentences | "Or your local poison centre", the pet verdict's source named in the sentence, and the table clauses cited or labelled, as backend changes | By the end of February |
| Pets custom product page | Yes, once the care notes are fixed and the holiday plants' and Pothos's pages have been read against their sources | After L |
| Review replies | Reply to every written review within 2 business days | From L |
| Spring nomination | File by 15 January only if a build or the catalog brings something new | 15 January |
| Lily of the valley write-up | Optional; proposal to The American Gardener first, then the site and Hacker News in April if declined | January, then April |
| Product Hunt | Optional, once, feedback only, no rating ask | Scheduled by L+7 if at all |
| Show HN | No for the app | — |
| r/iosapps | Only if Allison already uses Reddit or wants to; one megathread post | First 30 days |
| Organizations | Not a planned channel; if any, information only, no follow-up, never a cited institution's program | — |
| Apple Ads | $0 until mid-March; then the credit plus at most $100 on Advanced, if the ratings and conversion conditions hold | End of February |
| Spring hours | Reserve about 2 hours a week for March to May, or choose the store-only spring | End of February |
| Open web Almanac | Defer to after spring, as a smaller project | Summer |

## Pages read for this file

Beyond the research files and the repository, these public pages were read on 2026-10-24 while preparing this file: Apple's [App Analytics](https://developer.apple.com/app-store/app-analytics/), [ratings, reviews and responses](https://developer.apple.com/app-store/ratings-and-reviews/), [getting featured](https://developer.apple.com/app-store/getting-featured/) and [App Privacy details](https://developer.apple.com/app-store/app-privacy-details/) pages; the [Hacker News guidelines](https://news.ycombinator.com/newsguidelines.html); and the [Buttondown](https://buttondown.com/pricing) and [MailerLite](https://www.mailerlite.com/pricing) pricing pages. The care-notes count, the `is_houseplant` split, the `toxicity.py` table sources, the seed's skip rule, the site lines quoted, the absence of a "medical or veterinary" line in `mobile/src`, and the Pothos research record were checked in the repository on 2026-10-24. These are internal figures, not for public copy.
