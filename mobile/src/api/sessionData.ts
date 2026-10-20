import { forgetGardenLoad } from './plants';

/** The one part of a QueryClient this needs, so a test can pass its own. */
interface ClearableCache {
  clear(): void;
}

/**
 * What one account had loaded must not show to the next one to sign in on
 * this phone, even for the 30 seconds it would still count as fresh.
 *
 * Two caches hold it: React Query's, and the shared garden load in
 * api/plants.ts, which lives outside React Query so the to-do list, the
 * streaks and the reminder planner can share one fan-out. Clearing only the
 * first left a load still running from the last account for the next one to
 * join. Called whenever the session ends, however it ends.
 */
export function dropSessionData(queryClient: ClearableCache): void {
  forgetGardenLoad();
  queryClient.clear();
}
