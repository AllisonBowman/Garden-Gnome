import {
  MAX_MONTHS, MIN_MONTHS, TIMELINE_CHAR_SHARE, TIMELINE_GEOMETRY, eventTone, seasonTimeline, timelineDrawsAnything,
  timelineHeight, titleRect, todayCaptionRect,
} from './timeline';
import { SeasonEventSummary } from '../types/site';

const today = new Date(2026, 10, 16); // 16 Nov 2026
const ev = (key: string, start: string | null, end: string | null, over: Partial<SeasonEventSummary> = {}): SeasonEventSummary => ({
  event_key: key, type: 'first_frost', title: key, status: 'expected',
  window: { start, end, text: '' }, owner_actions: [], sort_date: start,
  explained: {
    display: '', confidence: 'area_estimate', confidence_label: 'Area estimate', reason: '', sources: [], provenance: 'modelled',
  },
  ...over,
});
const opts = { width: 360, charWidth: 6, gap: 4 };

test('the axis starts the month before today and spans to the last window', () => {
  const t = seasonTimeline([ev('frost', '2026-11-20', '2026-12-05'), ev('spring', '2027-04-01', '2027-04-30', { type: 'spring_emergence' })], opts, today);
  expect(t.start).toEqual(new Date(2026, 9, 1));
  expect(t.months.map((m) => m.label)).toEqual(['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr']);
  expect(t.spanText).toBe('October 2026 to April 2027');
  expect(t.end).toEqual(new Date(2027, 4, 1));
  expect(t.todayX).not.toBeNull();
  expect(t.todayX!).toBeGreaterThan(t.months[1].x);
  expect(t.todayX!).toBeLessThan(t.months[2].x);
});

test('a window across the year boundary is one band', () => {
  const t = seasonTimeline([ev('dormancy', '2026-12-15', '2027-02-10', { type: 'dormancy' })], opts, today);
  const [b] = t.items;
  expect(b.kind).toBe('band');
  const jan = t.months.find((m) => m.label === 'Jan')!;
  expect(b.x0).toBeLessThan(jan.x);
  expect(b.x1).toBeGreaterThan(jan.x + jan.width);
  expect(b.clippedEnd).toBe(false);
});

test('the axis starts earlier for a window still open that began before last month', () => {
  const t = seasonTimeline([ev('leaf', '2026-09-10', '2026-11-30', { type: 'leaf_drop', status: 'happening' })], opts, today);
  expect(t.start).toEqual(new Date(2026, 8, 1));
  expect(t.items[0]).toMatchObject({ x0: expect.any(Number), live: true, clippedStart: false });
  expect(t.months.length).toBeGreaterThanOrEqual(MIN_MONTHS);
});

test('a window that closed before last month does not pull the axis back, and is left out', () => {
  const t = seasonTimeline([ev('old', '2026-03-01', '2026-03-20'), ev('soon', '2026-12-01', null)], opts, today);
  expect(t.start).toEqual(new Date(2026, 9, 1));
  expect(t.items.map((i) => i.event_key)).toEqual(['soon']);
  expect(t.leftOut).toEqual(['old']);
});

test('at most twelve months; a window past the end is cut and says so', () => {
  const t = seasonTimeline([ev('far', '2027-08-01', '2028-03-01'), ev('farther', '2028-06-01', null)], opts, today);
  expect(t.months).toHaveLength(MAX_MONTHS);
  expect(t.end).toEqual(new Date(2027, 9, 1));
  const far = t.items.find((i) => i.event_key === 'far')!;
  expect(far.clippedEnd).toBe(true);
  expect(far.x1).toBe(360);
  expect(far.a11y).toContain('Runs past the end of this timeline');
  expect(t.leftOut).toEqual(['farther']);
});

test('a single date is a mark; only an end date is a mark too', () => {
  const t = seasonTimeline([ev('a', '2026-12-01', null), ev('b', null, '2027-01-10'), ev('c', '2027-01-20', '2027-01-20')], opts, today);
  expect(t.items.map((i) => [i.event_key, i.kind, i.x0 === i.x1])).toEqual([
    ['a', 'mark', true], ['b', 'mark', true], ['c', 'mark', true],
  ]);
});

test('events without dates (or with dates that do not parse) are left out of the picture', () => {
  const t = seasonTimeline([ev('none', null, null), ev('bad', '2026-02-30', 'soon'), ev('ok', '2026-12-01', '2026-12-10')], opts, today);
  expect(t.items.map((i) => i.event_key)).toEqual(['ok']);
  expect(t.leftOut).toEqual(['none', 'bad']);
});

test('no events: the default span around today', () => {
  const t = seasonTimeline([], opts, today);
  expect(t.items).toEqual([]);
  expect(t.rows).toBe(0);
  expect(t.months).toHaveLength(MIN_MONTHS);
  expect(t.todayX).not.toBeNull();
});

test('a start after the end is read the right way round', () => {
  const [b] = seasonTimeline([ev('x', '2027-01-10', '2026-12-10')], opts, today).items;
  expect(b.kind).toBe('band');
  expect(b.x1).toBeGreaterThan(b.x0);
});

test('overlapping bands and titles go into separate rows; later ones reuse free rows', () => {
  const t = seasonTimeline([
    ev('first frost', '2026-11-20', '2026-12-05'),
    ev('first freeze', '2026-11-25', '2026-12-15', { type: 'first_freeze' }),
    ev('spring', '2027-04-01', '2027-04-30', { type: 'spring_emergence' }),
  ], opts, today);
  const row = (k: string) => t.items.find((i) => i.event_key === k)!.row;
  expect(row('first frost')).toBe(0);
  expect(row('first freeze')).toBe(1);
  expect(row('spring')).toBe(0);
  expect(t.rows).toBe(2);
  // Items in one row never overlap, titles included.
  for (const r of [0, 1]) {
    const inRow = t.items.filter((i) => i.row === r).sort((a, b) => a.x0 - b.x0);
    for (let k = 1; k < inRow.length; k++) {
      const prev = inRow[k - 1];
      expect(Math.max(prev.x1, prev.labelX + prev.labelWidth)).toBeLessThanOrEqual(Math.min(inRow[k].x0, inRow[k].labelX));
    }
  }
});

test('a title near the right edge is pulled inside the axis', () => {
  const t = seasonTimeline([ev('A long title for the very end', '2027-02-25', null)], { width: 200, charWidth: 6 }, today);
  const [m] = t.items;
  expect(m.labelX + m.labelWidth).toBeLessThanOrEqual(200);
});

test('a long window still open keeps today on the axis', () => {
  const t = seasonTimeline([ev('long', '2025-10-01', '2026-10-20', { type: 'dormancy' })], opts, today);
  expect(t.months).toHaveLength(MAX_MONTHS);
  expect(t.start).toEqual(new Date(2025, 11, 1));
  expect(t.todayX).not.toBeNull();
  expect(t.todayX!).toBeLessThan(360);
  expect(t.items[0].clippedStart).toBe(true);
  expect(t.items[0].a11y).toContain('Began before the start of this timeline');
});

test('tone from type and status', () => {
  expect(eventTone('first_frost', 'expected')).toBe('frost');
  expect(eventTone('leaf_drop', 'forecast')).toBe('autumn');
  expect(eventTone('tender_plants_out', 'typically_around')).toBe('spring');
  expect(eventTone('hard_freeze', 'done')).toBe('settled');
  expect(eventTone('dormancy', 'happened')).toBe('settled');
});

test('a sentence per event: title, when, status', () => {
  const t = seasonTimeline([
    ev('First frost', '2026-11-20', '2026-12-05', { window: { start: '2026-11-20', end: '2026-12-05', text: 'Late November to early December' } }),
    ev('Last frost', '2027-04-10', null, { status: 'typically_around', window: { start: '2027-04-10', end: null, text: '' } }),
  ], opts, today);
  expect(t.items[0].a11y).toBe('First frost: Late November to early December. Expected.');
  expect(t.items[1].a11y).toBe('Last frost: 10 April. Typically around.');
});

test('window dates are read as local days (no slip west of UTC)', () => {
  const t = seasonTimeline([ev('d', '2026-12-01', null)], { width: 365 }, new Date(2026, 11, 1));
  // Axis starts 1 Nov; 1 Dec is 30 days in.
  const span = (Date.UTC(t.end.getFullYear(), t.end.getMonth(), 1) - Date.UTC(2026, 10, 1)) / 86_400_000;
  expect(t.items[0].x0).toBeCloseTo((30 / span) * 365);
});

test('timelineDrawsAnything is false when no event has a date on the axis', () => {
  expect(timelineDrawsAnything([], today)).toBe(false);
  expect(timelineDrawsAnything([ev('a', null, null), ev('b', null, null)], today)).toBe(false);
  expect(timelineDrawsAnything([ev('a', null, null), ev('frost', '2026-11-20', '2026-12-05')], today)).toBe(true);
  // Agrees with the drawn layout at a real width.
  const events = [ev('old', '2020-01-01', '2020-01-05'), ev('frost', '2026-11-20', null)];
  expect(timelineDrawsAnything(events, today)).toBe(seasonTimeline(events, opts, today).items.length > 0);
});

describe('at phone width', () => {
  // A year of events across a 313 pt chart.
  const events = [
    ev('First frost', '2026-11-01', '2026-11-25'),
    ev('Leaf drop', '2026-10-20', '2026-11-30', { type: 'leaf_drop' }),
    ev('Dormancy', '2026-12-01', '2027-02-28', { type: 'dormancy' }),
    ev('Last frost', '2027-04-10', '2027-05-05', { type: 'last_frost' }),
    ev('Tender plants out', '2027-05-15', null, { type: 'tender_plants_out' }),
    ev('Fall hardening', '2027-08-15', '2027-09-30', { type: 'fall_hardening' }),
  ];
  const width = 313;
  const t = seasonTimeline(events, { width, charWidth: TIMELINE_GEOMETRY.titleSize * TIMELINE_CHAR_SHARE }, today);

  test('short month names only, each fitting its month; the span said once', () => {
    expect(t.months).toHaveLength(MAX_MONTHS);
    for (const m of t.months) {
      expect(m.label).toMatch(/^[A-Z][a-z]{2}$/);
      expect(m.label.length * TIMELINE_GEOMETRY.monthSize * TIMELINE_CHAR_SHARE).toBeLessThanOrEqual(m.width - 3);
    }
    expect(t.spanText).toBe('October 2026 to September 2027');
  });

  test('the Today caption never covers a title', () => {
    const cap = todayCaptionRect(t, width)!;
    expect(cap).not.toBeNull();
    expect(cap.left).toBeGreaterThanOrEqual(0);
    expect(cap.left + cap.width).toBeLessThanOrEqual(width);
    expect(cap.top + cap.height).toBeLessThanOrEqual(timelineHeight(t.rows));
    for (const it of t.items) {
      const r = titleRect(it);
      const overlap = r.left < cap.left + cap.width && cap.left < r.left + r.width
        && r.top < cap.top + cap.height && cap.top < r.top + r.height;
      expect(overlap).toBe(false);
    }
  });

  test('titles and their halos stay inside their rows and do not overlap one another', () => {
    const rects = t.items.map(titleRect);
    rects.forEach((a, i) => rects.slice(i + 1).forEach((b) => {
      const overlap = a.left < b.left + b.width && b.left < a.left + a.width
        && a.top < b.top + b.height && b.top < a.top + a.height;
      expect(overlap).toBe(false);
    }));
    for (const [i, r] of rects.entries()) {
      const rowTop = TIMELINE_GEOMETRY.axisH + t.items[i].row * TIMELINE_GEOMETRY.rowH;
      expect(r.top).toBeGreaterThanOrEqual(rowTop);
      expect(r.top + r.height).toBeLessThanOrEqual(rowTop + TIMELINE_GEOMETRY.rowH - TIMELINE_GEOMETRY.bandH - 4);
    }
  });

  test('no today line, no caption', () => {
    const past = seasonTimeline([ev('x', '2026-11-20', null)], opts, today);
    expect(todayCaptionRect({ ...past, todayX: null }, 360)).toBeNull();
  });
});
