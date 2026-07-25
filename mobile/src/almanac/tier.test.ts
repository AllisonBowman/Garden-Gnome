import { tierOf, difficultyScore, fingerprint, matchesQuery, TIER_LABELS } from './tier';
import { Species } from '../types';

function sp(over: Partial<Species> = {}): Species {
  return {
    id: 1,
    common_name: 'Snake Plant',
    scientific_name: 'Dracaena trifasciata',
    light_need: 'low',
    humidity_pct_min: 30,
    humidity_pct_max: 60,
    temp_f_min: 55,
    temp_f_max: 90,
    soil_type: 'cactus mix',
    toxic_to_pets: false,
    care_notes: '',
    ...over,
  } as Species;
}

// --- tiers ------------------------------------------------------------------

test('a tolerant, low-light plant is beginner', () => {
  // wide temp band, ordinary humidity, forgiving light
  expect(tierOf(sp())).toBe('beginner');
});

test('high humidity plus a narrow temperature band is fussy', () => {
  const calathea = sp({
    common_name: 'Calathea',
    humidity_pct_min: 70, humidity_pct_max: 85,
    temp_f_min: 65, temp_f_max: 80,
    light_need: 'bright_indirect',
  });
  expect(tierOf(calathea)).toBe('fussy');
});

test('a moderate plant lands in between', () => {
  const monstera = sp({
    humidity_pct_min: 50, humidity_pct_max: 70,
    temp_f_min: 60, temp_f_max: 85,
    light_need: 'bright_indirect',
  });
  expect(tierOf(monstera)).toBe('intermediate');
});

test('narrow tolerance drives difficulty, not any single value', () => {
  const wide = sp({ temp_f_min: 50, temp_f_max: 90 });
  const narrow = sp({ temp_f_min: 68, temp_f_max: 78 });
  expect(difficultyScore(narrow)).toBeGreaterThan(difficultyScore(wide));
});

test('low light is forgiving; direct sun indoors is not', () => {
  const low = sp({ light_need: 'low' });
  const direct = sp({ light_need: 'direct' });
  expect(difficultyScore(direct)).toBeGreaterThan(difficultyScore(low));
});

test('every tier has a display label', () => {
  for (const t of ['beginner', 'intermediate', 'fussy'] as const) {
    expect(TIER_LABELS[t]).toBeTruthy();
  }
});

// --- fingerprint ------------------------------------------------------------

test('fingerprint summarises water, light and humidity', () => {
  const f = fingerprint(sp({
    care_schedules: [{
      id: 1, species_id: 1, care_type: 'water',
      interval_days_min: 7, interval_days_max: 10, notes: '',
    }],
  }));
  expect(f.water).toContain('7–10d');
  expect(f.light).toContain('low');
  expect(f.humidity).toContain('30–60%');
});

test('missing watering schedule degrades to a dash, not a crash', () => {
  expect(fingerprint(sp()).water).toBe('💧 —');
});

// --- search -----------------------------------------------------------------

test('search matches common and scientific names, case-insensitively', () => {
  const s = sp({ common_name: 'Monstera', scientific_name: 'Monstera deliciosa' });
  expect(matchesQuery(s, 'monst')).toBe(true);
  expect(matchesQuery(s, 'DELICIOSA')).toBe(true);
  expect(matchesQuery(s, 'fern')).toBe(false);
});

test('an empty query matches everything', () => {
  expect(matchesQuery(sp(), '   ')).toBe(true);
});
