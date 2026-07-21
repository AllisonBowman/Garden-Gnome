import axios from 'axios';

/**
 * Turn a failed request into something worth showing a caretaker.
 *
 * The server's 503 `detail` is user-presentable by construction: advisor and
 * vision failures raise AdvisorUnavailable / VisionUnavailable, whose message
 * is written for an end user while the technical cause (connection refused,
 * model not pulled, missing key) goes to the server log. So when a `detail`
 * is present we show it verbatim.
 *
 * Anything else — a network drop, a 500, a timeout — gets the caller's
 * fallback. We never synthesize setup instructions or name a backend: a
 * caretaker cannot act on "check the backend connection", and App Review
 * reads it as unfinished software.
 */
export function serverMessage(err: unknown, fallback: string): string {
  if (!axios.isAxiosError(err)) return fallback;
  const detail = err.response?.data?.detail;
  return typeof detail === 'string' && detail.trim() ? detail : fallback;
}
