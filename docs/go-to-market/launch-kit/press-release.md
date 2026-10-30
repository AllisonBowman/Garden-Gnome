# Launch press release, for day L

Written 2026-10-24 against the ship tip `3f6d7da`, for the day Allison releases PlantAdvocate 1.1.3 on the App Store, called L here. It is a draft. Nothing has been sent, posted or published, and whether it goes anywhere is Allison's decision. Every claim in it was checked against [product-truth.md](../product-truth.md) and [listing.md](../../app-store/listing.md), and the table at the end says where each one comes from. Words in square brackets are placeholders to fill in or remove. The facts a journalist would want to check are in [fact-sheet.md](fact-sheet.md), which the launch-day site lane turns into `press.html`.

## What it is for

The strategy expects little from press for a plant app. A 2023 indie launch pitched about 20 journalists and got no coverage, and Muck Rack's surveys say pitches are deleted mostly for irrelevance and a promotional tone ([launch-playbook.md](../research/launch-playbook.md)). So the release has two modest jobs. On L it is the text of the press page, for anyone who comes looking. Later, if Allison sends the optional notes to podcasts and editors that the strategy places in March and April, it is the page those notes link to. It is not something to paste into an email: 69% of the journalists in Muck Rack's 2025 survey, as PR News reported it, prefer pitches under 200 words.

Treat any note that does go out as commercial email under CAN-SPAM, which makes no exception for business email ([launch-playbook.md](../research/launch-playbook.md), emailing the waitlist and organizations). Each one needs a From line and reply address that say it is from Allison Bowman at PlantAdvocate, and a subject that says plainly what it is, such as "PlantAdvocate, a free garden care app for iPhone", with no "Re:" and nothing that implies an earlier conversation. In the note itself it needs one line saying it is a note promoting PlantAdvocate, the postal address the strategy asks Allison to set up (a USPS box or a registered private mailbox, so that no home address goes out), one line saying how to opt out, such as "Reply 'no more' and I won't write again", and the independence line, because the release names three organizations. Honor an opt-out within 10 business days, keep the reply route working for at least 30 days after sending, never pass on the address of anyone who opts out, and keep a do-not-contact list that outlives the campaign. Send each one through the outlet's own contact page, one per outlet, and use the `outreach` campaign link in place of the plain store link. Campaign links can only be made once the app has been live with downloads for about 24 hours ([strategy.md](../strategy.md), measurement section).

## Before it goes anywhere

Eight things have to be true first.

The App Store page has to load at `https://apps.apple.com/app/id6792203800`. Apple says a release can take up to 24 hours to appear. Put the link in only once it answers.

The 33 curated care notes that call a plant "Pet-safe" or "harmless" have to be rewritten, and production's rows updated to match. The release says a missing record is never treated as safe, and until that fix is live, 33 species pages say otherwise. The strategy already makes this a condition of pressing Release.

The °F and encoding fixes have to be in the 1.1.3 build and in production's rows ([strategy.md](../strategy.md), the "Pet-safe" care notes section). Both are in the working tree, not on `3f6d7da`, and the deploy has to correct the rows production already holds, because seeding never rewrites a row. Screenshot 05 in the fact sheet reads "60–85°F" only because of the first fix, so without both, the press screenshots show an app that doesn't exist.

`site/` has to be deployed with the copy fixes from strategy.md ("The site, riding along with step 3") in it, and the step 3 check block has to print `ok` on every line. That block tests none of those fixes, so run these lines too. Each must print `ok`:

```bash
check() { n=$(curl -sL "$1" | grep -c -- "$2"); if [ "$3" = present ]; then [ "$n" -gt 0 ]; else [ "$n" = 0 ]; fi && echo "ok   $1  $2" || echo "FAIL $1  $2 (on $n lines)"; }
check https://plantadvocate.ai/index.html 'have not reviewed or endorsed it' present
check https://plantadvocate.ai/faq.html 'have not reviewed or endorsed it' present
check https://plantadvocate.ai/resources.html 'have not reviewed or endorsed it' present
check https://plantadvocate.ai/about.html 'have not reviewed or endorsed it' present
check https://plantadvocate.ai/about.html 'vetted' absent
check https://plantadvocate.ai/about.html 'traced back to a specific fact' absent
check https://plantadvocate.ai/recommendations.html 'safe bet' absent
```

A sentence wrapped across two lines of HTML prints FAIL, so read the page before treating a FAIL as missing copy. The fifth fix, about "NO GUESSWORK", is Allison's judgment and no line tests it. The release sends people to plantadvocate.ai. It names three of the organizations those pages name and says a missing record is never treated as safe, but `site/` at the tip carries the independence line on no page and still calls Pothos "a safe bet for most rooms". Until `site/` is deployed, the live homepage also still says "EVERY FACT CITED".

App Store Connect's availability for Apple silicon Macs and Apple Vision Pro has to be checked on the Pricing and Availability page in step 4 of the handoff. If either is left on, change "PlantAdvocate is for iPhone only" to say so, as [fact-sheet.md](fact-sheet.md) describes.

The availability line has to name the territories actually set in App Store Connect. The strategy recommends the United States only for 1.1.3, and the placeholder assumes that.

Allison has to rewrite the quote in their own words, or cut it. The draft below is only a starting point, and it is marked so it can't go out by accident.

The dateline needs a decision. Nothing about where Allison lives is published beyond "based in the United States" (`site/privacy.html`), and product-truth.md says not to add a city. A release published online can carry just the date, so leave the city out unless Allison chooses to publish one.

The release says "PlantAdvocate" throughout, so it doesn't matter whether App Store Connect accepts the longer store name.

## Headline options

Each is plain and checkable, with no hype word. The first is the conventional news line, the second leads with what the app does, and the third leads with its honesty about unknowns.

```text
PlantAdvocate, a free garden care app that names its sources, is now available on the App Store
```

```text
New free app for iPhone shows what suits each spot you grow, and names its sources
```

```text
PlantAdvocate for iPhone names its sources, and says plainly where it has no record
```

The optional subhead works under any of them:

```text
Free, with no ads and no in-app purchases. More than 990 species, with care facts cited to the sources that published them.
```

## The release

About 770 words from the dateline to the end of the availability line, or 680 without the draft quote, which suits a page but not an email. Apple's naming rules are followed: "PlantAdvocate for iPhone", "available on the App Store", "iPhone models with Apple Intelligence", and no "iOS" ([launch-playbook.md](../research/launch-playbook.md)).

```text
[HEADLINE: one of the three options above]

[SUBHEAD, optional] Free, with no ads and no in-app purchases. More than 990 species, with care facts cited to the sources that published them.

[DATELINE, optional: CITY, STATE,] [MONTH DAY, YEAR OF L] — PlantAdvocate, a free app for iPhone that helps you look after the places you grow, is now available on the App Store. Advice about plants is easy to find and hard to check. PlantAdvocate is built to show where its care facts come from, and to say plainly where there is no record. You describe each place you keep plants, such as a windowsill, a shelf, a raised bed or a bed along a fence, and it shows what suits that spot, what doesn't, and why. What needs addressing comes with the reason and the source. It has no ads and no in-app purchases.

Each growing area records what plants sit in, how much room there is, whether it is indoors or out, how much sun it gets, and what it is for: something to eat, low upkeep, or food for pollinators. PlantAdvocate compares each plant with its spot one thing at a time: indoors or out, sun, soil, space and headroom, upkeep and goals. A shade fern in full sun is flagged. So is a climber that will outgrow a 7 ft fence. Each area also puts forward good candidates, which are species with nothing on record against that spot and at least 1 thing confirmed for it. The same check runs before a new plant is saved. A measurement left blank counts as unknown, and nothing is recommended on a guess.

The Species Almanac covers more than 990 species: houseplants, herbs, vegetables, perennials, shrubs, trees, bulbs and climbers. Care facts come from the organizations that publish them, such as NC State Extension, the Royal Horticultural Society and Missouri Botanical Garden, and each researched species page names its sources. A fact borrowed from a plant's genus is labelled as borrowed, and anything not yet cited says so. The check schedules that reminders follow were written by PlantAdvocate for 129 common plants and are not cited.

Where a source records a plant as harmful to people or pets, its page says so in plain sentences, with the source's severity rating for people where it gives one. A plant is shown as edible only with the conditions its source gives. Where there is no record, PlantAdvocate says that too, and a missing record is never treated as safe. These notes are based on what the sources publish. They are not medical or veterinary advice.

Reminders are checks, not chores. When a plant's watering check comes due, PlantAdvocate asks you to feel the soil, then tap Watered or Still damp, and either keeps your streak. Reminders follow a species' care window wherever the catalog holds a schedule for it, so a plant without one gets none. Nothing is called overdue while it is still inside its care window. Plants can be added by hand, or by typing or saying what is planted, such as "12 tomatoes along the south fence, a rosemary by the gate", and confirming each one.

PlantAdvocate has no ads, no tracking, and no analytics or crash-reporting software. The one thing it counts is an optional community census of what people grow and how it fares, which is off unless you turn it on, and which is what its App Store privacy label lists under Analytics. You sign in with Apple or Google, so there is no password to remember, and you can delete your account from Settings.

PlantAdvocate is for iPhone only. On iPhone models with Apple Intelligence, Add plant can also suggest likely matches from a photo. The photo is read on the phone and never uploaded, and you confirm the species before you save. On other iPhone models, you find a plant by searching for it. PlantAdvocate doesn't diagnose a sick plant. Species pages show the temperatures a source gives, including where cold damage begins, but the app doesn't judge whether a plant will survive the winter where you live.

[DRAFT QUOTE, FOR ALLISON TO REWRITE IN THEIR OWN WORDS OR CUT. DO NOT PUBLISH AS WRITTEN.]
"When I took on my first garden, the advice I found was confident and contradictory, and very little of it was about my plants or the spot they were in," said Allison Bowman, who builds PlantAdvocate. "I wanted something that says what suits each spot, shows where that comes from, and says plainly when there's no record. If a fact in it looks wrong, I want to hear about it."
[END OF DRAFT QUOTE]

PlantAdvocate for iPhone is available now on the App Store, free, in [the United States]: [https://apps.apple.com/app/id6792203800]. Signing in needs an Apple or Google account. More is at https://plantadvocate.ai.

About PlantAdvocate
PlantAdvocate is a free app for iPhone that helps people look after the places they grow, from a windowsill to a back bed. It shows what suits each spot and what doesn't, from more than 990 species with care facts cited to the sources that published them, and where there is no record, it says so. It has no ads, no tracking and no in-app purchases. PlantAdvocate is independent. The organizations it cites have not reviewed or endorsed it. PlantAdvocate is built by Allison Bowman and is an Ocean Dweller Media project. https://plantadvocate.ai

Press contact
Allison Bowman
support@plantadvocate.ai
[Press page URL, once press.html is live]

iPhone is a trademark of Apple Inc., registered in the U.S. and other countries and regions. App Store is a service mark of Apple Inc., registered in the U.S. and other countries and regions. Apple Intelligence is a trademark of Apple Inc.

###
```

The first sentence of the quote paraphrases the about page, which tells of a first home with a garden and "a wall of contradictory advice", little of it "specific to the plants I was actually trying to grow or the conditions they were living in" (`site/about.html`). The second and third sentences are the writer's wording of what the app does and of the support page's invitation to report problems, which go "straight to the person who builds PlantAdvocate". They are not anything Allison has said, and they are the parts Allison most needs to rewrite or cut. If Allison rewrites it, the same limits apply. It shouldn't add a city, a profession, a team or a backstory, promise a feature, use the word "safe" about any plant, or describe the app as AI.

The contact address is the one `site/contact.html` gives, which promises a reply "usually within 2 business days". For press.html, the site lane can link it with a subject line, such as `mailto:support@plantadvocate.ai?subject=Press`, the way the contact page does for bug reports.

## Where each claim comes from

Paths are relative to the repository root.

| Claim in the release | Where it is true |
|---|---|
| Free, no ads, no in-app purchases | `docs/app-store/listing.md`, FREE, WITH NO ADS; no purchase library in `mobile/package.json` |
| Advice easy to find and hard to check; built to show where its care facts come from, and to say where there is no record | `site/about.html` ("a wall of contradictory advice"); `mobile/src/care/facts.ts`, the Sources card, the "genus-inferred" pill and "From the catalog — not yet cited"; `listing.md`, opening paragraph ("Where there is no record, PlantAdvocate says so") |
| What suits a spot, what doesn't, and why; what needs addressing comes with the reason and the source | `listing.md`, SEE WHAT SUITS IT; `garden-gnome/app/services/fit.py`, where `Finding.authorities` is empty for an unknown or a genus-borrowed value, which is why the source is claimed only for what needs addressing |
| Surfaces, room, indoors or out, sun, the three goals | `listing.md`, DESCRIBE WHERE YOU GROW; `mobile/src/growingAreas/realEstate.ts` |
| The axes compared | product-truth.md section 1; `fit.py:76-83` |
| Shade fern, 7 ft fence, candidates, check before saving, blank means unknown | `listing.md`, SEE WHAT SUITS IT and DESCRIBE WHERE YOU GROW |
| More than 990 species, the plant types, borrowed and not-yet-cited labels, 129 uncited schedules | `listing.md`, MORE THAN 990 SPECIES, WITH SOURCES; product-truth.md section 3 |
| The three organizations, and researched pages naming sources | `listing.md`, opening paragraph; `mobile/src/components/CareFacts.tsx`, `CareSourceRows`, which renders nothing on a page with no sources, as on production's older uncited rows |
| Hazards, edibility, missing record never safe, not medical or veterinary advice | `listing.md`, opening paragraph and HAZARDS, STATED PLAINLY. "Based on" replaces the listing's "repeat" because some effect clauses come from code tables, not a cited page (`garden-gnome/app/services/toxicity.py`, `AROID_TOXICITY` and `SPECIES_SPECIFIC_RISK`; [strategy.md](../strategy.md), the hazard sentences) |
| A watering check's Watered or Still damp, care window, reminders only where a schedule exists | `listing.md`, CHECKS, NOT CHORES; product-truth.md section 1 (checks) and section 2 ("Reminders for every plant" row); `mobile/src/care/CareTodos.tsx` |
| Typing or saying what is planted, the tomato example | `listing.md`, WALK THE GARDEN |
| No ads, no tracking, no analytics or crash-reporting software | `site/privacy.html`, the short version |
| Census off unless turned on; Analytics on the label | `docs/app-store/app-privacy.md`, Collected and the paragraph under it; `listing.md`, FREE, WITH NO ADS |
| Sign in with Apple or Google, delete account from Settings | `listing.md`, FREE, WITH NO ADS |
| iPhone only, photo matching only on Apple Intelligence models, photo never uploaded | product-truth.md sections 1 and 2; `listing.md`, WALK THE GARDEN |
| Doesn't diagnose; temperatures and cold damage shown, cold not judged | product-truth.md section 2 ("AI plant doctor" and hardiness rows); `fit.py:41-49`; `mobile/src/care/facts.ts`, the Temperature row ("cold damage below N°F") and the Cold row, which none of the 999 records in `garden-gnome/app/data/verified/` fills; `docs/adr/0006-usda-plants-publishes-a-minimum-temperature.md` |
| Built by Allison Bowman; Ocean Dweller Media | `site/privacy.html` (sole proprietor); `site/index.html` footer |
| Independence line | `listing.md`, last line of the description |
| Apple credit line | Apple's [App Store marketing guidelines](https://developer.apple.com/app-store/marketing/guidelines/), credit lines, whose own footer reads "App Store is a service mark of Apple Inc." (read 2026-10-24); [launch-playbook.md](../research/launch-playbook.md), Apple's names in marketing copy |

Two of the documents this release leans on need a correction, and Allison should hear about both. First, `listing.md:101`, and product-truth.md after it, say each species page shows "size and cold hardiness". No species page can show a hardiness figure today. The Cold row reads `outdoor_temp_min_f`, and none of the 999 verified records holds it (`fit.py:41-49`, ADR 0006). What pages show is where cold damage begins, on the Temperature row, for 75 of those records, and ADR 0006 says that is not a survival floor. Change the listing's sentence before it is pasted into App Store Connect, for instance to "facts such as light, water, soil, temperature and size". Second, launch-playbook.md and aso.md give Apple's credit line with App Store as a trademark; Apple's own page calls it a service mark, as the release's credit line now does. Both were corrected on 2026-10-30: listing.md and product-truth.md now say "temperature and size", and both research files note the service mark.
