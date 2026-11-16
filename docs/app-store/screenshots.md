# Screenshots for 1.2.0 (build 26)

1.2.0 is iPhone only and portrait only (`mobile/app.json`:
`ios.supportsTablet` false, `orientation` portrait), so App Store Connect
asks for no iPad screenshots. The new land features come first: a searcher
sees the first three in the results list.

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

## The screenshot account

Use an account made for the screenshots, not your own: its name and email
show in Settings, which is not in the list. Land, zones and plants live on
the server, so the second simulator shows the same account after signing in.

Set it up against production with both feature flags on, the day before the
shoot, so the background reading and the map layers have finished. Use a
public place, never a home address. The U.S. National Arboretum is the
build spec's test landmark, and its block has the 1 metre elevation survey
and canopy data that all 3 layers need
(`docs/design/2026-11-15-sun-and-drainage-sources.md`).

1. Sign in. On the welcome cards tap Skip.
2. Home > Add your land. Type `3501 New York Avenue NE, Washington, DC`,
   tap the suggestion, Next. Leave the pin where the search put it, or
   move it onto open ground, then This is my home. Tap Trees that drop their
   leaves, Lawn and Garden beds, then Save your land, then See your report.
3. Home > Everything about your land > Draw zones on the map. Add 3 zones
   with Add a bed or area: a box over open lawn (Lawn or grass), a box over a
   stand of trees (Trees, then Loses its leaves in fall), and a small box named
   `Vegetable bed` (Garden bed). Save each.
4. Home > All growing spaces (or Add a growing space) > the zone or space
   of your choice > Add a plant here: add **Basil** and **Tomato**, so This
   week has care in it. Optional.
5. Next day, open Home and pull down once. Check that Your land no longer
   says the map is being prepared, and that the Sun, Trees and Water chips
   are all enabled. If one says it is still being prepared, wait and pull
   again. If one says it is unavailable, shoot the others and say so.

Name the land in Your land > This property, for example `Arboretum test`.
The place line on Home shows the land's name and town
(`mobile/src/screens/HomeScreen.tsx`, `placeLine`).

## The shot list

Shoot and upload in this order. Each caption is 8 words or fewer, for the
text over the screenshot if you frame them; captions are not an App Store
Connect field. Every caption describes what the shot shows, and none
promises accuracy.

| # | File | Screen | State it must be in | Caption |
|---|---|---|---|---|
| 1 | `01-home-forecast.png` | Home, top | The headline, the place line, and the Weather section with the forecast bars in full: each day's high and low, the 32 °F line if it falls in range, any frost nights marked, and the "Forecast: National Weather Service." credit. If the forecast is missing, wait and pull down; never shoot an empty Weather section | Today's weather and frost nights, at a glance. |
| 2 | `02-home-land-map.png` | Home, scrolled to Your land | The land map on the Aerial chip, with the pin and the 3 zone boxes and labels, the chips row, and the reading tiles (sun hours, hardiness zone, where water collects, topsoil) with their confidence labels. No "still being prepared" line | Your land, read from public maps. |
| 3 | `03-land-sun-layer.png` | Home > Everything about your land | The map with the Sun chip on, its legend (from "Under tree canopy" to "9 hours or more, full sun") and its notes ("Buildings are not counted." among them) in view | Where the sun falls in the growing season. |
| 4 | `04-land-water-layer.png` | Your land | The Water chip on, with both legend steps ("runs through" and "collects") and the note "This is not a flood insurance determination." If the Water layer is unavailable at this spot, use the Trees chip instead and name the file `04-land-trees-layer.png` | Where water collects and runs after rain. |
| 5 | `05-season-timeline.png` | Home > The whole season | The forecast bars and "The year at a glance" timeline with today marked, and the first event card below it with its status pill and tasks | Frost, leaf drop and spring, on one timeline. |
| 6 | `06-zone-map.png` | Your land > Open the zone map | The aerial image with the 3 zone boxes and labels, and the Zones list under it with Add a bed or area | Draw a box over each bed, then describe it. |
| 7 | `07-species-care-facts.png` | Home > Species > Snake Plant | The care facts and the Sources card together, sources named. A line labelled not yet cited may show and can stay | Care facts cited to the sources behind them. |
| 8 | `08-species-hazards.png` | Species > Dumb Cane (Dieffenbachia) | The hazard sentence in full, naming people and pets, NC State's severity rating for people, and the parts, with the line "These notes repeat what the sources publish. They are not medical or veterinary advice." under it. If the sentence reads as if NC State rated the hazard to pets, don't shoot it, and say so | Harm to people and pets, stated plainly. |

Why this order: shots 1 to 6 are what is new in 1.2.0 and what the
subtitle promises; 7 and 8 are the plant features that carry over. If you
want a ninth or tenth, add Walk the garden (Plants > Walk the garden, type
`12 tomatoes along the south fence, a rosemary by the gate`, tap Add these,
don't tap Add 2 to the garden) as `09-walk-the-garden.png`.

Before shooting each screen, check that nothing on it is a loading spinner,
an error line, or a "still being prepared" note.

## Never in a screenshot

- Settings. It shows the account's name and email. A development or
  preview build also shows the Backend connection card.
- Any home address or a pin on a private home. Use the Arboretum.
- Photo identification, a photo check-up or a symptom box. They are hidden
  in this build and must not appear in the listing.
- Any loading spinner, error screen or empty section.

## Building and capturing on the simulator

Use a Release build, so no developer menu, Metro banner, backend card or
debug text can appear. Build from the commit build 26 was made from. Don't use
`mobile/scripts/sim-build.sh`: it resets the checkout to another branch.
`--clean` deletes and regenerates `mobile/ios/`, which git ignores.

The 1.2.0 set uploaded on 2026-11-16 was captured on an iPhone 17 simulator
(1206 x 2622) from a Release build pointed at a local test server holding the
National Arboretum as its land, because the simulator cannot Sign in with Apple
without the owner's Apple ID.

```sh
cd mobile

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
xcrun simctl io booted screenshot --type=png --mask=ignored ~/Desktop/pa-shots/6.9/01-home-forecast.png
```

`--mask=ignored` saves the whole rectangle, with no transparent rounded
corners. Name the files `01-…` to `08-…` so they sort in shot order, and
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

In App Store Connect, open the 1.2.0 version, go to the iPhone screenshot
sizes under Previews and Screenshots, and add each set to its size in file
order, 01 to 08. Or copy them into `mobile/store/apple/screenshot/en-US/`
under each size's folder and replace the `screenshots` list in
`mobile/store.config.json` with the new file names before
`eas metadata:push`. The list there today names the 1.1.3 files.
