import {
  DATA_FLOWS, SETTINGS_FLOW_ORDER, orderedFlows, leavingDevice,
  DESTINATION_LABELS, PHOTO_DIAGNOSIS_NOTICE, CENSUS_CONSENT,
} from './copy';

// Read sibling modules to check the copy against them. Declared locally rather
// than pulling in @types/node: this is a React Native app, and node's globals
// conflict with RN's own timer typings across the whole project.
declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');

const readSrc = (rel: string): string =>
  fs.readFileSync(path.join(__dirname, rel), 'utf8');

// --- the copy is complete ----------------------------------------------------

test('every flow says what it is, in one line and in full', () => {
  for (const f of DATA_FLOWS) {
    expect(f.title.length).toBeGreaterThan(0);
    expect(f.summary.length).toBeGreaterThan(0);
    expect(f.detail.length).toBeGreaterThan(40);
    expect(DESTINATION_LABELS[f.destination]).toBeTruthy();
  }
});

test('the Settings list shows every flow — a new one cannot be quietly omitted', () => {
  const ids = DATA_FLOWS.map((f) => f.id).sort();
  expect([...SETTINGS_FLOW_ORDER].sort()).toEqual(ids);
  expect(orderedFlows()).toHaveLength(DATA_FLOWS.length);
});

// --- the copy matches what the code does ------------------------------------
// These are the claims a reviewer would check. Each is pinned to the module
// that implements it, so a change to the data flow breaks the test rather than
// quietly turning a true sentence into a false one.

test('identification is on-device, and nothing in the app uploads for it', () => {
  const identify = DATA_FLOWS.find((f) => f.id === 'identify')!;
  expect(identify.destination).toBe('device');

  // The claim above is only true while the app has no server-side identify
  // call. If someone adds one, this fails and the copy must change with it.
  const speciesApi = readSrc('../api/species.ts');
  expect(speciesApi).not.toMatch(/identify/i);
});

test('photo diagnosis is declared as leaving the device, because it does', () => {
  const diagnose = DATA_FLOWS.find((f) => f.id === 'diagnose')!;
  expect(diagnose.destination).not.toBe('device');

  // Pinned to the upload it describes (src/api/plants.ts POSTs the image).
  const plantsApi = readSrc('../api/plants.ts');
  expect(plantsApi).toMatch(/diagnose-photo/);
});

test('the census is opt-in, and is the only flow that is', () => {
  const optIns = DATA_FLOWS.filter((f) => f.optIn).map((f) => f.id);
  expect(optIns).toEqual(['census']);
});

test('nothing claims to stay on the phone while describing a transfer', () => {
  for (const f of DATA_FLOWS.filter((x) => x.destination === 'device')) {
    expect(`${f.summary} ${f.detail}`).not.toMatch(/\buploaded to\b|\bwe receive\b/i);
  }
});

test('leavingDevice is what a privacy-minded reader is looking for', () => {
  const ids = leavingDevice().map((f) => f.id);
  expect(ids).not.toContain('identify');
  expect(ids).toContain('diagnose');
  expect(ids).toContain('census');
});

// --- point-of-use consent ----------------------------------------------------

test('the photo notice names the upload plainly and offers a way out', () => {
  expect(PHOTO_DIAGNOSIS_NOTICE.title).toMatch(/photo/i);
  expect(PHOTO_DIAGNOSIS_NOTICE.body).toMatch(/upload|sent/i);
  // A consent prompt with no refusal is not consent.
  expect(PHOTO_DIAGNOSIS_NOTICE.cancelLabel.length).toBeGreaterThan(0);
});

test('the census toggle explains both directions', () => {
  expect(CENSUS_CONSENT.on.length).toBeGreaterThan(40);
  expect(CENSUS_CONSENT.off).toMatch(/stops it immediately/i);
});
