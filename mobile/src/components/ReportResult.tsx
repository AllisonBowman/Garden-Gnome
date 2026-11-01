import React, { useMemo } from 'react';
import { StyleSheet } from 'react-native';
import { Button } from 'react-native-paper';
import { ReportSurface, buildReportMailto, openExternal } from '../support';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';

type Props = {
  /** What is being reported: which feature produced the result, or a fact
   *  a species page states. Goes into the email subject. */
  surfaceLabel: ReportSurface;
  /** The text being reported (excerpted into the email body). */
  result: string;
  /** Extra context lines, e.g. the plant's nickname or species. */
  context?: string[];
  /** Match the surrounding card's accent color. */
  textColor?: string;
};

/** The link's words: a fact on a species page is reported as a fact, and
 *  everything else as a result. */
export function reportLinkLabel(surface: ReportSurface): string {
  return surface === 'fact' ? 'Report a fact' : 'Report this result';
}

/**
 * "Report this result" — required alongside every care-engine output so a
 * wrong or inappropriate result can be flagged (App Review's AI-disclosure
 * expectation) — and "Report a fact" on a species page. Files the report as
 * a prefilled support email.
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
      {reportLinkLabel(surfaceLabel)}
    </Button>
  );
}

const makeStyles = (p: Palette, f: Fonts) =>
  StyleSheet.create({
    btn: { alignSelf: 'flex-start', marginTop: 2 },
    label: { fontSize: 12 },
  });
