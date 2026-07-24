import React, { useState, useEffect } from 'react';
import { ScrollView, StyleSheet, Alert, View, Platform } from 'react-native';
import { Text, TextInput, Button, Card, Divider, Switch } from 'react-native-paper';
import { getBaseUrl, setBaseUrl } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import {
  APP_VERSION, WEBSITE_URL, SUPPORT_URL, SUPPORT_EMAIL, openExternal,
} from '../support';
import {
  getReminderPrefs, setReminderPrefs, ensureNotificationPermission,
  rescheduleAllReminders, getWeatherShiftPref, setWeatherShiftPref,
} from '../notifications/reminders';
import { ReminderPrefs } from '../notifications/plan';
import { useAppTheme } from '../theme/ThemeProvider';
import { CareType } from '../types';

// The backend-URL override is shown in dev AND in builds that opt in via
// EXPO_PUBLIC_SHOW_BACKEND_OVERRIDE (set for the development + preview EAS
// profiles, not production) — so preview testers can point at the Fly URL
// (the default) or a LAN server, while App Store builds keep it hidden.
const SHOW_BACKEND_OVERRIDE =
  __DEV__ || process.env.EXPO_PUBLIC_SHOW_BACKEND_OVERRIDE === '1';

const REMINDER_TOGGLES: { type: CareType; icon: string; label: string }[] = [
  { type: 'water',     icon: '💧', label: 'Watering'    },
  { type: 'fertilize', icon: '🌿', label: 'Fertilizing' },
  { type: 'mist',      icon: '💨', label: 'Misting'     },
  { type: 'prune',     icon: '✂️', label: 'Pruning'     },
  { type: 'repot',     icon: '🪴', label: 'Repotting'   },
  { type: 'rotate',    icon: '🔄', label: 'Rotating'    },
];

// Cross-platform confirm: Alert.alert buttons are no-ops on react-native-web
function confirmDialog(
  title: string, message: string, confirmLabel: string,
): Promise<boolean> {
  if (Platform.OS === 'web') {
    return Promise.resolve(window.confirm(`${title}\n\n${message}`));
  }
  return new Promise((resolve) => {
    Alert.alert(title, message, [
      { text: 'Cancel', style: 'cancel', onPress: () => resolve(false) },
      { text: confirmLabel, style: 'destructive', onPress: () => resolve(true) },
    ]);
  });
}

export default function SettingsScreen() {
  const { user, signOut, deleteAccount } = useAuth();
  const { name: themeName, toggle: toggleTheme } = useAppTheme();
  const [url, setUrl]       = useState('');
  const [saved, setSaved]   = useState(false);
  const [testing, setTesting] = useState(false);
  const [prefs, setPrefs]   = useState<ReminderPrefs>({});
  const [weatherShift, setWeatherShift] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const remindersSupported = Platform.OS !== 'web';

  async function onSignOut() {
    setSigningOut(true);
    try {
      await signOut();
    } finally {
      setSigningOut(false);
    }
  }

  async function onDeleteAccount() {
    const sure = await confirmDialog(
      'Delete your account?',
      'This permanently deletes your account, plants, care history, and '
      + 'environments from PlantAdvocate. This cannot be undone.',
      'Delete forever',
    );
    if (!sure) return;
    setDeleting(true);
    try {
      await deleteAccount();
    } catch {
      Alert.alert(
        'Deletion failed',
        'PlantAdvocate could not delete your account. Check your connection and try again.',
      );
    } finally {
      setDeleting(false);
    }
  }

  useEffect(() => {
    if (SHOW_BACKEND_OVERRIDE) getBaseUrl().then(setUrl);
    getReminderPrefs().then(setPrefs);
    getWeatherShiftPref().then(setWeatherShift);
  }, []);

  async function toggleWeatherShift(value: boolean) {
    setWeatherShift(value);
    await setWeatherShiftPref(value);
    // Recompute the schedule so the change takes effect immediately.
    void rescheduleAllReminders();
  }

  async function toggleReminder(type: CareType, value: boolean) {
    if (value) {
      // First-use path: this triggers the OS permission prompt if needed
      const granted = await ensureNotificationPermission();
      if (!granted) {
        Alert.alert(
          'Notifications disabled',
          'PlantAdvocate needs notification permission for care reminders. You can enable it in your device settings.',
        );
        return;
      }
    }
    const next = { ...prefs, [type]: value };
    setPrefs(next);
    await setReminderPrefs(next);
    // Recompute the schedule with the new preference set
    void rescheduleAllReminders();
  }

  async function save() {
    const trimmed = url.trim().replace(/\/$/, '');
    await setBaseUrl(trimmed);
    setUrl(trimmed);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  async function testConnection() {
    setTesting(true);
    try {
      const resp = await fetch(`${url.trim().replace(/\/$/, '')}/`);
      const data = await resp.json();
      Alert.alert('Connected ✓', `${data.name ?? 'API'} v${data.version ?? '?'}`);
    } catch {
      Alert.alert('Connection failed', 'Could not reach the backend. Check the URL and make sure the server is running.');
    } finally {
      setTesting(false);
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Card style={styles.card}>
        <Card.Title title="Account" titleVariant="titleMedium" />
        <Card.Content>
          <Text variant="bodyMedium" style={styles.accountName}>
            {user?.display_name || user?.email || 'Signed in'}
          </Text>
          {user?.email && user.display_name ? (
            <Text variant="bodySmall" style={styles.hint}>{user.email}</Text>
          ) : null}
          <Button
            mode="outlined"
            icon="logout"
            onPress={onSignOut}
            loading={signingOut}
            disabled={signingOut || deleting}
            style={styles.btn}
          >
            Sign out
          </Button>
          <Button
            mode="text"
            icon="delete-forever"
            onPress={onDeleteAccount}
            loading={deleting}
            disabled={signingOut || deleting}
            textColor="#B3261E"
            style={styles.btn}
          >
            Delete account
          </Button>
        </Card.Content>
      </Card>

      <Divider style={styles.divider} />

      <Card style={styles.card}>
        <Card.Title title="Appearance" titleVariant="titleMedium" />
        <Card.Content>
          <View style={styles.reminderRow}>
            <Text variant="bodyMedium" style={styles.reminderLabel}>
              {themeName === 'observatory' ? '🌙 Observatory (dark)' : '☀️ Almanac (light)'}
            </Text>
            <Switch
              value={themeName === 'observatory'}
              onValueChange={toggleTheme}
              color="#2D6A4F"
            />
          </View>
          <Text variant="bodySmall" style={styles.hint}>
            Almanac is the warm field-notebook look; Observatory is a dark,
            colorblind-safe night theme.
          </Text>
        </Card.Content>
      </Card>

      <Divider style={styles.divider} />

      {/* Shown in dev + preview builds only (see SHOW_BACKEND_OVERRIDE);
          hidden in production so end users can't break connectivity — the
          app then just uses the hosted DEFAULT_BASE_URL. */}
      {SHOW_BACKEND_OVERRIDE && (
        <>
          <Card style={styles.card}>
            <Card.Title title="Backend connection" titleVariant="titleMedium" />
            <Card.Content>
              <Text variant="bodySmall" style={styles.hint}>
                Override the API server URL.{'\n'}
                Default (cloud): https://garden-gnome-api.fly.dev{'\n'}
                Local network: http://192.168.x.x:8000
              </Text>
              <TextInput
                label="API base URL"
                value={url}
                onChangeText={(v) => { setUrl(v); setSaved(false); }}
                mode="outlined"
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="url"
                style={styles.input}
                placeholder="http://localhost:8000"
              />
              <Button
                mode="contained"
                onPress={save}
                style={styles.btn}
                buttonColor="#2D6A4F"
              >
                {saved ? 'Saved ✓' : 'Save URL'}
              </Button>
              <Button
                mode="outlined"
                onPress={testConnection}
                loading={testing}
                style={styles.btn}
              >
                Test connection
              </Button>
            </Card.Content>
          </Card>

          <Divider style={styles.divider} />
        </>
      )}

      <Card style={styles.card}>
        <Card.Title title="Care reminders" titleVariant="titleMedium" />
        <Card.Content>
          <Text variant="bodySmall" style={styles.hint}>
            {remindersSupported
              ? 'Get a notification when plants come due, based on each species’ schedule and your actual care history. Plants due the same day share one notification.'
              : 'Reminders are available in the mobile app (iOS and Android).'}
          </Text>
          {REMINDER_TOGGLES.map((t) => (
            <View key={t.type} style={styles.reminderRow}>
              <Text variant="bodyMedium" style={styles.reminderLabel}>
                {t.icon} {t.label}
              </Text>
              <Switch
                value={!!prefs[t.type]}
                disabled={!remindersSupported}
                onValueChange={(v) => toggleReminder(t.type, v)}
                color="#2D6A4F"
              />
            </View>
          ))}

          {remindersSupported && (
            <>
              <Divider style={styles.innerDivider} />
              <View style={styles.reminderRow}>
                <Text variant="bodyMedium" style={styles.reminderLabel}>
                  🌦️ Let weather adjust watering
                </Text>
                <Switch
                  value={weatherShift}
                  disabled={!prefs.water}
                  onValueChange={toggleWeatherShift}
                  color="#2D6A4F"
                />
              </View>
              <Text variant="bodySmall" style={styles.subHint}>
                {prefs.water
                  ? 'Nudges watering reminders by a day or two for outdoor, unsheltered plants — later before rain, sooner in a heat spike. Needs a location on the environment.'
                  : 'Turn on watering reminders above to use this.'}
              </Text>
            </>
          )}
        </Card.Content>
      </Card>

      <Divider style={styles.divider} />

      <Card style={styles.card}>
        <Card.Title title="About & Support" titleVariant="titleMedium" />
        <Card.Content>
          <Text variant="bodySmall" style={styles.about}>
            PlantAdvocate v{APP_VERSION}{'\n'}
            Every plant deserves an advocate. Care schedules, reminders, and a
            care engine grounded in a curated species database.{'\n\n'}
            Species data provided in part by Perenual (perenual.com).
          </Text>
          <Button
            mode="outlined"
            icon="web"
            onPress={() => openExternal(WEBSITE_URL)}
            style={styles.btn}
          >
            plantadvocate.ai
          </Button>
          <Button
            mode="outlined"
            icon="lifebuoy"
            onPress={() => openExternal(SUPPORT_URL)}
            style={styles.btn}
          >
            Help & support
          </Button>
          <Button
            mode="outlined"
            icon="email-outline"
            onPress={() => openExternal(`mailto:${SUPPORT_EMAIL}`)}
            style={styles.btn}
          >
            {SUPPORT_EMAIL}
          </Button>
        </Card.Content>
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6FAF7' },
  content: { padding: 16, paddingBottom: 48 },
  card: { marginBottom: 16, borderRadius: 12 },
  hint: { color: '#666', lineHeight: 20, marginBottom: 12 },
  input: { marginBottom: 12 },
  btn: { marginBottom: 10, borderRadius: 8 },
  divider: { marginVertical: 8 },
  about: { color: '#666', lineHeight: 20 },
  accountName: { color: '#333', fontWeight: '600', marginBottom: 2 },
  reminderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  reminderLabel: { color: '#333', flexShrink: 1, paddingRight: 12 },
  innerDivider: { marginTop: 10, marginBottom: 4 },
  subHint: { color: '#888', lineHeight: 18, marginTop: 2 },
});
