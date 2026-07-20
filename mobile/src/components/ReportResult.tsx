import React from 'react';
import { StyleSheet } from 'react-native';
import { Button } from 'react-native-paper';
import { buildReportMailto, openExternal } from '../support';

type Props = {
  /** Which feature produced the result — goes into the email subject. */
  surfaceLabel: 'identification' | 'diagnosis' | 'care advice';
  /** The result text being reported (excerpted into the email body). */
  result: string;
  /** Extra context lines, e.g. the plant's nickname or species. */
  context?: string[];
  /** Match the surrounding card's accent color. */
  textColor?: string;
};

/**
 * "Report this result" — required alongside every care-engine output so a
 * wrong or inappropriate result can be flagged (App Review's AI-disclosure
 * expectation). Files the report as a prefilled support email.
 */
export default function ReportResult({ surfaceLabel, result, context, textColor }: Props) {
  return (
    <Button
      compact
      mode="text"
      icon="flag-outline"
      textColor={textColor ?? '#52796F'}
      labelStyle={styles.label}
      style={styles.btn}
      onPress={() => openExternal(buildReportMailto(surfaceLabel, result, context))}
    >
      Report this result
    </Button>
  );
}

const styles = StyleSheet.create({
  btn: { alignSelf: 'flex-start', marginTop: 2 },
  label: { fontSize: 12 },
});
