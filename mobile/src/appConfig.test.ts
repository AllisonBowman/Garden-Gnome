// What app.json promises Apple, pinned. These keys end up in Info.plist and
// PrivacyInfo.xcprivacy at build time, where nobody reads them until a
// reviewer does, so the test reads them here.
//
import { PHOTO_ID_ENTRY_SHOWN } from './photoId/entry';

// app.json is read from source the way support.version.test.ts reads it.
declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');

const appJson = JSON.parse(fs.readFileSync(path.join(__dirname, '../app.json'), 'utf8'));
const expo = appJson.expo;

/** The options object a config plugin was given, or undefined if bare. */
function pluginOptions(name: string): Record<string, unknown> | undefined {
  for (const entry of expo.plugins as unknown[]) {
    if (entry === name) return {};
    if (Array.isArray(entry) && entry[0] === name) return entry[1] ?? {};
  }
  return undefined;
}

// --- purpose strings ------------------------------------------------------------
// Each one is what iOS shows when it asks. It must say what this app does
// with the permission, in the app's words, and a permission the app never
// asks for must not ship a string at all (a config plugin given `false`
// deletes its key: @expo/config-plugins ios/Permissions.js).

const camera = pluginOptions('expo-camera')!;
const picker = pluginOptions('expo-image-picker')!;
const location = pluginOptions('expo-location')!;
const secureStore = pluginOptions('expo-secure-store')!;

const shown: Record<string, string> = {
  NSCameraUsageDescription: camera.cameraPermission as string,
  NSMicrophoneUsageDescription: camera.microphonePermission as string,
  NSPhotoLibraryUsageDescription: picker.photosPermission as string,
  NSLocationWhenInUseUsageDescription: location.locationWhenInUsePermission as string,
  NSSpeechRecognitionUsageDescription: expo.ios.infoPlist.NSSpeechRecognitionUsageDescription,
};

test('every permission the app asks for has its own written string', () => {
  for (const [key, text] of Object.entries(shown)) {
    expect([key, typeof text]).toEqual([key, 'string']);
    expect(text).toMatch(/PlantAdvocate/);
    // Not a plugin default ("Allow $(PRODUCT_NAME) to access your camera")
    expect(text).not.toMatch(/\$\(PRODUCT_NAME\)/);
    expect(text).not.toMatch(/^Allow /);
    // The app's vocabulary, not the codebase's old one
    expect(text).not.toMatch(/environment/i);
  }
});

test('each string names the feature that uses it', () => {
  expect(shown.NSCameraUsageDescription).toMatch(/photograph a plant/);
  expect(shown.NSCameraUsageDescription).toMatch(/check-up/);
  expect(shown.NSCameraUsageDescription).toMatch(/Walk the garden/);
  expect(shown.NSPhotoLibraryUsageDescription).toMatch(/photo of a plant/);
  expect(shown.NSPhotoLibraryUsageDescription).toMatch(/check-up/);
  // Both places the "Use my location" button appears: setting up your land,
  // and a growing area's place (components/AddressPicker.tsx).
  expect(shown.NSLocationWhenInUseUsageDescription).toMatch(/Use my location/);
  expect(shown.NSLocationWhenInUseUsageDescription).toMatch(/your land/);
  expect(shown.NSLocationWhenInUseUsageDescription).toMatch(/growing area/);
  expect(shown.NSLocationWhenInUseUsageDescription).toMatch(/forecast/);
  expect(shown.NSLocationWhenInUseUsageDescription).toMatch(/public maps/);
  expect(shown.NSMicrophoneUsageDescription).toMatch(/Walk the garden/);
  expect(shown.NSSpeechRecognitionUsageDescription).toMatch(/Walk the garden/);
  // Where the sound goes, since the policy promises it never reaches us.
  expect(shown.NSSpeechRecognitionUsageDescription).toMatch(/Apple/);
  expect(shown.NSMicrophoneUsageDescription).toMatch(/never receives/);
});

// --- Spanish purpose strings ------------------------------------------------------
// app.json "locales" points iOS at locales/es.json, which @expo/config-plugins
// writes to es.lproj/InfoPlist.strings. A phone in Spanish reads these instead.

const esPlist: Record<string, string> = JSON.parse(
  fs.readFileSync(path.join(__dirname, '../locales/es.json'), 'utf8'),
);

test('Spanish is wired up for iOS', () => {
  expect(expo.locales).toEqual({ es: './locales/es.json' });
  expect(expo.ios.infoPlist.CFBundleAllowMixedLocalizations).toBe(true);
  expect(pluginOptions('expo-localization')).toEqual({ supportedLocales: { ios: ['en', 'es'] } });
});

test('every permission string has a Spanish one', () => {
  const keys = [...Object.keys(shown), 'NSMotionUsageDescription'];
  for (const key of keys) {
    expect([key, typeof esPlist[key]]).toEqual([key, 'string']);
    expect(esPlist[key]).toMatch(/PlantAdvocate/);
    expect(esPlist[key]).not.toEqual(shown[key]);
  }
  // Only Info.plist purpose strings belong there.
  for (const key of Object.keys(esPlist)) expect(key).toMatch(/^NS\w+UsageDescription$/);
});

test('the Spanish strings survive the .strings writer', () => {
  // @expo/config-plugins ios/Locales.js writes `key = "value";` without
  // escaping, so a double quote or backslash would break the file.
  for (const text of Object.values(esPlist)) expect(text).not.toMatch(/["\\\n]/);
});

test('the Spanish strings name the features as the Spanish screens do', () => {
  expect(esPlist.NSCameraUsageDescription).toMatch(/Recorre el jardín/);
  expect(esPlist.NSCameraUsageDescription).toMatch(/revisiones con foto/);
  expect(esPlist.NSMicrophoneUsageDescription).toMatch(/Recorre el jardín/);
  expect(esPlist.NSSpeechRecognitionUsageDescription).toMatch(/Recorre el jardín/);
  expect(esPlist.NSSpeechRecognitionUsageDescription).toMatch(/Apple/);
  expect(esPlist.NSPhotoLibraryUsageDescription).toMatch(/revisiones con foto/);
  expect(esPlist.NSLocationWhenInUseUsageDescription).toMatch(/Usar mi ubicación/);
  expect(esPlist.NSLocationWhenInUseUsageDescription).toMatch(/área de cultivo/);
});

test('no string offers what this version does not', () => {
  // Photo identification is hidden from 1.2.0 (src/photoId/entry.ts). While
  // it is, no prompt may say the phone can suggest what a plant is. When the
  // entry is switched back on, the camera and photos strings change with it.
  expect(PHOTO_ID_ENTRY_SHOWN).toBe(false);
  for (const text of Object.values(shown)) {
    expect(text).not.toMatch(/suggest what it is/i);
    expect(text).not.toMatch(/identif/i);
  }
  // A photo check-up is only ever described as something offered later:
  // the server has it switched off (care/aiCapabilities.ts).
  expect(shown.NSCameraUsageDescription).toMatch(/When photo check-ups are offered/);
  expect(shown.NSPhotoLibraryUsageDescription).toMatch(/When photo check-ups are offered/);
});

test('the image picker repeats the camera and microphone strings exactly', () => {
  // Both plugins write NSCameraUsageDescription and NSMicrophoneUsageDescription;
  // which runs last depends on mod order, so they must not disagree. The
  // picker's microphone is left a string, not false: false would delete the
  // key Walk the garden needs.
  expect(picker.cameraPermission).toBe(camera.cameraPermission);
  expect(picker.microphonePermission).toBe(camera.microphonePermission);
});

test('permissions the app never asks for ship no string, except motion', () => {
  // Foreground location only (src/location/permissions.ts); no motion; the
  // keychain is never read behind Face ID.
  expect(location.locationAlwaysAndWhenInUsePermission).toBe(false);
  expect(location.locationAlwaysPermission).toBe(false);
  // Motion is the exception: the app never asks, but expo-location links
  // Core Motion, and App Store Connect rejects the upload without the key
  // (error 90683, 1.1.3 build 18). So it ships a string that says so.
  expect(location.motionUsagePermission).toMatch(/doesn't use motion/);
  expect(location.motionUsagePermission).toMatch(/never asks/);
  expect(location.isIosBackgroundLocationEnabled).not.toBe(true);
  expect(secureStore.faceIDPermission).toBe(false);
  const plist = expo.ios.infoPlist as Record<string, unknown>;
  for (const key of [
    'NSLocationAlwaysUsageDescription', 'NSLocationAlwaysAndWhenInUseUsageDescription',
    'NSFaceIDUsageDescription',
  ]) {
    expect(plist[key]).toBeUndefined();
  }
});

// --- the privacy manifest ---------------------------------------------------------
// ios.privacyManifests is merged into PrivacyInfo.xcprivacy at prebuild
// (@expo/config-plugins ios/PrivacyInfo.js), and React Native's pod install
// then adds the required-reason API entries from every pod without touching
// these. So only the collected data is declared here, and it must agree with
// the App Privacy answers in App Store Connect.

const manifest = expo.ios.privacyManifests;
const collected = new Map<string, Record<string, unknown>>(
  (manifest?.NSPrivacyCollectedDataTypes ?? []).map(
    (t: Record<string, unknown>) => [t.NSPrivacyCollectedDataType as string, t],
  ),
);
const type = (name: string) => `NSPrivacyCollectedDataType${name}`;

test('nothing is collected for tracking, and no tracking domains exist', () => {
  expect(manifest.NSPrivacyTracking).toBe(false);
  expect(manifest.NSPrivacyTrackingDomains ?? []).toEqual([]);
  for (const t of collected.values()) {
    expect(t.NSPrivacyCollectedDataTypeTracking).toBe(false);
  }
});

test('the data the app collects is declared, each linked to the account, as App Store Connect says', () => {
  // Must agree with docs/app-store/app-privacy.md, which cites the code for
  // each row. Analytics here means only the opt-in community census.
  const AF = 'NSPrivacyCollectedDataTypePurposeAppFunctionality';
  const AN = 'NSPrivacyCollectedDataTypePurposeAnalytics';
  const expected: Record<string, string[]> = {
    Name: [AF], EmailAddress: [AF], // Apple or Google sign-in, stored on the account
    UserID: [AF], // the account id and the Apple/Google subject
    PreciseLocation: [AF], // a growing area's coordinates, for its forecast
    CoarseLocation: [AF, AN], // its city/region/country, also counted by the census
    CustomerSupport: [AF], // "Report this result" and support mail reach our inbox
    OtherUserContent: [AF, AN], // plants, care logs, notes, areas; counted by the census
  };
  expect([...collected.keys()].sort()).toEqual(Object.keys(expected).map(type).sort());
  for (const [name, purposes] of Object.entries(expected)) {
    const t = collected.get(type(name))!;
    expect(t.NSPrivacyCollectedDataTypeLinked).toBe(true);
    expect(t.NSPrivacyCollectedDataTypePurposes).toEqual(purposes);
  }
});

test('photos are not declared while photo check-ups are not offered', () => {
  // Identifying a plant runs on the phone and uploads nothing. The photo
  // check-up is the one upload, and the plant screen shows it only when the
  // server reports vision ready (care/aiCapabilities.ts). Before that server
  // setting is ever switched on, add PhotosorVideos here and in App Store
  // Connect, and ship that build first (docs/app-store/app-privacy.md).
  expect(collected.has(type('PhotosorVideos'))).toBe(false);
});

test('audio is not declared, because it never reaches PlantAdvocate', () => {
  // Speech is transcribed by the phone, or by Apple where the phone can't;
  // only the plants the gardener confirms are sent.
  expect(collected.has(type('AudioData'))).toBe(false);
});

test('the manifest leaves the required-reason API entries to the build', () => {
  // Declaring them here by hand would go stale as dependencies change.
  expect(manifest.NSPrivacyAccessedAPITypes).toBeUndefined();
});

// --- iPhone only, for now -----------------------------------------------------

test('the iOS build is iPhone-only', () => {
  // No screen has a tablet layout, and supporting iPad means 13-inch iPad
  // screenshots and an iPad review. iPad can be added later; it can't be
  // taken away after release. iPads still run it in iPhone mode.
  expect(expo.ios.supportsTablet).toBe(false);
  expect(expo.ios.isTabletOnly).not.toBe(true);
  expect(expo.orientation).toBe('portrait');
});
