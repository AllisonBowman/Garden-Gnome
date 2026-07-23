import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import * as SecureStore from 'expo-secure-store';
import { fetchPlants, fetchCareLogs } from '../api/plants';
import { fetchSpecies } from '../api/species';
import { fetchEnvironments, fetchEnvironmentWeather } from '../api/environments';
import { CareLog, CareType, Environment, Species } from '../types';
import {
  computeReminderPlan, ReminderPrefs, REMINDER_CARE_TYPES, WeatherSignal,
} from './plan';
import { computeWeatherSignal } from '../weather/signal';

const PREFS_KEY = 'garden_gnome_reminder_prefs';
const WEATHER_SHIFT_KEY = 'garden_gnome_weather_shift';
const CHANNEL_ID = 'care-reminders';

// expo-notifications has no web implementation (Android/iOS only in SDK 57)
const isSupported = Platform.OS !== 'web';

if (isSupported) {
  // Show reminders even while the app is open
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowBanner: true,
      shouldShowList: true,
      shouldPlaySound: true,
      shouldSetBadge: false,
    }),
  });
}

// ── Preferences (same storage pattern as api/client.ts) ──────────────────────

export async function getReminderPrefs(): Promise<ReminderPrefs> {
  const raw = Platform.OS === 'web'
    ? localStorage.getItem(PREFS_KEY)
    : await SecureStore.getItemAsync(PREFS_KEY);
  if (!raw) return {};
  try {
    const parsed = JSON.parse(raw) as ReminderPrefs;
    // Keep only known care types so a stale/corrupt value can't linger
    const prefs: ReminderPrefs = {};
    for (const t of REMINDER_CARE_TYPES) {
      if (parsed[t]) prefs[t] = true;
    }
    return prefs;
  } catch {
    return {};
  }
}

export async function setReminderPrefs(prefs: ReminderPrefs): Promise<void> {
  const value = JSON.stringify(prefs);
  if (Platform.OS === 'web') {
    localStorage.setItem(PREFS_KEY, value);
  } else {
    await SecureStore.setItemAsync(PREFS_KEY, value);
  }
}

// Whether the forecast may nudge watering reminders (default OFF — opt-in).
export async function getWeatherShiftPref(): Promise<boolean> {
  const raw = Platform.OS === 'web'
    ? localStorage.getItem(WEATHER_SHIFT_KEY)
    : await SecureStore.getItemAsync(WEATHER_SHIFT_KEY);
  return raw === '1';
}

export async function setWeatherShiftPref(enabled: boolean): Promise<void> {
  const value = enabled ? '1' : '0';
  if (Platform.OS === 'web') {
    localStorage.setItem(WEATHER_SHIFT_KEY, value);
  } else {
    await SecureStore.setItemAsync(WEATHER_SHIFT_KEY, value);
  }
}

// Build the per-environment weather nudge map used by the planner when the
// user has opted in. Only fetches weather for environments the outside world
// actually reaches and that have coordinates. Fully self-contained: any
// failure yields no signal for that environment, so reminders still schedule
// (just without the weather adjustment).
async function buildWeatherSignals(
  plants: { environment_id?: number }[],
): Promise<Record<number, WeatherSignal>> {
  const out: Record<number, WeatherSignal> = {};
  try {
    const envIds = [...new Set(
      plants.map((p) => p.environment_id).filter((id): id is number => id != null),
    )];
    if (!envIds.length) return out;

    const envById: Record<number, Environment> = {};
    for (const env of await fetchEnvironments()) envById[env.id] = env;

    await Promise.all(envIds.map(async (id) => {
      const env = envById[id];
      const weatherReaches = !!env
        && (env.temp_exposure === 'outdoor' || env.shelter !== 'sheltered');
      if (!weatherReaches || env.lat == null || env.lng == null) return;
      try {
        const resp = await fetchEnvironmentWeather(id);
        if (resp.available && resp.weather) {
          out[id] = computeWeatherSignal(env, resp.weather);
        }
      } catch {
        // Skip this environment's nudge; the rest still apply.
      }
    }));
  } catch {
    // No environments/weather available — return an empty map (no nudges).
  }
  return out;
}

// ── Permissions ───────────────────────────────────────────────────────────────

/** True if notifications are currently permitted (never prompts). */
export async function hasNotificationPermission(): Promise<boolean> {
  if (!isSupported) return false;
  const settings = await Notifications.getPermissionsAsync();
  return settings.granted
    || settings.ios?.status === Notifications.IosAuthorizationStatus.PROVISIONAL;
}

/**
 * Ask for permission if not yet granted (triggers the OS prompt on first
 * use — both the iOS dialog and the Android 13+ runtime prompt).
 */
export async function ensureNotificationPermission(): Promise<boolean> {
  if (!isSupported) return false;
  if (await hasNotificationPermission()) return true;
  const res = await Notifications.requestPermissionsAsync({
    ios: { allowAlert: true, allowBadge: true, allowSound: true },
  });
  return res.granted
    || res.ios?.status === Notifications.IosAuthorizationStatus.PROVISIONAL;
}

// ── Scheduling ────────────────────────────────────────────────────────────────

let inFlight = false;

/**
 * Recompute the full reminder schedule from live data and replace all
 * pending notifications. Called on app start, after logging care, after
 * adding a plant, and when reminder settings change. Safe to fire-and-forget:
 * failures (e.g. offline) leave the previous schedule in place.
 */
export async function rescheduleAllReminders(): Promise<void> {
  if (!isSupported || inFlight) return;
  inFlight = true;
  try {
    const prefs = await getReminderPrefs();
    const anyEnabled = REMINDER_CARE_TYPES.some((t) => prefs[t]);
    if (!anyEnabled) {
      await Notifications.cancelAllScheduledNotificationsAsync();
      return;
    }
    if (!(await hasNotificationPermission())) return;

    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync(CHANNEL_ID, {
        name: 'Care reminders',
        importance: Notifications.AndroidImportance.DEFAULT,
        lightColor: '#2D6A4F',
      });
    }

    const plants = await fetchPlants();

    const logsByPlant: Record<number, CareLog[]> = {};
    await Promise.all(plants.map(async (p) => {
      logsByPlant[p.id] = await fetchCareLogs(p.id);
    }));

    // Plant lists embed species WITHOUT care_schedules; fetch details once
    // per unique species
    const speciesIds = [...new Set(plants.map((p) => p.species_id))];
    const speciesById: Record<number, Species> = {};
    await Promise.all(speciesIds.map(async (id) => {
      speciesById[id] = await fetchSpecies(id);
    }));

    // Opt-in: let the forecast nudge watering due-dates (default off).
    const weatherByEnv = (await getWeatherShiftPref())
      ? await buildWeatherSignals(plants)
      : undefined;

    const batches = computeReminderPlan({
      plants, logsByPlant, speciesById, prefs, weatherByEnv,
    });

    // This app schedules no other local notifications, so a full replace is safe
    await Notifications.cancelAllScheduledNotificationsAsync();
    for (const batch of batches) {
      await Notifications.scheduleNotificationAsync({
        content: { title: batch.title, body: batch.body, sound: true },
        trigger: {
          type: Notifications.SchedulableTriggerInputTypes.DATE,
          date: batch.date,
          channelId: CHANNEL_ID,
        },
      });
    }
  } catch {
    // Offline or backend unreachable — keep the previously scheduled
    // reminders; the next successful reschedule will refresh them.
  } finally {
    inFlight = false;
  }
}
