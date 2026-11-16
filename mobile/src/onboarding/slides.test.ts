import { FINISH, SLIDES } from './slides';

// Read sibling modules to check the copy against them, as consent/copy.test
// does. Declared locally rather than pulling in @types/node, whose globals
// conflict with React Native's timer typings.
declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');

const readSrc = (rel: string): string =>
  fs.readFileSync(path.join(__dirname, rel), 'utf8');

const slide = (title: RegExp) => SLIDES.find((s) => title.test(s.title))!;

test('four slides: what the app is, the land, what it shows, then plants', () => {
  expect(SLIDES).toHaveLength(4);
  expect(SLIDES[0].body).toMatch(/land and the plants on it/);
  const land = SLIDES.findIndex((s) => /add your land/i.test(s.title));
  const see = SLIDES.findIndex((s) => /see your land/i.test(s.title));
  const plants = SLIDES.findIndex((s) => /add plants/i.test(s.title));
  expect(land).toBeGreaterThan(0);
  expect(see).toBeGreaterThan(land);
  expect(plants).toBeGreaterThan(see);
});

// --- the copy matches what the code does ------------------------------------

test('the land slide names what setup offers and what the site profile reads', () => {
  const land = slide(/add your land/i).body;
  const setup = readSrc('../screens/PropertySetupScreen.tsx');
  expect(land).toMatch(/Type an address or use your location/);
  expect(setup).toMatch(/Type your address or use your location/);
  expect(land).toMatch(/put a pin on your home/);
  // Every value it names is a site-profile field the server sends.
  const fields = readSrc('../types/site.ts');
  for (const [word, field] of [
    ['sun', 'sun'], ['where water collects', 'water_collects'], ['soil', 'soil_texture'],
    ['hardiness zone', 'hardiness_zone'], ['frost dates', 'frost_dates'],
  ]) {
    expect(land).toContain(word);
    expect(fields).toContain(`'${field}'`);
  }
  // Confidence and source on every value, and a correction where allowed.
  expect(fields).toMatch(/confidence_label: ConfidenceLabel/);
  expect(fields).toMatch(/sources: Source\[\]/);
  expect(land).toMatch(/correct any of them/);
});

test('the land slide says the maps are for the United States, as setup does', () => {
  expect(slide(/add your land/i).body).toMatch(/United States/);
  expect(readSrc('../screens/PropertySetupScreen.tsx')).toMatch(/cover the United States only/);
});

test('the map layers it names are the layers the map knows', () => {
  const see = slide(/see your land/i).body;
  expect(see).toMatch(/Sun, Trees and Water layers/);
  expect(readSrc('../land/mapLayers.ts')).toMatch(/sun: 'Sun', trees: 'Trees', water: 'Water'/);
  const home = readSrc('../screens/HomeScreen.tsx');
  expect(home).toMatch(/<SeasonTimeline/);
  expect(home).toMatch(/ForecastBars/);
});

test('advice is described as what it is, and nothing switched off is promised', () => {
  const plants = slide(/add plants/i).body;
  expect(plants).toMatch(/set rules/);
  // The plant page always offers rule-based care advice.
  const detail = readSrc('../screens/PlantDetailScreen.tsx');
  expect(detail).toMatch(/Get care advice/);
  // Photo check-ups and free-text questions are off on the server.
  for (const s of SLIDES) expect(`${s.title} ${s.body}`).not.toMatch(/photo|ask the gnome|questions?\b/i);
});

test('the last button leads to Home, not Add plant', () => {
  expect(FINISH.route).toBe('Home');
  const screen = readSrc('./Onboarding.tsx');
  expect(screen).toMatch(/navigation\.navigate\(FINISH\.route\)/);
  expect(screen).not.toMatch(/'AddPlant'|onPress=\{isLast \? onAddPlant/);
});

test('every slide says something, in plain words', () => {
  for (const s of SLIDES) {
    expect(s.emoji.trim()).not.toBe('');
    expect(s.title.trim()).not.toBe('');
    expect(s.body.trim()).not.toBe('');
    const text = `${s.title} ${s.body}`;
    expect(text).not.toMatch(/_|\[stub\]/i);
    // No tabs any more, and no em dashes in owner-facing copy.
    expect(text).not.toMatch(/\btabs?\b/i);
    expect(text).not.toContain('—');
  }
});
