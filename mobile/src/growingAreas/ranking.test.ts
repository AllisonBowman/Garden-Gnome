import {
  FIRST_FEW, RANK_ORDER, cutNote, inRankOrder, listIntro, totalCount,
} from './ranking';
import type { Candidate } from '../api/growingAreas';

const candidate = (id: number, score: number): Candidate => ({
  species_id: id, common_name: `Species ${id}`, scientific_name: `Genus ${id}`,
  score, fits: [],
});

/** n candidates, all at one score — the shape of a list cut through a tie. */
const level = (n: number, score: number, from = 1) =>
  Array.from({ length: n }, (_, i) => candidate(from + i, score));

describe('the count the server sent', () => {
  it('is read from the header whatever case its name arrives in', () => {
    expect(totalCount({ 'x-total-count': '263' })).toBe(263);
    expect(totalCount({ 'X-Total-Count': '263' })).toBe(263);
    expect(totalCount({ 'x-total-count': 0 })).toBe(0);
  });

  it('is null, never a guess, when there is none or it cannot be read', () => {
    // A server older than the count sends no header at all.
    expect(totalCount({ 'content-type': 'application/json' })).toBeNull();
    expect(totalCount(undefined)).toBeNull();
    expect(totalCount('263')).toBeNull();
    for (const junk of ['', ' ', 'many', '-1', '2.5', '12abc']) {
      expect(totalCount({ 'x-total-count': junk })).toBeNull();
    }
  });
});

describe('the line over the list', () => {
  it('says how many qualify, what that means, and how they are ordered', () => {
    expect(listIntro(263, FIRST_FEW)).toBe(
      '263 species have nothing on record against this spot and at least one thing '
      + `confirmed. ${RANK_ORDER}`);
    expect(RANK_ORDER).toMatch(/A to Z/);
  });

  it('keeps a lone candidate singular, with no order to explain', () => {
    expect(listIntro(1, 1)).toBe(
      'One species has nothing on record against this spot and at least one thing confirmed.');
  });

  it('says only the order when the server sent no count', () => {
    expect(listIntro(null, 12)).toBe(RANK_ORDER);
    expect(listIntro(null, 1)).toBeNull();
  });

  it('has nothing to introduce when nothing qualifies', () => {
    expect(listIntro(0, 0)).toBeNull();
  });
});

describe('where the list stops', () => {
  it('says when the cut fell between equals, so twelve are not read as the best twelve', () => {
    const shown = level(FIRST_FEW, 6);
    const note = cutNote(shown, candidate(99, 6), 263);
    expect(note).toBe(
      'Showing 12 of 263. The next one has as much confirmed as the last one here, so '
      + 'where this list stops is down to the alphabet, not the evidence.');
  });

  it('says so when the cut fell where the evidence drops', () => {
    const shown = [...level(10, 6), ...level(2, 5, 11)];
    expect(cutNote(shown, candidate(99, 4), 40)).toBe(
      'Showing 12 of 40. Everything after these has less confirmed.');
  });

  it('is silent when nothing was left out', () => {
    expect(cutNote(level(7, 3), undefined, 7)).toBeNull();
    expect(cutNote(level(12, 3), undefined, 12)).toBeNull();
    expect(cutNote([], undefined, 0)).toBeNull();
  });

  it('still says the list is cut, without a total, when the server sent none', () => {
    expect(cutNote(level(12, 1), candidate(99, 1), null)).toBe(
      'Showing the first 12. The next one has as much confirmed as the last one here, so '
      + 'where this list stops is down to the alphabet, not the evidence.');
    // No count and nothing past the cut: no way to say anything was left out.
    expect(cutNote(level(12, 1), undefined, null)).toBeNull();
  });

  it('says only how much is shown when it cannot see past the cut', () => {
    expect(cutNote(level(12, 2), undefined, 30)).toBe('Showing 12 of 30.');
  });
});

describe('a longer list in the same order', () => {
  it('follows the server’s ranking, not the order the catalog arrived in', () => {
    const ranked = [candidate(30, 6), candidate(10, 6), candidate(20, 5)];
    const catalog = [{ id: 10 }, { id: 20 }, { id: 30 }];
    expect(inRankOrder(catalog, ranked).map((s) => s.id)).toEqual([30, 10, 20]);
  });

  it('keeps anything unranked after the ranked, in its own order, and changes nothing in place', () => {
    const ranked = [candidate(3, 2)];
    const catalog = [{ id: 1 }, { id: 2 }, { id: 3 }];
    expect(inRankOrder(catalog, ranked).map((s) => s.id)).toEqual([3, 1, 2]);
    expect(catalog.map((s) => s.id)).toEqual([1, 2, 3]);
  });
});
