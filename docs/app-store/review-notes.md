# App Review Information for 1.2.0 (build 26)

App Store Connect > the 1.2.0 version page > App Review Information.
Checked on 2026-11-16 against `master` at `8379754`, the commit build 26 is
made from. `mobile/store.config.json` carries the same Notes under
`apple.review.notes`, so `eas metadata:push` sets them.

## Sign-In Information

PlantAdvocate signs in only with Sign in with Apple or Sign in with Google
(`mobile/src/auth/LoginScreen.tsx`). There is no password login, so there is
no demo account to give. Everything in the app sits behind sign-in
(`mobile/App.tsx`, `AuthGate`).

**Apple's rule.** Guideline 2.1(a) asks you to "include demo account info"
if the app has a login, and allows a built-in demo mode instead only with
Apple's prior approval. PlantAdvocate has neither, because a reviewer makes
a new account in one tap with their own Apple ID, and an Apple ID can't be
handed over as a demo login. The Notes say so in their SIGN-IN block. If App
Review still asks for an account, use the 2.1(a) reply in
[review-replies.md](review-replies.md) (check it against 1.2.0 first; it was
written for 1.1.3).

**The Sign-in required box.** The pulled `store.config.json` has
`demoRequired: true` with no user name or password, and I have left it so:
sign-in really is required. App Store Connect may refuse **Add for Review**
until the user name and password fields are filled. If it does, untick
Sign-in required (`demoRequired: false`) and rely on the SIGN-IN block of
the Notes, rather than entering placeholder text that can read as a broken
demo account. Never give out a personal Apple ID or Google login.

Before submitting, sign in once on the build with an Apple ID that has
never used PlantAdvocate, check that Home appears, then delete that account.
A reviewer's sign-in is a first authorization, the only time Apple sends
the person's name. The Notes also say Sign in with Google works. Nothing in
`docs/` records it being tried with a Google account that is not a listed
test user of the Google project; if Google refuses one, publish the consent
screen in Google Cloud, or change the first sentence of the SIGN-IN block
to "Sign in with Apple is the only sign-in." before pushing.

## Contact Information

Leave the contact fields exactly as they are in App Store Connect and in
`mobile/store.config.json`. The Notes no longer repeat them; Apple shows the
reviewer the contact fields beside the Notes.

## Notes

<!-- field limit=4000 bytes -->
```text
ABOUT THE APP
PlantAdvocate is an iPhone app for looking after the land and plants you grow at home. Add a yard in the United States and it estimates sun, where water collects, slope, soil, hardiness zone and frost dates from public maps, shows them on an aerial map, and plans the season. It also keeps growing spaces, plants, care checks and a cited species catalog. It is free, with no ads, no in-app purchases and no subscriptions.

REGION
Made for the United States: English, feet and Fahrenheit. The land maps and the National Weather Service cover only United States places, so please use a United States address.

SIGN-IN (no demo account exists)
Sign in with Apple and Sign in with Google are the only sign-ins. There is no username or password to give. Tap Sign in with Apple and use your own Apple ID. That makes a new, empty account at once, with 1 indoor growing space called My Home, then 4 welcome cards you can skip. Everything in the app is behind this sign-in. To delete the account: Settings > Account > Delete account > Delete forever.

SERVICES
Our server is on Fly.io in the United States. For land it asks the U.S. Department of Agriculture soil survey, the U.S. Geological Survey (elevation, land cover, aerial images) and a canopy height map hosted on Amazon Web Services about a block about 1,600 feet across that contains the pin, never the pin itself. Land forecasts come from the National Weather Service, with Apple Weather as a second opinion. Address search uses the iPhone's geocoder. No analytics, advertising or tracking software.

THE SERVER
The first request after an idle spell or a restart can take several seconds. If a screen says it couldn't reach the server, wait a few seconds and pull down or tap Try again. New land takes up to a few minutes to read; values fill in as they arrive.

A PATH THROUGH THE APP
1. Home > Add your land. Type 3501 New York Avenue NE, Washington, DC (the U.S. National Arboretum, a public place), tap the suggestion, then Next.
2. The aerial image shows a pin. Tap This is my home. On What's on your lot, tap Trees that drop their leaves and Lawn, then Save your land.
3. Tap See your report.
4. Home shows forecast bars, This week, The season ahead with a timeline, and Your land: the map with Aerial, Sun, Trees and Water chips, and reading tiles. A layer may say it is still being prepared; pull down to refresh after a minute.
5. Tap Everything about your land. Each value has a confidence label and Why and data source. Under Sun, tap a choice under Know better; the public estimate stays beside your answer.
6. Tap Draw zones on the map > Add a bed or area. Drag a box, tap Done drawing, pick Lawn or grass, tap Save.
7. Back on Home, tap The whole season: frost, freeze, leaf drop, dormancy and spring events, each with tasks and sources. Tap It happened here or Done on an event.
8. Home > Species: open a species for cited care facts, sources and hazard notes.
9. Home > Plants > Walk the garden. Type: 12 tomatoes along the south fence, a rosemary by the gate. Tap Add these.

PERMISSIONS
Nothing is asked at launch. Location: only on Use my location; typing an address needs none. Microphone and speech recognition: only on the mic in Walk the garden. Camera: only on Turn the camera on in Walk the garden, a live backdrop that is not recorded. Its prompt also mentions photo check-ups; they are off. Notifications: only when you turn on a care reminder or Frost and weather alerts in Settings.

SWITCHED OFF IN THIS VERSION
Identifying a plant from a photo, photo check-ups and free-text questions do not appear. We will submit a new version for review before offering them. The photo library is never asked for.

HAZARDS
Hazard notes come from their sources, mostly NC State Extension. A missing record reads as unknown, never as safe. Under each note the app says: These notes repeat what the sources publish. They are not medical or veterinary advice.
```
Characters: 3,938 of 4,000. Every character is ASCII, so bytes and
characters are the same number. The block has 33 line breaks; a form
that sends each as two bytes makes 3,971, still under 4,000.

There is no TESTED ON line, because the lead engineer is still checking
build 26 on the simulator. When that check passes, you can add this line
after the REGION block, with the simulator you used, for example
`TESTED ON` and then `iOS Simulator, iPhone 17 Pro, iOS 26.5.` on the next
line. It adds about 50 characters. Name only what build 26 actually ran on.

## What the reviewer sees, in order, and why each step works

| Step | What the reviewer sees | Code |
|---|---|---|
| Launch | The sign-in screen with Sign in with Apple and Sign in with Google. Nothing else is asked | `mobile/src/auth/LoginScreen.tsx`; `mobile/App.tsx`, `AuthGate` |
| First sign-in | A new account with 1 indoor growing space called My Home | `garden-gnome/app/routers/auth.py:45, 95` |
| Welcome cards | 4 cards, with Skip and Maybe later, shown once to an account with no plants | `mobile/App.tsx`, the onboarding effect; `mobile/src/onboarding/slides.ts`; `mobile/src/onboarding/Onboarding.tsx:24-25, 49-53` |
| Home with no land | A headline, This week, Your growing spaces, and the card "Have a yard or garden beds?" with Add your land | `mobile/src/screens/HomeScreen.tsx:360`; shown when the server sends `can_add_land` (`mobile/src/home/form.ts`, `offersAddLand`) |
| 1. Address | "Address or place (optional)" and Use my location. After 4 characters and a short pause the phone's geocoder offers one suggestion; tapping it sets the place, then Next | `mobile/src/components/AddressPicker.tsx:12-13, 81, 99, 103-106`; `PropertySetupScreen.tsx:150-157` |
| 2. Pin and lot | The aerial image with the pin at the address, This is my home, then What's on your lot with chips, Save your land or Skip | `PropertySetupScreen.tsx:196, 212, 225, 256-263`; labels `mobile/src/land/setup.ts:11-20` |
| 3. Reading | "Reading your land" with each step's state, then See your report | `PropertySetupScreen.tsx:281-296` |
| 4. Home with land | Forecast bars, This week, The season ahead with the timeline, Your land with the map, chips, legend and tiles | `HomeScreen.tsx:245, 292, 322, 347`; layer "still being prepared" text `garden-gnome/app/services/site/layers.py`, `NOT_READY_TEXT` |
| 5. Your land | Values with confidence labels, Why and data source, and "Know better? Tap what is true here" | `mobile/src/screens/LandScreen.tsx`; `mobile/src/land/CorrectionControl.tsx:42`; `mobile/src/components/explainedText.ts:28` |
| 6. Zone map | Draw zones on the map, Add a bed or area, Done drawing, What grows there (Lawn or grass), Save | `LandScreen.tsx:298`; `mobile/src/screens/ZoneMapScreen.tsx:339, 359-363, 573, 644`; `mobile/src/zones/describe.ts:11` |
| 7. Season | The whole season, then events with tasks, sources and It happened here or Done | `HomeScreen.tsx:311`; `mobile/src/season/sections.ts:22-31` |
| 8. Species | Home's Species link, then a species page with sources and hazard notes | `HomeScreen.tsx`, the quiet links; `mobile/src/components/CareFacts.tsx:106-124`; `mobile/src/care/notAdvice.ts` |
| 9. Walk the garden | "What's planted here?", Add these, then Add 2 to the garden | `mobile/src/screens/PlantsScreen.tsx:151`; `CaptureGardenScreen.tsx:272, 309, 337` |

The Arboretum is the public landmark the build spec uses for every live
check (38.9123, -76.9681; `docs/design/2026-11-15-overhaul-build-spec.md`
section 2). Its block has a 1 metre elevation survey and canopy data
(`docs/design/2026-11-15-sun-and-drainage-sources.md`), so the Sun, Trees and
Water layers can all be drawn there. Whether the phone's geocoder offers the
Arboretum for that typed address was not checked here (no live requests);
check it on the simulator.

## Permissions, and when each prompt appears

Nothing asks at launch.

| Prompt | When | What it is for | Code |
|---|---|---|---|
| Location, while using the app | Only on a tap of Use my location, in Add your land or a growing space | To find the land or the space from where the phone is. Typing an address needs no permission | `mobile/src/components/AddressPicker.tsx:63-64`; `mobile/src/location/permissions.ts:11-16`; string in `mobile/app.json`, `expo-location` |
| Microphone and speech recognition | Only on the mic in Walk the garden | To turn what is said into a plant list | `mobile/src/screens/CaptureGardenScreen.tsx:135`; strings in `mobile/app.json` |
| Camera | Only on Turn the camera on in Walk the garden | A live backdrop behind the list, not recorded or sent. The prompt's text in `mobile/app.json` also mentions photo check-ups, which are off in this build; the Notes say so | `CaptureGardenScreen.tsx:312-314`; strings in `mobile/app.json`, `expo-camera` and `expo-image-picker` |
| Notifications | Only on turning on a care reminder or Frost and weather alerts in Settings | Care reminders and frost alerts, scheduled on the phone | `mobile/src/screens/SettingsScreen.tsx:157-182`; `mobile/src/notifications/reminders.ts:200-207` |
| Photo library | Never in this build | Only photo identification and photo check-ups used it, and both are hidden | `mobile/src/photoId/entry.ts`; `mobile/src/care/aiCapabilities.ts` |

## What is switched off and not shown

- Identifying a plant from a photo: `PHOTO_ID_ENTRY_SHOWN = false`
  (`mobile/src/photoId/entry.ts`).
- Photo check-ups and free-text questions: the app reads `GET /ai/status`
  and hides both while the server reports `vision.ready: false` and the
  symptoms backend `stub` (`mobile/src/care/aiCapabilities.ts`). This was
  reported for production; I did not query it (no live requests).

## The server

`garden-gnome/fly.toml` on `master` sets `min_machines_running = 1`
(commit `2da6faa`, "Keep one machine awake through App Review"), but the
repository is not proof of what production runs: production was reported
to sleep when idle, and PLAN.md P0-11 says the deployed value has not been
recorded. Check `fly scale show` or `fly machine list` before submitting.
The Notes therefore say the first request after an idle spell or a
restart can take several seconds, which is true either way (a
deploy or a flag flip is a restart, PLAN.md section 9). The app retries a failed load once
(`mobile/App.tsx`, `retryOnceIfPassing`). Reading a new piece of land runs
a background step; the build spec's sources note measured 13 to 41 seconds
for a cold elevation request, so the Notes say "up to a few minutes".
