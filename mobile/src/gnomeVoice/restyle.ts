import { isAvailable, generate } from '../../modules/plant-id';

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

const PERSONA =
  'You are a warm, whimsical garden gnome who lovingly tends houseplants. ' +
  'Rewrite the CARE FACTS below as one short, cozy note to the plant\'s owner ' +
  '(3–5 sentences, plain prose, no lists, no emoji). STRICT RULES: mention ' +
  'every care fact given and nothing more — do not add, guess, or change any ' +
  'care activity, schedule, or detail. Keep every number exactly as written. ' +
  'Do not give any care advice that is not in the facts.';

function buildPrompt(fact: string, nickname?: string): string {
  const plantLine = nickname ? `\nTHE PLANT'S NAME: ${nickname}` : '';
  return `${PERSONA}${plantLine}\n\nCARE FACTS:\n${fact}\n\nYour note:`;
}

// Care activities the model could plausibly invent. Stems, so "watering",
// "fertilise"/"fertilize", "repotted" etc. all match.
const CARE_STEMS = [
  'water', 'fertili', 'feed', 'mist', 'humidif', 'prune', 'trim', 'repot',
  'rotate', 'clean', 'toxic', 'poison',
];

/**
 * Heuristic drift check: flag restyled text that mentions a number or a care
 * activity that never appeared in the source fact. Deliberately conservative —
 * a false positive only means the user sees the plain rule-based text.
 */
export function driftsFromFact(fact: string, styled: string): boolean {
  const factLower = fact.toLowerCase();
  const styledLower = styled.toLowerCase();

  // Any digit sequence in the styled text must literally exist in the fact.
  const factNumbers = new Set(factLower.match(/\d+/g) ?? []);
  for (const num of styledLower.match(/\d+/g) ?? []) {
    if (!factNumbers.has(num)) return true;
  }

  // Any care-activity stem in the styled text must also be in the fact.
  for (const stem of CARE_STEMS) {
    if (styledLower.includes(stem) && !factLower.includes(stem)) return true;
  }

  // Sanity bounds: empty or rambling output is a fallback, not a feature.
  const trimmed = styled.trim();
  if (trimmed.length === 0) return true;
  if (trimmed.length > Math.max(600, fact.length * 4)) return true;

  return false;
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
    if (driftsFromFact(fact, trimmed)) return flat;
    return { text: trimmed, styled: true };
  } catch {
    return flat;
  }
}
