// The Controls row on Home: large tiles, each stating its setting in words
// ("Frost and freeze alerts: On") and changing it, or opening it, in one
// tap. Solid fills, On and Off written out, at least 44 by 44 points, one
// accessibility element per tile. Two columns at ordinary text sizes; one
// column once the text is large, so a label 40 percent longer (Spanish,
// German) wraps instead of clipping.
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Platform, Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation/types';
import {
  ensureNotificationPermission, getReminderPrefs, getSeasonalAlertsPref, rescheduleAllReminders,
  setReminderPrefs, setSeasonalAlertsPref,
} from '../notifications/reminders';
import { REMINDER_CARE_TYPES, ReminderPrefs } from '../notifications/plan';
import { useUnits } from '../units/UnitsProvider';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette } from '../theme/tokens';
import { remindersOn, tilesStack } from './controlsState';
import { t } from '../i18n';

export interface ControlTileProps {
  /** The tile's whole sentence, state included: "Task reminders: On". */
  label: string;
  /** One quiet line under it, or none. */
  note?: string | null;
  /** On or off for a setting; undefined for a tile that opens a screen. */
  on?: boolean;
  /** What a screen reader hears as the name (the state is read from
   *  `accessibilityState` for a switch). */
  a11yLabel: string;
  a11yHint: string;
  icon: string;
  onPress: () => void;
  busy?: boolean;
}

export function ControlTile({ label, note, on, a11yLabel, a11yHint, icon, onPress, busy }: ControlTileProps) {
  const { palette, display } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, display.boldText), [palette, display.boldText]);
  const isSwitch = on !== undefined;
  const filled = on === true;
  const ink = filled ? palette.tileOnInk : palette.tileInk;
  return (
    <Pressable
      onPress={onPress}
      disabled={busy}
      accessibilityRole={isSwitch ? 'switch' : 'button'}
      accessibilityLabel={a11yLabel}
      accessibilityHint={a11yHint}
      accessibilityState={isSwitch ? { checked: on, disabled: !!busy } : { disabled: !!busy }}
      style={({ pressed }) => [
        styles.tile,
        { backgroundColor: filled ? palette.tileOn : palette.tile },
        pressed && styles.pressed,
      ]}
    >
      <View style={styles.row} importantForAccessibility="no-hide-descendants" accessibilityElementsHidden>
        <Text style={[styles.icon, { color: ink }]} maxFontSizeMultiplier={1.4}>{icon}</Text>
        <View style={styles.texts}>
          <Text style={[styles.label, { color: ink }]}>{label}</Text>
          {note ? <Text style={[styles.note, { color: ink }]}>{note}</Text> : null}
        </View>
        {isSwitch ? (
          // The state as a mark as well as the word: never color alone.
          <Text style={[styles.mark, { color: ink }]} maxFontSizeMultiplier={1.6}>{on ? '✓' : '○'}</Text>
        ) : <Text style={[styles.mark, { color: ink }]} maxFontSizeMultiplier={1.6}>›</Text>}
      </View>
    </Pressable>
  );
}

export interface ControlsRowProps {
  property: { id: number; name: string } | null;
  /** Drawn zones, or null while unknown. */
  zoneCount: number | null;
  /** The server can take a new property. */
  canAddLand: boolean;
}

export default function ControlsRow({ property, zoneCount, canAddLand }: ControlsRowProps) {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { fontScale } = useWindowDimensions();
  const { unit, setUnit } = useUnits();
  const [alerts, setAlerts] = useState(false);
  const [prefs, setPrefs] = useState<ReminderPrefs>({});
  const [busy, setBusy] = useState(false);
  const supported = Platform.OS !== 'web';

  // Read again whenever Home comes back into view: Settings can change both.
  const load = useCallback(() => {
    void getSeasonalAlertsPref().then(setAlerts);
    void getReminderPrefs().then(setPrefs);
  }, []);
  useEffect(load, [load]);
  useFocusEffect(load);

  const permissionOk = async (body: string): Promise<boolean> => {
    if (await ensureNotificationPermission()) return true;
    Alert.alert(t('settings.notificationsDisabled'), body);
    return false;
  };

  const toggleAlerts = async () => {
    setBusy(true);
    try {
      const next = !alerts;
      if (next && !(await permissionOk(t('settings.alertsNeedPermission')))) return;
      setAlerts(next);
      await setSeasonalAlertsPref(next);
      void rescheduleAllReminders();
    } finally { setBusy(false); }
  };

  const toggleReminders = async () => {
    setBusy(true);
    try {
      const next = !remindersOn(prefs);
      if (next && !(await permissionOk(t('settings.remindersNeedPermission')))) return;
      const all: ReminderPrefs = {};
      if (next) for (const k of REMINDER_CARE_TYPES) all[k] = true;
      setPrefs(all);
      await setReminderPrefs(all);
      void rescheduleAllReminders();
    } finally { setBusy(false); }
  };

  const tiles: (ControlTileProps & { key: string })[] = [];
  if (supported) {
    tiles.push({
      key: 'frost',
      icon: '❄️',
      label: alerts ? t('controls.frost.on') : t('controls.frost.off'),
      note: property ? (alerts ? t('controls.frost.onNote') : null) : t('controls.frost.needsLand'),
      on: alerts,
      a11yLabel: t('controls.frost.a11y'),
      a11yHint: alerts ? t('controls.hintTurnOff') : t('controls.hintTurnOn'),
      onPress: () => void toggleAlerts(),
      busy,
    });
  }
  if (property) {
    tiles.push({
      key: 'land', icon: '📍',
      label: t('controls.land.named', { name: property.name }),
      note: t('controls.land.note'),
      a11yLabel: t('controls.land.named', { name: property.name }),
      a11yHint: t('controls.land.hint'),
      onPress: () => navigation.navigate('Land', { propertyId: property.id }),
    });
    tiles.push({
      key: 'zones', icon: '🗺️',
      label: zoneCount ? t('controls.zones.count', { count: zoneCount }) : t('controls.zones.none'),
      a11yLabel: zoneCount ? t('controls.zones.count', { count: zoneCount }) : t('controls.zones.none'),
      a11yHint: t('controls.zones.hint'),
      onPress: () => navigation.navigate('ZoneMap', { propertyId: property.id }),
    });
    tiles.push({
      key: 'fix', icon: '✏️',
      label: t('controls.fix.label'),
      note: t('controls.fix.note'),
      a11yLabel: t('controls.fix.label'),
      a11yHint: t('controls.fix.hint'),
      onPress: () => navigation.navigate('Land', { propertyId: property.id }),
    });
  } else if (canAddLand) {
    tiles.push({
      key: 'land', icon: '📍',
      label: t('controls.land.add'),
      a11yLabel: t('controls.land.add'),
      a11yHint: t('controls.land.addHint'),
      onPress: () => navigation.navigate('PropertySetup'),
    });
  }
  tiles.push({
    key: 'units', icon: '🌡️',
    label: unit === 'C' ? t('controls.units.c') : t('controls.units.f'),
    a11yLabel: unit === 'C' ? t('controls.units.a11yC') : t('controls.units.a11yF'),
    a11yHint: unit === 'C' ? t('controls.units.hintToF') : t('controls.units.hintToC'),
    onPress: () => setUnit(unit === 'C' ? 'F' : 'C'),
  });
  if (supported) {
    const on = remindersOn(prefs);
    tiles.push({
      key: 'reminders', icon: '🔔',
      label: on ? t('controls.reminders.on') : t('controls.reminders.off'),
      note: on ? t('controls.reminders.onNote') : t('controls.reminders.offNote'),
      on,
      a11yLabel: t('controls.reminders.a11y'),
      a11yHint: on ? t('controls.hintTurnOff') : t('controls.hintTurnOn'),
      onPress: () => void toggleReminders(),
      busy,
    });
  }

  const stack = tilesStack(fontScale);
  return (
    <View style={stack ? styles.stack : styles.grid}>
      {tiles.map(({ key, ...p }) => (
        <View key={key} style={stack ? styles.full : styles.half}>
          <ControlTile {...p} />
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: { flexDirection: 'row', flexWrap: 'wrap', marginHorizontal: -5 },
  stack: { gap: 10 },
  half: { width: '50%', padding: 5 },
  full: { width: '100%' },
});

const makeStyles = (p: Palette, bold: boolean) => StyleSheet.create({
  tile: {
    minHeight: 64, minWidth: 44, borderRadius: 14, borderWidth: 2, borderColor: p.tileBorder,
    paddingHorizontal: 12, paddingVertical: 12, justifyContent: 'center', flexGrow: 1,
  },
  pressed: { opacity: 0.85 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  icon: { fontSize: 20 },
  texts: { flex: 1 },
  label: { fontSize: 16, lineHeight: 21, fontWeight: bold ? '800' : '700' },
  note: { fontSize: 13, lineHeight: 18, marginTop: 2, fontWeight: bold ? '600' : '400' },
  mark: { fontSize: 18, fontWeight: '800' },
});
