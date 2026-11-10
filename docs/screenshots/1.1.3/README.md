# App Store screenshots for 1.1.3

These follow `docs/app-store/screenshots.md`. They were shot on 2026-10-23 from the ship tip `3f6d7da` (branch `care-advice-honesty`, PR #22), and seven frames were retaken on 2026-10-24 after the check in `CHECK.md` and the °F fix. Every file is a portrait PNG with no alpha channel, checked with `sips -g pixelWidth -g pixelHeight -g hasAlpha`.

`17-pro-max/` is 1320 x 2868, for the iPhone 6.9" (Dynamic Island, large) size in App Store Connect. `17-pro/` is 1206 x 2622, for the iPhone 6.3" (Dynamic Island, medium) size. Upload each folder to its size in the order `docs/go-to-market/strategy.md` recommends, which is not file order: 01, 04, 06, then 02, 03, 05, 07, 08. The first three are what a searcher sees in the results list.

## The files

| File | What the frame shows | Caption |
|---|---|---|
| `01-needs-addressing.png` | Back fence bed, with "The space" and "Needs addressing" showing Chinese Wisteria (size, NC State Extension) and Lady Fern (sun, Royal Horticultural Society). The 17 Pro Max frame is the top of the page. The 17 Pro frame is scrolled a little, so the title card is cut off under the header and only its "Add a plant here" button shows; that is what lets both misfits fit. | See what doesn't suit each spot, and why. |
| `02-good-candidates.png` | Back fence bed scrolled to "Good candidates here", with the intro, the soil-depth note and the first candidates (6 on the 17 Pro Max, 5 on the 17 Pro), each with its "Confirmed here" line. | Plants that suit this spot, backed by sources. |
| `03-check-before-planting.png` | Add plant from Back fence bed, with Lady Fern picked and the "Worth knowing before it goes in Back fence bed" box (sun, Royal Horticultural Society) under the area buttons. The search field sits right under the header. Not saved. | Check the spot before you plant, not after. |
| `04-checks-not-chores.png` | Plants tab, with the streak badges, "Checks for today" (Check Basil and Check Boston Fern, each with Watered and Still damp), the "2 plants have no check schedule" line and the plant cards below. | A check, not a chore: look, then log. |
| `05-cited-care-facts.png` | Species > Snake Plant, with the cited care facts, "From the catalog — not yet cited" with TEMP 60–85°F, Care notes, and Sources (Clemson Cooperative Extension, NC State Extension, Royal Horticultural Society). | Each cited fact names the source behind it. |
| `06-hazards-stated-plainly.png` | Species > Pothos, with the whole hazard sentence: cats, dogs and people; all parts; NC State's rating for people; Poison Control. | Harm to people and pets is stated plainly. |
| `07-almanac-narrowed.png` | Species Almanac with "Fits Kitchen windowsill" picked and "Basil" in its search, so the list shows Basil, "Confirmed here: indoors or out" and "✿ you keep this one". | Narrow the catalog to what fits your space. |
| `08-walk-the-garden.png` | Walk the garden with the sentence typed and Add these tapped: 2 confirmed cards, "12 tomatoes along the south fence" (How many 12, Tomatoes, south fence) and "a rosemary by the gate" (How many 1, Rosemary, gate), and "Add 2 to the garden", not tapped. | Walk the garden and say what is growing. |

## What was retaken on 2026-10-24, and why

Seven frames were captured again: `17-pro-max/02`, `03`, `05` and `07`, and `17-pro/03`, `05` and `07`. The other nine are the 2026-10-23 captures, unchanged.

`17-pro-max/02` and `17-pro/05` had a black Dynamic Island pill in the status bar. The status bar override was not the cause: `simctl status_bar list` reads 9:41, full signal, Wi-Fi and a full battery on both simulators. The pill comes and goes on its own. In a test of 26 back-to-back captures of an unchanging screen, 1 came out with it, at a moment when nothing else was touching the simulator. The simulator's log shows SpringBoard taking and dropping a "System Aperture Complete Suppression Assertion" around every capture, which is how a screenshot hides the island, so the likely cause is a capture that now and then lands before the island is hidden. The capture script now checks the island area of every frame and takes it again if the pill is there, and every file in both folders was checked for it afterwards.

`17-pro/03` showed the photo-identification hint and the bottoms of the Take photo and Choose photo buttons, and `17-pro-max/03` showed half a line of the same hint. The page was too short to scroll the hint away with only one search result, so the search reads "Lady" and Lady Fern is picked from its four results (Lady Banks Rose, Lady Fern, Lady Palm, Lady's Mantle). That makes the page long enough to put the search field right under the header on both sizes, with no photo-identification text or buttons in view.

Both `05` frames showed the temperature as "60–85°f". The cause was `textTransform: 'capitalize'` in `mobile/src/components/CareFacts.tsx`, which lowercases the rest of each word on iOS. The fix on this branch capitalizes in code instead (`mobile/src/care/facts.ts`, `CareFacts.tsx`, `SpeciesDetailScreen.tsx`), and the retaken frames, built with it, read "60–85°F". The name "Snake Plant" is not in either frame. With the hazard sentence above the facts, the page from the name to the last source is taller than either screen, and the shot list needs the facts and the Sources card together. On the 17 Pro the Care facts heading and its watering row are above the frame, which starts cleanly at the Light row, so all three sources fit.

Both `07` frames failed because Basil, which ranks 108th of 206 in the "Fits Kitchen windowsill" list, was not in view, and the "My Home" chip was cut to "ome". The new frames type "Basil" into the Almanac's search with the Kitchen windowsill filter still on, and scroll the area chips so that "Fits My Home" shows whole. The two chips cannot all fit at once, so the picked chip is cut at the right edge: it reads "✓ Fits Kitchen w" on the 17 Pro Max and "✓ Fits Kitc" on the 17 Pro. The note under the count names Kitchen windowsill in full. The lower part of each frame is empty, because the search leaves one species. These replace the old `alternates/` shots, which showed the same search with the chip cut, so that folder is gone.

Shot 6 needed no retake for the °F fix. Pothos's temperature is a cited fact, shown as "Days 70–85°F; nights 60–70°F" by a row the fix didn't touch.

## The checks the shot list asks for

Shot 2: none of mayapple, taro, wisteria, foxglove, English yew, monkshood or jimsonweed is among the candidates. The first 20 were checked through the API, and every name in both frames was read: African Blue Lily, Ageratum, Allegheny Monkey Flower, American Alumroot, American Blue Vervain and American Boneset. No food crop with a warning line is in frame.

Shot 4: exactly Basil and Boston Fern are due. The card also says 2 plants have no check schedule for their species, and that line is in frame on both sizes.

Shot 6: the severity word belongs to people. NC State is named as rating it "for people", and pets are named only as "toxic to". Pothos is rated "medium", so the word "Seriously" doesn't appear.

## What differs from the shot list

Shot 6 shows Pothos, not Dumb Cane. Dumb Cane's hazard sentence reads correctly, but its Care notes card showed mojibake ("â€"" where a dash belongs). At `3f6d7da`, `garden-gnome/app/data/species_catalog.json` has 25 such sequences across 14 species, among them Boston Fern, Dumb Cane, Jade Plant and Bird of Paradise. The working tree of this branch has a change to that file that removes all 25, but the backend these shots used was seeded from `3f6d7da`, before it. The shot list allows Pothos.

Shot 7 has "Basil" typed into the Almanac's search, which the shot list doesn't ask for. Without it, Basil sits far down the narrowed list (see above).

Shot 3's search reads "Lady" rather than "Lady Fern", for the reason above. Lady Fern is the species picked, and the misfit box is for Lady Fern.

The account also has "My Home". Every new account gets a default "My Home" growing area at sign-in (`garden-gnome/app/routers/auth.py`). It was kept so the shots match a real account, and it shows as a button in shot 3 and as a chip in the Almanac's area row.

The "Ask the Gnome" alternate was not captured, because shots 6 and 7 were both usable.

## How they were made

These were taken against a local copy of the backend, not production, from a scratch worktree at `3f6d7da`. The backend ran on 127.0.0.1:8000 with a database built by `python -m app.data.seed` and throwaway JWT and Fernet keys. The "Demo Gardener" account was made with the backend's own sign-in helper (`_sign_in`) under a made-up Google subject, and its tokens were minted with `app.services.tokens`, with a 60-day access token so neither simulator needed a refresh.

The garden was built through the API with FastAPI's TestClient, following the shot list. Back fence bed is an in-ground bed of 24 sq ft with 84 in of headroom and 18 in of soil depth, in Raleigh, NC, outdoors, exposed and in full sun, set to feed pollinators, with Lady Fern, Chinese Wisteria and Rosemary. Kitchen windowsill is a windowsill, indoors, sheltered and in partial sun, with no goals, holding Basil, Boston Fern and Snake Plant. The rows were then backdated in SQLite: plants added 2026-10-21, Boston Fern watered 2026-10-21 and Basil watered 2026-10-22.

Two app patches stayed local to the scratch worktree. `mobile/src/api/baseUrl.ts` reads the API address from `EXPO_PUBLIC_SHOOT_API_URL`, and `mobile/src/auth/tokenStorage.ts` stores the demo session from `EXPO_PUBLIC_SHOOT_USER`, `EXPO_PUBLIC_SHOOT_ACCESS` and `EXPO_PUBLIC_SHOOT_REFRESH` when the keychain holds none. Those values were in `mobile/.env.local`. Nothing from the scratch worktree was committed, and no real Apple or Google account was used. For the 2026-10-24 retake, the four files of the °F fix were copied into the scratch worktree, which carried no shoot patch in them, and the app was rebuilt.

The build is a Release simulator build from `npx expo prebuild --platform ios --clean`, `pod install` and `xcodebuild`, so no dev menu, LogBox or backend card can appear. The generated Info.plist already allows local networking.

Both simulators run iOS 26.5: "PA Shoot 17 Pro Max" and "PA Shoot 17 Pro". The iOS 27.0 runtime crashed the Release build at launch inside UIKit's scene-lifecycle check (`_UIApplicationEvaluateRuntimeIssueForNoSceneLifecycleAdoption`), so 1.1.3 as built doesn't launch on iOS 27 simulators. That is worth checking on a device before release.

The status bar was set with `simctl status_bar override` (9:41, full signal and battery). Each shot was captured with `simctl io screenshot --mask=ignored`, checked for the island pill, re-saved as RGB with Pillow and checked with `sips`. Every frame was looked at before it was kept.

These were shot on the simulator against a local backend, but they show the same 1.1.3 build and the same garden the shot list describes. To shoot against production with a demo account of your own, the shot list's steps still apply.
