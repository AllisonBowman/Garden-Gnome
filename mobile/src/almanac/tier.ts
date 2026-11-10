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
//
// Two kinds of row hold no legacy envelope at all: one minted from the claim
// tranche (ADR 0005), and one whose concept the claims resolved into a better
// column. A resolved value is preferred where one exists; a missing value
// contributes nothing, exactly as a derived one does — never NaN, and never a
// number nobody stated.
import { Species, WaterRegime } from '../types';
import { outdoorSunPhrase } from '../care/facts';

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
  // watering category (imported rows) — not facts, so not scorable, and a
  // missing band is no more scorable than a derived one. Those rows are
  // scored on light and temperature with heavier weights, so the scale stays
  // comparable instead of every import drifting to "beginner". An absent
  // flag (older API) is curated-era data and counts as sourced.
  const legacyHumidity = s.humidity_sourced !== false
    && s.humidity_pct_min != null && s.humidity_pct_max != null;
  const humidityScorable = s.humidity_need != null || legacyHumidity;

  if (s.humidity_need != null) {
    // The cited category replaces the legacy band: "high" is the plant that
    // needs a humidifier, and the category carries no band to be narrow.
    if (s.humidity_need === 'high') score += 2;
  } else if (legacyHumidity) {
    const min = s.humidity_pct_min as number;
    if (min >= HIGH_HUMIDITY) score += 2;    // needs a humidifier
    else if (min >= 50) score += 1;

    const humidityBand = (s.humidity_pct_max as number) - min;
    if (humidityBand > 0 && humidityBand < NARROW_HUMIDITY_BAND) score += 1;
  }

  // The resolved day band replaces the legacy one; a half-stated band is not
  // a band and scores nothing rather than falling back to a synthetic one.
  const [low, high] = s.day_f_min != null || s.day_f_max != null
    ? [s.day_f_min, s.day_f_max]
    : [s.temp_f_min, s.temp_f_max];
  const tempWeight = humidityScorable ? [2, 1] : [3, 2];
  if (low != null && high != null) {
    const tempBand = high - low;
    if (tempBand > 0 && tempBand < NARROW_TEMP_BAND) score += tempWeight[0];
    else if (tempBand > 0 && tempBand < NARROW_TEMP_BAND + 10) score += tempWeight[1];
  }

  // Direct sun indoors is genuinely hard to supply; low light is forgiving.
  // No light value at all says nothing either way.
  if (s.light_need === 'direct') score += humidityScorable ? 1 : 2;
  if (s.light_need === 'low') score -= 1;

  return score;
}

/** Whether the record holds anything a difficulty grade could rest on: a
 *  humidity need or a sourced humidity band, a two-ended temperature band,
 *  or a light need. The score starts at 0 and only demands add to it, so a
 *  species with none of these used to score 0 and land in Beginner — three
 *  quarters of the catalog, poison hemlock and belladonna among them, graded
 *  easy on no evidence at all. */
export function isGradable(s: Species): boolean {
  const legacyHumidity = s.humidity_sourced !== false
    && s.humidity_pct_min != null && s.humidity_pct_max != null;
  const [low, high] = s.day_f_min != null || s.day_f_max != null
    ? [s.day_f_min, s.day_f_max]
    : [s.temp_f_min, s.temp_f_max];
  return s.humidity_need != null || legacyHumidity
    || (low != null && high != null)
    || s.light_need != null;
}

/** The difficulty grade, or null when there is nothing to grade on. Null is
 *  "not graded", never "Beginner": unknown is not a pass. */
export function tierOf(s: Species): Tier | null {
  if (!isGradable(s)) return null;
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

/** The watering regime in a glyph's worth of words. */
const REGIME_GLYPH: Record<WaterRegime, string> = {
  keep_moist: '💧 evenly moist',
  keep_barely_moist: '💧 barely moist',
  dry_surface_between: '💧 top dries between',
  dry_thoroughly_between: '💧 dries out between',
};

/** Light from the resolved columns first — hours of direct sun, then the
 *  footcandle floor, then the outdoor exposure — and the legacy word only
 *  where none of them exists, as care/facts.ts does. */
function lightGlyph(s: Species): string {
  if (s.direct_sun_hours_max != null) {
    return s.direct_sun_hours_max === 0
      ? '☀ no direct sun'
      : `☀ up to ${s.direct_sun_hours_max}h direct sun`;
  }
  if (s.light_fc_min != null) return `☀ ${s.light_fc_min}+ footcandles`;
  const outdoor = outdoorSunPhrase(s.outdoor_sun_exposure);
  if (outdoor) return `☀ ${outdoor}`;
  if (s.light_need) return LIGHT_GLYPH[s.light_need] ?? `☀ ${s.light_need.replace(/_/g, ' ')}`;
  return '☀ —';
}

/**
 * The three-glyph summary from the design's "CARE FINGERPRINT" — enough to
 * compare two species at a glance without opening either.
 *
 * Read from what the list row carries. The list endpoint sends no schedules,
 * so a fingerprint built on them was a dash on every card while a third of
 * the catalog has a cited watering regime; the resolved columns come first,
 * a schedule where a detail record supplies one, and a dash only when the
 * record truly has nothing.
 */
export function fingerprint(s: Species): Fingerprint {
  const water = s.care_schedules?.find((c) => c.care_type === 'water');
  const legacyHumidity = s.humidity_sourced !== false
    && s.humidity_pct_min != null && s.humidity_pct_max != null;
  return {
    water: s.water_regime && REGIME_GLYPH[s.water_regime]
      ? REGIME_GLYPH[s.water_regime]
      : water
        ? `💧 every ${water.interval_days_min}–${water.interval_days_max}d`
        : '💧 —',
    light: lightGlyph(s),
    // The cited category first; the legacy band only when its numbers came
    // from a source. Derived humidity (imports) shows the same honest dash
    // as missing data — because that's what it is.
    humidity: s.humidity_need
      ? `💦 ${s.humidity_need}`
      : legacyHumidity
        ? `💦 ${s.humidity_pct_min}–${s.humidity_pct_max}%`
        : '💦 —',
  };
}

/** Search lives with the catalog's other list rules, shared with the Species
 *  tab; re-exported so the Almanac reads it from one place. */
export { matchesQuery } from '../care/catalog';
