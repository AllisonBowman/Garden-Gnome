import { Explained, SiteField, SiteProfile, VitalCard, VitalCardKey } from '../types/site';
import { t } from '../i18n';

// "Your land" on Home: one line each for sun, soil, drainage and hardiness
// zone, each with its confidence, taken from the whole-lot values of the site
// profile. When the profile has not arrived, the vitals cards for sun, soil
// and drainage stand in (they carry the same Explained shape).

export interface LandLine {
  key: 'sun' | 'soil' | 'drainage' | 'hardiness';
  title: string;
  explained: Explained;
  /** The site value to open Land at, when it came from the profile. */
  field?: SiteField;
}

const ROWS: Array<{
  key: LandLine['key'];
  title: string;
  fields: SiteField[];
  card?: VitalCardKey;
}> = [
  { key: 'sun', title: t('home.land.sun'), fields: ['sun'], card: 'sun' },
  { key: 'soil', title: t('home.land.soil'), fields: ['soil_texture'], card: 'soil' },
  { key: 'drainage', title: t('home.land.drainage'), fields: ['water_collects', 'soil_drainage'], card: 'drainage' },
  { key: 'hardiness', title: t('home.land.hardiness'), fields: ['hardiness_zone'] },
];

function explainedOf(v: Explained): Explained {
  return {
    display: v.display,
    confidence: v.confidence,
    confidence_label: v.confidence_label,
    reason: v.reason,
    sources: v.sources,
    provenance: v.provenance,
  };
}

export function landLines(
  profile: SiteProfile | null | undefined, cards: VitalCard[],
): LandLine[] {
  const out: LandLine[] = [];
  for (const row of ROWS) {
    // Fields in their order of preference; the whole-lot value before a zone's.
    const values = profile?.values ?? [];
    let value: (typeof values)[number] | undefined;
    for (const field of row.fields) {
      value = values.find((v) => v.field === field && v.zone_id == null)
        ?? values.find((v) => v.field === field);
      if (value) break;
    }
    if (value) {
      out.push({ key: row.key, title: row.title, explained: explainedOf(value), field: value.field });
      continue;
    }
    const card = row.card ? cards.find((c) => c.key === row.card) : undefined;
    if (card?.explained) {
      out.push({ key: row.key, title: row.title, explained: explainedOf(card.explained) });
    }
  }
  return out;
}
