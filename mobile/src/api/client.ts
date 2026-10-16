import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import {
  clearSession, emitForcedSignOut, getAccessToken, getRefreshToken,
  storeTokens,
} from '../auth/tokenStorage';
import {
  refreshVerdict, renewedTokens, SessionRenewalDeferred,
} from '../auth/refreshPolicy';
// Hosted backend (Fly.io). iOS release builds block plain http to
// non-localhost hosts (ATS), so the default must be https. For local dev,
// point at your machine via Settings (e.g. http://192.168.1.119:8000).
const DEFAULT_BASE_URL = 'https://garden-gnome-api.fly.dev';
const BASE_URL_KEY = 'garden_gnome_api_url';

// expo-secure-store has no web implementation (not a supported platform in
// SDK 57), so the browser dev preview falls back to localStorage.
export async function getBaseUrl(): Promise<string> {
  const stored = Platform.OS === 'web'
    ? localStorage.getItem(BASE_URL_KEY)
    : await SecureStore.getItemAsync(BASE_URL_KEY);
  return stored ?? DEFAULT_BASE_URL;
}

export async function setBaseUrl(url: string): Promise<void> {
  const value = url.replace(/\/$/, '');
  if (Platform.OS === 'web') {
    localStorage.setItem(BASE_URL_KEY, value);
  } else {
    await SecureStore.setItemAsync(BASE_URL_KEY, value);
  }
}

// ── Single-flight token refresh ────────────────────────────────────────────────
// Many requests can 401 at once when the access token expires; they must all
// share ONE /auth/refresh call (rotation makes a second concurrent refresh a
// reuse -> the backend would revoke the whole token family).

type RefreshResult =
  /** New tokens are stored; retry with this one. */
  | { kind: 'renewed'; accessToken: string }
  /** The server refused the refresh token. The session is over and the
   *  app has been told to show the login screen. */
  | { kind: 'ended' }
  /** The refresh didn't complete (rate limit, server error, timeout, no
   *  signal). The tokens are kept; the next request tries again. */
  | { kind: 'deferred'; reason: unknown }
  /** Nothing to refresh with. */
  | { kind: 'noSession' };

let refreshInFlight: Promise<RefreshResult> | null = null;

async function doRefresh(): Promise<RefreshResult> {
  let refreshToken: string | null;
  try {
    refreshToken = await getRefreshToken();
  } catch (err) {
    // An unreadable keychain (a locked device) says nothing about the session.
    return { kind: 'deferred', reason: err };
  }
  if (!refreshToken) return { kind: 'noSession' };

  try {
    const baseURL = await getBaseUrl();
    // Bare axios on purpose: the refresh call must not run through the
    // 401-retry interceptor itself.
    const { data } = await axios.post(`${baseURL}/auth/refresh`, {
      refresh_token: refreshToken,
    }, { timeout: 15000 });
    const tokens = renewedTokens(data);
    if (!tokens) return { kind: 'deferred', reason: new Error('refresh answered without tokens') };
    await storeTokens(tokens.access, tokens.refresh);
    return { kind: 'renewed', accessToken: tokens.access };
  } catch (err) {
    if (refreshVerdict(err) === 'keepSession') return { kind: 'deferred', reason: err };
    // The server refused the token (revoked, expired, reused): sign out. The
    // signal goes out even if clearing the keychain fails, or the app would
    // sit on screens whose every request fails.
    try {
      await clearSession();
    } finally {
      emitForcedSignOut();
    }
    return { kind: 'ended' };
  }
}

function sharedRefresh(): Promise<RefreshResult> {
  if (!refreshInFlight) {
    refreshInFlight = doRefresh().finally(() => { refreshInFlight = null; });
  }
  return refreshInFlight;
}

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean };

// Build a fresh axios instance pointed at the current configured URL.
// Call this before each request batch rather than caching at module load time
// so URL changes in Settings take effect immediately.
export async function apiClient(): Promise<AxiosInstance> {
  const baseURL = await getBaseUrl();
  const instance = axios.create({
    baseURL,
    timeout: 15000,
    headers: { 'Content-Type': 'application/json' },
  });

  instance.interceptors.request.use(async (config) => {
    const token = await getAccessToken();
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  });

  instance.interceptors.response.use(
    (resp) => resp,
    async (error: AxiosError) => {
      const config = error.config as RetriableConfig | undefined;
      const isAuthRoute = (config?.url ?? '').startsWith('/auth/');
      if (
        error.response?.status === 401 &&
        config && !config._retried && !isAuthRoute
      ) {
        const result = await sharedRefresh();
        if (result.kind === 'renewed') {
          config._retried = true;
          config.headers.Authorization = `Bearer ${result.accessToken}`;
          return instance.request(config);
        }
        // Still signed in, just not renewed yet: fail this one request in a
        // way callers read as "try again", not as a rejection.
        if (result.kind === 'deferred') throw new SessionRenewalDeferred(result.reason);
      }
      throw error;
    },
  );

  return instance;
}
