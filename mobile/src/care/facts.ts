// The care facts a screen may show, built once from what a species row holds.
//
// Until now every screen read the six legacy columns as if every row had
// them. A row minted from the claim tranche has none (ADR 0005); a row the
// tranche resolved holds something better in the resolved columns; and a
// value borrowed from the genus has to say so wherever it appears (ADR 0002).
// So the wording lives here, not in the screens: a resolved concept replaces
// its legacy stat so a synthetic number never sits beside a cited one, a
// column token like `chunky_aroid` never reaches the page, nothing absent is
// invented, and the status line uses the words CONTEXT.md allows — "cited",
// "borrowed", never "verified". The advisor's fact block on the server says
// the same things in the same words; a caretaker and the model should not
// be told two different stories.
import {
  CareSource, FertilizeStrength, HumidityNeed, OutdoorSunExposure, SoilBase,
  SoilDrainage, Species, WaterRegime,
} from '../types';

export type CareFactKey =
  | 'water' | 'light' | 'humidity' | 'temperature' | 'soil'
  | 'fertilize' | 'outdoor_sun' | 'hardiness';

export interface CareFactRow {
  key: CareFactKey;
  label: string;
  value: string;
  /** True when any field this row drew on was borrowed from the genus. */
  inferred: boolean;
}

export type LegacyStatKey = 'light' | 'humidity' | 'temperature' | 'soil';

export interface LegacyStat {
  key: LegacyStatKey;
  label: string;
  value: string;
}

/** The status line's phrasing, exported so screens and tests share one copy. */
export const BORROWED_LINE = 'Care facts borrowed from the genus — not confirmed for this species';
export const NONE_LINE = 'No care facts cited for this species yet';
/** The caption over the legacy stats: they are catalog values no claim
 *  backs, and under a "cited to …" line they would read as equally cited. */
export const CATALOG_LINE = 'From the catalog — not yet cited';

// Wording for the categorical columns. A token is a column value, not a fact
// anyone can act on, so none of these leak through as-is.
const WATER_REGIME_TEXT: Record<WaterRegime, string> = {
  keep_moist: 'keep the medium evenly moist',
  keep_barely_moist: 'keep the medium barely moist',
  dry_surface_between: 'let the surface dry between waterings',
  dry_thoroughly_between: 'let the medium dry thoroughly between waterings',
};
const HUMIDITY_TEXT: Record<HumidityNeed, string> = {
  low: 'low; tolerates dry air',
  average: 'average room humidity',
  high: 'high; wants humid air',
};
const SOIL_BASE_TEXT: Record<SoilBase, string> = {
  standard_potting: 'standard potting mix',
  chunky_aroid: 'chunky aroid mix',
  cactus_succulent: 'cactus and succulent mix',
  ericaceous: 'ericaceous (acid) mix',
  orchid_bark: 'orchid bark',
  african_violet: 'African violet mix',
  semi_hydro: 'semi-hydro (inert medium)',
  garden_bed: 'garden bed soil',
};
const DRAINAGE_TEXT: Record<SoilDrainage, string> = {
  fast: 'fast-draining',
  moderate: 'moderately draining',
  moisture_retentive: 'moisture-retentive',
};
const STRENGTH_TEXT: Record<FertilizeStrength, string> = {
  full: 'full strength', half: 'half strength', quarter: 'quarter strength',
};
const SUN_TEXT: Record<OutdoorSunExposure, string> = {
  full_sun: 'full sun', part_sun: 'part sun',
  part_shade: 'part shade', full_shade: 'full shade',
};
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** The concepts a resolved column replaces. A legacy stat shows only while
 *  every resolved column for its concept is absent. */
const RESOLVED_FOR: Record<LegacyStatKey, (keyof Species)[]> = {
  light: ['light_fc_min', 'light_fc_good', 'direct_sun_hours_max'],
  humidity: ['humidity_need'],
  temperature: ['day_f_min', 'day_f_max', 'night_f_min', 'night_f_max', 'chill_damage_f'],
  soil: ['soil_base', 'soil_drainage', 'soil_ph_min', 'soil_ph_max'],
};
const RESOLVED_COLUMNS: (keyof Species)[] = [
  ...RESOLVED_FOR.light, ...RESOLVED_FOR.humidity, ...RESOLVED_FOR.temperature,
  ...RESOLVED_FOR.soil,
  'water_regime', 'water_check_depth_cm', 'water_growing_days_est',
  'water_dormant_days_est', 'fertilize_active_months', 'fertilize_interval_days',
  'fertilize_strength', 'outdoor_sun_exposure', 'hardiness_zones',
];
const LEGACY_COLUMNS: (keyof Species)[] = [
  'light_need', 'humidity_pct_min', 'humidity_pct_max', 'temp_f_min',
  'temp_f_max', 'soil_type',
];

const has = (s: Species, field: keyof Species) => {
  const v = s[field];
  return v !== null && v !== undefined && v !== '';
};
const hasAny = (s: Species, fields: (keyof Species)[]) => fields.some((f) => has(s, f));

/** 3 -> "3", 2.5 -> "2.5": depths, hours and degrees read as counts. */
const num = (v: number) => String(v);

/** Sentence case for a row, leaving a leading unit symbol alone: "pH 6–6.5"
 *  is a symbol, and "PH" reads as a typo. */
const capitalize = (text: string) => (
  text.startsWith('pH') ? text : text.charAt(0).toUpperCase() + text.slice(1)
);

/** "65–80°F", or the half that exists: "from 55°F" / "up to 80°F". */
function band(low: number | null | undefined, high: number | null | undefined, unit: string) {
  if (low != null && high != null) return `${num(low)}–${num(high)}${unit}`;
  if (low != null) return `from ${num(low)}${unit}`;
  return `up to ${num(high as number)}${unit}`;
}

/** Whether any of `fields` was borrowed from the genus (ADR 0002). */
export function isGenusInferred(species: Species, ...fields: string[]): boolean {
  const provenance = species.care_provenance ?? {};
  return fields.some((f) => provenance[f] === 'genus_inferred');
}

/** The regime as a caretaker would say it; null when nothing resolved. */
export function waterRegimeSentence(species: Species): string | null {
  return species.water_regime ? WATER_REGIME_TEXT[species.water_regime] ?? null : null;
}

/** "Mar–Oct" when the months run without a gap — wrapping through December
 *  counts, "Nov–Mar" — otherwise listed, "Mar and Sep". A range is a claim
 *  that every month between is included, so a gap is never bridged. */
export function monthSpan(months: number[]): string {
  const ordered = [...new Set(months.filter((m) => m >= 1 && m <= 12))].sort((a, b) => a - b);
  const names = ordered.map((m) => MONTHS[m - 1]);
  if (names.length <= 1) return names.join('');
  if (names.length === 12) return 'All year';
  // Around the circle of the year a contiguous run has exactly one gap that
  // is not a single month; the span starts just after it and ends on it.
  const gaps = ordered.map((m, i) => (((ordered[(i + 1) % ordered.length] - m) % 12) + 12) % 12);
  const breaks = gaps.map((g, i) => (g === 1 ? -1 : i)).filter((i) => i >= 0);
  if (breaks.length === 1) {
    const i = breaks[0];
    return `${names[(i + 1) % names.length]}–${names[i]}`;
  }
  return `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`;
}

/** "7–10" for a run without a gap, else "5, 7, 8". */
function zoneSpan(zones: number[]): string {
  const ordered = [...new Set(zones)].sort((a, b) => a - b);
  const contiguous = ordered.every((z, i) => i === 0 || z === ordered[i - 1] + 1);
  if (ordered.length >= 2 && contiguous) return `${ordered[0]}–${ordered[ordered.length - 1]}`;
  return ordered.join(', ');
}

/** One concept's parts and the fields they were read from. */
interface Concept { parts: string[]; used: string[] }

function concept(pairs: [string | null, string[]][]): Concept {
  const parts: string[] = [];
  const used: string[] = [];
  for (const [text, fields] of pairs) {
    if (text) { parts.push(text); used.push(...fields); }
  }
  return { parts, used };
}

const CONCEPTS: { key: CareFactKey; label: string; join: string; read: (s: Species) => Concept }[] = [
  // The regime and the check depth — never the dry-down target, which is a
  // verbatim passage and stays on the server (ADR 0003).
  { key: 'water', label: 'Watering', join: '; ', read: (s) => concept([
    [waterRegimeSentence(s), ['water_regime']],
    [s.water_check_depth_cm != null ? `check ${num(s.water_check_depth_cm)} cm down` : null,
      ['water_check_depth_cm']],
  ]) },
  { key: 'light', label: 'Light', join: '; ', read: (s) => concept([
    [s.light_fc_min != null ? `at least ${num(s.light_fc_min)} footcandles` : null, ['light_fc_min']],
    [s.light_fc_good != null ? `${num(s.light_fc_good)} footcandles is comfortable` : null, ['light_fc_good']],
    // "Up to 0 hours" is true and not how anyone says it.
    [s.direct_sun_hours_max == null ? null
      : s.direct_sun_hours_max === 0 ? 'no direct sun'
        : `up to ${num(s.direct_sun_hours_max)} hours of direct sun`, ['direct_sun_hours_max']],
  ]) },
  { key: 'humidity', label: 'Humidity', join: '; ', read: (s) => concept([
    [s.humidity_need ? HUMIDITY_TEXT[s.humidity_need] ?? null : null, ['humidity_need']],
  ]) },
  { key: 'temperature', label: 'Temperature', join: '; ', read: (s) => concept([
    [s.day_f_min != null || s.day_f_max != null
      ? `days ${band(s.day_f_min, s.day_f_max, '°F')}` : null, ['day_f_min', 'day_f_max']],
    [s.night_f_min != null || s.night_f_max != null
      ? `nights ${band(s.night_f_min, s.night_f_max, '°F')}` : null, ['night_f_min', 'night_f_max']],
    [s.chill_damage_f != null ? `cold damage below ${num(s.chill_damage_f)}°F` : null, ['chill_damage_f']],
  ]) },
  { key: 'soil', label: 'Soil', join: '; ', read: (s) => concept([
    [s.soil_base ? SOIL_BASE_TEXT[s.soil_base] ?? null : null, ['soil_base']],
    [s.soil_drainage ? DRAINAGE_TEXT[s.soil_drainage] ?? null : null, ['soil_drainage']],
    [s.soil_ph_min != null || s.soil_ph_max != null
      ? `pH ${band(s.soil_ph_min, s.soil_ph_max, '')}` : null, ['soil_ph_min', 'soil_ph_max']],
  ]) },
  { key: 'fertilize', label: 'Fertilize', join: '; ', read: (s) => concept([
    [monthSpan(s.fertilize_active_months ?? []) || null, ['fertilize_active_months']],
    [s.fertilize_interval_days != null ? `every ${num(s.fertilize_interval_days)} days` : null,
      ['fertilize_interval_days']],
    [s.fertilize_strength ? STRENGTH_TEXT[s.fertilize_strength] ?? null : null, ['fertilize_strength']],
  ]) },
  { key: 'outdoor_sun', label: 'Outdoor sun', join: ', ', read: (s) => concept([
    [s.outdoor_sun_exposure?.length
      ? s.outdoor_sun_exposure.map((v) => SUN_TEXT[v] ?? v.replace(/_/g, ' ')).join(', ')
      : null, ['outdoor_sun_exposure']],
  ]) },
  { key: 'hardiness', label: 'Hardiness', join: '', read: (s) => concept([
    [s.hardiness_zones?.length
      ? `${s.hardiness_zones.length === 1 ? 'zone' : 'zones'} ${zoneSpan(s.hardiness_zones)}`
      : null, ['hardiness_zones']],
  ]) },
];

/** One row per resolved concept the row can back, in reading order. A row
 *  is marked inferred when any field it actually drew on came from the
 *  genus; a flag on a field the row did not use does not taint it. */
export function careFactRows(species: Species): CareFactRow[] {
  const rows: CareFactRow[] = [];
  for (const { key, label, join, read } of CONCEPTS) {
    const { parts, used } = read(species);
    if (parts.length === 0) continue;
    rows.push({
      key, label,
      value: capitalize(parts.join(join)),
      inferred: isGenusInferred(species, ...used),
    });
  }
  return rows;
}

/** How well-backed the facts are, in one line — or null for a legacy row
 *  the recompute has not reached, which has nothing to announce. */
export function careStatusLine(species: Species): string | null {
  const status = species.care_data_status;
  if (status === 'sourced' || status === 'inferred') {
    const sources = species.care_sources;
    const names = [...new Set(
      (sources ?? []).filter((c) => !c.inferred && c.authority).map((c) => c.authority),
    )].sort();
    if (names.length === 1) return `Care facts cited to ${names[0]}`;
    if (names.length > 1) return `Care facts cited to ${names[0]} and ${names.length - 1} more`;
    if (status === 'inferred' || (sources && sources.length > 0)) return BORROWED_LINE;
    // The list endpoint omits the sources; a sourced row is still sourced.
    return 'Care facts cited to published sources';
  }
  if (hasAny(species, RESOLVED_COLUMNS) || hasAny(species, LEGACY_COLUMNS)) return null;
  return NONE_LINE;
}

/** One label per source row: the authority's name, "genus" when every field
 *  from that page was borrowed (ADR 0002), and a page number from the second
 *  page of one authority on — two identical rows would read as a duplicate
 *  when the pages differ. Still a name and a link, never more (ADR 0003). */
export function careSourceLabels(sources: CareSource[]): string[] {
  const seen = new Map<string, number>();
  return sources.map((source) => {
    const nth = (seen.get(source.authority) ?? 0) + 1;
    seen.set(source.authority, nth);
    const notes = [source.inferred ? 'genus' : '', nth > 1 ? `page ${nth}` : ''].filter(Boolean);
    return notes.length ? `${source.authority} (${notes.join(', ')})` : source.authority;
  });
}

/** The legacy stats that exist and whose concept nothing resolved replaces.
 *  The legacy values are the synthetic ones; showing one beside a cited fact
 *  would lend it the citation's credibility. */
export function legacyStats(species: Species): LegacyStat[] {
  const stats: LegacyStat[] = [];
  const s = species;
  if (s.light_need && !hasAny(s, RESOLVED_FOR.light)) {
    stats.push({ key: 'light', label: 'Light', value: s.light_need.replace(/_/g, ' ') });
  }
  // Derived humidity (imported rows) is not a fact: nobody measured it.
  if (s.humidity_pct_min != null && s.humidity_pct_max != null
      && s.humidity_sourced !== false && !hasAny(s, RESOLVED_FOR.humidity)) {
    stats.push({ key: 'humidity', label: 'Humidity', value: `${s.humidity_pct_min}–${s.humidity_pct_max}%` });
  }
  if (s.temp_f_min != null && s.temp_f_max != null && !hasAny(s, RESOLVED_FOR.temperature)) {
    stats.push({ key: 'temperature', label: 'Temp', value: `${s.temp_f_min}–${s.temp_f_max}°F` });
  }
  if (s.soil_type && !hasAny(s, RESOLVED_FOR.soil)) {
    stats.push({ key: 'soil', label: 'Soil', value: s.soil_type });
  }
  return stats;
}
