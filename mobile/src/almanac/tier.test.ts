import {
  tierOf, difficultyScore, fingerprint, isGradable, matchesQuery, TIER_LABELS,
} from './tier';
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

// --- rows without legacy values (ADR 0005) ----------------------------------
// A row minted from the claim tranche carries no legacy columns at all, and a
// resolved row carries something better. Nothing here may become NaN, and a
// missing value must score like an unsourced one: it contributes nothing.

test('a minted row with nothing to grade gets a finite score and no grade at all', () => {
  const bare = sp({
    light_need: null, humidity_pct_min: null, humidity_pct_max: null,
    temp_f_min: null, temp_f_max: null, soil_type: null,
  });
  expect(Number.isNaN(difficultyScore(bare))).toBe(false);
  // Not "beginner": a score of 0 from no inputs is the absence of evidence,
  // and three quarters of the catalog — deadly plants included — was badged
  // easy on it. Unknown is not a pass.
  expect(isGradable(bare)).toBe(false);
  expect(tierOf(bare)).toBeNull();
});

test('any one gradable input is enough for a grade', () => {
  const bare = {
    light_need: null, humidity_pct_min: null, humidity_pct_max: null,
    temp_f_min: null, temp_f_max: null,
  };
  expect(tierOf(sp({ ...bare, humidity_need: 'average' }))).toBe('beginner');
  expect(tierOf(sp({ ...bare, humidity_need: 'high', day_f_min: 68, day_f_max: 78 })))
    .toBe('fussy');
  expect(tierOf(sp({ ...bare, light_need: 'direct' }))).toBe('intermediate');
  // Half a band is not a band, and derived humidity is not a fact.
  expect(tierOf(sp({ ...bare, day_f_max: 80 }))).toBeNull();
  expect(tierOf(sp({ ...bare, humidity_pct_min: 40, humidity_pct_max: 60, humidity_sourced: false })))
    .toBeNull();
});

test('a missing humidity band scores exactly like a derived one', () => {
  const derived = sp({
    humidity_pct_min: 70, humidity_pct_max: 85, humidity_sourced: false,
    temp_f_min: 65, temp_f_max: 80, light_need: 'bright_indirect',
  });
  const missing = sp({
    humidity_pct_min: null, humidity_pct_max: null,
    temp_f_min: 65, temp_f_max: 80, light_need: 'bright_indirect',
  });
  expect(difficultyScore(missing)).toBe(difficultyScore(derived));
});

test('a resolved humidity need is preferred over the legacy band', () => {
  // The legacy numbers alone would score nothing; the cited category says
  // it wants a humidifier.
  const legacyOnly = sp({ humidity_pct_min: 30, humidity_pct_max: 60 });
  const cited = sp({ humidity_pct_min: 30, humidity_pct_max: 60, humidity_need: 'high' });
  expect(difficultyScore(legacyOnly)).toBe(-1);
  expect(difficultyScore(cited)).toBe(1);
  expect(difficultyScore(sp({ humidity_need: 'average' }))).toBe(difficultyScore(legacyOnly));
});

test('a resolved day band is preferred over the legacy temperature band', () => {
  const wideLegacy = sp({ temp_f_min: 50, temp_f_max: 90 });
  const narrowDays = sp({ temp_f_min: 50, temp_f_max: 90, day_f_min: 68, day_f_max: 78 });
  expect(difficultyScore(narrowDays)).toBe(difficultyScore(wideLegacy) + 2);
});

test('light contributes nothing when there is no light value', () => {
  expect(difficultyScore(sp({ light_need: null })))
    .toBe(difficultyScore(sp({ light_need: 'medium' })));
});

test('the fingerprint shows a dash for every missing stat', () => {
  const f = fingerprint(sp({
    light_need: null, humidity_pct_min: null, humidity_pct_max: null,
  }));
  expect(f.light).toBe('☀ —');
  expect(f.humidity).toBe('💦 —');
  expect(f.water).toBe('💧 —');
});

test('the fingerprint shows a resolved humidity need as its word', () => {
  expect(fingerprint(sp({ humidity_need: 'high' })).humidity).toBe('💦 high');
});

// The list endpoint sends no schedules, so a water glyph read only from them
// was a dash on every Almanac card while a third of the catalog had a cited
// regime on the very row being drawn.
test('the water glyph reads the cited regime the list row carries', () => {
  expect(fingerprint(sp({ water_regime: 'keep_moist' })).water).toBe('💧 evenly moist');
  expect(fingerprint(sp({ water_regime: 'dry_thoroughly_between' })).water)
    .toBe('💧 dries out between');
  // The regime is the species-level fact; it wins over a schedule's cadence.
  const both = sp({
    water_regime: 'dry_surface_between',
    care_schedules: [{
      id: 1, species_id: 1, care_type: 'water', interval_days_min: 7, interval_days_max: 10, notes: '',
    }],
  });
  expect(fingerprint(both).water).toBe('💧 top dries between');
});

test('the light glyph prefers the resolved columns over the legacy word', () => {
  expect(fingerprint(sp({ direct_sun_hours_max: 0 })).light).toBe('☀ no direct sun');
  expect(fingerprint(sp({ direct_sun_hours_max: 4 })).light).toBe('☀ up to 4h direct sun');
  expect(fingerprint(sp({ light_fc_min: 150 })).light).toBe('☀ 150+ footcandles');
  expect(fingerprint(sp({ outdoor_sun_exposure: ['full_sun', 'part_sun'] })).light)
    .toBe('☀ full sun, part sun');
  // Legacy only when nothing resolved exists — "low" is the fixture's word.
  expect(fingerprint(sp()).light).toBe('◐ low');
  expect(fingerprint(sp({ light_need: null })).light).toBe('☀ —');
});

test('no glyph ever shows a column token', () => {
  const f = fingerprint(sp({
    water_regime: 'keep_barely_moist', outdoor_sun_exposure: ['part_shade'],
    humidity_need: 'average',
  }));
  expect(`${f.water} ${f.light} ${f.humidity}`).not.toMatch(/[a-z]_[a-z]/);
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
