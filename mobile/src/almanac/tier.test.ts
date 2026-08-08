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

// --- fabricated humidity (plan 1.6) -----------------------------------------
// Imported rows derive their humidity percentages from a watering category and
// arrive with humidity_sourced=false. Numbers nobody measured must not decide
// a tier or appear in a fingerprint.

test('derived humidity is not scored; real signals are re-weighted', () => {
  const asIfMeasured = sp({
    humidity_pct_min: 70, humidity_pct_max: 85,
    temp_f_min: 65, temp_f_max: 80,
    light_need: 'bright_indirect',
  });
  const honest = { ...asIfMeasured, humidity_sourced: false } as Species;
  // measured: humidity (+3) + narrow-ish temp (+2) → fussy
  expect(tierOf(asIfMeasured)).toBe('fussy');
  // derived: humidity contributes nothing; temp carries fallback weight (+3)
  expect(difficultyScore(honest)).toBe(3);
  expect(tierOf(honest)).toBe('intermediate');
});

test('an absent flag is curated-era data and scores as sourced', () => {
  expect(difficultyScore(sp({ humidity_sourced: undefined })))
    .toBe(difficultyScore(sp()));
});

test('direct sun weighs heavier when humidity is unknowable', () => {
  const wideAndSunny = {
    humidity_pct_min: 40, humidity_pct_max: 70,
    temp_f_min: 50, temp_f_max: 90,
    light_need: 'direct' as const,
  };
  expect(difficultyScore(sp(wideAndSunny))).toBe(1);
  expect(difficultyScore(sp({ ...wideAndSunny, humidity_sourced: false }))).toBe(2);
});

test('the fingerprint shows a dash for derived humidity — that is what missing data looks like', () => {
  expect(fingerprint(sp({ humidity_sourced: false })).humidity).toBe('💦 —');
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
