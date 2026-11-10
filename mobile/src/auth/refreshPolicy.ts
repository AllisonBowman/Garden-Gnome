// What a failed POST /auth/refresh means for the session.
//
// Only the server saying "this refresh token is no good" ends a session.
// garden-gnome/app/routers/auth.py answers every unknown, expired, reused or
// revoked refresh token with a 401, and a 403 means the same refusal. Anything
// else says nothing about the token: a 429 from the rate limit, a 5xx while a
// cold machine boots, a timeout, or no signal at the bottom of the garden. For
// those the tokens stay where they are and only the request that needed them
// fails, with an error the caller can retry. Signing someone out because the
// network blinked sends them back through Apple or Google for nothing, and
// drops whatever they had just tapped.
//
// Pure on purpose (no axios, no React Native) so jest can pin the rule.

export type RefreshVerdict = 'signOut' | 'keepSession';

/** The HTTP status the server answered with, when it answered at all. Read
 *  by shape rather than through axios so this module stays dependency-free. */
export function responseStatus(err: unknown): number | undefined {
  const status = (err as { response?: { status?: unknown } } | null)?.response?.status;
  return typeof status === 'number' ? status : undefined;
}

/** Decide what a failed refresh does to the session. */
export function refreshVerdict(err: unknown): RefreshVerdict {
  const status = responseStatus(err);
  return status === 401 || status === 403 ? 'signOut' : 'keepSession';
}

/** A successful refresh must hand back both tokens. A 200 without them is
 *  treated like any other passing failure: nothing is stored, nobody is
 *  signed out, and the next request tries again. */
export function renewedTokens(
  data: unknown,
): { access: string; refresh: string } | null {
  const d = data as { access_token?: unknown; refresh_token?: unknown } | null;
  if (typeof d?.access_token === 'string' && d.access_token
    && typeof d?.refresh_token === 'string' && d.refresh_token) {
    return { access: d.access_token, refresh: d.refresh_token };
  }
  return null;
}

/**
 * Thrown in place of a request's 401 when the session could not be renewed
 * just now but is still good. Callers treat it like a dropped connection:
 * show their own "try again" message and keep everything the person entered.
 * `retryable` is what the query retry policy reads.
 */
export class SessionRenewalDeferred extends Error {
  readonly retryable = true;
  /** What went wrong with the refresh itself (a timeout, a 429, a 5xx). */
  readonly reason: unknown;

  constructor(reason: unknown) {
    super("The session couldn't be renewed just now.");
    this.name = 'SessionRenewalDeferred';
    this.reason = reason;
  }
}
