// The not-advice line. The App Store listing and the review notes say the
// app shows it, so this pins the sentence word for word, proves the shared
// note shows exactly that sentence in the muted colour, and checks that each
// screen with a hazard sentence puts the note straight under it.
//
// This jest setup can't load React Native (see jest.config.js), so the
// modules the note touches are stood in for by name and the component is
// called directly, as ErrorBoundary.test.ts does.
jest.mock('react-native', () => ({
  StyleSheet: { create: (s: unknown) => s },
}));
jest.mock('react-native-paper', () => ({ Text: 'Text' }));
jest.mock('../theme/ThemeProvider', () => ({
  useAppTheme: () => ({ palette: { sub: '#5A6B52' }, fonts: {} }),
}));

import NotAdviceNote from '../components/NotAdviceNote';
import { NOT_ADVICE_LINE } from './notAdvice';

declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..');
const read = (rel: string): string => fs.readFileSync(path.join(SRC, rel), 'utf8');

/** A style prop as one object, the last entry winning, as React Native does. */
const flat = (style: unknown): Record<string, unknown> =>
  Object.assign({}, ...[style].flat(Infinity).filter(Boolean));

test('the sentence is the one the listing and the review notes promise', () => {
  expect(NOT_ADVICE_LINE).toBe(
    'These notes repeat what the sources publish. They are not medical or veterinary advice.');
});

test('the note shows that sentence, muted, with the screen’s own spacing last', () => {
  const note = NotAdviceNote({ style: { marginTop: 6 } });
  expect(note.props.children).toBe(NOT_ADVICE_LINE);
  expect(flat(note.props.style)).toMatchObject({ color: '#5A6B52', marginTop: 6 });
});

// Each screen that shows the hazard sentence, and how it renders it.
const SCREENS: [string, RegExp][] = [
  ['SpeciesDetailScreen.tsx', /\{\s*species\.toxicity_description\s*\}/],
  ['PlantDetailScreen.tsx', /\{\s*species\.toxicity_description\s*\}/],
  ['AddPlantScreen.tsx', /\{\s*selectedToxicity\.text\s*\}/],
];

test.each(SCREENS)('%s puts the note straight under its hazard sentence', (file, sentence) => {
  const src = read(`screens/${file}`);
  expect(src).toMatch(/import NotAdviceNote from '\.\.\/components\/NotAdviceNote'/);
  const shown = src.search(sentence);
  const note = src.indexOf('<NotAdviceNote');
  expect(shown).toBeGreaterThan(-1);
  expect(note).toBeGreaterThan(shown);
  // Nothing else starts between the two: no card, no section, no fit check.
  expect(src.slice(shown, note)).not.toMatch(/<(Card|Eyebrow|AreaFitCard|View)\b/);
});

test('the sentence lives in one place, not in a copy per screen', () => {
  const files: string[] = fs.readdirSync(SRC, { recursive: true });
  const holders = files
    .filter((f) => /\.tsx?$/.test(f) && !/\.test\.ts$/.test(f))
    .filter((f) => /medical or veterinary/i.test(read(f)))
    .map((f) => f.split(path.sep).join('/'));
  expect(holders).toEqual(['care/notAdvice.ts']);
});
