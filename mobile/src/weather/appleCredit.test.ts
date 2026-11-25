// The Apple Weather credit is a licence term, not justification: it must stay
// on the face of every screen that shows Apple's forecast, never only in How
// we know.
import { isAppleForecast } from './appleCredit';

declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');
const read = (rel: string): string => fs.readFileSync(path.join(__dirname, rel), 'utf8');

test('Apple forecasts are recognised by provider', () => {
  expect(isAppleForecast({ provider: 'weatherkit', provider_name: ' Weather' })).toBe(true);
  expect(isAppleForecast({ provider: 'nws', provider_name: 'National Weather Service' })).toBe(false);
});

test('Home and Season draw the credit on their face', () => {
  for (const screen of ['../screens/HomeScreen.tsx', '../screens/SeasonScreen.tsx']) {
    const src = read(screen);
    expect(src).toMatch(/<WeatherCredit/);
    expect(src).toMatch(/isAppleForecast/);
  }
});
