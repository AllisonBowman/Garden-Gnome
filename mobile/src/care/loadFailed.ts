// What a screen says when a load failed, and when it says it.
//
// A failed request used to leave the detail screens on a spinner forever
// (`isLoading || !data` stays true once the query errors) and the catalog
// tabs on text with nothing to tap; a cold server or a dropped signal then
// looked like a broken app. Each screen now says it couldn't load, names no
// backend, and offers to try again.
//
// Two rules on top of that. A screen that already has something to show
// keeps showing it when a later refresh fails (the app refreshes on its own
// when it comes back to the foreground, often with no signal), with one
// small line saying the refresh didn't go through. And the reason given
// fits the failure: "check your connection" only when the server was never
// reached, since a server that answered with a problem, or a plant removed
// on another phone, is not the caretaker's connection to fix.
//
// Pure on purpose (no React Native imports) so jest can pin it.
import axios from 'axios';
import { t } from '../i18n';

export const LOAD_FAILED = {
  emoji: '🌧️',
  /** The server was never reached: no signal, or no answer in time. */
  body: t('care.loadFailed.body'),
  /** The server answered that the thing isn't there. */
  gone: t('care.loadFailed.gone'),
  /** The server answered, with a problem of its own. */
  answered: t('care.loadFailed.answered'),
  /** Not a network failure at all. */
  other: t('care.loadFailed.other'),
  action: t('care.loadFailed.action'),
} as const;

/** The one line a screen shows over content it kept after a refresh failed. */
export const REFRESH_FAILED = {
  line: t('care.loadFailed.refreshLine'),
  action: t('care.loadFailed.action'),
} as const;

// The things a screen names in its heading. A caller may pass one of these
// English phrases (or the key) and get it in the app's language; anything
// else is used as given, so a caller can pass its own translated phrase.
const LOAD_FAILED_WHAT = {
  'this plant': 'plant',
  'this species': 'species',
  'the catalog': 'catalog',
  'this growing area': 'area',
  'the Almanac': 'almanac',
} as const;
type LoadFailedWhat = (typeof LOAD_FAILED_WHAT)[keyof typeof LOAD_FAILED_WHAT];
const WHAT_KEYS: readonly string[] = Object.values(LOAD_FAILED_WHAT);

/** The heading for a screen about one thing: "Couldn’t load this plant". */
export function loadFailedTitle(what: string): string {
  const key = (LOAD_FAILED_WHAT as Record<string, LoadFailedWhat>)[what]
    ?? (WHAT_KEYS.includes(what) ? (what as LoadFailedWhat) : undefined);
  const phrase = key ? t(`care.loadFailed.what.${key}`) : what;
  return t('care.loadFailed.title', { what: phrase });
}

/** Why a load failed, as far as it matters to the person reading. */
export type LoadFailure = 'unreached' | 'gone' | 'answered' | 'other';

export function loadFailure(err: unknown): LoadFailure {
  if (err == null) return 'unreached';
  if (axios.isAxiosError(err)) {
    const status = err.response?.status;
    if (status === undefined) return 'unreached';
    return status === 404 ? 'gone' : 'answered';
  }
  // A session that couldn't be renewed just now (api/client.ts) is a
  // request that didn't get through, and says so.
  if ((err as { retryable?: unknown }).retryable === true) return 'unreached';
  return 'other';
}

/** The body for a screen whose first load failed. `shows` is whether the
 *  screen is about one thing (a plant, which can be removed) or a whole list
 *  (the catalog, which can't, so a 404 there is a problem like any other). */
export function loadFailedBody(err: unknown, shows: 'one' | 'list' = 'one'): string {
  const kind = loadFailure(err);
  if (kind === 'gone' && shows === 'list') return LOAD_FAILED.answered;
  return {
    unreached: LOAD_FAILED.body,
    gone: LOAD_FAILED.gone,
    answered: LOAD_FAILED.answered,
    other: LOAD_FAILED.other,
  }[kind];
}

/** What a list says after "Couldn’t load your plants." A list isn't removed
 *  on another phone, so a 404 there is the server's problem like any other. */
export function loadFailedAdvice(err: unknown): string {
  const kind = loadFailure(err);
  if (kind === 'unreached') return t('care.loadFailed.adviceUnreached');
  if (kind === 'other') return t('care.loadFailed.adviceOther');
  return LOAD_FAILED.answered;
}

/** What to draw: the content whenever there is some, even when a refresh
 *  just failed; the error only when there is nothing to show; otherwise a
 *  spinner. */
export type LoadView = 'loading' | 'failed' | 'shown';

export function loadView(hasData: boolean, isError: boolean): LoadView {
  if (hasData) return 'shown';
  return isError ? 'failed' : 'loading';
}
