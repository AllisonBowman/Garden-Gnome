import {
  LAND_SECTIONS, correctionShowing, drawnZones, groupValues, overrideBody, parseNumberOverride,
  publicLine, refetchEvery, sectionOf, selectedChoice, wholeLotValues, cleanName, FROST_BIAS_CHOICES,
} from './profileRows';
import { SiteField, SiteProfile, SiteValue } from '../types/site';

const v = (field: SiteField, extra: Partial<SiteValue> = {}): SiteValue => ({
  display: `${field} value`, confidence: 'area_estimate', confidence_label: 'Area estimate',
  reason: 'Because.', sources: [{ name: 'Soil survey' }], provenance: 'public_map',
  field, title: field, can_override: false, override_choices: [], override_kind: 'none', ...extra,
});

const profile = (values: SiteValue[], zones: SiteProfile['zones'] = []): SiteProfile => ({
  property_id: 1, status: { fast: 'ready', background: 'ready' }, values, zones, notes: [],
});

test('values read in the fixed order, empty groups left out', () => {
  const sections = groupValues([
    v('land_cover'), v('frost_dates'), v('hardiness_zone'), v('facing'), v('slope'),
    v('water_collects'), v('soil_ph'), v('soil_drainage'), v('sun'),
  ]);
  expect(sections.map((s) => s.key)).toEqual(['sun', 'soil', 'water', 'slope', 'hardiness', 'frost', 'land_cover']);
  expect(sections[1].values.map((x) => x.field)).toEqual(['soil_drainage', 'soil_ph']);
  expect(sections[3].values.map((x) => x.field)).toEqual(['slope', 'facing']);
});

test('every site field has a place, and an unknown one still shows', () => {
  const all: SiteField[] = ['sun', 'soil_drainage', 'water_collects', 'soil_texture', 'soil_ph',
    'disturbed_soil', 'slope', 'facing', 'flooding', 'land_cover', 'hardiness_zone', 'frost_dates'];
  const placed = LAND_SECTIONS.flatMap((s) => s.fields);
  expect([...placed].sort()).toEqual([...all].sort());
  const odd = v('sun', { field: 'night_sky' as SiteField });
  expect(groupValues([odd]).map((s) => s.title)).toEqual(['More']);
  expect(sectionOf('soil_ph')).toBe('soil');
  expect(sectionOf(undefined)).toBeNull();
});

test('the whole lot falls back to the whole-lot zone; drawn zones exclude it', () => {
  const zones = [
    { zone_id: 1, name: 'Whole lot', is_whole_lot: true, values: [v('sun')] },
    { zone_id: 2, name: 'Front bed', is_whole_lot: false, values: [v('sun', { zone_id: 2 })] },
  ];
  expect(wholeLotValues(profile([], zones)).map((x) => x.field)).toEqual(['sun']);
  expect(wholeLotValues(profile([v('slope')], zones)).map((x) => x.field)).toEqual(['slope']);
  expect(drawnZones(profile([], zones)).map((z) => z.zone_id)).toEqual([2]);
});

test('a correction keeps the public reading visible and marks its choice', () => {
  const sun = v('sun', {
    provenance: 'owner', confidence: 'you_told_us', confidence_label: 'You told us', value: 'part_shade',
    can_override: true, override_kind: 'choice',
    override_choices: [{ value: 'full_sun', label: 'Full sun' }, { value: 'part_shade', label: 'Part shade' }],
    public: { display: 'Full sun, about 7 hours', confidence_label: 'Area estimate' },
  });
  expect(correctionShowing(sun)).toBe(true);
  expect(publicLine(sun)).toBe('Public data reading: Full sun, about 7 hours (Area estimate).');
  expect(selectedChoice(sun)).toBe('part_shade');
  expect(selectedChoice({ ...sun, provenance: 'modelled', public: null })).toBeNull();
});

test('a choice is a tap, a number is measured, and a zone is named when given', () => {
  const sun = v('sun', { override_kind: 'choice' });
  expect(overrideBody(sun, 'shade')).toEqual({ field: 'sun', value: 'shade', method: 'tap' });
  expect(overrideBody(sun, 'shade', 7)).toEqual({ field: 'sun', value: 'shade', method: 'tap', zone_id: 7 });
  expect(overrideBody(v('soil_ph', { override_kind: 'number', zone_id: 3 }), 6.5))
    .toEqual({ field: 'soil_ph', value: 6.5, method: 'measured', zone_id: 3 });
});

test('a soil test number is checked and kept to one decimal', () => {
  expect(parseNumberOverride('soil_ph', ' 6.45 ')).toEqual({ ok: true, value: 6.5 });
  expect(parseNumberOverride('soil_ph', '6,2')).toEqual({ ok: true, value: 6.2 });
  expect(parseNumberOverride('soil_ph', '15').ok).toBe(false);
  expect(parseNumberOverride('soil_ph', 'acid').ok).toBe(false);
  expect(parseNumberOverride('soil_ph', '-1').ok).toBe(false);
});

test('the screen asks again only while a step runs', () => {
  expect(refetchEvery({ fast: 'ready', background: 'building' })).toBe(5000);
  expect(refetchEvery({ fast: 'pending', background: 'pending' })).toBe(5000);
  expect(refetchEvery({ fast: 'ready', background: 'failed' })).toBe(false);
  expect(refetchEvery(undefined)).toBe(false);
});

test('names are tidied; the frost setting has three plain choices', () => {
  expect(cleanName('  Our   yard ')).toBe('Our yard');
  expect(cleanName('   ')).toBeNull();
  expect(FROST_BIAS_CHOICES.map((c) => c.value)).toEqual(['earlier', null, 'later']);
});
