# Plant Advocate iOS debugging — handoff gaps filled from the repo

Companion to `~/Downloads/HANDOFF-plant-advocate-ios-debugging.md` (prepared
in a chat session, technical state unverified). Everything below was checked
against this repository on 2026-09-03. Where the handoff's assumption differs
from the code, the code wins and the difference is called out.

## Gaps, filled

- **Language and framework.** Not Swift. The app is Expo SDK 57 / React
  Native 0.86 / React 19.2 in TypeScript, navigation by React Navigation 7
  (no expo-router). One custom native module, `mobile/modules/plant-speech`,
  provides on-device speech-to-text. Bundle id
  `com.allisonbowman.plantadvocate`, app version 1.1.3 in `mobile/app.json`,
  slug still `garden-gnome`.
- **Data layer.** No on-device database. The phone talks to a FastAPI
  backend (`garden-gnome/`) through a `BASE_URL` API client with
  `@tanstack/react-query`; tokens live in `expo-secure-store`. The backend is
  SQLModel over SQLite (`sqlite:///garden_gnome.db` locally,
  `/data/garden_gnome.db` in the container) with Alembic migrations through
  `0014_authority_scope`.
- **Actual symptoms.** None were supplied, and none are recorded as open
  crashes. The two known live issues are: WeatherKit returns 401 with a valid
  key (ruled an Apple-side defect, open with Apple Support since July; the app
  runs on the fallback chain), and the speak-in-and-batch capture flow is
  judged insufficient for the data volume (a redesign candidate, not a crash).
- **App Store review history.** Never submitted to App Review. Internal
  TestFlight builds 1.1.0, 1.1.1 and 1.1.2 (build 15, 2026-08-02) shipped to
  testers; the planned 1.1.3 build was never made. Pre-review items already
  identified in `docs/`: Guideline 4.8 (Sign in with Apple must accompany
  Google Sign-In; `expo-apple-authentication` is installed), Guideline
  5.1.1(v) (in-app account deletion), the consent phase that "blocks App
  Review", and App Review notes for a social-login-only app with no demo
  account. Beta App Review only becomes necessary for external testers.
- **Deployment target; simulator vs device.** No iOS deployment target is
  overridden in `app.json` or `eas.json` (no `expo-build-properties`), so the
  Expo SDK 57 default applies. Simulator runs work from this Mac (see the
  `plantadvocate-sim-run` memory for the gotchas); device builds go through
  EAS from the Windows box, since `eas-cli` is not installed here.

## Integration surfaces, checked

| Surface | Status in the code |
| --- | --- |
| Weather | `garden-gnome/app/services/weather.py`: WeatherKit first (needs team id, key id, service id and the PEM), then NWS `api.weather.gov` for US coordinates, then Open-Meteo as the global fallback. Working on the fallback chain since 1.1.0. |
| Voice input | Real. `modules/plant-speech` (native STT) feeds `CaptureGardenScreen`, and `capture/splitUtterance.ts` splits one spoken sentence into groundable entries. `gnomeVoice/` is the persona's writing voice, not audio. |
| Landscaper connection / billing | Not built. No billing, subscription, purchase or landscaper code exists in `mobile/src` or `garden-gnome/app`. |

## Plant ID is live, not dead

The handoff says plant ID via reasoning models was dropped as a direction.
The code has not caught up: backend routes `/identify-photo`,
`/{plant_id}/diagnose-photo` and `/{plant_id}/advice` are live, and the
mobile side ships `photoId/identify.ts`, `AddPlantScreen`,
`PlantDetailScreen`, `CaptureGardenScreen` and the photo-upload consent
copy. The catalog-truth plan (`~/.claude/plans/the-app-needs-a-twinkling-crown.md`)
deliberately keeps photo ID offered even for species with no verified care
data. So this is a product decision to make before debugging, not a bug to
find: either the ID path stays and is maintained, or it is removed with its
consent surfaces and App Review notes updated.

## The pivot versus current work

Nothing for site characterization exists yet: no map or polygon library
(`expo-location` only), no USDA Soil Data Access or USGS 3DEP client. The
per-plant entry flows the handoff says to check "before spending time on"
are today's core. Note also that the species-level catalog collection loop
(claim graph, 59 batches, 2,472 claims as of this note) is exactly the
"optional later enrichment" the pivot describes. It keeps running until told
otherwise; whether it stays the priority is the user's call.

## Standing constraint

Acknowledged. One factual note: the catalog cites public University of
Maryland Extension pages (`extension.umd.edu`) as a data source, the same
way it cites NC State, Clemson and Penn State. That is use of a public
website, not of university resources or coursework.
