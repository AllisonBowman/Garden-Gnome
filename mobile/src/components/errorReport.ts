// The "Report this problem" email an error card opens.
//
// Reports go by email, like every other report in v1 (support.ts): no extra
// permissions, and the person sees exactly what they are sending before they
// send it. The technical detail goes in the email body, where support can
// read it, and never on the card itself, where a caretaker would have to.
//
// Pure on purpose (no React Native imports) so jest can pin it; the card
// passes in the support address, the version and the platform.

export interface ProblemReport {
  supportEmail: string;
  appVersion: string;
  platform: string;
  /** Which part of the app failed, in words: "Plants", "Species detail". */
  where: string;
  error: unknown;
}

/** One short line describing what was thrown, for the email body. */
export function describeError(error: unknown): string {
  let text: string;
  if (error instanceof Error) {
    text = error.message ? `${error.name}: ${error.message}` : error.name;
  } else if (typeof error === 'string') {
    text = error;
  } else {
    try {
      text = JSON.stringify(error) ?? String(error);
    } catch {
      text = String(error);
    }
  }
  const oneLine = text.replace(/\s+/g, ' ').trim() || 'Unknown error';
  return oneLine.length > 300 ? `${oneLine.slice(0, 300)}…` : oneLine;
}

export function buildProblemMailto(report: ProblemReport): string {
  const subject = 'Report a problem in PlantAdvocate';
  const body = [
    'Tell us what you were doing when this happened:',
    '',
    '',
    '——— What the app saw ———',
    `Where: ${report.where}`,
    describeError(report.error),
    '———',
    `App: PlantAdvocate ${report.appVersion} (${report.platform})`,
  ].join('\n');
  return `mailto:${report.supportEmail}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}
