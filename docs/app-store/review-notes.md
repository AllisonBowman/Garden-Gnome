# App Review Information for 1.1.3

This is App Store Connect > the 1.1.3 version page > App Review Information.
Rewritten on 24 October 2026 from what
`docs/go-to-market/research/review-risk.md` found, and checked against the
code at `3f6d7da`, the tip of `care-advice-honesty` (PR #22). Production has
to be serving that code first (see README.md). On 24 October,
`garden-gnome-api.fly.dev/` still answered with no `catalog` block, and
`openapi.json` listed 29 paths with none under `/growing-areas`, so step 1 of
the notes would fail until it is deployed. The 1.1.3 server lists 34 and
adds the `catalog` block. Both call themselves version 0.2.0, so check for
the block, not the version.

The notes now open with what Apple's help page on [a complete
review](https://developer.apple.com/help/app-review/before-submitting-for-review/complete-review/)
asks a new app to give: what it is and who it's for, the business model, the
devices and iOS versions tested, the services it uses, and any regional
differences. They say that the reviewer signs in with their own Apple ID,
which is why no demo account is needed, and say plainly that the Species
Almanac sits behind the same sign-in. To make room, the old steps 3 and 4 are
one step, the old steps 7 and 8 are two lines, the permission notes are
gathered into one sentence, and the weather paragraph is part of SERVICES.
Step 1 now says to tap the place suggestion after typing a town, because a
typed town isn't set until it is tapped.

On 30 October the HAZARDS block changed to say that the app shows the
not-advice line under each hazard note, which 1.1.3 now does
(`mobile/src/care/notAdvice.ts`), in the same words as the listing's
HAZARDS, STATED PLAINLY paragraph. It also says that words of
PlantAdvocate's own are labelled as its summary, as the hazard sentences
have done since the same day. The block grew from 3,750 to 3,881 bytes.
Sign-In Information below and decision 7 of
`docs/2026-10-16-app-store-finish-line-handoff.md` say the same thing: tick
Sign-in required, and if the form insists, `Sign in with Apple` and `none
needed`.

Before you paste, know one thing about iOS 27. The screenshots were taken on
iOS 26.5 simulators because the iOS 27.0 simulator crashed a local 1.1.3
build at launch (`docs/screenshots/1.1.3/README.md`).
`docs/2026-10-24-ios27-scene-lifecycle.md` traces that to the iOS 27.1 SDK
this Mac's Xcode 27.1 linked it against: Apple's scene-lifecycle rule applies
only to apps built with the iOS 27 SDK, and the EAS production profile builds
with Xcode 26.6 and the iOS 26.5 SDK (`mobile/eas.json`). So TESTED ON names
only the iOS 26.5 simulators, the only place a 1.1.3 build has run without
crashing, and that was a local build, not the one Apple will get. When the
EAS build finishes, check that its page names the image
`macos-tahoe-26.5-xcode-26.6`. If your step 5 phone runs iOS 27, name it in
TESTED ON, because that will be the first time 1.1.3 has launched on iOS 27,
and a reviewer may well be on it.

## Sign-In Information

Tick **Sign-in required**. PlantAdvocate signs in only with Sign in with
Apple or Google (`mobile/src/auth/LoginScreen.tsx`); there is no password
login and no demo account to give. The reviewer taps Sign in with Apple and
uses their own Apple ID, which makes them an account in one tap. If the form
insists on a user name and a password, enter `Sign in with Apple` as the user
name and `none needed` as the password, and let the Notes explain. Never give
out a personal Google login.

The reviewer's sign-in will be a first authorization of PlantAdvocate, the
only time Apple hands the app the person's name, and nobody has watched the
production server handle one. The handoff's step 5 rehearsal uses your own
Apple ID, which has authorized the app before. So before you submit, also
sign in once on the TestFlight build with an Apple ID that has never used
PlantAdvocate, check that My Home appears, then delete that account and sign
in again (review-risk.md, "Mitigations, cheapest first").

The Notes also say Sign in with Google works. I found no record in `docs/`
of Google sign-in being tried with someone else's Google account, and a
Google project whose consent screen is still in testing lets in only its
listed test users. Sign in once with a Google account that isn't yours or a
listed tester. If Google refuses it, either publish the consent screen in
Google Cloud or cut "Sign in with Google works too." from the Notes and from
the 2.1(a) reply in review-replies.md before pasting.

## Contact Information

| Field | Value |
|---|---|
| First name | Allison |
| Last name | Bowman |
| Phone number | A number you answer during review, in international format with a plus sign, such as `+1` and the 10 digits for a US number. Apple's field asks for that format ([reference](https://developer.apple.com/help/app-store-connect/reference/platform-version-information/)) |
| Email | An address you read daily during review, such as support@plantadvocate.ai (`mobile/src/support.ts:11`) |

The same number goes into the CONTACT line at the end of the Notes.

## Notes

Fill in the two brackets, then paste the block as it is.

The bracket under TESTED ON is for the phone you check the TestFlight build
on in step 5 of the handoff, for example `Also TestFlight on iPhone 15 Pro,
iOS 27.1.` Keep it no longer than the bracket, which is 53 characters. Name
only a phone you actually ran the build on. If step 5 isn't done on a phone,
delete the bracket and the space before it, and the simulator line stays
true on its own. The bracket in CONTACT is the phone number without the `+1`,
for example `555 555 5555`; if your number isn't a US one, change `+1` to its
own country code.

The line about a screen that couldn't reach the server is true whichever way
decision 1 goes. It doesn't say the server sleeps, because with one machine
kept running during review it doesn't.

<!-- field limit=4000 bytes -->
```text
ABOUT THE APP
PlantAdvocate is an iPhone app for people who grow plants at home, from a windowsill to a back bed. Describe each place you grow and it shows which plants suit it and which don't, with the reason and the source, plus a care log, checks and a local forecast. It is free, with no ads, no in-app purchases and no subscriptions.

TESTED ON
iOS Simulator, iPhone 17 Pro and 17 Pro Max, iOS 26.5. [FILL IN after TestFlight: iPhone model, iOS version]

REGION
Made for the US: English only, feet, inches and Fahrenheit, and hazard notes give the US Poison Control number. National Weather Service forecasts cover only US places; Apple Intelligence, needed for photo matching, isn't offered in every region.

SIGN-IN (no demo account needed)
There is no username or password. On the first screen, tap Sign in with Apple and use your own Apple ID. That creates a new account at once, with 1 empty indoor growing area called My Home, then 4 welcome cards you can skip. Sign in with Google works too. To delete the account: Settings tab > Account > Delete account > Delete forever. That deletes everything and asks Apple to revoke the sign-in.

The app's core is your own growing areas, plants and care log, kept in your account. The Species tab and its Almanac, a reference catalog of more than 990 researched species, sit behind the same sign-in; the Almanac reads your account to mark species you keep and to narrow to what fits one of your growing areas.

SERVICES
Sign in with Apple, Google Sign-In, and our server on Fly.io in the US. For forecasts the server asks Apple Weather, then the U.S. National Weather Service, then Open-Meteo, and credits the one that answered. Town search uses the iPhone's geocoder; dictation uses Apple's speech recognition. No analytics, ad or tracking SDKs. If a screen says it couldn't reach the server, wait a few seconds and tap Try again.

EACH FEATURE IN UNDER A MINUTE
1. Growing areas tab > New growing area. Name it Back fence, pick In-ground bed, type 84 in Headroom (inches), type a town in Address or place and tap the suggestion. Next (Outdoors and Full sun are set), Next, pick Feeds pollinators, Create. The area opens with good candidates, a care calendar and a forecast.
2. Tap Add a plant here, search Lady Fern and pick it: before saving, it says this spot gets more sun than its sources record. Search Basil instead and tap Save plant.
3. Plants tab > Basil. Under Log care, tap Watered; tomorrow its first check appears on the Checks for today card, with Watered and Still damp. Under Ask the Gnome, tap Get care advice (rule-based, with a Report this result link).
4. Plants tab > Walk the garden. Type: 12 tomatoes along the south fence, a rosemary by the gate. Tap Add these, then Add 2 to the garden.
5. Species tab: open any species for its facts, sources (they open in Safari) and hazard note. Older imported entries say they are not yet cited. The top card opens the Almanac.
6. Census tab: a summary of your garden. The community census (Settings > Privacy & data) is off by default.
Each permission is asked only on the tap that needs it: Use my location, the mic or camera in Walk the garden, Take photo, a reminder switch.

PHOTOS
Take photo and Choose photo in Add plant appear only on iPhones with Apple Intelligence turned on. The photo is read on the phone, never uploaded, and only suggests catalog matches to confirm. Photo check-ups and typed symptom reading are built but switched off, and the app hides both.

HAZARDS
Hazard and edibility notes come from their sources, mostly NC State Extension, and label any words of PlantAdvocate's own as its summary. A missing record reads as unknown, never as safe. Under each hazard note the app says: These notes repeat what the sources publish. They are not medical or veterinary advice.

CONTACT
Allison Bowman, +1 [FILL IN phone], support@plantadvocate.ai
```
Bytes: 3,881 of Apple's 4,000, counted on 30 October with the brackets in
place, from the first letter to the last, with nothing at either end. Every
character is ASCII, so bytes and characters are the same number. The block
has 33 line breaks; a browser form can send each one as two bytes, which
makes 3,914. Both counts are under 4,000, by 119 and 86 bytes, and stay under as long as each
bracket is replaced with text no longer than itself. A stray space or blank
line at either end adds to the count, so paste the block exactly.

## Where each part comes from

| Part | Code or record |
|---|---|
| About the app, and free | `docs/app-store/listing.md:119`; no purchase, ad or analytics library in `mobile/package.json` (`docs/go-to-market/product-truth.md`, sections 1 and 5) |
| Tested on | `docs/screenshots/1.1.3/README.md`, "How they were made": a Release simulator build of `3f6d7da` on two iOS 26.5 simulators, 23 October, against a local copy of the backend. Nothing on the ship branch has run on a phone yet (handoff, "What this build has NOT proven") |
| Region | Square feet and inches `mobile/src/growingAreas/realEstate.ts:163, 171`; Fahrenheit `mobile/src/care/facts.ts:159`; `POISON_CONTROL` in `garden-gnome/app/services/toxicity.py`, with "or your local poison centre" after it since 2026-10-30 (`LOCAL_POISON_CENTRE`); no localization in `mobile/src`; the National Weather Service is US-only (`weather.py`, `fetch_weather`), and Apple Weather and Open-Meteo come before and after it in the chain; photo matching is offered only when `SystemLanguageModel.default.availability` is `.available`, which Apple withholds where Apple Intelligence is restricted by region, hardware or Settings (`modules/plant-id/ios/PlantIdModule.swift:78-89`). Price is free in every territory (`listing.md:205`) |
| Account and My Home at first sign-in | `garden-gnome/app/routers/auth.py`, `_sign_in`, with `DEFAULT_ENV_NAME` at `auth.py:44`; a deleted account's leftover identity signs up fresh. My Home is indoor, sheltered, partial sun by the model defaults (`models.py:617-619`) |
| Welcome cards | Shown once, to an account with no plants (`mobile/App.tsx:222-241`); 4 cards (`mobile/src/onboarding/slides.ts`); Skip, Next, Add your first plant and Maybe later (`onboarding/Onboarding.tsx:24-25, 41-54`) |
| Deletion, with the Apple revoke | `mobile/src/screens/SettingsScreen.tsx:94-101, 220`; `garden-gnome/app/routers/auth.py`, `delete_me`, a hard delete of the plants, care logs, growing areas and user. A failed revoke never blocks deletion: the encrypted grant waits in `pending_apple_revocation` to be retried, and is deleted after 30 days or 10 tries, whichever comes first |
| The Almanac reads the account | `mobile/src/screens/AlmanacScreen.tsx:116-126` (the user's plants and growing areas), `:149` (the server's candidates for that area), `:86` ("you keep this one"); a species opened from an area reads it (`SpeciesDetailScreen.tsx:44-52`). Every species route wants a signed-in caller, as a default so that no new route ships open, not because a read needs the account (`garden-gnome/app/routers/species.py:21-30`) |
| Services | Weather chain `garden-gnome/app/services/weather.py:376-396`, credit `mobile/src/components/WeatherCredit.tsx`; Apple and Google sign-in `services/oauth/apple.py:29-32`, `services/oauth/google.py:15-16`; town search is `Location.geocodeAsync`, the phone's own geocoder (`mobile/src/location/lookup.ts:16-19`); Fly.io `garden-gnome/fly.toml`, `primary_region = 'iad'`. With every AI backend at `stub`, as production reports, the server calls no other outside service at run time; the Anthropic code paths in `advisor.py`, `catalog.py` and `vision.py` stay unused |
| A screen that couldn't reach the server | `mobile/src/care/loadFailed.ts:23, 30`; the client waits 15 s (`mobile/src/api/client.ts:122`) and sign-in 20 s (`mobile/src/auth/signIn.ts:23`); `fly.toml` has `min_machines_running = 0` unless decision 1 changes it |
| Step 1 | New growing area `GrowingAreasScreen.tsx:232`, Next and Create `:418`, lands on the new area `:174`; In-ground bed `realEstate.ts:18`, its Outdoors and Full sun preset `realEstate.ts:80`; Headroom `realEstate.ts:171`; Address or place, Use my location and the suggestion to tap `components/AddressPicker.tsx:79, 97, 100-106`; Feeds pollinators `realEstate.ts:66`; Good candidates `GrowingAreaDetailScreen.tsx:352`, care calendar `:437`, forecast and credit `:517-523` |
| Step 2 | Add a plant here `GrowingAreaDetailScreen.tsx:247`; the misfit before saving `AddPlantScreen.tsx:102, 409`, Save plant `:457`. On a scratch sync, Lady Fern in this bed reads "This spot gets 6+ hours of direct sun; sources record it for part shade, full shade." and Basil is a candidate with a water schedule of 1 to 2 days |
| Step 3 | Log care and Watered `PlantDetailScreen.tsx:52, 304`; Ask the Gnome and Get care advice `:327, 348`; Report this result `components/ReportResult.tsx:37`. A check is anchored to the last log of its care type (`mobile/src/care/schedule.ts`, `computeCareTasks`), or with nothing logged to the day the plant was added (`garden-gnome/app/routers/plants.py:107-108`); Checks for today, Watered and Still damp `care/CareTodos.tsx:148, 232, 242` |
| Step 4 | Walk the garden `PlantsScreen.tsx:151`; Add these and Add 2 to the garden `CaptureGardenScreen.tsx:309, 337`. Run through `splitUtterance` and `groundEntries` against a scratch catalog, the sentence gives 2 confident matches: 12 Tomatoes at south fence, 1 Rosemary at gate |
| Step 5 | Sources open with `Linking.openURL` (`components/CareFacts.tsx:118`); "From the catalog — not yet cited" `care/facts.ts:52`; the Almanac card `SpeciesScreen.tsx:150-163`; "more than 990" counts researched species (`listing.md:13-21`) |
| Step 6 | Census tab `CensusScreen.tsx`; the switch under Privacy & data `SettingsScreen.tsx:345-364`; off by default `models.py:268`; export and sync answer only the operator (`census.py`, `require_operator`) |
| Permissions | Location on Use my location `AddressPicker.tsx:62`; microphone and speech on the mic `CaptureGardenScreen.tsx:135`; camera on Turn the camera on `CaptureGardenScreen.tsx:312-315` and on Take photo `AddPlantScreen.tsx:251`; notifications on a reminder switch `SettingsScreen.tsx:153`, `notifications/reminders.ts:129-137`. Nothing asks at launch |
| Photo matching only with Apple Intelligence | `AddPlantScreen.tsx:140-141, 239-268`; `modules/plant-id/ios/PlantIdModule.swift:78-89` |
| Photo check-ups and symptoms hidden | `mobile/src/care/aiCapabilities.ts:45-55`; `PlantDetailScreen.tsx:329, 396`; production `/ai/status` on 23 October: every backend `stub`, vision `ready: false` |
| Hazards | `toxicity.py`, `describe`; no record never reads as safe (the no-record branches of `describe`); the summary label is `_summary_sentence` (2026-10-30). Of the 534 researched records with a `toxicity_detail` in `garden-gnome/app/data/verified/*.json`, 516 name NC State, counted on 24 October. The line under each hazard note is `NOT_ADVICE_LINE` in `mobile/src/care/notAdvice.ts`, shown by `components/NotAdviceNote.tsx` on species pages, plant pages and Add plant (the 2026-10-30 changes) |
