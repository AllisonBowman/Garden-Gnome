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
  expect(shown.NSLocationWhenInUseUsageDescription).toMatch(/growing area/);
  expect(shown.NSLocationWhenInUseUsageDescription).toMatch(/forecast/);
  expect(shown.NSMicrophoneUsageDescription).toMatch(/Walk the garden/);
  expect(shown.NSSpeechRecognitionUsageDescription).toMatch(/Walk the garden/);
  // Where the sound goes, since the policy promises it never reaches us.
  expect(shown.NSSpeechRecognitionUsageDescription).toMatch(/Apple/);
  expect(shown.NSMicrophoneUsageDescription).toMatch(/never receives/);
});

test('the image picker repeats the camera and microphone strings exactly', () => {
  // Both plugins write NSCameraUsageDescription and NSMicrophoneUsageDescription;
  // which runs last depends on mod order, so they must not disagree. The
  // picker's microphone is left a string, not false: false would delete the
  // key Walk the garden needs.
  expect(picker.cameraPermission).toBe(camera.cameraPermission);
  expect(picker.microphonePermission).toBe(camera.microphonePermission);
});

test('permissions the app never asks for ship no string', () => {
  // Foreground location only (src/location/permissions.ts); no motion; the
  // keychain is never read behind Face ID.
  expect(location.locationAlwaysAndWhenInUsePermission).toBe(false);
  expect(location.locationAlwaysPermission).toBe(false);
  expect(location.motionUsagePermission).toBe(false);
  expect(location.isIosBackgroundLocationEnabled).not.toBe(true);
  expect(secureStore.faceIDPermission).toBe(false);
  const plist = expo.ios.infoPlist as Record<string, unknown>;
  for (const key of [
    'NSLocationAlwaysUsageDescription', 'NSLocationAlwaysAndWhenInUseUsageDescription',
    'NSMotionUsageDescription', 'NSFaceIDUsageDescription',
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

test('the data the app collects is declared, each linked to the account, for the app itself', () => {
  const expected = [
    'Name', 'EmailAddress', // Apple or Google sign-in, stored on the account
    'UserID', // the account id and the Apple/Google subject
    'PreciseLocation', 'CoarseLocation', // a growing area's place and its city/region
    'PhotosorVideos', // a photo check-up's photo, when check-ups are offered
    'OtherUserContent', // plants, care logs, notes, growing areas
  ].map(type);
  expect([...collected.keys()].sort()).toEqual([...expected].sort());
  for (const t of collected.values()) {
    expect(t.NSPrivacyCollectedDataTypeLinked).toBe(true);
    expect(t.NSPrivacyCollectedDataTypePurposes).toEqual([
      'NSPrivacyCollectedDataTypePurposeAppFunctionality',
    ]);
  }
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
