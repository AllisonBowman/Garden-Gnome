import { CareType } from '../types';

// Presentation for a care check on the calendar and the to-do list.
// `check` is what a row asks for — always a look, never the chore, because
// the app schedules checks, never actions (CONTEXT.md): no calendar knows
// whether a plant wants feeding today. `done` is the past tense a
// confirmation uses once the caretaker logs what they did. Water's check is
// the soil, and the "💧 Watered" quick-log button is one of the ways a check
// can end.
export const CARE_PRESENTATION: Record<CareType, {
  icon: string; check: (nickname: string) => string; done: string;
}> = {
  water:     { icon: '💧', check: (n) => `Check ${n}`,                    done: 'Watered'    },
  fertilize: { icon: '🌿', check: (n) => `See if ${n} wants feeding`,     done: 'Fertilized' },
  mist:      { icon: '💨', check: (n) => `See if ${n} wants misting`,     done: 'Misted'     },
  prune:     { icon: '✂️', check: (n) => `See if ${n} wants pruning`,     done: 'Pruned'     },
  repot:     { icon: '🪴', check: (n) => `Look at ${n}’s roots`,          done: 'Repotted'   },
  rotate:    { icon: '🔄', check: (n) => `See if ${n} wants turning`,     done: 'Rotated'    },
  clean:     { icon: '🧽', check: (n) => `See if ${n}’s leaves want a wipe`, done: 'Cleaned' },
  other:     { icon: '🌱', check: (n) => `Look in on ${n}`,               done: 'Cared for'  },
};

/** "💧 Check Ferny" — the phrase for a to-do row or calendar entry. */
export function careActionLabel(careType: CareType, nickname: string): string {
  const p = CARE_PRESENTATION[careType];
  return `${p.icon} ${p.check(nickname)}`;
}
