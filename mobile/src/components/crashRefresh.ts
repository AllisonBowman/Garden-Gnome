import type { QueryClient } from '@tanstack/react-query';

// What "Try again" on a crashed screen does to the server data the app holds.
//
// A malformed server answer is the likeliest cause of a render crash, so the
// screen that crashed must not simply redraw from the same cache. But it used
// to reset every query in the cache: every other tab, still mounted and
// showing good content, went back to its spinner and asked for everything
// again (the whole catalog, the garden's per-plant fan-out), and with no
// signal those tabs fell to their first-load error, their data gone.
//
// When a boundary shows its card, the screen under it unmounts, so the
// queries only it was reading have nobody watching them any more. Those are
// reset: the screen fetches them fresh when it is drawn again. A query some
// other mounted screen is also showing is refreshed in place instead: its
// data stays on screen while it is asked for again, and stays there if the
// asking fails. The crashed screen is redrawn once that refresh has come
// back, so it doesn't redraw from the answer it crashed on, but never later
// than WAIT_MS: a server still waking up shouldn't hold the card on screen.
//
// Pure on purpose (no React Native imports) so jest can drive it against a
// real query cache.

/** The longest "Try again" waits for the refresh before redrawing anyway. */
export const WAIT_MS = 8_000;

type Refreshable = Pick<QueryClient, 'resetQueries' | 'invalidateQueries'>;

export async function refreshAfterCrash(
  queryClient: Refreshable,
  waitMs: number = WAIT_MS,
): Promise<void> {
  const refresh = Promise.all([
    // Nobody is showing these, the crashed screen's own among them.
    queryClient.resetQueries({ type: 'inactive' }),
    // On another screen too: ask again, keep what's shown meanwhile.
    queryClient.invalidateQueries({ type: 'active' }),
  ]);
  let timer: ReturnType<typeof setTimeout> | undefined;
  const enough = new Promise<void>((resolve) => { timer = setTimeout(resolve, waitMs); });
  try {
    await Promise.race([refresh.then(() => undefined, () => undefined), enough]);
  } finally {
    clearTimeout(timer);
  }
}
