import {
  FrostBias, OverridePut, ProfileStatus, SiteField, SiteProfile, SiteValue,
} from '../types/site';

// The Land screen as pure logic: the site profile grouped in a fixed order,
// the corrections the owner can make, and when to ask the server again.

export interface LandSection {
  key: string;
  title: string;
  values: SiteValue[];
}

/** The order the Land screen reads in, and the heading of each group. */
export const LAND_SECTIONS: Array<{ key: string; title: string; fields: SiteField[] }> = [
  { key: 'sun', title: 'Sun', fields: ['sun'] },
  { key: 'soil', title: 'Soil and drainage', fields: ['soil_drainage', 'soil_texture', 'soil_ph', 'disturbed_soil'] },
  { key: 'water', title: 'Where water collects', fields: ['water_collects'] },
  { key: 'slope', title: 'Slope and facing', fields: ['slope', 'facing'] },
  { key: 'flooding', title: 'Flooding', fields: ['flooding'] },
  { key: 'hardiness', title: 'Hardiness zone', fields: ['hardiness_zone'] },
  { key: 'frost', title: 'Typical frost dates', fields: ['frost_dates'] },
  { key: 'land_cover', title: 'Land cover around you', fields: ['land_cover'] },
];

/** Group values into the sections above, in order, leaving out empty ones.
 *  A field the app does not know yet goes last, under "More", so a newer
 *  server's value is still shown. */
export function groupValues(values: readonly SiteValue[]): LandSection[] {
  const out: LandSection[] = [];
  const placed = new Set<SiteValue>();
  for (const s of LAND_SECTIONS) {
    const vs: SiteValue[] = [];
    for (const f of s.fields) {
      for (const v of values) if (v.field === f && !placed.has(v)) { vs.push(v); placed.add(v); }
    }
    if (vs.length > 0) out.push({ key: s.key, title: s.title, values: vs });
  }
  const rest = values.filter((v) => !placed.has(v));
  if (rest.length > 0) out.push({ key: 'more', title: 'More', values: rest });
  return out;
}

/** Which section a field is in, for opening Land at one value. */
export function sectionOf(field: string | undefined): string | null {
  if (!field) return null;
  return LAND_SECTIONS.find((s) => (s.fields as string[]).includes(field))?.key ?? null;
}

/** The whole-lot values: the profile's own, or the whole-lot zone's when the
 *  server put them only there. */
export function wholeLotValues(profile: SiteProfile): SiteValue[] {
  if (profile.values.length > 0) return profile.values;
  return profile.zones.find((z) => z.is_whole_lot)?.values ?? [];
}

/** The owner-drawn zones (not the whole lot), in the server's order. */
export function drawnZones(profile: SiteProfile): SiteProfile['zones'] {
  return profile.zones.filter((z) => !z.is_whole_lot);
}

// ── Corrections ──────────────────────────────────────────────────────────────

/** Whether the owner's correction is what the row is showing. */
export function correctionShowing(v: SiteValue): boolean {
  return v.provenance === 'owner' || v.public != null;
}

/** The public-data reading kept visible beside a correction. */
export function publicLine(v: SiteValue): string | null {
  if (!v.public) return null;
  return `Public data reading: ${v.public.display} (${v.public.confidence_label}).`;
}

/** Which choice, if any, is the owner's current answer. */
export function selectedChoice(v: SiteValue): string | null {
  if (!correctionShowing(v) || v.value == null) return null;
  const value = String(v.value);
  return v.override_choices.some((c) => c.value === value) ? value : null;
}

/** The body for a correction. A number is something measured (a soil
 *  test); a choice is a tap. */
export function overrideBody(v: SiteValue, value: unknown, zoneId?: number | null): OverridePut {
  const body: OverridePut = {
    field: v.field, value, method: v.override_kind === 'number' ? 'measured' : 'tap',
  };
  const zone = zoneId ?? v.zone_id;
  if (zone != null) body.zone_id = zone;
  return body;
}

export type NumberParse = { ok: true; value: number } | { ok: false; message: string };

/** What a number field accepts. Soil acidity (pH) runs 0 to 14; a soil test
 *  reports it to one decimal place, so that is what is kept. */
export function parseNumberOverride(field: SiteField, text: string): NumberParse {
  const cleaned = text.trim().replace(',', '.');
  if (!/^\d+(\.\d+)?$/.test(cleaned)) {
    return { ok: false, message: field === 'soil_ph'
      ? 'Enter the soil acidity (pH) number from your soil test, such as 6.5.'
      : 'Enter a number.' };
  }
  const n = Number(cleaned);
  if (field === 'soil_ph') {
    if (n < 0 || n > 14) return { ok: false, message: 'Soil acidity (pH) is a number from 0 to 14.' };
    return { ok: true, value: Math.round(n * 10) / 10 };
  }
  return { ok: true, value: n };
}

/** The label of the control that puts the public reading back. */
export const USE_ESTIMATE_LABEL = 'Use the public data reading';

// ── Property-level settings ──────────────────────────────────────────────────

export const FROST_BIAS_CHOICES: Array<{ value: FrostBias | null; label: string; a11y: string }> = [
  { value: 'earlier', label: 'Earlier', a11y: 'My yard frosts earlier than the neighbourhood' },
  { value: null, label: 'About the same', a11y: 'My yard frosts about when the neighbourhood does' },
  { value: 'later', label: 'Later', a11y: 'My yard frosts later than the neighbourhood' },
];

/** A property name the server will take: trimmed, not empty, not overlong. */
export function cleanName(text: string): string | null {
  const t = text.trim().replace(/\s+/g, ' ');
  if (!t) return null;
  return t.slice(0, 80);
}

// ── Refreshing while the background step runs ───────────────────────────────

/** While either step runs, ask again this often; otherwise not at all. */
export function refetchEvery(status: ProfileStatus | null | undefined, ms = 5000): number | false {
  if (!status) return false;
  const busy = (s: string) => s === 'pending' || s === 'building';
  return busy(status.fast) || busy(status.background) ? ms : false;
}
