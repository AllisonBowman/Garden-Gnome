import { Vitals } from '../types/site';

// Which form Home takes. Pure, so the rules can be pinned by tests.
//
// - `land`: the server has the new routes on and the person has a property.
// - `no_land`: routes on, no property (an apartment with pots, or a yard not
//   added yet). Weather, care and spaces, with one calm "Add your land" card.
// - `feature_off`: the server answered 404 for the new routes. Home builds
//   the same no-property report from the routes the app used before, and
//   the "Add your land" card is hidden: there is nowhere to add it to.
// - `loading` / `failed`: nothing to show yet. A refresh that fails after a
//   first load keeps the form it had (React Query keeps the data).

export type HomeForm = 'loading' | 'failed' | 'land' | 'no_land' | 'feature_off';

export interface HomeFormInput {
  /** The vitals answer: a report, `null` for "feature off", `undefined`
   *  while nothing has arrived. */
  vitals: Vitals | null | undefined;
  /** The vitals load failed with a real error (not "feature off"). */
  failed: boolean;
}

export function homeForm({ vitals, failed }: HomeFormInput): HomeForm {
  if (vitals === null) return 'feature_off';
  if (vitals === undefined) return failed ? 'failed' : 'loading';
  return vitals.property ? 'land' : 'no_land';
}

/** "Add your land" is offered only where it can be done: no property yet,
 *  and a server that says it can add one. The seasonal plan and the land
 *  routes have separate switches, so /vitals can answer while adding land
 *  would answer 404; an older server that does not send `can_add_land` is
 *  taken at its word that it cannot. */
export function offersAddLand(form: HomeForm, vitals?: Vitals | null): boolean {
  return form === 'no_land' && vitals?.can_add_land === true;
}

/** Whether Home must read weather, spaces and the headline from the routes
 *  the app used before the new ones. */
export function usesLegacyRoutes(form: HomeForm): boolean {
  return form === 'feature_off';
}
