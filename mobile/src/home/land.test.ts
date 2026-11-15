import { landLines } from './land';
import { Explained, SiteProfile, SiteValue, VitalCard } from '../types/site';

const explained = (display: string): Explained => ({
  display, confidence: 'area_estimate', confidence_label: 'Area estimate',
  reason: `Reason for ${display}`, sources: [{ name: 'Soil survey' }], provenance: 'public_map',
});
const value = (field: SiteValue['field'], display: string, zone_id: number | null = null): SiteValue => ({
  ...explained(display), field, title: field, zone_id, can_override: true,
  override_choices: [], override_kind: 'choice',
});
const profile = (values: SiteValue[]): SiteProfile => ({
  property_id: 1, status: { fast: 'ready', background: 'ready' }, values, zones: [], notes: [],
});

test('sun, soil, drainage and hardiness, in that order, from the whole lot', () => {
  const lines = landLines(profile([
    value('hardiness_zone', 'Hardiness zone 7b'),
    value('sun', 'Part shade, zone', 9),
    value('sun', 'Full sun'),
    value('soil_texture', 'Silt loam'),
    value('soil_drainage', 'Well drained'),
    value('water_collects', 'Drains freely'),
  ]), []);
  expect(lines.map((l) => [l.key, l.explained.display, l.field])).toEqual([
    ['sun', 'Full sun', 'sun'],
    ['soil', 'Silt loam', 'soil_texture'],
    ['drainage', 'Drains freely', 'water_collects'],
    ['hardiness', 'Hardiness zone 7b', 'hardiness_zone'],
  ]);
});

test('drainage falls back to the soil drainage class', () => {
  const lines = landLines(profile([value('soil_drainage', 'Somewhat poorly drained')]), []);
  expect(lines).toHaveLength(1);
  expect(lines[0]).toMatchObject({ key: 'drainage', field: 'soil_drainage' });
});

test('before the profile arrives the vitals cards stand in, only with their reason', () => {
  const cards: VitalCard[] = [
    { key: 'sun', title: 'Sun', value_text: 'Part shade', detail: '', tone: 'ok', explained: explained('Part shade') },
    { key: 'soil', title: 'Soil', value_text: 'Clay', detail: '', tone: 'ok' },
  ];
  const lines = landLines(undefined, cards);
  expect(lines.map((l) => l.key)).toEqual(['sun']);
  expect(lines[0].explained.reason).toBe('Reason for Part shade');
});
