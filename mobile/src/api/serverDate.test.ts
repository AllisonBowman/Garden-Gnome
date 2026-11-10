import { localDateString, parseServerDate } from './serverDate';

// The suite runs in America/New_York (jest.globalSetup.js), so a date-only
// string read as UTC midnight would land on the evening before. That is the
// case these tests exist for; on a UTC runner it would hide.
test('the suite runs west of UTC, where a UTC read of a date goes wrong', () => {
  expect(new Date(2026, 6, 8).getTimezoneOffset()).toBeGreaterThan(0);
  // The trap itself: the built-in parser puts this on July 7 here.
  expect(new Date('2026-07-08').getDate()).toBe(7);
});

test('a date-only string from the server is that day on the caretaker’s calendar', () => {
  const d = parseServerDate('2026-07-08')!;
  expect([d.getFullYear(), d.getMonth(), d.getDate()]).toEqual([2026, 6, 8]);
  expect([d.getHours(), d.getMinutes()]).toEqual([0, 0]);
});

test('a full timestamp is the instant it names', () => {
  expect(parseServerDate('2026-07-08T18:30:00Z')!.getTime()).toBe(Date.UTC(2026, 6, 8, 18, 30));
  expect(parseServerDate('2026-07-08T09:00:00')!.getHours()).toBe(9);
});

test('nothing that isn’t a date becomes one', () => {
  expect(parseServerDate(undefined)).toBeNull();
  expect(parseServerDate(null)).toBeNull();
  expect(parseServerDate('')).toBeNull();
  expect(parseServerDate('soon')).toBeNull();
  // No rolling a day that doesn't exist into the next month.
  expect(parseServerDate('2026-02-30')).toBeNull();
});

test('the phone’s own day goes out the way the server writes one', () => {
  expect(localDateString(new Date(2026, 0, 5, 23, 59))).toBe('2026-01-05');
  // Late evening here is already tomorrow in UTC; the day sent is still today's.
  const evening = new Date(2026, 6, 8, 21, 30);
  expect(evening.toISOString().slice(0, 10)).toBe('2026-07-09');
  expect(localDateString(evening)).toBe('2026-07-08');
  // And it reads back as the same day.
  expect(parseServerDate(localDateString(evening))!.getDate()).toBe(8);
});
