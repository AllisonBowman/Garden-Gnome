import { EVENT_STATUS_WORDS, profileProgressLine, seasonAhead } from './season';
import { SeasonEventSummary } from '../types/site';

const ev = (key: string, sort_date: string | null): SeasonEventSummary => ({
  event_key: key, type: 'leaf_drop', title: key, status: 'expected',
  window: { text: 'around early November' },
  explained: {
    display: '', confidence: 'area_estimate', confidence_label: 'Area estimate',
    reason: 'r', sources: [{ name: 's' }], provenance: 'modelled',
  },
  owner_actions: [], sort_date,
});

test('the next few events in date order, undated ones last', () => {
  const out = seasonAhead([ev('c', '2027-03-01'), ev('x', null), ev('a', '2026-11-20'), ev('b', '2026-12-01')], 3);
  expect(out.map((e) => e.event_key)).toEqual(['a', 'b', 'c']);
});

test('every status has words', () => {
  for (const w of Object.values(EVENT_STATUS_WORDS)) expect(w.trim()).not.toBe('');
});

test('progress lines', () => {
  expect(profileProgressLine({ fast: 'ready', background: 'ready' })).toBeNull();
  expect(profileProgressLine({ fast: 'building', background: 'pending' })).toMatch(/^Still reading your land/);
  expect(profileProgressLine({ fast: 'ready', background: 'building' })).toMatch(/slope, tree cover/);
  expect(profileProgressLine({ fast: 'ready', background: 'failed' })).toMatch(/try them again/);
  expect(profileProgressLine(null)).toBeNull();
});
