import { AppState, Platform } from 'react-native';
import axios from 'axios';
import * as Notifications from 'expo-notifications';
import * as SecureStore from 'expo-secure-store';
import { loadGardenCareData } from '../api/plants';
import { fetchGrowingAreas, fetchGrowingAreaWeather } from '../api/growingAreas';
import { fetchPropertiesOrOff, fetchSeasonalPlan, fetchZones } from '../api/properties';
import { GrowingArea } from '../types';
import { SeasonalPlan } from '../types/site';
import {
  computeReminderPlan, ReminderPrefs, REMINDER_CARE_TYPES, WeatherSignal,
} from './plan';
import { fallHardeningStart, SeasonalInput } from '../season/alerts';
import { computeWeatherSignal } from '../weather/signal';
import { t } from '../i18n';

const PREFS_KEY = 'garden_gnome_reminder_prefs';
const WEATHER_SHIFT_KEY = 'garden_gnome_weather_shift';
const SEASONAL_ALERTS_KEY = 'garden_gnome_seasonal_alerts';
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

// "Frost and weather alerts" (default OFF, opt-in; PLAN.md section 7). Its
// own switch, honoured even when every care-type switch is off.
export async function getSeasonalAlertsPref(): Promise<boolean> {
  const raw = Platform.OS === 'web'
    ? localStorage.getItem(SEASONAL_ALERTS_KEY)
    : await SecureStore.getItemAsync(SEASONAL_ALERTS_KEY);
  return raw === '1';
}

export async function setSeasonalAlertsPref(enabled: boolean): Promise<void> {
  const value = enabled ? '1' : '0';
  if (Platform.OS === 'web') {
    localStorage.setItem(SEASONAL_ALERTS_KEY, value);
  } else {
    await SecureStore.setItemAsync(SEASONAL_ALERTS_KEY, value);
  }
}

/** A seasonal plan, or null when this server has the season feature off
 *  (it answers 404). Any other failure throws. */
async function seasonalPlanOrOff(propertyId: number): Promise<SeasonalPlan | null> {
  try {
    return await fetchSeasonalPlan(propertyId);
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 404) return null;
    throw err;
  }
}

interface SeasonalLoad {
  seasonal: SeasonalInput;
  outdoorFeedingStop: { growingAreaIds: number[]; from: Date } | null;
}

/**
 * Every property's seasonal plan: its alerts (merged; the planner applies
 * the daily, weekly and total limits across them) and, for the feeding
 * gate, the property's zones once fall hardening has begun. Null when the
 * feature is off or the person has no property. Throws on a failed load, so
 * the caller can keep the previous schedule.
 */
async function loadSeasonal(needZones: boolean): Promise<SeasonalLoad | null> {
  const properties = await fetchPropertiesOrOff();
  if (!properties?.length) return null;
  const alerts: SeasonalInput['alerts'] = [];
  const events: NonNullable<SeasonalInput['events']> = [];
  const zoneIds: number[] = [];
  let from: Date | null = null;
  for (const prop of properties) {
    const plan = await seasonalPlanOrOff(prop.id);
    if (!plan) continue;
    alerts.push(...plan.alerts);
    events.push(...plan.events);
    const start = fallHardeningStart(plan);
    if (needZones && start) {
      for (const z of await fetchZones(prop.id)) zoneIds.push(z.growing_area_id);
      // The earliest start across properties is the cautious one.
      if (!from || start < from) from = start;
    }
  }
  return {
    seasonal: { alerts, events },
    outdoorFeedingStop: from && zoneIds.length ? { growingAreaIds: zoneIds, from } : null,
  };
}

// Build the per-growing area weather nudge map used by the planner when the
// user has opted in. Only fetches weather for growing areas the outside world
// actually reaches and that have coordinates. Fully self-contained: any
// failure yields no signal for that growing area, so reminders still schedule
// (just without the weather adjustment).
async function buildWeatherSignals(
  plants: { growing_area_id?: number }[],
): Promise<Record<number, WeatherSignal>> {
  const out: Record<number, WeatherSignal> = {};
  try {
    const envIds = [...new Set(
      plants.map((p) => p.growing_area_id).filter((id): id is number => id != null),
    )];
    if (!envIds.length) return out;

    const envById: Record<number, GrowingArea> = {};
    for (const env of await fetchGrowingAreas()) envById[env.id] = env;

    await Promise.all(envIds.map(async (id) => {
      const env = envById[id];
      const weatherReaches = !!env
        && (env.temp_exposure === 'outdoor' || env.shelter !== 'sheltered');
      if (!weatherReaches || env.lat == null || env.lng == null) return;
      try {
        const resp = await fetchGrowingAreaWeather(id);
        if (resp.available && resp.weather) {
          out[id] = computeWeatherSignal(env, resp.weather);
        }
      } catch {
        // Skip this growing area's nudge; the rest still apply.
      }
    }));
  } catch {
    // No growing area / weather available — return an empty map (no nudges).
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

/**
 * Forget every scheduled reminder. Called when a session ends, so the next
 * account on this phone is never nudged about the last one's plants.
 */
export async function cancelAllReminders(): Promise<void> {
  if (!isSupported) return;
  try {
    await Notifications.cancelAllScheduledNotificationsAsync();
  } catch {
    // Nothing scheduled, or no permission: nothing to cancel.
  }
}

let inFlight: Promise<void> | null = null;
let rerunWanted = false;

/**
 * Recompute the full schedule (care reminders and seasonal alerts, in one
 * planning pass) from live data and replace all pending notifications.
 * Called on app start, after logging care, after adding a plant, when
 * reminder settings change, and when the app returns to the foreground with
 * seasonal alerts on. Safe to fire-and-forget: failures (e.g. offline) leave
 * the previous schedule in place.
 *
 * A call made while one is running is not dropped: the running pass is
 * followed by exactly one more, so the last change always lands in one
 * complete plan (AUDIT.md section 4.3).
 */
export function rescheduleAllReminders(): Promise<void> {
  if (!isSupported) return Promise.resolve();
  if (inFlight) {
    rerunWanted = true;
    return inFlight;
  }
  inFlight = (async () => {
    try {
      do {
        rerunWanted = false;
        await reschedulePass();
      } while (rerunWanted);
    } finally {
      inFlight = null;
    }
  })();
  return inFlight;
}

async function reschedulePass(): Promise<void> {
  try {
    const prefs = await getReminderPrefs();
    const anyCare = REMINDER_CARE_TYPES.some((t) => prefs[t]);
    const seasonalOn = await getSeasonalAlertsPref();
    if (!anyCare && !seasonalOn) {
      await Notifications.cancelAllScheduledNotificationsAsync();
      return;
    }
    if (!(await hasNotificationPermission())) return;

    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync(CHANNEL_ID, {
        name: t('notifications.channel'),
        importance: Notifications.AndroidImportance.DEFAULT,
        lightColor: '#2D6A4F',
      });
    }

    // The same load the to-do list and streaks read, joined if it is already
    // running (at launch it usually is). Plant lists embed species WITHOUT
    // care_schedules; the load fetches each species' record once. Skipped
    // when only seasonal alerts are on: they need no plants.
    let plants: Awaited<ReturnType<typeof loadGardenCareData>>['plants'] = [];
    let logsByPlant: Awaited<ReturnType<typeof loadGardenCareData>>['logsByPlant'] = {};
    let speciesById: Awaited<ReturnType<typeof loadGardenCareData>>['speciesById'] = {};
    if (anyCare) {
      const garden = await loadGardenCareData();
      // A plant whose log or species couldn't be read would lose its reminders
      // in the full replace below. Keep the previous schedule instead, exactly
      // as a failed load does; the next reschedule refreshes it.
      if (garden.unreadPlantIds.length > 0) return;
      ({ plants, logsByPlant, speciesById } = garden);
    }

    // The seasonal plan: its alerts when the owner turned them on, and the
    // fall feeding gate for outdoor plants when feeding checks are on. A
    // failed load with alerts on keeps the previous schedule (the replace
    // below would otherwise wipe the alerts already set); with alerts off it
    // only means no feeding gate this pass.
    let seasonalLoad: SeasonalLoad | null = null;
    if (seasonalOn || prefs.fertilize) {
      try {
        seasonalLoad = await loadSeasonal(!!prefs.fertilize);
      } catch {
        if (seasonalOn) return;
      }
    }

    // Opt-in: let the forecast nudge watering due-dates (default off).
    const weatherByEnv = anyCare && (await getWeatherShiftPref())
      ? await buildWeatherSignals(plants)
      : undefined;

    const batches = computeReminderPlan({
      plants, logsByPlant, speciesById, prefs, weatherByEnv,
      seasonal: seasonalOn ? seasonalLoad?.seasonal : null,
      outdoorFeedingStop: seasonalLoad?.outdoorFeedingStop ?? null,
    });

    // Every local notification this app sends comes from this one plan, so a
    // full replace is safe (seasonal alerts are rebuilt in the same pass).
    await Notifications.cancelAllScheduledNotificationsAsync();
    for (const batch of batches) {
      await Notifications.scheduleNotificationAsync({
        ...(batch.identifier ? { identifier: batch.identifier } : {}),
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
  }
}

// ── Returning to the app ──────────────────────────────────────────────────────

/** At most one foreground re-plan in this long, so flicking between apps
 *  does not refetch the plan every time. */
const FOREGROUND_REPLAN_MS = 15 * 60_000;
let lastForegroundReplan = 0;

// An on-device alert is only as fresh as the forecast it was built from, so
// with seasonal alerts on, coming back to the app re-plans with the newest
// forecast. Care reminders do not need this; they re-plan on every log.
if (isSupported) {
  AppState.addEventListener('change', (state) => {
    if (state !== 'active') return;
    const now = Date.now();
    if (now - lastForegroundReplan < FOREGROUND_REPLAN_MS) return;
    lastForegroundReplan = now;
    void getSeasonalAlertsPref()
      .then((on) => (on ? rescheduleAllReminders() : undefined))
      .catch(() => undefined);
  });
}
