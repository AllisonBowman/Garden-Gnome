// English strings: the Controls row on Home. The source of truth;
// es/controls.ts mirrors its keys. Each tile's text is one whole sentence
// per state, so a translation never glues a label to a state word.
const controls = {
  title: 'Controls',
  settings: 'Settings',
  settingsA11y: 'Settings',
  settingsHint: 'Opens all settings.',
  hintTurnOn: 'Double tap to turn on.',
  hintTurnOff: 'Double tap to turn off.',
  frost: {
    on: 'Frost and freeze alerts: On',
    off: 'Frost and freeze alerts: Off',
    a11y: 'Frost and freeze alerts',
    needsLand: 'Starts once your land is added.',
    onNote: 'A note before a frost or freeze night.',
  },
  land: {
    named: 'Your land: {{name}}',
    add: 'Add your land',
    hint: 'Opens your land.',
    addHint: 'Opens the steps to add your land.',
    note: 'Edit the pin, or add another place.',
  },
  zones: {
    count_one: 'Zones: 1',
    count_other: 'Zones: {{count}}',
    none: 'Zones: none yet. Add a zone',
    hint: 'Opens the zone map on the aerial view.',
  },
  fix: {
    label: 'Not right? Fix it',
    hint: 'Opens your land, where any value can be corrected.',
    note: 'Correct any value about your land.',
  },
  units: {
    f: 'Temperatures: °F',
    c: 'Temperatures: °C',
    a11yF: 'Temperatures in Fahrenheit',
    a11yC: 'Temperatures in Celsius',
    hintToC: 'Double tap to switch to Celsius.',
    hintToF: 'Double tap to switch to Fahrenheit.',
  },
  reminders: {
    on: 'Task reminders: On',
    off: 'Task reminders: Off',
    a11y: 'Task reminders',
    onNote: 'Settings has each kind of check.',
    offNote: 'Turns on every kind of plant check.',
  },
};

export default controls;
