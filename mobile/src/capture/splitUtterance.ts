// Turns one spoken sentence about a garden into separate, groundable entries.
//
// "Twelve tomatoes along the south fence, a rosemary bush by the gate, and
//  three basil in pots"
//   -> [ {count: 12, phrase: 'tomatoes',      location: 'south fence'}
//      , {count: 1,  phrase: 'rosemary bush', location: 'gate'}
//      , {count: 3,  phrase: 'basil',         location: 'pots'} ]
//
// Why this exists: feeding a whole utterance to the species matcher fails
// badly. "three tomato plants" scores Jade Plant, Snake Plant and Nerve Plant
// above Tomatoes, because the word "plant" matches every houseplant whose name
// ends in it. Counts and place words drag the match the same way. Splitting the
// sentence into its parts, and matching only the species part, is what fixes it.
//
// Pure and dependency-free (no react-native / expo imports) so it unit-tests
// directly, matching the house pattern in streaks.ts and care/schedule.ts.
//
// This is the universal tier: it runs identically on every phone with no model
// and no network. An on-device model only earns its keep on messier speech.

/** One clause of a spoken description, ready to be grounded in the catalog. */
export interface ParsedEntry {
  /** The clause as spoken, kept so the UI can show what it heard. */
  raw: string;
  /** Best species phrasing to match on ("tomatoes"). */
  phrase: string;
  /**
   * Other phrasings worth scoring. "snake plant" is a real species while
   * "tomato plants" is not, so the caller scores every phrasing and keeps the
   * best — rather than this module guessing which words are droppable.
   */
  altPhrases: string[];
  /** How many, or null when unstated ("some basil"). */
  count: number | null;
  /** Where, or "" when unstated. */
  location: string;
}

const NUMBER_WORDS: Record<string, number> = {
  a: 1, an: 1, one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7,
  eight: 8, nine: 9, ten: 10, eleven: 11, twelve: 12, thirteen: 13,
  fourteen: 14, fifteen: 15, sixteen: 16, seventeen: 17, eighteen: 18,
  nineteen: 19, twenty: 20, thirty: 30, forty: 40, fifty: 50, sixty: 60,
  seventy: 70, eighty: 80, ninety: 90, hundred: 100,
  couple: 2, pair: 2, dozen: 12,
};

// Vague quantities. Deliberately NOT given a number — "a few" is not three, and
// inventing one would be the app asserting something the user didn't say. The
// count comes back null and the review row defaults to 1 for the user to edit.
const VAGUE_QUANTITIES = new Set(['some', 'few', 'several', 'many', 'lots', 'loads', 'bunch']);

// Openers people say before naming anything. Stripped so "I have six tomatoes"
// parses the same as "six tomatoes".
const LEAD_FILLERS = [
  'i have', 'i have got', 'ive got', 'i got', 'we have', 'weve got', 'we got',
  'there is', 'there are', 'theres', 'there s', 'thats', 'that is',
  'then', 'also', 'plus', 'and then', 'next', 'over here', 'here',
  'this is', 'these are', 'its', 'it is',
];

// Generic growth-form nouns. Dropped only to make an ALTERNATIVE phrasing —
// never removed outright, because "Snake Plant", "Rubber Plant" and "Money
// Tree" are real catalog names where the word is the species, not a filler.
const FORM_NOUNS = [
  'plant', 'plants', 'bush', 'bushes', 'shrub', 'shrubs', 'tree', 'trees',
  'vine', 'vines', 'seedling', 'seedlings', 'start', 'starts', 'cutting',
  'cuttings', 'clump', 'clumps', 'row', 'rows', 'patch', 'bed',
];

// Words that begin a place phrase. Matched only after the species words, so
// "in pots" is a location while "Lily of the Valley" survives intact.
const LOCATION_PREPS = [
  'along', 'alongside', 'beside', 'behind', 'between', 'beneath', 'underneath',
  'under', 'near', 'nearest', 'next to', 'by', 'in', 'inside', 'on', 'at',
  'around', 'against', 'outside', 'over', 'across', 'up', 'down', 'toward',
  'towards', 'past', 'opposite', 'front of', 'back of',
];

/** Lowercase, strip punctuation that isn't a clause boundary, collapse spaces. */
function tidy(s: string): string {
  return (s || '')
    .toLowerCase()
    .replace(/[''`]/g, '')
    .replace(/[^a-z0-9,;\n]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Split a sentence into clauses on commas, semicolons, newlines and "and". */
function toClauses(text: string): string[] {
  return tidy(text)
    .split(/[,;\n]+|\band\b/)
    .map((c) => c.trim())
    .filter(Boolean);
}

function stripLeadFillers(clause: string): string {
  let out = clause;
  let changed = true;
  // Loop because people stack them: "and then I have six tomatoes".
  while (changed) {
    changed = false;
    for (const f of LEAD_FILLERS) {
      if (out === f) return '';
      if (out.startsWith(`${f} `)) {
        out = out.slice(f.length + 1);
        changed = true;
      }
    }
  }
  return out;
}

/** Read a leading quantity, returning the count and the rest of the clause. */
function takeCount(clause: string): { count: number | null; rest: string } {
  const words = clause.split(' ').filter(Boolean);
  if (!words.length) return { count: null, rest: '' };

  // Digits: "12 tomatoes"
  const asDigits = words[0].match(/^(\d+)$/);
  if (asDigits) {
    return { count: Number(asDigits[1]), rest: words.slice(1).join(' ') };
  }

  // "a few basil" / "some kale" — quantity acknowledged but left unstated.
  if (words[0] === 'a' && words[1] && VAGUE_QUANTITIES.has(words[1])) {
    return { count: null, rest: words.slice(2).join(' ') };
  }
  if (VAGUE_QUANTITIES.has(words[0])) {
    return { count: null, rest: words.slice(1).join(' ') };
  }

  // "a couple of tomatoes" / "a dozen tulips"
  if ((words[0] === 'a' || words[0] === 'an') && words[1] && NUMBER_WORDS[words[1]] > 1) {
    const rest = words.slice(2).join(' ').replace(/^of /, '');
    return { count: NUMBER_WORDS[words[1]], rest };
  }

  // "twenty four tomatoes" — compound tens.
  const first = NUMBER_WORDS[words[0]];
  if (first !== undefined) {
    const second = words[1] ? NUMBER_WORDS[words[1]] : undefined;
    if (first >= 20 && first < 100 && second !== undefined && second < 10) {
      return { count: first + second, rest: words.slice(2).join(' ') };
    }
    // "a"/"an" is only a count when something follows it.
    const rest = words.slice(1).join(' ').replace(/^of /, '');
    if (!rest) return { count: null, rest: clause };
    return { count: first, rest };
  }

  return { count: null, rest: clause };
}

/** Split the remainder into the species words and a trailing place phrase. */
function takeLocation(rest: string): { subject: string; location: string } {
  const words = rest.split(' ').filter(Boolean);
  for (let i = 1; i < words.length; i++) {
    const one = words[i];
    const two = `${words[i]} ${words[i + 1] ?? ''}`.trim();
    const matched = LOCATION_PREPS.includes(two) ? two
      : LOCATION_PREPS.includes(one) ? one
        : null;
    if (matched) {
      const subject = words.slice(0, i).join(' ');
      const location = words
        .slice(i + matched.split(' ').length)
        .join(' ')
        .replace(/^(the|a|an|my|our) /, '');
      // A preposition with nothing after it isn't a location.
      if (!subject || !location) continue;
      return { subject, location };
    }
  }
  return { subject: rest, location: '' };
}

/**
 * Build the phrasings worth scoring against the catalog, best guess first.
 * Dropping a trailing growth-form noun ("tomato plants" -> "tomato") is offered
 * as an alternative rather than applied, so real species names that end in one
 * ("Snake Plant") still score as themselves.
 */
function phrasings(subject: string): { phrase: string; altPhrases: string[] } {
  const words = subject.split(' ').filter(Boolean);
  const alts: string[] = [];
  if (words.length > 1 && FORM_NOUNS.includes(words[words.length - 1])) {
    alts.push(words.slice(0, -1).join(' '));
  }
  // Also try the last word alone ("cherry tomatoes" -> "tomatoes"), which
  // rescues varietal wording the catalog doesn't carry.
  if (words.length > 1) {
    const last = words[words.length - 1];
    if (!FORM_NOUNS.includes(last) && !alts.includes(last)) alts.push(last);
  }
  return { phrase: subject, altPhrases: alts };
}

/**
 * Split a spoken description into separate entries. Never invents a count and
 * never drops a clause silently: anything with words in it comes back, so the
 * caller can show "couldn't place this one" rather than quietly losing it.
 */
export function splitUtterance(text: string): ParsedEntry[] {
  const entries: ParsedEntry[] = [];
  for (const clause of toClauses(text)) {
    const stripped = stripLeadFillers(clause);
    if (!stripped) continue;
    const { count, rest } = takeCount(stripped);
    const { subject, location } = takeLocation(rest);
    if (!subject) continue;
    const { phrase, altPhrases } = phrasings(subject);
    entries.push({ raw: clause, phrase, altPhrases, count, location });
  }
  return entries;
}
