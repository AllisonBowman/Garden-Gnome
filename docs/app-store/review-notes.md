# App Review Information for 1.1.3

This is App Store Connect > the 1.1.3 version page > App Review Information.
Checked against the code at `b083a90`. Production has to be serving that
code first (see README.md). On 16 October, `garden-gnome-api.fly.dev`
still had no `/growing-areas` routes, so step 1 of the notes would fail
until it is deployed.

## Sign-In Information

Tick **Sign-in required**. PlantAdvocate signs in only with Sign in with
Apple or Google (`mobile/src/auth/LoginScreen.tsx`); there is no password
login and no demo account to give. If the form insists on a user name and a
password, enter `Sign in with Apple` as the user name and `none needed` as
the password, and let the Notes below explain: a reviewer taps Sign in with
Apple and has an account in one tap, with no other step. Google Sign-In
works too. Deleting the account afterwards is in Settings.

## Contact Information

| Field | Value |
|---|---|
| First name | Allison |
| Last name | Bowman |
| Phone number | (a number you answer during review, with country code) |
| Email | an address you read daily during review, such as support@plantadvocate.ai (`mobile/src/support.ts:11`) |

## Notes

Paste as is.

<!-- field limit=4000 -->
```text
SIGN-IN (there is no demo account)
PlantAdvocate signs in only with Sign in with Apple or Google, so there is no username, password or demo account. On the first screen, tap Sign in with Apple. That creates your account straight away, with 1 empty indoor growing area called My Home. Sign in with Google works too. To delete the account: Settings tab > Account > Delete account, then Delete forever. That deletes the account and everything in it, and asks Apple to revoke the sign-in.

FIRST LAUNCH
Our server sleeps when idle, so the first request can take several seconds while it wakes. If a screen says it couldn't reach the server, wait a few seconds and try again.

EACH FEATURE IN UNDER A MINUTE
1. Growing areas tab. Tap New growing area. Name it Back fence, pick In-ground bed, and type 84 in Headroom (inches). Under Location, search a town or tap Use my location (location permission is asked only then). Tap Next: Outdoors and Full sun are already set. Tap Next, pick Feeds pollinators, then Create. The new area opens with its good candidates, a care calendar and a local forecast.
2. On that area, tap Add a plant here. Search Lady Fern and pick it: before you save, the screen says this spot gets more sun than the sources record for it. Then search Basil instead and tap Save plant.
3. Plants tab, tap Basil. Log care with a tap. Under Ask the Gnome, tap Get care advice. The advice is built from the species' facts and this plant's log, and has a Report this result link. Below: the care guide with its hazard note, how its spot suits it, and Move or remove.
4. Checks. The Checks for today card on the Plants tab lists checks when they come due, counted from the last time that care was logged. Tap Watered on Basil today and its first check appears tomorrow, with Watered and Still damp to tap.
5. Walk the garden (button on the Plants tab). Type: 12 tomatoes along the south fence, a rosemary by the gate. Tap Add these, look over the 2 cards, then tap Add 2 to the garden. The microphone icon dictates instead (microphone and speech recognition permission are asked only on tap). The camera is only a backdrop.
6. Species tab. Search the catalog and open any species for its care facts, its sources (they open in Safari) and its hazard note. The card at the top opens the Species Almanac, which can be narrowed to what fits a growing area.
7. Census tab. A summary of your own garden, and a way into the Almanac. The community census is a switch in Settings > Privacy & data, off by default. If someone joins, our server can count their plants and care dates with no name, email, notes or coordinates, under identifiers made new for each export.
8. Settings. Reminders per care type (notification permission is asked when you turn a reminder on), weather-adjusted watering, light and dark themes, a privacy summary, support links, Sign out and Delete account.

PHOTOS
In Add plant, Take photo and Choose photo appear only on iPhones where Apple Intelligence is available and turned on. The photo is read on the phone, never uploaded, and only suggests catalog matches to confirm. On other devices those buttons are missing by design; species search works everywhere. Photo check-ups of an ailing plant, and reading typed symptoms, are not offered in this version. The app asks our server what it can do and hides both.

PLANT HAZARDS AND EDIBILITY
Hazard and edibility notes repeat what the cited sources publish, mostly NC State Extension and other university extension services. Where a source records harm to people or pets, the page says so plainly. A plant shows as edible only with its source's conditions. A missing record reads as unknown, never as safe. These notes are not medical or veterinary advice.

WEATHER
Forecasts come from Apple Weather when it answers, otherwise from the U.S. National Weather Service or Open-Meteo. The source is credited under the forecast.
```
Characters: 3,895 of 4,000.

Two parts of the notes describe 1.1.3 changes being made alongside this
paperwork rather than code already on `b083a90`. Check both in the build
before pasting:

- **PLANT HAZARDS AND EDIBILITY**: the second and third sentences need the
  plant-hazard and edibility change. Without it, most pages still word a
  hazard as pets only and show "grown to eat" with no conditions. Then
  either hold the submission or cut those 2 sentences.
- **Step 7 (Census tab)**: needs the operator-only census change. At
  `b083a90` the tab still has a Census sync card with a Sync now button,
  which answers "skipped" (`mobile/src/screens/CensusScreen.tsx:107-125`).
  Any account can call the export, and the export's `plant_uuid` never
  changes (`garden-gnome/app/routers/census.py:96-147`). The notes must
  not go in with either still true.

## Where each step comes from

| Step | Code |
|---|---|
| Account and My Home made at first sign-in | `garden-gnome/app/routers/auth.py:83-93`; My Home is indoor, sheltered, partial sun by the model defaults (`models.py:595-597`) |
| Deletion, with the Apple revoke | `mobile/src/screens/SettingsScreen.tsx:78-97, 194-204`; `garden-gnome/app/routers/auth.py:227-273`. A failed revoke is logged and never blocks deletion |
| Server sleeps | `garden-gnome/fly.toml` `auto_stop_machines` with `min_machines_running = 0`. A first request after idle took 6.7 s on 15 October; the client waits 15 s and retries once (`mobile/src/api/client.ts:76`; `App.tsx:150`) |
| Step 1 | Labels: `GrowingAreasScreen.tsx:214, 231-281, 387-401`; Headroom label `growingAreas/realEstate.ts:171`; In-ground bed preset `realEstate.ts:81`; goals `realEstate.ts:53-68`; lands on the new area, `GrowingAreasScreen.tsx:163-169` |
| Step 2 | `GrowingAreaDetailScreen.tsx:201-209`; the misfit before saving `AddPlantScreen.tsx:355-381`. On a scratch sync, Lady Fern in this bed reads "This spot gets 6+ hours of direct sun; sources record it for part shade, full shade." and Basil is a candidate with a water schedule of 1 to 2 days |
| Step 3 | `PlantDetailScreen.tsx:245-330, 422-458, 488-540`; a blank nickname becomes the species name (`garden-gnome/app/routers/plants.py:101-102`) |
| Step 4 | A check is anchored to the last log of its care type. A plant added in the app has no acquired date, so nothing comes due until a first log (`mobile/src/care/schedule.ts:87-98`); outcomes `CareTodos.tsx:178-203` |
| Step 5 | `CaptureGardenScreen.tsx:222-300`. Run through `splitUtterance` and `groundEntries` against a scratch catalog, the sentence gives 2 confident matches: 12 Tomatoes at south fence, 1 Rosemary at gate. The camera is a backdrop only (`CaptureGardenScreen.tsx:24-31`) |
| Step 6 | `SpeciesDetailScreen.tsx:62-126`; sources open with `Linking.openURL` (`components/CareFacts.tsx:115`); Almanac card `SpeciesScreen.tsx:119-140` |
| Step 7 | `CensusScreen.tsx:51-105`; switch `SettingsScreen.tsx:334-347`; default off `models.py:268` |
| Step 8 | `SettingsScreen.tsx:133-150, 279-388` |
| Photo identify only with Apple Intelligence | `AddPlantScreen.tsx:127-131, 221-253`; `modules/plant-id/ios/PlantIdModule.swift:78-89` |
| Photo check-ups and symptoms hidden | `mobile/src/care/aiCapabilities.ts:29-39`; `PlantDetailScreen.tsx:271, 339`; production `/ai/status` on 16 October: symptoms `stub`, vision `ready: false` |
| Weather chain and credit | `garden-gnome/app/services/weather.py:363-379`; `mobile/src/components/WeatherCredit.tsx` |
