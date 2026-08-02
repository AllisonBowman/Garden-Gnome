import { Species } from '../types';
import { matchSpecies } from '../photoId/fuzzyMatch';
import { splitUtterance } from './splitUtterance';
import { groundEntries, groundEntry, effectiveCount } from './ground';

// A slice of the real catalog chosen for its collisions: every houseplant here
// whose name ends in "Plant" is what "three tomato plants" used to match.
function sp(id: number, common: string, scientific = `Testus ${id}`): Species {
  return {
    id, common_name: common, scientific_name: scientific,
    light_need: 'bright_indirect', humidity_pct_min: 40, humidity_pct_max: 60,
    temp_f_min: 60, temp_f_max: 85, soil_type: 'loam', toxic_to_pets: false,
    care_notes: '',
  } as Species;
}

const CATALOG: Species[] = [
  sp(1, 'Snake Plant', 'Dracaena trifasciata'),
  sp(2, 'Jade Plant', 'Crassula ovata'),
  sp(3, 'Nerve Plant', 'Fittonia albivenis'),
  sp(4, 'ZZ Plant', 'Zamioculcas zamiifolia'),
  sp(5, 'Spider Plant', 'Chlorophytum comosum'),
  sp(6, 'Rubber Plant', 'Ficus elastica'),
  sp(7, 'Tomatoes', 'Solanum lycopersicum'),
  sp(8, 'Peppers', 'Capsicum annuum'),
  sp(9, 'Basil', 'Ocimum basilicum'),
  sp(10, 'Rosemary', 'Salvia rosmarinus'),
  sp(11, 'Kale', 'Brassica oleracea'),
  sp(12, 'Carrots', 'Daucus carota'),
  sp(13, 'Potatoes', 'Solanum tuberosum'),
  sp(14, 'Sweet Pea', 'Lathyrus odoratus'),
  sp(15, 'Mint', 'Mentha spicata'),
];

const top = (text: string) => {
  const [g] = groundEntries(splitUtterance(text), CATALOG);
  return g;
};

describe('grounding a spoken garden', () => {
  // The headline regression. Matching the whole clause put three houseplants
  // above Tomatoes and pushed Tomatoes off the list entirely.
  it('finds Tomatoes for "three tomato plants", where the raw clause does not', () => {
    const raw = matchSpecies('three tomato plants', CATALOG);
    expect(raw[0].species.common_name).not.toBe('Tomatoes');

    const g = top('three tomato plants');
    expect(g.candidates[0].species.common_name).toBe('Tomatoes');
    expect(g.tier).toBe('confident');
    expect(g.matchedPhrase).toBe('tomato');
    expect(effectiveCount(g.entry)).toBe(3);
  });

  // ...and the mirror case, which is why the form noun is offered as an
  // alternative rather than stripped: here the word IS the species.
  it('still finds Snake Plant for "a snake plant"', () => {
    const g = top('a snake plant');
    expect(g.candidates[0].species.common_name).toBe('Snake Plant');
    expect(g.matchedPhrase).toBe('snake plant');
  });

  it('finds Potatoes for "sweet potato" via the head noun', () => {
    const raw = matchSpecies('sweet potato', CATALOG);
    expect(raw[0].species.common_name).toBe('Sweet Pea'); // the old, wrong answer
    expect(top('sweet potato').candidates[0].species.common_name).toBe('Potatoes');
  });

  it('keeps every species from a six-plant sentence', () => {
    const grounded = groundEntries(
      splitUtterance('tomatoes, basil, rosemary, peppers, kale and carrots'),
      CATALOG,
    );
    expect(grounded).toHaveLength(6);
    expect(grounded.map((g) => g.candidates[0]?.species.common_name)).toEqual(
      ['Tomatoes', 'Basil', 'Rosemary', 'Peppers', 'Kale', 'Carrots'],
    );
  });

  it('carries counts and places through to the proposal', () => {
    const grounded = groundEntries(
      splitUtterance('twelve tomatoes along the south fence and three basil in pots'),
      CATALOG,
    );
    expect(grounded[0].entry).toMatchObject({ count: 12, location: 'south fence' });
    expect(grounded[0].candidates[0].species.common_name).toBe('Tomatoes');
    expect(grounded[1].entry).toMatchObject({ count: 3, location: 'pots' });
    expect(grounded[1].candidates[0].species.common_name).toBe('Basil');
  });

  it('defaults an unstated count to one rather than inventing a number', () => {
    const g = top('some kale');
    expect(g.entry.count).toBeNull();
    expect(effectiveCount(g.entry)).toBe(1);
  });

  it('keeps unmatchable clauses instead of dropping them', () => {
    const g = top('a jalapeno');
    expect(g.tier).toBe('none');
    expect(g.candidates).toEqual([]);
    expect(g.entry.raw).toBe('a jalapeno');
  });

  // Documented limitation, not a passing grade. "peppermint" scores Peppers
  // above Mint on character overlap alone, and splitting cannot help because
  // there is only one word to split. The review screen must therefore always
  // allow picking a different species by hand — this test exists so that
  // requirement doesn't get quietly dropped.
  it('still mis-scores "peppermint", so manual override stays mandatory', () => {
    const g = top('peppermint');
    expect(g.candidates[0].species.common_name).toBe('Peppers');
    expect(g.candidates.map((c) => c.species.common_name)).not.toContain('Mint');
  });

  it('prefers a reviewed row over an unreviewed one at the same score', () => {
    const unreviewed = { ...sp(20, 'Basil', 'Ocimum basilicum'), review_status: 'needs_review' as const };
    const reviewed = { ...sp(21, 'Basil', 'Ocimum basilicum'), review_status: 'approved' as const };
    const g = groundEntry(splitUtterance('basil')[0], [unreviewed, reviewed]);
    expect(g.candidates[0].species.id).toBe(21);
  });
});
