import React, { useState, useEffect, useMemo } from 'react';
import { ScrollView, StyleSheet, Alert, View, Platform } from 'react-native';
import { Text, TextInput, Button, Card, Divider, Switch } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation/types';
import { getBaseUrl, setBaseUrl } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import {
  APP_VERSION, WEBSITE_URL, SUPPORT_URL, SUPPORT_EMAIL, PRIVACY_URL, openExternal,
} from '../support';
import { updateMe } from '../api/me';
import {
  visibleFlows, DESTINATION_LABELS, CENSUS_CONSENT, PRIVACY_INTRO,
} from '../consent/copy';
import { useAiCapabilities } from '../care/useAiCapabilities';
import {
  getReminderPrefs, setReminderPrefs, ensureNotificationPermission,
  rescheduleAllReminders, getWeatherShiftPref, setWeatherShiftPref,
  getSeasonalAlertsPref, setSeasonalAlertsPref,
} from '../notifications/reminders';
import { ReminderPrefs } from '../notifications/plan';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import { BUILD_NUMBER, BUILD_COMMIT } from '../buildInfo';
import { CareType } from '../types';
import { t } from '../i18n';

// The backend-URL override is shown in dev AND in builds that opt in via
// EXPO_PUBLIC_SHOW_BACKEND_OVERRIDE (set for the development + preview EAS
// profiles, not production) — so preview testers can point at the Fly URL
// (the default) or a LAN server, while App Store builds keep it hidden.
const SHOW_BACKEND_OVERRIDE =
  __DEV__ || process.env.EXPO_PUBLIC_SHOW_BACKEND_OVERRIDE === '1';

// Each switch is for a kind of check: a reminder asks the caretaker to look,
// never to do the chore, because no schedule knows what a plant needs today.
const REMINDER_TOGGLES: { type: CareType; icon: string; label: string }[] = [
  { type: 'water',     icon: '💧', label: t('settings.reminderToggles.water') },
  { type: 'fertilize', icon: '🌿', label: t('settings.reminderToggles.fertilize') },
  { type: 'prune',     icon: '✂️', label: t('settings.reminderToggles.prune') },
  { type: 'repot',     icon: '🪴', label: t('settings.reminderToggles.repot') },
  { type: 'rotate',    icon: '🔄', label: t('settings.reminderToggles.rotate') },
];

/** What the reminders promise, and only what the planner keeps: a plan a
 *  month ahead, rebuilt when the app opens or care is logged, for plants
 *  whose species has a check schedule (notifications/plan.ts). */
const REMINDERS_HINT = t('settings.remindersHint');

// Cross-platform confirm: Alert.alert buttons are no-ops on react-native-web
function confirmDialog(
  title: string, message: string, confirmLabel: string,
): Promise<boolean> {
  if (Platform.OS === 'web') {
    return Promise.resolve(window.confirm(`${title}\n\n${message}`));
  }
  return new Promise((resolve) => {
    Alert.alert(title, message, [
      { text: t('common.cancel'), style: 'cancel', onPress: () => resolve(false) },
      { text: confirmLabel, style: 'destructive', onPress: () => resolve(true) },
    ]);
  });
}

export default function SettingsScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList, 'Settings'>>();
  const { user, signOut, deleteAccount, updateUser } = useAuth();
  // The privacy list describes what the app does today. Photo check-ups and
  // free-text questions are offered only while the server can serve them,
  // and their disclosures appear and disappear with them.
  const capabilities = useAiCapabilities();
  const { name: themeName, toggle: toggleTheme, palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const [url, setUrl]       = useState('');
  const [saved, setSaved]   = useState(false);
  const [testing, setTesting] = useState(false);
  const [prefs, setPrefs]   = useState<ReminderPrefs>({});
  const [weatherShift, setWeatherShift] = useState(false);
  const [seasonalAlerts, setSeasonalAlerts] = useState(false);
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
      t('settings.deleteConfirm.title'),
      t('settings.deleteConfirm.body'),
      t('settings.deleteConfirm.confirm'),
    );
    if (!sure) return;
    setDeleting(true);
    try {
      await deleteAccount();
    } catch {
      Alert.alert(
        t('settings.deleteFailed.title'),
        t('settings.deleteFailed.body'),
      );
    } finally {
      setDeleting(false);
    }
  }

  useEffect(() => {
    if (SHOW_BACKEND_OVERRIDE) getBaseUrl().then(setUrl);
    getReminderPrefs().then(setPrefs);
    getWeatherShiftPref().then(setWeatherShift);
    getSeasonalAlertsPref().then(setSeasonalAlerts);
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
        t('settings.censusFailed.title'),
        t('settings.censusFailed.body'),
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

  // Frost and weather alerts from the seasonal plan: their own switch, off by
  // default, asking for notification permission the same way care reminders do.
  async function toggleSeasonalAlerts(value: boolean) {
    if (value && !(await ensureNotificationPermission())) {
      Alert.alert(
        t('settings.notificationsDisabled'),
        t('settings.alertsNeedPermission'),
      );
      return;
    }
    setSeasonalAlerts(value);
    await setSeasonalAlertsPref(value);
    void rescheduleAllReminders();
  }

  async function toggleReminder(type: CareType, value: boolean) {
    if (value) {
      // First-use path: this triggers the OS permission prompt if needed
      const granted = await ensureNotificationPermission();
      if (!granted) {
        Alert.alert(
          t('settings.notificationsDisabled'),
          t('settings.remindersNeedPermission'),
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
        <Card.Title title={t('settings.account')} titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          <Text variant="bodyMedium" style={styles.accountName}>
            {user?.display_name || user?.email || t('settings.signedIn')}
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
            {t('settings.signOut')}
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
            {t('settings.deleteAccount')}
          </Button>
        </Card.Content>
      </Card>

      <Divider style={styles.divider} />

      <Card style={styles.card}>
        <Card.Title title={t('settings.appearance')} titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          <View style={styles.reminderRow}>
            <Text variant="bodyMedium" style={styles.reminderLabel}>
              {themeName === 'observatory' ? t('settings.themeDark') : t('settings.themeLight')}
            </Text>
            <Switch
              value={themeName === 'observatory'}
              onValueChange={toggleTheme}
              color={palette.acc}
            />
          </View>
          <Text variant="bodySmall" style={styles.hint}>{t('settings.themeHint')}</Text>
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
        <Card.Title title={t('settings.careReminders')} titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          <Text variant="bodySmall" style={styles.hint}>
            {remindersSupported
              ? REMINDERS_HINT
              : t('settings.remindersMobileOnly')}
          </Text>
          {REMINDER_TOGGLES.map((toggle) => (
            <View key={toggle.type} style={styles.reminderRow}>
              <Text variant="bodyMedium" style={styles.reminderLabel}>
                {toggle.icon} {toggle.label}
              </Text>
              <Switch
                value={!!prefs[toggle.type]}
                disabled={!remindersSupported}
                onValueChange={(v) => toggleReminder(toggle.type, v)}
                color={palette.acc}
              />
            </View>
          ))}

          {remindersSupported && (
            <>
              <Divider style={styles.innerDivider} />
              <View style={styles.reminderRow}>
                <Text variant="bodyMedium" style={styles.reminderLabel}>
                  {t('settings.weatherShift')}
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
                  ? t('settings.weatherShiftHint')
                  : t('settings.weatherShiftNeedsWater')}
              </Text>
              <Divider style={styles.innerDivider} />
              <View style={styles.reminderRow}>
                <Text variant="bodyMedium" style={styles.reminderLabel}>
                  {`❄️ ${t('settings.frostAlerts')}`}
                </Text>
                <Switch
                  value={seasonalAlerts}
                  onValueChange={toggleSeasonalAlerts}
                  color={palette.acc}
                  accessibilityLabel={t('settings.frostAlerts')}
                />
              </View>
              <Text variant="bodySmall" style={styles.subHint}>
                {t('settings.frostAlertsHint')}
              </Text>
            </>
          )}
        </Card.Content>
      </Card>

      <Divider style={styles.divider} />

      <Card style={styles.card}>
        <Card.Title title={t('settings.privacy')} titleVariant="titleMedium" titleStyle={styles.cardTitle} />
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
          {/* The census was its own tab before 1.2.0; it lives here now,
              beside the switch that decides whether you are counted in it. */}
          <Button
            mode="text"
            compact
            icon="chart-bar"
            onPress={() => navigation.navigate('Census')}
            style={styles.censusLink}
            textColor={palette.acc}
            accessibilityLabel={t('settings.seeCensusA11y')}
          >
            {t('settings.seeCensus')}
          </Button>

          <Divider style={styles.innerDivider} />

          {visibleFlows(capabilities).map((flow) => {
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
                  accessibilityLabel={t(open ? 'settings.flowA11yHide' : 'settings.flowA11yShow', {
                    title: flow.title, destination: DESTINATION_LABELS[flow.destination],
                  })}
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
            {t('settings.readPolicy')}
          </Button>
        </Card.Content>
      </Card>

      <Divider style={styles.divider} />

      <Card style={styles.card}>
        <Card.Title title={t('settings.aboutSupport')} titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          <Text variant="bodySmall" style={styles.about}>
            PlantAdvocate v{APP_VERSION}
            {BUILD_NUMBER > 0 ? `  ·  ${t('settings.build', { number: BUILD_NUMBER, commit: BUILD_COMMIT })}` : ''}{'\n'}
            {t('settings.aboutBody')}{'\n\n'}
            {t('settings.perenual')}
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
            {t('settings.helpSupport')}
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
  censusLink: { alignSelf: 'flex-start', marginTop: 4 },
});
