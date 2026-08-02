import { splitUtterance } from './splitUtterance';

describe('splitUtterance', () => {
  it('splits a whole spoken garden into counted, placed entries', () => {
    const out = splitUtterance(
      'Twelve tomatoes along the south fence, a rosemary bush by the gate, and three basil in pots',
    );
    expect(out).toHaveLength(3);
    expect(out[0]).toMatchObject({ count: 12, phrase: 'tomatoes', location: 'south fence' });
    expect(out[1]).toMatchObject({ count: 1, phrase: 'rosemary bush', location: 'gate' });
    expect(out[2]).toMatchObject({ count: 3, phrase: 'basil', location: 'pots' });
  });

  // The failure this module exists to fix: matching the whole clause put Jade
  // Plant, Snake Plant and Nerve Plant above Tomatoes.
  it('offers the form-noun-free phrasing for "three tomato plants"', () => {
    const [e] = splitUtterance('three tomato plants');
    expect(e.count).toBe(3);
    expect(e.phrase).toBe('tomato plants');
    expect(e.altPhrases).toContain('tomato');
  });

  // ...without breaking real species whose name ends in a form noun.
  it('keeps "snake plant" intact as a phrasing', () => {
    const [e] = splitUtterance('a snake plant');
    expect(e.count).toBe(1);
    expect(e.phrase).toBe('snake plant');
    expect(e.altPhrases).toContain('snake');
  });

  it('reads digits and spelled-out numbers, including compound tens', () => {
    expect(splitUtterance('12 tomatoes')[0].count).toBe(12);
    expect(splitUtterance('six tomatoes')[0].count).toBe(6);
    expect(splitUtterance('twenty four tomatoes')[0].count).toBe(24);
    expect(splitUtterance('a couple of tomatoes')[0].count).toBe(2);
    expect(splitUtterance('a dozen tulips')[0].count).toBe(12);
  });

  it('never invents a number for a vague quantity', () => {
    expect(splitUtterance('some kale')[0]).toMatchObject({ count: null, phrase: 'kale' });
    expect(splitUtterance('a few basil')[0]).toMatchObject({ count: null, phrase: 'basil' });
    expect(splitUtterance('several rosemary')[0].count).toBeNull();
  });

  it('strips conversational openers', () => {
    expect(splitUtterance('I have six tomatoes')[0]).toMatchObject({ count: 6, phrase: 'tomatoes' });
    expect(splitUtterance('and then there are three kale')[0]).toMatchObject({ count: 3, phrase: 'kale' });
  });

  it('treats a trailing preposition phrase as place, not species', () => {
    expect(splitUtterance('kale in the raised bed')[0]).toMatchObject({
      phrase: 'kale', location: 'raised bed',
    });
    expect(splitUtterance('lavender near the shed')[0].location).toBe('shed');
  });

  it('leaves a bare species alone', () => {
    expect(splitUtterance('rosemary')[0]).toMatchObject({
      count: null, phrase: 'rosemary', location: '',
    });
  });

  it('offers the head noun as an alternative for varietal wording', () => {
    const [e] = splitUtterance('cherry tomatoes');
    expect(e.phrase).toBe('cherry tomatoes');
    expect(e.altPhrases).toContain('tomatoes');
  });

  it('keeps the raw clause so the UI can show what it heard', () => {
    expect(splitUtterance('Twelve tomatoes along the south fence')[0].raw)
      .toBe('twelve tomatoes along the south fence');
  });

  it('returns nothing for empty or filler-only input', () => {
    expect(splitUtterance('')).toEqual([]);
    expect(splitUtterance('   ')).toEqual([]);
    expect(splitUtterance('i have')).toEqual([]);
  });
});
