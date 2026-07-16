import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import {
  clearSession, emitForcedSignOut, getAccessToken, getRefreshToken,
  storeTokens,
} from '../auth/tokenStorage';

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

let refreshInFlight: Promise<string | null> | null = null;

async function doRefresh(): Promise<string | null> {
  const refreshToken = await getRefreshToken();
  if (!refreshToken) return null;
  try {
    const baseURL = await getBaseUrl();
    // Bare axios on purpose: the refresh call must not run through the
    // 401-retry interceptor itself.
    const { data } = await axios.post(`${baseURL}/auth/refresh`, {
      refresh_token: refreshToken,
    }, { timeout: 15000 });
    await storeTokens(data.access_token, data.refresh_token);
    return data.access_token as string;
  } catch {
    // Refresh failed (revoked/expired/reused) — session is over.
    await clearSession();
    emitForcedSignOut();
    return null;
  }
}

function sharedRefresh(): Promise<string | null> {
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
        const newToken = await sharedRefresh();
        if (newToken) {
          config._retried = true;
          config.headers.Authorization = `Bearer ${newToken}`;
          return instance.request(config);
        }
      }
      throw error;
    },
  );

  return instance;
}
