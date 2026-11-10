import { GROWING_AREAS_TAB, SLIDES } from './slides';

// Read sibling modules to check the copy against them, as consent/copy.test
// does. Declared locally rather than pulling in @types/node, whose globals
// conflict with React Native's timer typings.
declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');

const readSrc = (rel: string): string =>
  fs.readFileSync(path.join(__dirname, rel), 'utf8');

const placeSlide = () => SLIDES.find((s) => /where you grow/i.test(s.title));

test('first run says where plants grow, before it says to add one', () => {
  const place = SLIDES.findIndex((s) => /where you grow/i.test(s.title));
  const plants = SLIDES.findIndex((s) => /add plants/i.test(s.title));
  expect(place).toBeGreaterThan(0);
  expect(plants).toBeGreaterThan(place);
});

// --- the copy matches what the code does ------------------------------------

test('it sends people to the tab by the title the tab actually wears', () => {
  expect(placeSlide()!.body).toContain(GROWING_AREAS_TAB);
  // App titles the tab from the same constant. Typing a new title there
  // instead would leave the slide pointing at a tab that no longer exists.
  expect(readSrc('../../App.tsx')).toMatch(/title: GROWING_AREAS_TAB,/);
});

test('what it promises an area shows is what an area shows', () => {
  // "shows what suits it — and says what it can't check"
  const area = readSrc('../screens/GrowingAreaDetailScreen.tsx');
  expect(area).toMatch(/Good candidates here/);
  expect(area).toMatch(/uncheckedNotes\(/);
});

test('every slide says something, in words rather than tokens', () => {
  for (const slide of SLIDES) {
    expect(slide.title.trim()).not.toBe('');
    expect(slide.body.trim()).not.toBe('');
    expect(`${slide.title} ${slide.body}`).not.toMatch(/_|\[stub\]/i);
  }
});
