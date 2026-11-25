import { almanacDate, firstSentence, oneThing, seasonOf, seasonWeekLine, weekOfSeason } from './almanac';

const d = (y: number, m: number, day: number) => new Date(y, m - 1, day);

test('calendar seasons, and the week counted from the first of the season', () => {
  expect(seasonOf(d(2026, 11, 24)).season).toBe('fall');
  expect(weekOfSeason(d(2026, 9, 1))).toBe(1);
  expect(weekOfSeason(d(2026, 9, 7))).toBe(1);
  expect(weekOfSeason(d(2026, 9, 8))).toBe(2);
  expect(seasonWeekLine(d(2026, 11, 24))).toBe('Week 13 of fall');
  // January belongs to the winter that began last December.
  expect(seasonOf(d(2027, 1, 10))).toEqual({ season: 'winter', start: d(2026, 12, 1) });
  expect(seasonWeekLine(d(2027, 1, 10))).toBe('Week 6 of winter');
  expect(seasonOf(d(2026, 3, 1)).season).toBe('spring');
  expect(seasonOf(d(2026, 6, 30)).season).toBe('summer');
});

test('the date line in words', () => {
  expect(almanacDate(d(2026, 11, 24))).toBe('Tuesday, November 24');
});

test('the one thing that matters is the headline’s first sentence', () => {
  const server = 'Frost possible tonight. Low near 35 °F. Trees are hardening for winter.';
  expect(oneThing(server, 'Nothing needs you today.', false))
    .toEqual({ line: 'Frost possible tonight.', fromServer: true, full: server });
  // A decimal point does not end a sentence.
  expect(firstSentence('About 5.5 hours of sun. More text.')).toBe('About 5.5 hours of sun.');
});

test('in °C, a first sentence quoting °F gives way to the phone’s own line', () => {
  const server = 'Low near 35 °F tonight. Cover tender plants.';
  expect(oneThing(server, 'Frost is possible tonight. 2 things to do this week.', true))
    .toEqual({ line: 'Frost is possible tonight.', fromServer: false, full: server });
});

test('with no server headline the phone’s line is used', () => {
  expect(oneThing(null, 'Nothing needs you today.', false))
    .toEqual({ line: 'Nothing needs you today.', fromServer: false, full: null });
});
