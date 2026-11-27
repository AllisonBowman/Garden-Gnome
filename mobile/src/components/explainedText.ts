import { CONFIDENCE_LABELS, Confidence, Explained, Source } from '../types/site';
import { language, t } from '../i18n';

// The words and tones ExplainedBlock and ConfidenceChip use, kept pure so the
// rules (every value shows its reason and where it came from) can be tested
// without rendering.

export type ChipTone = 'good' | 'accent' | 'neutral';

/** What the owner said or measured reads as settled; a good estimate is
 *  marked; everything else is plain. None is a warning: a rough estimate is
 *  honest, not wrong. */
export function confidenceTone(confidence: Confidence): ChipTone {
  if (confidence === 'you_told_us' || confidence === 'you_measured') return 'good';
  if (confidence === 'good_estimate') return 'accent';
  return 'neutral';
}

/** "Soil survey, map unit 12B, 2025 release" */
export function sourceText(source: Source): string {
  return [source.name, source.detail, source.version]
    // A part that ends its own sentence would double the full stop a caller adds.
    .map((s) => (s ?? '').trim().replace(/[.\s]+$/, ''))
    .filter(Boolean)
    .join(', ');
}

/** The disclosure's label, the same everywhere so people learn it once. */
export const WHY_LABEL = t('land.whyLabel');

/** What a value with no source says, rather than leaving the line blank. */
export const NO_SOURCE_LINE = t('land.noSource');

/** The sentences the disclosure shows: the reason, then each source. */
export function disclosureLines(explained: Pick<Explained, 'reason' | 'sources'>): {
  reason: string; sources: string[];
} {
  const sources = explained.sources.map(sourceText).filter(Boolean);
  return {
    reason: explained.reason.trim(),
    sources: sources.length > 0 ? sources : [NO_SOURCE_LINE],
  };
}

/** One line for a screen reader: value, then how sure. */
export function explainedA11yLabel(
  title: string | undefined, explained: Pick<Explained, 'display' | 'confidence_label'>,
): string {
  return [title, explained.display, t('land.tiles.confidenceA11y', {
    label: localConfidenceLabel(explained.confidence_label, (explained as Partial<Explained>).confidence),
  })]
    .filter(Boolean).join('. ');
}

/**
 * A confidence label in the app's language. The server sends its labels in
 * English ("Good estimate"); in English they are shown as sent, and in
 * another language the label is looked up by its confidence (or, when only
 * the label came, by matching it to one), falling back to the server's words.
 */
export function localConfidenceLabel(label: string, confidence?: Confidence | null): string {
  if (language === 'en') return label;
  const key = confidence && confidence in CONFIDENCE_LABELS ? confidence
    : (Object.keys(CONFIDENCE_LABELS) as Confidence[]).find((c) => CONFIDENCE_LABELS[c] === label.trim());
  return key ? t(`land.confidence.${key}`) : label;
}

// ── The face of a value (what a screen shows; the rest is in How we know) ──

/** The small mark a value's face carries: "est." for an estimate,
 *  "Checking" while a slow service has not answered, nothing for what the
 *  owner said or measured. Keyed on the confidence, never on its words. */
export function faceMark(confidence: Confidence): 'est' | 'checking' | null {
  if (confidence === 'not_known_yet') return 'checking';
  if (confidence === 'you_told_us' || confidence === 'you_measured') return null;
  return 'est';
}

/** What the face says: the value, or "Checking" in place of the slow-service
 *  retry wording (that sentence moves to How we know). */
export function faceDisplay(explained: Pick<Explained, 'display' | 'confidence'>): string {
  return explained.confidence === 'not_known_yet' ? t('howWeKnow.checking') : explained.display;
}

/** One line for a screen reader: the value, and "estimated" or "still
 *  checking" when the face shows that mark. */
export function faceA11yLabel(
  title: string | undefined, explained: Pick<Explained, 'display' | 'confidence'>,
): string {
  const mark = faceMark(explained.confidence);
  return [
    title,
    faceDisplay(explained),
    mark === 'est' ? t('howWeKnow.estA11y') : mark === 'checking' ? null : null,
  ].filter(Boolean).join('. ');
}
