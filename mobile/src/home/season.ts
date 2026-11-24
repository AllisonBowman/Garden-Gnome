import { SeasonEventStatus, SeasonEventSummary, ProfileStatus } from '../types/site';
import { t } from '../i18n';

// Words for "The season ahead" and for a land profile still being read. Pure.

export const EVENT_STATUS_WORDS: Record<SeasonEventStatus, string> = {
  happened: t('home.eventStatus.happened'),
  happening: t('home.eventStatus.happening'),
  forecast: t('home.eventStatus.forecast'),
  expected: t('home.eventStatus.expected'),
  typically_around: t('home.eventStatus.typically_around'),
  done: t('home.eventStatus.done'),
  not_needed: t('home.eventStatus.not_needed'),
};

/** How many events "The season ahead" lists on Home; Season has the rest. */
export const SEASON_AHEAD_ROWS = 4;

/** The next few events, in date order (undated ones after, as sent). */
export function seasonAhead(
  events: SeasonEventSummary[], max: number = SEASON_AHEAD_ROWS,
): SeasonEventSummary[] {
  return events
    .map((e, i) => ({ e, i }))
    .sort((a, b) => {
      const x = a.e.sort_date ?? '';
      const y = b.e.sort_date ?? '';
      if (x && y && x !== y) return x < y ? -1 : 1;
      if (x && !y) return -1;
      if (!x && y) return 1;
      return a.i - b.i;
    })
    .slice(0, max)
    .map(({ e }) => e);
}

/** A line while the land is still being read, or null once it is done. */
export function profileProgressLine(status: ProfileStatus | null | undefined): string | null {
  if (!status) return null;
  const busy = (s: string) => s === 'pending' || s === 'building';
  if (busy(status.fast)) return t('home.progress.fast');
  if (busy(status.background)) {
    return t('home.progress.background');
  }
  if (status.fast === 'failed' || status.background === 'failed'
    || status.fast === 'partial' || status.background === 'partial') {
    return t('home.progress.partial');
  }
  return null;
}
