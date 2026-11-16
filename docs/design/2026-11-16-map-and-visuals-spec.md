# Map and visuals: build spec (2026-11-16)

Owner's words: "the app need map and visuals". Home, Your land and the Season
screen are text only today; the aerial image appears only while placing the pin
or drawing a bed. The owner approved the proposal below ("Yes, build it").
This spec is binding for the build. Where it is silent, follow
`docs/design/2026-11-15-overhaul-build-spec.md` and the code's conventions.

## 1. What is added

1. **Land map** on Home and on Your land: the aerial image, the pin, and the
   owner's zones outlined and labelled. Chips switch the layer drawn on top:
   Aerial (none), Sun, Trees, Water. A legend and the layer's "Why and data
   source" sit under the map.
2. **Forecast bars** (Home, Season): one high/low bar per forecast day on a
   shared scale, a 32 °F line, frost nights marked, a weather icon per day.
3. **Season timeline** (Home, Season): event windows as bands on a month axis
   with today marked.
4. **Reading tiles** (Home, Your land): sun hours, hardiness zone, where water
   collects, topsoil, as small graphics with the confidence label.

## 2. Binding rules

- **No new outside requests.** Layers are drawn only from copies the server
  already holds in `geodata_tile` (elevation, canopy). The layer code must
  never construct an `OutboundClient` or call a loader that can fetch. A cache
  miss means "not ready", never a fetch.
- **Every visual keeps reason, data source and confidence label reachable**
  without leaving the screen (an `ExplainedBlock` under it or on tap).
- **Say what is not counted.** Buildings are not counted in sun. Soil is not
  drawn on the water layer. Canopy 0 can mean no trees or no data. Near the
  edge of the map the sun estimate reads high because land beyond the map is
  not counted.
- Plain words. No em dashes in owner-facing copy. Acronyms spelled out.
  Fahrenheit as "°F". No "AI" claims.
- All app colours come from `useAppTheme().palette` (both themes, almanac and
  observatory). Layer colours come from the server's legend, so the picture
  and its legend cannot disagree.
- Accessibility: every pressable has `accessibilityLabel`; each chart is one
  `accessible` element (or one per day/event) with a sentence label; decorative
  drawing is hidden from accessibility. Touch targets at least 44 pt. Add new
  `.tsx` files to `FILES` in `mobile/src/land/a11y.test.ts`.
- Drawing maths lives in pure `.ts` modules with jest tests. Only `.tsx`
  component files import `react-native-svg`. No test may import a module that
  imports `react-native-svg` or `react-native` unless it mocks them the way
  existing tests do.
- Behind `SITE_PROFILE_ENABLED` like every other land route. An older server
  that answers 404 for `/layers` must leave the app working with the Aerial
  layer only.
- Do not commit, push, run `scripts/sim-build.sh`, touch `site/`, or change the
  permission strings in `mobile/app.json`.
- Live calls to federal services are forbidden in this work. Tests use the
  recorded fixtures.

## 3. Server

New module `garden-gnome/app/services/site/layers.py`; routes in
`app/routers/properties.py`; schemas in `app/schemas.py`; tests in
`tests/test_site_layers.py` and route cases beside the existing property
route tests.

### 3.1 Sources (cache only)

- `cached_window(session, block) -> ElevationWindow | None` and
  `cached_canopy(session, block) -> CanopyGrid | None`: read with
  `tiles.get` / `tiles.get_json`, decode with the existing decoders. No client
  parameter exists on these functions.
- Both grids are on the 1e-5 degree lattice, shape (500, 600), north row first.
  The aerial image covers exactly the block, so a layer image stretched over
  `bounds` lines up with it.

### 3.2 Layers

| kind | grid | drawn |
|---|---|---|
| `sun` | average hours of direct sun a day in the growing season, on a coarser lattice (about 5 m stride) | a 4 or 5 step ramp from deep shade to full sun; cells under canopy of 2 m or more are the deepest shade, as in `sun.estimate` |
| `trees` | canopy height in metres | transparent below 2 m; 3 or 4 steps above |
| `water` | from `terrain.analyse_window`: `depth >= LOW_SPOT_DEPTH_M` is "water collects here"; `accumulation_m2 >= FLOW_CATCHMENT_M2` is "water runs through here"; everything else transparent | two colours |

- Sun reuses `season_sun`, `horizons` and the season from
  `season_from_normals(frost_normals(...))` at the **block centre**, so the
  layer is the same for every property in the block. Replace the
  `direct_hours` gather with a chunked or per-azimuth-bin method. Budget on the
  512 MB machine: under 80 MB of extra memory at peak and a few seconds of CPU.
  State the measured time and peak memory in the test file or module docstring.
- Water is unavailable when the window's resolution is coarser than
  `WATER_MAX_RESOLUTION_M`, as the drainage reading already is.
- Colours: chosen for contrast on an aerial photograph and distinguishable
  without relying on red versus green. Semi-transparent RGBA so the photograph
  shows through.
- `encode_png(rgba) -> bytes` with `zlib` and `struct` only (Pillow is not
  installed at runtime). Tests decode it back (Pillow is available in dev) and
  compare pixels.

### 3.3 Cache

- Encoded PNGs are stored in `geodata_tile`: provider `site_layers`, version
  `v1`, key `{block.key}_lyr_{kind}`. No migration.
- Expiry no later than the earliest expiry of the source tiles used.
- Warm all three at the end of the profile background step (after the grids are
  cached), inside its existing error handling: a failure to draw a layer must
  never fail the profile.
- A PNG request with the sources cached but the layer not yet drawn draws it
  then, stores it and returns it. With a source missing it answers 409 with a
  plain sentence. Call `session.commit()` after reads, as the tile route does.

### 3.4 Routes

`GET /properties/{id}/layers` (auth, `require_site_profile`, `_owned_property`):

```json
{
  "property_id": 1,
  "bounds": {"west": 0, "south": 0, "east": 0, "north": 0},
  "layers": [
    {
      "kind": "sun",
      "title": "Sun",
      "status": "ready",
      "status_text": null,
      "image_path": "/properties/1/layers/sun.png",
      "width": 120, "height": 100,
      "legend": [{"color": "#RRGGBB", "label": "Under 2 hours"}],
      "explained": { "display": "...", "confidence": "...", "confidence_label": "Rough estimate", "reason": "...", "sources": [], "provenance": "modelled" },
      "notes": ["Buildings are not counted."]
    }
  ]
}
```

- `status` is `ready` (drawn, or drawable now from cached sources),
  `not_ready` (a source is not cached yet; `status_text` says the map is still
  being prepared) or `unavailable` (outside the United States, or the ground
  data is too coarse; `status_text` says why). `image_path` is null unless
  ready. Always returns all three kinds in the order sun, trees, water.
- `explained` uses the existing Explained shape, confidence labels and source
  records (`copy.py`, `confidence.py`, the readings' own sources). Sun and
  water are "Rough estimate"; trees is whatever the canopy source already uses.

`GET /properties/{id}/layers/{kind}.png`: same guards, ownership checked (unlike
the jpg route), `image/png`, `Cache-Control: private, max-age=86400`, 404 for an
unknown kind, rate limited more gently than site builds (about 30 a minute).

### 3.5 Tests

- No outbound: patch `OutboundClient.__init__` to raise and exercise both
  routes and the warm step's layer part; also assert
  `site_http.requests_sent()` is unchanged.
- Alignment: a synthetic window with one tall canopy cell or one pit lands on
  the expected PNG pixel.
- Sun sanity: flat open ground reads full sun; a cell just north of a tall
  canopy block reads fewer hours than one just south of it; under canopy is the
  deepest step.
- Ownership: another user's property answers 404 for both routes. Flag off:
  404. Outside the United States: `unavailable`. Missing source: `not_ready`
  and 409.
- Expiry no later than the sources'. Housekeeping prunes layer tiles with the
  block's other tiles.
- The whole backend suite still passes.

## 4. App

`npx expo install react-native-svg` (Expo SDK 57 pins 15.15.4).

### 4.1 Types and API (`src/types/site.ts`, `src/api/properties.ts`)

```ts
export type MapLayerKind = 'sun' | 'trees' | 'water';
export type MapLayerStatus = 'ready' | 'not_ready' | 'unavailable';
export interface LegendStep { color: string; label: string; }
export interface MapLayer {
  kind: MapLayerKind; title: string; status: MapLayerStatus; status_text?: string | null;
  image_path?: string | null; width: number; height: number;
  legend: LegendStep[]; explained: Explained; notes: string[];
}
export interface MapLayers { property_id: number; bounds: Box; layers: MapLayer[]; }
```

`fetchMapLayersOrOff(propertyId): Promise<MapLayers | null>` (null on 404),
query key `SITE_QUERY_KEYS.mapLayers(id)`. The layer PNG loads through the
signed-in client like the aerial image (`useSignedImage(path)` generalised from
`useImagerySource`, which stays as a thin wrapper).

### 4.2 Pure modules (each with tests)

- `src/land/mapLayout.ts`: `zoneRects(imagery, zones)`, `yardFocus(imagery)`,
  `viewRect(rect, ctx)`, label placement (keep labels inside the view, drop a
  label that does not fit). Move the embedded versions out of `ZoneMapScreen`
  and make that screen use these.
- `src/land/mapLayers.ts`: the chip list (Aerial first, then the server's
  layers), which chips are enabled, the status sentence for a layer that is not
  ready, the accessibility sentence for the map with a layer on.
- `src/land/readingTiles.ts`: `readingTiles(profile, cards)` built on
  `landLines`, with tolerant parsers for sun `{hours, category}`, hardiness
  `{zone, low_f, high_f}`, water `{class}`, soil texture. Each tile:
  `{key, title, valueText, detail, fraction | null, confidenceLabel, explained, field, a11y}`.
  A value that cannot be parsed still yields a tile with its display text and
  no graphic.
- `src/home/forecastBars.ts`: shared °F scale, per-day bar geometry, the 32 °F
  line position (only when it falls inside the scale, otherwise a note), frost
  marks from `frost_risk`, an icon name per day from the summary and
  precipitation chance (MaterialCommunityIcons names), a11y sentences reused
  from `forecastCells`. Days with a missing high or low draw what is known.
- `src/season/timeline.ts`: a month axis that starts at the earliest shown
  window (or the month before today) and spans at most 12 months; bands from
  `window.start/end` (a single date is a mark); row packing so bands do not
  overlap; `todayX`; tone from event type and status; a11y sentence per event.
  Events without dates are left out of the picture and stay in the list.
  Use `parseServerDate`.

### 4.3 Components (`.tsx`, the only importers of `react-native-svg`)

- `src/components/LandMap.tsx`: `TopDownImage` plus an optional overlay image
  drawn exactly over the aerial image (add overlay props to `TopDownImage`),
  zone outlines and labels, the pin. Props choose read-only (Home) or pan and
  zoom (Your land).
- `src/components/LayerChips.tsx`, `src/components/MapLegend.tsx`.
- `src/components/ForecastBars.tsx`, `src/components/SeasonTimeline.tsx`,
  `src/components/ReadingTile.tsx` (and a small grid wrapper).

### 4.4 Screens

- **Home**: forecast bars at the top of the Weather section (the cards stay
  below). Timeline at the top of "The season ahead". "Your land" starts with
  the map (read-only, focused on the yard, chips, legend), then the tiles in a
  two-column grid; tapping a tile shows its `ExplainedBlock` under the grid.
  The four text rows the tiles replace are removed. With no land, none of the
  land visuals show and the "Add your land" card is unchanged. A map that
  fails to load shows a one-line message and the rest of Home still renders.
- **Your land**: the map with pan and zoom, chips, legend, the layer's notes
  and `ExplainedBlock`; then the tiles; then the existing sections unchanged.
  A link to "Draw or change your zones" stays reachable.
- **Season**: bars replace the text forecast strip (its a11y labels are kept);
  the timeline sits above the sections.
- Imagery and zones on Home and Your land use the existing query keys
  (`imagery(id)`, `zones(id)`) so the cache is shared with the zone map.

### 4.5 Checks

`npx jest` and `npx tsc --noEmit` pass. `npm run web` renders all three
screens (react-native-web draws the SVG).
