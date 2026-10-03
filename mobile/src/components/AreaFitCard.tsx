import React, { useMemo } from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Card, ActivityIndicator, Button } from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { fetchSpeciesFit } from '../api/growingAreas';
import {
  CHECK_FAILED, fitsOf, misfitsOf, notKnownLine, speciesFitNote,
} from '../growingAreas/fitFindings';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import FitFindingRow from './FitFindingRow';

/** How one species suits one growing area, in full: what is against it, what
 *  was confirmed and on whose word, and what nobody could judge. Where a
 *  list says it in a line ("Confirmed here: sun, soil and size"), this is
 *  the detail behind the line.
 *
 *  Every row is the server's finding as sent (FitFindingRow); this only
 *  sorts them. A request that failed is said to have failed, never shown as
 *  an empty answer — an empty answer would read as nothing against it. */
export default function AreaFitCard({
  areaId, areaName, speciesId,
}: { areaId: number; areaName: string; speciesId: number }) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const { data: fit, isLoading, isError, refetch } = useQuery({
    queryKey: ['speciesFit', areaId, speciesId],
    queryFn: () => fetchSpeciesFit(areaId, speciesId),
  });

  const against = fit ? misfitsOf(fit.findings) : [];
  const confirmed = fit ? fitsOf(fit.findings) : [];
  // Nothing judged either way gets the one sentence that says so, rather
  // than two empty sections and a list of unknowns.
  const nothingJudged = fit != null && against.length === 0 && confirmed.length === 0;
  const notKnown = fit && !nothingJudged ? notKnownLine(fit.findings) : null;

  return (
    <Card style={styles.card}>
      <Card.Title title={`In ${areaName}`} titleVariant="titleMedium" titleStyle={styles.cardTitle} />
      <Card.Content>
        {isLoading ? (
          <ActivityIndicator style={styles.loading} />
        ) : isError ? (
          <View>
            <Text style={styles.quiet}>{CHECK_FAILED}</Text>
            <Button compact onPress={() => refetch()} style={styles.retry}>Try again</Button>
          </View>
        ) : fit ? (
          <>
            {against.length > 0 ? (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Against it here</Text>
                {against.map((f, i) => <FitFindingRow key={`${f.axis}-${i}`} finding={f} />)}
              </View>
            ) : null}
            {confirmed.length > 0 ? (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Confirmed here</Text>
                {confirmed.map((f, i) => <FitFindingRow key={`${f.axis}-${i}`} finding={f} />)}
              </View>
            ) : null}
            {nothingJudged ? <Text style={styles.quiet}>{speciesFitNote(fit, areaName)}</Text> : null}
            {notKnown ? <Text style={styles.quiet}>{notKnown}</Text> : null}
          </>
        ) : null}
      </Card.Content>
    </Card>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  card: { marginBottom: 12, borderRadius: 12, backgroundColor: p.card },
  cardTitle: { color: p.ink, fontFamily: f.display },
  loading: { marginVertical: 16 },
  section: { marginBottom: 8 },
  sectionTitle: { fontSize: 14, fontWeight: '700', color: p.ink, marginBottom: 6 },
  quiet: { color: p.sub, fontSize: 13, lineHeight: 19 },
  retry: { alignSelf: 'flex-start', marginTop: 6 },
});
