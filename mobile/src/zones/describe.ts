import {
  Box, Imagery, LeafHabit, OverrideChoice, OverridePut, SiteField, SiteValue, VegetationType,
  Zone, ZoneCreate, ZonePatch,
} from '../types/site';

// Describing a zone by taps: what grows there, leaf habit where it applies,
// optional sun and soil corrections, and the words the zone map shows. Pure.

export const VEGETATION_CHOICES: { value: VegetationType; label: string; hint: string }[] = [
  { value: 'garden_bed', label: 'Garden bed', hint: 'Flowers, vegetables or other planted beds' },
  { value: 'grass', label: 'Lawn or grass', hint: 'Mown grass or a meadow' },
  { value: 'shrub', label: 'Shrubs or bushes', hint: 'Woody plants shorter than a tree' },
  { value: 'tree', label: 'Trees', hint: 'One tree or a group of trees' },
  { value: 'bare_hardscape', label: 'Paving, gravel or bare ground', hint: 'Patio, path, driveway or bare soil' },
];

export const VEGETATION_WORDS: Record<VegetationType, string> = Object.fromEntries(
  VEGETATION_CHOICES.map((c) => [c.value, c.label]),
) as Record<VegetationType, string>;

export const LEAF_HABIT_CHOICES: { value: LeafHabit; label: string }[] = [
  { value: 'drops_leaves', label: 'Loses its leaves in fall' },
  { value: 'evergreen', label: 'Evergreen' },
  { value: 'mixed', label: 'Some of each' },
];

/** Leaf habit is asked only for trees and shrubs. */
export function leafHabitApplies(v: VegetationType | null | undefined): boolean {
  return v === 'tree' || v === 'shrub';
}

/** The sun choices, used when the server sends none for a zone. */
export const DEFAULT_SUN_CHOICES: OverrideChoice[] = [
  { value: 'full_sun', label: 'Full sun (6 hours or more)' },
  { value: 'part_shade', label: 'Part shade (3 to 6 hours)' },
  { value: 'shade', label: 'Shade (under 3 hours)' },
];

/** The fields a zone can be corrected on here, in the order asked. Soil is
 *  offered through what the server says can be corrected. */
export const CORRECTION_FIELDS: SiteField[] = ['sun', 'water_collects', 'soil_texture'];

export const CORRECTION_TITLES: Partial<Record<SiteField, string>> = {
  sun: 'Sun here (optional)',
  water_collects: 'Water after rain (optional)',
  soil_texture: 'Soil here (optional)',
};

export interface CorrectionQuestion {
  field: SiteField;
  title: string;
  choices: OverrideChoice[];
}

/**
 * The correction questions for a zone: from the zone's own values when it
 * has them, else from the whole lot's, keeping only fields the server says
 * can be corrected by a choice. Sun is always asked, with the standard three
 * choices if the server gave none.
 */
export function correctionQuestions(
  zoneValues: SiteValue[] | null | undefined, lotValues: SiteValue[] | null | undefined,
): CorrectionQuestion[] {
  const pick = (field: SiteField) => (zoneValues ?? []).find((v) => v.field === field)
    ?? (lotValues ?? []).find((v) => v.field === field);
  const out: CorrectionQuestion[] = [];
  for (const field of CORRECTION_FIELDS) {
    const v = pick(field);
    const usable = v && v.can_override && v.override_kind === 'choice' && v.override_choices.length > 0;
    if (usable) {
      out.push({ field, title: CORRECTION_TITLES[field] ?? v.title, choices: v.override_choices });
    } else if (field === 'sun') {
      out.push({ field, title: CORRECTION_TITLES.sun!, choices: DEFAULT_SUN_CHOICES });
    }
  }
  return out;
}

export interface ZoneDraft {
  name: string;
  vegetation: VegetationType | null;
  leafHabit: LeafHabit | null;
  /** Owner corrections picked, by field. */
  corrections: Partial<Record<SiteField, string>>;
}

export function emptyDraft(): ZoneDraft {
  return { name: '', vegetation: null, leafHabit: null, corrections: {} };
}

export function draftFromZone(z: Zone): ZoneDraft {
  return { name: z.name, vegetation: z.vegetation_type ?? null, leafHabit: z.leaf_habit ?? null, corrections: {} };
}

/** "Garden bed 2" when "Garden bed" is taken. */
export function defaultZoneName(v: VegetationType, existing: string[]): string {
  const base = VEGETATION_WORDS[v];
  const taken = new Set(existing.map((n) => n.trim().toLowerCase()));
  if (!taken.has(base.toLowerCase())) return base;
  for (let i = 2; ; i++) {
    const name = `${base} ${i}`;
    if (!taken.has(name.toLowerCase())) return name;
  }
}

/** What is still missing before a draft can be saved, or null. */
export function draftProblem(d: ZoneDraft, box: Box | null): string | null {
  if (!d.vegetation) return 'Choose what grows there.';
  if (!box) return 'Stretch a box over the area first.';
  return null;
}

export function zoneCreateBody(
  d: ZoneDraft, box: Box, existingNames: string[], drawn = true,
): ZoneCreate {
  const vegetation = d.vegetation!;
  const body: ZoneCreate = {
    name: d.name.trim() || defaultZoneName(vegetation, existingNames),
    vegetation_type: vegetation,
    box,
    drawn,
  };
  if (leafHabitApplies(vegetation) && d.leafHabit) body.leaf_habit = d.leafHabit;
  return body;
}

/** Only what changed, so an edit never resends what the owner left alone. */
export function zonePatchBody(z: Zone, d: ZoneDraft, box: Box | null): ZonePatch {
  const patch: ZonePatch = {};
  const name = d.name.trim();
  if (name && name !== z.name) patch.name = name;
  if (d.vegetation && d.vegetation !== z.vegetation_type) patch.vegetation_type = d.vegetation;
  if (box && !sameBox(box, z.box)) patch.box = box;
  if (d.leafHabit && leafHabitApplies(d.vegetation ?? z.vegetation_type) && d.leafHabit !== z.leaf_habit) {
    patch.leaf_habit = d.leafHabit;
  }
  return patch;
}

export function sameBox(a: Box | null | undefined, b: Box | null | undefined): boolean {
  if (!a || !b) return a == b;
  const eq = (x: number, y: number) => Math.abs(x - y) < 1e-9;
  return eq(a.west, b.west) && eq(a.south, b.south) && eq(a.east, b.east) && eq(a.north, b.north);
}

/** The override bodies for the corrections picked, all by tap. */
export function correctionBodies(zoneId: number, d: ZoneDraft): OverridePut[] {
  return (Object.entries(d.corrections) as [SiteField, string][])
    .filter(([, v]) => !!v)
    .map(([field, value]) => ({ zone_id: zoneId, field, value, method: 'tap' as const }));
}

// ── Boxes without drawing ────────────────────────────────────────────────────

/** About 8,500 square feet, the typical United States lot the server's
 *  default yard uses (PLAN.md section 5). */
export const DEFAULT_LOT_SQFT = 8500;
const M_PER_DEG_LAT = 111_320;
const SQFT_PER_SQM = 10.7639;

/** A north-aligned square of `sqft` centred on a point, in degrees. */
export function squareAround(lat: number, lng: number, sqft = DEFAULT_LOT_SQFT): Box {
  const side = Math.sqrt(sqft / SQFT_PER_SQM);
  const dLat = side / 2 / M_PER_DEG_LAT;
  const dLng = side / 2 / (M_PER_DEG_LAT * Math.cos((lat * Math.PI) / 180));
  return { west: lng - dLng, east: lng + dLng, south: lat - dLat, north: lat + dLat };
}

/**
 * The box a zone made without drawing gets: the approximate yard the server
 * drew, else the same square around the pin. Said plainly on screen: it
 * covers the whole approximate yard until the owner draws it.
 */
export function defaultZoneBox(
  imagery: Pick<Imagery, 'default_footprint' | 'pin'> | null | undefined,
  pin: { lat: number; lng: number },
): Box {
  if (imagery?.default_footprint) return imagery.default_footprint;
  const p = imagery?.pin ?? pin;
  return squareAround(p.lat, p.lng);
}

// ── Deleting ─────────────────────────────────────────────────────────────────

/** Why a zone cannot be deleted, in plain words, or null if it can. */
export function deleteBlockedReason(z: Pick<Zone, 'is_whole_lot' | 'plant_count'>): string | null {
  if (z.is_whole_lot) {
    return 'The whole yard cannot be deleted. It holds the values for your land as a whole.';
  }
  if (z.plant_count > 0) {
    const n = z.plant_count === 1 ? '1 plant' : `${z.plant_count} plants`;
    return `This zone has ${n} in it, so it cannot be deleted. Move ${z.plant_count === 1 ? 'it' : 'them'} to another space first.`;
  }
  return null;
}

/** What to say when the server refuses a delete (it answers 409). */
export const DELETE_REFUSED = 'This zone still has plants in it, so it cannot be deleted. Move them to another space first.';

// ── What the zone map shows ──────────────────────────────────────────────────

/** The label drawn on a zone's box. */
export function zoneLabel(z: Pick<Zone, 'name' | 'is_whole_lot' | 'boundary_source'>): string {
  if (z.is_whole_lot && z.boundary_source === 'default') {
    return 'Approximate yard (typical United States lot size, not your property line)';
  }
  return z.name;
}

/** The values shown under a saved zone: sun and where water collects. */
export const ZONE_VALUE_FIELDS: SiteField[] = ['sun', 'water_collects'];

export function zoneShownValues(values: SiteValue[] | null | undefined): SiteValue[] {
  return ZONE_VALUE_FIELDS
    .map((f) => (values ?? []).find((v) => v.field === f))
    .filter((v): v is SiteValue => v != null);
}

/** Whether a saved zone is still waiting on the server for its values. */
export function zoneValuesPending(values: SiteValue[] | null | undefined): boolean {
  const shown = zoneShownValues(values);
  return shown.length < ZONE_VALUE_FIELDS.length
    || shown.some((v) => v.confidence === 'not_known_yet' && v.provenance !== 'owner');
}

/** One line for a screen reader about a zone's box. */
export function zoneA11yLabel(z: Pick<Zone, 'name' | 'vegetation_type' | 'is_whole_lot' | 'boundary_source' | 'plant_count'>): string {
  const what = z.vegetation_type ? VEGETATION_WORDS[z.vegetation_type] : null;
  const plants = z.plant_count === 1 ? '1 plant' : `${z.plant_count} plants`;
  return [zoneLabel(z), what, plants].filter(Boolean).join('. ') + '. Opens this zone to edit it.';
}
