// The scheduler itself, with the phone and the server replaced: seasonal
// alerts survive the full cancel-and-replace, and two overlapping
// reschedules leave one complete plan.

const store: Record<string, string> = {};
const scheduled: { identifier?: string; content: { title: string; body: string } }[] = [];
const appStateListeners: ((s: string) => void)[] = [];

jest.mock('react-native', () => ({
  Platform: { OS: 'ios' },
  AppState: { addEventListener: (_: string, fn: (s: string) => void) => { appStateListeners.push(fn); } },
}));
jest.mock('expo-secure-store', () => ({
  getItemAsync: async (k: string) => store[k] ?? null,
  setItemAsync: async (k: string, v: string) => { store[k] = v; },
}));
jest.mock('expo-notifications', () => ({
  setNotificationHandler: () => undefined,
  getPermissionsAsync: async () => ({ granted: true }),
  requestPermissionsAsync: async () => ({ granted: true }),
  IosAuthorizationStatus: { PROVISIONAL: 3 },
  AndroidImportance: { DEFAULT: 3 },
  SchedulableTriggerInputTypes: { DATE: 'date' },
  setNotificationChannelAsync: async () => undefined,
  cancelAllScheduledNotificationsAsync: jest.fn(async () => { scheduled.length = 0; }),
  scheduleNotificationAsync: jest.fn(async (req: { identifier?: string; content: { title: string; body: string } }) => {
    scheduled.push(req);
    return req.identifier ?? 'id';
  }),
}));
jest.mock('../api/plants', () => ({
  loadGardenCareData: jest.fn(async () => ({ plants: [], logsByPlant: {}, speciesById: {}, unreadPlantIds: [] })),
}));
jest.mock('../api/growingAreas', () => ({
  fetchGrowingAreas: async () => [], fetchGrowingAreaWeather: async () => ({ available: false }),
}));
const plan = {
  property_id: 1, generated_at: '', season_label: 'Fall 2026', events: [], notes: [],
  alerts: [] as unknown[],
};
const fetchSeasonalPlan = jest.fn(async () => plan);
jest.mock('../api/properties', () => ({
  fetchPropertiesOrOff: async () => [{ id: 1 }],
  fetchSeasonalPlan: (...a: unknown[]) => (fetchSeasonalPlan as unknown as (...x: unknown[]) => unknown)(...a),
  fetchZones: async () => [],
}));

import {
  rescheduleAllReminders, setReminderPrefs, setSeasonalAlertsPref,
} from './reminders';

function futureAlert(key: string, daysAhead: number) {
  const d = new Date();
  d.setDate(d.getDate() + daysAhead);
  d.setHours(15, 0, 0, 0);
  return {
    alert_key: key, event_key: 'ev', title: `Frost ${key}`, body: 'Cover tender plants.',
    fire_at: d.toISOString(), built_from_forecast_at: new Date().toISOString(),
  };
}

beforeEach(() => {
  for (const k of Object.keys(store)) delete store[k];
  scheduled.length = 0;
  fetchSeasonalPlan.mockClear();
  plan.alerts = [futureAlert('a1', 2)];
});

it('schedules seasonal alerts with every care type off, each body with its forecast time', async () => {
  await setSeasonalAlertsPref(true);
  await rescheduleAllReminders();
  expect(scheduled.map((s) => s.identifier)).toEqual(['a1']);
  expect(scheduled[0].content.body).toMatch(/Forecast as of .+\.$/);
});

it('rebuilds seasonal alerts on every replace, alongside care reminders', async () => {
  await setSeasonalAlertsPref(true);
  await setReminderPrefs({ water: true });
  await rescheduleAllReminders();
  await rescheduleAllReminders();
  expect(scheduled.map((s) => s.identifier)).toEqual(['a1']);
});

it('cancels everything when every switch is off', async () => {
  await setSeasonalAlertsPref(true);
  await rescheduleAllReminders();
  await setSeasonalAlertsPref(false);
  await rescheduleAllReminders();
  expect(scheduled).toEqual([]);
});

it('keeps the previous schedule when the plan cannot be loaded', async () => {
  await setSeasonalAlertsPref(true);
  await rescheduleAllReminders();
  fetchSeasonalPlan.mockImplementationOnce(async () => { throw new Error('offline'); });
  await rescheduleAllReminders();
  expect(scheduled.map((s) => s.identifier)).toEqual(['a1']);
});

it('runs one more pass for a call made mid-pass, so the newest plan lands once', async () => {
  await setSeasonalAlertsPref(true);
  const first = rescheduleAllReminders();
  plan.alerts = [futureAlert('a2', 3)];
  const second = rescheduleAllReminders();
  const third = rescheduleAllReminders();
  await Promise.all([first, second, third]);
  // Two calls during the first pass make one more pass, not two.
  expect(fetchSeasonalPlan).toHaveBeenCalledTimes(2);
  expect(scheduled.map((s) => s.identifier)).toEqual(['a2']);
});

it('re-plans when the app returns to the foreground with alerts on', async () => {
  await setSeasonalAlertsPref(true);
  expect(appStateListeners).toHaveLength(1);
  plan.alerts = [futureAlert('fresh', 1)];
  appStateListeners[0]('active');
  await new Promise((r) => setTimeout(r, 0));
  await rescheduleAllReminders();
  expect(scheduled.map((s) => s.identifier)).toEqual(['fresh']);
});
