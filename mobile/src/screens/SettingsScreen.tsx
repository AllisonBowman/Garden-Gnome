import React, { useState, useEffect } from 'react';
import { ScrollView, StyleSheet, Alert, View, Platform } from 'react-native';
import { Text, TextInput, Button, Card, Divider, Switch } from 'react-native-paper';
import { getBaseUrl, setBaseUrl } from '../api/client';
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

export default function SettingsScreen() {
  const [url, setUrl]       = useState('');
  const [saved, setSaved]   = useState(false);
  const [testing, setTesting] = useState(false);
  const [prefs, setPrefs]   = useState<ReminderPrefs>({});

  const remindersSupported = Platform.OS !== 'web';

  useEffect(() => {
    getBaseUrl().then(setUrl);
    getReminderPrefs().then(setPrefs);
  }, []);

  async function toggleReminder(type: CareType, value: boolean) {
    if (value) {
      // First-use path: this triggers the OS permission prompt if needed
      const granted = await ensureNotificationPermission();
      if (!granted) {
        Alert.alert(
          'Notifications disabled',
          'Garden Gnome needs notification permission for care reminders. You can enable it in your device settings.',
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
        <Card.Title title="Backend connection" titleVariant="titleMedium" />
        <Card.Content>
          <Text variant="bodySmall" style={styles.hint}>
            Enter the URL of your Garden Gnome API server.{'\n'}
            For local development: http://192.168.x.x:8000{'\n'}
            For production: https://your-server.example.com
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
            Garden Gnome v1.0.0{'\n'}
            AI-powered plant care assistant with environmental stewardship census.{'\n\n'}
            The app connects to a self-hosted or cloud-deployed FastAPI backend.
            All plant data remains under your control.
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
  reminderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  reminderLabel: { color: '#333' },
});
