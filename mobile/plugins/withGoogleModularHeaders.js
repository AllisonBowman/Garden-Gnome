const { withDangerousMod } = require('@expo/config-plugins');
const fs = require('fs');
const path = require('path');

// GoogleSignIn 9.x pulls in AppCheckCore, a Swift pod that depends on
// GoogleUtilities and RecaptchaInterop — both Objective-C pods that do NOT
// define modules. CocoaPods refuses to integrate a Swift pod against
// non-modular dependencies as static libraries, which fails the EAS
// "Install pods" phase with:
//   The Swift pod `AppCheckCore` depends upon `GoogleUtilities` and
//   `RecaptchaInterop`, which do not define modules.
//
// We fix it the scoped way the error recommends: opt those two specific
// pods into modular headers. This is deliberately NOT `use_frameworks!`
// (expo-build-properties useFrameworks: 'static'), which would switch the
// whole workspace's integration mode and risks disturbing the custom
// PlantId static_framework pod. Here nothing else changes.
//
// Managed/CNG note: ios/ is generated on EAS, so we edit the Podfile via a
// dangerous mod during prebuild rather than committing a Podfile.

const POD_LINES = [
  "  pod 'GoogleUtilities', :modular_headers => true",
  "  pod 'RecaptchaInterop', :modular_headers => true",
];
const ANCHOR = 'use_expo_modules!';

module.exports = function withGoogleModularHeaders(config) {
  return withDangerousMod(config, [
    'ios',
    (cfg) => {
      const podfilePath = path.join(
        cfg.modRequest.platformProjectRoot, 'Podfile');
      let contents = fs.readFileSync(podfilePath, 'utf8');

      if (contents.includes("pod 'GoogleUtilities', :modular_headers => true")) {
        return cfg; // already applied (idempotent)
      }
      if (!contents.includes(ANCHOR)) {
        throw new Error(
          `[withGoogleModularHeaders] anchor "${ANCHOR}" not found in the ` +
          'generated Podfile; cannot place modular-header pod declarations.');
      }
      // Insert the two pod lines just after `use_expo_modules!` (inside the
      // app target block).
      contents = contents.replace(
        ANCHOR, `${ANCHOR}\n${POD_LINES.join('\n')}`);
      fs.writeFileSync(podfilePath, contents);
      return cfg;
    },
  ]);
};
