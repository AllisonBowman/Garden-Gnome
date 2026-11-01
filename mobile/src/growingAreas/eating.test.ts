import {
  EATEN_PART_GROUPS, eatingGroups, eatingLine, groupByEatenPart, leftOffNote,
} from './eating';
import type { Candidate } from '../api/growingAreas';
import type { EatenPart } from '../types';

// Read the area screen. Declared locally rather than pulling in @types/node,
// which conflicts with React Native's timer typings.
declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');
const readSrc = (rel: string): string => fs.readFileSync(path.join(__dirname, rel), 'utf8');

/** A candidate as the server sends it, with the parts a source names as
 *  eaten when there are any: `undefined` leaves the field off altogether,
 *  as a server older than the parts does. */
const candidate = (id: number, name: string, parts?: EatenPart[] | null): Candidate => ({
  species_id: id, common_name: name, scientific_name: `Genus ${id}`, score: 3, fits: [],
  ...(parts !== undefined ? { eaten_parts: parts } : {}),
});

const names = (rows: Candidate[]) => rows.map((c) => c.common_name);

describe('the groups an eat list falls into', () => {
  it('runs leaves, fruit, roots, seeds, flowers, stems, each headed in plain words', () => {
    expect(EATEN_PART_GROUPS).toEqual([
      { part: 'leaves', label: 'Leaves' },
      { part: 'fruit', label: 'Fruit' },
      { part: 'roots', label: 'Roots and tubers' },
      { part: 'seeds', label: 'Seeds and nuts' },
      { part: 'flowers', label: 'Flowers' },
      { part: 'stems', label: 'Stems and shoots' },
    ]);
  });
});

describe('grouping by the part eaten', () => {
  it('puts the groups in their own order, whatever order the rows arrive in', () => {
    const rows = [
      candidate(1, 'Nasturtium', ['flowers']),
      candidate(2, 'Taro', ['roots']),
      candidate(3, 'Sunflower', ['seeds']),
      candidate(4, 'Asparagus', ['stems']),
      candidate(5, 'Basil', ['leaves']),
      candidate(6, 'Tomato', ['fruit']),
    ];
    expect(groupByEatenPart(rows).map((g) => g.label)).toEqual([
      'Leaves', 'Fruit', 'Roots and tubers', 'Seeds and nuts', 'Flowers',
      'Stems and shoots',
    ]);
  });

  it('puts a species whose source names two parts under both', () => {
    const rows = [candidate(1, 'Squash', ['fruit', 'flowers']), candidate(2, 'Chives', ['leaves'])];
    expect(groupByEatenPart(rows).map((g) => [g.part, names(g.rows)])).toEqual([
      ['leaves', ['Chives']],
      ['fruit', ['Squash']],
      ['flowers', ['Squash']],
    ]);
  });

  it('leaves out a group nothing is in, rather than showing it empty', () => {
    const groups = groupByEatenPart([candidate(1, 'Mint', ['leaves']), candidate(2, 'Fig', ['fruit'])]);
    expect(groups.map((g) => g.part)).toEqual(['leaves', 'fruit']);
    expect(groupByEatenPart([])).toEqual([]);
  });

  it('keeps the server’s order within a group, never re-sorting it', () => {
    // The server ranks by what is confirmed, then A to Z; Sorrel here sits
    // above Arugula because more was confirmed for it.
    const rows = [
      candidate(1, 'Sorrel', ['leaves']),
      candidate(2, 'Arugula', ['leaves']),
      candidate(3, 'Kale', ['stems', 'leaves']),
    ];
    const [leaves, stems] = groupByEatenPart(rows);
    expect(names(leaves.rows)).toEqual(['Sorrel', 'Arugula', 'Kale']);
    expect(names(stems.rows)).toEqual(['Kale']);
  });

  it('puts a candidate with no part on record in no group', () => {
    expect(groupByEatenPart([candidate(1, 'Hosta', null), candidate(2, 'Fern')])).toEqual([]);
  });
});

describe('whether an area’s list is grouped', () => {
  const eatList = [candidate(1, 'Chives', ['leaves']), candidate(2, 'Tomato', ['fruit'])];

  it('groups the list of a space that asked for something to eat', () => {
    expect(eatingGroups(['edible'], eatList)?.map((g) => g.part)).toEqual(['leaves', 'fruit']);
    expect(eatingGroups(['pollinators', 'edible'], eatList)?.map((g) => g.part))
      .toEqual(['leaves', 'fruit']);
  });

  it('shows one list as before when the space did not ask for something to eat', () => {
    expect(eatingGroups(['pollinators'], eatList)).toBeNull();
    expect(eatingGroups([], eatList)).toBeNull();
    expect(eatingGroups(null, eatList)).toBeNull();
    expect(eatingGroups(undefined, eatList)).toBeNull();
  });

  it('shows one list as before when the server named no parts', () => {
    // A server older than the parts sends the rows without them.
    expect(eatingGroups(['edible'], [candidate(1, 'Chives'), candidate(2, 'Tomato')])).toBeNull();
  });

  it('never drops a row: one that no group holds keeps the whole list as one', () => {
    // A part a newer server can name and this build has no group for, or a
    // row with none: grouped, either would vanish from the list unsaid.
    const newer = [...eatList, candidate(3, 'Sugar maple', ['sap' as EatenPart])];
    expect(eatingGroups(['edible'], newer)).toBeNull();
    expect(eatingGroups(['edible'], [...eatList, candidate(4, 'Hosta', null)])).toBeNull();
  });

  it('has nothing to group when nothing is on the list', () => {
    expect(eatingGroups(['edible'], [])).toBeNull();
  });
});

describe('the eating line on a row', () => {
  it('is the server’s line as written, condition and all', () => {
    const taro = 'Roots are eaten, only after cooking. It is also recorded as poisonous to '
      + 'people. Check the source before eating any of it.';
    expect(eatingLine({ eating: taro })).toBe(taro);
    expect(eatingLine({ eating: `  ${taro}\n` })).toBe(taro);
  });

  it('is nothing when the server sends nothing, null, or a blank line', () => {
    expect(eatingLine({})).toBeNull();
    expect(eatingLine({ eating: null })).toBeNull();
    expect(eatingLine({ eating: '   ' })).toBeNull();
  });
});

describe('the count under an eat list', () => {
  it('says how many suit the spot but were left off, and why', () => {
    expect(leftOffNote(2)).toBe(
      '2 species fit this spot, but no source records any part of them as eaten, '
      + 'so they are not on this list.');
    expect(leftOffNote(31)).toBe(
      '31 species fit this spot, but no source records any part of them as eaten, '
      + 'so they are not on this list.');
  });

  it('keeps one species singular', () => {
    expect(leftOffNote(1)).toBe(
      'One species fits this spot, but no source records any part of it as eaten, '
      + 'so it is not on this list.');
  });

  it('says nothing when none were left off, or no count came', () => {
    expect(leftOffNote(0)).toBeNull();
    expect(leftOffNote(null)).toBeNull();
  });

  it('never calls a plant safe or edible, and says it without a dash', () => {
    const said = [...EATEN_PART_GROUPS.map((g) => g.label), leftOffNote(1)!, leftOffNote(9)!];
    for (const text of said) {
      expect(text).not.toMatch(/\b(safe|safely|edible|harmless)\b/i);
      expect(text).not.toMatch(/[—–]/);
    }
  });
});

// The screens that list an area's candidates, with the style each gives the
// hazard line, the eating line and the reasons under a candidate's name.
const LISTS: [string, string, string, string][] = [
  ['GrowingAreaDetailScreen.tsx', 'candidateHazard', 'candidateEating', 'candidateWhy'],
  ['AlmanacScreen.tsx', 'hazard', 'eating', 'confirmed'],
];

describe('the screens that list an area’s candidates', () => {
  it.each(LISTS)('%s says what is eaten under the hazard and over the reasons, whole',
    (file, hazardStyle, eatingStyle, whyStyle) => {
      const src = readSrc(`../screens/${file}`);
      const at = (style: string) => src.indexOf(`<Text style={styles.${style}}`);
      expect(src).toMatch(/eatingLine\(/);
      expect(at(hazardStyle)).toBeGreaterThan(-1);
      expect(at(eatingStyle)).toBeGreaterThan(at(hazardStyle));
      expect(at(whyStyle)).toBeGreaterThan(at(eatingStyle));
      // Never cut: the part without its condition is a different claim.
      const element = src.slice(at(eatingStyle), src.indexOf('</Text>', at(eatingStyle)));
      expect(element).toMatch(/\{eating\}/);
      expect(element).not.toMatch(/numberOfLines|ellipsizeMode/);
    });

  it.each(LISTS)('%s says how many species an eat list left off', (file) => {
    expect(readSrc(`../screens/${file}`)).toMatch(/leftOffNote\([^)]*leftOff/);
  });

  it('groups the list on the area’s own screen and keeps the Almanac’s flat', () => {
    expect(readSrc('../screens/GrowingAreaDetailScreen.tsx'))
      .toMatch(/eatingGroups\(env\.goals, candidateRows\)/);
    expect(readSrc('../screens/AlmanacScreen.tsx')).not.toMatch(/eatingGroups|groupByEatenPart/);
  });

  it('reads every candidate as a page in the Almanac, cached apart from the first few', () => {
    // One key for both would hand a screen the other's list: the area
    // screen's first few where every candidate was wanted, or the reverse.
    const almanac = readSrc('../screens/AlmanacScreen.tsx');
    expect(almanac).toMatch(/fetchCandidatePage\(areaId as number, EVERY_CANDIDATE\)/);
    expect(almanac).toMatch(/queryKey: \['growingAreaCandidates', areaId, 'every'\]/);
    expect(readSrc('../screens/GrowingAreaDetailScreen.tsx'))
      .toMatch(/queryKey: \['growingAreaCandidates', growingAreaId, 'first', FIRST_FEW\]/);
  });

  it('shows the Almanac’s left-off count with its other notes, in their style', () => {
    const almanac = readSrc('../screens/AlmanacScreen.tsx');
    expect(almanac).toMatch(/\[\.\.\.uncheckedNotes\(area, candidates\), leftOffNote\(/);
    expect(almanac).toMatch(/notes\.map\(\(note, i\) => \(\s*<Text key=\{i\} style=\{styles\.caveat\}>/);
  });
});
