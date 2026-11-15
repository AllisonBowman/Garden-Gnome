import { PHOTO_ID_ENTRY_SHOWN } from './entry';

declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');
const readSrc = (rel: string): string => fs.readFileSync(path.join(__dirname, rel), 'utf8');

test('the photo suggestion entry is hidden in this release', () => {
  expect(PHOTO_ID_ENTRY_SHOWN).toBe(false);
});

test('Add plant draws the photo buttons only behind the switch', () => {
  const screen = readSrc('../screens/AddPlantScreen.tsx');
  const buttons = screen.indexOf('onPress={() => pickAndIdentify(true)}');
  expect(buttons).toBeGreaterThan(-1);
  const gate = screen.lastIndexOf('{PHOTO_ID_ENTRY_SHOWN && aiIdAvailable && catalogReady && (', buttons);
  expect(gate).toBeGreaterThan(-1);
  // Nothing between the gate and the buttons closes it first.
  expect(screen.slice(gate, buttons)).not.toMatch(/\)\}\s*\n/);
});

test('the phone is not asked whether it can suggest while the entry is hidden', () => {
  const screen = readSrc('../screens/AddPlantScreen.tsx');
  expect(screen).toMatch(/if \(PHOTO_ID_ENTRY_SHOWN\) photoIdAvailable\(\)/);
});

test('the native module and its code stay in the app', () => {
  expect(fs.existsSync(path.join(__dirname, 'identify.ts'))).toBe(true);
});
