import { Alert, Linking, Platform } from 'react-native';
import { t } from './i18n';

// Single source of truth for the app's outward-facing contact points.
// The App Store listing uses the same URLs (privacy/support must resolve
// on plantadvocate.ai), so change them here and there together.
// Must match expo.version in app.json — it labels every support email, so a
// stale value here misattributes tester reports to the wrong build.
export const APP_VERSION = '1.2.0';
export const WEBSITE_URL = 'https://plantadvocate.ai';
export const SUPPORT_URL = 'https://plantadvocate.ai/support.html';
export const SUPPORT_EMAIL = 'support@plantadvocate.ai';
// App Review requires a reachable privacy policy, and the in-app consent card
// links to it as the binding version of the plain-language summary.
export const PRIVACY_URL = 'https://plantadvocate.ai/privacy.html';

/** Open an external URL in the device's default browser/mail app. */
export async function openExternal(url: string): Promise<void> {
  try {
    await Linking.openURL(url);
  } catch {
    Alert.alert(
      t('common.link.title'),
      url.startsWith('mailto:')
        ? t('common.link.noMail', { email: SUPPORT_EMAIL })
        : t('common.link.cannotOpen', { url }),
    );
  }
}

/** What a report is about. The care engine's three outputs are reported as
 *  results; a fact is something a species page states. */
export type ReportSurface = 'identification' | 'diagnosis' | 'care advice' | 'fact';

/**
 * Build a mailto: URL that files a report with support: a care-engine result
 * that was wrong or inappropriate, or a fact on a species page that looks
 * wrong. Reports go by email in v1 — no extra permissions, and the user
 * sees exactly what they are sending before they hit send.
 */
export function buildReportMailto(
  surfaceLabel: ReportSurface,
  result: string,
  context: string[] = [],
): string {
  // Keep the whole mailto URL comfortably under client length limits
  const excerpt = result.length > 1000 ? `${result.slice(0, 1000)}…` : result;
  // A fact report asks which fact and why, under what the page said; a
  // result report asks what was wrong with the result.
  const fact = surfaceLabel === 'fact';
  const body = [
    fact
      ? t('common.report.factPrompt')
      : t('common.report.resultPrompt'),
    '',
    '',
    fact ? '——— What the page says ———' : '——— Reported result ———',
    ...context,
    excerpt,
    '———',
    `App: PlantAdvocate ${APP_VERSION} (${Platform.OS})`,
  ].join('\n');
  const subject = fact
    ? t('common.report.factSubject')
    : t('common.report.resultSubject', { surface: surfaceLabel });
  return `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}
