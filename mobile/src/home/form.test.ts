import { homeForm, offersAddLand, usesLegacyRoutes } from './form';
import { Vitals, Property } from '../types/site';

const base: Vitals = {
  generated_at: '2026-11-15T12:00:00Z', headline: '', property: null, forecast: null,
  cards: [], this_week: [], season_ahead: [], spaces: [], notes: [],
};
const property = { id: 1 } as Property;

test('nothing yet is loading, and a failed first load is failed', () => {
  expect(homeForm({ vitals: undefined, failed: false })).toBe('loading');
  expect(homeForm({ vitals: undefined, failed: true })).toBe('failed');
});

test('a 404 for the new routes is the feature-off form, never an error', () => {
  expect(homeForm({ vitals: null, failed: false })).toBe('feature_off');
  expect(usesLegacyRoutes('feature_off')).toBe(true);
  expect(offersAddLand('feature_off', null)).toBe(false);
});

test('no property is the apartment form, with the one calm offer', () => {
  const canAdd = { ...base, can_add_land: true };
  expect(homeForm({ vitals: canAdd, failed: false })).toBe('no_land');
  expect(offersAddLand('no_land', canAdd)).toBe(true);
  expect(usesLegacyRoutes('no_land')).toBe(false);
});

test('a property is the land form, and no offer to add one', () => {
  expect(homeForm({ vitals: { ...base, property }, failed: false })).toBe('land');
  expect(offersAddLand('land', { ...base, property, can_add_land: true })).toBe(false);
});

test('no offer when the season is on but the land routes are off (adding would 404)', () => {
  expect(homeForm({ vitals: base, failed: false })).toBe('no_land');
  expect(offersAddLand('no_land', { ...base, can_add_land: false })).toBe(false);
  expect(offersAddLand('no_land', base)).toBe(false);
});

test('a refresh that fails after a load keeps the form it had', () => {
  expect(homeForm({ vitals: { ...base, property }, failed: true })).toBe('land');
  expect(homeForm({ vitals: base, failed: true })).toBe('no_land');
});
