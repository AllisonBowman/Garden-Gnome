// APP_VERSION labels Settings and every support and report email. It is a
// hand-copied string, and it has drifted once already: 1.1.3 nearly shipped
// calling itself 1.1.2 to every tester who wrote in. This pins it to the
// version App Store Connect will actually show.
//
// support.ts imports react-native, which jest here cannot load, so the
// constant is read from source the way census.keys.test.ts reads the server.
declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');

const read = (rel: string): string =>
  fs.readFileSync(path.join(__dirname, rel), 'utf8');

test('the version the app reports is the version in app.json', () => {
  const appJson = JSON.parse(read('../app.json'));
  const support = read('./support.ts');
  const match = support.match(/export const APP_VERSION = '([^']+)';/);
  expect(match).not.toBeNull();
  expect(match![1]).toBe(appJson.expo.version);
});
