import { Alert, Linking, Platform } from 'react-native';

// Single source of truth for the app's outward-facing contact points.
// The App Store listing uses the same URLs (privacy/support must resolve
// on plantadvocate.ai), so change them here and there together.
export const APP_VERSION = '1.0.0';
export const WEBSITE_URL = 'https://plantadvocate.ai';
export const SUPPORT_URL = 'https://plantadvocate.ai/support.html';
export const SUPPORT_EMAIL = 'support@plantadvocate.ai';

/** Open an external URL in the device's default browser/mail app. */
export async function openExternal(url: string): Promise<void> {
  try {
    await Linking.openURL(url);
  } catch {
    Alert.alert(
      'Could not open link',
      url.startsWith('mailto:')
        ? `No mail app is set up on this device. You can reach us at ${SUPPORT_EMAIL}.`
        : `Your device could not open ${url}.`,
    );
  }
}

/**
 * Build a mailto: URL that files a report about a care-engine result with
 * support. Reports go by email in v1 — no extra permissions, and the user
 * sees exactly what they are sending before they hit send.
 */
export function buildReportMailto(
  surfaceLabel: string,
  result: string,
  context: string[] = [],
): string {
  // Keep the whole mailto URL comfortably under client length limits
  const excerpt = result.length > 1000 ? `${result.slice(0, 1000)}…` : result;
  const body = [
    'Tell us what was wrong or inappropriate about this result:',
    '',
    '',
    '——— Reported result ———',
    ...context,
    excerpt,
    '———',
    `App: PlantAdvocate ${APP_VERSION} (${Platform.OS})`,
  ].join('\n');
  const subject = `Report a ${surfaceLabel} result`;
  return `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}
