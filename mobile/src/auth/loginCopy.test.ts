import { SIGN_IN_REASON } from './loginCopy';

declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');
const readSrc = (rel: string): string => fs.readFileSync(path.join(__dirname, rel), 'utf8');

test('the login screen says, in one sentence, why there is an account', () => {
  // One sentence: a single full stop, at the end.
  expect(SIGN_IN_REASON.match(/\./g)).toHaveLength(1);
  expect(SIGN_IN_REASON.endsWith('.')).toBe(true);
  // ...that signing in is what makes the account...
  expect(SIGN_IN_REASON).toMatch(/^Signing in creates your account/);
  // ...and what it is for, in the app's own words.
  expect(SIGN_IN_REASON).toMatch(/plants/);
  expect(SIGN_IN_REASON).toMatch(/growing areas/);
  expect(SIGN_IN_REASON).toMatch(/new phone/);
  expect(SIGN_IN_REASON).not.toMatch(/environment/i);
});

test('the sentence is on the screen, above the sign-in buttons', () => {
  const screen = readSrc('./LoginScreen.tsx');
  const shown = screen.indexOf('{SIGN_IN_REASON}');
  expect(shown).toBeGreaterThan(-1);
  expect(shown).toBeLessThan(screen.indexOf('AppleAuthenticationButton\n'));
});
