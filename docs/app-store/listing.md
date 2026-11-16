# App Store listing for 1.2.0 (build 26)

Paste each block into the App Store Connect field named in its heading. The
count under each block is the block exactly as written, counted against
Apple's limit; newlines count as characters. `mobile/store.config.json`
carries the same text, so `eas metadata:push` sets these fields for you.
Read "Before you submit" in [README.md](README.md) first.

Checked on 2026-11-16 against `master` at `8379754`, the commit build 26 is
made from. Every sentence describes something a reviewer can see in that
build, signed in with their own Apple ID, against production with both
feature flags on. Nothing here mentions identifying a plant from a photo,
photo check-ups or AI: the first is hidden in this build
(`mobile/src/photoId/entry.ts`), and the server switches the other two off.

1.2.0 is the first version Apple will review. 1.1.3 was uploaded but never
submitted (`docs/design/2026-11-15-overhaul-build-spec.md`, A15), and the
listing pulled from App Store Connect on 2026-11-16 has no release notes.

## App information

### Name

<!-- field limit=30 -->
```text
PlantAdvocate: Garden Care
```
Characters: 26 of 30.

Unchanged. Garden care is still true of 1.2.0, and the land features sit in
the subtitle and the description. If the name is ever refused, use
`PlantAdvocate` (13), the name under the home-screen icon
(`mobile/app.json` `expo.name`).

### Subtitle

<!-- field limit=30 -->
```text
Know your land and its seasons
```
Characters: 30 of 30.

The pulled listing said "Plants that suit each spot". 1.2.0 opens on Home, a
weather-and-season report, and leads with the land, so the subtitle does
too.

### Categories

Primary: **Lifestyle**. Secondary: **Reference**. Unchanged from the pulled
listing.

Lifestyle, because what people do in the app is look after their own yard,
beds and plants, which the App Store files under home and garden. Reference,
because the Species Almanac is a cited catalog people open without a plant
of their own in mind. Weather was considered and left out: the forecast
serves the land and the seasonal plan, and is not the reason to open the
app. Not Medical: hazard notes repeat what sources record and diagnose no
one.

### Copyright

```text
2026 Allison Bowman
```

Use the legal name exactly as the Apple Developer account shows it (App
Store Connect > Business, or the Membership page). The website footer says
"© 2026 PlantAdvocate". Use that only if PlantAdvocate is a registered
business that holds the developer account. Otherwise you are the rights
holder. Apple asks for the year and the owner, with no URL.

Unchanged from the pulled listing.

## Version information (1.2.0)

### Promotional text

Promotional text can be changed at any time without a new review.

<!-- field limit=170 -->
```text
Add your land in the United States for estimates of its sun, soil, water and frost dates, each with how sure it is and where it came from, and an aerial map of it.
```
Characters: 163 of 170.

### Description

The last two sentences of the MORE THAN 990 SPECIES paragraph are, word for
word, the line the app shows under each hazard note
(`mobile/src/care/notAdvice.ts`). Change them only together with the app
and with `review-notes.md`.

<!-- field limit=4000 -->
```text
PlantAdvocate helps you look after the land and the plants you grow, from a back yard to a pot on a windowsill. Add your land in the United States and PlantAdvocate reads public maps for the area around it, then plans the season with you. Every reading from public maps is an estimate, and each one says how sure it is and where it came from.

ADD YOUR LAND
Type an address or tap Use my location, put a pin on your home on an aerial image, and tap what is on your lot: lawn, garden beds, trees that drop their leaves, and so on. The address is used only on your phone to find the image. The pin is what PlantAdvocate keeps. The public map services are asked about a block of land about 1,600 feet across that contains your pin, never the pin itself.

READ YOUR LAND
PlantAdvocate estimates sun, where water collects, slope, soil, the hardiness zone and typical frost dates from public sources such as the U.S. Department of Agriculture soil survey and the U.S. Geological Survey's elevation and aerial maps. Each value carries a label such as Good estimate, Area estimate or Rough estimate, and a Why and data source note that says what was counted and what was not. Know better about the sun, soil, slope or drainage? Tap what is true, and your answer is used instead, with the public estimate still shown beside it.

SEE IT ON A MAP
Home and Your land show the aerial image with your pin and your zones. Switch on the Sun, Trees or Water layer to see where the sun falls in the growing season, how tall the tree canopy is, and where water collects or runs after rain. A legend and notes under the map say what each layer leaves out. Buildings, for example, are not counted in sun.

DRAW YOUR ZONES
Stretch a box over a bed, a lawn or a tree on the aerial image, then describe it with a few taps: what grows there and whether it loses its leaves. Each zone gets its own sun, soil and drainage values.

WEATHER AND THE SEASON
Once your land is added, Home opens on a report of the weather, what is due this week and the season ahead. For land in the United States, the forecast comes from the National Weather Service. Bars show each day's high and low, with frost nights marked. The seasonal plan sets out first frost and freeze, leaf drop, dormancy, the last spring freeze, spring growth and when tender plants can go back outside, on a timeline, each with its window, tasks, reasons and sources. Tell it a frost has happened at your place, or that a task is done or not needed. Frost and weather alerts are optional, off until you turn them on, and are scheduled on your phone.

NO YARD? STILL USEFUL
Pots on a balcony or a windowsill work too. Describe each place you grow, add your plants, and log care. When a plant comes due, feel the soil, then tap Watered or Still damp. Walk the garden lets you type or say what is planted, then confirm each plant and add them all at once.

MORE THAN 990 SPECIES, WITH SOURCES
The Species Almanac covers houseplants, herbs, vegetables, perennials, shrubs, trees, bulbs and climbers. Care facts come from organizations that publish them, such as NC State Extension, the Royal Horticultural Society and Missouri Botanical Garden, and each species page names its sources. Anything not yet cited says so. If a source records a plant as harmful to people or pets, its page says so plainly. Where there is no record, PlantAdvocate says so. A missing record is never treated as safe. Under each hazard note, the app says: These notes repeat what the sources publish. They are not medical or veterinary advice.

FREE, WITH NO ADS
PlantAdvocate is free, with no ads and no in-app purchases. Sign in with Apple or Google; there is no password to remember. The community census is off unless you turn it on. You can delete your account, and everything in it, from Settings.

PlantAdvocate is independent. The organizations it cites have not reviewed or endorsed it. Estimates from public maps can be wrong for your spot, so check what matters on the ground.
```
Characters: 3,991 of 4,000.

### Keywords

None of these repeats a word from the name or the subtitle, which Apple
already indexes. Commas count; there are no spaces after them.

<!-- field limit=100 -->
```text
frost,yard,soil,sun,shade,drainage,hardiness,zone,weather,plant,houseplant,vegetable,toxic,pets,tree
```
Characters: 100 of 100.

"identify" stays out, because identifying a plant from a photo is hidden in
this build. "map" and "forecast" were cut for length; "frost", "soil", "sun"
and "yard" carry the land features.

### What's New in This Version

Does not apply. App Store Connect shows this field only for an update, and
no version of PlantAdvocate has been released on the App Store. The pulled
`store.config.json` has no `releaseNotes`, and `store.config.json` keeps it
that way. If you want a note for TestFlight testers, the build's **What to
Test** field takes any text; it is not part of the listing.

## URLs

| Field | URL | Why |
|---|---|---|
| Support URL | `https://plantadvocate.ai/support` | The app links `/support.html` (`mobile/src/support.ts:10`), which the site serves at `/support` |
| Marketing URL | `https://plantadvocate.ai` | `mobile/src/support.ts:9` |
| Privacy Policy URL | `https://plantadvocate.ai/privacy` | The app links `/privacy.html` (`mobile/src/support.ts:14`). The pulled listing had `/privacy.html`; `/privacy` is the page that link ends on. Also asked for in App Privacy |

These were not loaded for this check (no live requests). Before you submit,
open each one and check that the support page describes 1.2.0 and the
privacy page shows the 1.2.0 policy (`site/privacy.html`, effective
November 16, 2026 in the copy read on 2026-11-16),
which covers the land features. See README.md.

## Pricing and rights

Price: Free. Availability: the United States only at launch (decided
2026-10-31, `docs/2026-10-16-app-store-finish-line-handoff.md`, decision
11). The land features need a United States place, so this matches what the
app can do. There are no in-app purchases: no StoreKit or purchase library
in `mobile/package.json`, and nothing in `mobile/src` sells anything.

Content Rights: answer **Yes, it contains, shows or accesses third-party
content**, and **Yes, I have the rights**. That content is:

- the names of cited sources, with a link to each page;
- forecasts from the National Weather Service, Apple Weather or Open-Meteo,
  each credited where it is shown;
- public map data: the U.S. Department of Agriculture soil survey, U.S.
  Geological Survey elevation, land cover and National Agriculture Imagery
  Program aerial images, the 2023 Plant Hardiness Zone Map, NOAA climate
  normals, the USA National Phenology Network spring index, and the Meta and
  World Resources Institute canopy height map, each named in the value's
  Why and data source note (`garden-gnome/app/services/site/copy.py:55-85`,
  `garden-gnome/app/services/site/sources/canopy.py:50`,
  `garden-gnome/app/services/season/events.py:43`);
- species data that came in part from Perenual, credited in Settings.

The federal sources are public domain. The hardiness map and the spring
index are Creative Commons Attribution 4.0 (PLAN.md section 10), and so is
the canopy height map, attributed to Meta and the World Resources Institute
(`docs/design/2026-11-15-sun-and-drainage-sources.md`). Open-Meteo's free tier is for
non-commercial use (`garden-gnome/app/services/weather.py:43-44`), which a
free app with no ads fits.

## Where each claim comes from

Paths are from the repository root at `8379754`.

| Claim | Where it is true |
|---|---|
| Land features only in the United States | `garden-gnome/app/services/site/profile.py:170-173`, `:346`, `:509`; `mobile/src/screens/PropertySetupScreen.tsx:173`; `garden-gnome/app/services/site/layers.py`, `OUTSIDE_US_TEXT` |
| Address or Use my location, pin on an aerial image, what is on the lot | `mobile/src/screens/PropertySetupScreen.tsx:150, 212, 225`; `mobile/src/components/AddressPicker.tsx:99`; lot labels `mobile/src/land/setup.ts:11-20` |
| Address used only on the phone; the pin is stored | `PropertySetupScreen.tsx:150`; `mobile/src/land/setup.ts:7-9`; `garden-gnome/app/models/models.py:726-752` (`Property`, no address column) |
| Block about 1,600 feet across, never the pin | `PropertySetupScreen.tsx:196`; `docs/design/2026-11-15-overhaul-build-spec.md` section 2 (snap grid and guarded outbound client, `garden-gnome/app/services/site/http.py`) |
| Sun, water, slope, soil, hardiness, frost dates; sources | `docs/design/2026-11-15-overhaul-build-spec.md` section 4 (`SiteValue.field`); sources `garden-gnome/app/services/site/sources/soil.py:35`, `elevation.py:47`, `imagery.py:48`, `landcover.py:36`, `canopy.py:52` |
| Confidence labels | `garden-gnome/app/models/schemas.py:615, 652` |
| Why and data source | `mobile/src/components/explainedText.ts:28` |
| Corrections for sun, soil, slope, drainage, with the public estimate beside | `garden-gnome/app/services/site/overrides.py` (`SPECS`; hardiness, land cover and frost dates are `none`); `mobile/src/land/CorrectionControl.tsx:31-42`; `mobile/src/land/profileRows.ts:70-72` |
| Map on Home and Your land, Sun, Trees and Water layers | `mobile/src/screens/HomeScreen.tsx:322`; `mobile/src/screens/LandScreen.tsx`, "The map"; `garden-gnome/app/services/site/layers.py:86` |
| What each layer shows and leaves out | `garden-gnome/app/services/site/layers.py:110-149` (legends and notes, including "Buildings are not counted.") |
| Zones: box, what grows, leaf habit, own values | `mobile/src/screens/ZoneMapScreen.tsx:339, 573, 593`; `mobile/src/zones/describe.ts:10-11`; `LandScreen.tsx`, the empty "Your zones" line |
| Home: weather, this week, season ahead with land | `mobile/src/screens/HomeScreen.tsx:245, 292, 360` |
| National Weather Service for land in the United States | `garden-gnome/app/services/vitals.py:89, 110`; `garden-gnome/app/services/season/forecast.py:45`; `site/privacy.html`, "Weather" |
| Forecast bars with frost nights | `mobile/src/home/forecastBars.ts:6-14, 99-101` |
| Season events, tasks, sources, timeline | `garden-gnome/app/services/season/events.py:46-53, 428-438, 657, 691, 752`; `mobile/src/screens/SeasonScreen.tsx`; `mobile/src/components/SeasonTimeline.tsx` |
| It happened here, Done, Not needed | `mobile/src/season/sections.ts:22-31` |
| Alerts optional, off by default, scheduled on the phone | `mobile/src/notifications/reminders.ts:82-89`; `mobile/src/screens/SettingsScreen.tsx:362`; no push token anywhere in `mobile/src` |
| Watered or Still damp | `mobile/src/care/CareTodos.tsx:242` |
| Walk the garden | `mobile/src/screens/PlantsScreen.tsx:151`; `mobile/src/screens/CaptureGardenScreen.tsx:272, 309` |
| More than 990 species | 999 records in `garden-gnome/app/data/verified/*.json`, unchanged since `307930e`; 4 are genus-level, so a sync makes 995 researched species |
| Cited organizations, sources named, uncited labelled | `garden-gnome/app/data/claims/authorities.py`; `mobile/src/components/CareFacts.tsx:106-124`; `mobile/src/care/facts.ts` |
| Hazards, missing record never safe, the not-advice line | `garden-gnome/app/services/toxicity.py`, `describe`; `mobile/src/care/notAdvice.ts` |
| Free, no ads, no purchases | `mobile/package.json` (no purchase, ad or analytics library) |
| Sign in with Apple or Google | `mobile/src/auth/LoginScreen.tsx` |
| Census off by default | `garden-gnome/app/models/models.py:338` |
| Delete account from Settings | `mobile/src/screens/SettingsScreen.tsx:101-120`; `garden-gnome/app/routers/auth.py:374-430`, which also deletes land (`garden-gnome/app/routers/properties.py:278-305`) |
