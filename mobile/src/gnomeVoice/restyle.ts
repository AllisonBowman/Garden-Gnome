import { isAvailable, generate } from '../../modules/plant-id';
import { PERSONA_CONTRACT, appendSignOff } from './persona';

// Gnome voice: restyle already-determined care facts in a warm gnome persona
// using the same on-device model as photo ID (Apple Foundation Models on iOS,
// Gemini Nano on Android). The rule-based engine remains the sole source of
// factual content — this layer only changes tone, and falls back to the flat
// text whenever the device can't run the model or the output drifts from the
// facts it was given.

export interface GnomeVoiceResult {
  text: string;
  /** True when the on-device gnome persona produced the text; false = flat fallback. */
  styled: boolean;
}

function buildPrompt(fact: string, nickname?: string): string {
  const plantLine = nickname ? `\nTHE PLANT'S NAME: ${nickname}` : '';
  return `${PERSONA_CONTRACT}${plantLine}\n\nCARE FACTS:\n${fact}\n\nYour note:`;
}

// Care activities the model could plausibly invent. Stems, so "watering",
// "fertilise"/"fertilize", "repotted" etc. all match.
const CARE_STEMS = [
  'water', 'fertili', 'feed', 'mist', 'humidif', 'prune', 'trim', 'repot',
  'rotate', 'clean', 'toxic', 'poison',
];

// Cardinal number words, so a spelled-out number is checked against the fact
// exactly like a digit. Compounds ("thirty-five") resolve before standalone
// words, and both lists match longest-first so "seventeen" never lands as
// "seven". "a week"/"a day" are deliberately out of scope — the persona
// demands digits, and this normalization is belt-and-suspenders.
const ONES: Record<string, number> = {
  one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8,
  nine: 9, ten: 10, eleven: 11, twelve: 12, thirteen: 13, fourteen: 14,
  fifteen: 15, sixteen: 16, seventeen: 17, eighteen: 18, nineteen: 19,
};
const TENS: Record<string, number> = {
  twenty: 20, thirty: 30, forty: 40, fifty: 50, sixty: 60, seventy: 70,
  eighty: 80, ninety: 90,
};

const longestFirst = (words: string[]) =>
  [...words].sort((a, b) => b.length - a.length).join('|');

const TENS_ALT = longestFirst(Object.keys(TENS));
const ONES_ALT = longestFirst(Object.keys(ONES));

/** "thirty-five days" -> "35 days", so the digit-subset rule can see it. */
export function normalizeNumberWords(text: string): string {
  return text
    .replace(
      new RegExp(`\\b(${TENS_ALT})[\\s-]+(${ONES_ALT})\\b`, 'gi'),
      (_m, tens: string, ones: string) =>
        String(TENS[tens.toLowerCase()] + ONES[ones.toLowerCase()]),
    )
    .replace(new RegExp(`\\b(${TENS_ALT})\\b`, 'gi'),
      (_m, tens: string) => String(TENS[tens.toLowerCase()]))
    .replace(new RegExp(`\\b(${ONES_ALT})\\b`, 'gi'),
      (_m, ones: string) => String(ONES[ones.toLowerCase()]));
}

/** Why a restyle was rejected. Exported so tests can assert that a known-bad
 * output trips several *independent* checks, not one lucky regex. */
export type DriftReason =
  | 'empty'
  | 'too-long'
  | 'invented-number'
  | 'invented-care-activity'
  | 'placeholder'
  | 'first-person-care'
  | 'commitment'
  | 'letter-scaffolding';

/**
 * Every way the styled text departs from the facts it was given. Deliberately
 * conservative: each check may false-positive, and the only cost is that the
 * user sees the plain rule-based wording instead.
 */
export function driftReasons(fact: string, styled: string): DriftReason[] {
  const trimmed = styled.trim();
  if (trimmed.length === 0) return ['empty'];

  const reasons: DriftReason[] = [];
  const factLower = fact.toLowerCase();
  const styledLower = trimmed.toLowerCase();

  if (trimmed.length > Math.max(600, fact.length * 4)) reasons.push('too-long');

  // Every number in the styled text — digit or spelled — must be in the fact.
  const factNumbers = new Set(normalizeNumberWords(factLower).match(/\d+/g) ?? []);
  const styledNumbers = normalizeNumberWords(styledLower).match(/\d+/g) ?? [];
  if (styledNumbers.some((n) => !factNumbers.has(n))) reasons.push('invented-number');

  // Any care-activity stem in the styled text must also be in the fact.
  if (CARE_STEMS.some((s) => styledLower.includes(s) && !factLower.includes(s))) {
    reasons.push('invented-care-activity');
  }

  // A template artifact is never a valid note ("Love, [Your Name]").
  if (/\[[^\]]*\]|\{[^}]*\}/.test(trimmed)
      || /\b(your name|plant owner|insert)\b/i.test(trimmed)) {
    reasons.push('placeholder');
  }

  // The caretaker performs all care. "you watered it 2 days ago" is fine;
  // "I've watered it" and "I'll hold off on watering" are not. Scoped to the
  // sentence so an unrelated "I" elsewhere doesn't poison the whole note.
  const sentences = trimmed.split(/[.!?\n]+/);
  if (sentences.some((s) => /\bi\b/i.test(s)
      && CARE_STEMS.some((stem) => s.toLowerCase().includes(stem)))) {
    reasons.push('first-person-care');
  }

  // The restyle layer cannot know whether a reminder is actually scheduled,
  // so it may never say one is.
  const promises = /\bi(?:'ll|\s+will)\b[^.!?]*\b(send|remind|notify|alert)/i.test(trimmed);
  const styledReminds = /\b(reminders?|notifications?)\b/i.test(trimmed);
  const factReminds = /\b(reminders?|notifications?)\b/i.test(fact);
  if (promises || (styledReminds && !factReminds)) reasons.push('commitment');

  // The sign-off is appended by code, so any model-written greeting or
  // signature is scaffolding that shouldn't exist.
  const lines = trimmed.split('\n').map((l) => l.trim()).filter(Boolean);
  const greeting = lines.length > 0 && /^dear\b/i.test(lines[0]);
  const closing = lines.some((l) =>
    /^(love|sincerely|yours(?:\s+truly)?|warmly|fondly)\s*[,.]?$/i.test(l));
  if (greeting || closing) reasons.push('letter-scaffolding');

  return reasons;
}

/** Convenience wrapper: did the restyle drift at all? */
export function driftsFromFact(fact: string, styled: string): boolean {
  return driftReasons(fact, styled).length > 0;
}

/**
 * Restyle a rule-based advice string in the gnome's voice. Always resolves —
 * on any unavailability, error, or drift, the original flat text comes back
 * with styled=false so advice keeps working on every device.
 */
export async function gnomeVoice(fact: string, nickname?: string): Promise<GnomeVoiceResult> {
  const flat: GnomeVoiceResult = { text: fact, styled: false };
  try {
    if (!(await isAvailable())) return flat;
    const styled = await generate(buildPrompt(fact, nickname));
    if (!styled) return flat;
    const trimmed = styled.trim();
    // Guard the model's own words only — the sign-off is appended afterwards
    // so a code-written signature can never be mistaken for model drift.
    if (driftsFromFact(fact, trimmed)) return flat;
    return { text: appendSignOff(trimmed), styled: true };
  } catch {
    return flat;
  }
}
