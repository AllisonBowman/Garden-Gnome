import {
  HARDINESS_GAUGE_LABELS, SUN_GAUGE_LABELS, WATER_CLASSES, parseHardiness, parseSoil, parseSun, parseWater,
  readingTiles, tileValueText,
} from './readingTiles';
import { Explained, SiteProfile, SiteValue, VitalCard } from '../types/site';

const explained = (display: string): Explained => ({
  display, confidence: 'area_estimate', confidence_label: 'Area estimate',
  reason: `Reason for ${display}`, sources: [{ name: 'Survey' }], provenance: 'public_map',
});
const value = (
  field: SiteValue['field'], display: string, v: unknown, zone_id: number | null = null,
  facts: SiteValue['facts'] = undefined,
): SiteValue => ({
  ...explained(display), field, title: field, value: v, zone_id, can_override: true,
  override_choices: [], override_kind: 'choice', ...(facts !== undefined ? { facts } : {}),
});
const profile = (values: SiteValue[]): SiteProfile => ({
  property_id: 1, status: { fast: 'ready', background: 'ready' }, values, zones: [], notes: [],
});

test('all four tiles from the whole lot, in order, with graphics', () => {
  const tiles = readingTiles(profile([
    value('hardiness_zone', 'Hardiness zone 7b', { zone: '7b', low_f: 5, high_f: 10 }),
    value('sun', 'Part shade', { category: 'shade', hours: 1 }, 9),
    value('sun', 'Full sun', { category: 'full_sun', hours: 7.24 }),
    value('soil_texture', 'Silt loam', { texture: 'Silt loam', family: 'loamy', sand_percent: 20, clay_percent: 18 }),
    value('water_collects', 'Drains freely', { class: 'drains_freely' }),
  ]), []);
  expect(tiles.map((t) => [t.key, t.title, t.valueText])).toEqual([
    ['sun', 'Sun', 'About 7 hours'],
    ['soil', 'Topsoil', 'Silt loam'],
    ['drainage', 'Where water collects', 'Drains freely'],
    ['hardiness', 'Hardiness zone', 'Zone 7b'],
  ]);
  const [sun, soil, water, zone] = tiles;
  expect(sun.gauge?.fraction).toBeCloseTo(7.24 / 12);
  expect(sun.detail).toBe('Full sun');
  expect(sun.field).toBe('sun');
  expect(soil.mix).toEqual({ sand: 20, silt: 62, clay: 18 });
  expect(soil.detail).toBe('Sand 20%, silt 62%, clay 18%');
  expect(soil.gauge).toBeNull();
  expect(water.gauge).toBeNull();
  expect(water.steps).toEqual({ labels: ['Drains freely', 'Slow to drain', 'Gathers after rain', 'Often wet'], current: 0 });
  expect(zone.detail).toBe('Coldest night of the year, on average 5°F to 10°F');
  expect(zone.gauge?.fraction).toBeCloseTo(13.5 / 26);
  expect(zone.a11y).toBe('Hardiness zone: Zone 7b. Coldest night of the year, on average 5 degrees Fahrenheit to 10 degrees Fahrenheit. Confidence: Area estimate.');
  expect(soil.a11y).toContain('Sand 20 percent');
  for (const t of tiles) {
    expect(t.confidenceLabel).toBe('Area estimate');
    expect(t.explained.reason).toMatch(/^Reason for/);
  }
});

test('a value that cannot be parsed still makes a tile, with its display text and no graphic', () => {
  const tiles = readingTiles(profile([
    value('sun', 'About half a day', 'lots'),
    value('hardiness_zone', 'Not known yet', null),
    value('soil_texture', 'Mixed fill', { family: 'loamy' }),
    value('water_collects', 'Unclear', { class: 'swampy' }),
  ]), []);
  expect(tiles.map((t) => [t.valueText, t.gauge ?? t.steps, t.mix, t.detail])).toEqual([
    ['About half a day', null, null, ''],
    ['Mixed fill', null, null, ''],
    ['Unclear', null, null, ''],
    ['Not known yet', null, null, ''],
  ]);
});

test('drainage from the soil survey class is titled Drainage', () => {
  const [t] = readingTiles(profile([value('soil_drainage', 'Well drained', { class: 'well drained' })]), []);
  expect(t).toMatchObject({ key: 'drainage', title: 'Drainage', valueText: 'Well drained', gauge: null, steps: null });
});

test('before the profile arrives the vitals cards stand in, text only', () => {
  const cards: VitalCard[] = [
    { key: 'sun', title: 'Sun', value_text: 'Part shade', detail: '', tone: 'ok', explained: explained('Part shade') },
  ];
  const [t] = readingTiles(undefined, cards);
  expect(t).toMatchObject({ key: 'sun', valueText: 'Part shade', gauge: null, field: undefined });
  expect(t.a11y).toBe('Sun: Part shade. Confidence: Area estimate.');
});

test('no land readings: no tiles', () => {
  expect(readingTiles(profile([]), [])).toEqual([]);
});

describe('parsers', () => {
  test('sun', () => {
    expect(parseSun({ hours: 5, category: 'part_shade' })).toEqual({ hours: 5, category: 'part_shade' });
    expect(parseSun({ hours: '3.5' })).toEqual({ hours: 3.5, category: null });
    expect(parseSun(4)).toEqual({ hours: 4, category: null });
    expect(parseSun('full_sun')).toEqual({ hours: null, category: 'full_sun' });
    expect(parseSun({ hours: 30 })).toBeNull();
    expect(parseSun({ hours: -1, category: 'shade' })).toEqual({ hours: null, category: 'shade' });
    expect(parseSun({ hours: NaN })).toBeNull();
    expect(parseSun(null)).toBeNull();
  });

  test('sun with a category and no hours shows the category without a gauge', () => {
    const [t] = readingTiles(profile([value('sun', 'Full sun (you told us)', { category: 'full_sun' })]), []);
    expect(t).toMatchObject({ valueText: 'Full sun', gauge: null });
  });

  test('hardiness', () => {
    expect(parseHardiness({ zone: '7b', low_f: 5, high_f: 10 })).toMatchObject({ zone: '7b', number: 7, half: 'b' });
    expect(parseHardiness('Zone 6A')).toMatchObject({ zone: '6a', low_f: null });
    expect(parseHardiness({ zone: 9 })).toMatchObject({ zone: '9', half: null });
    expect(parseHardiness({ zone: '14a' })).toBeNull();
    expect(parseHardiness({ zone: 'tropical' })).toBeNull();
    expect(parseHardiness(undefined)).toBeNull();
  });

  test('hardiness with only a low, or a whole zone', () => {
    const [t] = readingTiles(profile([value('hardiness_zone', 'Zone 5', { zone: '5', low_f: -20 })]), []);
    expect(t.detail).toBe('Coldest night of the year, on average down to -20°F');
    expect(t.gauge?.fraction).toBeCloseTo(9 / 26);
  });

  test('water', () => {
    expect(parseWater({ class: 'often_wet' })).toBe('often_wet');
    expect(parseWater('slow_to_drain')).toBe('slow_to_drain');
    expect(parseWater({ class: 7 })).toBeNull();
    expect(parseWater([])).toBeNull();
  });

  test('soil', () => {
    expect(parseSoil({ texture: 'CLAY LOAM', sand_percent: 30, clay_percent: 35 }))
      .toEqual({ texture: 'CLAY LOAM', mix: { sand: 30, clay: 35, silt: 35 } });
    expect(parseSoil({ texture: 'Sand', sand_percent: 90, clay_percent: 20 })).toEqual({ texture: 'Sand', mix: null });
    expect(parseSoil('Loam')).toEqual({ texture: 'Loam', mix: null });
    expect(parseSoil({ sand_percent: 40, clay_percent: 10 })).toEqual({ texture: null, mix: { sand: 40, clay: 10, silt: 50 } });
    expect(parseSoil({})).toBeNull();
  });

  test('upper-case soil texture reads in sentence case', () => {
    const [t] = readingTiles(profile([value('soil_texture', 'Clay loam', { texture: 'CLAY LOAM' })]), []);
    expect(t.valueText).toBe('Clay loam');
  });
});

describe('sun hours over the API', () => {
  const display = 'Sun: full sun, about 7 hours of direct sun a day in the growing season.';

  test('the hours come from facts: value "About 7 hours", detail the category, a 0 to 12 hour gauge', () => {
    const [t] = readingTiles(profile([value('sun', display, 'full_sun', null, { hours: 7.0 })]), []);
    expect(t).toMatchObject({ title: 'Sun', valueText: 'About 7 hours', detail: 'Full sun', steps: null });
    expect(t.gauge).toEqual({ fraction: 7 / 12, startLabel: '0', endLabel: '12 hours' });
    expect(SUN_GAUGE_LABELS).toEqual({ start: '0', end: '12 hours' });
    expect(t.a11y).toBe('Sun: About 7 hours. Full sun. Confidence: Area estimate.');
  });

  test('hours are said to the half hour, as the server sentence says them', () => {
    const [t] = readingTiles(profile([value('sun', display, 'part_shade', null, { hours: 4.6 })]), []);
    expect(t.valueText).toBe('About 4.5 hours');
    expect(t.gauge?.fraction).toBeCloseTo(4.6 / 12);
  });

  test('facts win over hours inside the value', () => {
    expect(parseSun({ category: 'shade', hours: 1 }, { hours: 2.5 })).toEqual({ hours: 2.5, category: 'shade' });
    expect(parseSun('full_sun', { hours: 'x' })).toEqual({ hours: null, category: 'full_sun' });
  });

  test("an owner's answer has no facts: the category words, no gauge", () => {
    const [t] = readingTiles(profile([
      value('sun', 'Sun: part shade (3 to 6 hours). You told us.', 'part_shade', null, null),
    ]), []);
    expect(t).toMatchObject({ valueText: 'Part shade', detail: '', gauge: null, steps: null });
  });
});

describe('gauges and steps have captions', () => {
  test('hardiness runs from Zone 1, coldest, to Zone 13, warmest, by zone and half zone', () => {
    const tiles = (zone: string) => readingTiles(profile([value('hardiness_zone', `Zone ${zone}`, { zone })]), [])[0];
    expect(tiles('7a').gauge).toEqual({ fraction: 12.5 / 26, startLabel: 'Zone 1, coldest', endLabel: 'Zone 13, warmest' });
    expect(tiles('1a').gauge?.fraction).toBeCloseTo(0.5 / 26);
    expect(tiles('13b').gauge?.fraction).toBeCloseTo(25.5 / 26);
    expect(tiles('7b').gauge!.fraction).toBeGreaterThan(tiles('7a').gauge!.fraction);
    expect(HARDINESS_GAUGE_LABELS).toEqual({ start: 'Zone 1, coldest', end: 'Zone 13, warmest' });
  });

  test('where water collects: one labelled step per class the server sends, the current one marked', () => {
    expect([...WATER_CLASSES]).toEqual(['drains_freely', 'slow_to_drain', 'gathers_after_rain', 'often_wet']);
    WATER_CLASSES.forEach((c, i) => {
      const [t] = readingTiles(profile([value('water_collects', 'Where water collects: x.', { class: c })]), []);
      expect(t.gauge).toBeNull();
      expect(t.steps?.labels).toHaveLength(4);
      expect(t.steps?.current).toBe(i);
    });
  });

  test('an unknown water class, or an owner answer, draws no graphic', () => {
    const [a] = readingTiles(profile([value('water_collects', 'Where water collects: not known yet.', null)]), []);
    const [b] = readingTiles(profile([value('water_collects', 'You told us water stands here after rain.', 'stands_after_rain')]), []);
    expect([a.gauge, a.steps, b.gauge, b.steps]).toEqual([null, null, null, null]);
    expect(a.valueText).toBe('Not known yet');
  });
});

describe('a tile never repeats its title and has no trailing full stop', () => {
  test('Topsoil: not known yet. reads Not known yet', () => {
    const [t] = readingTiles(profile([value('soil_texture', 'Topsoil: not known yet.', null)]), []);
    expect(t).toMatchObject({ title: 'Topsoil', valueText: 'Not known yet' });
  });

  test('the rule, on every tile', () => {
    const tiles = readingTiles(profile([
      value('sun', 'Sun: not known yet.', null),
      value('soil_texture', 'Topsoil: not known yet.', null),
      value('water_collects', 'Where water collects: not known yet.', null),
      value('hardiness_zone', 'Hardiness zone: not known yet.', null),
    ]), []);
    expect(tiles).toHaveLength(4);
    for (const t of tiles) {
      expect(t.valueText.toLowerCase().startsWith(t.title.toLowerCase())).toBe(false);
      expect(t.valueText).not.toMatch(/\.$/);
      expect(t.valueText).toBe('Not known yet');
    }
  });

  test('tileValueText', () => {
    expect(tileValueText('Topsoil', 'Topsoil: not known yet.')).toBe('Not known yet');
    expect(tileValueText('Sun', 'Sunny corner.')).toBe('Sunny corner');
    expect(tileValueText('Hardiness zone', 'Hardiness zone 7b')).toBe('7b');
    expect(tileValueText('Sun', 'Sun.')).toBe('');
  });

  test('a hardiness value that is not a zone but whose display names one reads Zone 7b with its gauge', () => {
    const [t] = readingTiles(profile([value('hardiness_zone', 'Hardiness zone 7b', null)]), []);
    expect(t.valueText).toBe('Zone 7b');
    expect(t.gauge).not.toBeNull();
  });
});
