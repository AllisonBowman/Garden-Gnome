import { createSignInGate } from './signInGate';

declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');
const readSrc = (rel: string): string => fs.readFileSync(path.join(__dirname, rel), 'utf8');

test('a second tap while a sign-in runs is refused, whichever button it is', () => {
  const gate = createSignInGate();
  expect(gate.tryStart('apple')).toBe(true);
  expect(gate.tryStart('apple')).toBe(false);
  expect(gate.tryStart('google')).toBe(false);
  expect(gate.current()).toBe('apple');
});

test('once the sign-in ends, however it ended, the next one can start', () => {
  const gate = createSignInGate();
  gate.tryStart('google');
  gate.finish();
  expect(gate.current()).toBeNull();
  expect(gate.tryStart('apple')).toBe(true);
});

// The login screen is a component this jest setup can't render, so its use
// of the gate is checked from source: the guard runs before any await, and
// the Apple button can't be pressed while busy.
test('the login screen checks the gate before starting a sign-in', () => {
  const screen = readSrc('./LoginScreen.tsx');
  const run = screen.slice(screen.indexOf('async function run('));
  const guard = run.indexOf('tryStart(kind)');
  const firstAwait = run.indexOf('await ');
  expect(guard).toBeGreaterThan(-1);
  expect(guard).toBeLessThan(firstAwait);
  expect(run.slice(0, run.indexOf('\n  }\n'))).toMatch(/finally \{[\s\S]*finish\(\)/);
});

test('the Apple button is covered while a sign-in runs', () => {
  const screen = readSrc('./LoginScreen.tsx');
  // The view around the Apple button stops taking touches according to
  // `busy`, however that expression happens to be written.
  const button = screen.search(/<AppleAuthentication\.AppleAuthenticationButton\b/);
  expect(button).toBeGreaterThan(-1);
  const wrapper = screen.slice(screen.lastIndexOf('<View', button), button);
  const pointerEvents = wrapper.match(/pointerEvents=\{([^}]*)\}/);
  expect(pointerEvents).not.toBeNull();
  expect(pointerEvents![1]).toMatch(/\bbusy\b/);
  expect(pointerEvents![1]).toMatch(/['"]none['"]/);
});
