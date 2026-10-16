// How the catalog is listed and searched: A to Z by common name, and found by
// any name it goes by. Pure, so the Species tab, the Almanac and the pickers
// list and find species the same way.
import { Species } from '../types';

// One collator for every comparison: locale-aware, so "Ångel's trumpet"
// sorts with the A's and "baby's breath" beside "Baby sage"; numeric, so
// "Fern 2" comes before "Fern 10".
const collator = new Intl.Collator(undefined, { sensitivity: 'base', numeric: true });

/** A to Z by common name, then scientific name, then id — so two rows that
 *  share a common name always come out in the same order. */
export function byCommonName(a: Species, b: Species): number {
  return collator.compare(a.common_name, b.common_name)
    || collator.compare(a.scientific_name, b.scientific_name)
    || a.id - b.id;
}

/** A sorted copy; the list the server sent is left as it came. */
export function aToZ(species: Species[]): Species[] {
  return [...species].sort(byCommonName);
}

/** A name folded for searching: lower case, single spaces, and the hybrid
 *  marker written one way. The catalog stores hybrids both as
 *  "Citrus × paradisi" and "Citrus x paradisi", and nobody types "×". */
export function foldName(text: string): string {
  return text.toLowerCase().replace(/×/g, ' x ').replace(/\s+/g, ' ').trim();
}

/** The folded name with a standalone hybrid marker dropped, so "citrus
 *  paradisi" finds "Citrus × paradisi" too. */
function withoutMarker(folded: string): string {
  return folded.split(' ').filter((w) => w !== 'x').join(' ');
}

/** Case-insensitive match across every name a species goes by — common,
 *  scientific and accepted — so "monstera" and "deliciosa" both find the
 *  same plant, and "x" and "×" are the same letter in a hybrid's name. */
export function matchesQuery(s: Species, query: string): boolean {
  const q = foldName(query);
  if (!q) return true;
  const bare = withoutMarker(q);
  const names = [s.common_name, s.scientific_name, s.scientific_name_accepted ?? '']
    .filter(Boolean)
    .map(foldName);
  return names.some((n) => n.includes(q) || (bare !== '' && withoutMarker(n).includes(bare)));
}
