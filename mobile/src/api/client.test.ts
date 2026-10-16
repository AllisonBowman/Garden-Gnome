// The real client against a simulated server: what a failed token refresh
// does to the session, and that concurrent requests still share one refresh.
//
// Both native modules are stubbed, the way tokenStorage.test.ts does it; the
// keychain stub keeps its values so the test can read what survived. Requests
// go through axios's adapter hook, so the interceptors under test are the
// ones the app runs.
jest.mock('react-native', () => ({ Platform: { OS: 'ios' } }));
jest.mock('expo-secure-store', () => {
  const values = new Map<string, string>();
  return {
    __values: values,
    getItemAsync: jest.fn(async (key: string) => values.get(key) ?? null),
    setItemAsync: jest.fn(async (key: string, value: string) => { values.set(key, value); }),
    deleteItemAsync: jest.fn(async (key: string) => { values.delete(key); }),
  };
});

import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import * as SecureStore from 'expo-secure-store';
import { apiClient, getBaseUrl, DEFAULT_BASE_URL } from './client';
import { isRetryableError } from './errorMessage';
import { onForcedSignOut } from '../auth/tokenStorage';
import { SessionRenewalDeferred } from '../auth/refreshPolicy';

const keychain = (SecureStore as unknown as { __values: Map<string, string> }).__values;

// ── the simulated server ─────────────────────────────────────────────────────

type Reply = { status: number; data?: unknown } | 'network' | 'timeout';

/** What POST /auth/refresh answers next. */
let refreshReply: () => Reply;
let refreshCalls = 0;
/** The access token the server currently accepts. */
let validAccess = 'access-new';

function pathOf(config: InternalAxiosRequestConfig): string {
  return (config.url ?? '').replace(config.baseURL ?? '', '').replace(DEFAULT_BASE_URL, '');
}

function route(config: InternalAxiosRequestConfig): Reply {
  const path = pathOf(config);
  if (path === '/auth/refresh') {
    refreshCalls += 1;
    return refreshReply();
  }
  const auth = String(config.headers?.Authorization ?? '');
  return auth === `Bearer ${validAccess}`
    ? { status: 200, data: [{ id: 1, nickname: 'Fern' }] }
    : { status: 401, data: { detail: 'Could not validate credentials' } };
}

beforeAll(() => {
  axios.defaults.adapter = async (config: InternalAxiosRequestConfig) => {
    // Let concurrent callers pile up before anyone is answered, the way a
    // launch fan-out does against a slow server.
    await new Promise((r) => setTimeout(r, 5));
    const reply = route(config);
    if (reply === 'network') {
      throw new AxiosError('Network Error', AxiosError.ERR_NETWORK, config);
    }
    if (reply === 'timeout') {
      throw new AxiosError('timeout of 15000ms exceeded', AxiosError.ECONNABORTED, config);
    }
    const response: AxiosResponse = {
      data: reply.data, status: reply.status, statusText: '', headers: {}, config,
    };
    if (reply.status >= 200 && reply.status < 300) return response;
    throw new AxiosError(
      `Request failed with status code ${reply.status}`,
      AxiosError.ERR_BAD_RESPONSE, config, null, response,
    );
  };
});

let signOuts = 0;
let unsubscribe: () => void;

beforeEach(() => {
  keychain.clear();
  // Signed in, holding an access token the server no longer accepts.
  keychain.set('pa_user', JSON.stringify({ id: 'u', email: null, display_name: null, census_opt_in: false }));
  keychain.set('pa_access_token', 'access-expired');
  keychain.set('pa_refresh_token', 'refresh-1');
  validAccess = 'access-new';
  refreshCalls = 0;
  refreshReply = () => ({
    status: 200,
    data: { access_token: 'access-new', refresh_token: 'refresh-2', token_type: 'bearer' },
  });
  signOuts = 0;
  unsubscribe = onForcedSignOut(() => { signOuts += 1; });
  delete process.env.EXPO_PUBLIC_SHOW_BACKEND_OVERRIDE;
});

afterEach(() => unsubscribe());

async function getPlants() {
  const client = await apiClient();
  return client.get('/plants/');
}

async function failureOf(p: Promise<unknown>): Promise<unknown> {
  try {
    await p;
  } catch (err) {
    return err;
  }
  throw new Error('expected the request to fail');
}

// ── the happy path ───────────────────────────────────────────────────────────

test('an expired access token is renewed once and the request goes through', async () => {
  const res = await getPlants();
  expect(res.status).toBe(200);
  expect(refreshCalls).toBe(1);
  expect(keychain.get('pa_access_token')).toBe('access-new');
  expect(keychain.get('pa_refresh_token')).toBe('refresh-2');
  expect(signOuts).toBe(0);
});

// ── only a refusal signs anyone out ──────────────────────────────────────────

test.each([401, 403])('a %i from /auth/refresh ends the session', async (status) => {
  refreshReply = () => ({ status, data: { detail: 'Invalid refresh token' } });

  const err = await failureOf(getPlants());

  expect(signOuts).toBe(1);
  expect(keychain.has('pa_refresh_token')).toBe(false);
  expect(keychain.has('pa_access_token')).toBe(false);
  expect(keychain.has('pa_user')).toBe(false);
  // The request itself fails with its own 401, and is not worth retrying.
  expect((err as AxiosError).response?.status).toBe(401);
  expect(isRetryableError(err)).toBe(false);
});

const passing: Array<[string, () => Reply]> = [
  ['a 429 from the rate limit', () => ({ status: 429, data: { error: 'Rate limit exceeded' } })],
  ['a 500', () => ({ status: 500 })],
  ['a 502 while the machine boots', () => ({ status: 502 })],
  ['a 503', () => ({ status: 503, data: { detail: 'Starting up' } })],
  ['a timeout', () => 'timeout'],
  ['a dropped connection', () => 'network'],
  ['a 200 without tokens', () => ({ status: 200, data: '<html>proxy page</html>' })],
];

test.each(passing)('%s keeps the session and fails only this request, retryably', async (_label, reply) => {
  refreshReply = reply;

  const err = await failureOf(getPlants());

  expect(signOuts).toBe(0);
  expect(keychain.get('pa_refresh_token')).toBe('refresh-1');
  expect(keychain.get('pa_access_token')).toBe('access-expired');
  expect(keychain.has('pa_user')).toBe(true);
  expect(err).toBeInstanceOf(SessionRenewalDeferred);
  expect(isRetryableError(err)).toBe(true);
});

test('after a passing failure, the next request renews and succeeds', async () => {
  refreshReply = () => 'timeout';
  await failureOf(getPlants());

  refreshReply = () => ({
    status: 200,
    data: { access_token: 'access-new', refresh_token: 'refresh-2', token_type: 'bearer' },
  });
  const res = await getPlants();

  expect(res.status).toBe(200);
  expect(refreshCalls).toBe(2);
  expect(signOuts).toBe(0);
});

// ── single flight ────────────────────────────────────────────────────────────
// Rotation revokes the old refresh token the moment the server answers, so a
// second concurrent refresh would be a reuse and revoke the whole family.

test('a launch fan-out with an expired token shares one refresh', async () => {
  const results = await Promise.all(Array.from({ length: 20 }, () => getPlants()));
  expect(results.every((r) => r.status === 200)).toBe(true);
  expect(refreshCalls).toBe(1);
  expect(signOuts).toBe(0);
});

test('a fan-out that hits a 429 on refresh fails together, once, and stays signed in', async () => {
  refreshReply = () => ({ status: 429 });
  const errors = await Promise.all(Array.from({ length: 20 }, () => failureOf(getPlants())));
  expect(errors.every((e) => e instanceof SessionRenewalDeferred)).toBe(true);
  expect(refreshCalls).toBe(1);
  expect(signOuts).toBe(0);
  expect(keychain.get('pa_refresh_token')).toBe('refresh-1');
});

test('a fan-out that hits a refusal signs out once', async () => {
  refreshReply = () => ({ status: 401 });
  await Promise.all(Array.from({ length: 20 }, () => failureOf(getPlants())));
  expect(refreshCalls).toBe(1);
  expect(signOuts).toBe(1);
});

// ── which server ─────────────────────────────────────────────────────────────

test('a production build ignores a backend override left in the keychain', async () => {
  keychain.set('garden_gnome_api_url', 'http://192.168.1.119:8000');
  await expect(getBaseUrl()).resolves.toBe(DEFAULT_BASE_URL);
});

test('a preview build honours the stored override', async () => {
  process.env.EXPO_PUBLIC_SHOW_BACKEND_OVERRIDE = '1';
  keychain.set('garden_gnome_api_url', 'http://192.168.1.119:8000');
  await expect(getBaseUrl()).resolves.toBe('http://192.168.1.119:8000');
});
