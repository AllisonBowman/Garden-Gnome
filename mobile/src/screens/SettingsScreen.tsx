import React, { useState, useEffect, useMemo } from 'react';
import { ScrollView, StyleSheet, Alert, View, Platform } from 'react-native';
import { Text, TextInput, Button, Card, Divider, Switch } from 'react-native-paper';
import { getBaseUrl, setBaseUrl } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import {
  APP_VERSION, WEBSITE_URL, SUPPORT_URL, SUPPORT_EMAIL, PRIVACY_URL, openExternal,
} from '../support';
import { updateMe } from '../api/me';
import {
  orderedFlows, DESTINATION_LABELS, CENSUS_CONSENT, PRIVACY_INTRO,
} from '../consent/copy';
import {
  getReminderPrefs, setReminderPrefs, ensureNotificationPermission,
  rescheduleAllReminders, getWeatherShiftPref, setWeatherShiftPref,
} from '../notifications/reminders';
import { ReminderPrefs } from '../notifications/plan';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import { BUILD_NUMBER, BUILD_COMMIT } from '../buildInfo';
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
  const { user, signOut, deleteAccount, updateUser } = useAuth();
  const { name: themeName, toggle: toggleTheme, palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const [url, setUrl]       = useState('');
  const [saved, setSaved]   = useState(false);
  const [testing, setTesting] = useState(false);
  const [prefs, setPrefs]   = useState<ReminderPrefs>({});
  const [weatherShift, setWeatherShift] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [censusSaving, setCensusSaving] = useState(false);
  const [openFlow, setOpenFlow] = useState<string | null>(null);

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

  // Consent has to round-trip to the server before the UI claims it happened:
  // the census reads the column, not this screen. On failure we say so and
  // leave the switch where it was, rather than showing a state the server
  // does not agree with.
  async function toggleCensus(value: boolean) {
    if (!user) return;
    setCensusSaving(true);
    try {
      const updated = await updateMe({ census_opt_in: value });
      await updateUser({ ...user, census_opt_in: updated.census_opt_in });
    } catch {
      Alert.alert(
        'Could not save that',
        'PlantAdvocate could not reach the server to change your census '
        + 'setting, so nothing has changed. Check your connection and try again.',
      );
    } finally {
      setCensusSaving(false);
    }
  }

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
        <Card.Title title="Account" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
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
            textColor={palette.warn}
            style={styles.btn}
          >
            Delete account
          </Button>
        </Card.Content>
      </Card>

      <Divider style={styles.divider} />

      <Card style={styles.card}>
        <Card.Title title="Appearance" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          <View style={styles.reminderRow}>
            <Text variant="bodyMedium" style={styles.reminderLabel}>
              {themeName === 'observatory' ? '🌙 Observatory (dark)' : '☀️ Almanac (light)'}
            </Text>
            <Switch
              value={themeName === 'observatory'}
              onValueChange={toggleTheme}
              color={palette.acc}
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
            <Card.Title title="Backend connection" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
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
                buttonColor={palette.acc}
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
        <Card.Title title="Care reminders" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
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
                color={palette.acc}
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
                  color={palette.acc}
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
        <Card.Title title="Privacy & data" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          <Text variant="bodySmall" style={styles.hint}>{PRIVACY_INTRO}</Text>

          {/* The one control the policy promises. Everything else on this card
              is disclosure; this is the part the caretaker can actually set. */}
          <View style={styles.reminderRow}>
            <Text variant="bodyMedium" style={styles.reminderLabel}>
              🌍 {CENSUS_CONSENT.label}
            </Text>
            <Switch
              value={!!user?.census_opt_in}
              disabled={censusSaving || !user}
              onValueChange={toggleCensus}
              color={palette.acc}
            />
          </View>
          <Text variant="bodySmall" style={styles.subHint}>
            {user?.census_opt_in ? CENSUS_CONSENT.on : CENSUS_CONSENT.off}
          </Text>

          <Divider style={styles.innerDivider} />

          {orderedFlows().map((flow) => {
            const open = openFlow === flow.id;
            return (
              <View key={flow.id} style={styles.flowRow}>
                <Button
                  mode="text"
                  compact
                  onPress={() => setOpenFlow(open ? null : flow.id)}
                  contentStyle={styles.flowBtnContent}
                  labelStyle={styles.flowBtnLabel}
                  textColor={palette.ink}
                  accessibilityLabel={
                    `${flow.title}. ${DESTINATION_LABELS[flow.destination]}. `
                    + `${open ? 'Hide' : 'Show'} details.`
                  }
                >
                  {`${open ? '▾' : '▸'}  ${flow.title}`}
                </Button>
                <Text variant="bodySmall" style={styles.flowSummary}>
                  {flow.destination === 'device' ? '✓ ' : '→ '}{flow.summary}
                </Text>
                {open && (
                  <Text variant="bodySmall" style={styles.flowDetail}>{flow.detail}</Text>
                )}
              </View>
            );
          })}

          <Button
            mode="outlined"
            icon="shield-account-outline"
            onPress={() => openExternal(PRIVACY_URL)}
            style={styles.privacyBtn}
          >
            Read the full policy
          </Button>
        </Card.Content>
      </Card>

      <Divider style={styles.divider} />

      <Card style={styles.card}>
        <Card.Title title="About & Support" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          <Text variant="bodySmall" style={styles.about}>
            PlantAdvocate v{APP_VERSION}
            {BUILD_NUMBER > 0 ? `  ·  build ${BUILD_NUMBER} (${BUILD_COMMIT})` : ''}{'\n'}
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

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  container: { flex: 1, backgroundColor: p.bg },
  content: { padding: 16, paddingBottom: 48 },
  card: { marginBottom: 16, borderRadius: 12, backgroundColor: p.card },
  cardTitle: { fontFamily: f.display, color: p.ink },
  hint: { color: p.sub, lineHeight: 20, marginBottom: 12 },
  input: { marginBottom: 12 },
  btn: { marginBottom: 10, borderRadius: 8 },
  divider: { marginVertical: 8, backgroundColor: p.line },
  about: { color: p.sub, lineHeight: 20 },
  accountName: { color: p.ink, fontWeight: '600', marginBottom: 2 },
  reminderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  reminderLabel: { color: p.ink, flexShrink: 1, paddingRight: 12 },
  innerDivider: { marginTop: 10, marginBottom: 4, backgroundColor: p.line },
  subHint: { color: p.faint, lineHeight: 18, marginTop: 2 },
  flowRow: { marginBottom: 10 },
  // Pull the text button back to the card's left edge so the disclosure list
  // reads as a list, not as a column of buttons.
  flowBtnContent: { justifyContent: 'flex-start', paddingHorizontal: 0, minHeight: 44 },
  flowBtnLabel: { marginHorizontal: 0, textAlign: 'left', fontWeight: '600' },
  flowSummary: { color: p.sub, lineHeight: 18, marginTop: -2 },
  flowDetail: {
    color: p.faint, lineHeight: 18, marginTop: 6, paddingLeft: 10,
    borderLeftWidth: 2, borderLeftColor: p.line,
  },
  privacyBtn: { marginTop: 12, borderRadius: 8 },
});
