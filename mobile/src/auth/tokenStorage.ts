import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

// Access/refresh tokens live in the iOS Keychain / Android Keystore via
// expo-secure-store — NEVER AsyncStorage. The web dev preview falls back to
// localStorage (secure-store has no web implementation in SDK 57), which is
// acceptable for development only.

const ACCESS_KEY = 'pa_access_token';
const REFRESH_KEY = 'pa_refresh_token';
const USER_KEY = 'pa_user';

async function getItem(key: string): Promise<string | null> {
  if (Platform.OS === 'web') return localStorage.getItem(key);
  return SecureStore.getItemAsync(key);
}

async function setItem(key: string, value: string): Promise<void> {
  if (Platform.OS === 'web') {
    localStorage.setItem(key, value);
    return;
  }
  await SecureStore.setItemAsync(key, value);
}

async function deleteItem(key: string): Promise<void> {
  if (Platform.OS === 'web') {
    localStorage.removeItem(key);
    return;
  }
  await SecureStore.deleteItemAsync(key);
}

export interface AuthUser {
  id: string;
  email: string | null;
  display_name: string | null;
  census_opt_in: boolean;
}

export const getAccessToken = () => getItem(ACCESS_KEY);
export const getRefreshToken = () => getItem(REFRESH_KEY);

export async function getStoredUser(): Promise<AuthUser | null> {
  const raw = await getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export async function storeSession(
  user: AuthUser, accessToken: string, refreshToken: string,
): Promise<void> {
  await setItem(USER_KEY, JSON.stringify(user));
  await setItem(ACCESS_KEY, accessToken);
  await setItem(REFRESH_KEY, refreshToken);
}

export async function storeTokens(
  accessToken: string, refreshToken: string,
): Promise<void> {
  await setItem(ACCESS_KEY, accessToken);
  await setItem(REFRESH_KEY, refreshToken);
}

export async function clearSession(): Promise<void> {
  await deleteItem(ACCESS_KEY);
  await deleteItem(REFRESH_KEY);
  await deleteItem(USER_KEY);
}

export type InitialSession =
  | { status: 'signedIn'; user: AuthUser }
  | { status: 'signedOut'; user: null };

/**
 * Read the persisted session at launch, treating an unreadable store as
 * "no session".
 *
 * Lives here rather than inline in AuthProvider so the failure path is
 * reachable from a unit test — the app hanging on a blank splash was caused
 * by exactly this code throwing, and a branch that can't be tested is a
 * branch that regresses silently.
 */
export async function resolveInitialSession(): Promise<InitialSession> {
  try {
    const [user, refresh] = await Promise.all([getStoredUser(), getRefreshToken()]);
    if (user && refresh) return { status: 'signedIn', user };
  } catch {
    // Keychain unreadable — locked device, a build missing the keychain
    // entitlement, or a corrupted item. Fall through to signedOut: signing in
    // again rewrites the session, which is the recovery path anyway. Letting
    // this reject would strand AuthGate on 'loading', which renders nothing.
  }
  return { status: 'signedOut', user: null };
}

// ── Forced sign-out signal ─────────────────────────────────────────────────────
// Fired by the API client when a refresh attempt fails (expired/revoked
// session). The AuthProvider listens and drops the user to the login screen.

type Listener = () => void;
const listeners = new Set<Listener>();

export function onForcedSignOut(cb: Listener): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

export function emitForcedSignOut(): void {
  listeners.forEach((cb) => cb());
}
