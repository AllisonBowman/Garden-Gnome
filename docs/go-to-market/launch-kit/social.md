# Social posts and the launch calendar

Written 2026-10-24 against the ship tip `3f6d7da`. It has three parts: launch week day by day, a six-week calendar after launch day L, and a winter and spring content plan to June 2027. Each covers the public surfaces [strategy.md](../strategy.md) picks, plus a set of optional short posts. Nothing here was posted, scheduled or signed up for. Every product claim was checked against [product-truth.md](../product-truth.md), and the sheet wins where they differ. Every plant fact was taken from a record in `garden-gnome/app/data/verified/`, and each post names its record next to the fact. The community venues (Product Hunt, r/iosapps, Hacker News) have their drafts in [community-posts.md](community-posts.md). This file only times them.

## Which platforms

The strategy picks no social media platform. Its channels are the App Store page and its promotional text, a pets custom product page, plantadvocate.ai, one waitlist email, review replies, and the optional community venues. [channels.md](../research/channels.md) did not research TikTok, Instagram, Facebook groups, Discord or YouTube, "because their public pages need a login or state no rules I could read". So this file doesn't create a social presence, and the plan doesn't depend on one. In the one no-marketing launch with published numbers, 90.6% of downloads came from search ([launch-playbook.md](../research/launch-playbook.md)).

The calendars below are built on the surfaces the strategy does pick. The posts are an optional extra, for one personal account Allison already uses, if they want to. They are short and plain, so they suit any text-and-image platform. Making a brand account would be a new channel, and it is Allison's call, not this plan's.

## Rules for every post

Each post discloses, in its own text, that Allison makes the app ("I make PlantAdvocate", "which I make", "the app I make"). It follows Apple's naming: "PlantAdvocate for iPhone", "available on the App Store", "iPhone models with Apple Intelligence". Until App Store Connect has campaign links, which needs about 24 hours of downloads, a post links the plain store URL `https://apps.apple.com/app/id6792203800`. After that, posts use the campaign link with the `outreach` token. That groups personal posts with the other people-to-people links, so no sixth token is needed (my choice). With winter volumes it will probably show nothing below Apple's floor of five, and that is a result too.

Every count below is the post's own text, counted exactly, before the link. Each post is 256 characters or fewer, so it still fits X's 280 once the link is added, since X counts any link as 23 characters, plus the space before it. On platforms with a 500-character limit they fit with room to spare. The platform's own counter has the last word.

P1, the one post that says the app is available, says "in the US", following the strategy's US-only recommendation. Drop those words if App Store Connect is set to more territories.

A plant fact in a post is a paraphrase of what a source the record cites says. The truth sheet forbids quoting a source's prose in marketing, so no post quotes one. The words in quotation marks inside posts are the app's own. The "Fact" line under each post is for Allison, so they can open the record and the source page and check, and it never gets posted. Where a post mentions the app's own check schedules or feeding rest next to a cited source, it says that the app's part isn't cited, so a reader doesn't take the source as the schedule's authority. An organization is named only as the source of a fact, as the truth sheet allows where the independence line can't fit.

No post asks for a rating, a vote or a share, or quotes any rating, review or download figure. None mentions frost, hardiness zones or planting dates, which the app doesn't answer. None mentions photo check-ups or symptom reading. None calls a plant safe, pet-safe or non-toxic in the app's voice. The pause rule holds here too: if anyone reports a wrong hazard statement, every hazard-led post stops until the fix is in the catalog, in production and in the corrections log.

Visuals use the 17 Pro Max frames in `docs/screenshots/1.1.3/17-pro-max/`. Post each one whole and uncropped, so the reason and source lines stay in view, with no text over it. Use no device frame unless it is Apple's own, unmodified. Each brief gives alt text, which most platforms take.

## Gates

A post goes up only when every gate it lists is met. G0 applies to all of them.

| Gate | What has to be true | Where it comes from |
|---|---|---|
| G0 | The store page answers at the link, the clean-install check on L passed, and the step 3 site is live with every check line `ok` | Strategy, launch day and site sections |
| G1 | The 33 "Pet-safe" and "harmless" care notes are rewritten, and production's rows match | Strategy, "The 'Pet-safe' care notes" |
| G2 | The encoding and °F fixes are in the build and in production's existing rows | Strategy, same section |
| G3 | Allison has read the in-app pages for the plants a post names against their cited sources | Strategy, the pets page's gates |
| G4 | Allison has read Pothos's in-app hazard sentence against NC State's page | Strategy, hazard sentences |
| G5 | The three hazard-sentence changes are shipped: "or your local poison centre", the pet verdict's source named in the sentence, and the code-table clauses cited or labelled. They landed on 2026-10-30, so G5 is met once step 2's deploy is live | Strategy, hazard sentences |
| G6 | The page the post links to exists and is checked: a corrections log with a real entry, or the published write-up | Strategy, measurement and editorial sections |

## Launch week, L to L+7

The dates assume L on Wednesday 18 November 2026, which is only an example inside the strategy's guess of 16 to 20 November. If L moves, shift every row by the same number of days.

| Day | Example date | On the strategy's surfaces | Optional post |
|---|---|---|---|
| L | Wed 18 Nov | Release. Wait for the product page, which can take up to 24 hours. Clean-install check: sign-in, a growing area, the Almanac, a hazard note. Deploy the launch-day site edit (badge, banner, credit line, the campaign-label clause, check line). The early-access clause is already live, from step 3. The promotional text launch line is already live. Send nothing in bulk | None. Only the site's plain link goes out on L |
| L+1 | Thu 19 Nov | Make campaign links as soon as the button appears (`waitlist`, `site`, `outreach` and `ph`; `writeup` waits until the piece exists). Give the site's buttons the `site` link, redeploy and re-run the check block, as [launch-day-runbook.md](../launch-day-runbook.md) sets out, so the campaign-label clause that went up on L describes links the site actually carries. Reply to any written review | None |
| L+2 | Fri 20 Nov | Send the waitlist email with the `waitlist` link, only if the six conditions in [waitlist-email.md](waitlist-email.md) hold, among them a postal address, July form wording that supports a launch note, and the early-access privacy clause live. Otherwise it doesn't go. Start the individual replies to early-access emailers, which wait on the same postal address, each ending with "If you'd rather not hear from PlantAdvocate again, reply and say so." and "PlantAdvocate, [POSTAL ADDRESS]" | P1 |
| L+3 | Sat 21 Nov | Finish the early-access replies (L+1 to L+3) | None |
| L+5 | Mon 23 Nov | First Monday read: impressions, conversion against the peer median, downloads by source, ratings | P2 |
| L+7 | Wed 25 Nov | Replies to reviews within 2 business days. If the week was rough, everything optional moves later | None. Nothing on Thanksgiving, Thu 26 Nov (my judgement) |

### P1. Launch, L+2

```text
PlantAdvocate for iPhone is now available on the App Store in the US. I made it to help you look after the places you grow: describe a windowsill or a bed, and see what suits it, what doesn't, and why, naming the source. Free, no ads, no in-app purchases.
```

Characters: 255, before the link.

Fact: no plant fact. The app claims are the listing's opening paragraph ("helps you look after the places you grow", so the person does the care, not the app) and its FREE, WITH NO ADS paragraph (`docs/app-store/listing.md`). "In the US" is there because a personal account's followers live anywhere.

Gates: G0.

Visual: `01-needs-addressing.png`. The frame shows the demo account's bed with "Home" and "Raleigh, NC", so the alt text says it is a demo garden, and nothing may say or suggest the bed is Allison's. Alt text: "PlantAdvocate's page for a demo garden's back fence bed, listing Chinese Wisteria and Lady Fern under Needs addressing, each with its reason and its source."

### P2. A shade fern in a sunny bed, L+5

```text
I make PlantAdvocate. Put a lady fern in a full-sun bed and it says so: "This spot gets 6+ hours of direct sun; sources record it for part shade, full shade." The Royal Horticultural Society lists lady fern for full or partial shade.
```

Characters: 233, before the link.

Fact: `b50-native-woodland.json`, Lady Fern, `outdoor_sun_exposure` part_shade and full_shade. It is cited to the RHS profile's Position field ([RHS](https://www.rhs.org.uk/plants/1897/athyrium-filix-femina/details)) and to NC State's light tags ([NC State](https://plants.ces.ncsu.edu/plants/athyrium-filix-femina/)). The quoted finding is the app's own sentence from a scratch sync (`listing.md`).

Gates: G0.

Visual: `01-needs-addressing.png`, the frame where Lady Fern's sun misfit names the Royal Horticultural Society. Alt text: "Needs addressing on a demo garden's full-sun bed: Lady Fern, with the reason that the spot gets 6+ hours of direct sun and the source, Royal Horticultural Society."

## Weeks 2 to 6

| Week | Example dates | On the strategy's surfaces | Community venues | Optional posts |
|---|---|---|---|---|
| 2 | Thu 26 Nov to Wed 2 Dec | Switch the default promotional text to the feeding-rest line ("Feeding reminders rest from November to February...", 168). Put up the pets custom product page and its holiday line once its gates are met. The L+14 check on Wed 2 Dec: crash rate, support themes, and whether a December build is worth it | Keep earning r/iosapps karma by taking part in its threads | P3 on Mon 30 Nov |
| 3 | Thu 3 Dec to Wed 9 Dec | Monday read. Decide the December build by about 7 Dec | Product Hunt, if at all, Sat 5 or Sun 6 Dec at 12:01 am Pacific (between L+14 and L+21). No cross-post about it, so nothing reads as a vote ask | P4 on Thu 3 Dec; P5 on Tue 8 Dec |
| 4 | Thu 10 Dec to Wed 16 Dec | A December build, if any, is submitted by Fri 11 Dec | The r/iosapps megathread comment, if the karma is earned and it's still within 30 days of L | P6 on Thu 10 Dec; P7 on Mon 14 Dec |
| 5 | Thu 17 Dec to Wed 23 Dec | Hands off from about 20 Dec. Apple's last holiday notice said reviews may take longer from 20 to 26 December | None | P8 on Thu 17 Dec, then nothing |
| 6 | Thu 24 Dec to Wed 30 Dec | Hands off to 3 Jan. The one thing that continues is replying to written reviews | None | None |

If L lands later, two things don't simply shift. If L+14 falls after Sunday 13 December, Product Hunt moves to Saturday 9 and Sunday 10 January 2027. P5 and P6 are holiday posts, so if they can't go up by about 18 December, hold them for next year rather than posting into January. The strategy's holiday promotional line ends with December too.

### P3. Checks, not chores, week 2

```text
PlantAdvocate, which I make, schedules checks, not chores: when a plant comes due, feel the soil, then tap Watered or Still damp. The check schedules that reminders follow were written by PlantAdvocate for 129 common plants and are not cited.
```

Characters: 242, before the link.

Fact: no plant fact. The claims are the listing's CHECKS, NOT CHORES paragraph and its sentence on the 129 schedules (`listing.md`), which the truth sheet's numbers table says to quote word for word. This is the post that says the reminders reach only 129 species, before a reviewer has to.

Gates: G0.

Visual: `04-checks-not-chores.png`. Alt text: "Checks for today, with checks for Basil and Boston Fern, each with Watered and Still damp buttons, and a note that 2 plants have no check schedule."

### P4. Snake plant in winter, week 3

```text
Snake plant in winter: NC State Extension's page says to water it only every 1 to 2 months. In PlantAdvocate, which I make, its check comes due more often, on the app's own schedule, which isn't cited. So feel the soil first, and tap Still damp if it is.
```

Characters: 254, before the link.

Fact: `b1-foliage-core.json`, Snake Plant, `water_dormant_days_est` 45, the record's own midpoint of NC State's 1-to-2-month winter interval, cited to [NC State](https://plants.ces.ncsu.edu/plants/dracaena-trifasciata/). The app's check schedule for snake plant, in `garden-gnome/app/data/species_catalog.json`, comes due every 14 to 21 days all year. That schedule is PlantAdvocate's own and not cited, so the post says so in as many words, rather than letting NC State's name stand behind it.

Gates: G0.

Visual: `05-cited-care-facts.png`, which is Snake Plant's page, though the name is scrolled out of the frame. Alt text: "Snake Plant's care facts in PlantAdvocate, an uncited temperature row labelled From the catalog, not yet cited, and its sources: Clemson Cooperative Extension, NC State Extension and Royal Horticultural Society."

### P5. Holiday plants, week 3

```text
Bringing home holly or mistletoe? NC State Extension marks both as a problem for cats and dogs. In PlantAdvocate, which I make, each page says what its sources record about harm to people and pets. It isn't veterinary advice; if a pet eats one, call a vet.
```

Characters: 256, before the link.

Fact: NC State's Problems tags, in each record's `toxic_to_pets` citation. English holly: `b121-shrubs.json` ([NC State](https://plants.ces.ncsu.edu/plants/ilex-aquifolium/)). American holly: `b28-holly-and-nuts.json` ([NC State](https://plants.ces.ncsu.edu/plants/ilex-opaca/)). American mistletoe: `b29-mistletoe-and-more.json` ([NC State](https://plants.ces.ncsu.edu/plants/phoradendron-leucarpum/)). Each lists Problem for Cats and Problem for Dogs. The post says only what NC State tags and what the app's page does, and gives no severity. Poinsettia is left out on purpose. NC State tags it the same way (`b20-common-ornamentals.json`, [NC State](https://plants.ces.ncsu.edu/plants/euphorbia-pulcherrima/)), but its record also cites Penn State Extension on a milder stomach upset and notes that UF/IFAS calls it not poisonous, so listing it level with holly and mistletoe would flatten a record whose sources disagree. Give poinsettia its own post, if at all, only after its page has been read at G3.

Gates: G0, G1, G3 for all three plants.

Visual: `06-hazards-stated-plainly.png`, which shows Pothos, not a holiday plant. It illustrates how a hazard sentence reads, and the alt text has to say so. If Allison would rather not pair a holiday post with another plant, post it with no image. Alt text: "How a hazard note reads in PlantAdvocate, shown on Pothos: toxic to cats, dogs and people, NC State Extension's severity rating for people, and the US Poison Control number."

### P6. Christmas cactus, week 4

```text
Christmas cactus in PlantAdvocate, which I make: its page says NC State Extension records no toxicity to pets, and adds that this is not a guarantee of safety. Thanksgiving cactus, often sold under the same name, has its own page. Not veterinary advice.
```

Characters: 253, before the link.

Fact: `b4-tricky-cases.json`, Christmas Cactus (*Schlumbergera* × *buckleyi*), `toxic_to_pets` false. It is cited to [NC State](https://plants.ces.ncsu.edu/plants/schlumbergera-x-buckleyi/), and the record calls it an explicit non-toxicity statement. The app's wording is the cited branch of `describe` in `garden-gnome/app/services/toxicity.py`: "{Source} records no toxicity to pets for {plant}. That is not a guarantee of safety — keep it away from pets that chew plants." The post leads with the app's page, not with a verdict beside the plant's name, because the truth sheet keeps "non-toxic" away from any plant in marketing, and a skimming reader takes the first clause as the answer. The record's name note says many plants sold as Christmas cactus are *S. truncata*, the Thanksgiving cactus, which its sources treat separately. It has its own record, `b90-houseplants.json`, Thanksgiving Cactus, `toxic_to_pets` false, cited to NC State's [*S. truncata* page](https://plants.ces.ncsu.edu/plants/schlumbergera-truncata/), so the post points to that page and says nothing more about it.

Gates: G0, G1, G3 for Christmas cactus and Thanksgiving cactus.

Visual: none. No frame shows a plant with a recorded no-toxicity statement, and the text carries the claim.

### P7. Basil on the windowsill, week 4

```text
I make PlantAdvocate. Narrow its Species Almanac to a kitchen windowsill and basil shows "Confirmed here: indoors or out." The Royal Horticultural Society suggests basil as an indoor annual in full sun. The app says plainly that indoor light isn't checked.
```

Characters: 256, before the link.

Fact: `b7-culinary-herbs.json`, Basil, `is_houseplant` true. Among other sources it is cited to the RHS cultivation line ([RHS](https://www.rhs.org.uk/plants/11649/i-ocimum-basilicum-i/details)), the same page behind its full-sun claim. The quoted line is the app's own, in shot 07. "Confirmed here" covers indoors or out and nothing else. The app doesn't judge indoor light, and shot 07 says so in red under the count ("Indoor light isn't checked: nothing records how bright this spot is"). The post says it too, so the RHS's full sun doesn't read as something the app confirmed for the windowsill.

Gates: G0.

Visual: `07-almanac-narrowed.png`. The picked chip is cut to "✓ Fits Kitchen w", and the note under the count names the windowsill in full. Alt text: "The Species Almanac narrowed to what fits a kitchen windowsill, searched for Basil, showing Basil with Confirmed here: indoors or out. The note under the count says indoor light isn't checked."

### P8. Feeding rests, week 5

```text
PlantAdvocate's feeding reminders rest from November to February (I make the app). NC State Extension's pothos page says to skip feeding during its winter rest. The November-to-February dates are the app's own and aren't cited.
```

Characters: 227, before the link.

Fact: `b1-foliage-core.json`, Pothos. NC State's page corroborates the winter stop ([NC State](https://plants.ces.ncsu.edu/plants/epipremnum-aureum/)). The November-to-February rest is PlantAdvocate's own reminder plan (`mobile/src/notifications/plan.ts:29-31`), not a source fact, and the post says so. Clemson is left out on purpose. The record's `fertilize_active_months` (March to August) and `fertilize_interval_days` 60 come from Clemson's pothos factsheet ([Clemson HGIC 1568](https://hgic.clemson.edu/factsheet/how-to-grow-pothos-indoors-epipremnum-spp-care-cultivars-and-common-problems/)), feeding every other month in spring and summer. The app's feeding checks run March to October, and pothos's own schedule in `species_catalog.json` is every 30 to 60 days, so putting Clemson beside the app's rest would suggest the app follows it, and for pothos it doesn't.

Gates: G0 and G4, because the post sends people to Pothos's page, which leads with its hazard sentence.

Visual: `04-checks-not-chores.png`, since no frame shows feeding. Alt text as P3.

## Winter and spring

The promotional text rotation is the strategy's, in its "promotional text calendar". This plan repeats only the first words of each line so the posts can be lined up against them. The optional posts run at about one or two a month, at about 15 minutes each (my estimate). If Allison chooses the store-only spring at the end of February, the posts stop and the promotional text carries on.

| When | Promotional text (the strategy's lines) | Optional posts | Other dates that touch them |
|---|---|---|---|
| 20 Dec to 3 Jan | Unchanged | None | Hands off. Replies only |
| January | Default: "Feeding reminders rest from November to February..." to the end of January. Pets page: "Before a plant comes home, look it up..." from January to mid-March | W1, mid-January | Product Hunt's fallback weekend, 9 and 10 Jan. The spring nomination by Fri 15 Jan. The optional AHS proposal. The 31 January check |
| February | Default: "February is repot-check month..." | W2 in the first week; W3 only if a correction has been logged | Confirm Poison Prevention Week's 2027 dates. Decide on Apple Ads and on spring hours |
| March | Default: "Planting this spring? Describe the bed once..." to mid-April. Pets page: the Poison Prevention Week line, probably 21 to 27 March, once G5 is met | S1 early in March; S2 mid-March; S3 during Poison Prevention Week | The Apple Ads test, mid-March to early April, if its conditions hold |
| April | Default: "Looking for something for a bare bed?..." from mid-April into May | S4 mid-April; S5 only once the write-up is published | The lily of the valley write-up and its Hacker News submission, if AHS declined the proposal or Allison withdrew it after hearing nothing |
| May | Unchanged | S6; S7 | World Bee Day, 20 May, has no post planned |
| June | Default: "Give a bed the goal Feeds pollinators..." around Pollinator Week, 21 to 27 June | S8 during Pollinator Week | The 30 June read of the season |

### W1. Boston fern in a heated room, January

```text
Boston fern in a heated room: NC State Extension says it needs high humidity and constantly moist soil; Clemson Cooperative Extension gives 68 to 72°F by day. PlantAdvocate, which I make, has you feel the soil first, on its own schedule, which isn't cited.
```

Characters: 256, before the link.

Fact: `b3-humidity-lovers.json`, Boston Fern. `humidity_need` high and `water_regime` keep_moist are cited to [NC State](https://plants.ces.ncsu.edu/plants/nephrolepis-exaltata/). `day_f_min` 68 and `day_f_max` 72 are cited to Clemson's indoor-ferns factsheet ([Clemson HGIC](https://hgic.clemson.edu/factsheet/indoor-ferns/)). Boston fern's check schedule, every 2 to 4 days in `species_catalog.json`, is one of the 129 PlantAdvocate wrote, so the post says it isn't cited.

Gates: G0, G1 and G2. Boston Fern is one of the 33 notes that said "Pet-safe", and one of the species whose care notes were garbled at the tip.

Visual: `04-checks-not-chores.png`, where "Check Boston Fern" is on the card. Alt text: "Checks for today in PlantAdvocate, including Check Boston Fern with Watered and Still damp buttons."

### W2. The February repot check, early February

```text
February is repot-check month in PlantAdvocate, which I make: once a year, a look at a plant's roots, ending Repotted, Top-dressed or All fine. Looking and finding nothing to do is a complete answer, not a skipped one.
```

Characters: 218, before the link.

Fact: no plant fact. It is the app's repot check (`mobile/src/notifications/plan.ts:55-60`; `listing.md`, CHECKS, NOT CHORES), and the caretaker rule that a check which "looked, and it didn't need doing" is complete (`CONTEXT.md`, via product-truth.md section 7).

Gates: G0.

Visual: `04-checks-not-chores.png`, since no frame shows the repot check. Say in the alt text that it shows watering checks. Alt text: "A Checks for today card in PlantAdvocate; this frame shows watering checks, and the February repot check uses the same card."

### W3. The corrections log, only once it has an entry

```text
PlantAdvocate, which I make, now keeps a public corrections log: the date, the species, the field, the old value, the new value and the source. A wrong fact gets fixed in the open. The first entry is here:
```

Characters: 205, before the link.

Fact: no plant fact. It describes the corrections page the strategy proposes, which doesn't exist yet. The link goes to that page on plantadvocate.ai, not to the store.

Gates: G0 and G6, meaning a real, confirmed correction is on the page. If no correction has happened, there is no post.

Visual: a screenshot of the corrections page itself. None of the 16 frames applies.

### S1. Check before it goes in, early March

```text
Planting this spring? In PlantAdvocate, which I make, describe the bed once, then check each new plant against it before it goes in. Here a lady fern is flagged for a full-sun bed. The Royal Horticultural Society lists it for full or partial shade.
```

Characters: 248, before the link.

Fact: the Lady Fern record, as P2 (`b50-native-woodland.json`, `outdoor_sun_exposure`, [RHS](https://www.rhs.org.uk/plants/1897/athyrium-filix-femina/details)). The check before saving is in `listing.md`, SEE WHAT SUITS IT.

Gates: G0.

Visual: `03-check-before-planting.png`. Alt text: "Add plant in PlantAdvocate with Lady Fern picked, its note that no toxicity verdict is recorded, and a box saying the full-sun bed doesn't suit it, citing the Royal Horticultural Society."

### S2. The fence and the wisteria, mid-March

```text
Chinese wisteria on a 7 ft fence. PlantAdvocate, which I make, flags it: "Outgrows this spot: climbs to 25 ft and there is 7 ft of headroom…" NC State Extension gives its height as 10 to 25 ft and tags it invasive, so the app never puts it forward.
```

Characters: 248, before the link.

Fact: `b23-daylily-and-more-gaps.json`, Chinese Wisteria, `mature_height_in` 120 to 300, from NC State's Height of 10 to 25 ft ([NC State](https://plants.ces.ncsu.edu/plants/wisteria-sinensis/)). The Invasive Species tag is in the same page's Problems list, quoted in the record's `toxic_to_pets` citation. The exclusion is `never_put_forward` in `toxicity.py`, settled in the handoff and ADR 0009. The quoted finding is the app's own, from `listing.md`. In shot 01 the sentence carries on ("; spreads to 30 ft across and the space is 24 sq ft", then a line about support and hard cutting back), so the quotation ends in an ellipsis, not a full stop, and the quoted words aren't changed. "Never puts it forward" means it is never listed among good candidates. Keep "climbs to", never "reaches".

Gates: G0.

Visual: `01-needs-addressing.png`, with Chinese Wisteria's size misfit citing NC State Extension. Alt text: "Needs addressing on a demo garden's back fence bed: Chinese Wisteria climbs to 25 ft and there is 7 ft of headroom, citing NC State Extension."

### S3. National Poison Prevention Week, probably 21 to 27 March

```text
National Poison Prevention Week. Pothos: NC State Extension rates its poison severity for people medium and marks it a problem for cats and dogs. PlantAdvocate, which I make, says so, with the US Poison Control number. Not medical or veterinary advice.
```

Characters: 252, before the link.

Fact: `b1-foliage-core.json`, Pothos, `toxic_to_pets` true. Its `toxicity_detail` records NC State's Medium rating and its cat, dog and horse tags, cited to [NC State](https://plants.ces.ncsu.edu/plants/epipremnum-aureum/), with Clemson's philodendron factsheet corroborating ([Clemson HGIC 1509](https://hgic.clemson.edu/factsheet/philodendron-pothos-monstera/)). The severity word is about people, as the app's rule requires. The post names cats and dogs only, because the app's sentence, in shot 06, reads "Toxic to cats, dogs and people" with no horses, and the post says the app says so. The post doesn't repeat the in-app effect clause, because that clause comes from the arum-family table in `toxicity.py`, not from a cited page.

Gates: G0, G1, G4 and G5. Also confirm the week's 2027 dates in February, since [channels.md](../research/channels.md) found sources disagreeing.

Visual: `06-hazards-stated-plainly.png`. Alt text: "Pothos in PlantAdvocate: toxic to cats, dogs and people, all parts, NC State Extension's medium severity rating for people, and Poison Control (US 1-800-222-1222) or a vet."

### S4. Tomatoes along the south fence, mid-April

```text
Say "12 tomatoes along the south fence" and PlantAdvocate, which I make, turns it into a plant, a count and a spot to confirm. NC State Extension's tomato page calls for 6+ hours of full sun, and even watering against blossom end rot and split fruit.
```

Characters: 250, before the link.

Fact: `b5-edible-and-garden.json`, Tomato. `outdoor_sun_exposure` full_sun and `water_regime` keep_moist are both cited to [NC State](https://plants.ces.ncsu.edu/plants/solanum-lycopersicum/), and the record's dry-down note ties uneven moisture to blossom end rot and splitting. The spoken example is the listing's (WALK THE GARDEN) and shot 08's. The post leaves out tomato's hazard line. Its effect clause in the app ("drooling and stomach upset") comes from the `KNOWN_NUANCE` table in `toxicity.py`, sourced to "well-established Solanaceae chemistry", the same kind of clause G5 is about. Since 2026-10-30 the app labels it "PlantAdvocate's own summary", and the post still leaves it out.

Gates: G0.

Visual: `08-walk-the-garden.png`. Alt text: "Walk the garden in PlantAdvocate: two confirmed cards, 12 tomatoes along the south fence and a rosemary by the gate, and a button to add 2 to the garden."

### S5. The lily of the valley write-up, April, only if published

```text
I wrote about lily of the valley: NC State Extension and Missouri Botanical Garden, 2 sources cited in PlantAdvocate, the app I make, rate its poison risk differently. Neither has reviewed or endorsed the app. What each records, and what the app shows:
```

Characters: 252, before the link.

The post says Allison makes the app, as every post must, and since its whole subject is two named organizations and it links to a piece about Allison's own app, it carries a short form of the independence line too.

Fact: `b26-toxic-and-more-trees.json`, Lily of the Valley, which cites Missouri Botanical Garden calling all parts very poisonous ([Plant Finder](https://plantfinder.mobot.org/PlantFinderDetails.aspx?kempercode=c250)) and NC State's page ([NC State](https://plants.ces.ncsu.edu/plants/convallaria-majalis/)). NC State's Poison Severity: Low reading of its live page is in the handoff's decision 6, read on 2026-10-17. The write-up is Allison's, in their own words. This post only points to it, and links the write-up's page, not the store.

Gates: G0 and G6: The American Gardener has declined the proposal, or Allison has written to withdraw it after hearing nothing; the write-up is published with the independence line; decision 6 is settled; and both source pages were re-read that day.

Visual: none of the 16 frames shows lily of the valley, which stays out of store copy. Use the write-up page's own link preview.

### S6. A rosemary by the gate, May

```text
Rosemary by the gate. NC State Extension lists it for full sun, says overwatering is the usual cause of decline or death, and records its flowers drawing butterflies, bees and hummingbirds. In PlantAdvocate, which I make, each cited fact names its source.
```

Characters: 255, before the link.

Fact: `b4-tricky-cases.json`, Rosemary. `outdoor_sun_exposure` full_sun, `water_regime` dry_thoroughly_between (the overwatering line) and `attracts_pollinators` true (butterflies, bees and hummingbirds) are all cited to [NC State](https://plants.ces.ncsu.edu/plants/salvia-rosmarinus/).

Gates: G0.

Visual: `08-walk-the-garden.png`, where "a rosemary by the gate" is the second card. Alt text as S4.

### S7. What a candidate is, and isn't, May

```text
Each growing area in PlantAdvocate, which I make, lists good candidates: species with nothing on record against that spot and at least 1 thing confirmed for it. A candidate isn't a safety verdict: it can carry a hazard line, as the first in this bed does.
```

Characters: 255, before the link.

Fact: no catalog fact beyond the frame. The candidate rule is the listing's (SEE WHAT SUITS IT), and the truth sheet notes that candidates can carry hazard lines. The first candidate in shot 02, African Blue Lily, shows "Toxic to people." (`docs/screenshots/1.1.3/CHECK.md`). The post says nothing about which plants are never put forward, because that rule has exceptions a post can't carry.

Gates: G0 and G1.

Visual: `02-good-candidates.png`. Alt text: "Good candidates here on a full-sun bed, opening with African Blue Lily and its line "Toxic to people", then Ageratum and others, each with what is confirmed for the spot."

### S8. Pollinator Week, 21 to 27 June

```text
Pollinator Week. Give a bed the goal Feeds pollinators and PlantAdvocate, which I make, checks each plant against it. NC State Extension lists American blue vervain as attracting butterflies and specialized bees. Where no source says, the app says so.
```

Characters: 251, before the link.

Fact: `b76-native-wet-meadow-perennials.json`, American Blue Vervain, `attracts_pollinators` true, cited to NC State's Attracts field ([NC State](https://plants.ces.ncsu.edu/plants/verbena-hastata/)). The goal check is `garden-gnome/app/services/fit.py:440-454`, whose two sentences read "Recorded as feeding pollinators." and "No source says whether this feeds pollinators." Don't call vervain native. Its sources say so, but the app has no native-status field, and native gardeners' first question is one it can't answer.

Gates: G0.

Visual: `02-good-candidates.png`, the 17 Pro Max frame, where American Blue Vervain is the fifth candidate and its confirmed line is in view (it's cut on the 17 Pro). Alt text: "Good candidates on a bed set to feed pollinators, including American Blue Vervain with what is confirmed for the spot."

## Held for later

One catalog fact suits a season outside this plan. `b4-tricky-cases.json` records that a Christmas cactus sets buds from mid-September given bright days, nights of 55 to 65°F and at least 13 hours of unbroken darkness. NC State's page and Missouri Botanical Garden's Plant Finder both give it ([NC State](https://plants.ces.ncsu.edu/plants/schlumbergera-x-buckleyi/), [Plant Finder](https://www.missouribotanicalgarden.org/PlantFinder/PlantFinderDetails.aspx?taxonid=253152)). It would make an honest early-September 2027 post, written then and checked against both pages that week.

## Found while writing

Four things turned up that Allison may want to know. None blocks a post as drafted.

First, the hazard sentence prints a plant's name in lower case: `describe` in `garden-gnome/app/services/toxicity.py` sets `name = common_name.lower()` (line 832). So pages read "christmas cactus", "thanksgiving cactus", "boston fern" and "american blue vervain" in their no-record sentences. It shows on a phone too: frame `03-check-before-planting.png` reads "No toxicity verdict recorded for lady fern yet". For lady fern the lower case is ordinary English, so that frame can stay; the names with a proper noun are the ones it breaks. It's a backend-only fix that ships with a deploy, and worth doing before any screenshot of those pages is taken, and before P6 sends anyone to the Christmas and Thanksgiving cactus pages.

Second, tomato's effect clause in the app comes from a code table, not a cited page, like the lily and arum clauses the strategy names. The third hazard-sentence change should cover it too, along with the other `KNOWN_NUANCE` entries that carry an `effect`. It did: the 2026-10-30 change labels tomato's and rhubarb's effect clauses "PlantAdvocate's own summary" along with the lily, daylily and arum ones.

Third, the snake plant's check schedule (every 14 to 21 days, PlantAdvocate's own) sits a long way from NC State's winter interval of 1 to 2 months. The "Still damp" answer makes that honest in use, and P4 says outright that the app's check comes due more often, on its own uncited schedule. It's one example of why the 129 schedules are labelled uncited.

Fourth, the poinsettia record's `toxicity_detail` opens with a judgement, that its reputation as seriously poisonous is exaggerated, and its sources disagree. P5 leaves poinsettia out for that reason. Read that page with particular care at G3 before any holiday line names it.
