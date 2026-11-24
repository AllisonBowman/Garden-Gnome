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

// Screen text lives in the English resources (src/i18n/en) once it is
// translated, so a screen's words are its source plus those resources.
type Tree = { [k: string]: string | Tree };
const leafText = (tree: Tree): string[] =>
  Object.values(tree).flatMap((v) => (typeof v === 'string' ? [v] : leafText(v)));
const EN_DIR = path.join(__dirname, '../i18n/en');
const EN_TEXT = [
  ...leafText(require('../i18n/en').default),
  // The resource files as written, for checks on their structure.
  ...fs.readdirSync(EN_DIR).map((f: string) => fs.readFileSync(path.join(EN_DIR, f), 'utf8')),
].join('\n');
const readScreen = (rel: string): string => `${readSrc(rel)}\n${EN_TEXT}`;

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
  const setup = readScreen('../screens/PropertySetupScreen.tsx');
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
  expect(readScreen('../screens/PropertySetupScreen.tsx')).toMatch(/cover the United States only/);
});

test('the map layers it names are the layers the map knows', () => {
  const see = slide(/see your land/i).body;
  expect(see).toMatch(/Sun, Trees and Water layers/);
  expect(readScreen('../land/mapLayers.ts')).toMatch(/sun: ['"]Sun['"],\s*trees: ['"]Trees['"],\s*water: ['"]Water['"]/);
  const home = readSrc('../screens/HomeScreen.tsx');
  expect(home).toMatch(/<SeasonTimeline/);
  expect(home).toMatch(/ForecastBars/);
});

test('advice is described as what it is, and nothing switched off is promised', () => {
  const plants = slide(/add plants/i).body;
  expect(plants).toMatch(/set rules/);
  // The plant page always offers rule-based care advice.
  const detail = readScreen('../screens/PlantDetailScreen.tsx');
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

describe('in Spanish', () => {
  afterEach(() => { delete (globalThis as { __TEST_LOCALES__?: string[] }).__TEST_LOCALES__; });

  it('the slides and the last button speak Spanish on a Spanish phone', () => {
    (globalThis as { __TEST_LOCALES__?: string[] }).__TEST_LOCALES__ = ['es-MX'];
    let mod: typeof import('./slides') | undefined;
    jest.isolateModules(() => { mod = require('./slides'); });
    expect(mod!.SLIDES).toHaveLength(4);
    expect(mod!.SLIDES[0].title).toBe('Te damos la bienvenida a PlantAdvocate');
    expect(mod!.SLIDES[1].title).toBe('Agrega tu terreno');
    expect(mod!.FINISH).toEqual({ route: 'Home', label: 'Comenzar' });
    expect(mod!.GROWING_AREAS_TAB).toBe('Áreas de cultivo');
    for (const s of mod!.SLIDES) expect(s.body).not.toContain('—');
  });
});
