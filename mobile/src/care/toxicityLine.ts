// The toxicity line shown with a picked species on Add plant.
//
// The server writes the sentence (app/services/toxicity.py describe): which
// parts, to whom, how serious, or that nothing is on record, which is never
// "safe". What the screen adds is emphasis, and that has to follow the
// sentence itself. It used to follow the pet flag alone, so a hazard to
// people (Poison Ivy, Bloodroot: toxic_to_pets false) sat in the muted note
// colour like "no toxicity recorded", and a severe pet hazard, whose sentence
// already starts with ⚠️, was shown "⚠️ ⚠️ Seriously toxic…".
//
// Pure on purpose (no React Native imports) so jest can pin it.
import { Species } from '../types';

const SIGN = '⚠️';

/**
 * Whether a server toxicity sentence records a hazard to anyone. The
 * sentences that don't all say so in their first sentence: "No toxicity is
 * recorded for…", "No toxicity verdict recorded for… yet", "ASPCA records no
 * toxicity to pets for…". Anything else names someone at risk. A sentence
 * this can't place is read as a hazard: the cautious side to be wrong on.
 */
export function isHazardSentence(sentence: string): boolean {
  const s = sentence.trim();
  if (!s) return false;
  if (s.startsWith('⚠')) return true;  // the server's mark of a severe hazard
  const first = s.split(/[.!?](?:\s|$)/)[0];
  return !/\bno toxicity\b/i.test(first);
}

export interface ToxicityLine {
  text: string;
  /** Shown in the warning colour, behind one warning sign. */
  hazard: boolean;
}

/** What Add plant shows under a picked species, or null for nothing to say
 *  (an older server with no sentence and no flag). */
export function toxicityLine(
  species: Pick<Species, 'toxicity_description' | 'toxic_to_pets'>,
): ToxicityLine | null {
  const sentence = species.toxicity_description?.trim();
  if (sentence) {
    const hazard = isHazardSentence(sentence) || species.toxic_to_pets === true;
    // One sign, never two: a severe sentence arrives with its own.
    const text = hazard && !sentence.startsWith('⚠') ? `${SIGN} ${sentence}` : sentence;
    return { text, hazard };
  }
  // An older server sends only the flag.
  if (species.toxic_to_pets === true) return { text: `${SIGN} Toxic to pets.`, hazard: true };
  return null;
}
