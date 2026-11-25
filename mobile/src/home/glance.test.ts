import { landGlance, soilWord, sunWord } from './glance';
import { Explained, SiteProfile, SiteValue } from '../types/site';

const value = (
  field: SiteValue['field'], display: string, v: unknown, confidence: Explained['confidence'] = 'area_estimate',
): SiteValue => ({
  display, confidence, confidence_label: 'Area estimate', reason: 'r', sources: [{ name: 'Survey' }],
  provenance: 'public_map', field, title: field, value: v, zone_id: null, can_override: true,
  override_choices: [], override_kind: 'choice',
});
const profile = (values: SiteValue[]): SiteProfile => ({
  property_id: 1, status: { fast: 'ready', background: 'ready' }, values, zones: [], notes: [],
});

test('sun, water and soil, one word each, marked est. when estimated', () => {
  const g = landGlance(profile([
    value('sun', 'About 7 hours', 'full_sun'),
    value('water_collects', 'Drains freely', { class: 'drains_freely' }),
    value('soil_texture', 'Fine sandy loam', { texture: 'Fine sandy loam', sand_percent: 69, clay_percent: 10 }),
  ]));
  expect(g.map((x) => [x.key, x.word, x.estimated])).toEqual([
    ['sun', 'Sunny', true], ['water', 'Drains', true], ['soil', 'Loamy', true],
  ]);
  expect(g[0].a11y).toBe('Sun: Sunny, estimated.');
  expect(g[0].field).toBe('sun');
});

test('what the owner said is not marked, and a slow value says Checking', () => {
  const g = landGlance(profile([
    value('sun', 'Part shade', 'part_shade', 'you_told_us'),
    value('soil_texture', 'Not known yet. PlantAdvocate will try again.', null, 'not_known_yet'),
  ]));
  expect(g.map((x) => [x.key, x.word, x.estimated, x.checking])).toEqual([
    ['sun', 'Part shade', false, false], ['soil', 'Checking', false, true],
  ]);
});

test('words from hours and from the soil mix', () => {
  expect(sunWord({ hours: 2, category: null })).toBe('Shady');
  expect(sunWord({ hours: 4, category: null })).toBe('Part shade');
  expect(soilWord({ texture: null, mix: { sand: 20, silt: 30, clay: 50 } })).toBe('Clay');
  expect(soilWord({ texture: 'Silt loam', mix: null })).toBe('Silty');
});

test('no land, no glance', () => {
  expect(landGlance(null)).toEqual([]);
});
