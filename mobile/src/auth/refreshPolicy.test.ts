import {
  refreshVerdict, renewedTokens, responseStatus, SessionRenewalDeferred,
} from './refreshPolicy';

// The shape axios gives a failed request: `response` only when the server
// answered, with its status on it.
const answered = (status: number) => ({ isAxiosError: true, response: { status } });
const unanswered = (code: string) => ({ isAxiosError: true, code });

// --- only a refusal ends a session -----------------------------------------

test('a 401 from /auth/refresh signs the person out', () => {
  // garden-gnome/app/routers/auth.py answers every unknown, expired, reused
  // or revoked refresh token with exactly this.
  expect(refreshVerdict(answered(401))).toBe('signOut');
});

test('a 403 from /auth/refresh signs the person out', () => {
  expect(refreshVerdict(answered(403))).toBe('signOut');
});

// --- everything else keeps the session --------------------------------------
// Each of these says something about the network or the server, nothing about
// the token. The finding this pins: a 429 or a dropped connection used to wipe
// the keychain and send people back through Apple or Google sign-in.

test.each([429, 500, 502, 503, 504, 400, 404, 422])(
  'a %i from /auth/refresh keeps the session', (status) => {
    expect(refreshVerdict(answered(status))).toBe('keepSession');
  },
);

test.each(['ECONNABORTED', 'ETIMEDOUT', 'ERR_NETWORK'])(
  'a refresh that got no answer (%s) keeps the session', (code) => {
    expect(refreshVerdict(unanswered(code))).toBe('keepSession');
  },
);

test('a failure that is not an HTTP answer at all keeps the session', () => {
  expect(refreshVerdict(new Error('keychain locked'))).toBe('keepSession');
  expect(refreshVerdict(undefined)).toBe('keepSession');
  expect(refreshVerdict(null)).toBe('keepSession');
});

test('a status that is not a number is not read as one', () => {
  expect(responseStatus({ response: { status: '401' } })).toBeUndefined();
  expect(refreshVerdict({ response: { status: '401' } })).toBe('keepSession');
});

// --- a 200 must actually carry the tokens -----------------------------------

test('a refresh answer with both tokens is accepted', () => {
  expect(renewedTokens({ access_token: 'a', refresh_token: 'r', token_type: 'bearer' }))
    .toEqual({ access: 'a', refresh: 'r' });
});

test('a refresh answer missing either token is not stored', () => {
  expect(renewedTokens({ access_token: 'a' })).toBeNull();
  expect(renewedTokens({ refresh_token: 'r' })).toBeNull();
  expect(renewedTokens({ access_token: '', refresh_token: 'r' })).toBeNull();
  expect(renewedTokens(null)).toBeNull();
  expect(renewedTokens('<html>proxy error</html>')).toBeNull();
});

// --- the error a deferred renewal throws -------------------------------------

test('a deferred renewal is marked retryable and carries what went wrong', () => {
  const cause = answered(503);
  const err = new SessionRenewalDeferred(cause);
  expect(err).toBeInstanceOf(Error);
  expect(err.retryable).toBe(true);
  expect(err.reason).toBe(cause);
  expect(err.name).toBe('SessionRenewalDeferred');
});
