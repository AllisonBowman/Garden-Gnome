# Screenshots for 1.1.3

1.1.3 is iPhone only (`ios.supportsTablet` false in `mobile/app.json`), so
App Store Connect asks for no iPad screenshots. If the build still says
`true`, it will ask for 13-inch iPad shots as well. Fix the build rather
than shooting them.

## Sizes

Apple's "Screenshot specifications" page, as it read on 15 October 2026:

- **Required:** at least 1 screenshot for **iPhone with Dynamic Island
  (medium display)**: iPhone 18 Pro, 17 Pro, 17, 16 Pro, 16, 15 Pro, 15 and
  14 Pro. Accepted sizes are 1206 × 2622 or 1179 × 2556 portrait, and
  2622 × 1206 or 2556 × 1179 landscape.
- **6.9-inch, which Apple now calls iPhone with Dynamic Island (large
  display):** iPhone Air, 18 Pro Max, 17 Pro Max, 16 Pro Max, 16 Plus, 15
  Pro Max, 15 Plus and 14 Pro Max. Accepted sizes are 1320 × 2868,
  1290 × 2796 or 1260 × 2736 portrait, and 2868 × 1320, 2796 × 1290 or
  2736 × 1260 landscape. It is no longer required, but it is what the
  largest iPhones show, so upload it too.
- Up to 10 per size, as `.png`, `.jpg` or `.jpeg`, with no alpha channel or
  transparency.

So shoot the list below twice, on 2 simulators, and upload each set to its
own size:

| Simulator | Screenshot size | App Store Connect size |
|---|---|---|
| iPhone 17 Pro Max | 1320 × 2868 | iPhone 6.9" (Dynamic Island, large) |
| iPhone 17 Pro | 1206 × 2622 | iPhone 6.3" (Dynamic Island, medium) |

All portrait. The app is locked to portrait (`mobile/app.json`
`orientation`).

## The demo account

Use an account made for the screenshots, not your own. Its name and email
appear only in Settings, which is not in the list. The growing areas and
plants live on the server, so the second simulator shows the same garden
after signing in.

Set this up against production, after the 1.1.3 backend is deployed.
Since `7dac70d` the server dates a plant the day it's added, and with
nothing logged its first check counts from that day
(`mobile/src/care/schedule.ts`, `computeCareTasks`). The plan below adds
everything 2 days ahead and logs water on chosen days, so that exactly
Basil and Boston Fern are due on the day: Rosemary (every 7 to 14 days)
and Snake Plant (every 14 to 21) aren't due yet, and Lady Fern and Chinese
Wisteria have no check schedule.

**2 days before the shoot:**

A new account opens with the first-run tips. Tap Skip.

1. Growing areas tab > New growing area. Name **Back fence bed**, In-ground
   bed, Footprint 24, Headroom 84, Soil depth 18, and a place (a town
   search is enough). Next: leave Outdoors, Exposed, Full sun. Next: tick
   Feeds pollinators. Create.
2. On Back fence bed, Add a plant here 3 times: **Lady Fern**, **Chinese
   Wisteria**, **Rosemary**.
3. New growing area: **Kitchen windowsill**, Windowsill, no measurements,
   the same place. Leave Indoors, Partial sun. No goals. Create.
4. On Kitchen windowsill, add **Basil**, **Boston Fern** and **Snake Plant**.
5. Open Boston Fern and tap Watered.

**1 day before the shoot:** open Basil and tap Watered.

**On the day:** Basil (water every 1 to 2 days) and Boston Fern (every 2 to
4 days) are both due, so the Plants tab shows 2 checks.

These species were checked on a scratch sync of the catalog at `b083a90`.
Lady Fern misfits a full-sun bed on sun. Chinese Wisteria outgrows 84 in of
headroom ("climbs to 25 ft and there is 7 ft of headroom"). Basil, Boston
Fern and Snake Plant have care schedules. Basil, Boston Fern, Rosemary and
Snake Plant have no edible-and-toxic conflict to show.

## The shot list

Shoot in this order and upload in this order. Each caption is 8 words, for
the text over the screenshot if you frame them. Captions aren't an App
Store Connect field.

### 1. What doesn't suit a spot

Screen: Growing areas > Back fence bed, top of the page.

Set up: "The space" card and "Needs addressing" in view, showing Lady Fern
(sun) and Chinese Wisteria (headroom), each with its reason and source.

<!-- field limit=8 unit=words exact -->
```text
See what doesn't suit each spot, and why.
```
Words: 8 of 8.

### 2. Good candidates

Screen: Back fence bed, scrolled to "Good candidates here".

Set up: the list intro and 3 or more candidates in view, each with its
confirmed line. Before shooting, read every visible name. A source's
serious poison for people is never a candidate unless it is a food crop
eaten without conditions (potato, eggplant, peanut, tomatillo and butter
bean can appear, each with its hazard line). If mayapple, taro, wisteria,
foxglove, English yew, monkshood or jimsonweed shows, the exclusion isn't
in the build: don't shoot it, and say so. A food crop with a warning line
is true, but scroll it out of frame if it would lead the shot.

<!-- field limit=8 unit=words exact -->
```text
Plants that suit this spot, backed by sources.
```
Words: 8 of 8.

### 3. The check before planting

Screen: Back fence bed > Add a plant here.

Set up: search Lady Fern and pick it, so the misfit box shows under the
area buttons. Don't save. Go back afterwards.

<!-- field limit=8 unit=words exact -->
```text
Check the spot before you plant, not after.
```
Words: 8 of 8.

### 4. Checks, not chores

Screen: Plants tab.

Set up: the streak badges and the "Checks for today" card with Check
Basil and Check Boston Fern, each offering Watered and Still damp, with
the plant cards below. The card also says 2 plants have no check schedule
for their species (Lady Fern and Chinese Wisteria). That line is true; keep
it in if it fits, or let it fall below the frame.

<!-- field limit=8 unit=words exact -->
```text
A check, not a chore: look, then log.
```
Words: 8 of 8.

### 5. Cited care facts

Screen: Species tab > Snake Plant.

Set up: the care facts and the Sources card in view together. Snake Plant
is cited to NC State Extension and others. Its page may also show an older
value under "From the catalog — not yet cited". That label is the app
being honest, so it can stay in frame, and it is why the caption says
"each cited fact" rather than "every fact".

<!-- field limit=8 unit=words exact -->
```text
Each cited fact names the source behind it.
```
Words: 8 of 8.

### 6. Hazards, stated plainly

Screen: Species tab > Dumb Cane (Dieffenbachia), a common houseplant whose
cited record names people and pets, carries NC State's high Poison Severity
rating, which is a rating for people, and names the parts. Pothos or Peace
Lily also work; English Yew and Castor Bean do not, because their records
name no parts on this build.

Set up: the hazard sentence in view, naming people, pets, the parts, the
rating and the Poison Control line. The severity word ("Seriously") belongs
to people; pets are named as "toxic to" them unless the record says more.
If the sentence reads as if NC State rated the hazard to pets, don't shoot
it, and say so. If the sentence is cut off, scroll it fully into view
before shooting.

<!-- field limit=8 unit=words exact -->
```text
Harm to people and pets is stated plainly.
```
Words: 8 of 8.

### 7. The Almanac, narrowed to a space

Screen: Species tab > the "What suits one of your spaces" card > the
Species Almanac.

Set up: tap the "Fits Kitchen windowsill" chip. The list shows that area's
candidates, with Basil marked as one you keep.

<!-- field limit=8 unit=words exact -->
```text
Narrow the catalog to what fits your space.
```
Words: 8 of 8.

### 8. Walk the garden

Screen: Plants tab > Walk the garden.

Set up: type `12 tomatoes along the south fence, a rosemary by the gate`
and tap Add these, so 2 confirmed cards and "Add 2 to the garden" show.
Don't tap it. On the simulator the backdrop is plain, which is fine.

<!-- field limit=8 unit=words exact -->
```text
Walk the garden and say what is growing.
```
Words: 8 of 8.

### Alternate: Ask the Gnome

Use this in place of shot 6 or 7 if you'd rather show the advice.

Screen: Plants tab > Basil > Ask the Gnome > Get care advice.

Set up: the advice and its "rule-based" pill in view.

<!-- field limit=8 unit=words exact -->
```text
Ask the Gnome: advice from facts and history.
```
Words: 8 of 8.

## Never in a screenshot

- Settings. It shows the account's name and email. A development or
  preview build also shows the Backend connection card
  (`mobile/src/screens/SettingsScreen.tsx:252-294`).
- Photo identification. It needs Apple Intelligence, and the listing
  doesn't lead with it.
- A photo check-up or symptom box. They are hidden in production anyway.
- Any loading spinner or error screen.

## Building and capturing on the simulator

Use a Release build, so no developer menu, Metro banner, backend card or
debug text can appear. These commands run from the main checkout on this
Mac. Don't use `mobile/scripts/sim-build.sh`: it resets the checkout to
another branch. `--clean` deletes and regenerates `mobile/ios/`, which git
ignores, so only local edits there are lost.

Don't reuse `docs/screenshots/`. Those are July development captures, and
one of them shows the photo check-up this version hides.

```sh
cd ~/Developer/Garden-Gnome/mobile

# Regenerate ios/ from app.json, so the build is iPhone only and has the new icon.
npx expo prebuild --platform ios --clean

xcodebuild -workspace ios/PlantAdvocate.xcworkspace -scheme PlantAdvocate \
  -configuration Release -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro Max' \
  -derivedDataPath /tmp/pa-shots-build build

APP=/tmp/pa-shots-build/Build/Products/Release-iphonesimulator/PlantAdvocate.app
```

If either simulator is missing, `xcrun simctl list devicetypes | grep "iPhone 17"`
shows its type, and `xcrun simctl create "iPhone 17 Pro Max" <that type id>`
makes one.

For each of the 2 simulators:

```sh
# First set on "iPhone 17 Pro Max"; repeat with "iPhone 17 Pro" for the second set.
xcrun simctl boot "iPhone 17 Pro Max"
open -a Simulator
xcrun simctl install booted "$APP"
xcrun simctl launch booted com.allisonbowman.plantadvocate

# A clean status bar: 9:41, full signal, full battery.
xcrun simctl status_bar booted override --time 9:41 \
  --dataNetwork wifi --wifiMode active --wifiBars 3 \
  --cellularMode active --cellularBars 4 \
  --batteryState charged --batteryLevel 100

mkdir -p ~/Desktop/pa-shots/6.9 ~/Desktop/pa-shots/6.3
```

Sign in to the demo account in the app. Sign in with Apple on the simulator
needs the simulator itself signed in to an Apple Account (its Settings app).
Then set up each screen and capture it:

```sh
xcrun simctl io booted screenshot --type=png --mask=ignored ~/Desktop/pa-shots/6.9/01-needs-addressing.png
```

`--mask=ignored` saves the whole rectangle, with no transparent rounded
corners. Name the files `01-…` to `08-…` so they sort in upload order, and
put the iPhone 17 Pro set in `6.3/`.

Check every file before uploading:

```sh
sips -g pixelWidth -g pixelHeight -g hasAlpha ~/Desktop/pa-shots/*/*.png
```

The 6.9 set must read 1320 × 2868 and the 6.3 set 1206 × 2622. If any file
says `hasAlpha: yes`, convert it to JPEG, which has no alpha:

```sh
sips -s format jpeg -s formatOptions 92 in.png --out in.jpg
```

When you're done, `xcrun simctl status_bar booted clear` puts the real
status bar back.

In App Store Connect, open the 1.1.3 version, go to the iPhone screenshot
sizes under Previews and Screenshots, and drag each set onto its size in
order.
