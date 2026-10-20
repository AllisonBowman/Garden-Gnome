import axios from 'axios';

/**
 * Turn a failed request into something worth showing a caretaker.
 *
 * The server's 503 `detail` is user-presentable by construction: advisor and
 * vision failures raise AdvisorUnavailable / VisionUnavailable, whose message
 * is written for an end user while the technical cause (connection refused,
 * model not pulled, missing key) goes to the server log. So a 503's `detail`
 * is shown verbatim, and only a 503's.
 *
 * Every other answer's detail is written for whoever reads the server's
 * code: a 400 "species_id does not exist", a 404 "Growing area not found", a
 * 500 "Plant's species missing". Those, and a network drop or a timeout, get
 * the caller's fallback. We never synthesize setup instructions or name a
 * backend: a caretaker cannot act on "check the backend connection", and App
 * Review reads it as unfinished software.
 */
export function serverMessage(err: unknown, fallback: string): string {
  if (!axios.isAxiosError(err) || err.response?.status !== 503) return fallback;
  const detail = err.response.data?.detail;
  return typeof detail === 'string' && detail.trim() ? detail.trim() : fallback;
}

/** Statuses that say "not right now" rather than "no": asking again a moment
 *  later can succeed. 502-504 are what Fly's proxy answers while a machine
 *  that scaled to zero is still booting. */
const PASSING_STATUSES = new Set([408, 429, 500, 502, 503, 504]);

/**
 * Whether a failed request is worth one automatic retry.
 *
 * Yes for a dropped connection, a timeout, a server that is busy or still
 * waking up, and a session that couldn't be renewed just now. No for an
 * answer that will be the same next time (a 404, a 422, a refusal), and for
 * a bug in our own code: retrying those only makes the person wait twice as
 * long for the same error.
 */
export function isRetryableError(err: unknown): boolean {
  if ((err as { retryable?: unknown } | null)?.retryable === true) return true;
  if (!axios.isAxiosError(err)) return false;
  const status = err.response?.status;
  if (status === undefined) return true;  // never reached the server, or no answer in time
  return PASSING_STATUSES.has(status);
}

/**
 * React Query's retry rule for every query in the app: one automatic retry,
 * and only for a failure that can pass. `failureCount` is how many attempts
 * have failed before this one (0 after the first).
 */
export function retryOnceIfPassing(failureCount: number, err: unknown): boolean {
  return failureCount < 1 && isRetryableError(err);
}

/**
 * Whether the server answered at all. A save that failed with an answer (the
 * server turned it down) must not be reported as "couldn't reach the server".
 */
export function serverAnswered(err: unknown): boolean {
  return axios.isAxiosError(err) && err.response !== undefined;
}
