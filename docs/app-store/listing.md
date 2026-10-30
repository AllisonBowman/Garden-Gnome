# App Store listing for 1.1.3

Paste each block into the App Store Connect field named in its heading. The
count under each block is the block exactly as written, counted against
Apple's limit; newlines count as characters. Read "Before you submit" in
[README.md](README.md) first. Until those things are true of the build, the
server and the website, some of this text isn't.

Checked against the code at `307930e` on `care-advice-honesty`, the ship
branch, with the review fixes made alongside it. Brought up to the
2026-10-30 changes on the same branch: the line the app now shows under
each hazard note, the hazard sentences' pet source and local poison
centre, the Report a fact link, and the description's "temperature" in
place of "cold hardiness", which no page shows. Every 1.1.3 change these blocks describe
is on that branch once the 2026-10-30 changes land, so build from a tip
that carries them; no line is waiting on anything later.

The species figure is "more than 990". The 134 files in
`garden-gnome/app/data/verified/` hold 999 records. Four of them are
genus-level (Hippeastrum, Brugmansia, Cattleya, Nymphaea), and the claim sync
never turns those into catalog rows, so a fresh sync makes 995 researched
species (`python -m app.data.seed` on a scratch database: "genus subjects
skipped 4", 995 rows with care data status `sourced`). "More than 990" stays
true as batches land. It also stays true if production keeps listing its
older, uncited imports, because it counts researched species, not catalog
rows.

## App information

### Name

<!-- field limit=30 -->
```text
PlantAdvocate: Garden Care
```
Characters: 26 of 30.

If that name is taken, use `PlantAdvocate` (13), which is also the name under
the home-screen icon (`mobile/app.json` `expo.name`).

### Subtitle

<!-- field limit=30 -->
```text
What suits each spot you grow
```
Characters: 29 of 30.

### Categories

Primary: **Lifestyle**. What people do every day in the app is look after
their own plants and places: growing areas, plants, checks, reminders. That
is home and garden upkeep, which the App Store files under Lifestyle.

Secondary: **Reference**. The Species Almanac is a cited reference to more
than 990 species that people open without a plant of their own in mind.

Not Education: nothing is taught in lessons or graded. Not Weather: the
forecast supports a growing area and is not the reason to open the app. Not
Medical: the hazard notes say what a plant can do to people and pets. They
don't diagnose or treat anyone.

### Copyright

```text
2026 Allison Bowman
```

Use the legal name exactly as the Apple Developer account shows it (App
Store Connect > Business, or the Membership page). The website footer says
"© 2026 PlantAdvocate". Use that only if PlantAdvocate is a registered
business that holds the developer account. Otherwise you are the rights
holder. Apple asks for the year and the owner, with no URL.

## Version information (1.1.3)

### Promotional text

Promotional text can be changed at any time without a new review.

<!-- field limit=170 -->
```text
Describe each place you grow, then see what suits it, what doesn't, and why. More than 990 species, with care facts cited to the sources that published them.
```
Characters: 157 of 170.

### Description

The **HAZARDS, STATED PLAINLY** paragraph describes the plant-hazard and
edibility change, which is in the build. Most hazard sentences name no
parts, because most sources don't: on a scratch sync at `798f905`, 30 of the
378 species with a hazard line named parts. So the paragraph promises parts
only where the source gives them. Its last two sentences are, word for word,
the line the app shows under each hazard note from 1.1.3
(`mobile/src/care/notAdvice.ts`), so change them only together with the app
and with `review-notes.md`.

<!-- field limit=4000 -->
```text
PlantAdvocate helps you look after the places you grow, from a windowsill to a back bed. Its advice is never made up on the spot. Care facts come from the organizations that publish them, such as NC State Extension, the Royal Horticultural Society and Missouri Botanical Garden, and each species page names its sources. Where there is no record, PlantAdvocate says so. A missing record is never treated as safe.

DESCRIBE WHERE YOU GROW
Set up a growing area for each place you grow. Say what plants sit in: an in-ground bed, a raised bed, containers, a windowsill, a shelf or floor, a hanging basket, a greenhouse bench or a pond. Add how much room there is, whether it is indoors or out, how much sun it gets, and what you want from it: something to eat, low upkeep, or food for pollinators. Leave a measurement blank and it counts as unknown. Nothing is recommended on a guess.

SEE WHAT SUITS IT
Each growing area lists what needs addressing among its plants, with the reason and the source. A shade fern in full sun is flagged. So is a climber that will outgrow a 7 ft fence. Each area also puts forward good candidates: species with nothing on record against that spot and at least 1 thing confirmed for it. You get the same check before you save a new plant, and again on each plant's own page.

MORE THAN 990 SPECIES, WITH SOURCES
The Species Almanac covers houseplants, herbs, vegetables, perennials, shrubs, trees, bulbs and climbers. Narrow it to what fits a growing area of yours. Each species page shows facts such as light, water, soil, temperature and size, and lists where they came from. A fact borrowed from the plant's genus is labelled as borrowed. Anything not yet cited says so. The check schedules that reminders follow were written by PlantAdvocate for 129 common plants and are not cited.

HAZARDS, STATED PLAINLY
If a source records a plant as harmful to people or pets, its page says so, gives the source's severity rating for people where it has one, and names the parts where the source does. A plant is shown as edible only with the conditions its source gives. Under each hazard note, the app says: These notes repeat what the sources publish. They are not medical or veterinary advice.

CHECKS, NOT CHORES
When a plant comes due, feel the soil, then tap Watered or Still damp. Either keeps your streak. Nothing is called overdue while it is still inside its care window. Repotting is a look at the roots once a year, in February. Feeding reminders rest from November to February. Reminders are optional and set per care type. They follow a species' care window wherever the catalog holds a schedule for it, and can move an outdoor watering reminder by 1 or 2 days around rain and heat.

WALK THE GARDEN
Add plants by hand, or walk your garden and say what's there: "12 tomatoes along the south fence, a rosemary by the gate." Type it or dictate it, confirm each plant, and add them all at once. On iPhones with Apple Intelligence, Add plant can also suggest likely matches from a photo. The photo is read on your phone and never uploaded, and you confirm the species before you save.

ASK THE GNOME
On any plant, the Gnome gives care advice built from its species' facts and that plant's own care log. On iPhones with Apple Intelligence, the Gnome can say it in its own voice, worked out on your phone, without changing the facts.

LOCAL WEATHER
Give a growing area a place and it gets a local forecast, with what the weather means for that spot.

FREE, WITH NO ADS
PlantAdvocate is free, with no ads and no in-app purchases. Sign in with Apple or Google; there is no password to remember. The community census is off unless you turn it on. You can delete your account, and everything in it, from Settings.

PlantAdvocate is independent. The organizations it cites have not reviewed or endorsed it.
```
Characters: 3,830 of 4,000.

The description says nothing about photo check-ups of an ailing plant or
about reading typed symptoms. Production doesn't offer either: the app asks
`GET /ai/status` and hides both while the server reports them off. If they
are switched on later, describe them in the next version's description, and
update App Privacy first (see [app-privacy.md](app-privacy.md)).

### Keywords

None of these repeat a word from the name or subtitle, which Apple already
indexes. Commas count. There are no spaces after them.

<!-- field limit=100 -->
```text
plant,houseplant,watering,reminder,raised bed,herb,vegetable,perennial,shrub,toxic,pets,weather,yard
```
Characters: 100 of 100.

"identify" is left out on purpose. Photo identification only exists on
iPhones with Apple Intelligence, so most people who searched for it would
not find it in the app.

### What's New in This Version

App Store Connect shows this field only for an update. 1.1.3 is the first
version to go to the App Store, because 1.1.0 to 1.1.2 went to TestFlight
only. So for this submission, paste this into the TestFlight build's **What
to Test** field (same 4,000 limit) and keep it for the store's version
history. It covers everything since 1.1.2 build 15 (`a5d0d07`, 2 August
2026).

Every line describes a change on `307930e`: the hazard and edibility
wording, the operator-only census with no sync button, and
`ios.supportsTablet` false in `mobile/app.json` are all in the build. The
exceptions came with the 2026-10-30 changes: the not-advice line under each
hazard note, the pet source and local poison centre in the hazard
sentences, and the Report a fact link.

<!-- field limit=4000 -->
```text
Growing areas. Describe each place you grow: what plants sit in, how much room there is, indoors or out, how much sun, and what you want from it. A blank measurement counts as unknown, never as 0.

What suits each spot. Each growing area lists what needs addressing among its plants, with the reason and the source, and puts forward good candidates. Add plant shows the same check before you save, and each plant's page shows how its spot suits it. A climber's height is read as how far it climbs, so a wisteria on a 7 ft fence says what it will take to keep it there.

The Species Almanac. Open it from the Species tab or from a growing area, and narrow it to what fits a growing area. It opens faster, too.

A cited catalog. More than 990 species now carry care facts from named sources such as NC State Extension and the Royal Horticultural Society. Each species page lists its sources and labels anything borrowed from the genus.

Hazards stated plainly. Where a source records a plant as harmful to people or pets, its page says so. A plant is shown as edible only with the conditions its source gives. A pet warning a source gives now names that source, and readers outside the US are pointed to their local poison centre. Under each hazard note, a line says these notes repeat what the sources publish and are not medical or veterinary advice.

Report a fact. A link under each species page's sources opens an email to tell us a fact looks wrong.

Checks, not chores. A watering check on the Checks for today card now asks you to feel the soil first, then tap Watered or Still damp. Either keeps your streak. Nothing is called overdue while it is inside its care window. A plant you add is dated that day, so its first check comes due without a log first.

A February repot check. Repotting is now a look at the roots once a year, in February, with 3 endings: Repotted, Top-dressed or All fine. The setting is now called Spring repot check.

Seasonal care. Feeding reminders rest from November to February. Misting reminders are gone, because the sources say misting doesn't help.

Honest humidity. Species pages no longer show humidity figures nobody measured.

A gentler start. The first-run tips now introduce growing areas before your first plant.

Fewer dead ends. The photo check-up and the symptom box stay hidden until they can give a real answer. The Census tab no longer has a sync button.

iPhone only. On iPad, PlantAdvocate now runs as an iPhone app.

New icon. A terracotta pot with a seedling.
```
Characters: 2,515 of 4,000.

## URLs

| Field | URL | Why |
|---|---|---|
| Support URL | `https://plantadvocate.ai/support` | The app links `/support.html` (`mobile/src/support.ts:10`), which redirects (308) to `/support` |
| Marketing URL | `https://plantadvocate.ai` | `mobile/src/support.ts:9` |
| Privacy Policy URL | `https://plantadvocate.ai/privacy` | Also asked for in App Privacy. The app links `/privacy.html` (`support.ts:14`), which redirects (308) to `/privacy` |

All 3 answered 200 on 16 October, but 2 of them say the wrong things. The
live support page still describes subscriptions and Restore Purchases. The
live privacy page is the July 17 policy, which says the app doesn't collect
precise location. Both have to be replaced with the corrected pages before
you submit (see README.md).

## Pricing and rights

Price: Free (tier 0) in every territory. There are no in-app purchases: no
StoreKit or purchase library in `mobile/package.json`, and nothing in
`mobile/src` sells anything.

Content Rights: answer **Yes, it contains, shows or accesses third-party
content**, and **Yes, I have the rights**. That content is:

- the names of the cited sources, with a link to each page (facts are cited
  with attribution and the source's own wording never reaches the app,
  ADR 0003 and `garden-gnome/app/data/claims/authorities.py:27`);
- forecasts from Apple Weather, the U.S. National Weather Service or
  Open-Meteo, each credited under the forecast
  (`garden-gnome/app/services/weather.py:32-48`);
- species data that came in part from Perenual, credited in Settings
  (`mobile/src/screens/SettingsScreen.tsx:417`).

Open-Meteo's free tier is for non-commercial use (`weather.py:43-44`). A
free app with no ads fits that today. Revisit it before PlantAdvocate ever
charges for anything.

## Where each claim comes from

Paths are relative to the repository root, at `307930e`. Files the review
fixes are still changing are cited by function, not line.

| Claim | Where it is true |
|---|---|
| Cited organizations | `garden-gnome/app/data/claims/authorities.py:52-80`; NC State, Missouri Botanical Garden and RHS are the most-cited in `verified/*.json` |
| Each species page names its sources | `mobile/src/screens/SpeciesDetailScreen.tsx:140`, `mobile/src/components/CareFacts.tsx:106-124` |
| Missing record never safe | `garden-gnome/app/services/toxicity.py`, `describe` (the no-verdict branches) and `hazard_line`; CONTEXT.md "Unknown" |
| Hazard sentence: who, the source's severity for people, parts where the source names them | `toxicity.py`, `describe`. Parts come only from a source's own table; a bare flag names none (`from_legacy`) |
| The not-advice line under each hazard note | `mobile/src/care/notAdvice.ts` holds the two sentences once, and `mobile/src/components/NotAdviceNote.tsx` shows them under the hazard note on species pages, plant pages and Add plant (the 2026-10-30 changes) |
| A pet warning names its source; the local poison centre | `garden-gnome/app/services/toxicity.py`, `_pets_source` ("For pets, the source is ...") and `LOCAL_POISON_CENTRE`, after the US number (the 2026-10-30 changes) |
| Report a fact | `mobile/src/components/ReportFact.tsx`, at the foot of the Sources card on `SpeciesDetailScreen.tsx`; the email is built in `mobile/src/care/factReport.ts` (the 2026-10-30 changes) |
| Surfaces and goals | `mobile/src/growingAreas/realEstate.ts:12-68` |
| Blank means unknown | `mobile/src/screens/GrowingAreasScreen.tsx:273-276` |
| Shade fern in full sun, climber on a 7 ft fence | Fit engine run on a scratch sync: Lady Fern in a full-sun bed gets "This spot gets 6+ hours of direct sun; sources record it for part shade, full shade."; Chinese Wisteria under 84 in of headroom gets "Outgrows this spot: climbs to 25 ft and there is 7 ft of headroom" (`garden-gnome/app/services/fit.py:193-363`) |
| Candidates need 0 misfits and 1 confirmed fit | `garden-gnome/app/services/fit.py:494`, `is_candidate`; CONTEXT.md "Candidate" |
| Check before saving, and on the plant's page | `mobile/src/screens/AddPlantScreen.tsx:392-418`; `PlantDetailScreen.tsx:497` |
| Almanac narrowed to an area | `mobile/src/screens/AlmanacScreen.tsx:242-271`; `SpeciesScreen.tsx:133-154` |
| Borrowed and uncited labels | `mobile/src/care/facts.ts:43-52` |
| Temperature, not cold hardiness | `mobile/src/care/facts.ts`, the Temperature row (days, nights, and "cold damage below" for 75 of the 999 researched records). The Cold row reads `outdoor_temp_min_f`, which no researched record holds (`garden-gnome/app/services/fit.py:41-49`, ADR 0006), so no page shows a survival floor |
| Watered / Still damp, streak kept | `mobile/src/care/CareTodos.tsx:219-244`; commit `9bb1fe7` |
| Care window, no early "overdue" | `mobile/src/care/schedule.ts:133-150`; commit `59e9a0d` |
| February repot inspection | `mobile/src/notifications/plan.ts:55-60`; `SettingsScreen.tsx:37`; commit `b4e2d24` |
| Feeding March to October | `mobile/src/notifications/plan.ts:29-31` |
| Weather nudge | `mobile/src/screens/SettingsScreen.tsx:323-335` |
| Only species with a schedule get reminders | `mobile/src/notifications/plan.ts:154-157`; 129 of 997 rows have schedules on a fresh sync |
| Walk the garden, digits understood | `mobile/src/screens/CaptureGardenScreen.tsx:256-346`; `capture/splitUtterance.ts:121` |
| Gnome voice on the phone, facts unchanged | `mobile/src/gnomeVoice/restyle.ts:1-10`; `modules/plant-id/ios/PlantIdModule.swift:62-75` |
| Photo matches in Add plant, on the phone, never uploaded | `mobile/src/photoId/identify.ts:56-117`; `AddPlantScreen.tsx:236-268`; `modules/plant-id/ios/PlantIdModule.swift:39-56` |
| Local weather per area | `garden-gnome/app/routers/growing_areas.py:79-100`; `GrowingAreaDetailScreen.tsx:456-538` |
| Sign in with Apple or Google only | `mobile/src/auth/LoginScreen.tsx:67-102` |
| Census off by default | `garden-gnome/app/models/models.py:268` |
| Delete account from Settings | `mobile/src/screens/SettingsScreen.tsx:95-114, 211-221`; `garden-gnome/app/routers/auth.py`, `delete_me` |
| Photo check-ups and symptom box hidden | `mobile/src/care/aiCapabilities.ts:45-55`; `PlantDetailScreen.tsx:312, 379`; commit `2f12456` |
