import { ConfidenceLabel, Explained, SiteField, SiteProfile, SiteValue, VitalCard } from '../types/site';
import { LandLine, landLines } from '../home/land';
import { t } from '../i18n';
import { localConfidenceLabel } from '../components/explainedText';
import { formatTemp, unitSpoken } from '../units/temperature';

// The reading tiles on Home and Your land (map and visuals spec sections 1
// and 4.2): sun hours, hardiness zone, where water collects and topsoil, each
// a small graphic with its confidence label. Built on `landLines`, so a tile
// shows exactly the value the text row used to. The parsers are tolerant: a
// value whose shape is not what we expect still makes a tile, with its
// display text and no graphic. Pure: no React Native imports.

export type ReadingTileKey = LandLine['key'];

/** Sand, silt and clay as percentages that add up to 100. */
export interface SoilMix { sand: number; silt: number; clay: number }

export interface ReadingTile {
  key: ReadingTileKey;
  title: string;
  /** The big text: "About 5.2 hours", "Zone 7b", "Drains freely", "Silt loam".
   *  Never starts with the title and never ends with a full stop. */
  valueText: string;
  /** One line under it, or '' when there is nothing more to say. */
  detail: string;
  /** A gauge with captions at both ends (sun: hours of a 12 hour day;
   *  hardiness: coldest to warmest zone), or null to draw no gauge. */
  gauge: TileGauge | null;
  /** Labelled steps with the current one filled (where water collects), or
   *  null to draw none. */
  steps: TileSteps | null;
  /** The topsoil's sand, silt and clay, when known (drawn as one bar). */
  mix: SoilMix | null;
  confidenceLabel: ConfidenceLabel | string;
  explained: Explained;
  /** The site value behind the tile, to open Your land at. */
  field?: SiteField;
  /** What a screen reader hears for the tile. */
  a11y: string;
}

/** A bar from `startLabel` to `endLabel` with a knob at `fraction` (0 to 1). */
export interface TileGauge { fraction: number; startLabel: string; endLabel: string }

/** Labelled steps in order, with `current` (an index into `labels`) filled. */
export interface TileSteps { labels: string[]; current: number }

/** The sun gauge's full width: hours of direct sun in a day. */
export const SUN_GAUGE_HOURS = 12;

export const SUN_GAUGE_LABELS = { start: '0', end: t('land.tiles.gaugeHours', { hours: SUN_GAUGE_HOURS }) } as const;
export const HARDINESS_GAUGE_LABELS = { start: t('land.tiles.zoneColdest'), end: t('land.tiles.zoneWarmest') } as const;

const SUN_WORDS: Record<string, string> = {
  full_sun: t('land.tiles.fullSun'), part_shade: t('land.tiles.partShade'), shade: t('land.tiles.shade'),
};

// Where water collects: every class the server's drainage outcome can send
// (app/services/site/drainage.py `outcome`, value `{class}`), driest first.
// `step` is the short caption under the steps graphic.
export const WATER_CLASSES = ['drains_freely', 'slow_to_drain', 'gathers_after_rain', 'often_wet'] as const;

const WATER_WORDS: Record<string, { text: string; step: string }> = {
  drains_freely: { text: t('land.tiles.drainsFreely'), step: t('land.tiles.drainsFreely') },
  slow_to_drain: { text: t('land.tiles.slowToDrain'), step: t('land.tiles.slowToDrain') },
  gathers_after_rain: { text: t('land.tiles.gathersAfterRainText'), step: t('land.tiles.gathersAfterRain') },
  often_wet: { text: t('land.tiles.oftenWet'), step: t('land.tiles.oftenWet') },
};

function num(v: unknown): number | null {
  if (typeof v === 'number') return Number.isFinite(v) ? v : null;
  if (typeof v === 'string' && v.trim() !== '' && Number.isFinite(Number(v))) return Number(v);
  return null;
}

function obj(v: unknown): Record<string, unknown> | null {
  return v != null && typeof v === 'object' && !Array.isArray(v) ? v as Record<string, unknown> : null;
}

function str(v: unknown): string | null {
  return typeof v === 'string' && v.trim() ? v.trim() : null;
}

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

const round1 = (x: number) => Math.round(x * 10) / 10;

const fmtF = (x: number) => formatTemp(x);

function tileTitle(key: keyof typeof SERVER_TITLES): string {
  switch (key) {
    case 'sun': return t('land.tiles.sun');
    case 'hardiness': return t('land.tiles.hardiness');
    case 'drainage': return t('land.tiles.drainage');
    case 'water': return t('land.tiles.water');
    default: return t('land.tiles.topsoil');
  }
}

function sentenceCase(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// ── Parsers (exported for tests) ─────────────────────────────────────────────

/**
 * `{hours, category}`; also a bare number of hours or a category word. Over
 * the API the value is the bare category and the hours come in the value's
 * `facts` (`{hours}`), which are read first. An owner's own answer has no
 * facts, so it gives the category alone.
 */
export function parseSun(v: unknown, facts?: unknown): { hours: number | null; category: string | null } | null {
  const o = obj(v);
  const f = obj(facts);
  const hours = (f ? num(f.hours) : null) ?? (o ? num(o.hours) : num(v));
  const rawCat = o ? str(o.category) : (typeof v === 'string' && num(v) == null ? str(v) : null);
  const category = rawCat && SUN_WORDS[rawCat] ? rawCat : null;
  if ((hours == null || hours < 0 || hours > 24) && category == null) return null;
  return { hours: hours != null && hours >= 0 && hours <= 24 ? hours : null, category };
}

const ZONE_RE = /^\s*(?:zone\s*)?(\d{1,2})\s*([ab])?\s*$/i;

/** `{zone, low_f, high_f}`; also a bare zone such as "7b". */
export function parseHardiness(v: unknown): { zone: string; number: number; half: 'a' | 'b' | null; low_f: number | null; high_f: number | null } | null {
  const o = obj(v);
  const raw = o ? (str(o.zone) ?? (num(o.zone) != null ? String(num(o.zone)) : null)) : (str(v) ?? (num(v) != null ? String(num(v)) : null));
  if (!raw) return null;
  const m = ZONE_RE.exec(raw);
  if (!m) return null;
  const n = Number(m[1]);
  if (n < 1 || n > 13) return null;
  const half = m[2] ? (m[2].toLowerCase() as 'a' | 'b') : null;
  return { zone: `${n}${half ?? ''}`, number: n, half, low_f: o ? num(o.low_f) : null, high_f: o ? num(o.high_f) : null };
}

/** `{class}` from where-water-collects; also the bare class word. */
export function parseWater(v: unknown): string | null {
  const o = obj(v);
  const c = o ? str(o.class) : str(v);
  return c && WATER_WORDS[c] ? c : null;
}

/** `{texture, family, sand_percent, clay_percent}`; also a bare texture. */
export function parseSoil(v: unknown): { texture: string | null; mix: SoilMix | null } | null {
  const o = obj(v);
  const texture = o ? str(o.texture) : str(v);
  let mix: SoilMix | null = null;
  if (o) {
    const sand = num(o.sand_percent);
    const clay = num(o.clay_percent);
    if (sand != null && clay != null && sand >= 0 && clay >= 0 && sand + clay <= 100) {
      mix = { sand: round1(sand), clay: round1(clay), silt: round1(100 - sand - clay) };
    }
  }
  if (!texture && !mix) return null;
  return { texture, mix };
}

// ── Tiles ────────────────────────────────────────────────────────────────────

export function valueFor(profile: SiteProfile | null | undefined, field: SiteField | undefined): SiteValue | undefined {
  if (!profile || !field) return undefined;
  return profile.values.find((v) => v.field === field && v.zone_id == null)
    ?? profile.values.find((v) => v.field === field);
}

// The server writes its display text in English ("Topsoil: not known yet."),
// so a title is taken off the front in English as well as in the app's
// language. Never shown.
const SERVER_TITLES: Record<string, string> = {
  sun: 'Sun', hardiness: 'Hardiness zone', drainage: 'Drainage', water: 'Where water collects', topsoil: 'Topsoil',
};

function stripTitles(titleKey: string, title: string, text: string): string {
  const own = tileValueText(title, text);
  const server = SERVER_TITLES[titleKey];
  return server && server !== title ? tileValueText(server, own) : own;
}

interface Shown {
  titleKey: string;
  title: string; valueText: string; detail: string;
  gauge: TileGauge | null; steps: TileSteps | null; mix: SoilMix | null;
}

/**
 * A tile's big text from any text: without the tile's own title at the
 * start ("Topsoil: not known yet." reads "Not known yet"), in sentence case,
 * with no full stop at the end. Exported for tests.
 */
export function tileValueText(title: string, text: string): string {
  let s = text.trim();
  const lowerTitle = title.trim().toLowerCase();
  // Take the title off as many times as it leads ("Sun: sun ..." is unlikely,
  // but the rule is that the value never starts with it).
  while (lowerTitle && s.toLowerCase().startsWith(lowerTitle)) {
    const rest = s.slice(lowerTitle.length);
    // Only a whole word: "Sunny" does not start with the title "Sun".
    if (rest && !/^[\s:,.;-]/.test(rest)) break;
    s = rest.replace(/^[\s:,.;-]+/, '');
  }
  s = s.replace(/[.\s]+$/, '');
  return s ? sentenceCase(s) : '';
}

function shown(line: LandLine, value: unknown, facts: unknown): Shown {
  const display = line.explained.display;
  const none = { gauge: null, steps: null, mix: null };
  const plain = (titleKey: keyof typeof SERVER_TITLES): Shown => ({
    titleKey, title: tileTitle(titleKey), valueText: display, detail: '', ...none,
  });
  switch (line.key) {
    case 'sun': {
      const sun = parseSun(value, facts);
      if (!sun) return plain('sun');
      const cat = sun.category ? SUN_WORDS[sun.category] : '';
      // An owner's answer (or any value with no hours): the category words alone.
      if (sun.hours == null) return { titleKey: 'sun', title: tileTitle('sun'), valueText: cat, detail: '', ...none };
      // To the half hour, as the server's own sentence says it.
      const h = Math.round(sun.hours * 2) / 2;
      return {
        titleKey: 'sun',
        title: tileTitle('sun'),
        valueText: t('land.tiles.aboutHours', { count: h }),
        detail: cat || t('land.tiles.directSun'),
        gauge: {
          fraction: clamp01(sun.hours / SUN_GAUGE_HOURS),
          startLabel: SUN_GAUGE_LABELS.start, endLabel: SUN_GAUGE_LABELS.end,
        },
        steps: null,
        mix: null,
      };
    }
    case 'hardiness': {
      // A value that is not a zone; the display may still name one
      // ("Hardiness zone 7b" from a vitals card).
      const z = parseHardiness(value) ?? parseHardiness(tileValueText('Hardiness zone', display));
      if (!z) return plain('hardiness');
      const range = z.low_f != null && z.high_f != null
        ? t('land.tiles.coldestRange', { low: fmtF(z.low_f), high: fmtF(z.high_f) })
        : z.low_f != null ? t('land.tiles.coldestDown', { low: fmtF(z.low_f) }) : '';
      // 26 half zones, 1a to 13b; a zone with no half sits in its middle.
      const step = (z.number - 1) * 2 + (z.half === 'b' ? 1 : 0) + (z.half ? 0.5 : 1);
      return {
        titleKey: 'hardiness', title: tileTitle('hardiness'), valueText: t('land.tiles.zone', { zone: z.zone }), detail: range,
        gauge: {
          fraction: clamp01(step / 26),
          startLabel: HARDINESS_GAUGE_LABELS.start, endLabel: HARDINESS_GAUGE_LABELS.end,
        },
        steps: null,
        mix: null,
      };
    }
    case 'drainage': {
      const titleKey = line.field === 'soil_drainage' ? 'drainage' : 'water';
      const c = parseWater(value);
      if (!c) return plain(titleKey);
      return {
        titleKey, title: tileTitle(titleKey), valueText: WATER_WORDS[c].text, detail: '', gauge: null,
        steps: { labels: WATER_CLASSES.map((k) => WATER_WORDS[k].step), current: WATER_CLASSES.indexOf(c as typeof WATER_CLASSES[number]) },
        mix: null,
      };
    }
    case 'soil': {
      const s = parseSoil(value);
      if (!s) return plain('topsoil');
      const detail = s.mix
        ? t('land.tiles.mix', { sand: Math.round(s.mix.sand), silt: Math.round(s.mix.silt), clay: Math.round(s.mix.clay) })
        : '';
      return { titleKey: 'topsoil', title: tileTitle('topsoil'), valueText: s.texture ? sentenceCase(s.texture.toLowerCase()) : display, detail, gauge: null, steps: null, mix: s.mix };
    }
  }
}

/**
 * The tiles, in `landLines` order (sun, topsoil, water, hardiness zone),
 * one per line it returns. Values come from the profile's whole-lot reading
 * when there is one; before the profile arrives the vitals cards stand in,
 * with their display text and no graphic.
 */
export function readingTiles(profile: SiteProfile | null | undefined, cards: VitalCard[]): ReadingTile[] {
  return landLines(profile, cards).map((line) => {
    const sv = valueFor(profile, line.field);
    const s = shown(line, sv?.value, sv?.facts);
    const valueText = stripTitles(s.titleKey, s.title, s.valueText) || stripTitles(s.titleKey, s.title, line.explained.display)
      || line.explained.display.trim().replace(/[.\s]+$/, '');
    const label = line.explained.confidence_label;
    const a11y = [
      `${s.title}: ${valueText}`,
      s.detail,
      t('land.tiles.confidenceA11y', { label: localConfidenceLabel(label, line.explained.confidence) }),
    ].filter(Boolean).map((p) => p.replace(/[.\s]+$/, '')).join('. ') + '.';
    return {
      key: line.key,
      title: s.title,
      valueText,
      detail: s.detail,
      gauge: s.gauge,
      steps: s.steps,
      mix: s.mix,
      confidenceLabel: label,
      explained: line.explained,
      field: line.field,
      a11y: a11y.replace(/ ?°[FC]/g, ` ${unitSpoken()}`).replace(/%/g, t('land.tiles.percent')),
    };
  });
}
