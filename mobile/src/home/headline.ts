import { FrostRisk } from '../types/site';
import { parseServerDate } from '../api/serverDate';
import { startOfDay } from '../care/schedule';

// Home's headline: one plain sentence about today and the season. The server
// writes it when it has the plan; this picks one when it gives none (the
// feature is off, or it sent an empty string). Pure and dated by `today`, so
// it can be pinned.
//
// What it may say is only what the data shows: a frost or freeze in the
// forecast, the number of things due, or that nothing is due. It never names
// a season it has not been told about.

export interface HeadlineDay {
  date: string;
  low_f?: number | null;
  /** From the new forecast. The older weather route has only the low. */
  frost_risk?: FrostRisk | null;
}

export interface HeadlineInput {
  serverHeadline?: string | null;
  days: HeadlineDay[];
  careDue: number;
  openSeasonTasks: number;
  today?: Date;
}

/** How far ahead a frost is worth leading with, in days from today. */
export const FROST_LOOKAHEAD_DAYS = 3;

const WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

/** The risk a forecast low carries, when the forecast does not say:
 *  32 °F and under is a freeze, 28 °F and under a hard freeze, and up to
 *  36 °F frost is possible on clear, still nights. */
export function riskFromLow(low: number | null | undefined): FrostRisk {
  if (low == null) return 'none';
  if (low <= 28) return 'hard_freeze';
  if (low <= 32) return 'freeze';
  if (low <= 36) return 'frost';
  return 'none';
}

const RISK_PHRASE: Record<Exclude<FrostRisk, 'none'>, string> = {
  frost: 'Frost is possible',
  freeze: 'A freeze is possible',
  hard_freeze: 'A hard freeze is possible',
};

/** "today", "tomorrow", "Thursday". */
export function dayWord(day: Date, today: Date): string {
  const diff = Math.round((startOfDay(day).getTime() - startOfDay(today).getTime()) / 86_400_000);
  if (diff === 0) return 'today';
  if (diff === 1) return 'tomorrow';
  return WEEKDAYS[day.getDay()];
}

/** "tonight", "tomorrow night", "Thursday night". */
export function nightWord(day: Date, today: Date): string {
  const word = dayWord(day, today);
  return word === 'today' ? 'tonight' : `${word} night`;
}

/** The first frost-risk night in the lookahead, or null. */
export function nextFrostNight(
  days: HeadlineDay[], today: Date = new Date(),
): { date: Date; risk: Exclude<FrostRisk, 'none'> } | null {
  const start = startOfDay(today).getTime();
  const end = start + FROST_LOOKAHEAD_DAYS * 86_400_000;
  const dated = days
    .map((d) => ({ d, at: parseServerDate(d.date) }))
    .filter((x): x is { d: HeadlineDay; at: Date } => x.at != null)
    .filter((x) => x.at.getTime() >= start && x.at.getTime() < end)
    .sort((a, b) => a.at.getTime() - b.at.getTime());
  for (const { d, at } of dated) {
    const risk = d.frost_risk ?? riskFromLow(d.low_f);
    if (risk !== 'none') return { date: at, risk };
  }
  return null;
}

function dueSentence(careDue: number, openSeasonTasks: number): string | null {
  const total = careDue + openSeasonTasks;
  if (total === 0) return null;
  if (openSeasonTasks === 0) {
    return careDue === 1 ? '1 plant is worth a look.' : `${careDue} plants are worth a look.`;
  }
  return total === 1 ? '1 thing to do this week.' : `${total} things to do this week.`;
}

export function pickHeadline(input: HeadlineInput): string {
  const server = input.serverHeadline?.trim();
  if (server) return server;
  const today = input.today ?? new Date();
  const parts: string[] = [];
  const frost = nextFrostNight(input.days, today);
  if (frost) parts.push(`${RISK_PHRASE[frost.risk]} ${nightWord(frost.date, today)}.`);
  const due = dueSentence(input.careDue, input.openSeasonTasks);
  if (due) parts.push(due);
  if (parts.length === 0) return 'Nothing needs you today.';
  return parts.join(' ');
}
