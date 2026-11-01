// What a "Report a fact" email carries: the species page's facts as the
// reader saw them, in the page's order and in its words, so a report still
// names the fact as shown after the catalog has changed. The hazard sentence
// comes first, since a wrong one can hurt someone; then the care facts, the
// values not yet cited, and the care notes. Only what the page shows: the
// passage behind a fact stays on the server (ADR 0003).
//
// Pure on purpose (no React Native imports) so jest can pin it.
import { Species } from '../types';
import {
  CATALOG_LINE, INFERRED_PILL, careFactRows, legacyStats,
} from './facts';

/** The page's facts, one per line; empty when the page states none. */
export function reportedFacts(species: Species): string {
  const lines: string[] = [];
  const sentence = species.toxicity_description?.trim();
  if (sentence) lines.push(sentence);
  // An older server sends only the flag, and the page shows a chip for it.
  else if (species.toxic_to_pets === true) lines.push('⚠️ Toxic to pets');
  for (const row of careFactRows(species)) {
    const label = row.inferred ? `${row.label} (${INFERRED_PILL})` : row.label;
    lines.push(`${label}: ${row.caution ? `⚠️ ${row.value}` : row.value}`);
  }
  // Under the page's "From the catalog — not yet cited" caption.
  const uncited = CATALOG_LINE.charAt(0).toLowerCase() + CATALOG_LINE.slice(1);
  for (const stat of legacyStats(species)) {
    lines.push(`${stat.label} (${uncited}): ${stat.value}`);
  }
  const notes = species.care_notes?.trim();
  if (notes) lines.push(`Care notes: ${notes}`);
  return lines.join('\n');
}
