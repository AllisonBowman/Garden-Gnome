# The iOS 27 launch crash and 1.1.3

Written 2026-10-24 on the Mac, about the ship tip `3f6d7da` (PR #22). Every
source below was read today. No code was changed.

## Verdict for 1.1.3

1.1.3 is not affected, as long as it is built the way the handoff says: on
EAS, with the image `eas.json` already pins. That image builds with Xcode 26.6
and the iOS 26.5 SDK. Apple's rule switches on only for apps linked against
the iOS 27 SDK. I checked this directly. An earlier PlantAdvocate build made
with that same Xcode 26.6, against the iOS 26.5 SDK and with no scene manifest,
launched and drew its screen on an iOS 27.0 simulator today. The crash from
the screenshot shoot happened because that build was made locally with Xcode
27.1, the only Xcode on this Mac. That local build will never go to Apple.

So the crash doesn't block 1.1.3, and nothing in the handoff changes. Don't
change the image in `eas.json` for this release, and don't upload a 1.1.3
built locally on this Mac.

Two small checks are still worth doing in the handoff's existing steps. When
the EAS build finishes, its page on expo.dev names the image it ran on. It
should read `macos-tahoe-26.5-xcode-26.6`. In step 5, the handoff already asks
you to write down the phone's iOS version. If the phone runs iOS 27, the
TestFlight build launching at all is the hardware confirmation. If it runs iOS
26, the simulator run below is the only iOS 27 evidence, and it's good
evidence but not a device.

1.1.4 is different. Apple has said that uploads must be built with the iOS 27
SDK starting April 2027, and an Expo SDK 57 app built that way crashes exactly
like the shoot build unless it adopts the scene life cycle first. That work is
at the end of this file.

## What the shoot actually hit

On 2026-10-23 the shoot ran `npx expo prebuild --platform ios --clean` and
built a Release simulator app with `xcodebuild` in a scratch worktree at
`3f6d7da`. The build log at `/tmp/claude-501/pa-shoot-data/build.log` shows
`SDKROOT = iphonesimulator27.1`, and the built app's Info.plist agrees:
`DTSDKName` is `iphonesimulator27.1` and `DTXcodeBuild` is `27A9275`, which is
Xcode 27.1. The Info.plist has no `UIApplicationSceneManifest` key. The
generated `AppDelegate.swift` is the stock Expo SDK 57 template. It creates
the `UIWindow` itself in `didFinishLaunchingWithOptions` and has no scene
delegate.

The shoot installed that app on two simulators running the iOS 27.0 runtime
(24A434), and both crashed at launch. The crash reports are now in
`~/Library/Logs/DiagnosticReports/Retired/` as
`PlantAdvocate-2026-10-23-115707.ips` and `PlantAdvocate-2026-10-23-115756.ips`.
Both say the same thing. The exception is `EXC_BREAKPOINT` (`SIGTRAP`,
"Trace/BPT trap: 5"). The top frame of the crashing thread is
`___UIApplicationEvaluateRuntimeIssueForNoSceneLifecycleAdoption_block_invoke`
in UIKitCore. Below it, UIKit is creating the app's first scene
(`-[UIApplication workspace:didCreateScene:withTransitionContext:completion:]`)
under `UIApplicationMain`. That is a deliberate UIKit assertion firing at the
first scene connection. It isn't a fault in PlantAdvocate's code, and nothing
in JavaScript had run yet. The report has no extra message text (its
application-specific information field is empty), so the symbol name is the
diagnosis. It names the missing adoption, and it matches the assert Apple
warned about (below). The same app ran normally on the iOS 26.5 simulators
used for the screenshots.

## Apple's rule is keyed to the SDK the app links against

TN3187, "Migrating to the UIKit scene-based life cycle", is Apple's migration
guide. It was first published 2025-05-05, and the requirement was added on
2025-06-23. It says that in the next major release after iOS 26, the scene
life cycle will be "required when building with the latest SDK; otherwise,
your app won't launch." It also says only adopting the scene life cycle is
required, not supporting multiple scenes. Apps that don't adopt it get warning
logs on iOS 18.4 and later. TN3187 gives the iOS 26 wording, which says that
not adopting will lead to an assert in the future.

The iOS & iPadOS 27 release notes make it final. Under UIKit, in Deprecations
(item 141837548), they say apps built with the latest SDK must adopt the
scene-based life cycle, and that apps that don't fail to launch. The iOS 26
release notes have no scene life cycle entry. Their only related UIKit
deprecation is `UIScreen.mainScreen`.

The WWDC sessions say the same. In WWDC25 session 282, "Make your UIKit app
more flexible", Apple says the scene life cycle will be required in the next
major release after iOS 26 when building with the latest SDK. In WWDC26
session 278, "Modernize your UIKit app", Apple says the scene life cycle is
now required when building with the latest SDKs, and that apps without it
won't launch.

All three sources key the rule to the SDK the app is built with, not to the
iOS version it runs on. An app linked against the iOS 26.5 SDK runs on iOS 27
with the old behaviour.

## What EAS builds 1.1.3 with

`mobile/eas.json` pins `"image": "macos-tahoe-26.5-xcode-26.6"` for the
development, preview and production profiles. Expo's build infrastructure page
(docs.expo.dev/build-reference/infrastructure) lists that image as macOS Tahoe
26.5.2 with Xcode 26.6 (17F113), and gives it the `sdk-57` alias. Apple's
Xcode 26.6 release notes say Xcode 26.6 includes the SDKs for iOS 26.5 and
iPadOS 26.5. So the production build links against the iOS 26.5 SDK, and the
iOS 27 check doesn't apply to it.

The pin matters. On the same page Expo's `latest` image is
`macos-tahoe-26.6-xcode-27.1` (also `sdk-58`), and there is a
`macos-tahoe-26.6-xcode-27.0`. A 1.1.3 built on either would link against the
iOS 27 SDK and crash on iOS 27 like the shoot build did. The handoff's
`eas-cli@latest` only updates the command-line tool. It doesn't change the
image, because the image comes from `eas.json`.

## The direct test

This Mac had one PlantAdvocate build made with the same Xcode as the EAS
image. It's a development-client build of 1.0.0 from July 25, installed on an
iOS 26.5 simulator. Its Info.plist says `DTSDKName` `iphonesimulator26.5`,
`DTXcodeBuild` `17F113` (Xcode 26.6) and no `UIApplicationSceneManifest`, the
same lack of adoption as 1.1.3.

Today I made a temporary iPhone 17 Pro simulator on the iOS 27.0 runtime
(24A434) and installed that build. It launched and kept running, and its
process was still alive after twelve seconds. It drew the Expo development
client's home screen with its tab bar, which can only happen after UIKit has
connected the first scene and passed the check that killed the shoot build.
No new crash report appeared. I then deleted the temporary simulator. The
screenshot is in this session's scratchpad as
`/private/tmp/claude-501/-Users-allisonbowman-Developer-Garden-Gnome--claude-worktrees-go-to-market-strategy-cd07f3/b737605c-ac93-493c-b5dd-2f1c39e6d0ab/scratchpad/ios27-july-build.png`.

The July build is older app code on an older Expo SDK, so it doesn't prove
anything about 1.1.3's own screens. It does settle the question here: the
check didn't fire for a build linked against the iOS 26.5 SDK by Xcode 26.6.
It fired for a build linked against the iOS 27.1 SDK. That matches what Apple
wrote.

## One consequence for this Mac now

Xcode 27.1 is the only Xcode installed, so any local build of 1.1.3 links
against the iOS 27.1 SDK and crashes on iOS 27 simulators. That includes the
four screenshot frames being retaken. Take them on the iOS 26.5 simulators, as
the shoot did. App Store screenshots don't depend on the simulator's iOS
version, only on the device size.

## What Expo SDK 57 and React Native 0.86 offer

The project is on `expo` 57.0.7 (package-lock) and `react-native` 0.86.0.
Neither one adopts the scene life cycle by default. The React Native 0.86
release post doesn't mention scenes. React Native added SceneDelegate support
in 0.88 (released 2026-10-19), with two new `RCTReactNativeFactory` entry
points, and it supports a single scene only.

Expo gives SDK 57 a way in without upgrading. The SDK 57 changelog (section
"Building with Xcode 27 and the iOS 27 SDK") says `expo@57.0.23` adds opt-in
scene support, switched on with the `ios.enableSceneSupport` property of
`expo-build-properties`. Expo's guide at expo.fyi/ios-scene-lifecycle (section
"Staying on SDK 57 with Xcode 27") says the setting makes prebuild do three
things. It makes `AppDelegate` conform to `ExpoReactNativeFactoryProvider`. It
removes React Native's startup code from `didFinishLaunchingWithOptions`. It
adds a scene manifest pointing at Expo's built-in `EXExpoAppSceneDelegate`. The
guide also says the plugin throws on SDK 57 patches older than 57.0.23, and
that it only edits the standard SDK 57 `AppDelegate` template. The published
`expo-build-properties` 57.0.22 (npm tag `sdk-57`) has `enableSceneSupport` in
its type definitions. The newest SDK 57 `expo` on npm today is 57.0.31 (tag
`sdk-57`, published 2026-10-21).

Expo SDK 58 (released 2026-10-15, with React Native 0.88) adopts the scene
life cycle by default. Prebuild generates `SceneDelegate.swift` and a scene
manifest. Expo forwards URL, user activity, life cycle and quick action events
to `ExpoAppDelegate` overrides and `ExpoAppDelegateSubscriber` implementations.

PlantAdvocate fits the simple path. It uses Continuous Native Generation (no
committed `ios/`). The shoot's prebuild produced the unmodified SDK 57
`AppDelegate.swift`, so no config plugin in `app.json` edits the app delegate.
The only local plugin, `mobile/plugins/withGoogleModularHeaders.js`, edits the
Podfile. The two local modules, `modules/plant-id` and `modules/plant-speech`,
don't touch `UIScreen`, `keyWindow` or the app delegate. Google Sign-In
(`@react-native-google-signin/google-signin` 16.1.2) gets its return URL
through an `ExpoAppDelegateSubscriber` (`GoogleSignInAppDelegate`), which is
the kind of hook Expo says keeps working under scenes. That still needs a test
on a device, because a URL handler that silently stops firing would break
Google sign-in.

## When Apple requires the iOS 27 SDK

This has been announced, but only as a month. Apple's news post "App Store
submissions now open for the latest OS releases" (September 9, 2026) says that
starting April 2027, iOS and iPadOS apps uploaded to App Store Connect must be
built with the iOS 27 and iPadOS 27 SDK or later, and must target iOS 15 or
later. Apple's Submitting page says the same. The Upcoming Requirements page
doesn't list it yet. Its newest SDK entry is the iOS 26 one, in force since
April 28, 2026.

The exact day isn't announced. In recent years Apple has given the month in
September and the day later, usually in February, and the day has always
fallen at the end of April. That is a pattern, not an announcement:

| Requirement | Exact date | Where Apple gave the date |
| --- | --- | --- |
| Xcode 14.1, iOS 16.1 SDK | April 25, 2023 | Upcoming Requirements page |
| Xcode 15, iOS 17 SDK | April 29, 2024 | Upcoming Requirements page |
| Xcode 16, iOS 18 SDK | April 24, 2025 | News post, February 21, 2025 |
| Xcode 26, iOS 26 SDK | April 28, 2026 | News post, February 3, 2026 (the September 9, 2025 post said "April 2026") |
| iOS 27 SDK | April 2027, day not yet given | News post, September 9, 2026 |

The rule applies to every upload, not just new versions. After the April 2027
date, even a one-line 1.1.x fix has to be built with Xcode 27, so the scene
work has to be in place before then.

## What 1.1.4 must do, and by when

1.1.4 must adopt the scene life cycle in the same build that moves to an Xcode
27 image. Doing either one alone isn't enough. Without adoption, the move to
Xcode 27 gives the shoot's crash for every iOS 27 user. If 1.1.4 stays on
Xcode 26.6, it postpones the problem to the April deadline.

The smallest change that does it is to stay on SDK 57 and opt in. Bring `expo`
up to the newest SDK 57 patch, which must be at least 57.0.23, and align the
other Expo packages. Add `expo-build-properties` at its SDK 57 version, and
add it to the `plugins` list in `mobile/app.json` with `ios.enableSceneSupport`
set to `true`, as in Expo's guide. Then change the image in all three
`eas.json` profiles to an Xcode 27 image. Evidence that SDK 57 compiles under
Xcode 27.1 already exists, because the shoot's Release build succeeded with
it. Expo lists `macos-tahoe-26.6-xcode-27.1`. The package steps, from the repo
root, are these:

```bash
cd mobile && npx expo install expo@sdk-57
```

```bash
cd mobile && npx expo install --fix
```

```bash
cd mobile && npx expo install expo-build-properties
```

Before building, run `npx expo prebuild --platform ios --clean` in a scratch
copy. Check that the generated Info.plist has a `UIApplicationSceneManifest`
naming `EXExpoAppSceneDelegate`, and that `AppDelegate.swift` no longer
creates the window. Then make a local Release build with this Mac's Xcode
27.1, and launch it on the iOS 27.0 simulator, the same test the shoot failed.

The bigger alternative is to upgrade to Expo SDK 58 and React Native 0.88,
which adopt scenes by default. That brings more change than this needs:
React Native 0.87's Strict TypeScript API is the default, event dispatching
moves to the Web-based path, and every module is bumped. It's worth doing on
its own schedule, not as the vehicle for this fix.

Linking against the iOS 27 SDK also brings behaviour that 1.1.4 has to test
on top of the launch. Expo's SDK 58 notes and Apple's iOS 27 release notes
say iPhone apps built with the iOS 27 SDK become resizable, and orientation
locks may stop applying while they are. PlantAdvocate is portrait-only and
iPhone-only, so 1.1.4's TestFlight pass should include these:

1. A cold launch on iOS 27.
2. Sign in with Apple, and Sign in with Google returning to the app.
3. Tapping a care reminder notification.
4. Camera, photo picker, location and Walk the garden.
5. The main screens at a resized window width.
6. The same checks on an iOS 26 phone, to catch regressions.

Timing: plan to have a scene-adopted 1.1.4 approved by the end of March 2027.
That leaves about four weeks before the earliest end-of-April date the pattern
suggests, in case review or the device pass turns something up. Watch Apple's
news page in February 2027 for the exact day. If you'd rather not depend on
the pattern, do it as the first update after 1.1.3 is live. The reasons to
move sooner are that iOS 27 tooling is already the default on this Mac and on
Expo's `latest` image, and that every local build until then needs the iOS
26.5 simulator.

## Sources read on 2026-10-24

Apple, TN3187 "Migrating to the UIKit scene-based life cycle":
https://developer.apple.com/documentation/technotes/tn3187-migrating-to-the-uikit-scene-based-life-cycle

Apple, iOS & iPadOS 27 Release Notes (UIKit, Deprecations, 141837548):
https://developer.apple.com/documentation/ios-ipados-release-notes/ios-ipados-27-release-notes

Apple, iOS & iPadOS 26 Release Notes:
https://developer.apple.com/documentation/ios-ipados-release-notes/ios-ipados-26-release-notes

Apple, WWDC25 session 282 "Make your UIKit app more flexible":
https://developer.apple.com/videos/play/wwdc2025/282/

Apple, WWDC26 session 278 "Modernize your UIKit app":
https://developer.apple.com/videos/play/wwdc2026/278/

Apple, Xcode 26.6 Release Notes:
https://developer.apple.com/documentation/xcode-release-notes/xcode-26_6-release-notes

Apple, Upcoming Requirements: https://developer.apple.com/news/upcoming-requirements/

Apple, Latest News (September 9, 2026 and February 3, 2026 posts):
https://developer.apple.com/news/ and https://developer.apple.com/news/?id=ueeok6yw

Apple, February 21, 2025 news post (Xcode 16 date):
https://developer.apple.com/news/?id=9s0rgdy9

Apple, Submitting: https://developer.apple.com/app-store/submitting/

Expo, build infrastructure (iOS server images):
https://docs.expo.dev/build-reference/infrastructure/

Expo, SDK 57 changelog: https://expo.dev/changelog/sdk-57

Expo, SDK 58 changelog: https://expo.dev/changelog/sdk-58

Expo, iOS scene-based life cycle guide: https://expo.fyi/ios-scene-lifecycle
(source: https://github.com/expo/fyi/blob/main/ios-scene-lifecycle.md)

React Native 0.88 release post:
https://reactnative.dev/blog/2026/10/19/react-native-0.88

React Native 0.86 release post:
https://reactnative.dev/blog/2026/06/11/react-native-0.86

npm registry, `expo` and `expo-build-properties` dist-tags:
https://registry.npmjs.org/expo and https://registry.npmjs.org/expo-build-properties

Local evidence: `/tmp/claude-501/pa-shoot-data/build.log`, the built app at
`/tmp/claude-501/pa-shoot-build/Build/Products/Release-iphonesimulator/PlantAdvocate.app`,
the generated `/tmp/claude-501/pa-shoot/mobile/ios/PlantAdvocate/AppDelegate.swift`,
the two crash reports in `~/Library/Logs/DiagnosticReports/Retired/`, and the
shoot agent's transcript under
`~/.claude/projects/-Users-allisonbowman-Developer-Garden-Gnome--claude-worktrees-go-to-market-strategy-56bf52/10cadeea-b00f-4922-86b6-f93a9fde4389/subagents/workflows/wf_a51350b9-aea/`.
