# Controls first: PlantAdvocate almanac redesign (2026-11-24)

The PlantAdvocate half of Duet's note "ui-redesign: controls first, sources behind a tap". The plan is in the Claude Doc "Controls first: PlantAdvocate and Exposure Radar redesign". This branch is `claude/ui-almanac-controls-518ad0`, cut from `claude/i18n-spanish`. Nothing has been merged, pushed, deployed or uploaded.

## Where things sat before (1.2.0 plus the Spanish branch)

- **Home**: a long server headline ("Frost possible tonight. Low near 35 °F. Trees and shrubs are hardening…"). Then a Weather card: forecast bars, a caption, and three notes. Each weather value had a confidence chip ("Area estimate") and a "Why and data source" disclosure, and the card ended with a "Forecast: National Weather Service." line. Below that came This week (each task with its own Why and data source), The season ahead (a timeline, with a chip on each event), and Your land (map, layer chips, legend, the layer's explained block, reading tiles with chips, and the slow-service progress sentence). Then Growing spaces and the server notes. Plants, Species and Settings were quiet text links at the very bottom, so Settings was a full scroll away.
- **Your land**: every value showed a chip, a Why and data source disclosure and a "Know better?" correction. The map legend had its own explained block. There was also a progress sentence and notes.
- **Season**: forecast bars, a "Forecast by X as of …" line and the Apple Weather credit. Each event had a chip and a disclosure, each task had a disclosure, and notes came at the end.
- **Zone map**: a saved zone's values, each with a chip and a disclosure.
- **Species**: care facts with a Sources card, and hazard notes with the not-advice line. This screen is unchanged.
- **Settings**: Account, Appearance, care reminders by kind, frost alerts, weather shift, privacy flows, census, and About with the Perenual credit.
- **Onboarding**: four slides (welcome, add land, see land, add plants).

## What changed

- **Home, "This week on your land"**, in this order:
  1. The almanac line: the date, the week of the season, the one thing that matters (the first sentence of the headline), and "Forecast as of …".
  2. Up to three tasks, each with Done and Skip.
  3. The Controls row.
  4. Land at a glance: sun, water and soil, one word each, with an "est." tag and "Not right? Fix it".
  5. A How we know button.

  Text links to the season, the land and its map, spaces, plants, species and settings follow, because Home has no tab bar. Settings is in the header, in words. People with no land see the same almanac with "Add your land".
- **Controls row**: frost and freeze alerts (On/Off), your land, zones, Not right? Fix it, temperatures °F/°C, and task reminders (On/Off). Each tile is one accessibility element with its state, a word and a mark for that state, at least 44 pt, and solid fills. Tiles stack in one column from text scale 1.3.
- **How we know**: a modal sheet, one per screen (Home, Your land, Season, Zone map). It holds the confidence labels, reasons, sources, the forecast fetch time, the method for the week of the season, the full headline, the slow-service sentences and the notes. The faces now show the value with "est." or "Checking". `howWeKnow/sections.test.ts` pins that no source or note is lost.
- **°C**: `units/temperature.ts` formats every temperature the app writes itself. The default comes from the phone's region, and the setting lives in the Controls row and in Settings.
- **Contrast**: solid tile tokens, a stronger palette per theme under Increase Contrast, flattening under Reduce Transparency, and heavier weights under Bold Text. `theme/contrast.test.ts` pins the ratios in all four palettes.
- **Onboarding**: five slides (almanac, three tasks, controls, add your land, How we know).

## Control-label contrast (WCAG ratio)

| Palette | Tile label on tile, off | On | Tile border vs card / page | Verdict line (ink on card) |
|---|---|---|---|---|
| Almanac | 9.60 | 9.60 | 4.22 / 3.75 | 9.60 |
| Observatory | 13.78 | 8.23 | 4.80 / 5.28 | 13.78 |
| Almanac, Increase Contrast | 13.53 | 13.53 | 13.53 / 12.64 | 13.53 |
| Observatory, Increase Contrast | 19.14 | 13.23 | 13.88 / 15.23 | 19.14 |

## Known gaps

- Sentences the server writes (the headline, card details, season plan text, alerts) still say °F. When the reader uses °C and the headline's first sentence quotes a °F reading, the almanac line uses the phone's own sentence instead. The sheet and Settings say this.
- Frost alerts have no "how early" choice, and task reminders have no time of day, because neither exists in the reminder preferences. Both tiles are On/Off. The reminders tile turns every kind of check on or off together, and Settings keeps the per-kind switches.
- Done and Skip on a season task answer its event, which is how the server's API works, the same as on the Season screen. Skip on a plant check other than water logs nothing and hides the row until next week.
- The species pages were not changed. The hazard notes and the not-advice line must stay on the face, and the care-fact sources already sit in their own card at the foot of the page.
- The status bar text in Observatory is white on a light blue header (this was already so). Also, iOS 26 draws its own glass capsule around header buttons.
- The Spanish strings are a first pass and need review by a native speaker.

## Store and review copy to update before this ships

- `docs/app-store/listing.md` says each value carries a label such as Good estimate and a Why and data source note, and that Home opens on a weather report. Under this design the labels sit behind How we know and Home is the almanac. Guideline 2.3 requires accurate metadata, so the description needs a rewrite.
- `docs/app-store/review-notes.md` steps 5 and 7 and the table rows for Your land and Season mention the chips, Why and data source, and "Know better?". The new words are "est.", How we know, and "Not right? Fix it".
- The 1.2.0 store screenshot 02 shows confidence chips on the reading tiles. It should be retaken.
- The privacy pages are unaffected. No new data leaves the phone: the °C choice and Home's skips are kept on the phone.

## Screenshots

These are Release simulator builds on an iPhone 17 Pro Max. Sign-in is real Apple or Google and no account was signed in on the simulator, so the screenshots come from a throwaway copy of the source. In that copy, sign-in is stubbed and the API answers with sample data for a made-up garden in Washington, DC. That patch was never committed. The Drive folder is "2026-11-24 PlantAdvocate ui-redesign screenshots", in the mailbox's to-duet folder.
