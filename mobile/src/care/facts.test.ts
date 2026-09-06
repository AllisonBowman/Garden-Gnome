// The screens read the claim graph through one module, and this pins what it
// may say. Every rule here exists because the alternative misleads someone:
// a raw column token is not a fact a caretaker can act on; a synthetic legacy
// value beside a cited one looks equally cited; a value borrowed from the
// genus must say so (ADR 0002); and "no record" must never read as "safe" or
// as "verified" (CONTEXT.md bans that word for care data).
import {
  CATALOG_LINE, careFactRows, careSourceLabels, careStatusLine, legacyStats,
  monthSpan, waterRegimeSentence,
} from './facts';
import { Species } from '../types';

const NCSU = 'https://plants.ces.ncsu.edu/plants/fuchsia-magellanica/';
const RHS = 'https://www.rhs.org.uk/plants/fuchsia-magellanica';
const CLEMSON = 'https://hgic.clemson.edu/factsheet/fuchsia/';
const GENUS_PAGE = 'https://plants.ces.ncsu.edu/plants/fuchsia/';

const RESOLVED: Partial<Species> = {
  light_fc_min: 100, light_fc_good: 250, direct_sun_hours_max: 2,
  water_regime: 'dry_surface_between', water_check_depth_cm: 3,
  water_growing_days_est: 7, water_dormant_days_est: 14,
  humidity_need: 'high',
  day_f_min: 65, day_f_max: 80, night_f_min: 55, chill_damage_f: 45,
  soil_base: 'chunky_aroid', soil_drainage: 'fast',
  soil_ph_min: 5.5, soil_ph_max: 6.5,
  fertilize_active_months: [3, 4, 5, 6, 7, 8, 9, 10],
  fertilize_interval_days: 14, fertilize_strength: 'half',
  outdoor_sun_exposure: ['part_sun', 'part_shade'],
  hardiness_zones: [7, 8, 9, 10],
};
const ALL_SOURCED = Object.fromEntries(
  Object.keys(RESOLVED).map((f) => [f, 'sourced' as const]));

const LEGACY: Partial<Species> = {
  light_need: 'bright_indirect',
  humidity_pct_min: 40, humidity_pct_max: 60,
  temp_f_min: 60, temp_f_max: 85,
  soil_type: 'well-draining',
};

/** A minted row (ADR 0005): identity and nothing else. */
function minted(over: Partial<Species> = {}): Species {
  return {
    id: 1, common_name: 'Hardy fuchsia', scientific_name: 'Fuchsia magellanica',
    care_notes: '', ...over,
  } as Species;
}

function sourced(over: Partial<Species> = {}): Species {
  return minted({
    ...RESOLVED, care_provenance: ALL_SOURCED, care_data_status: 'sourced',
    care_sources: [
      { authority: 'NC State Extension', url: NCSU, fields: ['light_fc_min'], inferred: false },
    ],
    ...over,
  });
}

const values = (s: Species) => careFactRows(s).map((r) => r.value).join('\n');

// --- careFactRows -----------------------------------------------------------

test('one row per resolved concept, in the order a caretaker reads them', () => {
  expect(careFactRows(sourced()).map((r) => r.key)).toEqual([
    'water', 'light', 'humidity', 'temperature', 'soil',
    'fertilize', 'outdoor_sun', 'hardiness',
  ]);
});

test('the watering row is the regime and the check depth, no dry-down target', () => {
  const water = careFactRows(sourced()).find((r) => r.key === 'water')!;
  expect(water.label).toBe('Watering');
  expect(water.value).toBe('Let the surface dry between waterings; check 3 cm down');
});

test('light, humidity, temperature and soil read as sentences, not columns', () => {
  const by = Object.fromEntries(careFactRows(sourced()).map((r) => [r.key, r.value]));
  expect(by.light).toBe('At least 100 footcandles; 250 footcandles is comfortable; up to 2 hours of direct sun');
  expect(by.humidity).toBe('High; wants humid air');
  expect(by.temperature).toBe('Days 65–80°F; nights from 55°F; cold damage below 45°F');
  expect(by.soil).toBe('Chunky aroid mix; fast-draining; pH 5.5–6.5');
  expect(by.fertilize).toBe('Mar–Oct; every 14 days; half strength');
  expect(by.outdoor_sun).toBe('Part sun, part shade');
  expect(by.hardiness).toBe('Zones 7–10');
});

test('no column token ever reaches a row', () => {
  const text = values(sourced());
  expect(text).not.toMatch(/[a-z]_[a-z]/);
  for (const token of ['dry_surface_between', 'chunky_aroid', 'part_sun', 'half'])
    expect(text.split('\n').some((v) => v === token)).toBe(false);
});

test('a row with nothing resolved has no fact rows — not rows of dashes', () => {
  expect(careFactRows(minted())).toEqual([]);
  expect(careFactRows(minted(LEGACY))).toEqual([]);
});

test('a partial band is stated as the half that exists', () => {
  const only = minted({ day_f_max: 80, care_provenance: { day_f_max: 'sourced' } });
  expect(values(only)).toBe('Days up to 80°F');
});

test('a row is inferred when any field it drew on came from the genus', () => {
  const s = sourced({
    care_provenance: { ...ALL_SOURCED, water_check_depth_cm: 'genus_inferred' },
  });
  const rows = careFactRows(s);
  expect(rows.find((r) => r.key === 'water')!.inferred).toBe(true);
  expect(rows.filter((r) => r.key !== 'water').every((r) => !r.inferred)).toBe(true);
});

test('a genus flag on a field the row did not use does not taint it', () => {
  const s = minted({
    water_regime: 'keep_moist',
    care_provenance: { water_regime: 'sourced', water_check_depth_cm: 'genus_inferred' },
  });
  expect(careFactRows(s)[0].inferred).toBe(false);
});

test('hardiness zones list when they skip', () => {
  expect(values(minted({ hardiness_zones: [5, 7, 8] }))).toBe('Zones 5, 7, 8');
});

test('a leading unit symbol keeps its case: "pH", never "PH"', () => {
  expect(values(minted({ soil_ph_min: 6, soil_ph_max: 6.5 }))).toBe('pH 6–6.5');
  expect(values(minted({ soil_ph_max: 6 }))).toBe('pH up to 6');
});

test('zero hours of direct sun is said the way a gardener says it', () => {
  expect(values(minted({ direct_sun_hours_max: 0 }))).toBe('No direct sun');
  expect(values(minted({ light_fc_min: 50, direct_sun_hours_max: 0 })))
    .toBe('At least 50 footcandles; no direct sun');
});

// --- fertilize months -------------------------------------------------------

test('a contiguous run is a dash range; one that wraps December still is', () => {
  expect(monthSpan([3, 4, 5, 6, 7, 8, 9, 10])).toBe('Mar–Oct');
  expect(monthSpan([11, 12, 1, 2, 3])).toBe('Nov–Mar');
  expect(monthSpan([1, 12])).toBe('Dec–Jan');
});

test('months with a gap are listed, never bridged into a range', () => {
  expect(monthSpan([3, 9])).toBe('Mar and Sep');
  expect(monthSpan([9, 3, 6])).toBe('Mar, Jun and Sep');
});

test('one month is itself; all twelve is all year; nothing is nothing', () => {
  expect(monthSpan([4])).toBe('Apr');
  expect(monthSpan([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])).toBe('All year');
  expect(monthSpan([])).toBe('');
});

// --- careStatusLine ---------------------------------------------------------

test('a sourced row names the authority that cited it', () => {
  expect(careStatusLine(sourced())).toBe('Care facts cited to NC State Extension');
});

test('several authorities: the first alphabetically, then a count', () => {
  const s = sourced({ care_sources: [
    { authority: 'Royal Horticultural Society', url: RHS, fields: ['soil_base'], inferred: false },
    { authority: 'NC State Extension', url: NCSU, fields: ['light_fc_min'], inferred: false },
    { authority: 'NC State Extension', url: GENUS_PAGE, fields: ['water_regime'], inferred: false },
    { authority: 'Clemson Cooperative Extension', url: CLEMSON, fields: ['day_f_min'], inferred: false },
  ] });
  expect(careStatusLine(s)).toBe('Care facts cited to Clemson Cooperative Extension and 2 more');
});

test('the list endpoint omits the sources, so a sourced row says so generically', () => {
  expect(careStatusLine(sourced({ care_sources: undefined })))
    .toBe('Care facts cited to published sources');
});

test('sourced by status but every page at genus scope is borrowed, not cited', () => {
  const s = sourced({ care_sources: [
    { authority: 'NC State Extension', url: GENUS_PAGE, fields: ['water_regime'], inferred: true },
  ] });
  expect(careStatusLine(s)).toBe('Care facts borrowed from the genus — not confirmed for this species');
  expect(careStatusLine(minted({ ...RESOLVED, care_data_status: 'inferred' })))
    .toBe('Care facts borrowed from the genus — not confirmed for this species');
});

test('a bare minted row admits it has nothing cited', () => {
  expect(careStatusLine(minted())).toBe('No care facts cited for this species yet');
  expect(careStatusLine(minted({ care_data_status: 'none' })))
    .toBe('No care facts cited for this species yet');
});

test('a legacy row the recompute never reached shows no status line at all', () => {
  expect(careStatusLine(minted(LEGACY))).toBeNull();
  expect(careStatusLine(minted({ ...LEGACY, care_data_status: 'none' }))).toBeNull();
});

test('"verified" is not a word this module uses for care data', () => {
  const rows = [
    sourced(), minted(), minted(LEGACY),
    minted({ ...RESOLVED, care_data_status: 'inferred' }),
    sourced({ care_sources: undefined }),
  ];
  for (const s of rows) {
    expect((careStatusLine(s) ?? '').toLowerCase()).not.toContain('verified');
    expect(values(s).toLowerCase()).not.toContain('verified');
  }
  expect(CATALOG_LINE.toLowerCase()).not.toContain('verified');
});

// --- careSourceLabels -------------------------------------------------------

test('a second page from one authority is numbered so it does not read as a duplicate', () => {
  expect(careSourceLabels([
    { authority: 'Clemson Cooperative Extension', url: CLEMSON, fields: ['soil_base'], inferred: false },
    { authority: 'Clemson Cooperative Extension', url: `${CLEMSON}care/`, fields: ['day_f_min'], inferred: false },
    { authority: 'NC State Extension', url: GENUS_PAGE, fields: ['water_regime'], inferred: true },
    { authority: 'NC State Extension', url: NCSU, fields: ['light_fc_min'], inferred: false },
  ])).toEqual([
    'Clemson Cooperative Extension',
    'Clemson Cooperative Extension (page 2)',
    'NC State Extension (genus)',
    'NC State Extension (page 2)',
  ]);
});

// --- legacyStats ------------------------------------------------------------

test('a legacy row shows its four stats in plain words', () => {
  expect(legacyStats(minted(LEGACY))).toEqual([
    { key: 'light', label: 'Light', value: 'bright indirect' },
    { key: 'humidity', label: 'Humidity', value: '40–60%' },
    { key: 'temperature', label: 'Temp', value: '60–85°F' },
    { key: 'soil', label: 'Soil', value: 'well-draining' },
  ]);
});

test('derived humidity is not a stat — nobody measured it', () => {
  const keys = legacyStats(minted({ ...LEGACY, humidity_sourced: false })).map((s) => s.key);
  expect(keys).toEqual(['light', 'temperature', 'soil']);
});

test('a resolved concept hides its legacy stat so a synthetic value never sits beside a cited one', () => {
  const keys = (over: Partial<Species>) => legacyStats(minted({ ...LEGACY, ...over })).map((s) => s.key);
  expect(keys({ light_fc_min: 100 })).toEqual(['humidity', 'temperature', 'soil']);
  expect(keys({ humidity_need: 'average' })).toEqual(['light', 'temperature', 'soil']);
  expect(keys({ night_f_min: 55 })).toEqual(['light', 'humidity', 'soil']);
  expect(keys({ soil_ph_min: 6 })).toEqual(['light', 'humidity', 'temperature']);
  expect(keys(RESOLVED)).toEqual([]);
});

test('a minted row has no legacy stats and no "null–null" bands', () => {
  expect(legacyStats(minted())).toEqual([]);
  expect(legacyStats(minted({ temp_f_min: 60 }))).toEqual([]);
});

// --- waterRegimeSentence ----------------------------------------------------

test('the regime sentence is the wording the advisor uses, or nothing', () => {
  expect(waterRegimeSentence(minted({ water_regime: 'keep_barely_moist' })))
    .toBe('keep the medium barely moist');
  expect(waterRegimeSentence(minted())).toBeNull();
});
