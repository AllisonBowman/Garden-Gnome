// tokenStorage is the only module that touches the keychain, so both native
// dependencies are stubbed here. The jest setup is deliberately RN-free
// (see jest.config.js), and these factories keep it that way.
jest.mock('react-native', () => ({ Platform: { OS: 'ios' } }));
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

import * as SecureStore from 'expo-secure-store';
import { AuthUser, resolveInitialSession } from './tokenStorage';

const getItem = SecureStore.getItemAsync as jest.MockedFunction<
  typeof SecureStore.getItemAsync
>;

const USER: AuthUser = {
  id: 'u_1',
  email: 'allison@example.com',
  display_name: 'Allison',
  census_opt_in: false,
};

/** Serve stored values by key, the way the real keychain would. */
function keychain(values: Record<string, string | null>) {
  getItem.mockImplementation(async (key: string) => values[key] ?? null);
}

beforeEach(() => jest.clearAllMocks());

describe('resolveInitialSession', () => {
  it('reports signedIn when a user and refresh token are both stored', async () => {
    keychain({ pa_user: JSON.stringify(USER), pa_refresh_token: 'refresh-abc' });

    await expect(resolveInitialSession()).resolves.toEqual({
      status: 'signedIn',
      user: USER,
    });
  });

  it('reports signedOut on a fresh install', async () => {
    keychain({});

    await expect(resolveInitialSession()).resolves.toEqual({
      status: 'signedOut',
      user: null,
    });
  });

  it('reports signedOut when the user is stored but the refresh token is gone', async () => {
    keychain({ pa_user: JSON.stringify(USER) });

    await expect(resolveInitialSession()).resolves.toEqual({
      status: 'signedOut',
      user: null,
    });
  });

  // The regression this whole extraction exists for: an unreadable keychain
  // used to reject out of AuthProvider's effect, so setStatus never ran and
  // the app sat on a blank splash forever with no error and no way out.
  describe('when the keychain is unreadable', () => {
    it('falls through to signedOut rather than rejecting', async () => {
      getItem.mockRejectedValue(
        new Error("KeyChainException: A required entitlement isn't present."),
      );

      await expect(resolveInitialSession()).resolves.toEqual({
        status: 'signedOut',
        user: null,
      });
    });

    it('never rejects, whatever the store throws', async () => {
      getItem.mockRejectedValue(new Error('User interaction is not allowed.'));

      await expect(resolveInitialSession()).resolves.toBeDefined();
    });

    it('recovers even when only one of the two reads fails', async () => {
      getItem.mockImplementation(async (key: string) => {
        if (key === 'pa_refresh_token') throw new Error('keychain locked');
        return JSON.stringify(USER);
      });

      await expect(resolveInitialSession()).resolves.toEqual({
        status: 'signedOut',
        user: null,
      });
    });
  });

  it('treats a corrupted user record as no session, not a crash', async () => {
    keychain({ pa_user: 'not json{', pa_refresh_token: 'refresh-abc' });

    await expect(resolveInitialSession()).resolves.toEqual({
      status: 'signedOut',
      user: null,
    });
  });
});
