import { Platform } from 'react-native';
import axios from 'axios';
import * as Crypto from 'expo-crypto';
import { getBaseUrl } from '../api/client';
import { AuthUser } from './tokenStorage';

// Native sign-in flows. Both providers need real builds:
// - Sign in with Apple: EAS/dev build on a real iOS device (not Expo Go, not web)
// - Google Sign-In: config-plugin native module, also EAS/dev build only
// The functions below lazy-require their native modules so the web bundle
// never touches them.

export interface SignInResult {
  user: AuthUser;
  access_token: string;
  refresh_token: string;
}

async function postAuth(path: string, body: object): Promise<SignInResult> {
  const baseURL = await getBaseUrl();
  // Bare axios: sign-in doesn't carry a Bearer token and must not enter the
  // 401-refresh interceptor.
  const { data } = await axios.post(`${baseURL}${path}`, body, { timeout: 20000 });
  return data as SignInResult;
}

function randomNonce(bytes: Uint8Array): string {
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

export async function signInWithApple(): Promise<SignInResult> {
  if (Platform.OS !== 'ios') {
    throw new Error('Sign in with Apple is only available on iOS.');
  }
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const AppleAuthentication = require('expo-apple-authentication');

  // Nonce binding: Apple receives sha256(raw) and embeds it in the identity
  // token; the backend recomputes sha256(raw_nonce) and compares. The raw
  // value itself never goes to Apple, only to our backend.
  const raw = randomNonce(await Crypto.getRandomBytesAsync(16));
  const hashed = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256, raw);

  const credential = await AppleAuthentication.signInAsync({
    requestedScopes: [
      AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
      AppleAuthentication.AppleAuthenticationScope.EMAIL,
    ],
    nonce: hashed,
  });

  if (!credential.identityToken || !credential.authorizationCode) {
    throw new Error('Apple did not return the expected credentials.');
  }

  // fullName arrives ONLY on the first authorization — forward it immediately
  const fullName = [
    credential.fullName?.givenName,
    credential.fullName?.familyName,
  ].filter(Boolean).join(' ') || undefined;

  return postAuth('/auth/apple', {
    identity_token: credential.identityToken,
    authorization_code: credential.authorizationCode,
    raw_nonce: raw,
    full_name: fullName,
  });
}

const GOOGLE_IOS_CLIENT_ID =
  '997811516738-l75faapsrdvglh34tfj8vj15r0lcs0qt.apps.googleusercontent.com';

function googleSignin() {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { GoogleSignin } = require('@react-native-google-signin/google-signin');
  GoogleSignin.configure({ iosClientId: GOOGLE_IOS_CLIENT_ID });
  return GoogleSignin;
}

export async function signInWithGoogle(): Promise<SignInResult> {
  if (Platform.OS === 'web') {
    throw new Error('Google Sign-In needs the PlantAdvocate mobile app.');
  }
  const GoogleSignin = googleSignin();
  await GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true })
    .catch(() => { /* iOS: not applicable */ });
  const response = await GoogleSignin.signIn();
  const idToken: string | undefined =
    response?.data?.idToken ?? response?.idToken;
  if (!idToken) {
    throw new Error('Google did not return an id token.');
  }
  return postAuth('/auth/google', { id_token: idToken });
}

/** Best-effort local Google sign-out (no-op where unavailable). */
export async function googleSignOutLocal(): Promise<void> {
  if (Platform.OS === 'web') return;
  try {
    await googleSignin().signOut();
  } catch {
    // Never let a Google SDK hiccup block our own sign-out
  }
}
