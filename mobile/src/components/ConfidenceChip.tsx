import React from 'react';
import { StyleProp, View, ViewStyle } from 'react-native';
import Pill from './Pill';
import { Confidence, ConfidenceLabel, CONFIDENCE_LABELS } from '../types/site';
import { confidenceTone } from './explainedText';
import { t } from '../i18n';

/**
 * How sure a value is, in the server's own words ("Area estimate", "You told
 * us"). The label comes from the server; the table in types/site.ts is the
 * fallback if it ever arrives empty.
 */
export default function ConfidenceChip({
  confidence, label, style,
}: {
  confidence: Confidence;
  label?: ConfidenceLabel | string | null;
  style?: StyleProp<ViewStyle>;
}) {
  const text = label?.trim() || CONFIDENCE_LABELS[confidence] || t('care.confidence.notKnown');
  const tone = confidenceTone(confidence);
  return (
    <View
      accessible
      accessibilityLabel={t('care.confidence.a11y', { text })}
      style={style}
    >
      <Pill tone={tone} filled={tone !== 'neutral'}>{text}</Pill>
    </View>
  );
}
