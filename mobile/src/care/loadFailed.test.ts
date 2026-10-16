import { LOAD_FAILED, loadFailedTitle } from './loadFailed';

// Read the screens: the rule is about how each one handles a failed query,
// which a unit test of the copy alone cannot see. Declared locally rather
// than pulling in @types/node, which conflicts with React Native's typings.
declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');
const read = (rel: string): string => fs.readFileSync(path.join(__dirname, rel), 'utf8');

const SCREENS = [
  '../screens/PlantDetailScreen.tsx',
  '../screens/SpeciesDetailScreen.tsx',
  '../screens/GrowingAreaDetailScreen.tsx',
  '../screens/AlmanacScreen.tsx',
  '../screens/SpeciesScreen.tsx',
];

test('the copy names no backend and offers a way out', () => {
  expect(LOAD_FAILED.body).not.toMatch(/backend|api|url|server is running/i);
  expect(LOAD_FAILED.action).toBe('Try again');
  expect(loadFailedTitle('this plant')).toBe('Couldn’t load this plant');
});

test.each(SCREENS)('%s shows a retry when its first load fails', (rel) => {
  const src = read(rel);
  expect(src).toMatch(/<EmptyState[\s\S]*?LOAD_FAILED\.action[\s\S]*?onAction=\{\(\) => refetch\w*\(\)\}/);
});

test.each(SCREENS)('%s never spins on a load that failed', (rel) => {
  // `isLoading || !data` stays true forever once the query errors.
  expect(read(rel)).not.toMatch(/if \(isLoading \|\| !\w+\)/);
});
