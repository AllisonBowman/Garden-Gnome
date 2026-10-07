// How an area's candidate list is ordered, and where it stops, in words.
//
// The server ranks (`fit.candidates`): the more a source confirmed about a
// species in this space, the higher it sits, and where two are level, A to
// Z. Nothing finer is on record to tell level candidates apart, so the
// order within a tie claims nothing — and a list cut at twelve usually cuts
// through one. Dozens of species can be confirmed on everything a bed is
// checked for, and an indoor spot nobody has measured can confirm only one
// thing, so every candidate it has is level. Left unsaid, the first twelve of
// an alphabet read as the twelve best. So the screens say how many there are,
// how they are ordered, and whether the cut fell between equals.
//
// Pure, like fitFindings: the area screen and the Almanac say it alike.

import type { Candidate } from '../api/growingAreas';

/** How many candidates an area's screen shows before offering the rest. */
export const FIRST_FEW = 12;

/** The ranking rule, said once wherever a ranked list is shown. */
export const RANK_ORDER =
  'The more that’s confirmed here, the higher a species sits; where they tie, it’s A to Z.';

/** The whole count the server sent with a cut list (its X-Total-Count
 *  header), or null when there is none to read — a server older than the
 *  count — in which case a screen says nothing about the rest rather than
 *  guess. Header names are matched case-blind: they reach the app in
 *  whatever case the platform hands them over. */
export function totalCount(headers: unknown): number | null {
  if (headers == null || typeof headers !== 'object') return null;
  const hit = Object.entries(headers as Record<string, unknown>)
    .find(([name]) => name.toLowerCase() === 'x-total-count');
  if (!hit) return null;
  const text = String(hit[1]).trim();
  return /^\d+$/.test(text) ? Number(text) : null;
}

/** The line over the list: how many species the spot has nothing on record
 *  against and at least one thing confirmed for, then the rule they are in
 *  order by. Null when there is no list to introduce. */
export function listIntro(total: number | null, shown: number): string | null {
  if (total === 1) {
    return 'One species has nothing on record against this spot and at least one '
      + 'thing confirmed.';
  }
  if (total != null && total > 1) {
    return `${total} species have nothing on record against this spot and at least `
      + `one thing confirmed. ${RANK_ORDER}`;
  }
  // A server that sent no count: the order is still true of what is shown.
  return total == null && shown > 1 ? RANK_ORDER : null;
}

/** The line under a list that stops short: how much of it is shown, and
 *  whether the cut fell between equals. `next` is the first candidate past
 *  the cut — fetched for this and never shown — and the only way to know
 *  whether the last one here is better evidenced than what follows or merely
 *  earlier in the alphabet. Null when nothing was left out. */
export function cutNote(
  shown: Candidate[], next: Candidate | undefined, total: number | null,
): string | null {
  const more = total != null ? total > shown.length : next != null;
  if (!more || shown.length === 0) return null;
  const showing = total != null
    ? `Showing ${shown.length} of ${total}.`
    : `Showing the first ${shown.length}.`;
  if (next == null) return showing;
  const last = shown[shown.length - 1];
  if (next.score === last.score) {
    return `${showing} The next one has as much confirmed as the last one here, so `
      + 'where this list stops is down to the alphabet, not the evidence.';
  }
  // The list is ranked, so a next one with less confirmed than the last one
  // here means everything after it has less confirmed too.
  if (next.score < last.score) return `${showing} Everything after these has less confirmed.`;
  return showing;
}

/** Species in the order the server ranked them for an area, the order its
 *  own screen lists them in, so a longer list that takes up where that one
 *  stops goes on in the same order. Anything the ranking doesn't hold keeps
 *  its place, after everything it does. */
export function inRankOrder<T extends { id: number }>(items: T[], ranked: Candidate[]): T[] {
  const rank = new Map(ranked.map((c, i) => [c.species_id, i]));
  const at = (item: T) => rank.get(item.id) ?? Number.MAX_SAFE_INTEGER;
  return [...items].sort((a, b) => at(a) - at(b));
}
