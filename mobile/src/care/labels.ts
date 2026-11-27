import { CareType } from '../types';
import { t } from '../i18n';

// Presentation for a care check on the calendar and the to-do list.
// `check` is what a row asks for — always a look, never the chore, because
// the app schedules checks, never actions (CONTEXT.md): no calendar knows
// whether a plant wants feeding today. `done` is the past tense a
// confirmation uses once the caretaker logs what they did. Water's check is
// the soil, and the "💧 Watered" quick-log button is one of the ways a check
// can end.
const ICONS: Record<CareType, string> = {
  water: '💧', fertilize: '🌿', mist: '💨', prune: '✂️',
  repot: '🪴', rotate: '🔄', clean: '🧽', other: '🌱',
};
const TYPES = Object.keys(ICONS) as CareType[];

export const CARE_PRESENTATION: Record<CareType, {
  icon: string; check: (nickname: string) => string; done: string;
}> = Object.fromEntries(TYPES.map((type) => [type, {
  icon: ICONS[type],
  check: (n: string) => t(`care.presentation.${type}.check`, { name: n }),
  done: t(`care.presentation.${type}.done`),
}])) as Record<CareType, { icon: string; check: (nickname: string) => string; done: string }>;

/** A care log row's title: "Water", "Repot". */
export function careActionName(careType: CareType): string {
  return TYPES.includes(careType) ? t(`care.actionNames.${careType}`) : careType;
}

/** "💧 Check Ferny" — the phrase for a to-do row or calendar entry. */
export function careActionLabel(careType: CareType, nickname: string): string {
  const p = CARE_PRESENTATION[careType];
  return `${p.icon} ${p.check(nickname)}`;
}
