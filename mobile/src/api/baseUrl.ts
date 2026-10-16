// Which server the app talks to.
//
// Hosted backend (Fly.io). iOS release builds block plain http to non-localhost
// hosts (ATS), so the default must be https. Development and preview builds
// can point somewhere else from Settings (e.g. http://192.168.1.119:8000);
// that card only exists where EXPO_PUBLIC_SHOW_BACKEND_OVERRIDE is set or in
// dev (see SettingsScreen), never in an App Store build.
//
// Pure on purpose (no React Native imports) so jest can pin the rule.

export const DEFAULT_BASE_URL = 'https://garden-gnome-api.fly.dev';

/**
 * The URL to use, given what is stored and whether this build offers the
 * override at all.
 *
 * A stored override is honoured only in a build that can also show and clear
 * it. Keychain items survive deleting the app on iOS, so a tester who once
 * saved a LAN address in a preview build would otherwise install the App Store
 * build and find it pointed at a machine on their old Wi-Fi, with no screen
 * anywhere to put it back.
 */
export function resolveBaseUrl(stored: string | null | undefined, overrideAllowed: boolean): string {
  if (!overrideAllowed) return DEFAULT_BASE_URL;
  const trimmed = (stored ?? '').trim();
  return trimmed ? trimmed : DEFAULT_BASE_URL;
}
