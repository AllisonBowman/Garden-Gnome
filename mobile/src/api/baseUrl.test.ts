import { DEFAULT_BASE_URL, resolveBaseUrl } from './baseUrl';

test('the hosted default is https, which iOS release builds require', () => {
  expect(DEFAULT_BASE_URL.startsWith('https://')).toBe(true);
});

test('a build without the override card ignores a stored override', () => {
  // A keychain item from an old preview build survives deleting the app.
  expect(resolveBaseUrl('http://192.168.1.119:8000', false)).toBe(DEFAULT_BASE_URL);
});

test('a build with the override card uses the stored override', () => {
  expect(resolveBaseUrl('http://192.168.1.119:8000', true)).toBe('http://192.168.1.119:8000');
});

test('with nothing usable stored, every build uses the hosted default', () => {
  expect(resolveBaseUrl(null, true)).toBe(DEFAULT_BASE_URL);
  expect(resolveBaseUrl(undefined, true)).toBe(DEFAULT_BASE_URL);
  expect(resolveBaseUrl('   ', true)).toBe(DEFAULT_BASE_URL);
  expect(resolveBaseUrl(null, false)).toBe(DEFAULT_BASE_URL);
});
