import React, { useMemo } from 'react';
import { StyleSheet } from 'react-native';
import { Button } from 'react-native-paper';
import { buildReportMailto, openExternal } from '../support';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';

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
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  return (
    <Button
      compact
      mode="text"
      icon="flag-outline"
      textColor={textColor ?? palette.sub}
      labelStyle={styles.label}
      style={styles.btn}
      onPress={() => openExternal(buildReportMailto(surfaceLabel, result, context))}
    >
      Report this result
    </Button>
  );
}

const makeStyles = (p: Palette, f: Fonts) =>
  StyleSheet.create({
    btn: { alignSelf: 'flex-start', marginTop: 2 },
    label: { fontSize: 12 },
  });
