import { dayWord, nextFrostNight, nightWord, pickHeadline, riskFromLow } from './headline';

// A Sunday morning. jest.globalSetup pins one time zone for every run.
const today = new Date(2026, 10, 15, 9, 0);

test('the server headline wins when there is one', () => {
  expect(pickHeadline({ serverHeadline: ' Leaves are down. ', days: [], careDue: 3, openSeasonTasks: 1, today }))
    .toBe('Leaves are down.');
});

test('with none, a frost in the next three days leads', () => {
  const days = [
    { date: '2026-11-15', low_f: 40 },
    { date: '2026-11-17', low_f: 30 },
  ];
  expect(pickHeadline({ serverHeadline: '', days, careDue: 0, openSeasonTasks: 0, today }))
    .toBe('A freeze is possible Tuesday night.');
});

test('the forecast\'s own risk is used over the low', () => {
  const days = [{ date: '2026-11-15', low_f: 35, frost_risk: 'hard_freeze' as const }];
  expect(pickHeadline({ days, careDue: 2, openSeasonTasks: 0, today }))
    .toBe('A hard freeze is possible tonight. 2 plants are worth a look.');
});

test('a frost past the lookahead or in the past is not news', () => {
  const days = [{ date: '2026-11-14', low_f: 20 }, { date: '2026-11-19', low_f: 20 }];
  expect(nextFrostNight(days, today)).toBeNull();
});

test('counts of what is due, then a calm line when nothing is', () => {
  expect(pickHeadline({ days: [], careDue: 1, openSeasonTasks: 0, today })).toBe('1 plant is worth a look.');
  expect(pickHeadline({ days: [], careDue: 1, openSeasonTasks: 2, today })).toBe('3 things to do this week.');
  expect(pickHeadline({ days: [], careDue: 0, openSeasonTasks: 0, today })).toBe('Nothing needs you today.');
});

test('frost thresholds', () => {
  expect(riskFromLow(null)).toBe('none');
  expect(riskFromLow(37)).toBe('none');
  expect(riskFromLow(36)).toBe('frost');
  expect(riskFromLow(32)).toBe('freeze');
  expect(riskFromLow(28)).toBe('hard_freeze');
});

test('day words', () => {
  expect(dayWord(new Date(2026, 10, 15), today)).toBe('today');
  expect(nightWord(new Date(2026, 10, 15), today)).toBe('tonight');
  expect(nightWord(new Date(2026, 10, 16), today)).toBe('tomorrow night');
  expect(dayWord(new Date(2026, 10, 18), today)).toBe('Wednesday');
});

test('no headline has an em dash', () => {
  const lines = [
    pickHeadline({ days: [{ date: '2026-11-16', low_f: 34 }], careDue: 4, openSeasonTasks: 1, today }),
    pickHeadline({ days: [], careDue: 0, openSeasonTasks: 0, today }),
  ];
  for (const l of lines) expect(l).not.toMatch(/—/);
});
