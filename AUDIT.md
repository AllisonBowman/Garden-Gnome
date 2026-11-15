# Plant Advocate: Step 0 architecture audit

Date: 2026-11-13. Repository: `/Users/allisonbowman/Developer/Garden-Gnome`, read at `2ae894e` (branch `new-pot-icon`, tree identical to `origin/master` `26525f9`). App version 1.1.3 (`mobile/app.json:5`). Nothing in the repository was changed.

Companion document: [PLAN.md](./PLAN.md), which turns these verdicts and the open questions in section 8 into phases and owner decisions (PLAN.md sections 11 and 13).

Every claim about code cites a file, with line numbers where the claim is about specific lines. Paths starting `mobile/` are the phone app, `garden-gnome/` the backend, `site/` the marketing site, `docs/` the project notes. Where a reader report and its fact-check disagreed, the fact-check wins; section 9 lists how this was done.

---

## 1. Summary

**What the app is today.** Plant Advocate 1.1.3 is a plant-first garden and houseplant care app. An Expo / React Native iPhone app talks to a FastAPI (Python web framework) backend that keeps everything in one SQLite file on one Fly.io machine. The owner signs in with Apple or Google, describes "growing areas" by hand, adds plants (a catalog species is required), and gets per-species check reminders, rule-based care advice, a fit verdict (does this species suit this area, and why), and a local forecast. The plant care database is a cited catalog: 999 researched records turned into 10,681 claims from 8 vetted publishers, plus 129 hand-written entries.

**What carries over to the vision.**
- The fit engine (`garden-gnome/app/services/fit.py`) already answers "What belongs here?" and "Will this plant work?" for one area: three verdicts, a server-written reason sentence that names the limiting factor, the publishers behind it, a score (`fit.py:485-511`) and a ranked candidate list that already excludes invasive and noxious species (`fit.py:534-581`).
- The evidence model: `Claim` / `Authority` rows, per-field provenance on species (`garden-gnome/app/models/models.py:391-404, 529-578`), and the phone components that show a source with each fact (`mobile/src/components/FitFindingRow.tsx`, `CareFacts.tsx`, `WeatherCredit.tsx`).
- A provider-neutral weather payload with the provider credit attached (`garden-gnome/app/services/weather.py:376-400`), on-device address geocoding (`mobile/src/location/lookup.ts:12-39`), local notifications (`mobile/src/notifications/`), the speech module, accounts and deletion, the deploy pipeline.

**What conflicts.**
- Species are required everywhere: `Plant.species_id` is a non-null foreign key (`models.py:646`), Add Plant blocks without one, and Walk the garden saves only matched rows (`mobile/src/screens/CaptureGardenScreen.tsx:192`).
- Photo identification is offered in Add Plant and advertised on the pricing page (`mobile/src/screens/AddPlantScreen.tsx:138-315`; `site/pricing.html:264`).
- Care runs on calendar intervals and calendar months, including feeding in September and October (`garden-gnome/app/services/advisor.py:370`, `mobile/src/notifications/plan.ts:30`).
- Every account starts with an indoor, sheltered, unlocated "My Home" area (`garden-gnome/app/routers/auth.py:92-97`, defaults at `models.py:617-619`), which switches weather advice off.
- Public promises contradict the brief: "rounded to about a kilometer" and "we don't keep the address you typed" (`site/privacy.html:140`), "no push token" (`docs/app-store/app-privacy.md:72`), and a go-to-market rule to "never mention frost, zones or planting dates" (`docs/go-to-market/strategy.md:17`).

**What is missing.** No property object, no zone outlines, no vegetation type, no public site data (soil, slope, land cover, hardiness), no confidence or override on any site value, no persisted geodata cache, no weather history, no growing degree days (GDD), no frost, dormancy or leaf-drop logic, no server-side background job scheduler (the phone schedules only local notifications), no server push, no map library, no native-status, hardiness, habit or deciduous fields in the catalog, no landscaper code.

**The four biggest risks.**
1. **Release and deploy coupling.** Every push to master deploys to production (`.github/workflows/ci.yml:14-17, 66-100`), migrations run at boot, and a rollback restores the image but not the database. The repo's last record (2026-10-31) put production on the archived July build at database migration 0009 (Alembic, the migration tool). That is no longer true: on 2026-11-13 the live API at `garden-gnome-api.fly.dev` published the same 34 public paths as master, including `/growing-areas` and `/plants/bulk`, so a master-era build has since deployed. (The version string "0.2.0" is hard-coded in `garden-gnome/app/main.py:50` on master too, so it does not identify the build.) The repo still does not record which commit or migration production is on; confirm before the first overhaul migration, and take a volume snapshot first. According to the task notes (the repo does not record it), 1.1.3 was uploaded 2026-11-12 and has not yet been through App Review; see open question 1. The overhaul must stay additive and invisible to 1.1.3 for as long as 1.1.3 is installed.
2. **The seasonal engine has no reliable data foundation yet.** WeatherKit has answered `NOT_ENABLED` since July (`weather.py:40`). Master falls back to the National Weather Service (NWS), then Open-Meteo (`weather.py:391-396`); production appears to run a master-era build (risk 1), so U.S. users most likely get NWS forecasts and others Open-Meteo. (The archived July build on `origin/rescue/deployed-production` was WeatherKit-only.) Open-Meteo's free tier is non-commercial (`weather.py:43`), and it is also what the public-data prototype (the "spike", section 9) used for GDD history. Forecasts are 5 days, history is not stored, there is no server-side scheduler, and reminders re-plan only on a cold launch or sign-in, a care log, an added plant or a Settings change (`App.tsx:211-213`; `CareTodos.tsx:78`; `AddPlantScreen.tsx:125`; `SettingsScreen.tsx:147, 166`), never on return to the foreground and never when the forecast changes. On Apple Intelligence iPhones, the shipped 1.1.3 can also reword a frost warning through the on-device "gnome voice" with no check that the warning survives.
3. **Public promises and privacy disclosures point the other way.** Parcel-level soil and terrain lookups break the 1 km rounding promise. Server push breaks "no push token". The store listing, screenshots, strategy and press copy deny frost and zone features. Each must change in a set order, tied to builds, and most store fields change only with a new version.
4. **Public site data and the catalog are thinner than the brief assumes.** In the spike, sun from terrain alone always came out "full sun", so the owner's correction is the real source for sun. USGS 3DEP elevation (U.S. Geological Survey 3D Elevation Program) took 6-10 s cold and failed often, so fetch it in the background. NLCD land cover (National Land Cover Database) covers only the lower 48 states. Hardiness comes only from an unofficial service or a local copy of the 2023 map. The catalog has no native status, hardiness or dormancy fields, so natives-first ranking and growing-degree-day triggers need new cited research (open question 11) before they can show a source.

---

## 2. Architecture map

```
 iPhone (Expo SDK 57, React Native 0.86)                 Fly.io, region iad, 1 machine
 +-------------------------------------------+          +----------------------------------+
 | App.tsx: auth gate -> 5 bottom tabs        |  HTTPS   | uvicorn + FastAPI                |
 |  Plants | Species | Growing areas |        |  axios   |  routers: auth, species, plants, |
 |  Census | Settings                         | -------> |  growing_areas (+/environments), |
 | TanStack Query cache (memory only)         |  bearer  |  census, ai, static /ui          |
 | SecureStore: tokens, prefs, theme          |  JWT     |  services: fit, advisor, weather,|
 | expo-notifications (local, 30 days ahead)  |          |  toxicity, care_facts, grounding,|
 | expo-location geocoder (on device)         |          |  vision, name_match, catalog     |
 | native: plant-speech (SFSpeechRecognizer)  |          |  claim graph (app/data/claims)   |
 |         plant-id (Vision + on-device model)|          |  SQLite on volume /data          |
 +-------------------------------------------+          +----------------+-----------------+
                                                                         | coords rounded to 2 decimal places
                                                     WeatherKit web API -> NWS -> Open-Meteo
 GitHub master push -> CI tests -> flyctl deploy -> boot: migrate + seed + claim sync -> smoke check
 site/ (13 static pages) -> Cloudflare Pages, deployed by hand with wrangler
```

Key: SDK = software development kit. HTTPS = secure web requests. JWT = JSON Web Token, the signed sign-in token. CI = continuous integration (automatic tests on each push). API = application programming interface; WeatherKit web API = Apple's REST (representational state transfer) interface. The NWS and Open-Meteo fallbacks are on master, and production appears to run a master-era build (section 2.3). The `/data` volume is documented as 1 GB (`README.md:202`).

### 2.1 Mobile

| Part | What is there | Evidence |
|---|---|---|
| Framework | Expo SDK 57.0.7, React Native 0.86.0, React 19.2.3, TypeScript, React Native Paper 5 (Material Design 3) | `mobile/package.json:10-29` |
| Navigation | React Navigation 7. Five bottom tabs (Plants, Species, Growing areas, Census, Settings); four have native stacks. Emoji tab icons. Almanac and SpeciesDetail are each registered in three stacks | `mobile/App.tsx:79-85, 142-187, 284-327` |
| Screens | Plants: PlantsScreen, PlantDetail, AddPlant, CaptureGarden ("Walk the garden"). Species: SpeciesScreen, SpeciesDetail, Almanac. Growing areas: list with a three-step create modal, detail. Census. Settings. Plus Login and a four-slide onboarding overlay | `mobile/src/screens/`; `mobile/src/onboarding/Onboarding.tsx` |
| Server state | TanStack Query 5 over axios, memory only, `staleTime` 30 s (weather 30 min). No query persistence, no AsyncStorage, nothing shown offline. One refresh call is shared between concurrent requests | `mobile/App.tsx:93-100`; `mobile/src/screens/GrowingAreaDetailScreen.tsx:98`; `mobile/src/api/client.ts:54-136` |
| Local storage | expo-secure-store under `garden_gnome_*` keys: tokens, theme, onboarding flag, consents, reminder preferences | `mobile/src/theme/ThemeProvider.tsx:9`; `mobile/src/notifications/reminders.ts:12-13` |
| Care load | Plant list, then one care-log request per plant and one species request per species, in parallel | `mobile/src/api/plants.ts:62-91` |
| Native modules | `plant-speech` (iOS only, Apple's speech recognizer, on-device when supported). `plant-id` (Vision labels, then Apple's on-device language model; also `generate()` used by the gnome voice; an Android Kotlin path that was never compiled) | `mobile/modules/plant-speech/ios/PlantSpeechModule.swift`; `mobile/modules/plant-id/ios/PlantIdModule.swift:39-75` |
| Expo modules | expo-notifications, expo-location, expo-camera, expo-image-picker, expo-secure-store. No map library | `mobile/package.json:14-22` |
| Platform | iPhone only and portrait, both pinned by a test (`appConfig.test.ts:164-171`). Light mode is forced in `app.json:8`, but no test pins it. `mobile/ios` is generated and not committed. Android remnants remain in `app.json` and an EAS (Expo Application Services) preview profile | `mobile/app.json:6-10, 83-96`; `mobile/src/appConfig.test.ts:164-171`; `mobile/eas.json:22-24` |
| Tests | Jest runs `*.test.ts` only, in a node environment. No component render tests. About 15 test files read screen source by regular expression | `mobile/jest.config.js:7-8`; `mobile/src/care/facts.test.ts:345-374` |

### 2.2 Backend

| Part | What is there | Evidence |
|---|---|---|
| Framework | FastAPI, SQLModel (an object-relational mapper over SQLAlchemy), Pydantic, slowapi rate limiting on `/auth/*` only | `garden-gnome/app/main.py:76-91`; `garden-gnome/app/rate_limit.py:19-57` |
| Data model, per user | `User`, `AuthIdentity`, `RefreshToken`, `PendingAppleRevocation`, `GrowingArea`, `Plant`, `CareLog`, `StewardshipRecord` | `models.py:248-310, 596-725`; `garden-gnome/app/db/revocations.py:28` |
| Data model, shared catalog | `Species` (legacy columns, ~30 cited care fields, fit fields, provenance), `CareSchedule`, `SpeciesTrait`, `Authority`, `Claim`, `SyncState` | `models.py:313-593` |
| Persistence | One SQLite file at `sqlite:////data/garden_gnome.db` on volume `gnome_data`. No database settings are tuned: links between tables (foreign keys) are not enforced, the slower default write mode is used, and a busy database fails at once instead of waiting (no `PRAGMA` is set) | `garden-gnome/fly.toml:10-15`; `garden-gnome/app/db/database.py:9-114` |
| Migrations | Alembic, 22 linear revisions (0001-0022, head `0022_backfill_acquired_on`), batch mode on SQLite. Run at boot inside the seed, then again in the app's startup hook | `garden-gnome/alembic/versions/`; `garden-gnome/Dockerfile:29`; `garden-gnome/app/main.py:30-44` |
| Boot | `python -m app.data.seed && uvicorn ...`: migrate, seed 129 curated species, refresh curated prose, run the claim sync over ~16 MB of evidence (a sync failure is logged and skipped) | `garden-gnome/Dockerfile:29`; `garden-gnome/app/data/seed.py:188-210` |
| Services | `fit` (suitability), `advisor` (rule-based advice; a language-model backend exists but is off), `weather`, `toxicity`, `care_facts`, `grounding` (rejects model text that drifts from cited facts), `persona`, `vision` (identify and diagnose, stub by default), `name_match`, `catalog` (language-model species generator), `tokens`, `oauth` | `garden-gnome/app/services/` |
| Routers | `ai` (`/ai/status`), `auth` (`/auth/*`, `/me`), `species`, `plants`, `growing_areas` (mounted twice: `/growing-areas` and the deprecated `/environments`), `census`; static test console at `/ui` | `garden-gnome/app/main.py:76-91` |
| Isolation | Each route checks the signed-in user itself and returns "not found" (404) for anyone else's rows; the database does not enforce this | `garden-gnome/app/deps.py:12-35`; `garden-gnome/app/routers/growing_areas.py:32-37` |

### 2.3 Hosting and deploy

- **Every push to master deploys.** CI runs backend pytest and mobile typecheck and Jest, then `flyctl deploy --remote-only`, then a smoke check that polls `GET /` until `catalog.synced` is true (`.github/workflows/ci.yml:14-17, 66-130`). Documentation-only pushes deploy too. `/ai/status` is only printed in the smoke check, with `|| true` (`ci.yml:126`).
- **Migrations at boot.** Not a Fly release command, because release machines do not mount the volume (`garden-gnome/README.md:174`). A failed migration fails every boot after it. SQLite schema changes are not transactional here; migration 0017 once left a half-renamed table (`garden-gnome/alembic/versions/0017_growing_area.py:32-37`).
- **Rollback does not restore data.** Take a manual volume snapshot before any deploy with a migration (`docs/deploys.md:126-134`). The repo records no test restore of a snapshot.
- **Machine:** `shared-cpu-1x`, 512 MB, auto-stop, `min_machines_running = 1` (`fly.toml:20-30`), set on 2026-10-31 to stay awake through App Review (commit `2da6faa`). `ci.yml:104`, `docs/deploys.md:63` and `docs/app-store/README.md:67` still say 0 (`docs/app-store/review-notes.md:162` says 0 unless that document's own "decision 1" changes it).
- **Production state.** On 2026-10-31 production answered with 29 paths and no `/growing-areas`, at Alembic 0009 (`docs/2026-10-16-app-store-finish-line-handoff.md:101-104, 364-369, 1513`); that July build's source is archived on `origin/rescue/deployed-production`. **Checked live on 2026-11-13:** `GET https://garden-gnome-api.fly.dev/openapi.json` lists 34 public paths, the same set master publishes (operator routes are hidden from the schema), including `/growing-areas/*`, `/plants/bulk` and `/census/summary`. So a master-era build has deployed since 10-31. `/ai/status` reports the advisor and vision backends as stubs. The exact commit and migration level are not observable from outside; confirm them (for example with `flyctl ssh console` and `alembic current`) before the first overhaul migration.
- **Python and Node.** CI and the Docker image use Python 3.12 (`ci.yml:44`, `Dockerfile:1-6`) and Node 20 (`ci.yml:59`). The local virtual environment runs Python 3.14.7 and Node 26.5.

### 2.4 Marketing site

`site/` holds 13 static HTML pages, deployed by hand to Cloudflare Pages with wrangler (`site/README-SITE.md`). They carry plant-first positioning, a "free, no subscriptions" pricing page (`site/pricing.html:248`), a planned nursery partner page ("None of this exists yet", `site/nurseries.html:256`), a community-garden demo that stores plots in the browser, a nine-slot houseplant picker (`site/recommendations.html:273-289`, eight distinct entries), and the privacy policy effective 2026-10-20, which the app links as binding. On 2026-10-31 the live site still served the 2026-10-16 pages (`handoff:101-104`); this was not re-checked on 2026-11-13 (open question 1). The README warns not to rerun the July desktop generator until it has been reconciled with `site/` (`site/README-SITE.md:11-17`). Branch `claude/launch-day-site` holds the launch-morning edits, including a press page that says the app has no frost dates or hardiness-zone matching.

---

## 3. Areas the brief names

### 3.1 UI framework

Expo / React Native with React Navigation and React Native Paper (section 2.1). The shell is sound and neutral to the brief: providers, per-screen error boundaries, a retry-once query policy, refetch on return to the foreground, cache drop on sign-out (`mobile/App.tsx:87-122, 215-220, 336-368`).

What has to change is the information architecture. The first tab is a plant list, the second a browsable species catalog, and onboarding ends in "Add your first plant" (`mobile/src/onboarding/slides.ts`; `App.tsx:228-255`). A site-first app needs the property and the seasonal plan as the first surfaces.

- **No map.** Zone sketching needs a new native dependency and a new App Store build (`mobile/package.json`, no maps package).
- **Little editing.** After an area is created, only a missing location can be set (`GrowingAreaDetailScreen.tsx:139-163`). Sun, surface, measurements and goals cannot be changed, and no screen deletes an area.
- **Copy.** "UV" (ultraviolet) and "AI" (artificial intelligence) appear unexplained in the app (`GrowingAreaDetailScreen.tsx:75, 508`; `mobile/src/weather/translate.ts:102`; `mobile/src/consent/copy.ts:125, 138`). No test checks acronyms.
- **Accessibility.** `accessibilityLabel`, `accessibilityRole`, `accessibilityHint` and `accessibilityState` appear only 15 times in 7 files under `mobile/src` (a grep for `accessibility`). Map and zone screens should ship with labels, because no render test will catch a missing one.
- **Test coupling.** Tests read screen files by path, so renames and deletions break them even when behaviour is right: `slides.test.ts:25-37`, `loadFailed.test.ts:90-126`, and `facts.test.ts:345-374`, which scans every `.tsx` file under `src`.

### 3.2 Data model

The single place object is `GrowingArea` (`models.py:596-637`): name, type (8 values), user, city, region, country, latitude and longitude, a unique `uuid` (`models.py:604`), three climate enums with defaults, and nullable surface, `area_sqft`, `headroom_in`, `soil_depth_in` and `goals`. Plants and stewardship records point at it by foreign key (`models.py:666, 718`). It has no parent property, no outline, no vegetation type, and no source or confidence on any value.

Points the vision depends on:

- **`Plant.species_id` is required** (`models.py:646`). The 1.1.3 client types it as a number and builds `/species/{id}` and `/fit/{id}` requests from it (`mobile/src/types/index.ts:183`; `mobile/src/api/plants.ts:66-82`; `mobile/src/api/growingAreas.ts:185-186`). Making it nullable means a table rebuild and breaks 1.1.3, so record species-less vegetation on zones instead.
- **Defaults are stored as if chosen.** `sun_exposure` defaults to `partial_sun`, `temp_exposure` to `indoor`, `shelter` to `sheltered` (`models.py:617-619`), and nothing tells a default from an owner's answer. Because of the indoor default, `advisor.weather_applies` skips weather for the default area (`advisor.py:107-118`).
- **Two sun scales.** Species use four values (`full_sun`, `part_sun`, `part_shade`, `full_shade`); areas use three (`full_sun`, `partial_sun`, `shade`) (`models.py:152-155, 222-233, 354-355`). The brief's tap (full sun / part shade / shade) needs one shared mapping.
- **Soil exists in pieces.** The area has `soil_depth_in`, which no fit axis reads (the phone shows it and notes that it is unchecked: `GrowingAreaDetailScreen.tsx:216`; `realEstate.ts:142-147, 300-305`). Species carry `soil_drainage` (787 claims), `soil_base` and `soil_ph`. `fit.py` does not read drainage or pH (`fit.py:247-288`).
- **Seasonal fields exist but are calendar-based or thin.** `fertilize_active_months` (31 claims), `water_dormant_days_est` (3 claims), `cool_rest_note`, and `chill_damage_f` (75 claims) (`models.py:363-389`). Absent: native status, deciduous or evergreen, life cycle, growth habit, hardiness zone, and GDD thresholds. `outdoor_temp_min_f` has 0 claims.
- **A provenance template exists.** `Claim` (value as JSON, authority, citation, collected-at) and `care_provenance` / `care_sources` on species (`models.py:391-404, 529-578`). That shape suits site conditions, but site data should not go into `Claim` itself. Its subject is a species or genus name, and every catalog write stamps a new catalog generation that rebuilds the species cache (`models.py:741-771`).
- **Deleting a zone is guarded.** `DELETE /growing-areas/{id}` returns 409 while plants or any stewardship record point at it (`growing_areas.py:126-153`). Redrawn or merged zones need an archive or merge path.

### 3.3 Persistence

SQLite on one Fly volume, one writer, one machine (`fly.toml:13-15`; `garden-gnome/README.md:192`). It is adequate for phase 1 if zone outlines are stored as GeoJSON (a standard text format for map shapes) in a JSON column and only derived geodata is kept. The spike measured a cached site profile at 12-13 KB compact JSON, or 3.1-3.4 KB gzipped (`/private/tmp/claude-501/-Users-allisonbowman--claude-spares-spare-XM0k7R/3e5c7cc7-c986-4f99-8da6-1f158ad938a5/scratchpad/audit/spike.json`, findings).

Hazards:

- **Foreign keys are not enforced, and deletion is partly by hand.** `delete_me` deletes Plant and GrowingArea rows by hand and relies on ORM cascades for care logs, stewardship records, identities and refresh tokens (`garden-gnome/app/routers/auth.py:407-424`; `models.py:270-275`). A new table (property, zone conditions, geodata cache, tasks, device tokens) that is neither deleted there nor reached by a cascade survives account deletion silently. That would break `site/privacy.html:179`.
- **SQLite limits.** A NOT NULL column cannot be added to existing rows, nullability changes rebuild the table, and schema changes are not transactional (`0006_plant_quantity.py:25-27`; `0015_species_claim_wiring.py:26-29`; `0017_growing_area.py:32-37`). New tables and nullable columns are the safe path.
- **No write-ahead logging (WAL) or busy timeout.** Background writers (daily weather or GDD jobs) could hit "database is locked".
- **The boot path is already slow.** Migrate, seed and a 16 MB claim sync run before uvicorn binds, which can take minutes on a throttled CPU (`ci.yml:104-114`). Geodata fetches must never run at boot.
- **Migration number clash.** An unmerged branch (`origin/candidate-categorization-proposal`) already uses migration 0023 (`0023_eaten_parts`). If the overhaul also adds a 0023, the migration history forks and the migration tests fail (`garden-gnome/tests/test_migrations.py:13-25`). Agree the numbering first.
- **Running cost.** `min_machines_running = 1` bills all day. Under the owner's free-then-paid rule, server-side geodata caching and daily jobs are running costs that need a tier decision.

### 3.4 WeatherKit integration

Only the backend calls weather providers, and only on request (`weather.py:1-16`). The phone never calls one; WeatherKit is a REST call from the server, not Apple's Swift framework.

- **Provider fallback chain**, first answer wins: Apple WeatherKit over its web interface (REST, representational state transfer) with a JSON Web Token (JWT) signed with Apple's required elliptic-curve key (ES256), then the U.S. National Weather Service (NWS), then Open-Meteo (`weather.py:391-396`). Each request has a 10-second per-phase timeout (`httpx.Timeout(10.0)`: connect, read, write and pool each). The NWS step can make 4 sequential requests, so a chain that hangs everywhere takes a minute or more (`weather.py:198, 254, 331-367`). The phone's API client gives up after 15 seconds (`mobile/src/api/client.ts:122`).
- **WeatherKit status.** The code comment says Apple was returning `NOT_ENABLED` as of 2026-07 (`weather.py:39-40`). Docs as late as 2026-10-23 say production forecasts come from NWS in the U.S. and Open-Meteo elsewhere (`docs/go-to-market/product-truth.md:307-311`). **Production appears to run a master-era build (section 2.3), so U.S. users most likely get NWS forecasts and everyone else Open-Meteo.** The archived July build was WeatherKit-only. The WeatherKit success path has been tested only against a hand-written sample (`garden-gnome/tests/test_weather.py:3-35`). The docs disagree on whether an Apple support ticket was actually filed (`docs/2026-07-30-weatherkit-401-closed.md:7, 68` says drafted; `docs/2026-09-03-ios-debugging-handoff.md:23-25` says open). Because WeatherKit is configured but refused, every uncached forecast first makes a failing WeatherKit call and logs a warning, with no circuit breaker (`weather.py:191-209`).
- **Open-Meteo licence.** "Open-Meteo's free tier is licensed for non-commercial use — revisit the provider before a paid/commercial launch" (`weather.py:43-44`). Its data is CC BY 4.0 (Creative Commons Attribution), so a credit and link are required. The weather researcher found its terms treat any app with subscriptions or ads as commercial (`/private/tmp/claude-501/-Users-allisonbowman--claude-spares-spare-XM0k7R/3e5c7cc7-c986-4f99-8da6-1f158ad938a5/scratchpad/audit/research-weather-phenology.json`).
- **NWS limits.** U.S. only, User-Agent required, no ultraviolet (UV) index and no sunrise or sunset. When NWS answers, the UV and daylight lines never appear (`weather.py:71-84, 273-328`).
- **Privacy.** Coordinates are rounded to 2 decimals (about 1 km) for every provider and for the cache key (`weather.py:90-97`). This is a published promise (`site/privacy.html:140`) pinned by `test_weather.py:266-313` and `mobile/src/consent/copy.test.ts:101-123`.
- **Cache.** A process-local dict keyed by (rounded latitude, rounded longitude, hour bucket). It is never evicted and is lost on restart (`weather.py:100-102, 387-400`).
- **Horizon.** 5 days (`weather.py:88`), although `fit.py:45-47` calls it a ten-day forecast. No history is fetched or stored, so GDD cannot be computed.
- **Where weather reaches the user.** `GET /growing-areas/{id}/weather` (`growing_areas.py:79-107`) feeds the area's weather card and the "OUTSIDE → IN HERE" translation (`mobile/src/weather/translate.ts`). `POST /plants/{id}/advice` adds rain, heat, cold and UV nudges (`advisor.py:276-357`) and a `weather_attribution`. That credit is sent whenever a forecast was fetched, even if no advice line used it (`garden-gnome/app/routers/plants.py:540-572`).
- **Two sets of thresholds.** Server nudges compare forecast lows with a species' `chill_damage_f`, falling back to the uncited `temp_f_min` (`advisor.py:319-334, 350-357`). The phone uses fixed thresholds instead: a "Cold night" line at 40°F or below (`translate.ts:93`). No rule uses 32°F, and nothing detects a season's first frost.
- **Apple credit.** The credit text is `" Weather"` with a plain leading space and no Apple mark (`weather.py:34-37`). If WeatherKit ever answers, the on-screen credit would read "Weather ›".

### 3.5 The speak-in-and-batch voice flow ("Walk the garden")

The flow, in order (Plants tab button, `mobile/src/screens/PlantsScreen.tsx:143-153`):

1. **Speech.** `plant-speech` wraps `SFSpeechRecognizer`. It requires on-device recognition where supported, otherwise uses Apple's servers, and says which on screen (`PlantSpeechModule.swift:134, 177-181`; `CaptureGardenScreen.tsx:141-145`). It starts a new segment after each final phrase. This was confirmed on a real phone (commit `bd27176`).
2. **Split.** `mobile/src/capture/splitUtterance.ts` is a fixed English grammar. It splits clauses on commas and "and", reads a leading count, and takes a trailing preposition phrase as the spot. Tested live: "a big oak out back" keeps "big oak out back" as the subject, "a strip of lawn" reads as a count of one, "two hundred" gives 2, and "black and blue salvia" becomes two items.
3. **Ground.** `mobile/src/capture/ground.ts` and `mobile/src/photoId/fuzzyMatch.ts` match against the in-memory catalog by character-pair similarity. A score of 0.60 or more is pre-filled as confident; 0.42 or more is offered. Yard words mis-ground: "maples" scores 0.667 for Mayapple and Apple, and "grass" scores 0.667 for Woolgrass. A pre-filled card hides its alternatives (`CaptureGardenScreen.tsx:394-450`).
4. **Confirm and save.** The owner confirms one card per item. `mobile/src/capture/bulkSave.ts` sends batches of up to 200 to `POST /plants/bulk`, each all-or-nothing on the server (`garden-gnome/app/routers/plants.py:160-178`). The wire payload has five keys: `species_id`, `quantity`, `location`, `growing_area_id`, plus `acquired_on`, which `createPlantsBulk` adds (`mobile/src/api/plants.ts:153-155, 177-182`).

Facts that matter for the vision:

- **Species required.** Only rows with a species are sent (`CaptureGardenScreen.tsx:192`). On a fully successful save the screen closes and unmatched items are discarded (`CaptureGardenScreen.tsx:214-218`).
- **One area per walk**, defaulting to the oldest area. The spoken spot is free text in `Plant.location` (`models.py:673`).
- **No reschedule.** Walk the garden saves do not reschedule reminders; Add Plant does (`mobile/src/screens/AddPlantScreen.tsx:124-125`).
- **The camera does nothing.** The live camera backdrop records nothing, but the screen offers a "Turn the camera on" button that raises the camera prompt, and the backdrop is one of the stated purposes in the camera string (`CaptureGardenScreen.tsx:240-244, 312-316`; `app.json:126`).
- **The recognizer can stall.** Errors in `kLSRErrorDomain` are swallowed and audio interruptions are not handled, so the screen can keep saying "Listening" (`PlantSpeechModule.swift:191-210`).
- **No offline queue.** None exists, although the bulk endpoint's docstrings say there is one (`plants.py:166-170`).
- **Cost.** Speech, splitting, grounding and the gnome voice all run on the phone at zero running cost, so they fit a free tier.

**The gnome voice** (same on-device model, `mobile/src/gnomeVoice/restyle.ts`) rewords server advice on a plant page. It holds back lines that start with ⚠️ or contain a listed hazard word, and rejects drift with ten checks. **It has no omission check.** The advisor's "Cold night ahead ... bring it in or shelter it" line has no ⚠️ prefix and no hazard word, and "bring", "shelter" and "shade" are in neither word list. So a rewrite that drops the frost warning passes (`advisor.py:298-334`; `restyle.ts:24-27, 35, 65, 181-261`). This is the shipped 1.1.3 code path.

### 3.6 The plant care database (the cited catalog)

**Pipeline.**

- **Research.** A researcher workflow writes cited records into 134 batch files, 999 records in all (995 species, 4 genera), under `garden-gnome/app/data/verified/`.
- **Claims.** The loader turns them into 10,681 claims, pinned by `garden-gnome/tests/test_claim_ingest.py:401`. NC State Extension supplies 8,676 (81%); the rest come from Royal Horticultural Society 833, Missouri Botanical Garden 430, Clemson 389, University of Florida IFAS (Institute of Food and Agricultural Sciences) 151, University of Georgia 90, Penn State 62 and Maryland 50.
- **Authorities.** The registry (`garden-gnome/app/data/claims/authorities.py`) maps citation domains to 9 authorities. The USDA (U.S. Department of Agriculture) PLANTS database is tier 1 but scoped to `outdoor_temp_min_f` only, and no USDA PLANTS row has ever been minted (`ingest.py:38-50`).
- **Resolution.** Deterministic: the lower tier wins, values borrowed from the genus are labelled, and harm-capable fields never borrow and never resolve when sources disagree (`garden-gnome/app/data/claims/resolve.py:69-162`).
- **Boot sync.** On every boot the sync mints missing species rows and writes resolved values with `RESOLVER_VERSION` "6" (`recompute.py:49`). Each new field bumps the version and rewrites every row once.
- **Curated entries.** `species_catalog.json` holds 129 hand-written entries with uncited calendar `CareSchedule`s and free-text traits, including an uncited `native_region`.
- **Production has now run the claim sync.** The repo's last record (2026-10-31) had production at 0009 with no claim sync (`handoff:320-326, 364-369`). On 2026-11-13 the live root endpoint `GET /` reported `catalog.synced: true`, 2,589 species and 10,681 claims (catalog version `8c520db39b21:6:1`). The species count is consistent with about 1,900 older rows imported from Perenual, a commercial plant-data service, without citations, plus the cited tranches.

**Fit for the vision.** The catalog knows where a plant can sit: outdoor sun (942 claims), mature size (941), drainage (787), soil base (778), pollinators (654). It knows almost nothing about what the seasonal engine and natives-first ranking need: no native status, hardiness zone, deciduous or evergreen, life cycle or habit, or dormancy timing. The raw evidence is partly present in quotes: 483 records mention "native" and 502 mention a hardiness zone, and NC State pages show "Plant Type" and `#deciduous` tags. Those were never captured as claims.

**Advisor.** Rule-based in production (`ADVISOR_BACKEND=stub`; `docs/pre-deploy-checklist.md:270-279`). Feeding is gated to months 3-10, intersected with cited `fertilize_active_months` where they exist (`advisor.py:366-385`, by the UTC (Coordinated Universal Time) month). The phone repeats the gate by local month in `mobile/src/notifications/plan.ts:30-32`. The language-model prompt calls the model "a careful houseplant care assistant" (`advisor.py:67`).

**Invasive filter.** `never_a_candidate` drops species that a cited safety passage calls a noxious weed or an invasive species (`fit.py:534-561`; `toxicity.py:405-407, 573-578`). The match is a regular expression on English phrases. It knows nothing about region, and it fails open on a database error (`toxicity.py:1075-1078`).

**Query cost.** The candidates route runs about one database query for every species in the catalog on each request, because the invasive-species check looks up each species' safety text separately (`never_a_candidate` → `safety_of` → `_passages_for`, `toxicity.py:1056-1089`). The Almanac asks for 100,000 rows (`mobile/src/api/growingAreas.ts:137`).

### 3.7 Landscaper features

**None exist in code.** A search of `mobile/src`, `mobile/App.tsx`, `garden-gnome/app` and `site/` for `landscap*`, `contractor`, `irrigat*` and `sprinkler` finds one unrelated line, a research prompt that says "not landscape use" (`garden-gnome/app/data/expansion/research_review.py:87`). Other hits are quotes inside research data under `app/data/verified/`. There is no billing, dispatch, multi-party or professional role. Plant transfer is same-account only (`plants.py:225-241`).

What exists nearby:

- **Site:** a planned nursery partner program, "None of this exists yet" (`site/nurseries.html:256`), a pricing-page teaser (`site/pricing.html:288-290`) and a contact mailto (`site/contact.html:248, 259`).
- **Code:** a `nursery` growing-area type that the create modal offers as a selectable "kind of place" (`mobile/src/growingAreas/realEstate.ts:104-107`; `mobile/src/screens/GrowingAreasScreen.tsx:358`), read only by the census; and `StewardshipRecord`, a chain-of-custody record that a future hand-off could use (`models.py:706-725`).
- **Automated care:** nothing. "Automated care recommendations" is read here as care carried out or scheduled without the owner (for example irrigation control, or a care service acting on the plan), as distinct from the seasonal engine's suggestions. The closest primitive is the rain-delay watering shift (`mobile/src/weather/signal.ts:19-23`).

---

## 4. Verdict tables

Keep = carry over as is (small edits allowed). Refactor = keep the idea, change the shape. Delete = remove. Defer = a fourth verdict this audit adds: leave the code in place and build nothing on it for now. Only two Defer rows are the brief's own "keep dormant" items (landscaper connection and automated care recommendations, end of 4.7). Every other Defer is this audit's choice and can be read as "keep, no new work". Effort: S (days), M (one to two weeks), L (more). Risk names what breaks. Section 4.8 lists what must be built new. Rows where readers disagreed or the fact-check changed a verdict are listed in section 9.

### 4.1 Mobile app

| Component | Verdict | Reason | Effort | Risk | Evidence |
|---|---|---|---|---|---|
| UI framework (Expo SDK 57, React Native 0.86, React Navigation 7, React Native Paper 5) | keep | Neutral to the brief; zone sketching adds one map dependency and needs a new App Store build | S | A map library means a native rebuild | `mobile/package.json:9-29` |
| Accessibility labels | refactor | Only 15 accessibility props in 7 files; new zone and map screens need labels from the start | M | No render tests to catch gaps | `mobile/src/` |
| App shell, query client, error boundaries, sign-out cache drop | keep | Neutral; later add a persisted cache for property and zone data | S | Persistence is a new native dependency; must still clear on sign-out | `mobile/App.tsx:87-122`; `mobile/src/api/sessionData.ts` |
| API client and token refresh | keep | Neutral transport | S | None | `mobile/src/api/client.ts` |
| Bottom-tab structure | refactor | Site first: suggested Plan / Yard / Plants / Settings | L | Source-reading tests (`slides.test.ts:25-30`, `loadFailed.test.ts:90-126`, `facts.test.ts:345-374`); deep link at `App.tsx:252-254` | `mobile/App.tsx:48-85, 269-333` |
| Onboarding overlay | refactor | Keep the mechanism; content becomes address → site profile → sun and soil taps; trigger on "no property" | M | `slides.test.ts` (4); the seen flag lives in the keychain and survives reinstall | `mobile/src/onboarding/` |
| PlantsScreen (My Plants) | refactor | Becomes a secondary inventory grouped by zone | M | `GET /plants/` must keep its shape | `mobile/src/screens/PlantsScreen.tsx` |
| AddPlantScreen | refactor | Species stays required (3.2, 4.2); an unidentified plant is recorded as its zone's vegetation type; keep the fit-before-save block (mode 3) | M | Must still send a species; species-less entries go to the zone | `AddPlantScreen.tsx:190, 228, 398-424` |
| Photo identification in Add Plant | delete | "Deliberately NOT a plant identification app"; houseplant-tuned (`PlantIdModule.swift:47-50`), no measured accuracy. The brief's dormant list does not include it | M (mostly copy) | Camera/photo strings (`app.json:126, 134-135`), `photoId/copy.test.ts`, `consent/copy.test.ts:84-91, 223-229`, listing, pricing and privacy pages | `AddPlantScreen.tsx:138-315`; `mobile/src/photoId/` |
| `plant-id` native `identify()` and Vision step | delete | Same; keep `isAvailable()` and `generate()` while the gnome voice exists | S | Native rebuild; module name must stay `PlantId` | `PlantIdModule.swift:39-59, 91-109` |
| PlantDetailScreen | refactor | Secondary plant page; add seasonal tasks; leave photo diagnosis behind its gate | M | 1.1.3 calls `/advice` and `/diagnose-photo` | `mobile/src/screens/PlantDetailScreen.tsx` |
| SpeciesScreen as a top-level tab | refactor | Becomes the "Will this plant work?" search across zones | M | Whole catalog in one request | `mobile/src/screens/SpeciesScreen.tsx`; `mobile/src/api/species.ts:9` |
| SpeciesDetailScreen | keep | Sources card already shows reason and source | S | `factReport.test.ts:141` | `mobile/src/screens/SpeciesDetailScreen.tsx` |
| AlmanacScreen | refactor | Mode 2 base; scope to a zone, rank natives first | M | Unmerged branch edits it | `mobile/src/screens/AlmanacScreen.tsx` |
| Almanac difficulty tier | defer | Houseplant difficulty; would mis-grade sun-lovers outdoors | S | `tier.test.ts` (25) | `mobile/src/almanac/tier.ts:3-8, 78-81` |
| GrowingAreasScreen and create modal | refactor | Address moves to the property; zones sketched and tagged; values prefilled with override | L | `POST /growing-areas/` must accept the 1.1.3 payload; `realEstate.test.ts` (36) | `GrowingAreasScreen.tsx:84-425` |
| GrowingAreaDetailScreen | refactor | Becomes the Zone Profile: each value with source, confidence, override; editable | L | Unmerged branch edits it (+67/−32); no screen tests | `GrowingAreaDetailScreen.tsx:80-548` |
| Census tab and CensusScreen | delete | Species-inventory dashboard; serves none of the four modes | S | `census.keys.test.ts`, `census.test.ts:127`, `loadFailed.test.ts`; keep the server route and opt-in switch | `mobile/src/screens/CensusScreen.tsx`; `App.tsx:163-171` |
| Streaks and badges | delete | Reward plant counts, care volume and streak length; work against minimal effort | S | `streaks.test.ts` (6); no backend | `mobile/src/streaks/streaks.ts:196-216` |
| CareTodos ("Checks for today") | refactor | Daily surface for seasonal tasks; add a reason and source line | M | Fan-out load does not scale to a property plan | `mobile/src/care/CareTodos.tsx`; `api/plants.ts:62-112` |
| CareCalendar | refactor | Month grid shows predicted events instead of next-due checks | S | No tests | `mobile/src/care/CareCalendar.tsx` |
| Care task computation | refactor | Add zone and property tasks that need no plant inventory | M | `schedule.test.ts` (19); shares grace days with streaks | `mobile/src/care/schedule.ts:65-171` |
| Settings: care reminders card | refactor | Phase 1: switch off or season-gate "Feeding checks" now, since it contradicts "skip fall fertilizer" | M | SecureStore prefs to migrate | `SettingsScreen.tsx:31-49, 295-340` |
| Settings: account, delete, appearance, privacy, about | keep | Rewrite the About text ("Every plant deserves an advocate") | S | `consent/copy.test.ts` (20) | `SettingsScreen.tsx:192-243, 343-440` |
| Theme (Almanac / Observatory) | keep | Field-notebook look suits stewardship | S | Following system dark mode needs a native rebuild | `mobile/src/theme/` |
| Evidence components (FitFindingRow, AreaFitCard, CareFacts, WeatherCredit, Report*) | keep | They already show reason and source; extend the genus pill into a confidence marker; fix the Apple credit | S | `facts.test.ts` | `mobile/src/components/` |
| General components (EmptyState, LoadError, RefreshFailed, Pill, Eyebrow) | keep | Neutral, honest empty and failed states | S | `loadFailed.test.ts` | `mobile/src/components/` |
| AddressPicker and location helpers | keep | Phase 1 starts with an address; offer more than the first hit, allow change | S | Location purpose string pinned (`appConfig.test.ts:59-60`) | `mobile/src/components/AddressPicker.tsx`; `mobile/src/location/` |
| placement.ts default-area rule | refactor | Default to the whole-lot zone, not the oldest area | S | `placement.test.ts` (8) | `mobile/src/growingAreas/placement.ts:12-40` |
| realEstate.ts presets and notes | refactor | Presets become estimates with confidence | M | `realEstate.test.ts` (36) | `realEstate.ts:77-95, 253-308` |
| Client types | refactor | Add Property, Zone and site-condition types; add only, never rename | M | 1.1.3 has the old types compiled in | `mobile/src/types/index.ts:179-235` |
| Login screen and required sign-in | keep | Rewrite tagline and sign-in reason; drop "anonymized" from the census footer | S | `loginCopy.test.ts`; App Review expects a reason for required login | `mobile/src/auth/loginCopy.ts:10-11`; `LoginScreen.tsx:112-115` |
| Android remnants | defer | Not in the brief; costs nothing while dormant | S | The preview profile still builds an Android app package (APK) | `mobile/app.json:83-96`; `mobile/eas.json:22-24` |

### 4.2 Backend data model, persistence and routes

| Component | Verdict | Reason | Effort | Risk | Evidence |
|---|---|---|---|---|---|
| User, identities, tokens, Apple revoke queue, `/auth/*` | keep | Identity is unchanged | S | 1.1.3 calls `/auth/apple`, `/auth/google`, `/auth/refresh`, `/auth/logout` | `models.py:248-310`; `garden-gnome/app/db/revocations.py:28`; `auth.py:128-228` |
| `DELETE /me` | refactor | Must delete every new user-owned table | M | A missed table orphans personal data silently | `auth.py:372-431`; `tests/test_account_deletion.py` |
| `PATCH /me`, `census_opt_in` | keep | Consent toggle | S | 1.1.3 Settings reads it (`SettingsScreen.tsx:356`); `GET /me` is not called by 1.1.3 | `auth.py:227-229, 434-447` |
| `GrowingArea` model | refactor | Becomes the Zone: add nullable `property_id`, `vegetation_type`, outline GeoJSON, `is_whole_lot`; new outdoor default; archive or merge instead of a hard delete | M | No renames or new enum values; `uuid` must survive; the 409 delete guard | `models.py:596-637`; `growing_areas.py:126-153` |
| Default "My Home" at sign-up | refactor | Becomes property plus an outdoor whole-lot zone once an address is given; keep something 1.1.3 can list | M | `test_scoping.py:134`; review notes | `auth.py:88-98`; `plants.py:64-84` |
| `Plant` model | keep | Species-level enrichment; do not make `species_id` nullable | S | A nullable rebuild would break 1.1.3 | `models.py:640-690` |
| `CareLog`, Check/Outcome/Care-window model | keep | "Looked and it didn't need doing" is already a success, which is the low-impact stance | S | 1.1.3 posts these outcomes | `models.py:50-74, 693-703` |
| `StewardshipRecord`, transfer, stewardship routes | keep | 1.1.3 calls them; possible future hand-off base | S | Removal breaks 1.1.3 | `models.py:706-725`; `plants.py:225-375` |
| `CareSchedule` | keep | Serves potted plants and the 1.1.3 to-do list; build seasonal tasks beside it | S | 1.1.3 reads `care_schedules` | `models.py:506-515` |
| `SpeciesTrait` | keep | Neutral legacy; never rank on uncited `native_region` | S | Low | `models.py:518-526` |
| `SyncState` | keep | Boot sync gate and catalog generation | S | None | `models.py:581-593` |
| Persistence: SQLite, one volume, Alembic at boot | keep | Adequate for phase 1 with JSON outlines and derived geodata. Before any background job writes, set `PRAGMA journal_mode=WAL` (write-ahead logging) and `PRAGMA busy_timeout` in `app/db/database.py`. Turn on `foreign_keys` only after checking for orphaned rows. Set a tier for running costs | S | No WAL or busy timeout today; volume documented as 1 GB (`README.md:202`) | `garden-gnome/app/db/database.py`; `fly.toml:13-15` (mount) |
| Deploy pipeline | keep | Add an automatic snapshot when `alembic/versions` changes; fix the stale `min_machines_running` notes (`ci.yml:104`, `docs/deploys.md:63`, `docs/app-store/README.md:67`, `docs/app-store/review-notes.md:162`) | S | Migrations apply before anyone can check them | `.github/workflows/ci.yml`; `docs/deploys.md` |
| `/plants/` create, read, update and delete (CRUD) and `/plants/bulk` | keep | 1.1.3 depends on them; zone capture gets a new endpoint | S | Any field removal breaks 1.1.3 | `plants.py:148-224` |
| `/plants/{id}/advice` | refactor | Per-plant view of stored, sourced seasonal tasks; add fields only | M | 1.1.3 parses it and rewords it on device | `plants.py:509-573` |
| `/diagnose-photo`, `/split`, `/timeline*` | defer | Not phase 1; `diagnose-photo` is called by 1.1.3 and is a paid path if switched on | S | Deleting `diagnose-photo` breaks 1.1.3 | `plants.py:288-360, 415-507, 575-631` |
| `growing_areas` router (CRUD, weather, candidates, misfits, fit) | refactor | Keep paths for 1.1.3; add `/properties/...` and a species-across-zones read reusing `fit` | L | Bare-list candidates body plus `X-Total-Count` | `growing_areas.py:40-286` |
| `/environments` alias and `environment_id` aliases | delete | Only TestFlight 1.1.2 used them, and by its upload date that build should have expired around 2026-10-31; confirm, then remove. The aliases reach beyond `schemas.py:189-243` into plant, transfer and census schemas | S | 15 legacy tests; the `/ui` console | `growing_areas.py:291-294`; `schemas.py:258, 389, 419, 430, 462`; `census.py:89-91` |
| Static `/ui` console | delete | Built on `/environments`; same pull request as the alias | S | Low | `garden-gnome/app/static/index.html`; `main.py:84-88` |
| `census` router | defer | `/census/summary` stays for 1.1.3; export and sync stay operator-only (404 while the token is unset); add no zone data | S | Census field lists are public in three places | `garden-gnome/app/routers/census.py` |
| `ai` router (`/ai/status`) | keep | 1.1.3 calls it (the smoke check only prints it) | S | None | `garden-gnome/app/routers/ai.py`; `ci.yml:126` |

### 4.3 Weather and reminders

| Component | Verdict | Reason | Effort | Risk | Evidence |
|---|---|---|---|---|---|
| WeatherKit REST client and JWT signing | keep | Brief names WeatherKit; takes over when Apple enables it. Add a circuit breaker and a quota guard; fix the credit | S | Never answered in production; the code has no limit on calls, so if Apple enables it, calls beyond the 500,000-a-month allowance would need a paid WeatherKit plan | `weather.py:32-37, 105-209` |
| Normalized payload and 2-decimal rounding | keep | Provider-neutral; credit travels with data | S | Field renames break 1.1.3; rounding is a published promise | `weather.py:90-97, 159-188` |
| NWS fallback | keep | Public domain, free, what answers in the U.S. today; cache its `/points` lookup | S | No UV or daylight; up to 4 calls | `weather.py:71-84, 273-373` |
| Open-Meteo fallback | refactor | Behind a config switch; license or remove before any paid feature | S | Changes the recipient list in privacy copy | `weather.py:39-60, 212-270` |
| In-process weather cache | refactor | Persisted per-property store with provider, fetch time and eviction; stores daily highs and lows for GDD | M | New table; no client impact | `weather.py:87, 100-102, 387-400` |
| Weather service as a whole | refactor | Seasonal engine depends on it: needs history, a horizon decision (5 vs 10 days), persistence and a licence decision | M | See sections 3.4 and 6.6 | `weather.py`; `growing_areas.py:79-107` |
| Area weather endpoints | keep | 1.1.3 weather card and reminder signal | S | 1.1.2 uses the alias | `growing_areas.py:79-107` |
| `weather_attribution` on advice | keep | Pattern for every task; fix its meaning (sent when fetched, not when used) | S | 1.1.3 reads it | `plants.py:540-572` |
| Rain, heat, cold and UV nudges | refactor | Seed of the frost task: stored events per zone, a 32°F rule, first-frost detection, container targeting, shared thresholds, ⚠️ prefix for frost lines | M | `test_advisor_weather.py` (18 cases) | `advisor.py:276-357` |
| Language-model prompt weather blocks | defer | Production is rule-based | S | Switching on needs consent work | `advisor.py:65-84, 143-178` |
| Exposure gates (shelter, temperature exposure, sun, `weather_applies`) | refactor | Defaults are stored as answers, and the brief needs confidence and override | M | 1.1.3 sends and reads these tokens | `models.py:141-155, 617-619`; `advisor.py:107-118` |
| Calendar season gates (feeding Mar-Oct, server and phone) | refactor | Drive from the property's season state; months only for indoor or unlocated plants; one consistent clock | M | `plan.season.test.ts` (9), `test_advice_rules.py`; `listing.md:115, 188` promise today's behaviour | `plan.ts:21-38`; `advisor.py:366-393` |
| February repot check | keep | Still right for pots indoors | S | `plan.inspection.test.ts` (7) | `plan.ts:57-74` |
| Local reminder planner and scheduler | refactor | Keep batching under iOS's 64-notification cap; add seasonal events and a reason line; reschedule on return to the foreground and when the forecast changes (today only a cold launch or sign-in, a care log, an added plant or a Settings change re-plans); fix the dropped-call race | M | About 30 plan tests; avoid double alerts with push | `plan.ts:91-294`; `reminders.ts:139-219`; `App.tsx:209-213` |
| Weather-shifted watering | refactor | Fold into the seasonal engine as a suggestion only, with no automatic action; the notification never says weather moved it, and the Settings copy is wrong | S | `signal.test.ts` (7) | `mobile/src/weather/signal.ts`; `SettingsScreen.tsx:318-335` |
| "Outside → in here" card | refactor | Zone or property view; write "ultraviolet (UV)" | S | `translate.test.ts` (9) | `translate.ts`; `GrowingAreaDetailScreen.tsx:461-543` |

### 4.4 Voice and photo

| Component | Verdict | Reason | Effort | Risk | Evidence |
|---|---|---|---|---|---|
| Speech module (`plant-speech`) | keep | Text from speech serves zones unchanged; fix the swallowed errors, interruptions and Settings route | S | Native rebuild for fixes | `mobile/modules/plant-speech/` |
| Walk the garden screen | refactor | Cards take a vegetation type; unmatched items become zone vegetation, not plants; cards target a zone and save to a new endpoint | L | Listing, review notes and screenshot 8 describe today's flow | `CaptureGardenScreen.tsx` |
| Utterance splitter | refactor | Vegetation nouns, place phrases, measure words, site statements | M | `splitUtterance.test.ts` (11) | `splitUtterance.ts` |
| Species grounding | refactor | Ground to vegetation types and zone names first, species only when one was named | M | `ground.test.ts` (9) | `mobile/src/capture/ground.ts` |
| Chunked bulk save | keep | Generic and well tested | S | Its test reads the 200 limit from `schemas.py` | `bulkSave.ts` |
| Live camera backdrop | delete | It records nothing, but it needs a "Turn the camera on" button and is a stated purpose in the camera string; phase 1 ships the tap override only | S | `appConfig.test.ts:57` | `CaptureGardenScreen.tsx:240-244, 312-316`; `app.json:126` |
| Phone-side matcher (`fuzzyMatch.ts`) | keep | Offline species lookup for mode 3; move out of `photoId/`; never the first pass for yard words | S | Parity fixtures shared with `evals/fuzzy_mirror.py` | `mobile/src/photoId/fuzzyMatch.ts` |
| Server `/species/identify-photo`, `vision.identify_species` | delete | No app caller since 2026-07-11; a test forbids one. The brief says the app is not a plant identification app | S | 5 tests in `test_vision.py`; README lines | `species.py:240-285`; `vision.py:309-404` |
| `garden-gnome/evals/` harness | delete | Grades on-device identification only. Note: it holds `fuzzy_mirror.py`, the parity partner named by `fuzzyMatch.test.ts:4-7`; that comment must change | S | Parity comment goes stale | `garden-gnome/evals/` |
| Server name matcher (`name_match.py`) | delete | Its only caller goes with identify-photo, the phone matcher stays, and its tie-break already disagrees with the phone | S | 9 tests | `garden-gnome/app/services/name_match.py`; `vision.py:32` |
| Gnome voice restyle and drift guard | refactor | Add an omission check and outdoor verbs (mulch, rake, leave leaves, cut back, bring inside, cover) before it touches seasonal text | M | `restyle.test.ts` (36); 1.1.3 keeps the old guard | `mobile/src/gnomeVoice/restyle.ts` |
| Gnome persona and branding | defer | Owner decision; do not extend to site or seasonal surfaces | S | Many copy and test touch points | `mobile/src/gnomeVoice/persona.ts` |
| Server persona contract and grounding guard | keep | Brand-neutral rules for any model-written text | S | Inert while backends are stub | `garden-gnome/app/services/persona.py`; `grounding.py` |
| Permission strings and privacy copy for voice, camera, photos | refactor | Must describe what each permission is now for | S | `appConfig.test.ts`, `consent/copy.test.ts` | `mobile/app.json:80, 123-137`; `consent/copy.ts:118-128` |

### 4.5 Catalog and advisor

| Component | Verdict | Reason | Effort | Risk | Evidence |
|---|---|---|---|---|---|
| Claim graph (loader, resolver, recompute, sync) | keep | It is how "reason and data source" is true for plant facts; new species fields go through it | S | Each field bumps `RESOLVER_VERSION` | `garden-gnome/app/data/claims/` |
| Authority registry | refactor | Native status and phenology need sources; widen USDA PLANTS by ADR (architecture decision record). No row to migrate | S | Licence vetting (ADR 0001) is the real cost | `authorities.py:50-79` |
| Verified tranche (134 files) | keep | Holds sun, drainage, soil, size and pollinators; backfill hardiness, habit, leaf retention, native status, moisture tolerance | S | `test_claim_ingest.py:401` pins 10,681 | `garden-gnome/app/data/verified/` |
| Harm-capable rules | keep | Hardiness and frost tenderness should join them | S | Coverage loss when sources disagree | `resolve.py:69-97` |
| Species fit fields | refactor | Start using drainage and pH; add new cited fields | L | Each field: migration, backfill, mobile type | `models.py:351-446` |
| Container and indoor care fields | keep | Still valid for pots | S | None | `models.py:351-386` |
| Legacy uncited columns (`temp_f_min` etc.) | refactor | New engine must not read them; drop only after 1.1.3 retires | M | 1.1.3 reads them | `models.py:329-336`; `advisor.py:350-357` |
| ~1,900 uncited rows imported from Perenual | defer | Exclude from candidates and the engine now; delete unreferenced rows later | M | Plants reference them by required foreign key | `garden-gnome/app/data/expansion/README.md:28` |
| Curated catalog and calendar schedules | refactor | Keep for pots; do not extend to landscape plants | M | 1.1.3 reminders read schedules | `species_catalog.json`; `seed.py` |
| `native_region` trait | refactor | Uncited; never rank on it; replace with a cited field | S | Shown on species detail | `species_catalog.json` |
| Toxicity service | keep | Hazard sentences protect households | S | `test_toxicity.py` (72) | `garden-gnome/app/services/toxicity.py` |
| Candidate rule and `never_a_candidate` | refactor | Invasive status must become a cited, regional field, and the database-error path fails open. Keep zero-misfit, one-fit | M | `test_fit.py`, real-catalog tests | `fit.py:496-561`; `toxicity.py:1075-1078` |
| Care fact block | refactor | Container wording ("the medium"); spell out authority acronyms | M | `test_care_facts.py` (27) | `garden-gnome/app/services/care_facts.py` |
| Rule-based advisor | refactor | Becomes seasonal tasks; drop Sept-Oct feeding, the `temp_f_min` fallback and the houseplant framing | L | 1.1.3 calls `/advice`; ~41 tests | `advisor.py:276-520` |
| Anthropic advisor backend | defer | Off in production; paid per call | S | Consent work if switched on | `advisor.py:181-262, 522-556` |
| Photo diagnosis (`vision.diagnose_photo`) | defer | Off in production; 1.1.3 calls the route; paid if switched on | S | Keep the route answering | `vision.py:211-305, 404-419`; `mobile/src/api/plants.ts:254` |
| Language-model species generator (`/species/generate`) | delete | Writes uncited records; stub defaults `toxic_to_pets` to False | S | Operator only; keep the enum value | `garden-gnome/app/services/catalog.py:70-84` |
| Operator `POST /species/` and `/species/bulk` | defer | New species arrive through the tranche | S | No client caller | `species.py:165-212` |
| `GET /species/`, `GET /species/{id}` | keep | Behind all four modes; add fields only | S | Payload grows on a 512 MB machine | `species.py:136-165, 288-293` |
| Legacy Perenual expansion pipeline | delete | Produced the uncited rows; nothing at runtime imports it. `test_hybrid_names.py` must be rewritten, not deleted | M | ~117 test functions; ADR 0004 needs a note | `garden-gnome/app/data/expansion/` |
| Catalog landing and backfill tools | keep | How new fields land with citations | S | None | `garden-gnome/scripts/catalog/` |

### 4.6 Fit engine and areas

| Component | Verdict | Reason | Effort | Risk | Evidence |
|---|---|---|---|---|---|
| Fit engine core (`assess`, Finding, verdicts, Unknown rule) | refactor | Takes a Zone Profile; each Finding gains a site source and confidence in a new field, never a fourth verdict | L | 1.1.3 filters exact verdict strings (`fitFindings.ts:51-82`) | `fit.py:72-135, 461-501` |
| Ranking (score, A to Z) | refactor | Natives first, then confirmed checks; show "confirmed on N checks" | M | 1.1.3's sentence "where they tie, it's A to Z" becomes untrue | `fit.py:485-531`; `ranking.ts:21-22` |
| Sun axis | refactor | Terrain estimate plus tap; keep tokens, relabel "Partial" as "Part shade" | M | `_AREA_SUN_WORDS` raises on unknown tokens | `fit.py:167-226` |
| Soil axis | refactor | Keep the pot-versus-bed check; add a drainage axis against the soil survey | M | Needs a drainage-class mapping | `fit.py:229-288` |
| Footprint axis | keep | Outline gives square feet | S | Long, narrow beds | `fit.py:291-368` |
| Upkeep axis | refactor | Needs outdoor measures; `water_regime` is container-based (339 records) | M | `low_upkeep` token must stay | `fit.py:371-403` |
| Goals and `GrowingGoal` | refactor | Add the brief's goals, then follow-up question and plan | L | Removing `edible` breaks 1.1.3 create | `fit.py:406-456`; `models.py:127-134` |
| Indoor/outdoor axis | keep | "What to bring inside" needs it | S | None | `fit.py:137-164` |
| No cold or hardiness axis | refactor | Zone-to-zone axis under a new ADR; Unknown until species research lands. Not barred by ADR 0006 | L | Rewrites the docstring; `test_fit.py:469-476` only bans two words | `fit.py:40-49` |
| Location fields on the area | refactor | Move to the property | M | 1.1.3 gates weather on area lat/lng | `models.py:611-615` |
| `GrowingAreaType` | refactor | A property-level fact; `nursery` stays as a dormant label | S | Census groups by it | `models.py:92-101` |
| `GrowingSurface` | refactor | Keep for pots; vegetation type is a separate field | M | Never add surface values (blank label on 1.1.3) | `models.py:109-124`; `GrowingAreasScreen.tsx:40`; `GrowingAreaDetailScreen.tsx:257` |
| Measurements, "blank means unknown" | keep | Area computed from the outline, labelled so | S | Tests pin null | `models.py:621-632` |
| `soil_depth_in` | defer | No fit axis reads it (the phone shows it and notes that it is unchecked: `GrowingAreaDetailScreen.tsx:216`; `realEstate.ts:142-147, 300-305`) | S | 1.1.3 sends it | `models.py:630` |
| Candidates and misfits routes | keep | Serve modes 2 and 1 | S | Candidates route runs about one query per species | `growing_areas.py:163-251` |
| Species-fit route | refactor | Add an across-zones read for mode 3 | M | 1.1.3 calls `/fit/{id}` | `growing_areas.py:252-285` |
| `CONTEXT.md` glossary | refactor | Add Property, Zone, Site condition, Estimate, Override | S | None | `CONTEXT.md:86-127` |

### 4.7 Accounts, privacy, site and branches

| Component | Verdict | Reason | Effort | Risk | Evidence |
|---|---|---|---|---|---|
| Consent copy module | refactor | Add a property site-lookup flow; spell out USDA (U.S. Department of Agriculture), USGS (U.S. Geological Survey) and MRLC (Multi-Resolution Land Characteristics consortium); demote identify | M | 20 pinned tests | `mobile/src/consent/copy.ts` |
| Privacy manifest and purpose strings | refactor | Location string covers only a forecast; drop the Analytics purpose with the census tab if unused | S | `appConfig.test.ts`; manifest must match App Privacy | `mobile/app.json:14-80, 140-146` |
| Privacy policy | refactor | New recipients, precision, deletion list, push | M | Binding; deployed by hand | `site/privacy.html:134-182` |
| App Privacy answers | refactor | Physical Address, Photos, Device ID only if adopted | S | Changeable without review | `docs/app-store/app-privacy.md` |
| Store listing, screenshots, review notes | refactor | Repositioning needs a new version | M | 1.1.3 text must stay true for 1.1.3 | `docs/app-store/listing.md` |
| Marketing pages (index, how-it-works, FAQ) | refactor | Site first | M | Rebase on `launch-day-site` | `site/index.html:293` |
| `site/recommendations.html` | delete | Houseplant picks with no sources; replace with a yard page or redirect | S | Linked from every footer | `site/recommendations.html:246-289` |
| Pricing page | refactor | Keep "free" for phase 1; remove the photo-ID tick | S | "No subscriptions" repeated widely | `site/pricing.html:248-290` |
| Nursery partner page and teasers | defer | Landscaper and B2B (business-to-business) ideas are kept dormant; retitle at repositioning, claim no partners | S | In every nav | `site/nurseries.html` |
| Community-garden demo page | defer | It costs nothing, the policy names it, and `launch-day-site` edits it. Drop it with the repositioning site change | S | Policy sentence | `site/community-garden.html`; `site/privacy.html:187` |
| Go-to-market strategy, product-truth, fact sheet | refactor | Strategy contradicts the brief; rewrite only after the build ships | M | Unshipped claims | `docs/go-to-market/strategy.md:17, 33, 43, 51` |
| Superseded privacy corrections doc | delete | Marked "Do not paste" | S | Dangling references | `docs/privacy-policy-corrections.md:3` |
| Branch `care-notes-1.1.4` | keep | Content only (4 files), ties curated notes to cited records | S | First check the 26 care-note sentences that rest on Missouri Botanical Garden pages (`handoff:31-34`) | `origin/care-notes-1.1.4` (0451683) |
| Branch `candidate-categorization-proposal` | defer | 142 files, migration 0023, `RESOLVER_VERSION` 7, edible focus not in the brief. Land `weed_listing` alone after the first backend deploy succeeds | S | Holds Alembic slot 0023; edits `fit.py`, `GrowingAreaDetailScreen.tsx`, `models.py`, `schemas.py` | `origin/candidate-categorization-proposal` (9cc32cb) |
| Branch `claude/launch-day-site` | keep | 1.1.3 launch-morning site; overhaul builds on it | S | Press page denies frost features | `origin/claude/launch-day-site` (d279afc) |
| Branch `care-advice-honesty` | defer | Fully merged (pull request 22, `ec248bb`); the launch runbook still names it as the ship branch, so update that reference, then the branch can be deleted at the owner's choice | S | Checklist references | `origin/care-advice-honesty` (65ecf93) |
| Dormant per the brief: landscaper connection | defer | Nothing exists to keep; build nothing | — | Do not claim partners | section 3.7 |
| Dormant per the brief: automated care recommendations | defer | Read here as care carried out or scheduled without the owner (for example irrigation control, or a care service acting on the plan), as distinct from the seasonal engine's suggestions. Nothing exists. The rain-delay watering shift is folded into the seasonal engine (4.3) as a suggestion only and gains no automatic action | — | — | `mobile/src/weather/signal.ts:19-23` |

### 4.8 To build new

These do not exist yet, so they get no keep, refactor or delete verdict.

- **New tables:** property, site_condition, geodata_cache, seasonal_event, care_task (effort L). They carry the Zone Profile, per-value confidence and override, the geodata cache and the seasonal plan. Each must be added to `delete_me` or reached by a cascade from a row it deletes (`auth.py:386-424`), and their migration numbers must be agreed against the 0023 on the unmerged branch (open question 4). These names are this audit's placeholders; PLAN.md section 5 fixes the tables: property, site_reading, site_override, geodata_tile, forecast_cache, observed_cell_season, season_event_state and provider_usage (no care_task table: the seasonal plan is computed on each request).

---

## 5. Vision coverage matrix

| Brief element | Status | Closest existing code and notes |
|---|---|---|
| Property (address, parent of zones) | absent | Location lives on each area (`models.py:611-615`) |
| Zones as rough polygons | absent | Point plus typed square feet; no map library |
| Zone tags: tree / shrub / grass / garden bed / bare-hardscape | partial | `GrowingSurface` covers beds, containers, indoor spots and water (8 values, `models.py:109-124`); none is tree, shrub, grass or hardscape |
| Species optional | absent | Conflicts: `models.py:646`; `AddPlantScreen.tsx:190`; `CaptureGardenScreen.tsx:192` |
| Default whole-lot zone | partial | "My Home" (`auth.py:92-97`), but indoor, unlocated, offers houseplants only |
| Address entry | partial | `AddressPicker.tsx`, `lookup.ts:12-39`; optional, per area, first hit only |
| Soil from Soil Data Access (SSURGO, the Soil Survey Geographic Database) | absent | Species-side `soil_drainage` (787 claims) is unused by fit. Spike: reachable, 130-750 ms |
| Slope, aspect, water collection from USGS 3DEP (U.S. Geological Survey 3D Elevation Program) | absent | Spike: works but slow (6-10 s cold) and flaky; run in background |
| Land cover from NLCD (National Land Cover Database) | absent | Spike: about 200 ms; newest layer only under a `-wmstest` name; lower 48 states only |
| USDA hardiness zone | absent | Species side dropped in 0016 (`0016_outdoor_temp_min_f.py`). Spike: ZIP lookup via phzmapi.org, or a local copy of the 2023 map |
| WeatherKit | partial | Client exists and runs first; refused since July (`weather.py:40`) |
| Sun computed, then corrected | partial | Owner three-way choice at creation only; spike shows terrain-only sun is always "full sun" and needs house and tree shade from the owner |
| Confidence and owner override per value | absent | Pattern: `care_provenance` / `care_sources` (`models.py:391-404`); genus pill (`FitFindingRow.tsx:12-24`) |
| Mode 1: What's here? | partial | Plant list per area (`GET /plants/`) and Walk the garden capture (`CaptureGardenScreen.tsx`) record what is here, species only. The misfits route (`growing_areas.py:216-251`) adds "and what is struggling". No site conditions or vegetation types |
| Mode 2: What belongs here? (natives first) | partial | `fit.candidates` ranks and excludes invasives (`fit.py:534-581`); no native field |
| Mode 3: Will this plant work? (score per zone, limiting factor) | partial | `fit.score` and misfit sentences (`fit.py:485-511, 224-226`); one area per call |
| Mode 4: Help me get there (goal → targets) | partial | Three goals as list filters (`models.py:127-134`); no plan, no targets |
| Seasonal engine triggered by weather | partial | Watering shift (`signal.ts`), on-demand nudges (`advisor.py:276-357`); calendar gates dominate |
| First frost → bring potted plants in | partial | Cold nudge "bring it in or shelter it" (`advisor.py:320-335`); no 32°F rule, no first-of-season detection, no task |
| GDD for dormancy, leaf drop, spring emergence | absent | No history, no species thresholds; spike computed GDD from Open-Meteo's archive |
| Low-impact guidance | partial | Check-not-chore wording, misting removed, winter feeding rest; conflicts with Sept-Oct feeding (`advisor.py:370`) |
| Seasonal plan per property | absent | `CareCalendar.tsx` is per area, next-due checks |
| Optional push | partial | Local notifications only. Reminders re-plan only on a cold launch or sign-in, a care log, an added plant or a Settings change (`App.tsx:211-213`; `CareTodos.tsx:78`; `AddPlantScreen.tsx:125`; `SettingsScreen.tsx:147, 166`), never on return to the foreground and never when the forecast changes |
| Minimal owner effort | partial | Voice capture is low effort; area setup is all manual |
| Cache geodata per property | absent | Only the in-memory weather cache |
| Every recommendation shows reason and source | partial | Species facts and fit findings do; site values, notifications and check intervals do not |
| Acronyms spelled out | partial | "UV", "AI", "UF/IFAS Extension" reach users |
| Not a plant identification app | partial | Server route unused; in-app photo ID and the pricing tick remain |
| Speak-in-and-batch entry | exists | `CaptureGardenScreen.tsx`; needs vegetation types; items without a species go to zones (3.2) |
| Landscaper connection (dormant) | absent | Site copy only (`site/nurseries.html:256`) |
| Automated care recommendations (dormant) | absent | Rain-delay signal only |

---

## 6. Constraints and risks

### 6.1 Release state

- **1.1.3.** Uploaded 2026-11-12 after App Store Connect rejected build 18 for a missing motion purpose string (error 90683; fix in commit `080d7d0`, `mobile/app.json:145`). It has never been seen by App Review. The upload date and review status were supplied with this task; the repo itself does not record them, and its last dated handoff block is 2026-11-01. The listing, review notes and screenshots describe the plant-first product and must stay accurate while 1.1.3 is the live build.
- **Production backend.** The repo last recorded the July build at Alembic 0009 (2026-10-31), but on 2026-11-13 the live API published master's 34 public paths, including `/growing-areas` (section 2.3). A master-era build has deployed; its exact commit and migration level still need confirming.
- **Unmerged branches** (ahead/behind master):

| Branch | Ahead / behind | What it holds |
|---|---|---|
| `care-notes-1.1.4` (0451683) | 19 / 17 | Content only |
| `candidate-categorization-proposal` (9cc32cb) | 10 / 8 | Migration 0023, 142 files (101 batch files), mobile edits to `GrowingAreaDetailScreen.tsx`, `AlmanacScreen.tsx`, `ranking.ts`, `realEstate.ts`, `care/facts.ts`, `api/growingAreas.ts`, `types/index.ts` and a new `growingAreas/eating.ts` (12 mobile files in all, tests included) |
| `claude/launch-day-site` (d279afc) | 7 / 12 | `site/` only |
| `care-advice-honesty` (65ecf93) | 0 / 8 | Fully merged (pull request 22, `ec248bb`) |

Also present: `rescue/deployed-production` (1 unique commit, the archived production source) and `claude/database-build-goals-e548af` (1 unique commit). Six `worktree-wf_adf477fc-b3d-*` branches remain. Three of them (-1, -2, -4) touch `advisor.py`, `weather.py` and reminder files, but all changes on all six are already on master (`git cherry`). There are 23 remote branches in all.

### 6.2 Deploy on master

Any merge to master ships to production within minutes, with migrations at boot and no database rollback. Overhaul work must land as additive schema (new tables, nullable or server-defaulted columns) behind code paths 1.1.3 cannot reach, or stay on a branch. Take a volume snapshot before each migration deploy.

### 6.3 SQLite migration hazards

- No transactional schema changes; a failed migration leaves a half-applied file (0017 precedent).
- No NOT NULL on existing tables; nullability changes rebuild the table (0015).
- 0018's downgrade deletes measurements owners typed.
- Foreign keys are not enforced, so orphaned rows fail silently.
- Alembic slot 0023 is taken on an unmerged branch; decide the order before phase 1 adds migrations.
- Python 3.12 in production versus 3.14 locally: a green local run does not prove 3.12 behaviour.

### 6.4 Shipped-client compatibility surface (1.1.3)

**Routes 1.1.3 calls:**

- **Auth and profile:** `POST /auth/apple`, `/auth/google`, `/auth/refresh`, `/auth/logout`; `PATCH /me` and `DELETE /me` (not `GET /me`); `GET /ai/status`.
- **Catalog:** `GET /species/` (the whole list, matched on the phone by `id`, `common_name`, `scientific_name`) and `GET /species/{id}` (with `care_schedules` and `traits`).
- **Plants:** create, bulk, list, get, delete, logs (get and post), advice, diagnose-photo, transfer, stewardship.
- **Growing areas:** list, get, post, patch, weather, candidates (a bare list plus `X-Total-Count`), misfits, fit.
- **Census:** `GET /census/summary`.
- Evidence: `mobile/src/api/*.ts`; `mobile/src/auth/signIn.ts:63, 94`; `mobile/src/auth/AuthContext.tsx:75, 86`.

**Tokens and shapes that must not change:**

- **Enums.** Removing any value of `SunExposure`, `TempExposure`, `Shelter`, `GrowingSurface`, `GrowingAreaType` or `GrowingGoal` makes 1.1.3's create fail with 422. A new surface value shows a blank label. A new verdict value silently drops findings. New goals and new axes are safe.
- **Ranking.** A natives-first order makes 1.1.3's "where they tie, it's A to Z" untrue on installed phones.
- **Advice text.** Any advice text sent to 1.1.3 that must not be reworded needs a ⚠️ prefix.
- **Reminders on the phone.** Notifications already scheduled on a 1.1.3 phone cannot be changed from the server.
- **TestFlight 1.1.2** (build 15, uploaded 2026-08-02) should have expired around 2026-10-31, since builds expire after 90 days. Confirm in App Store Connect; if it has, nothing installed uses `/environments`.

### 6.5 App Store privacy and purpose strings

Each of these becomes false under the vision and must change in a set order:

- **Rounding and the typed address.** "Rounded to about a kilometer" and "we don't keep the address you typed" (`site/privacy.html:140`). Parcel lookups need finer coordinates, so split the promise by recipient.
- **Recipients.** The policy names Fly.io, Apple, Google, three weather services, Anthropic and Cloudflare (`privacy.html:166-176`). Soil Data Access, The National Map and MRLC (the Multi-Resolution Land Characteristics consortium) are missing.
- **Push.** "Care reminders are scheduled on your phone and are not sent to us" (`privacy.html:139`) and "no push token" (`docs/app-store/app-privacy.md:72`). Server push adds Device ID.
- **Deletion list.** Account, plants, care logs, growing areas (`privacy.html:179`; `SettingsScreen.tsx:97-99`).
- **Photos and logs.** Photos or Videos and Audio Data are "not collected" (`app-privacy.md:67-68`). Error logs may hold only a 1 km location (`privacy.html:146`), so geodata errors must not log parcel coordinates.
- **Purpose strings and manifest.** The location string names only a growing area's forecast (`mobile/app.json:142`), pinned by `appConfig.test.ts:59-60`. The camera and photo strings promise "Your phone can suggest what it is" and "photo check-ups" (`app.json:126, 134`). The privacy manifest declares Coarse Location and Other User Content with the Analytics purpose, tied to the census (`app.json:42-75`).
- **An easier path.** An address-first flow can skip location permission entirely: geocoding runs on the phone and the address is not stored.

**Order** (from the accounts reader, adopted):

1. Publish the policy and update App Privacy before any overhaul build reaches testers.
2. In that build: consent copy, purpose strings, manifest, deletion dialog, login copy.
3. Backend deploys ahead of the client, still serving 1.1.3.
4. Store text and screenshots ship with the version submission.
5. Marketing, press and strategy copy change only after approval.

### 6.6 Licences and running costs

| Source | Terms (from the data researchers, to confirm before launch) | Implication |
|---|---|---|
| Open-Meteo forecast and archive | Free application programming interface (API) non-commercial; any app with subscriptions or ads counts as commercial; data CC BY 4.0 | Out of licence once anything is paid; the spike's GDD path depends on it |
| Apple WeatherKit | Developer Program allowance (500,000 calls a month per Apple's terms, not recorded in the repo); end-user notice that weather may be inaccurate; may not charge for raw Apple Weather data | Never answered; no quota guard |
| NWS | U.S. government work, public domain | Free; no UV or daylight data |
| Soil Data Access (USDA NRCS, the Natural Resources Conservation Service) | Federal data, no reuse restriction; cite survey area and date | Free |
| 3DEP / The National Map | Public domain | Free; slow and flaky |
| NLCD (USGS / MRLC) | No restrictions; citation requested | Free; unstable layer name |
| 2023 USDA hardiness map (PRISM, the Parameter-elevation Regressions on Independent Slopes Model group, Oregon State) | Reproducible with attribution; terms partly conflict | Prefer a local copy; phzmapi.org is unofficial and names no map edition |
| USDA PLANTS (native status) | Public domain | Candidate authority for native status |
| Catalog publishers | Vetted under ADR 0001; 81% NC State; 288 values rest on Missouri Botanical Garden pages the verify script cannot re-fetch, 47 of them harm-capable (`docs/2026-10-16-app-store-finish-line-handoff.md:564-567`, as of that handoff) | Regional skew to the Southeast |
| Anthropic (advisor, vision), Perenual (expansion pipeline) | Paid per call | Switched off or to be deleted |
| Fly machine with `min_machines_running = 1` | Bills continuously | Revert to 0 after review, or count it in the paid tier |

### 6.7 Test coupling that will break on restructuring

- **Mobile, source-reading tests.** These regex-read screen files and fail on renames or deletions: `onboarding/slides.test.ts`, `care/loadFailed.test.ts:90-126` (a fixed list of screen paths including CensusScreen), `care/facts.test.ts:345-374` (every `.tsx`), `consent/copy.test.ts` (pins the bulk payload keys and the "Walk the garden" wording), `appConfig.test.ts` (purpose-string phrases), `api/census.keys.test.ts`, `growingAreas/fitFindings.test.ts`, `care/factReport.test.ts`, `capture/bulkSave.test.ts` (reads the 200 limit out of `schemas.py`), `care/notAdvice.test.ts:45-72` (reads the species, plant and Add Plant screens by path and walks `src` for `.tsx` files), `auth/signInGate.test.ts:29-39` (LoginScreen).
- **Mobile, behaviour tests that pin today's design:** `tier.test.ts` (25), `realEstate.test.ts` (36), `ranking.test.ts` (13), `plan.*.test.ts` (30), `schedule.test.ts` (19), `signal.test.ts` (7), `translate.test.ts` (9), `restyle.test.ts` (36).
- **Backend:** `test_claim_ingest.py:401` (10,681), `test_candidates_on_the_real_catalog.py`, `test_fit.py` (61 functions built on `GrowingArea` rows), `test_fit_routes.py` (24), `test_advisor_weather.py` (18 cases), `test_advice_rules.py` (calendar feeding gate), `test_care_facts.py` (weather nudge thresholds), `test_weather.py` (16), `test_legacy_client_fields.py` (15), `test_account_deletion.py`, `test_migrations.py` (single head), `test_hybrid_names.py`.
- **No safety net.** No screen or component render tests exist, so screen rewrites are verified only on a simulator or phone.

---

## 7. Test baseline (2026-11-13)

| Suite | Command | Result |
|---|---|---|
| Backend | `.venv/bin/python -m pytest -q -p no:cacheprovider -rfE` in `garden-gnome/` | **7,094 passed**, 0 failed, 0 errors, 0 skipped; about 67 s |
| Mobile typecheck | `npm run typecheck` (`tsc --noEmit`, TypeScript 6.0.3) | **Clean** |
| Mobile Jest | `npx jest --silent --no-watchman` | **557 tests in 50 suites passed**; about 16 s |

Environment notes:

- **Python versions differ.** Locally Python 3.14.7 (the virtual environment was upgraded in place by Homebrew; `pyvenv.cfg` says 3.14.6). CI and the Docker image use 3.12, and `constraints.txt` says its pins were validated on 3.12. Every direct pin matches.
- **Node versions differ.** Locally Node 26.5.0 and npm 11.17.0; CI uses Node 20. Nothing pins the Node version.
- **Jest in the sandbox needed `--no-watchman`.** Watchman could not write `~/.local/state/watchman` there. A normal terminal and CI are unaffected.
- **Deprecation warnings.** About 65,000, mostly `datetime.utcnow()` (`app/routers/auth.py:55`, `app/services/tokens.py:111`).
- **Summary line hidden.** `pytest.ini` already sets `-q`, so an extra `-q` hides the final summary line.
- **Untracked clutter.** A root `tests/__pycache__` and a local `garden-gnome/garden_gnome.db`.
- **Counting note.** Mobile tests count 557 executed cases. The 494 figure in one reader report counted declarations, before `test.each` tables expand.

---

## 8. Open questions for the owner

Each has a recommended default from the readers. Answer the first four before phase 1 is sequenced.

1. **Release state.** Confirm whether 1.1.3 has been submitted and approved, which commit and Alembic revision production runs (the live API matches master's public paths as of 2026-11-13), and whether the 2026-10-20 privacy policy is live. *Default: ship 1.1.3 as is; reposition in a later version such as 1.2.*
2. **Weather source.** WeatherKit is refused, and Open-Meteo is non-commercial. *Default: build the engine on the provider-neutral payload with NWS for U.S. properties; keep WeatherKit first in the chain; pursue Apple; put Open-Meteo behind a switch and license it or drop it before anything is paid. Take GDD history from public-domain sources (NOAA ACIS, the National Oceanic and Atmospheric Administration's Applied Climate Information System, or a daily NWS log) rather than Open-Meteo's archive.*
3. **Push for frost alerts.** *Default from the data and accounts readers: local notifications in phase 1, so no push token and no privacy change. The weather reader recommends remote push (APNs, the Apple Push Notification service) for time-sensitive alerts. Pick one. Local-only alerts will be late or missed, because reminders re-plan only on a cold launch or sign-in, a care log, an added plant or a Settings change (`App.tsx:211-213`; `CareTodos.tsx:78`; `AddPlantScreen.tsx:125`; `SettingsScreen.tsx:147, 166`), never on return to the foreground and never when the forecast changes.*
4. **Order of the unmerged catalog branch.** *Default: park `candidate-categorization-proposal`, renumber its 0023 after the overhaul's first migration, and land `weed_listing` on its own. Merge `care-notes-1.1.4` after checking the 26 care-note sentences that rest on Missouri Botanical Garden pages (`handoff:31-34`).*
5. **Zone shape.** *Default: extend `growingarea` as the Zone (new nullable columns) under a new `property` table, rather than adding a parallel zone table.*
6. **Location precision for public data.** *Default: send the exact point (later the outline) from the server to named U.S. government services only, with no account data. Keep weather at 2 decimals. Do not store the typed address.*
7. **Geodata cache key.** *Default: store geodata per property, delete it with the account, and refresh it every few months. Inside that store, key each lookup by the point rounded to about 1 m, so redrawing a zone reuses earlier answers.*
8. **Photo identification.** Readers split between hiding it (keep the on-device module as optional enrichment) and deleting it. *This audit recommends deleting it, with the server route and the eval harness, and rewriting the camera and photo strings in the same release.*
9. **The Gnome.** Keep, rename or retire the persona? *Default: leave it on plant advice in 1.x and keep it off new site and seasonal surfaces. Decide before phase 2 copy.*
10. **Indoor spaces and houseplants.** *Default: existing indoor areas keep working and serve as the "bring inside" destination; build nothing new for indoors; keep cited houseplant species (the listing promises "more than 990 species").*
11. **Native status and hardiness research.** *Default: native status by state from USDA PLANTS, with a widened authority scope under a new ADR. Hardiness as a cited zone range per species, compared zone to zone and never turned into a temperature, run first as a 50-species pilot.*
12. **Low-confidence estimates in fit.** *Default: a low-confidence value counts as Unknown until the owner confirms it; an owner tap always wins.*
13. **Sign-in before the site profile.** *Default: keep sign-in first in phase 1 (every route, including the catalog, requires it; `garden-gnome/app/routers/species.py:26-30`), but reword the reason around the property.*
14. **Tiering.** Which pieces go in the paid tier under the free-then-paid rule? Candidates: the always-on machine, server-side geodata caching, daily weather jobs, WeatherKit beyond the allowance, any commercial weather licence. *Default: keep "free" for phase 1 and design the free tier to compute on request and cache only derived values.*
15. **Map provider for zone sketching.** *Default: Apple Maps satellite imagery (no third-party key); confirm before sizing, since it needs a native rebuild.*
16. **When to remove `/environments`.** *Default: confirm build 15 shows as expired (due about 2026-10-31), then remove `/environments`, the `environment_id` aliases and `/ui` in one pull request, the first overhaul backend change.*

---

## 9. How this audit was made

- **Code readers (7).** Each read one subsystem and wrote a structured report of components, facts with evidence, a vision mapping, verdicts, constraints and open questions. The subsystems were: UI shell, data and backend, weather and reminders, voice and photo, catalog and advisor, areas/fit/location, and accounts/privacy/go-to-market.
- **Data researchers (5).** They covered maps and zones, native-plant data, soil/land-cover/hardiness, terrain and sun, and weather and phenology. Their licence findings feed section 6.6.
- **Prototype.** A live public-data spike queried the federal services at two test points (U.S. National Arboretum, Washington DC; Zilker Park, Austin TX) and measured reachability, latency and cached size. Code: `/private/tmp/claude-501/-Users-allisonbowman--claude-spares-spare-XM0k7R/3e5c7cc7-c986-4f99-8da6-1f158ad938a5/scratchpad/site-profile-spike/site_profile.py`. The spike and research files live in session scratch space and are not in the repository; copy them into `docs/` if they need to outlive this session.
- **Fact-checkers (7).** One per reader report. Each re-checked claims against the repo at `2ae894e` and recorded corrections, verdict disputes and missed items. Their corrections override the readers throughout this document.
- **Disputed verdicts.** Rows where readers disagreed or the fact-check changed a reader's verdict: photo identification in Add Plant (readers split defer/delete; delete adopted); server `/species/identify-photo` (data-backend reader defer, catalog and voice readers delete; delete adopted); server name matcher (one reader defer, the catalog reader refactor; the fact-check's delete adopted); exposure gates (keep to refactor); live camera backdrop (refactor to delete); candidate rule and `never_a_candidate` (keep to refactor); community-garden page (delete to defer); `care-advice-honesty` branch (delete to defer); `candidate-categorization-proposal` branch (catalog reader merge; fact-check, areas and accounts readers park; park adopted). The authority registry's effort was lowered to S by the fact-check. No reader gave a verdict on the weather service as a whole; refactor is this audit's.
- **This document.** Load-bearing facts were re-checked directly in the repo before writing: weather chain and comments, model defaults, `species_id`, the CI trigger, `fly.toml`, the migration count, branch state, and the absence of landscaper code.

| Subsystem | Facts checked | Confirmed | Not confirmed |
|---|---|---|---|
| UI shell | 52 | 45 | 7 |
| Data and backend | 44 | 39 | 5 |
| Weather and reminders | 54 | 49 | 5 |
| Voice and photo | 48 | 44 | 4 |
| Catalog and advisor | 54 | 45 | 9 |
| Areas, fit and location | 64 | 55 | 9 |
| Accounts, privacy and go-to-market | 48 | 42 | 6 |
| **Total** | **364** | **319 (88%)** | **45 (12%)** |

Most unconfirmed items were interpretive, not numeric. "No score" in fit and "What belongs here? absent" were wrong. So were readers marking WeatherKit "exists" in the vision mapping (the client exists, but Apple refuses it) and "hardiness conflicts with ADR 0006", and two readers misstated the branch inventory. The test baseline was run fresh on 2026-11-13 without installing anything or changing the tree.
