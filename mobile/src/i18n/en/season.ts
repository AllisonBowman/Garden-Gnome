// English strings: season. The source of truth; es/season.ts mirrors its keys.
// Also holds the calendar words (dates) the Home, Season and forecast code shares.
const season = {
  dates: {
    weekdaysShort: 'Sun,Mon,Tue,Wed,Thu,Fri,Sat',
    weekdaysLong: 'Sunday,Monday,Tuesday,Wednesday,Thursday,Friday,Saturday',
    monthsShort: 'Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec',
    monthsLong: 'January,February,March,April,May,June,July,August,September,October,November,December',
    today: 'Today',
    tomorrow: 'Tomorrow',
    yesterday: 'Yesterday',
    /** "Tue 17 Nov" */
    shortDay: '{{weekday}} {{day}} {{month}}',
    /** "12 November" */
    spokenDay: '{{day}} {{month}}',
    clockHour: '{{hour}} {{ampm}}',
    clockMinute: '{{hour}}:{{minute}} {{ampm}}',
    am: 'am',
    pm: 'pm',
  },
  status: {
    happened: 'Recorded for your area',
    happening: 'Happening now',
    forecast: 'In the forecast',
    expected: 'Expected',
    typically_around: 'Typically around',
    done: 'Done',
    not_needed: 'Not needed this year',
  },
  actions: {
    mark_happened: 'It happened here',
    mark_not_yet: 'Not yet at my place',
    mark_done: 'Done',
    mark_not_needed: 'Not needed',
    clear: 'Clear my answer',
  },
  sections: {
    now: 'Needs attention now',
    ahead: 'The next twelve months',
    settled: 'Already happened or settled',
  },
  taskStates: {
    open: 'To do',
    done: 'Done',
    not_needed: 'Not needed',
  },
  frostRisk: {
    frost: 'Frost possible',
    freeze: 'Freeze',
    hard_freeze: 'Hard freeze',
  },
  cells: {
    noTemperature: 'No temperature',
    rain: '{{pct}}% rain',
    a11yHigh: 'high {{temp}} {{unit}}',
    a11yLow: 'low {{temp}} {{unit}}',
    a11yRain: '{{pct}} percent chance of rain',
  },
  credit: {
    providerFallback: 'the forecast provider',
    forecastBy: 'Forecast: {{name}}.',
    forecastByAsOf: 'Forecast: {{name}}, as of {{time}} {{day}}.',
  },
  frostNights: 'Frost in the forecast: {{nights}}.',
  frostNight: '{{day}} ({{risk}})',
  alerts: {
    asOf: 'Forecast as of {{time}} on {{weekday}} {{day}} {{month}}.',
    data: 'Data: {{source}}.',
  },
  timeline: {
    range: '{{from}} to {{to}}',
    runsPast: 'Runs past the end of this timeline',
    beganBefore: 'Began before the start of this timeline',
    span: '{{from}} {{fromYear}} to {{to}} {{toYear}}',
    opensEvent: 'Opens this event',
  },
  screen: {
    titleFallback: 'Your seasonal plan',
    loadFailed: 'Couldn’t load your seasonal plan.',
    noForecast: 'No forecast right now. Dates below are typical dates for your area, not this year\'s forecast.',
    notSaved: 'That answer was not saved. Check your connection and try again.',
    yearAtAGlance: 'The year at a glance',
    empty: 'Nothing is in your seasonal plan yet.',
    forecast: 'Forecast',
    whenHappened: 'When did it happen at your place?',
    happenedToday: 'It happened today',
    happenedYesterday: 'It happened yesterday',
    happenedOn: 'It happened on {{day}}',
    whyTaskA11y: '{{why}} for this task. {{toggle}}.',
    hide: 'Hide',
    show: 'Show',
    data: 'Data: {{source}}',
  },
};

export default season;
