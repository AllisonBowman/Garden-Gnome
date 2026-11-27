// English strings: settings. The source of truth; es/settings.ts mirrors its keys.
const settings = {
  reminderToggles: {
    water: 'Watering checks',
    fertilize: 'Feeding checks',
    prune: 'Pruning checks',
    repot: 'Spring repot check',
    rotate: 'Turning checks',
  },
  remindersHint:
    'Get a nudge to look at a plant when it reaches its usual window, based on its '
    + 'species’ check schedule and your care log. Plants due the same day share one '
    + 'notification. A plant whose species has no check schedule on record gets no '
    + 'reminders. Reminders are planned a month ahead each time you open '
    + 'PlantAdvocate, so open it at least once a month to keep them coming.',
  remindersMobileOnly: 'Reminders are available in the mobile app (iOS and Android).',
  deleteConfirm: {
    title: 'Delete your account?',
    body: 'This permanently deletes your account, plants, care history, and '
      + 'growing areas from PlantAdvocate. This cannot be undone.',
    confirm: 'Delete forever',
  },
  deleteFailed: {
    title: 'Deletion failed',
    body: 'PlantAdvocate could not delete your account. Check your connection and try again.',
  },
  censusFailed: {
    title: 'Could not save that',
    body: 'PlantAdvocate could not reach the server to change your census '
      + 'setting, so nothing has changed. Check your connection and try again.',
  },
  notificationsDisabled: 'Notifications disabled',
  alertsNeedPermission: 'PlantAdvocate needs notification permission for frost and weather alerts. You can enable it in your device settings.',
  remindersNeedPermission: 'PlantAdvocate needs notification permission for care reminders. You can enable it in your device settings.',
  account: 'Account',
  signedIn: 'Signed in',
  signOut: 'Sign out',
  deleteAccount: 'Delete account',
  appearance: 'Appearance',
  themeDark: '🌙 Observatory (dark)',
  themeLight: '☀️ Almanac (light)',
  themeHint: 'Almanac is the warm field-notebook look; Observatory is a dark, colorblind-safe night theme.',
  celsius: 'Show temperatures in Celsius',
  unitsHint: 'Temperatures the app writes itself. Forecasts and the season plan arrive in °F and are converted; a few notes from the server may still read in °F.',
  careReminders: 'Care reminders',
  weatherShift: '🌦️ Let weather adjust watering',
  weatherShiftHint: 'Nudges watering reminders by a day or two for outdoor, unsheltered plants. Later before rain, sooner in a heat spike. Needs a location on the growing area.',
  weatherShiftNeedsWater: 'Turn on watering reminders above to use this.',
  frostAlerts: 'Frost and weather alerts',
  frostAlertsHint: 'A note before a frost or freeze night and other moments in your seasonal plan, at most one a day and none between 9 pm and 8 am. Each alert uses the forecast from the last time you opened the app and says when that forecast was made, so it can be out of date. Needs your land added.',
  privacy: 'Privacy & data',
  seeCensus: 'See the census',
  seeCensusA11y: 'See the census of what everyone grows',
  flowA11yShow: '{{title}}. {{destination}}. Show details.',
  flowA11yHide: '{{title}}. {{destination}}. Hide details.',
  readPolicy: 'Read the full policy',
  aboutSupport: 'About & Support',
  build: 'build {{number}} ({{commit}})',
  aboutBody: 'Every plant deserves an advocate. Care schedules, reminders, and a care engine grounded in a curated species database.',
  perenual: 'Species data provided in part by Perenual (perenual.com).',
  helpSupport: 'Help & support',
};

export default settings;
