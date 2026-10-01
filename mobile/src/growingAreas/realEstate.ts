// The growing area's real estate: what it is, how it is measured, what it is
// for. Pure data and pure functions — no React, so the setup flow and the fit
// surfaces can share one vocabulary and the whole thing is testable.

import {
  GrowingSurface, GrowingGoal, GrowingAreaType, GrowingArea,
  Shelter, TempExposure, SunExposure,
} from '../types';
import type { Candidate } from '../api/growingAreas';

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

const SURFACE_TYPE: Record<GrowingSurface, GrowingAreaType> = {
  in_ground_bed: 'community_garden', raised_bed: 'community_garden',
  containers: 'home', windowsill: 'home', shelf_or_floor: 'home',
  hanging: 'home', greenhouse_bench: 'nursery', pond_or_water: 'conservation',
};

export function typeForSurface(surface: GrowingSurface): GrowingAreaType {
  return SURFACE_TYPE[surface];
}

export type Prompt = { label: string; hint: string };
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
      hint: bed
        ? 'How far roots can run before they hit hardpan, liner or rock.'
        : water
          ? 'Depth at the planting shelf, not the deepest point.'
          : 'Inside depth of the pots you’ll use here.',
    },
  };
}

// --- what could not be checked -------------------------------------------

/** The axes this area turns on that the catalog cannot answer, in plain words.
 *
 * A recommendation list is read as a verdict on the space, so a list thinned
 * by a gap in the evidence has to say which gap. The alternative is what the
 * first end-to-end run did: the gardener asked for something edible that feeds
 * pollinators, neither field is researched on a single species yet, and the
 * app quietly returned a list narrowed by neither — indistinguishable from a
 * list that had honoured both.
 *
 * Derived from the answers themselves rather than from a separate endpoint:
 * a confirmed fit on an axis appears in a candidate's `fits`, so an axis that
 * appears nowhere across the whole list is an axis nothing could confirm.
 */
export function uncheckedNotes(
  area: Pick<GrowingArea, 'temp_exposure' | 'goals' | 'area_sqft' | 'headroom_in'>,
  candidates: Candidate[],
): string[] {
  const notes: string[] = [];
  const axesConfirmed = new Set(
    candidates.flatMap((c) => c.fits.map((f) => f.axis)));

  if (area.temp_exposure === 'indoor') {
    notes.push(
      'Indoor light isn’t checked. Almost nothing in the catalog records a '
      + 'species’ light level in footcandles, and the old light column is the '
      + 'one known to be wrong — so what’s here rests on the other axes.');
  }

  if (area.goals && area.goals.length > 0 && !axesConfirmed.has('goal')) {
    const wanted = GOALS.filter((g) => area.goals!.includes(g.value))
      .map((g) => g.label.replace(/^\S+\s/, '').toLowerCase());
    notes.push(
      `Nothing here is filtered by what you asked for (${wanted.join(', ')}). `
      + 'No species in the catalog has been researched for it yet, so the list '
      + 'below honours the space but not the wish.');
  }

  const measured = area.area_sqft != null || area.headroom_in != null;
  if (measured && !axesConfirmed.has('footprint')) {
    notes.push(
      'Size isn’t checked against your measurements. No species in the catalog '
      + 'carries a mature height or spread yet, so nothing here is ruled in or '
      + 'out on whether it would outgrow the space.');
  }

  return notes;
}
