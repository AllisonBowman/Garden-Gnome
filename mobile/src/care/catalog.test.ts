import { aToZ, byCommonName, catalogCollation, foldName, matchesQuery } from './catalog';
import { Species } from '../types';

const sp = (id: number, common: string, scientific = 'Testus', over: Partial<Species> = {}) => (
  { id, common_name: common, scientific_name: scientific, care_notes: '', ...over } as Species);

// --- A to Z -----------------------------------------------------------------
// The server sends the catalog in the order rows were added: Snake Plant,
// Pothos, Monstera… a thousand species with no order a person can browse.

test('the catalog lists A to Z by common name, ignoring case and accents', () => {
  const list = [
    sp(1, 'Snake Plant'), sp(2, 'pothos'), sp(3, 'Monstera'), sp(4, 'Ångel’s trumpet'),
    sp(5, 'aloe vera'),
  ];
  expect(aToZ(list).map((s) => s.common_name)).toEqual([
    'aloe vera', 'Ångel’s trumpet', 'Monstera', 'pothos', 'Snake Plant',
  ]);
});

test('the order is English collation, whatever locale the phone or runner is in', () => {
  // Under sv_SE or da_DK the runtime's default puts Å after Z; the catalog
  // is sorted in English on purpose, so the test above holds everywhere.
  expect(catalogCollation()).toMatch(/^en\b/);
});

test('ties break on the scientific name, then the id, so the order never shuffles', () => {
  const list = [
    sp(9, 'Blackberry', 'Rubus ulmifolius'), sp(3, 'Blackberry', 'Rubus fruticosus'),
    sp(7, 'Blackberry', 'Rubus fruticosus'),
  ];
  expect(aToZ(list).map((s) => s.id)).toEqual([3, 7, 9]);
  expect(aToZ([...list].reverse()).map((s) => s.id)).toEqual([3, 7, 9]);
});

test('numbers sort as numbers', () => {
  expect([sp(1, 'Fern 10'), sp(2, 'Fern 2')].sort(byCommonName).map((s) => s.common_name))
    .toEqual(['Fern 2', 'Fern 10']);
});

test('sorting leaves the list it was given alone', () => {
  const list = [sp(1, 'Zinnia'), sp(2, 'Aster')];
  aToZ(list);
  expect(list.map((s) => s.id)).toEqual([1, 2]);
});

// --- search -----------------------------------------------------------------
// Hybrids are stored both ways — "Citrus × paradisi" and "Fragaria x
// ananassa" — and nobody types the multiplication sign.

test('"x" and "×" are the same letter in a hybrid name', () => {
  const grapefruit = sp(1, 'Grapefruit', 'Citrus × paradisi');
  const strawberry = sp(2, 'Strawberry', 'Fragaria x ananassa');
  expect(matchesQuery(grapefruit, 'Citrus x paradisi')).toBe(true);
  expect(matchesQuery(grapefruit, 'citrus × paradisi')).toBe(true);
  expect(matchesQuery(strawberry, 'Fragaria × ananassa')).toBe(true);
  expect(matchesQuery(strawberry, 'fragaria x')).toBe(true);
});

test('a hybrid is found without its marker, and with an unspaced one', () => {
  expect(matchesQuery(sp(1, 'Grapefruit', 'Citrus × paradisi'), 'citrus paradisi')).toBe(true);
  expect(matchesQuery(sp(2, 'Leyland cypress', '×Hesperotropsis leylandii'), 'x hesperotropsis'))
    .toBe(true);
  expect(matchesQuery(sp(3, 'Leyland cypress', 'x Hesperotropsis leylandii'), 'hesperotropsis leylandii'))
    .toBe(true);
});

test('the accepted name finds a row held under an older one', () => {
  const s = sp(1, 'Snake Plant', 'Sansevieria trifasciata', {
    scientific_name_accepted: 'Dracaena trifasciata',
  });
  expect(matchesQuery(s, 'dracaena')).toBe(true);
  expect(matchesQuery(s, 'sansevieria')).toBe(true);
});

test('a plain word still matches as it always did, and only where it appears', () => {
  const phlox = sp(1, 'Creeping phlox', 'Phlox subulata');
  expect(matchesQuery(phlox, 'phlox')).toBe(true);
  expect(matchesQuery(phlox, 'x')).toBe(true); // the letter, in "phlox"
  expect(matchesQuery(phlox, 'fern')).toBe(false);
  expect(matchesQuery(phlox, '   ')).toBe(true);
});

test('folding lower-cases, single-spaces and writes the marker one way', () => {
  expect(foldName('  Citrus  ×paradisi ')).toBe('citrus x paradisi');
});
