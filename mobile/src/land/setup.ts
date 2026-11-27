import {
  LOT_CONTENTS, LotContent, PinSource, ProfileStatus, ProfileStepStatus, PropertyCreate, PropertyPatch,
} from '../types/site';
import { LatLng } from './imageGeometry';
import { t } from '../i18n';

// Property setup as pure logic: the lot contents chips, whether a place is in
// the United States, nudging the pin, and the body sent to the server. The
// address the device geocoder found only centres the image: nothing here
// ever puts it (or the city or country it came with) in a request.

export const LOT_CONTENT_LABELS: Record<LotContent, string> = {
  trees_that_drop_leaves: t('land.lotContents.trees_that_drop_leaves'),
  evergreens: t('land.lotContents.evergreens'),
  shrubs: t('land.lotContents.shrubs'),
  lawn: t('land.lotContents.lawn'),
  garden_beds: t('land.lotContents.garden_beds'),
  potted_plants: t('land.lotContents.potted_plants'),
  vegetables: t('land.lotContents.vegetables'),
  mostly_paved: t('land.lotContents.mostly_paved'),
};

/** The chips in their fixed order, with their labels. */
export function lotContentChoices(): Array<{ value: LotContent; label: string }> {
  return LOT_CONTENTS.map((value) => ({ value, label: LOT_CONTENT_LABELS[value] }));
}

/** Tap a chip: add it, or take it away. The order stays the chips' order. */
export function toggleLotContent(current: readonly LotContent[], value: LotContent): LotContent[] {
  const set = new Set(current);
  if (set.has(value)) set.delete(value); else set.add(value);
  return LOT_CONTENTS.filter((v) => set.has(v));
}

const US_NAMES = new Set([
  'united states', 'united states of america', 'usa', 'us', 'u.s.', 'u.s.a.',
  'puerto rico', 'guam', 'u.s. virgin islands', 'united states virgin islands',
  'american samoa', 'northern mariana islands',
]);

/** Rough boxes around the states and territories the public maps cover,
 *  used only when the geocoder gave no country name. */
const US_BOXES: Array<[number, number, number, number]> = [
  // west, south, east, north
  [-125, 24.4, -66.9, 49.4],   // the lower 48 states
  [-170, 51, -129.9, 71.5],    // Alaska
  [-160.3, 18.9, -154.8, 22.3], // Hawaii
  [-67.3, 17.8, -65.2, 18.6],  // Puerto Rico and the Virgin Islands
];

/**
 * Whether the public land maps can describe this place. The geocoder's
 * country name decides when there is one; otherwise a rough outline.
 */
export function inUnitedStates(place: { country?: string | null; lat: number; lng: number }): boolean {
  const country = (place.country ?? '').trim().toLowerCase();
  if (country) return US_NAMES.has(country);
  return US_BOXES.some(([w, s, e, n]) => place.lng >= w && place.lng <= e && place.lat >= s && place.lat <= n);
}

const METRES_PER_DEGREE_LAT = 111_320;

/** Distance between two places in metres (flat-earth, fine at yard scale). */
export function metresBetween(a: LatLng, b: LatLng): number {
  const dy = (a.lat - b.lat) * METRES_PER_DEGREE_LAT;
  const dx = (a.lng - b.lng) * METRES_PER_DEGREE_LAT * Math.cos(((a.lat + b.lat) / 2) * Math.PI / 180);
  return Math.hypot(dx, dy);
}

export type Direction = 'north' | 'south' | 'east' | 'west';

/** How far one tap on a nudge button moves the pin. */
export const NUDGE_METRES = 5;

/** Move the pin a few metres without dragging (for anyone who cannot drag). */
export function nudge(p: LatLng, direction: Direction, metres: number = NUDGE_METRES): LatLng {
  const dLat = metres / METRES_PER_DEGREE_LAT;
  const dLng = metres / (METRES_PER_DEGREE_LAT * Math.cos(p.lat * Math.PI / 180));
  switch (direction) {
    case 'north': return { lat: p.lat + dLat, lng: p.lng };
    case 'south': return { lat: p.lat - dLat, lng: p.lng };
    case 'east': return { lat: p.lat, lng: p.lng + dLng };
    case 'west': return { lat: p.lat, lng: p.lng - dLng };
  }
}

/** Where the pin came from: the device's position, left where it was, or
 *  the owner's own placement. A pin moved more than a couple of metres, or
 *  one that started from a typed address, is the owner's. */
export function pinSourceFor(start: 'device' | 'typed', moved: boolean): PinSource {
  return start === 'device' && !moved ? 'device_location' : 'owner_pin';
}

/** A pin counts as moved once it is this far from where it started. */
export const MOVED_METRES = 2;

/** The create body: the pin, how it was placed, and the chips. Nothing from
 *  the address search goes in. */
export function createBody(pin: LatLng, pinSource: PinSource, lotContents: readonly LotContent[]): PropertyCreate {
  const body: PropertyCreate = { pin_lat: pin.lat, pin_lng: pin.lng, pin_source: pinSource };
  if (lotContents.length > 0) body.lot_contents = [...lotContents];
  return body;
}

/** The patch after going back over an existing property: only what changed. */
export function editPatch(
  before: { pin: LatLng; lotContents: readonly LotContent[] },
  after: { pin: LatLng; lotContents: readonly LotContent[] },
): PropertyPatch {
  const patch: PropertyPatch = {};
  if (metresBetween(before.pin, after.pin) >= MOVED_METRES) {
    patch.pin_lat = after.pin.lat;
    patch.pin_lng = after.pin.lng;
  }
  const a = [...before.lotContents].sort().join(',');
  const b = [...after.lotContents].sort().join(',');
  if (a !== b) patch.lot_contents = [...after.lotContents];
  return patch;
}

// ── "Reading your land" ─────────────────────────────────────────────────────

export interface ReadingLine { key: 'fast' | 'background'; what: string; state: string; done: boolean }

const STEP_WORDS: Record<ProfileStepStatus, string> = {
  pending: t('land.steps.pending'),
  building: t('land.steps.building'),
  ready: t('land.steps.ready'),
  partial: t('land.steps.partial'),
  failed: t('land.steps.failed'),
};

/** One line per step of the profile, for the screen shown after creating. */
export function readingLines(status: ProfileStatus): ReadingLine[] {
  return [
    {
      key: 'fast', what: t('land.readingFast'),
      state: STEP_WORDS[status.fast], done: status.fast !== 'pending' && status.fast !== 'building',
    },
    {
      key: 'background', what: t('land.readingBackground'),
      state: STEP_WORDS[status.background],
      done: status.background !== 'pending' && status.background !== 'building',
    },
  ];
}

/** Whether either step is still running, so the screen keeps asking. */
export function stillReading(status: ProfileStatus | null | undefined): boolean {
  if (!status) return true;
  const busy = (s: ProfileStepStatus) => s === 'pending' || s === 'building';
  return busy(status.fast) || busy(status.background);
}

/** How often to ask the server again while a step runs. */
export const POLL_MS = 4000;
