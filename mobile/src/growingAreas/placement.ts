// Where a new plant goes, said before it is saved.
//
// Add Plant used to leave the area blank until someone tapped one, and blank
// never meant "no area": the server put the plant in the caller's oldest area
// (`plants._resolve_growing_area_id`), or made a "My Home" for an account with
// none. The plant landed somewhere the screen had never shown. The fix is to
// show that same choice, preselected, so the default is visible and the
// gardener can change it.

import type { GrowingArea } from '../types';

/** The area a plant saved without one would land in: the oldest, by id —
 *  the server's own rule, whatever order the list happens to arrive in. */
export function defaultAreaId(areas: Pick<GrowingArea, 'id'>[]): number | null {
  if (areas.length === 0) return null;
  return Math.min(...areas.map((a) => a.id));
}

/** The area to show selected once the list has loaded: the one asked for —
 *  the area Add Plant was opened from, or the one last tapped — while it is
 *  still in the list, and otherwise the default. An area deleted elsewhere
 *  must not stay selected, or the save would name a place that is gone. */
export function placementAreaId(
  areas: Pick<GrowingArea, 'id'>[], wanted: number | null,
): number | null {
  if (wanted != null && areas.some((a) => a.id === wanted)) return wanted;
  return defaultAreaId(areas);
}

/** The name the server gives the area it makes for an account with none.
 *  Mirrors `_resolve_growing_area_id`; if that changes, so must this. */
export const FIRST_AREA_NAME = 'My Home';

/** Said where the area picker would be, when there is nothing to pick. The
 *  made area is a bare name — nothing about the space can be filled in once
 *  it exists — so the only useful advice is to set a space up first. */
export const NO_AREA_NOTE =
  `You have no growing areas yet, so this plant will go in a new one called `
  + `“${FIRST_AREA_NAME}”. Set up a space under Growing areas first if you’d `
  + 'like it checked against this plant.';

/** Said when the areas could not be loaded: the plant still lands somewhere,
 *  and the screen says where rather than leaving it to be discovered — the
 *  area it was added from, when it came from one, or else the oldest. */
export function areasFailedNote(fromArea: boolean): string {
  return `Couldn’t load your growing areas just now, so this plant will go in ${
    fromArea ? 'the one you came from' : 'your oldest one'
  }. You can move it from the plant’s page afterwards.`;
}
