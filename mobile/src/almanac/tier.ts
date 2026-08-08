// Difficulty tier and care fingerprint for the Species Almanac.
//
// The design calls for Beginner / Intermediate / Fussy filters, but "tier" is
// not a field in the catalog and adding one would mean a human grading ~1,940
// species. It is derivable instead: what makes a houseplant hard is a NARROW
// tolerance, not any single value. A plant that accepts a wide temperature
// band and ordinary room humidity forgives a beginner's mistakes; one that
// wants 70% humidity in a ten-degree window punishes them.
//
// Derived rather than stored so it stays honest as the catalog is corrected —
// when a record's care envelope is fixed, its tier follows automatically.
import { Species } from '../types';

export type Tier = 'beginner' | 'intermediate' | 'fussy';

export const TIER_LABELS: Record<Tier, string> = {
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  fussy: 'Fussy',
};

/** Humidity above this is hard to hold in a normal room without help. */
const HIGH_HUMIDITY = 60;
/** A temperature band narrower than this leaves little margin for error. */
const NARROW_TEMP_BAND = 20;
/** A humidity band this narrow means the plant notices ordinary drift. */
const NARROW_HUMIDITY_BAND = 20;

/**
 * A difficulty score: how many demands the plant makes. Exposed for testing
 * and so the thresholds stay legible rather than buried in a chain of ifs.
 */
export function difficultyScore(s: Species): number {
  let score = 0;

  // humidity_sourced === false means the percentages were derived from a
  // watering category (imported rows) — not facts, so not scorable. Those
  // rows are scored on light and temperature with heavier weights, so the
  // scale stays comparable instead of every import drifting to "beginner".
  // An absent flag (older API) is curated-era data and counts as sourced.
  const humiditySourced = s.humidity_sourced !== false;

  if (humiditySourced) {
    if (s.humidity_pct_min >= HIGH_HUMIDITY) score += 2;    // needs a humidifier
    else if (s.humidity_pct_min >= 50) score += 1;

    const humidityBand = s.humidity_pct_max - s.humidity_pct_min;
    if (humidityBand > 0 && humidityBand < NARROW_HUMIDITY_BAND) score += 1;
  }

  const tempBand = s.temp_f_max - s.temp_f_min;
  const tempWeight = humiditySourced ? [2, 1] : [3, 2];
  if (tempBand > 0 && tempBand < NARROW_TEMP_BAND) score += tempWeight[0];
  else if (tempBand > 0 && tempBand < NARROW_TEMP_BAND + 10) score += tempWeight[1];

  // Direct sun indoors is genuinely hard to supply; low light is forgiving.
  if (s.light_need === 'direct') score += humiditySourced ? 1 : 2;
  if (s.light_need === 'low') score -= 1;

  return score;
}

export function tierOf(s: Species): Tier {
  const score = difficultyScore(s);
  if (score >= 4) return 'fussy';
  if (score >= 2) return 'intermediate';
  return 'beginner';
}

export interface Fingerprint {
  water: string;
  light: string;
  humidity: string;
}

const LIGHT_GLYPH: Record<string, string> = {
  low: '◐ low',
  medium: '◑ medium',
  bright_indirect: '☀ bright indirect',
  direct: '☀☀ direct sun',
};

/**
 * The three-glyph summary from the design's "CARE FINGERPRINT" — enough to
 * compare two species at a glance without opening either.
 */
export function fingerprint(s: Species): Fingerprint {
  const water = s.care_schedules?.find((c) => c.care_type === 'water');
  return {
    water: water
      ? `💧 every ${water.interval_days_min}–${water.interval_days_max}d`
      : '💧 —',
    light: LIGHT_GLYPH[s.light_need] ?? `☀ ${s.light_need}`,
    // Derived humidity (imports) shows the same honest dash as missing data —
    // because that's what it is.
    humidity: s.humidity_sourced !== false
      ? `💦 ${s.humidity_pct_min}–${s.humidity_pct_max}%`
      : '💦 —',
  };
}

/** Case-insensitive match across both names, so "monstera" and "deliciosa"
 *  both find the same plant. */
export function matchesQuery(s: Species, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return (
    s.common_name.toLowerCase().includes(q) ||
    s.scientific_name.toLowerCase().includes(q)
  );
}
