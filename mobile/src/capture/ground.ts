import { Species } from '../types';
import { matchSpecies, classifyMatches, ScoredSpecies } from '../photoId/fuzzyMatch';
import { ParsedEntry } from './splitUtterance';

// Grounds each clause of a spoken description in the curated catalog.
//
// The rule the rest of the app already follows applies here unchanged: what a
// person said (or what a model heard) is never authoritative. It is a query
// into records that carry real care data, and a weak match yields no species
// rather than a wrong one. Only a Species the catalog already holds can end up
// on a plant.
//
// Pure and dependency-free so it unit-tests off-device.

/** Near-ties to show beside a confident pick. Higher than the photo-ID flow's
 *  three: several species are grounded in one pass here, and a truncated list
 *  silently drops a plant the user actually named. */
const CONFIDENT_LIMIT = 5;
/** Options offered when nothing is confident. */
const PLAUSIBLE_LIMIT = 6;

export interface GroundedEntry {
  entry: ParsedEntry;
  tier: 'confident' | 'plausible' | 'none';
  /** Best-first; empty when nothing scored well enough to be worth offering. */
  candidates: ScoredSpecies[];
  /** Which phrasing actually earned the match, for showing our working. */
  matchedPhrase: string;
}

/**
 * Ground one clause. Every phrasing the splitter offered is scored and the best
 * one wins, which is what lets "three tomato plants" find Tomatoes while
 * "a snake plant" still finds Snake Plant: the first is only matchable with the
 * form noun dropped, the second only with it kept. Deciding by score means this
 * module never has to guess which words are filler.
 */
export function groundEntry(entry: ParsedEntry, catalog: Species[]): GroundedEntry {
  const phrasings = [entry.phrase, ...entry.altPhrases].filter(Boolean);

  let bestPhrase = entry.phrase;
  let bestScored: ScoredSpecies[] = [];
  for (const phrasing of phrasings) {
    const scored = matchSpecies(phrasing, catalog);
    if ((scored[0]?.score ?? 0) > (bestScored[0]?.score ?? 0)) {
      bestScored = scored;
      bestPhrase = phrasing;
    }
  }

  const { tier, candidates } = classifyMatches(bestScored, {
    confident: CONFIDENT_LIMIT,
    plausible: PLAUSIBLE_LIMIT,
  });
  return { entry, tier, candidates, matchedPhrase: bestPhrase };
}

/** Ground a whole description. Entries that match nothing are kept, not
 *  dropped — the UI owes the user "couldn't place this one" rather than
 *  silently losing a plant they told us about. */
export function groundEntries(entries: ParsedEntry[], catalog: Species[]): GroundedEntry[] {
  return entries.map((e) => groundEntry(e, catalog));
}

/** What to write down when the user didn't say a number. One is the honest
 *  floor — they named the plant, so at least one exists — and the review row
 *  lets them correct it before anything is saved. */
export function effectiveCount(entry: ParsedEntry): number {
  return entry.count ?? 1;
}
