import {
  NO_SOURCE_LINE, WHY_LABEL, confidenceTone, disclosureLines, explainedA11yLabel, sourceText,
} from './explainedText';
import { CONFIDENCE_LABELS, Confidence } from '../types/site';

test('what the owner said reads as settled; no confidence is a warning', () => {
  expect(confidenceTone('you_told_us')).toBe('good');
  expect(confidenceTone('you_measured')).toBe('good');
  expect(confidenceTone('good_estimate')).toBe('accent');
  for (const c of ['area_estimate', 'rough_estimate', 'not_known_yet', 'neighbourhood_context'] as Confidence[]) {
    expect(confidenceTone(c)).toBe('neutral');
  }
});

test('a source line joins what is known and skips what is not', () => {
  expect(sourceText({ name: 'Soil survey', detail: 'map unit 12B', version: '2025' }))
    .toBe('Soil survey, map unit 12B, 2025');
  expect(sourceText({ name: 'Soil survey', detail: null, version: ' ' })).toBe('Soil survey');
});

test('the disclosure always has a reason and at least one source line', () => {
  expect(disclosureLines({ reason: ' Because. ', sources: [] }))
    .toEqual({ reason: 'Because.', sources: [NO_SOURCE_LINE] });
  expect(WHY_LABEL).toBe('Why and data source');
});

test('screen readers hear the value and how sure it is', () => {
  expect(explainedA11yLabel('Sun', { display: 'Part shade', confidence_label: CONFIDENCE_LABELS.area_estimate }))
    .toBe('Sun. Part shade. Confidence: Area estimate');
});
