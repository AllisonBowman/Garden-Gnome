// census.ts reaches the network through ./client, which pulls in the keychain
// and React Native; the normalizer under test needs neither.
jest.mock('./client', () => ({ apiClient: jest.fn() }));

import { apiClient } from './client';
import { fetchCensusSummary, normalizeCensusSummary } from './census';

declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');
const readSrc = (rel: string): string => fs.readFileSync(path.join(__dirname, rel), 'utf8');

// --- the answers the app will actually meet ---------------------------------

test('the current server answer is read as is', () => {
  const view = normalizeCensusSummary({
    total_plants: 7,
    total_plantings: 3,
    total_growing_areas: 2,
    growing_areas_by_type: { home: 1, community_garden: 1 },
    plants_by_growing_area_type: { home: 5, community_garden: 2 },
    species_distribution: [{ species_id: 3, common_name: 'Basil', count: 4 }],
    // ...and the pre-rename copies it sends alongside for 1.1.2
    total_environments: 2,
    environments_by_type: { home: 1, community_garden: 1 },
  });
  expect(view).toEqual({
    total_plants: 7,
    total_growing_areas: 2,
    growing_areas_by_type: { home: 1, community_garden: 1 },
    species_distribution: [{ species_id: 3, common_name: 'Basil', count: 4 }],
  });
});

test("today's production answer, with only the pre-rename keys, renders", () => {
  // This exact shape threw "Cannot convert undefined or null to object" on
  // the Census tab and took the app down.
  const view = normalizeCensusSummary({
    total_plants: 4,
    total_environments: 1,
    environments_by_type: { home: 1 },
    plants_by_environment_type: { home: 4 },
    species_distribution: [],
  });
  expect(view.total_growing_areas).toBe(1);
  expect(view.growing_areas_by_type).toEqual({ home: 1 });
  expect(view.species_distribution).toEqual([]);
});

test('a brand-new account reads as empty, not missing', () => {
  const view = normalizeCensusSummary({
    total_plants: 0, total_growing_areas: 0, growing_areas_by_type: {},
    plants_by_growing_area_type: {}, species_distribution: [],
  });
  expect(view).toEqual({
    total_plants: 0, total_growing_areas: 0,
    growing_areas_by_type: {}, species_distribution: [],
  });
});

// --- answers nobody planned for ----------------------------------------------
// A missing field is null (shown as a dash or left out), never a made-up 0.

test('an empty or broken answer yields nulls, not a throw', () => {
  const nothing = {
    total_plants: null, total_growing_areas: null,
    growing_areas_by_type: null, species_distribution: null,
  };
  for (const raw of [{}, null, undefined, 'oops', 42, []]) {
    expect(normalizeCensusSummary(raw)).toEqual(nothing);
  }
});

test('the area total falls back to the sum of the breakdown when only that came', () => {
  const view = normalizeCensusSummary({ growing_areas_by_type: { home: 2, school: 1 } });
  expect(view.total_growing_areas).toBe(3);
  expect(view.total_plants).toBeNull();
});

test('malformed counts and rows are dropped, the rest kept', () => {
  const view = normalizeCensusSummary({
    total_plants: '7',
    growing_areas_by_type: { home: 2, school: 'three', allotment: null, balcony: -1 },
    species_distribution: [
      { species_id: 3, common_name: 'Basil', count: 4 },
      { species_id: 4, common_name: null, count: 2 },
      { common_name: 'Mint', count: 1 },
      null,
      'Fern',
      { species_id: 5, common_name: 'Thyme', count: 1 },
    ],
  });
  expect(view.total_plants).toBeNull();
  expect(view.growing_areas_by_type).toEqual({ home: 2 });
  expect(view.species_distribution).toEqual([
    { species_id: 3, common_name: 'Basil', count: 4 },
    { species_id: 5, common_name: 'Thyme', count: 1 },
  ]);
});

test('fetchCensusSummary hands the screen the shaped view', async () => {
  (apiClient as jest.Mock).mockResolvedValue({
    get: jest.fn().mockResolvedValue({ data: { total_environments: 1, environments_by_type: { home: 1 } } }),
  });
  await expect(fetchCensusSummary()).resolves.toMatchObject({
    total_growing_areas: 1, growing_areas_by_type: { home: 1 },
  });
});

// --- the fallback names are the server's -------------------------------------

test('the pre-rename keys read here are the ones the server still sends', () => {
  const schemas = readSrc('../../../garden-gnome/app/models/schemas.py');
  const census = readSrc('./census.ts');
  for (const key of ['total_environments', 'environments_by_type']) {
    expect(census).toContain(`r.${key}`);
    expect(schemas).toContain(`"${key}":`);
  }
});

// --- no census sync in the app ------------------------------------------------
// Pushing the community census is an operator job (POST /census/sync takes an
// operator credential). The card that offered it answered "skipped".

test('nothing in the app calls the census sync or export routes', () => {
  for (const file of ['./census.ts', '../screens/CensusScreen.tsx', '../screens/SettingsScreen.tsx']) {
    const src = readSrc(file);
    // A route as a string the code would request, not a comment naming it.
    expect(src).not.toMatch(/['"`]\/census\/(sync|export)/);
    expect(src).not.toMatch(/syncCensus/);
  }
});
