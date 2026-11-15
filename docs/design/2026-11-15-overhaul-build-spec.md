# Overhaul build spec — version 1.2.0, build 1

Date: 2026-11-15. Branch: `land-stewardship-overhaul`.

This spec turns `PLAN.md` into one build. **Where this spec and `PLAN.md`
disagree, this spec wins**, because it carries the owner's answers of
2026-11-14 (recorded in `PLAN.md` section 13, "Owner answers"). Everything
`PLAN.md` says that is not changed here still holds: read its sections 2, 5,
6 and 7 before writing code in those areas.

## 1. What the owner changed

| # | Owner's answer | What it changes |
|---|---|---|
| A1 | Release now, as one release. No mid-March / late-April split. | One version, **1.2.0**, holds all of Phase 1: address, pin, site profile, corrections, zones, seasonal plan, alerts. The plan must also show what is coming later in the year, so an owner can plan from it. D28 and decision 27 are withdrawn. |
| A2 | Sun is to be estimated from the shape of the land, overhanging features and sun angle. | D14 is replaced. The server computes a **sun estimate** (full sun, part shade or shade, with hours) from terrain, tree canopy and, where a source exists, buildings, using sun-position maths. It is shown with its confidence and what was and was not counted. The owner corrects it with one tap. See section 5. |
| A3 | Fall timing from day length, freeze normals and observed freezes; spring from the Spring Index. | Unchanged (D12, D13). |
| A4 | National Weather Service first; WeatherKit as a second opinion. | Unchanged (D11). |
| A5 | No owner override on land cover or the official hardiness zone. | Unchanged. |
| A6 | Drainage must come from data, not from asking the owner. | D15 is replaced. "Where water collects" is computed in this build from the soil survey (drainage class, ponding, flooding, depth to water table, how fast water moves through the slowest layer) and from the elevation survey (low spots and flow paths). No standing-water question is asked as the way to get the value. The owner can still correct the result, like any inferred value. See section 5. |
| A7 | Corrections on a top-down map: stretch a box over each bed, then describe it with tap choices. No photos. | Zones are **boxes drawn on a top-down aerial image**, then described by taps (what grows there, leaf habit, sun, soil). Free polygon drawing is not built. |
| A8 | On-device alerts now; server push later. | Unchanged (D21). |
| A9 | No tabs. Home is a seasonal weather-and-maintenance report: the vitals of the yard or growing spaces, not a workbook. | D22 is replaced. The app has **no tab bar**. It opens on **Home**, a single scrolling vitals report. Everything else is reached from Home. It must read well for someone with no yard (an apartment with pots). See section 6. |
| A10 | Prune photo identification. | The entry point in Add Plant is hidden. Native code stays for now. |
| A11 | Grid-snapped block only to federal services. | Unchanged (D7). |
| A12 | Shelve `candidate-categorization-proposal`. | The overhaul's first migration is **0023**. |
| A13 | `/environments` stays until 30 days of quiet logs after release. | Unchanged. |
| A15 | Version 1.1.3 will not be submitted. | The hold "no migration before Apple approves 1.1.3" (D4) no longer applies. 1.2.0 is the first version Apple reviews. Production still only changes with the owner's explicit go-ahead. |

## 2. Rules that still bind every change

- **Additive database changes only** (D3). No existing column, row or enum
  member changes. Every migration has a tested downgrade. One Alembic head.
- **The shipped client keeps working.** `/growing-areas`, `/environments`,
  `/plants` and the auth routes answer exactly as before for a 1.1.x client.
  `garden-gnome/tests/test_legacy_client_fields.py` must stay green.
- **Dark launch** (D5). `SITE_PROFILE_ENABLED` and `SEASON_PLAN_ENABLED`
  default to false. When a flag is off its routes answer 404 and no outbound
  geodata request is made. Tests and local development turn them on.
- **Privacy** (D7, D8). The stored location is the owner-confirmed pin. Soil,
  elevation, land cover, canopy and imagery services only ever receive the
  grid-snapped block. All such requests go through one outbound client
  (`app/services/site/http.py`) whose guard rejects any coordinate finer than
  the snap grid; a test proves it. The phone never calls those services.
- **Never Open-Meteo for United States coordinates** on the new routes.
  Nothing from Apple WeatherKit is stored beyond the short forecast cache.
- **Reason and source on everything** (D25). Every site value and every
  seasonal event and task uses the `Explained` shape in section 4. A test
  walks every response and fails on an empty reason or source.
- **Plain words.** Every acronym in owner-facing text is spelled out on first
  use in that screen. The hardiness value is always "hardiness zone". Write
  "United States" in full. No em dashes in owner-facing text.
- **Live network calls while building** go only to public landmarks, never a
  home address. Use the United States National Arboretum (38.9123, -76.9681)
  and Zilker Park, Austin (30.2669, -97.7729). At most 2 to 4 requests at a
  time per service, with a generic descriptive User-Agent that holds no
  personal detail. **Automated tests never touch the network**: record small
  fixtures from those two points.
- **Dependencies.** Backend: `numpy` (pinned) is allowed. One more small
  pure-Python reader is allowed only if a source cannot be read without it;
  say so in your report. Mobile: **no new native modules** (nothing that
  changes the `ios/` project). JavaScript-only packages already in
  `package.json` are fine.
- Do not commit, push, deploy, or touch `master`. Do not edit `PLAN.md` or
  `AUDIT.md`. Stay inside the files your work package owns; if you must touch
  another package's file, make the smallest change and report it.

## 3. Backend layout and ownership

All paths are under `garden-gnome/`.

| Package | Owns | Summary |
|---|---|---|
| **B1 foundation** | `app/models/models.py`, `app/models/schemas.py`, `app/config.py`, `app/main.py`, `alembic/versions/0023…`, `app/routers/properties.py`, `app/services/site/{__init__,types,grid,tiles,http}.py`, `app/services/site/profile.py` and `app/services/season/plan.py` and `app/services/vitals.py` as **stubs with the final signatures**, account-deletion changes, guardrail tests | Tables from `PLAN.md` section 5 (all of them, numbered from 0023, one concern per migration), flags, every route in section 4 wired to service entry points, the snap grid, the tile cache, the guarded outbound client. |
| **B2a sources** | `app/services/site/sources/{soil,hardiness,landcover,imagery}.py`, their data files and tests | Soil survey (including every drainage, ponding, flooding and water-table field), hardiness grid, land cover and tree cover, top-down aerial image for the snapped block. |
| **B2b terrain and sun** | `app/services/site/sources/{elevation,canopy}.py`, `app/services/site/{terrain,sun,drainage}.py` and tests | Elevation window, slope, facing, low spots and flow paths, canopy and building heights where a source exists, sun-position maths, the sun estimate, the "where water collects" computation. |
| **B2c profile** | `app/services/site/{profile,confidence,copy,overrides}.py` and tests | Turns readings into the owner-facing site profile: confidence caps, plain-word sentences, overrides, the fast step and the background step, per-zone values. |
| **B3 season** | `app/services/season/*`, `app/services/vitals.py`, data files and tests | Forecast (National Weather Service) with the cache, frost normals, observed freezes, day length, events, tasks with citations, alerts, the plan, the Home vitals report. |

Shared types (B1 writes them; nobody else changes their fields without
reporting it):

```python
# app/services/site/types.py
@dataclass(frozen=True)
class Reading:
    field: str            # one of READING_FIELDS below
    value: Any            # JSON-serialisable
    level: str            # "high" | "medium" | "low" | "unknown"
    provenance: str       # "public_map" | "modelled" | "default"
    source_key: str       # e.g. "ssurgo", "3dep", "nlcd", "phzm2023", "naip", "canopy"
    source_version: str
    method: str
    reason_codes: tuple[str, ...] = ()
    detail: dict | None = None   # extra numbers the copy needs (shares, resolution, months)

@dataclass(frozen=True)
class Block:              # the grid-snapped area sent to outside services
    key: str              # text, never floating point
    west: float; south: float; east: float; north: float
```

`READING_FIELDS`: `hardiness_zone`, `soil_mapunit`, `soil_drainage_class`,
`soil_slowest_layer`, `soil_runoff_group`, `soil_texture`, `soil_water_holding`,
`soil_ph`, `soil_disturbed_share`, `soil_flooding`, `soil_ponding`,
`soil_water_table`, `land_cover`, `tree_cover`, `elevation_window`, `slope`,
`facing`, `low_spot`, `canopy_shade`, `open_sky_sun`, `sun_estimate`,
`water_collects`.

Every source module exposes
`read(block: Block, pin: tuple[float, float], footprint: dict | None, *, client) -> list[Reading]`.
It fetches by block (through the tile cache), then samples at the pin or
over the footprint **on our server**. It raises `SourceUnavailable` when the
service fails; it returns a reading with level `unknown` when the service
answers but has no data there. B2c calls sources only through this
signature, so B2a, B2b and B2c can work at the same time.

Service entry points (B1 stubs them, B2c and B3 fill them in):

```python
# app/services/site/profile.py
def build_fast(session, prop) -> None            # hardiness, soil; called inline on create
def build_background(property_id: int) -> None   # terrain, canopy, land cover, imagery; opens its own session
def site_profile(session, prop) -> SiteProfileOut
# app/services/season/plan.py
def seasonal_plan(session, prop, *, today=None) -> SeasonalPlanOut
# app/services/vitals.py
def vitals(session, user, prop | None, *, today=None) -> VitalsOut
# app/services/season/normals.py
def frost_normals(lat, lng) -> dict              # also used by the site profile's frost-dates row
```

## 4. API contract

All routes need a signed-in user and are scoped to that user's rows. Flag off
means 404. Dates are ISO `YYYY-MM-DD`; instants are ISO 8601 in UTC.

```
GET    /properties                         -> [Property]
POST   /properties                         -> 201 Property
       body {name?, pin_lat, pin_lng, pin_source: "owner_pin"|"device_location", lot_contents?: [str]}
       Creates the whole-lot zone, runs the fast step inline, queues the background step.
GET    /properties/{id}                    -> Property
PATCH  /properties/{id}                    -> Property     body {name?, pin_lat?, pin_lng?, lot_contents?, frost_bias?: "earlier"|"later"|null}
DELETE /properties/{id}                    -> 204          zones holding plants become plain growing areas; empty zones are removed

GET    /properties/{id}/site-profile       -> SiteProfile
POST   /properties/{id}/site-profile/refresh -> 202 {status}
PUT    /properties/{id}/overrides          -> SiteProfile  body {zone_id?: int, field, value, method: "tap"|"measured"}
DELETE /properties/{id}/overrides/{field}  -> SiteProfile  query zone_id?

GET    /properties/{id}/zones              -> [Zone]
POST   /properties/{id}/zones              -> 201 Zone     body {name?, vegetation_type, box, leaf_habit?}
PATCH  /properties/{id}/zones/{zone_id}    -> Zone         body {name?, vegetation_type?, box?, leaf_habit?}
DELETE /properties/{id}/zones/{zone_id}    -> 204          the whole-lot zone cannot be deleted; a zone with plants answers 409

GET    /imagery/block?lat=&lng=            -> Imagery      for the pin step, before a property exists
GET    /properties/{id}/imagery            -> Imagery
GET    /imagery/tiles/{tile_key}.jpg       -> image/jpeg   the bytes for an Imagery.image_path

GET    /properties/{id}/seasonal-plan      -> SeasonalPlan
PUT    /properties/{id}/seasonal-plan/events/{event_key} -> SeasonEvent
       body {state: "done"|"not_needed"|"happened"|"not_yet"|"clear", observed_on?: date}

GET    /vitals?property_id=                -> Vitals       property_id optional
```

Shapes (JSON; `?` means the key may be null):

```
Property   {id, uuid, name, pin_lat, pin_lng, pin_source, city?, region?, country?, timezone?,
            lot_contents: [str], frost_bias?, whole_lot_zone_id, profile_status: {fast, background}, created_at}
           lot_contents values: "trees_that_drop_leaves","evergreens","shrubs","lawn","garden_beds",
                                "potted_plants","vegetables","mostly_paved"
           profile_status values: "pending"|"building"|"ready"|"partial"|"failed"

Box        {west, south, east, north}            degrees; the server stores it as a GeoJSON polygon

Zone       {id, growing_area_id (same number), property_id, name, vegetation_type, is_whole_lot,
            box?, boundary_source: "default"|"owner", leaf_habit?, plant_count, values: [SiteValue]}
           vegetation_type: "tree"|"shrub"|"grass"|"garden_bed"|"bare_hardscape"
           leaf_habit: "drops_leaves"|"evergreen"|"mixed"

Source     {name, detail?, version?, url?}

Explained  {display, confidence, confidence_label, reason, sources: [Source], provenance}
           confidence: "you_told_us"|"you_measured"|"good_estimate"|"area_estimate"|"rough_estimate"|
                       "not_known_yet"|"neighbourhood_context"
           confidence_label: "You told us"|"You measured"|"Good estimate"|"Area estimate"|"Rough estimate"|
                             "Not known yet"|"Neighbourhood context"
           provenance: "owner"|"public_map"|"modelled"|"default"

SiteValue  Explained + {field, title, value?, zone_id?, can_override, override_choices: [{value, label}],
                        override_kind: "choice"|"number"|"none", public?: {display, confidence_label}}
           field: "sun"|"soil_drainage"|"water_collects"|"soil_texture"|"soil_ph"|"disturbed_soil"|"slope"|
                  "facing"|"flooding"|"land_cover"|"hardiness_zone"|"frost_dates"
           `public` is the public-data reading, present only when an owner correction is showing.

SiteProfile {property_id, status: {fast, background}, updated_at?, values: [SiteValue],
             zones: [{zone_id, name, is_whole_lot, values: [SiteValue]}], notes: [str]}

Imagery    {tile_key, image_path, width, height, bounds: Box, source: Source, captured?: str,
            pin?: {lat, lng}, default_footprint?: Box}

Forecast   {provider, provider_name, fetched_at, days: [{date, high_f?, low_f?, precipitation_chance?,
            summary, frost_risk: "none"|"frost"|"freeze"|"hard_freeze"}]}

SeasonTask {task_key, text, low_impact_note?, reason, sources: [Source],
            applies_to: {kind: "lot"|"zones"|"plants", ids: [int]}, state: "open"|"done"|"not_needed"}

SeasonEvent {event_key, type, title, status, window: {start?, end?, text}, explained: Explained,
             tasks: [SeasonTask], owner_actions: [str], sort_date?}
            type: "first_frost"|"first_freeze"|"hard_freeze"|"fall_hardening"|"leaf_drop"|"dormancy"|
                  "last_frost"|"spring_emergence"|"tender_plants_out"|"spring_cleanup"
            status: "happened"|"happening"|"forecast"|"expected"|"typically_around"|"done"|"not_needed"
            owner_actions: any of "mark_happened","mark_not_yet","mark_done","mark_not_needed","clear"

SeasonAlert {alert_key, event_key, title, body, fire_at, built_from_forecast_at}

SeasonalPlan {property_id, generated_at, season_label, forecast?: Forecast, events: [SeasonEvent],
              alerts: [SeasonAlert], notes: [str]}

VitalCard  {key, title, value_text, detail, tone: "ok"|"watch"|"act", explained?: Explained, link?: str}
           key: "weather_now"|"frost"|"rain"|"heat"|"sun"|"soil"|"drainage"|"season"
           link: a screen name from section 6

Vitals     {generated_at, headline, property?: Property, forecast?: Forecast, cards: [VitalCard],
            this_week: [{event_key?, task: SeasonTask}], season_ahead: [SeasonEvent (without tasks)],
            spaces: [{growing_area_id, name, kind: "zone"|"space", vegetation_type?, indoor: bool, plant_count}],
            notes: [str]}
```

With no property, `/vitals` still answers: weather for the first growing
area that has coordinates (through the existing weather service), the
person's spaces, and a `notes` line inviting them to add land if they have
any. It never tells an apartment dweller they are missing something.

## 5. Sun and drainage (the two changed science rows)

**Sun estimate.** For the whole lot and for each owner-drawn zone:

1. Sun position through the growing season (frost-free period from the frost
   normals, else April to October) at the pin's latitude, sampled at least
   hourly.
2. Horizon blocking from terrain (the elevation window).
3. Blocking from overhanging features: tree canopy and buildings from the
   best source B2b can prove at both test points. Candidates, in order: a
   canopy height model at about 1 metre (for example the Meta and World
   Resources Institute global canopy height tiles); a first-return surface
   model from the laser survey; building footprints with heights; and, as the
   coarse fallback, the tree cover percentage from land cover. Record in the
   design note which sources worked, their licence and attribution, and what
   each costs in time and bytes.
4. Result: average direct-sun hours a day and a category, full sun (6 or more
   hours), part shade (3 to 6), shade (under 3).

Confidence: never above "Area estimate" from public data. "Rough estimate"
when only the coarse fallback was available, when the zone is the default
footprint, or when buildings could not be counted. "Not known yet" only when
neither terrain nor any canopy source answered. The reason sentence says what
was counted and what was not, for example "Counts the slope of the ground
and tree cover mapped at 1 metre detail. Buildings are not counted." The
owner's one-tap correction (full sun, part shade, shade) reads "You told us",
and the estimate stays visible beside it. Deciduous canopy: say plainly that
the estimate is for the growing season, when leaves are out.

**Where water collects and drainage.** Built from data, in this build:

1. From the soil survey: natural drainage class, how fast water moves
   through the slowest layer, runoff group, ponding frequency and duration by
   month, flooding by month, depth to the seasonal water table.
2. From the elevation window: filled-depression depth (low spots) and flow
   accumulation (where runoff from uphill gathers), computed at the best
   resolution the survey offers there. Leave out a 10 metre radius around the
   pin (the house).
3. Combine into one `water_collects` value per zone: "drains freely", "slow
   to drain", "water gathers here after rain", or "often wet", with the
   reason naming which signals agreed.

Confidence follows the data: "Good estimate" only on a 1 metre survey with an
owner-drawn zone and agreeing soil signals; "Area estimate" on 1 to 3 metre
elevation or soil alone with 75% or more of the mapped area agreeing; "Rough
estimate" on 10 metre elevation, the default footprint, or disturbed soil.
Never claim a flood insurance determination. The owner correction is a
choice ("Water stands here after rain" / "This stays dry"), not a required
question.

## 6. The app

No tab bar. One native stack. Screen names are fixed here so packages can
link to each other:

| Screen name | File | Package | What it is |
|---|---|---|---|
| `Home` | `src/screens/HomeScreen.tsx` | M1 | The vitals report. Opens the app. |
| `PropertySetup` | `src/screens/PropertySetupScreen.tsx` | M2 | Address, confirm the pin on the top-down image, "What's on your lot?" (skippable), then Home. |
| `Land` | `src/screens/LandScreen.tsx` | M2 | The site profile: each value with its confidence, reason, source and correction. |
| `ZoneMap` | `src/screens/ZoneMapScreen.tsx` | M3 | Top-down image; stretch a box over a bed; describe it by taps. |
| `Season` | `src/screens/SeasonScreen.tsx` | M3 | The full seasonal plan: events, windows, tasks, "why and data source". |
| `Spaces`, `SpaceDetail` | existing `GrowingAreasScreen`, `GrowingAreaDetailScreen` | M1 registers | Growing spaces, including indoor ones. |
| `Plants`, `PlantDetail`, `AddPlant`, `CaptureGarden`, `Species`, `SpeciesDetail`, `Settings`, `Census` | existing | M1 registers | Unchanged in behaviour, reached from Home. Existing route names inside those screens keep working. |

**Home, top to bottom:** a headline in plain words about today and the
season; weather vitals (today, the next frost or freeze risk, rain); "This
week" (seasonal tasks from the plan merged with per-plant care that is due);
"The season ahead" (the next few events with their windows); "Your land"
(sun, soil, drainage and hardiness one-liners with confidence, linking to
`Land`); "Your growing spaces" (zones and spaces with plant counts); and
quiet links to Plants, Species, Settings. With no property it shows weather,
plant care due and spaces, with one calm card offering "Add your land". When
the server answers 404 for the new routes (flags off), Home works in that
no-property form and the card is hidden.

**M1 also owns:** `App.tsx`, navigation types, `src/api/properties.ts` and
`src/types/site.ts` (the whole section 4 contract, typed), shared pieces
`src/components/ExplainedBlock.tsx` and `ConfidenceChip.tsx`, hiding the
photo-identification entry in Add Plant, moving Census under Settings, and
the version change to 1.2.0 in `app.json` and wherever the version is
checked. **M3 also owns** scheduling the plan's alerts through the one
existing planner (`src/notifications/plan.ts`, `reminders.ts`); nothing else
may schedule notifications.

The top-down image comes from our server (`Imagery`), is drawn with a plain
`Image`, and is panned, zoomed and drawn on with JavaScript gesture handling.
Converting between image pixels and latitude and longitude uses
`Imagery.bounds`. Every interactive element has an accessibility label, and
the box tool has a non-drawing path ("Add a zone without drawing") for
people who cannot use the gesture.

## 7. Done means

Backend: `cd garden-gnome && .venv/bin/python -m pytest -q` is green, with
new tests for every rule in section 2. Mobile: `cd mobile && npm test` and
`npm run typecheck` are green. Then, on the simulator against a local
server: enter an address, confirm the pin, see a site profile with sun and
drainage estimated from data, correct sun and soil by taps, stretch a box
over a bed and describe it, and read a seasonal plan with frost, dormancy
and leaf-drop events, each with its reason and source.
