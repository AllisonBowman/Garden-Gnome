import React, { useState, useEffect } from 'react';
import { ScrollView, StyleSheet, Alert, View, Platform } from 'react-native';
import { Text, TextInput, Button, Card, Divider, Switch } from 'react-native-paper';
import { getBaseUrl, setBaseUrl } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import {
  getReminderPrefs, setReminderPrefs, ensureNotificationPermission,
  rescheduleAllReminders,
} from '../notifications/reminders';
import { ReminderPrefs } from '../notifications/plan';
import { CareType } from '../types';

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
  const [url, setUrl]       = useState('');
  const [saved, setSaved]   = useState(false);
  const [testing, setTesting] = useState(false);
  const [prefs, setPrefs]   = useState<ReminderPrefs>({});
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
    if (__DEV__) getBaseUrl().then(setUrl); // field only shown in dev builds
    getReminderPrefs().then(setPrefs);
  }, []);

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

      {/* Dev-only: point the app at a local backend. Hidden in release builds
          so end users can't accidentally break connectivity (the app then just
          uses the hosted DEFAULT_BASE_URL). */}
      {__DEV__ && (
        <>
          <Card style={styles.card}>
            <Card.Title title="Backend connection (dev)" titleVariant="titleMedium" />
            <Card.Content>
              <Text variant="bodySmall" style={styles.hint}>
                Dev only — override the API server URL.{'\n'}
                For local development: http://192.168.x.x:8000{'\n'}
                Default (release): https://garden-gnome-api.fly.dev
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
        </Card.Content>
      </Card>

      <Divider style={styles.divider} />

      <Card style={styles.card}>
        <Card.Title title="About" titleVariant="titleMedium" />
        <Card.Content>
          <Text variant="bodySmall" style={styles.about}>
            PlantAdvocate v1.0.0{'\n'}
            AI-powered plant care assistant with environmental stewardship census.{'\n\n'}
            The app connects to a self-hosted or cloud-deployed FastAPI backend.
            All plant data remains under your control.{'\n\n'}
            Species data provided in part by Perenual (perenual.com).
          </Text>
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
  reminderLabel: { color: '#333' },
});
