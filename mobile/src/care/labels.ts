import { CareType } from '../types';

// Presentation for a care action on the calendar and the to-do list. Emoji and
// imperative verbs match the quick-log buttons on PlantDetailScreen so a
// "💧 Water" to-do reads the same as the "💧 Watered" button that clears it.
export const CARE_PRESENTATION: Record<CareType, { icon: string; verb: string }> = {
  water:     { icon: '💧', verb: 'Water'     },
  fertilize: { icon: '🌿', verb: 'Fertilize' },
  mist:      { icon: '💨', verb: 'Mist'      },
  prune:     { icon: '✂️', verb: 'Prune'     },
  repot:     { icon: '🪴', verb: 'Repot'     },
  rotate:    { icon: '🔄', verb: 'Rotate'    },
  clean:     { icon: '🧽', verb: 'Clean'     },
  other:     { icon: '🌱', verb: 'Care for'  },
};

/** "💧 Water Ferny" — the action phrase for a to-do row or calendar entry. */
export function careActionLabel(careType: CareType, nickname: string): string {
  const p = CARE_PRESENTATION[careType];
  return `${p.icon} ${p.verb} ${nickname}`;
}
