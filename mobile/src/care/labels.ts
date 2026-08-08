import { CareType } from '../types';

// Presentation for a care action on the calendar and the to-do list.
// `verb` is the imperative on a to-do row; `done` is the past tense a
// confirmation uses. Water's verb is *Check*, not *Water*: the to-do asks for
// the finger test, and the "💧 Watered" quick-log button is one of the ways a
// check can end.
export const CARE_PRESENTATION: Record<CareType, { icon: string; verb: string; done: string }> = {
  water:     { icon: '💧', verb: 'Check',    done: 'Watered'    },
  fertilize: { icon: '🌿', verb: 'Fertilize', done: 'Fertilized' },
  mist:      { icon: '💨', verb: 'Mist',      done: 'Misted'     },
  prune:     { icon: '✂️', verb: 'Prune',     done: 'Pruned'     },
  repot:     { icon: '🪴', verb: 'Inspect',   done: 'Repotted'   },
  rotate:    { icon: '🔄', verb: 'Rotate',    done: 'Rotated'    },
  clean:     { icon: '🧽', verb: 'Clean',     done: 'Cleaned'    },
  other:     { icon: '🌱', verb: 'Care for',  done: 'Cared for'  },
};

/** "💧 Water Ferny" — the action phrase for a to-do row or calendar entry. */
export function careActionLabel(careType: CareType, nickname: string): string {
  const p = CARE_PRESENTATION[careType];
  return `${p.icon} ${p.verb} ${nickname}`;
}
