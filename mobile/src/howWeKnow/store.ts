// What the "How we know" sheet shows. A screen hands its sections over as it
// opens the sheet; the sheet reads them back. A plain module, not route
// params, because sections carry whole explained values and React
// Navigation wants params small and serializable. Pure apart from the one
// slot of state.
import type { Explained } from '../types/site';

export interface HowWeKnowItem {
  /** "Sun", "First frost". */
  title?: string;
  explained: Explained;
}

export interface HowWeKnowSection {
  key: string;
  heading: string;
  /** Plain sentences, shown before the items. */
  lines: string[];
  items: HowWeKnowItem[];
}

let current: HowWeKnowSection[] = [];

export function setHowWeKnow(sections: HowWeKnowSection[]): void {
  current = sections.filter((s) => s.lines.length > 0 || s.items.length > 0);
}

export function getHowWeKnow(): HowWeKnowSection[] {
  return current;
}

/** A section from parts that may be missing. */
export function section(
  key: string, heading: string, lines: (string | null | undefined | false)[], items: HowWeKnowItem[] = [],
): HowWeKnowSection {
  return { key, heading, lines: lines.filter((l): l is string => typeof l === 'string' && l.trim() !== ''), items };
}
