import { Confidence, Explained, Source } from '../types/site';

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
export const WHY_LABEL = 'Why and data source';

/** What a value with no source says, rather than leaving the line blank. */
export const NO_SOURCE_LINE = 'No data source was given for this.';

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
  return [title, explained.display, `Confidence: ${explained.confidence_label}`]
    .filter(Boolean).join('. ');
}
