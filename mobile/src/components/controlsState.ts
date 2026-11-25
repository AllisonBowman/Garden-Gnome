// The Controls row's rules, kept pure so they can be pinned.
import type { ReminderPrefs } from '../notifications/plan';

/** "Task reminders: On" when any kind of plant check is on. Turning the
 *  tile off turns every kind off; turning it on turns every kind on, and
 *  Settings keeps the per-kind switches. */
export function remindersOn(prefs: ReminderPrefs): boolean {
  return Object.values(prefs).some(Boolean);
}

/** Text scale (iOS Dynamic Type) from which the tiles stack in one column
 *  instead of two: from the first accessibility size up, or sooner, so a
 *  label 40 percent longer than the English still fits on two lines. */
export const STACK_FROM_FONT_SCALE = 1.3;

export function tilesStack(fontScale: number): boolean {
  return fontScale >= STACK_FROM_FONT_SCALE;
}
