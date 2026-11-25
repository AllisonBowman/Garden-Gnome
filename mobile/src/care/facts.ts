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
import { t } from '../i18n';
import { formatTemp, fromFahrenheit, unitSymbol } from '../units/temperature';

export type CareFactKey =
  | 'water' | 'light' | 'humidity' | 'temperature' | 'soil'
  | 'fertilize' | 'outdoor_sun' | 'cold' | 'size' | 'place' | 'eating';

export interface CareFactRow {
  key: CareFactKey;
  label: string;
  value: string;
  /** True when any field this row drew on was borrowed from the genus. */
  inferred: boolean;
  /** A row that warns rather than describes — shown in the warning colour.
   *  Only the edibility note today: "some parts are eaten, others are
   *  poisonous" is read as a caution or it is read wrong. */
  caution?: boolean;
}

export type LegacyStatKey = 'light' | 'humidity' | 'temperature' | 'soil';

export interface LegacyStat {
  key: LegacyStatKey;
  label: string;
  value: string;
}

/** The status line's phrasing, exported so screens and tests share one copy. */
export const BORROWED_LINE = t('care.facts.borrowedLine');
/** The pill on anything one species borrowed from its genus (ADR 0002). One
 *  copy, because the same fact is labelled on a care row and on a fit
 *  finding, and a reader should not have to learn two words for it. */
export const INFERRED_PILL = t('care.facts.inferredPill');
export const NONE_LINE = t('care.facts.noneLine');
/** The caption over the legacy stats: they are catalog values no claim
 *  backs, and under a "cited to …" line they would read as equally cited. */
export const CATALOG_LINE = t('care.facts.catalogLine');

// Wording for the categorical columns. A token is a column value, not a fact
// anyone can act on, so none of these leak through as-is.
// Read from the translation, keyed by the column's own token; null for a
// token this build does not know.
const WATER_REGIMES: Record<WaterRegime, true> = {
  keep_moist: true, keep_barely_moist: true, dry_surface_between: true, dry_thoroughly_between: true,
};
const HUMIDITIES: Record<HumidityNeed, true> = { low: true, average: true, high: true };
const SOIL_BASES: Record<SoilBase, true> = {
  standard_potting: true, chunky_aroid: true, cactus_succulent: true, ericaceous: true,
  orchid_bark: true, african_violet: true, semi_hydro: true, garden_bed: true,
};
const DRAINAGES: Record<SoilDrainage, true> = { fast: true, moderate: true, moisture_retentive: true };
const STRENGTHS: Record<FertilizeStrength, true> = { full: true, half: true, quarter: true };
const SUNS: Record<OutdoorSunExposure, true> = {
  full_sun: true, part_sun: true, part_shade: true, full_shade: true,
};
const WATER_REGIME_TEXT = (v: WaterRegime): string | null =>
  (v in WATER_REGIMES ? t(`care.facts.waterRegime.${v}`) : null);
const HUMIDITY_TEXT = (v: HumidityNeed): string | null =>
  (v in HUMIDITIES ? t(`care.facts.humidity.${v}`) : null);
const SOIL_BASE_TEXT = (v: SoilBase): string | null =>
  (v in SOIL_BASES ? t(`care.facts.soilBase.${v}`) : null);
const DRAINAGE_TEXT = (v: SoilDrainage): string | null =>
  (v in DRAINAGES ? t(`care.facts.drainage.${v}`) : null);
const STRENGTH_TEXT = (v: FertilizeStrength): string | null =>
  (v in STRENGTHS ? t(`care.facts.strength.${v}`) : null);
const SUN_TEXT = (v: OutdoorSunExposure): string | null =>
  (v in SUNS ? t(`care.facts.sun.${v}`) : null);
const MONTHS = t('care.facts.monthsShort').split(',');

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
  'fertilize_strength', 'outdoor_sun_exposure', 'outdoor_temp_min_f',
  'is_houseplant', 'is_edible', 'attracts_pollinators',
  'mature_height_in_min', 'mature_height_in_max',
  'mature_spread_in_min', 'mature_spread_in_max',
  'climbs',
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

/** A length as a gardener says it: inches under two feet, and from there
 *  feet to one decimal, a half rounded up. The fit engine's `_ft` to the
 *  operation — not Math.round on v / 12, since Python's round takes a half
 *  to even and this must land on the same tenth — so the "7 ft" of headroom
 *  in a sentence is the "7 ft" printed for the 84 in somebody measured. The
 *  fixtures in facts.test.ts are shared with the engine's tests. */
export const lengthSaid = (v: number) => (
  v < 24
    ? t('care.facts.inches', { n: num(v) })
    : t('care.facts.feet', { n: num(Math.floor((v * 10) / 12 + 0.5) / 10) }));

/** A mature-size range. Null at both ends means nobody measured it, which is
 *  not the same as a plant with no size — so the row simply does not appear. */
/** A climber's height is reach given support (0020), so it reads as how far
 *  it climbs rather than how tall it stands. */
function climb(lo: number | null | undefined, hi: number | null | undefined): string | null {
  if (lo == null && hi == null) return null;
  if (lo != null && hi != null) {
    return t('care.facts.climbsRange', { low: lengthSaid(lo), high: lengthSaid(hi) });
  }
  return lo != null
    ? t('care.facts.climbsFrom', { low: lengthSaid(lo) })
    : t('care.facts.climbsUpTo', { high: lengthSaid(hi!) });
}

function span(
  lo: number | null | undefined, hi: number | null | undefined, word: 'tall' | 'wide',
): string | null {
  if (lo == null && hi == null) return null;
  if (lo != null && hi != null) {
    return t(`care.facts.${word}Range`, { low: lengthSaid(lo), high: lengthSaid(hi) });
  }
  return lo != null
    ? t(`care.facts.${word}From`, { low: lengthSaid(lo) })
    : t(`care.facts.${word}UpTo`, { high: lengthSaid(hi!) });
}

/** 3 -> "3", 2.5 -> "2.5": depths, hours and degrees read as counts. */
const num = (v: number) => String(v);
/** A Fahrenheit value in the person's unit, whole degrees. */
const cv = <T extends number | null | undefined>(v: T): T => (v == null ? v : Math.round(fromFahrenheit(v)) as T);

/** A soil depth in centimetres, said in inches to the nearest half inch:
 *  "1 inch", "1.5 inches", "half an inch" for anything shallower. The same
 *  rule as the server's care_facts.depth_said, so the card and the advice
 *  agree. */
export function depthSaid(cm: number): string {
  const half = Math.floor((cm / 2.54) * 2 + 0.5) / 2;
  if (half <= 0.5) return t('care.facts.halfInch');
  return t('care.facts.depthInches', { count: half });
}

/** Sentence case for a row, leaving a leading unit symbol alone: "pH 6–6.5"
 *  is a symbol, and "PH" reads as a typo. Exported so a screen capitalizes
 *  in code: a `textTransform: 'capitalize'` lowercases the rest of every
 *  word on iOS, and "60–85°F" reached the App Store screenshots as
 *  "60–85°f". */
export const capitalize = (text: string) => (
  text.startsWith('pH') ? text : text.charAt(0).toUpperCase() + text.slice(1)
);

/** "65–80°F", or the half that exists: "from 55°F" / "up to 80°F". */
function band(low: number | null | undefined, high: number | null | undefined, unit: string) {
  if (low != null && high != null) return `${num(low)}–${num(high)}${unit}`;
  if (low != null) return t('care.facts.bandFrom', { low: num(low), unit });
  return t('care.facts.bandUpTo', { high: num(high as number), unit });
}

/** Whether any of `fields` was borrowed from the genus (ADR 0002). */
export function isGenusInferred(species: Species, ...fields: string[]): boolean {
  const provenance = species.care_provenance ?? {};
  return fields.some((f) => provenance[f] === 'genus_inferred');
}

/** The outdoor exposure as a caretaker would say it — "part sun, part
 *  shade" — or null when nothing resolved. */
export function outdoorSunPhrase(values: OutdoorSunExposure[] | null | undefined): string | null {
  if (!values?.length) return null;
  return values.map((v) => SUN_TEXT(v) ?? v.replace(/_/g, ' ')).join(', ');
}

/** The regime as a caretaker would say it; null when nothing resolved. */
export function waterRegimeSentence(species: Species): string | null {
  return species.water_regime ? WATER_REGIME_TEXT(species.water_regime) : null;
}

/** "Mar–Oct" when the months run without a gap — wrapping through December
 *  counts, "Nov–Mar" — otherwise listed, "Mar and Sep". A range is a claim
 *  that every month between is included, so a gap is never bridged. */
export function monthSpan(months: number[]): string {
  const ordered = [...new Set(months.filter((m) => m >= 1 && m <= 12))].sort((a, b) => a - b);
  const names = ordered.map((m) => MONTHS[m - 1]);
  if (names.length <= 1) return names.join('');
  if (names.length === 12) return t('care.facts.allYear');
  // Around the circle of the year a contiguous run has exactly one gap that
  // is not a single month; the span starts just after it and ends on it.
  const gaps = ordered.map((m, i) => (((ordered[(i + 1) % ordered.length] - m) % 12) + 12) % 12);
  const breaks = gaps.map((g, i) => (g === 1 ? -1 : i)).filter((i) => i >= 0);
  if (breaks.length === 1) {
    const i = breaks[0];
    return `${names[(i + 1) % names.length]}–${names[i]}`;
  }
  return t('care.facts.listAnd', { list: names.slice(0, -1).join(', '), last: names[names.length - 1] });
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

/** The server's edibility sentence, when there is one. Non-null means the
 *  species is eaten only with conditions, and the bare "grown to eat" would
 *  leave those conditions out — so the note replaces it. */
export function edibilityNote(species: Species): string | null {
  const note = species.edibility_note?.trim();
  return note ? note : null;
}

/** Whether "grown to eat" may stand on its own: edible, with no conditions
 *  on record. Edibility is shown with its conditions or not at all. */
export function plainlyEdible(species: Species): boolean {
  return species.is_edible === true && edibilityNote(species) == null;
}

const CONCEPTS: {
  key: CareFactKey; label: string; join: string; caution?: boolean;
  read: (s: Species) => Concept;
}[] = [
  // The regime and the check depth — never the dry-down target, which is a
  // verbatim passage and stays on the server (ADR 0003).
  { key: 'water', label: t('care.facts.labels.water'), join: '; ', read: (s) => concept([
    [waterRegimeSentence(s), ['water_regime']],
    [s.water_check_depth_cm != null
      ? t('care.facts.checkDepth', { depth: depthSaid(s.water_check_depth_cm) }) : null,
      ['water_check_depth_cm']],
  ]) },
  { key: 'light', label: t('care.facts.labels.light'), join: '; ', read: (s) => concept([
    [s.light_fc_min != null ? t('care.facts.lightMin', { n: num(s.light_fc_min) }) : null, ['light_fc_min']],
    [s.light_fc_good != null ? t('care.facts.lightGood', { n: num(s.light_fc_good) }) : null, ['light_fc_good']],
    // "Up to 0 hours" is true and not how anyone says it.
    [s.direct_sun_hours_max == null ? null
      : s.direct_sun_hours_max === 0 ? t('care.facts.noDirectSun')
        : t('care.facts.directSunMax', { count: s.direct_sun_hours_max }), ['direct_sun_hours_max']],
  ]) },
  { key: 'humidity', label: t('care.facts.labels.humidity'), join: '; ', read: (s) => concept([
    [s.humidity_need ? HUMIDITY_TEXT(s.humidity_need) : null, ['humidity_need']],
  ]) },
  { key: 'temperature', label: t('care.facts.labels.temperature'), join: '; ', read: (s) => concept([
    [s.day_f_min != null || s.day_f_max != null
      ? t('care.facts.days', { band: band(cv(s.day_f_min), cv(s.day_f_max), unitSymbol()) }) : null, ['day_f_min', 'day_f_max']],
    [s.night_f_min != null || s.night_f_max != null
      ? t('care.facts.nights', { band: band(cv(s.night_f_min), cv(s.night_f_max), unitSymbol()) }) : null, ['night_f_min', 'night_f_max']],
    [s.chill_damage_f != null ? t('care.facts.chillDamage', { n: formatTemp(s.chill_damage_f) }) : null, ['chill_damage_f']],
  ]) },
  { key: 'soil', label: t('care.facts.labels.soil'), join: '; ', read: (s) => concept([
    [s.soil_base ? SOIL_BASE_TEXT(s.soil_base) : null, ['soil_base']],
    [s.soil_drainage ? DRAINAGE_TEXT(s.soil_drainage) : null, ['soil_drainage']],
    [s.soil_ph_min != null || s.soil_ph_max != null
      ? t('care.facts.ph', { band: band(s.soil_ph_min, s.soil_ph_max, '') }) : null, ['soil_ph_min', 'soil_ph_max']],
  ]) },
  { key: 'fertilize', label: t('care.facts.labels.fertilize'), join: '; ', read: (s) => concept([
    [monthSpan(s.fertilize_active_months ?? []) || null, ['fertilize_active_months']],
    [s.fertilize_interval_days != null
      ? t('care.facts.everyDays', { count: s.fertilize_interval_days }) : null,
      ['fertilize_interval_days']],
    [s.fertilize_strength ? STRENGTH_TEXT(s.fertilize_strength) : null, ['fertilize_strength']],
  ]) },
  { key: 'outdoor_sun', label: t('care.facts.labels.outdoorSun'), join: ', ', read: (s) => concept([
    [outdoorSunPhrase(s.outdoor_sun_exposure), ['outdoor_sun_exposure']],
  ]) },
  // A survival floor from USDA PLANTS — not the temperature row's damage
  // point, which is where harm begins in cultivation. The two can sit tens
  // of degrees apart on one plant, so they are never folded into one row.
  { key: 'cold', label: t('care.facts.labels.cold'), join: '', read: (s) => concept([
    [s.outdoor_temp_min_f != null ? t('care.facts.survives', { n: formatTemp(s.outdoor_temp_min_f) }) : null,
      ['outdoor_temp_min_f']],
  ]) },
  // Size answers a different question from the care rows above: not "what
  // does it need from me" but "does it belong in this space".
  { key: 'size', label: t('care.facts.labels.size'), join: ', ', read: (s) => concept([
    s.climbs
      ? [climb(s.mature_height_in_min, s.mature_height_in_max),
        ['mature_height_in_min', 'mature_height_in_max', 'climbs']]
      : [span(s.mature_height_in_min, s.mature_height_in_max, 'tall'),
        ['mature_height_in_min', 'mature_height_in_max']],
    [span(s.mature_spread_in_min, s.mature_spread_in_max, 'wide'),
      ['mature_spread_in_min', 'mature_spread_in_max']],
  ]) },
  { key: 'place', label: t('care.facts.labels.place'), join: '; ', read: (s) => concept([
    [s.is_houseplant == null ? null
      : (s.is_houseplant ? t('care.facts.indoors') : t('care.facts.outdoors')),
      ['is_houseplant']],
    [s.climbs ? t('care.facts.climber') : null, ['climbs']],
    [plainlyEdible(s) ? t('care.facts.edible') : null, ['is_edible']],
    [s.attracts_pollinators ? t('care.facts.pollinators') : null, ['attracts_pollinators']],
  ]) },
  // Its own row, in the warning colour, never folded into "Where it lives":
  // the note is a whole sentence about which parts are safe to eat, and
  // squeezed between "grown indoors" and "feeds pollinators" it would read
  // as one more pleasant trait.
  { key: 'eating', label: t('care.facts.labels.eating'), join: '', caution: true, read: (s) => concept([
    [edibilityNote(s), ['is_edible']],
  ]) },
];

/** One row per resolved concept the row can back, in reading order. A row
 *  is marked inferred when any field it actually drew on came from the
 *  genus; a flag on a field the row did not use does not taint it. */
export function careFactRows(species: Species): CareFactRow[] {
  const rows: CareFactRow[] = [];
  for (const { key, label, join, caution, read } of CONCEPTS) {
    const { parts, used } = read(species);
    if (parts.length === 0) continue;
    rows.push({
      key, label,
      value: capitalize(parts.join(join)),
      inferred: isGenusInferred(species, ...used),
      ...(caution ? { caution: true } : {}),
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
    if (names.length === 1) return t('care.facts.citedOne', { name: names[0] });
    if (names.length > 1) return t('care.facts.citedMore', { name: names[0], n: names.length - 1 });
    if (status === 'inferred' || (sources && sources.length > 0)) return BORROWED_LINE;
    // The list endpoint omits the sources; a sourced row is still sourced.
    return t('care.facts.citedPublished');
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
    const notes = [
      source.inferred ? t('care.facts.sourceGenus') : '',
      nth > 1 ? t('care.facts.sourcePage', { n: nth }) : '',
    ].filter(Boolean);
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
    stats.push({ key: 'light', label: t('care.facts.labels.light'), value: capitalize(s.light_need.replace(/_/g, ' ')) });
  }
  // Derived humidity (imported rows) is not a fact: nobody measured it.
  if (s.humidity_pct_min != null && s.humidity_pct_max != null
      && s.humidity_sourced !== false && !hasAny(s, RESOLVED_FOR.humidity)) {
    stats.push({ key: 'humidity', label: t('care.facts.labels.humidity'), value: `${s.humidity_pct_min}–${s.humidity_pct_max}%` });
  }
  if (s.temp_f_min != null && s.temp_f_max != null && !hasAny(s, RESOLVED_FOR.temperature)) {
    stats.push({ key: 'temperature', label: t('care.facts.labels.temp'), value: `${cv(s.temp_f_min)}–${cv(s.temp_f_max)}${unitSymbol()}` });
  }
  if (s.soil_type && !hasAny(s, RESOLVED_FOR.soil)) {
    stats.push({ key: 'soil', label: t('care.facts.labels.soil'), value: s.soil_type });
  }
  return stats;
}
