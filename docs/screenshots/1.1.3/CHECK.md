# Check of the 1.1.3 screenshots

Checked on 2026-10-24 against `docs/app-store/screenshots.md`, after seven frames were retaken that morning. This replaces the check of 2026-10-23. I didn't edit any images.

**Result: no file fails.** All 16 files pass: 8 in `17-pro-max/` and 8 in `17-pro/`. The `alternates/` folder no longer exists, and nothing else is in the screenshot folders. Six of the passes, shots 3, 5 and 7 on both sizes, carry a weakness worth knowing about before upload. They are set out under those shots. None breaks a rule in the shot list, and each is disclosed in the README.

**Sizes and alpha: pass.** `sips -g pixelWidth -g pixelHeight -g hasAlpha` reads 1320 x 2868 for every file in `17-pro-max/` and 1206 x 2622 for every file in `17-pro/`, all RGB PNG with `hasAlpha: no`. Both sets have the same 8 shots in the same order, 01 to 08.

**Status bar: pass on all 16.** Every frame shows 9:41, four signal bars, full Wi-Fi and a full green battery with the charging bolt, which is how the simulator draws the `charged` state the override sets. There is no location arrow or other indicator. I looked for the Dynamic Island pill in two ways: by eye, on a strip of all 16 status bars side by side, and by counting near-black pixels across the middle 40% of the top 200 pixel rows of each file. No row in any file has a single near-black pixel there, so the pill is in none of them, including the retaken `17-pro-max/02` and `17-pro/05`. The top-left corner of every frame still has 9 near-black pixels, as on 2026-10-23. That can't be seen and isn't a fail.

**Never in a screenshot: pass on all 16.** None shows photo identification, a photo check-up or symptom box, the Settings screen, an account name or email, a dev menu, LogBox, a Metro banner, a backend card, "localhost", "127.0.0.1", "stub", a raw id, an error or a spinner. The tab bar's Settings tab shows in every frame, but that is the tab, not the screen. The "Turn the camera on" line in shot 8 belongs to Walk the garden, where the camera is only a backdrop (`mobile/src/screens/CaptureGardenScreen.tsx` says it does no identifying), so it isn't photo identification.

**Text: pass on all 16.** Nothing is garbled: every dash, curly apostrophe, degree sign and emoji renders as it should, and shot 5 reads "60–85°F" with a capital F on both sizes. Two kinds of truncation are the app's own layout, not capture faults: on the 17 Pro the tab bar reads "Growing are…" in every frame, and in `17-pro/03` the first condition button reads "Excelle…".

## Shot 1: What doesn't suit a spot

**`17-pro-max/01-needs-addressing.png`: pass.** Back fence bed at the top of the page, with the title card, "The space" card and "Needs addressing" in view. Chinese Wisteria shows its size misfit (NC State Extension, "climbs to 25 ft and there is 7 ft of headroom"), and Lady Fern its sun misfit (Royal Horticultural Society), each with its reason.

**`17-pro/01-needs-addressing.png`: pass.** The same content, scrolled a little so that only the title card's "Add a plant here" button shows under the header. That isn't quite "top of the page", but it is what fits both misfits on the smaller screen, and the README now says so.

## Shot 2: Good candidates

**`17-pro-max/02-good-candidates.png`: pass.** This is the retaken frame, and its status bar is now clean. "Good candidates here" is in view with its intro (418 species) and the soil-depth note, then 6 candidates: African Blue Lily, Ageratum, Allegheny Monkey Flower, American Alumroot, American Blue Vervain and American Boneset. The first five show their "Confirmed here" line, and the sixth is cut by the tab bar after its "Toxic to people." line. None of mayapple, taro, wisteria, foxglove, English yew, monkshood or jimsonweed shows, and none is in the first 20 candidates the rig saved from the API. No food crop leads. The list opens on African Blue Lily with "Toxic to people.", which is true, and isn't a food crop, so the shot list's scrolling rule doesn't apply.

**`17-pro/02-good-candidates.png`: pass.** The same intro and note, and the first 5 of those candidates. American Blue Vervain's confirmed line is cut by the tab bar. No excluded species shows.

## Shot 3: The check before planting

**`17-pro-max/03-check-before-planting.png`: pass.** Add plant from Back fence bed. The search field sits right under the header, and at full size nothing shows above it: no photo-identification hint, and no Take photo or Choose photo button. Lady Fern is picked from four results, its no-toxicity-verdict note shows, Back fence bed is the selected area, and the "Worth knowing before it goes in Back fence bed" box (sun, Royal Horticultural Society) is under the area buttons. Save plant is in view and hasn't been tapped.

**`17-pro/03-check-before-planting.png`: pass.** This is the retaken frame, and the photo-identification text and buttons that failed it on 2026-10-23 are gone. The content matches the Pro Max frame, with the misfit box in full.

The weakness in both: the search reads "Lady", not "Lady Fern", and four results show (Lady Banks Rose, Lady Fern, Lady Palm, Lady's Mantle). The shot list says to search Lady Fern and pick it. The picked chip and the misfit box make it plain which species is chosen, and the README explains why: with one result the page was too short to scroll the photo hint away. I'd take that trade.

## Shot 4: Checks, not chores

**`17-pro-max/04-checks-not-chores.png`: pass.** My Plants, with the 3-day care streak and badges (3 of 6). "Checks for today" has a count of 2: Check Basil and Check Boston Fern, each with Watered and Still damp. The "2 plants have no check schedule" line is in frame, and the Lady Fern and Chinese Wisteria cards (with its Pet caution chip) are below.

**`17-pro/04-checks-not-chores.png`: pass.** The same elements, including the no-schedule line. The Lady Fern card shows, and Chinese Wisteria is cut by the tab bar.

## Shot 5: Cited care facts

**`17-pro-max/05-cited-care-facts.png`: pass.** This is Snake Plant's page, retaken. In view are the Care facts card (Watering, Light, Humidity, Soil, Mature size), "From the catalog — not yet cited" with TEMP "60–85°F", Care notes, and the Sources card with Clemson Cooperative Extension, NC State Extension and the Royal Horticultural Society. The capital F is right.

**`17-pro/05-cited-care-facts.png`: pass.** Retaken, with a clean status bar and "60–85°F". The frame starts cleanly at the Light row: the "Care facts" heading and the Watering row are above it. Light, Humidity, Soil and Mature size, the not-yet-cited card, Care notes and all three sources are in view.

The weakness in both: nothing in the frame says which plant this is. The name "Snake Plant" and its "Care facts cited to …" line are scrolled away, and the header just says "Species". The shot list asks only for the facts and the Sources card together, and they are, so this isn't a fail. The README explains that the page from the name to the last source is taller than either screen. If a caption is laid over the screenshot, "Each cited fact names the source behind it." is fair to the app as a whole, but in this frame the facts and the sources are in separate cards and no row names its own source.

## Shot 6: Hazards, stated plainly

**`17-pro-max/06-hazards-stated-plainly.png`: pass.** Species > Pothos (*Epipremnum aureum*), which the shot list allows. The name, "Care facts cited to Clemson Cooperative Extension and 1 more" and the whole hazard sentence are in view. The sentence names cats, dogs and people, all parts (calcium oxalate crystals), says "NC State Extension rates its poison severity for people medium", and ends with Poison Control (US 1-800-222-1222) or a vet. The rating belongs to people, and pets are named only as "toxic to". Pothos is rated medium, so the word "Seriously" doesn't appear. Below are the care facts, including the cited "Days 70–85°F; nights 60–70°F", and Care notes. It wasn't retaken, and didn't need to be.

**`17-pro/06-hazards-stated-plainly.png`: pass.** The same name, cited line and full hazard sentence, with the care facts below.

## Shot 7: The Almanac, narrowed to a space

**`17-pro-max/07-almanac-narrowed.png`: pass.** The Species Almanac, retaken, with "Fits Kitchen windowsill" picked and "Basil" typed in the search. "Species · 1 shown" is followed by the note naming Kitchen windowsill in full and the line that indoor light isn't checked. The one card is Basil (*Ocimum basilicum*, Intermediate) with "Confirmed here: indoors or out" and "✿ you keep this one". "Fits My Home" and "Fits Back fence bed" are whole.

**`17-pro/07-almanac-narrowed.png`: pass.** The same content, retaken.

The weaknesses in both, none of which breaks the shot list:

- The picked chip, the one the shot is about, is cut at the right edge: "✓ Fits Kitchen w" on the Pro Max and "✓ Fits Kitc" on the Pro. The note under the count names the area in full, so the frame still says what it's filtered to. Scrolling the chip row all the way right would show the picked chip whole and leave the cut on the unpicked "Fits My Home" at the left edge, which reads more naturally as a row that scrolls. That would be my preference on a reshoot, but it's not needed.
- The typed "Basil" isn't in the shot list, and the search is what brings the list down to 1. The search field is plainly visible, so the frame doesn't pretend the filter alone did it.
- The lower part of each frame is empty, because the search leaves one species.

## Shot 8: Walk the garden

**`17-pro-max/08-walk-the-garden.png`: pass.** Walk the garden on the plain simulator backdrop, with My Home as the selected area. There are 2 confirmed cards: "12 tomatoes along the south fence" (How many 12, Tomatoes, south fence) and "a rosemary by the gate" (How many 1, Rosemary, gate). "Add 2 to the garden" shows and hasn't been tapped. The text field shows its own hint, "What's planted here?", because the sentence has moved into the cards.

**`17-pro/08-walk-the-garden.png`: pass.** The same content, with the area chips on two rows.

## README

The README now matches the files. Its file list, its account of the seven retakes, and its notes on shots 3, 5, 6 and 7 and on "My Home" agree with what the frames show. The four errors this check listed on 2026-10-23 are all fixed. One small imprecision is left: its table says shot 2 shows the first candidates "each with its 'Confirmed here' line", but the last candidate in each frame is cut by the tab bar before that line. That doesn't affect the upload.
