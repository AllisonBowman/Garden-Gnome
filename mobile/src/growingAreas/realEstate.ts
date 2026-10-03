// The growing area's real estate: what it is, how it is measured, what it is
// for. Pure data and pure functions — no React, so the setup flow and the fit
// surfaces can share one vocabulary and the whole thing is testable.

import {
  GrowingSurface, GrowingGoal, GrowingAreaType, GrowingArea,
  Shelter, TempExposure, SunExposure,
} from '../types';
import type { Candidate, FitFinding } from '../api/growingAreas';
import { lengthSaid } from '../care/facts';

export const SURFACES: GrowingSurface[] = [
  'in_ground_bed', 'raised_bed', 'containers', 'windowsill',
  'shelf_or_floor', 'hanging', 'greenhouse_bench', 'pond_or_water',
];

export const SURFACE_LABEL: Record<GrowingSurface, string> = {
  in_ground_bed:    '🌍 In-ground bed',
  raised_bed:       '🪵 Raised bed',
  containers:       '🪴 Containers',
  windowsill:       '🪟 Windowsill',
  shelf_or_floor:   '🗄️ Shelf or floor',
  hanging:          '🌿 Hanging',
  greenhouse_bench: '🏕️ Greenhouse bench',
  pond_or_water:    '💧 Pond or water',
};

/** Surfaces whose soil is whatever is already there, at whatever depth. */
export const IS_BED: Record<GrowingSurface, boolean> = {
  in_ground_bed: true, raised_bed: true, containers: false, windowsill: false,
  shelf_or_floor: false, hanging: false, greenhouse_bench: false,
  pond_or_water: false,
};

export const GOALS: { value: GrowingGoal; label: string; hint: string }[] = [
  {
    value: 'edible',
    label: '🥕 Something to eat',
    hint: 'Only species grown to eat.',
  },
  {
    value: 'low_upkeep',
    label: '😌 Low upkeep',
    hint: 'Only species that tolerate being left alone.',
  },
  {
    value: 'pollinators',
    label: '🐝 Feeds pollinators',
    hint: 'Only species recorded as feeding bees, butterflies or hummingbirds.',
  },
];

export type Climate = {
  shelter: Shelter;
  temp_exposure: TempExposure;
  sun_exposure: SunExposure;
};

// Where a surface usually sits, so the conditions step starts somewhere
// sensible. A preset, never a fact: every value stays editable, and none of
// these is what the fit engine reads — it reads what the gardener confirmed.
const SURFACE_CLIMATE: Record<GrowingSurface, Climate> = {
  in_ground_bed:    { shelter: 'exposed',   temp_exposure: 'outdoor', sun_exposure: 'full_sun'    },
  raised_bed:       { shelter: 'exposed',   temp_exposure: 'outdoor', sun_exposure: 'full_sun'    },
  containers:       { shelter: 'partial',   temp_exposure: 'outdoor', sun_exposure: 'partial_sun' },
  windowsill:       { shelter: 'sheltered', temp_exposure: 'indoor',  sun_exposure: 'partial_sun' },
  shelf_or_floor:   { shelter: 'sheltered', temp_exposure: 'indoor',  sun_exposure: 'shade'       },
  hanging:          { shelter: 'sheltered', temp_exposure: 'indoor',  sun_exposure: 'partial_sun' },
  // Glass keeps the rain off but not the season — a greenhouse still follows
  // the outside temperature far more closely than a living room does.
  greenhouse_bench: { shelter: 'sheltered', temp_exposure: 'outdoor', sun_exposure: 'full_sun'    },
  pond_or_water:    { shelter: 'exposed',   temp_exposure: 'outdoor', sun_exposure: 'full_sun'    },
};

export function climateForSurface(surface: GrowingSurface): Climate {
  return SURFACE_CLIMATE[surface];
}

// --- who keeps the space ----------------------------------------------------
// An area's type says whose space it is. The census counts areas by it, and
// nothing that judges fit reads it. It is asked, never inferred: what plants
// sit in says nothing about who keeps them — most raised beds are someone's
// back garden, not a community plot — and a guess here once labelled a home
// bed "Community garden" behind the gardener's back.

/** The types the setup offers, in the order it offers them. */
export const AREA_TYPES: GrowingAreaType[] = [
  'home', 'nursery', 'community_garden', 'conservation', 'research',
];

/** Keyed by string, not by the type: the server knows a few more types than
 *  the setup offers (balcony, greenhouse, other), and those still need words. */
const AREA_TYPE_LABEL: Record<string, string> = {
  home: '🏠 Home',
  nursery: '🌱 Nursery',
  community_garden: '🌳 Community garden',
  conservation: '🌿 Conservation',
  research: '🔬 Research',
  balcony: '🪴 Balcony',
  greenhouse: '🏕️ Greenhouse',
  other: '📍 Other',
};

/** An area type in words — never the raw token, even for one this build
 *  has not heard of. */
export function areaTypeLabel(type: string): string {
  const known = AREA_TYPE_LABEL[type];
  if (known) return known;
  const words = type.replace(/_/g, ' ');
  return words.charAt(0).toUpperCase() + words.slice(1);
}

export type Prompt = { label: string; hint: string };

/** Said wherever the depth is asked for or counted on. Nothing in the fit
 *  engine reads it — no axis compares a plant's roots with it — and a field
 *  that silently does nothing breaks the promise the form makes, that a
 *  number given here shapes what gets suggested. Drop this when an axis
 *  reads `soil_depth_in`. */
const DEPTH_UNCHECKED = 'Kept with the space — no plant is checked against it yet.';
export type DimensionPrompts = {
  area: Prompt; headroom: Prompt; depth: Prompt;
};

/** What to call each measurement, given what the space actually is.
 *
 * "Soil depth" is the wrong question for a windowsill and "pot depth" is the
 * wrong one for a border. Asking the right one is the difference between a
 * number somebody measures and a field they skip. */
export function dimensionPrompts(surface: GrowingSurface | null): DimensionPrompts {
  const bed = surface != null && IS_BED[surface];
  const water = surface === 'pond_or_water';

  return {
    area: {
      label: 'Footprint (sq ft)',
      hint: bed
        ? 'Roughly how much bed there is to fill.'
        : water
          ? 'Surface area of the water.'
          : 'How much shelf, sill or floor this spot gives you.',
    },
    headroom: {
      label: 'Headroom (inches)',
      hint: bed
        ? 'How tall something can get before it shades or crowds its neighbours.'
        : 'Distance to the shelf, cupboard or ceiling above.',
    },
    depth: {
      label: bed ? 'Soil depth (inches)' : water ? 'Water depth (inches)' : 'Pot depth (inches)',
      hint: `${bed
        ? 'How far roots can run before they hit hardpan, liner or rock.'
        : water
          ? 'Depth at the planting shelf, not the deepest point.'
          : 'Inside depth of the pots you’ll use here.'} ${DEPTH_UNCHECKED}`,
    },
  };
}

// --- lengths, as the reasons say them --------------------------------------
// Headroom and depth are asked in inches, and the fit sentences say anything
// from two feet up in feet: 84 in typed, "there is 7 ft of headroom" read.
// One number shown two ways with nothing joining them reads as two numbers,
// so wherever a measured length is shown back it is said the way the
// sentences say it (`lengthSaid`, the engine's own rule), with the inches the
// gardener typed beside it.

/** A measured length on the area's card: "7 ft (84 in)", or "18 in" where
 *  the sentences would say inches too. */
export function measuredLength(inches: number): string {
  const said = lengthSaid(inches);
  return said === `${inches} in` ? said : `${said} (${inches} in)`;
}

/** Under a length field as it is typed, once the reasons would say it in
 *  feet: "That’s 7 ft." Nothing for a blank, a zero or a length kept in
 *  inches. */
export function lengthEcho(raw: string): string | null {
  const inches = parseFloat(raw);
  if (!Number.isFinite(inches) || inches <= 0) return null;
  const said = lengthSaid(inches);
  return said === `${inches} in` ? null : `That’s ${said}.`;
}

// --- what could not be checked -------------------------------------------

/** A goal as it reads mid-sentence: "something to eat", "low upkeep". */
export function goalPhrase(goal: GrowingGoal): string {
  const entry = GOALS.find((g) => g.value === goal);
  return entry
    ? entry.label.replace(/^\S+\s/, '').toLowerCase()
    : goal.replace(/_/g, ' ');
}

/** Which of the area's goals a finding answers.
 *
 * The server says so in `goal`. Low upkeep is also recognisable by its axis;
 * edible and pollinators share the `goal` axis and are not — so a finding
 * from a server older than the `goal` field is taken to answer either, the
 * reading these notes gave before the field existed. */
export function goalsAnswered(finding: FitFinding): GrowingGoal[] {
  if (finding.goal) return [finding.goal];
  if (finding.axis === 'upkeep') return ['low_upkeep'];
  if (finding.axis === 'goal') return ['edible', 'pollinators'];
  return [];
}

/** The axes this area turns on that the list could not answer, in plain words.
 *
 * A recommendation list is read as a verdict on the space, so a list thinned
 * by a gap in the evidence has to say which gap. The alternative is what the
 * first end-to-end run did: the gardener asked for something edible that feeds
 * pollinators, neither field was researched on a single species yet, and the
 * app quietly returned a list narrowed by neither — indistinguishable from a
 * list that had honoured both.
 *
 * Derived from the answers themselves rather than from a separate endpoint:
 * a confirmed fit on an axis appears in a candidate's `fits`, so an axis — or
 * a goal — that appears nowhere across the list is one nothing on it could
 * confirm. Every note speaks about the list it sits above, never about the
 * whole catalog: the catalog keeps being researched, and a sentence like "no
 * species carries a mature size yet" goes on being shown long after it stops
 * being true. An empty list gets only the note about the space itself, since
 * "nothing on this list" says nothing about a list with nothing on it.
 */
export function uncheckedNotes(
  area: Pick<
    GrowingArea,
    'temp_exposure' | 'goals' | 'area_sqft' | 'headroom_in' | 'soil_depth_in' | 'surface'
  >,
  candidates: Candidate[],
): string[] {
  const notes: string[] = [];
  const confirmed = candidates.flatMap((c) => c.fits);
  const axesConfirmed = new Set(confirmed.map((f) => f.axis));
  const goalsConfirmed = new Set(confirmed.flatMap(goalsAnswered));

  // Indoors the engine answers light with `unknown` every time: an area
  // records hours of direct sun, not how bright a room is, so there is
  // nothing to set a species' indoor light need against. That is a fact
  // about the space, true whatever the catalog holds — and it is said in a
  // gardener's words, not in the database's ("the old light column").
  if (area.temp_exposure === 'indoor') {
    notes.push(
      'Indoor light isn’t checked: nothing records how bright this spot is, '
      + 'so nothing here was matched on light.');
  }

  if (candidates.length === 0) return notes;

  // Per goal, not per axis: a list narrowed by low upkeep (its own axis) or
  // by pollinators has still not been narrowed by edibility.
  const unanswered = GOALS
    .filter((g) => (area.goals ?? []).includes(g.value) && !goalsConfirmed.has(g.value))
    .map((g) => goalPhrase(g.value));
  if (unanswered.length > 0) {
    notes.push(
      `Nothing here is filtered by what you asked for (${unanswered.join(', ')}). `
      + 'Nothing on this list has a source that answers it yet, so the list '
      + 'honours the space but not the wish.');
  }

  const measured = area.area_sqft != null || area.headroom_in != null;
  if (measured && !axesConfirmed.has('footprint')) {
    notes.push(
      'Size isn’t checked against your measurements. Nothing on this list has '
      + 'a recorded mature size to set against them, so whether any of it would '
      + 'outgrow the space is unknown.');
  }

  // A depth was measured and nothing reads it (DEPTH_UNCHECKED): said, so the
  // number is not taken to have narrowed the list.
  if (area.soil_depth_in != null) {
    const depth = dimensionPrompts(area.surface ?? null).depth.label.replace(/ \(.*\)$/, '');
    notes.push(
      `${depth} isn’t checked: nothing on this list was compared with the `
      + `${area.soil_depth_in} in you measured.`);
  }

  return notes;
}
