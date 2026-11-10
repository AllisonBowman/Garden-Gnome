import React, { useMemo } from 'react';
import { View, StyleSheet } from 'react-native';
import { Text } from 'react-native-paper';
import type { FitFinding } from '../api/growingAreas';
import { findingHeading } from '../growingAreas/fitFindings';
import { INFERRED_PILL } from '../care/facts';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette } from '../theme/tokens';
import Eyebrow from './Eyebrow';
import Pill from './Pill';

/** One fit finding: what it is about and whose word it is, then the
 *  server's sentence exactly as sent. A value borrowed from the genus wears
 *  the same pill the care facts use for it (ADR 0002). */
export default function FitFindingRow({ finding }: { finding: FitFinding }) {
  const { palette } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette), [palette]);
  return (
    <View style={styles.row}>
      <View style={styles.head}>
        <Eyebrow style={styles.heading}>{findingHeading(finding)}</Eyebrow>
        {finding.borrowed ? <Pill style={styles.pill}>{INFERRED_PILL}</Pill> : null}
      </View>
      <Text style={styles.sentence}>{finding.sentence}</Text>
    </View>
  );
}

const makeStyles = (p: Palette) => StyleSheet.create({
  row: { marginBottom: 8 },
  head: { flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 2 },
  heading: { flexShrink: 1 },
  pill: { paddingVertical: 1 },
  sentence: { fontSize: 14, lineHeight: 20, color: p.sub },
});
