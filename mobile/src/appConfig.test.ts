// What app.json promises Apple, pinned. These keys end up in Info.plist and
// PrivacyInfo.xcprivacy at build time, where nobody reads them until a
// reviewer does, so the test reads them here.
//
// app.json is read from source the way support.version.test.ts reads it.
declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');

const appJson = JSON.parse(fs.readFileSync(path.join(__dirname, '../app.json'), 'utf8'));
const expo = appJson.expo;

// --- iPhone only, for now -----------------------------------------------------

test('the iOS build is iPhone-only', () => {
  // No screen has a tablet layout, and supporting iPad means 13-inch iPad
  // screenshots and an iPad review. iPad can be added later; it can't be
  // taken away after release. iPads still run it in iPhone mode.
  expect(expo.ios.supportsTablet).toBe(false);
  expect(expo.ios.isTabletOnly).not.toBe(true);
  expect(expo.orientation).toBe('portrait');
});
