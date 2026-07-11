import { Species } from '../types';

// Grounds an on-device model's free-text answer in the curated species
// catalog. The AI's raw text is NEVER treated as authoritative — it's only a
// query into records that have real, reviewed care data. Pure and
// dependency-free so it's unit-testable off-device.

export interface ScoredSpecies {
  species: Species;
  score: number; // 0..1
}

// Confidence tiers (tuned in fuzzyMatch tests against realistic model output):
export const CONFIDENT = 0.6; // populate the species field from this match
export const PLAUSIBLE = 0.42; // offer as a pickable candidate, not auto-trusted

export function normalize(s: string): string {
  return (s || '')
    .toLowerCase()
    .replace(/[''`]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

function bigrams(s: string): Map<string, number> {
  const m = new Map<string, number>();
  const t = s.replace(/\s+/g, ' ');
  for (let i = 0; i < t.length - 1; i++) {
    const bg = t.slice(i, i + 2);
    m.set(bg, (m.get(bg) ?? 0) + 1);
  }
  return m;
}

/** Sørensen–Dice coefficient over character bigrams (0..1). */
export function diceCoefficient(a: string, b: string): number {
  if (a === b) return 1;
  if (a.length < 2 || b.length < 2) return 0;
  const A = bigrams(a);
  const B = bigrams(b);
  let overlap = 0;
  let totalA = 0;
  for (const n of A.values()) totalA += n;
  let totalB = 0;
  for (const n of B.values()) totalB += n;
  for (const [bg, countA] of A) {
    const countB = B.get(bg);
    if (countB) overlap += Math.min(countA, countB);
  }
  return (2 * overlap) / (totalA + totalB);
}

/** True when every token of `name` appears in `text` (order-independent). */
function containsAllTokens(text: string, name: string): boolean {
  const words = new Set(text.split(' ').filter(Boolean));
  const nameTokens = name.split(' ').filter(Boolean);
  return nameTokens.length > 0 && nameTokens.every((t) => words.has(t));
}

/**
 * Score how well the model's answer matches a single candidate name.
 * The model often returns a sentence ("This looks like a Monstera deliciosa,
 * commonly the Swiss cheese plant"), so exact containment of the whole name is
 * the strongest signal; character-level Dice catches typos/inflections.
 */
export function scoreName(aiText: string, name: string): number {
  const a = normalize(aiText);
  const b = normalize(name);
  if (!a || !b) return 0;
  if (a === b) return 1;
  // Whole candidate name appears verbatim in the answer (word-complete).
  if (b.length >= 4 && containsAllTokens(a, b)) {
    // Longer, more specific names (e.g. binomials) are stronger evidence.
    return b.includes(' ') ? 0.97 : 0.82;
  }
  return diceCoefficient(a, b);
}

/**
 * Rank the catalog against the model's answer. Each species is scored on the
 * best of its common and scientific names. Returns matches sorted best-first.
 */
export function matchSpecies(aiText: string, species: Species[]): ScoredSpecies[] {
  return species
    .map((sp) => ({
      species: sp,
      score: Math.max(
        scoreName(aiText, sp.common_name),
        scoreName(aiText, sp.scientific_name),
      ),
    }))
    .filter((s) => s.score > 0)
    .sort((a, b) => b.score - a.score);
}

export interface MatchResult {
  tier: 'confident' | 'plausible' | 'none';
  candidates: ScoredSpecies[]; // best-first; [] when tier is 'none'
}

/**
 * Turn ranked matches into a decision: a confident single hit, a few plausible
 * options to choose from, or nothing worth trusting.
 */
export function classifyMatches(scored: ScoredSpecies[]): MatchResult {
  const best = scored[0];
  if (!best || best.score < PLAUSIBLE) return { tier: 'none', candidates: [] };
  if (best.score >= CONFIDENT) {
    // Include near-ties so an obvious pick is pre-selected but alternatives show.
    const near = scored.filter((s) => s.score >= best.score - 0.12).slice(0, 3);
    return { tier: 'confident', candidates: near };
  }
  return { tier: 'plausible', candidates: scored.filter((s) => s.score >= PLAUSIBLE).slice(0, 4) };
}
