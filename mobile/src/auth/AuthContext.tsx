import React, {
  createContext, useCallback, useContext, useEffect, useMemo, useState,
} from 'react';
import axios from 'axios';
import { apiClient, getBaseUrl } from '../api/client';
import { googleSignOutLocal } from './signIn';
import {
  AuthUser, clearSession, getRefreshToken, onForcedSignOut,
  resolveInitialSession, storeSession,
} from './tokenStorage';

export type AuthStatus = 'loading' | 'signedOut' | 'signedIn';

interface AuthContextValue {
  status: AuthStatus;
  user: AuthUser | null;
  /** Store a fresh session (called by the login screen). */
  setSession: (user: AuthUser, access: string, refresh: string) => Promise<void>;
  /** Full sign-out: revoke server-side, clear local state, back to login. */
  signOut: () => Promise<void>;
  /** DELETE /me then full local sign-out. */
  deleteAccount: () => Promise<void>;
  /** Refresh the cached profile after PATCH /me etc. */
  updateUser: (user: AuthUser) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    (async () => {
      // resolveInitialSession swallows an unreadable keychain and reports
      // signedOut, so status always leaves 'loading' — AuthGate renders
      // nothing while loading, so a throw here is a permanent blank splash.
      const initial = await resolveInitialSession();
      setUser(initial.user);
      setStatus(initial.status);
    })();
  }, []);

  // The API client fires this when a token refresh fails (revoked session)
  useEffect(() => onForcedSignOut(() => {
    setUser(null);
    setStatus('signedOut');
  }), []);

  const setSession = useCallback(
    async (nextUser: AuthUser, access: string, refresh: string) => {
      await storeSession(nextUser, access, refresh);
      setUser(nextUser);
      setStatus('signedIn');
    }, []);

  const localSignOut = useCallback(async () => {
    await googleSignOutLocal();
    await clearSession();
    setUser(null);
    setStatus('signedOut');
  }, []);

  const signOut = useCallback(async () => {
    // Best-effort server-side revoke of this device's refresh token; local
    // sign-out proceeds regardless (the plan's logout is idempotent anyway).
    try {
      const refresh = await getRefreshToken();
      if (refresh) {
        const baseURL = await getBaseUrl();
        await axios.post(`${baseURL}/auth/logout`,
          { refresh_token: refresh }, { timeout: 10000 });
      }
    } catch {
      // Offline logout is still a logout
    }
    await localSignOut();
  }, [localSignOut]);

  const deleteAccount = useCallback(async () => {
    const client = await apiClient();
    await client.delete('/me');  // throws on failure — caller shows the error
    await localSignOut();
  }, [localSignOut]);

  const updateUser = useCallback((next: AuthUser) => setUser(next), []);

  const value = useMemo(
    () => ({ status, user, setSession, signOut, deleteAccount, updateUser }),
    [status, user, setSession, signOut, deleteAccount, updateUser]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
