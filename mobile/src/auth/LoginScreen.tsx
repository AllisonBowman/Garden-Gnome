import React, { useMemo, useState } from 'react';
import { Platform, StyleSheet, View } from 'react-native';
import { Button, Text } from 'react-native-paper';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import { useAuth } from './AuthContext';
import { signInWithApple, signInWithGoogle } from './signIn';

// Sign in with Apple renders Apple's own button component (required styling).
// Loaded lazily so the web bundle never imports the native module.
let AppleAuthentication: typeof import('expo-apple-authentication') | null = null;
if (Platform.OS === 'ios') {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  AppleAuthentication = require('expo-apple-authentication');
}

export default function LoginScreen() {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const { setSession } = useAuth();
  const [busy, setBusy] = useState<'apple' | 'google' | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(kind: 'apple' | 'google') {
    setBusy(kind);
    setError(null);
    try {
      const result = kind === 'apple'
        ? await signInWithApple()
        : await signInWithGoogle();
      await setSession(result.user, result.access_token, result.refresh_token);
    } catch (e) {
      // User-cancelled Apple sign-in throws ERR_REQUEST_CANCELED — stay quiet
      const code = (e as { code?: string }).code;
      if (code !== 'ERR_REQUEST_CANCELED' && code !== 'SIGN_IN_CANCELLED') {
        setError('Sign-in didn\'t complete. Please try again.');
      }
    } finally {
      setBusy(null);
    }
  }

  return (
    <View style={styles.container}>
      <View style={styles.hero}>
        <Text style={styles.mascot}>🧙🌱</Text>
        <Text style={styles.title}>PlantAdvocate</Text>
        <Text style={styles.tagline}>
          Plant care that knows what it&apos;s talking about — with a gnome
          who never guesses.
        </Text>
      </View>

      <View style={styles.buttons}>
        {Platform.OS === 'ios' && AppleAuthentication && (
          <AppleAuthentication.AppleAuthenticationButton
            buttonType={
              AppleAuthentication.AppleAuthenticationButtonType.SIGN_IN}
            buttonStyle={
              AppleAuthentication.AppleAuthenticationButtonStyle.BLACK}
            cornerRadius={8}
            style={styles.appleButton}
            onPress={() => run('apple')}
          />
        )}
        {Platform.OS !== 'web' && (
          <Button
            mode="contained"
            icon="google"
            onPress={() => run('google')}
            loading={busy === 'google'}
            disabled={busy !== null}
            style={styles.googleButton}
            buttonColor="#FFFFFF"
            textColor="#1F1F1F"
          >
            Sign in with Google
          </Button>
        )}
        {Platform.OS === 'web' && (
          <Text style={styles.webNote}>
            Signing in requires the PlantAdvocate mobile app — Apple and
            Google sign-in aren&apos;t available in the browser preview.
          </Text>
        )}
        {error && <Text style={styles.error}>{error}</Text>}
      </View>

      <Text style={styles.footer}>
        Your plants stay yours: private by default, and the anonymized census
        is strictly opt-in.
      </Text>
    </View>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: p.bg,
    padding: 24,
    justifyContent: 'space-between',
  },
  hero: { alignItems: 'center', marginTop: 96 },
  mascot: { fontSize: 56, marginBottom: 12 },
  title: { fontSize: 32, fontWeight: '700', color: p.acc, fontFamily: f.display },
  tagline: {
    marginTop: 10,
    textAlign: 'center',
    color: p.sub,
    fontSize: 15,
    lineHeight: 22,
    maxWidth: 300,
  },
  buttons: { gap: 12, alignItems: 'stretch' },
  appleButton: { height: 48 },
  // Google's brand button keeps its required white fill + #DADCE0 border in
  // both themes, so a theme token would break the brand spec here.
  googleButton: { borderRadius: 8, borderWidth: 1, borderColor: '#DADCE0' },
  webNote: {
    textAlign: 'center',
    color: p.sub,
    fontStyle: 'italic',
    lineHeight: 20,
  },
  error: { textAlign: 'center', color: p.warn },
  footer: {
    textAlign: 'center',
    color: p.faint,
    fontSize: 12,
    lineHeight: 18,
    marginBottom: 12,
  },
});
