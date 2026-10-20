import {
  NO_NAME_OBSERVATION, PHOTO_SUGGESTIONS_LABEL, SUGGESTED_OBSERVATION,
  UNAVAILABLE_OBSERVATION, UNREADABLE_OBSERVATION, notInCatalogObservation,
} from './copy';

declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');
const readSrc = (rel: string): string => fs.readFileSync(path.join(__dirname, rel), 'utf8');

const everyLine = [
  PHOTO_SUGGESTIONS_LABEL, SUGGESTED_OBSERVATION, UNAVAILABLE_OBSERVATION,
  UNREADABLE_OBSERVATION, NO_NAME_OBSERVATION, notInCatalogObservation('Monstera'),
];

// The phone guesses from a few coarse labels it reads off the photo. Nothing
// it says may read as knowing what the plant is.
test('no line claims the plant was identified', () => {
  for (const line of everyLine) {
    expect(line).not.toMatch(/identif/i);
    expect(line).not.toMatch(/\b(is|this is) (a|an|the) /i);
  }
});

test('a suggestion always asks the gardener to confirm it', () => {
  expect(PHOTO_SUGGESTIONS_LABEL).toMatch(/^Suggested from the photo/);
  expect(PHOTO_SUGGESTIONS_LABEL).toMatch(/check it’s right/);
  expect(SUGGESTED_OBSERVATION).toMatch(/^Suggested from the photo/);
  expect(SUGGESTED_OBSERVATION).toMatch(/confirm/);
});

test('no line names the machinery', () => {
  for (const line of everyLine) {
    expect(line).not.toMatch(/\b(model|on-device|AI|database|backend|Foundation|Gemini)\b/i);
  }
});

test('the name the phone suggested is quoted back, attributed to the phone', () => {
  expect(notInCatalogObservation('Monstera')).toBe(
    'Your phone suggested “Monstera”, but that isn’t in the catalog yet. '
    + 'Search below for the closest match.',
  );
});

// --- nothing is chosen for the gardener ---------------------------------------

test('Add plant does not pick a species from the photo on its own', () => {
  const screen = readSrc('../screens/AddPlantScreen.tsx');
  const start = screen.indexOf('const identifyMutation = useMutation({');
  expect(start).toBeGreaterThan(-1);
  const block = screen.slice(start, screen.indexOf('\n  });', start));
  expect(block).not.toMatch(/setSpeciesId/);
  expect(block).not.toMatch(/setSpeciesSearch/);
});

test('identify.ts takes every line it shows from this file', () => {
  const identify = readSrc('./identify.ts');
  expect(identify).not.toMatch(/Identified on-device/);
  expect(identify).not.toMatch(/observation:\s*['"`]/);
});
