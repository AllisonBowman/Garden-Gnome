// How a fit finding is introduced on screen: which axis it is about, and
// whose word it rests on. Pure, so every surface that shows findings — the
// area's two cards, the Almanac, Add Plant — labels them the same way.
//
// What this module never does is word a verdict. The sentence a person reads
// is the server's (`FitFinding.sentence`), shown as-is, borrowed label and
// all: a second copy of the fit rules here would sooner or later disagree
// with the first, and the gardener would see both.

import type { FitAxis, FitFinding } from '../api/growingAreas';
import { goalPhrase } from './realEstate';

export const AXIS_LABEL: Record<FitAxis, string> = {
  indoor_outdoor: 'Indoors or out',
  sun: 'Sun',
  soil: 'Soil',
  footprint: 'Size',
  upkeep: 'Upkeep',
  goal: 'What it’s for',
};

const capitalize = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

/** What a finding is about: its axis, or for a goal, the goal itself —
 *  "Something to eat" says more than "What it’s for" when there are two. */
export function findingLabel(finding: FitFinding): string {
  if (finding.goal) return capitalize(goalPhrase(finding.goal));
  // An axis a newer server added: still readable, never a raw token.
  return AXIS_LABEL[finding.axis] ?? capitalize(String(finding.axis).replace(/_/g, ' '));
}

/** The line over a finding's sentence: the axis, then whose word it is —
 *  "Sun · NC State Extension". No authority means nothing about this
 *  species was cited for it, and the line says only the axis rather than
 *  inventing a "sources" for it. */
export function findingHeading(finding: FitFinding): string {
  const who = finding.authorities ?? [];
  return who.length > 0
    ? `${findingLabel(finding)} · ${who.join(', ')}`
    : findingLabel(finding);
}

/** Shown in place of a fit answer the app could not fetch. A failed request
 *  has checked nothing, so it must never fall through to an empty list's
 *  all-clear wording ("nothing here contradicts the space"). */
export const CHECK_FAILED =
  'Couldn’t reach the catalog to check this just now — that isn’t an all-clear. '
  + 'Try again in a moment.';
