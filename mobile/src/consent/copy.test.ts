import {
  DATA_FLOWS, SETTINGS_FLOW_ORDER, orderedFlows, visibleFlows, leavingDevice,
  DESTINATION_LABELS, PHOTO_DIAGNOSIS_NOTICE, CENSUS_CONSENT, CENSUS_FIELDS,
} from './copy';
import { AiCapabilities, NO_CAPABILITIES } from '../care/aiCapabilities';

// Read sibling modules to check the copy against them. Declared locally rather
// than pulling in @types/node: this is a React Native app, and node's globals
// conflict with RN's own timer typings across the whole project.
declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');

const readSrc = (rel: string): string =>
  fs.readFileSync(path.join(__dirname, rel), 'utf8');

const flow = (id: string) => DATA_FLOWS.find((f) => f.id === id)!;
const text = (id: string) => `${flow(id).summary} ${flow(id).detail}`;

// --- the copy is complete ----------------------------------------------------

test('every flow says what it is, in one line and in full', () => {
  for (const f of DATA_FLOWS) {
    expect(f.title.length).toBeGreaterThan(0);
    expect(f.summary.length).toBeGreaterThan(0);
    expect(f.detail.length).toBeGreaterThan(40);
    expect(DESTINATION_LABELS[f.destination]).toBeTruthy();
  }
});

test('the Settings order names every flow — a new one cannot be quietly omitted', () => {
  const ids = DATA_FLOWS.map((f) => f.id).sort();
  expect([...SETTINGS_FLOW_ORDER].sort()).toEqual(ids);
  expect(orderedFlows()).toHaveLength(DATA_FLOWS.length);
});

// --- shown only while true ---------------------------------------------------
// A disclosure for a feature the caretaker cannot find sends them, and App
// Review, looking for it. So each flow is either always true, or tied to the
// capability that gates the feature itself — and the screen that offers the
// feature gates on that same capability.

const ALL_ON: AiCapabilities = { photoDiagnosis: true, symptoms: true };

test('every flow is either always shown or tied to a real capability', () => {
  const capabilities = Object.keys(NO_CAPABILITIES);
  for (const f of DATA_FLOWS) {
    if (f.requires) expect(capabilities).toContain(f.requires);
  }
  const always = DATA_FLOWS.filter((f) => !f.requires).map((f) => f.id).sort();
  expect(visibleFlows(NO_CAPABILITIES).map((f) => f.id).sort()).toEqual(always);
  expect(visibleFlows(ALL_ON)).toHaveLength(DATA_FLOWS.length);
});

test('photo check-ups and free-text questions are listed only while offered', () => {
  expect(flow('diagnose').requires).toBe('photoDiagnosis');
  expect(flow('advice').requires).toBe('symptoms');
  const productionToday = visibleFlows(NO_CAPABILITIES).map((f) => f.id);
  expect(productionToday).not.toContain('diagnose');
  expect(productionToday).not.toContain('advice');
  expect(visibleFlows({ photoDiagnosis: true, symptoms: false }).map((f) => f.id))
    .toEqual(expect.arrayContaining(['diagnose']));
});

test('the plant screen gates each feature on the capability its flow names', () => {
  const plantScreen = readSrc('../screens/PlantDetailScreen.tsx');
  for (const f of DATA_FLOWS.filter((x) => x.requires)) {
    expect(plantScreen).toContain(`capabilities.${f.requires}`);
  }
});

test('Settings lists the visible flows, not every flow', () => {
  const settings = readSrc('../screens/SettingsScreen.tsx');
  expect(settings).toMatch(/visibleFlows\(/);
  expect(settings).not.toMatch(/orderedFlows\(/);
});

// --- the copy matches what the code does ------------------------------------
// These are the claims a reviewer would check. Each is pinned to the module
// that implements it, so a change to the data flow breaks the test rather than
// quietly turning a true sentence into a false one.

test('identification is on-device, and nothing in the app uploads for it', () => {
  expect(flow('identify').destination).toBe('device');

  // The claim above is only true while the app has no server-side identify
  // call. If someone adds one, this fails and the copy must change with it.
  const speciesApi = readSrc('../api/species.ts');
  expect(speciesApi).not.toMatch(/identify/i);
});

test('photo diagnosis is declared as leaving the device, because it does', () => {
  expect(flow('diagnose').destination).not.toBe('device');

  // Pinned to the upload it describes (src/api/plants.ts POSTs the image).
  const plantsApi = readSrc('../api/plants.ts');
  expect(plantsApi).toMatch(/diagnose-photo/);
});

test('the location flow names every weather service the server asks', () => {
  const weather = readSrc('../../../garden-gnome/app/services/weather.py');
  const said = text('location');
  // Each provider the server can send coordinates to, beside the name the
  // copy gives it.
  const providers: [string, string][] = [
    ['weatherkit.apple.com', 'Apple Weather'],
    ['api.weather.gov', 'U.S. National Weather Service'],
    ['api.open-meteo.com', 'Open-Meteo'],
  ];
  for (const [host, name] of providers) {
    expect(weather).toContain(host);
    expect(said).toContain(name);
  }
  expect(flow('location').destination).toBe('partner');
});

test('weather services get the coordinates rounded, as the location flow says', () => {
  const weather = readSrc('../../../garden-gnome/app/services/weather.py');
  // Two decimal places is about a kilometer of latitude.
  expect(weather).toMatch(/^_COORD_DECIMALS = 2$/m);
  expect(text('location')).toMatch(/coordinates rounded to about a kilometer/);
});

test('the census export carries no coordinates, as the location flow says', () => {
  const census = readSrc('../../../garden-gnome/app/routers/census.py');
  // Read the function that builds the export, from its def to the next
  // top-level statement: census_export is only the route around it.
  const start = census.indexOf('def build_export(');
  expect(start).toBeGreaterThan(-1);
  const rest = census.slice(start + 1);
  const next = rest.search(/^(?:def |async def |@|class )/m);
  const builder = next === -1 ? rest : rest.slice(0, next);
  // The slice is the export body itself, not a stub left behind by a move.
  expect(builder).toMatch(/growing_area/);
  expect(builder).toMatch(/records/);
  expect(census).toMatch(/def census_export\([\s\S]*?return build_export\(/);
  // No coordinate is read, by attribute, by key or by getattr.
  const coordinate = /\.(lat|lng)\b|\[\s*['"](lat|lng)['"]\s*\]|getattr\([^)]*['"](lat|lng)['"]/;
  expect(builder).not.toMatch(coordinate);
  expect(text('census')).toMatch(/no coordinates/);
});

test('the voice flow is true of the speech module and the capture screen', () => {
  // On the phone where it can be: the module asks for on-device recognition
  // whenever the device supports it, and tells the screen which it got.
  const speech = readSrc('../../modules/plant-speech/ios/PlantSpeechModule.swift');
  expect(speech).toMatch(/requiresOnDeviceRecognition\s*=\s*onDevice/);
  expect(speech).toMatch(/supportsOnDeviceRecognition/);
  const capture = readSrc('../screens/CaptureGardenScreen.tsx');
  expect(capture).toMatch(/sends audio to Apple/);

  // Only the confirmed plants reach the server: the bulk payload is built
  // from the drafts' species, count and spot, never the transcript. The save
  // goes out in batches (capture/bulkSave.ts), each built the same way.
  const payload = capture.match(/createPlantsBulk\(\s*batch\.map\([\s\S]*?\}\)\)/);
  expect(payload).not.toBeNull();
  expect(payload![0]).not.toMatch(/\bheard\b/);
  const keys = [...payload![0].matchAll(/(\w+):/g)].map((m) => m[1]).sort();
  expect(keys).toEqual(['growing_area_id', 'location', 'quantity', 'species_id']);

  expect(text('voice')).toMatch(/never receives the audio/);
  expect(text('voice')).toMatch(/Apple/);
});

test('the census is opt-in, defaults off, and is the only flow that is opt-in', () => {
  const optIns = DATA_FLOWS.filter((f) => f.optIn).map((f) => f.id);
  expect(optIns).toEqual(['census']);
  const models = readSrc('../../../garden-gnome/app/models/models.py');
  expect(models).toMatch(/census_opt_in: bool = Field\(default=False\)/);
});

// The census is described twice: the Settings entry, and the text under the
// switch once joined. Both carry the same list of what a record holds.
const censusTexts = () => [flow('census').detail, CENSUS_CONSENT.on];

test('the census copy names every field a record carries, in both places', () => {
  // Export 4.1's record, field by field, in the words the copy uses.
  const fields: [string, RegExp][] = [
    ['species_id', /its species/],
    ['quantity', /how many there are/],
    ['maturity_stage', /growth stage/],
    ['acquired_month', /the month you got it/],
    ['initial_condition', /how it looked then \(soil, leaves, any pests\)/],
    ['care_history', /how many times each kind of care was logged in each month/],
    ['stewardship_count', /how many growing areas it has been in/],
    ['stewardship_chain', /the months it moved between them/],
    ['split_from_ref', /which planting it was split from/],
    ['growing_area', /growing area’s type, city, region and country/],
  ];
  for (const t of censusTexts()) {
    expect(t).toContain(CENSUS_FIELDS);
    for (const [, words] of fields) expect(t).toMatch(words);
  }
});

test('the census promises only what holds: no identifier links exports', () => {
  for (const t of censusTexts()) {
    expect(t).toMatch(/no identifier links one export to another/);
    expect(t).toMatch(/records are shuffled/);
    // Monthly care counts are the planting's own; the copy says they could
    // still look alike, instead of promising exports can never be matched.
    expect(t).toMatch(/monthly care counts could still look alike/);
    expect(t).not.toMatch(/can’t be joined|can't be joined|cannot be (linked|joined)|can’t be linked/i);
    expect(t).toMatch(/no exact dates/);
  }
  // Before joining, the switch points at the full list.
  expect(CENSUS_CONSENT.off).toMatch(/“The community census” below/);
});

test('nothing claims to stay on the phone while describing a transfer', () => {
  for (const f of DATA_FLOWS.filter((x) => x.destination === 'device')) {
    expect(`${f.summary} ${f.detail}`).not.toMatch(/\buploaded to\b|\bwe receive\b/i);
  }
});

test('a flow that goes beyond our server says so in its words', () => {
  for (const f of DATA_FLOWS.filter((x) => x.destination === 'partner')) {
    expect(`${f.summary} ${f.detail}`).toMatch(/outside|Apple|weather service|census/i);
  }
});

test('leavingDevice is what a privacy-minded reader is looking for', () => {
  const ids = leavingDevice().map((f) => f.id);
  expect(ids).not.toContain('identify');
  expect(ids).toContain('diagnose');
  expect(ids).toContain('voice');
  expect(ids).toContain('census');
});

// --- point-of-use consent ----------------------------------------------------

test('the photo notice names the upload plainly and offers a way out', () => {
  expect(PHOTO_DIAGNOSIS_NOTICE.title).toMatch(/photo/i);
  expect(PHOTO_DIAGNOSIS_NOTICE.body).toMatch(/upload|sent/i);
  expect(PHOTO_DIAGNOSIS_NOTICE.body).toMatch(/outside AI service/);
  // A consent prompt with no refusal is not consent.
  expect(PHOTO_DIAGNOSIS_NOTICE.cancelLabel.length).toBeGreaterThan(0);
});

test('the census toggle explains both directions', () => {
  expect(CENSUS_CONSENT.on.length).toBeGreaterThan(40);
  expect(CENSUS_CONSENT.off).toMatch(/stops it immediately/i);
});
