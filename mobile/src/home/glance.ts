// "Your land at a glance" on Home: sun, water and soil as one word each,
// with "est." where the value is an estimate and "Checking" while a slow
// public service has not answered. The full value, its reason and its
// sources live on Your land and in the How we know sheet. Pure.
import { Confidence, SiteField, SiteProfile } from '../types/site';
import { parseSoil, parseSun, parseWater, valueFor } from '../land/readingTiles';
import { t } from '../i18n';

export type GlanceKey = 'sun' | 'water' | 'soil';

export interface GlanceItem {
  key: GlanceKey;
  title: string;
  /** One word, or "Checking" while the value is not known yet. */
  word: string;
  /** Mark the word "est.". */
  estimated: boolean;
  checking: boolean;
  /** The value behind it, to open Your land at. */
  field: SiteField;
  a11y: string;
}

/** Confidences that read as settled: what the owner said or measured. */
const SETTLED: Confidence[] = ['you_told_us', 'you_measured'];

export function isEstimate(c: Confidence): boolean {
  return !SETTLED.includes(c) && c !== 'not_known_yet';
}

export function sunWord(hoursOrCategory: { hours: number | null; category: string | null }): string | null {
  const cat = hoursOrCategory.category
    ?? (hoursOrCategory.hours == null ? null
      : hoursOrCategory.hours >= 6 ? 'full_sun' : hoursOrCategory.hours >= 3 ? 'part_shade' : 'shade');
  return cat ? t(`home.almanac.sunWords.${cat}`, { defaultValue: '' }) || null : null;
}

export function waterWord(cls: string | null): string | null {
  return cls ? t(`home.almanac.waterWords.${cls}`, { defaultValue: '' }) || null : null;
}

/** The soil's one word: by its mix when known (USDA texture triangle,
 *  coarsely), else by the texture's own words. */
export function soilWord(soil: { texture: string | null; mix: { sand: number; silt: number; clay: number } | null }): string | null {
  let k: 'sand' | 'silt' | 'clay' | 'loam' | null = null;
  if (soil.mix) {
    const { sand, silt, clay } = soil.mix;
    k = clay >= 40 ? 'clay' : sand >= 70 ? 'sand' : silt >= 70 ? 'silt' : 'loam';
  } else if (soil.texture) {
    const tx = soil.texture.toLowerCase();
    k = tx.includes('clay') ? 'clay' : tx.includes('sand') ? 'sand' : tx.includes('silt') ? 'silt'
      : tx.includes('loam') ? 'loam' : null;
  }
  return k ? t(`home.almanac.soilWords.${k}`) : null;
}

const ROWS: { key: GlanceKey; fields: SiteField[]; title: () => string }[] = [
  { key: 'sun', fields: ['sun'], title: () => t('home.almanac.glanceSun') },
  { key: 'water', fields: ['water_collects', 'soil_drainage'], title: () => t('home.almanac.glanceWater') },
  { key: 'soil', fields: ['soil_texture'], title: () => t('home.almanac.glanceSoil') },
];

export function landGlance(profile: SiteProfile | null | undefined): GlanceItem[] {
  if (!profile) return [];
  const out: GlanceItem[] = [];
  for (const row of ROWS) {
    const field = row.fields.find((f) => valueFor(profile, f) != null);
    const v = field ? valueFor(profile, field) : undefined;
    if (!v || !field) continue;
    const title = row.title();
    const checking = v.confidence === 'not_known_yet';
    let word: string | null = null;
    if (!checking) {
      if (row.key === 'sun') { const s = parseSun(v.value, v.facts); word = s ? sunWord(s) : null; }
      if (row.key === 'water') word = waterWord(parseWater(v.value));
      if (row.key === 'soil') { const s = parseSoil(v.value); word = s ? soilWord(s) : null; }
    }
    // A value this cannot put in one word keeps its own short text.
    const shown = checking ? t('howWeKnow.checking')
      : word ?? v.display.trim().replace(/[.\s]+$/, '');
    const estimated = !checking && isEstimate(v.confidence);
    out.push({
      key: row.key, title, word: shown, estimated, checking, field,
      a11y: estimated
        ? t('home.almanac.glanceEstA11y', { title, word: shown })
        : t('home.almanac.glanceA11y', { title, word: shown }),
    });
  }
  return out;
}
