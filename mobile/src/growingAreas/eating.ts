// What is eaten, as an area's candidate list groups it and says it.
//
// Eating is a cited description, not a verdict (ADR 0011). The server names
// the parts a source records as eaten, from a fixed vocabulary, and writes
// one line that says them with the condition on eating them and the hazards
// recorded beside them. When a space asked for something to eat, its list
// holds only species with a part on record, and this groups them by the
// part: what there is to harvest from the spot, and how.
//
// What this module never does is word the eating. The line is the server's,
// shown whole: the part without its condition is a different claim ("fruit"
// is not "ripe fruit"), and a second copy of the rule here would sooner or
// later drop the half that keeps it honest. Pure, like fitFindings, so the
// grouping and the words under the list are pinned by tests.

import type { Candidate } from '../api/growingAreas';
import type { EatenPart, GrowingGoal } from '../types';

/** The groups an eat list falls into, in the order it shows them, with the
 *  heading each is shown under. One per part the server can name; the
 *  headings say what a part covers, so tubers are found under roots and
 *  nuts under seeds, where the vocabulary files them. */
export const EATEN_PART_GROUPS: { part: EatenPart; label: string }[] = [
  { part: 'leaves', label: 'Leaves' },
  { part: 'fruit', label: 'Fruit' },
  { part: 'roots', label: 'Roots and tubers' },
  { part: 'seeds', label: 'Seeds and nuts' },
  { part: 'flowers', label: 'Flowers' },
  { part: 'stems', label: 'Stems and shoots' },
];

/** One group of an eat list: the part, its heading, and the candidates a
 *  source records it as eaten from. */
export interface EatenPartGroup {
  part: EatenPart;
  label: string;
  rows: Candidate[];
}

/** The candidates grouped by the part a source names as eaten, in the
 *  groups' order. A species whose source names two parts is in both groups,
 *  as the source names both. Within a group the rows keep the server's
 *  order, the ranking and then A to Z, and a group nothing is in is left out
 *  rather than shown empty. A candidate with no part on record is in no
 *  group: nothing says what is eaten from it. */
export function groupByEatenPart(rows: Candidate[]): EatenPartGroup[] {
  return EATEN_PART_GROUPS
    .map(({ part, label }) => ({
      part, label, rows: rows.filter((c) => (c.eaten_parts ?? []).includes(part)),
    }))
    .filter((group) => group.rows.length > 0);
}

/** The groups an area's candidates are shown in, or null when they are shown
 *  as one list, as they were before eating was described by the part.
 *  Grouped only when the area asked for something to eat and every row is
 *  in a group. A server older than the parts sends none, and a row whose
 *  only part this build has no group for would otherwise drop out of the
 *  list without a word: a species missing from a list reads as one that does
 *  not suit the space. */
export function eatingGroups(
  goals: GrowingGoal[] | null | undefined, rows: Candidate[],
): EatenPartGroup[] | null {
  if (!(goals ?? []).includes('edible') || rows.length === 0) return null;
  const groups = groupByEatenPart(rows);
  const placed = new Set(groups.flatMap((g) => g.rows.map((c) => c.species_id)));
  return rows.every((c) => placed.has(c.species_id)) ? groups : null;
}

/** What is eaten from a candidate, as its row says it: the server's line,
 *  whole, or null. It sits under the hazard line and over the reasons, and
 *  is never cut for space. A blank line is no line, and a server too old to
 *  send one sends nothing. */
export function eatingLine(candidate: Pick<Candidate, 'eating'>): string | null {
  const line = candidate.eating?.trim();
  return line ? line : null;
}

/** Under an eat list: how many species suit the spot but are off the list
 *  because no source records a part of them as eaten, so a short list reads
 *  as the sources' silence on eating and not as a verdict on the space. It
 *  takes the place of the caveat that the wish went unanswered, which
 *  stopped being true once the list held only species with a part on
 *  record. Null when none were left off, or when the server sent no count. */
export function leftOffNote(leftOff: number | null): string | null {
  if (leftOff == null || leftOff <= 0) return null;
  if (leftOff === 1) {
    return 'One species fits this spot, but no source records any part of it as eaten, '
      + 'so it is not on this list.';
  }
  return `${leftOff} species fit this spot, but no source records any part of them as `
    + 'eaten, so they are not on this list.';
}
