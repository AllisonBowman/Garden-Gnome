import type { CensusSummary } from '../types';

// The server's route is read to check the client's keys against it, the way
// consent/copy.test.ts reads sibling modules. Declared locally rather than
// pulling in @types/node, which conflicts with React Native's timer typings.
declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');

const readSrc = (rel: string): string =>
  fs.readFileSync(path.join(__dirname, rel), 'utf8');

// GET /census/summary, spelled the way garden-gnome/app/routers/census.py
// sends it: snake_case throughout. The growing-areas rename once turned two of
// these into `total_growingAreas` and `growingAreas_by_type`, which the server
// never sent, and the Census tab threw on first open. A find-and-replace over
// this tree rewrites the type, the screen and a literal like this one together,
// so they keep agreeing with each other and with nothing real. The literal
// pins the type's names (tsc under ts-jest fails the file on a missing or
// unknown key); the tests below pin them to the server's own source.
const summary: CensusSummary = {
  total_plants: 7,
  total_growing_areas: 2,
  growing_areas_by_type: { home: 1, community_garden: 1 },
  plants_by_growing_area_type: { home: 5, community_garden: 2 },
  species_distribution: [{ species_id: 3, common_name: 'Basil', count: 4 }],
};

// A key counts as sent when the route spells it as a dict key (`"key":`), not
// when a comment merely mentions it.
const route = readSrc('../../../garden-gnome/app/routers/census.py');
const sent = (key: string) => route.includes(`"${key}":`);

test('every key CensusSummary declares is one the server route sends', () => {
  const declared = [
    ...Object.keys(summary),
    ...Object.keys(summary.species_distribution[0]),
  ];
  expect(declared.filter((k) => !sent(k))).toEqual([]);
});

test('every key CensusScreen reads off the summary is one the server route sends', () => {
  const reads = [...readSrc('../screens/CensusScreen.tsx').matchAll(/summary\.(\w+)/g)]
    .map((m) => m[1]);
  // Not vacuous: the two area counts are among the reads.
  expect(reads).toEqual(
    expect.arrayContaining(['total_growing_areas', 'growing_areas_by_type']),
  );
  expect(reads.filter((k) => !sent(k))).toEqual([]);
});
