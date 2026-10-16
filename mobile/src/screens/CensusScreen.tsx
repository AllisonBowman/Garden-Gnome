import React, { useMemo } from 'react';
import { ScrollView, View, StyleSheet } from 'react-native';
import { Text, Card, ActivityIndicator, ProgressBar } from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { fetchCensusSummary } from '../api/census';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import Eyebrow from '../components/Eyebrow';
import LoadError from '../components/LoadError';
import { areaTypeLabel } from '../growingAreas/realEstate';
import type { CensusStackParamList } from '../../App';

type Nav = NativeStackNavigationProp<CensusStackParamList, 'CensusSummary'>;


export default function CensusScreen() {
  const navigation = useNavigation<Nav>();
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);

  // The summary arrives already shaped (api/census.ts): a field the server
  // left out or renamed is null there, never undefined here.
  const { data: summary, isLoading, isError, isFetching, refetch } = useQuery({
    queryKey: ['census'],
    queryFn: fetchCensusSummary,
  });

  if (isLoading) return <ActivityIndicator style={styles.center} size="large" />;

  if (isError || !summary) {
    return (
      <LoadError
        message="Couldn't load the census. Check your connection and try again."
        onRetry={() => refetch()}
        retrying={isFetching}
      />
    );
  }

  const areaTypes = summary.growing_areas_by_type
    ? Object.entries(summary.growing_areas_by_type).filter(([, n]) => n > 0)
    : null;
  const topSpecies = summary.species_distribution
    ? summary.species_distribution.slice(0, 8)
    : null;
  const maxCount = Math.max(...(topSpecies ?? []).map((s) => s.count), 1);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* The almanac: the catalog as something to read, not just count */}
      <Card style={styles.almanacCard} mode="elevated" onPress={() => navigation.navigate('Almanac')}>
        <Card.Content>
          <Eyebrow>Species Almanac</Eyebrow>
          <Text variant="titleMedium" style={styles.almanacTitle}>
            Read the catalog ›
          </Text>
          <Text variant="bodySmall" style={styles.almanacSub}>
            Every species we hold, with its care fingerprint and how demanding
            it is to keep — and which of them suit each of your growing areas.
          </Text>
        </Card.Content>
      </Card>

      {/* Totals */}
      <View style={styles.totalsRow}>
        <TotalCard styles={styles} label="Plants" value={summary.total_plants} color={palette.acc} />
        <TotalCard styles={styles} label="Growing areas" value={summary.total_growing_areas} color={palette.sub} />
      </View>

      {/* Growing areas by type. Left out when the server didn't report it,
          rather than shown as a card that claims there are none. */}
      {areaTypes && (
        <Card style={styles.card}>
          <Card.Title title="Growing areas by type" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
          <Card.Content>
            {areaTypes.length === 0 ? (
              <Text variant="bodySmall" style={styles.emptyNote}>
                No growing areas yet. Add one from the Growing areas tab.
              </Text>
            ) : areaTypes.map(([type, count]) => (
              <View key={type} style={styles.envRow}>
                <Text variant="bodySmall" style={styles.envLabel}>
                  {areaTypeLabel(type)}
                </Text>
                <Text variant="bodySmall" style={styles.envCount}>{count}</Text>
              </View>
            ))}
          </Card.Content>
        </Card>
      )}

      {/* Species distribution */}
      {topSpecies && (
        <Card style={styles.card}>
          <Card.Title title="Top species" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
          <Card.Content>
            {topSpecies.length === 0 ? (
              <Text variant="bodySmall" style={styles.emptyNote}>
                No plants yet. Once you add some, the ones you grow most show up here.
              </Text>
            ) : topSpecies.map((s) => (
              <View key={s.species_id} style={styles.speciesRow}>
                <Text variant="bodySmall" style={styles.speciesName} numberOfLines={1}>
                  {s.common_name}
                </Text>
                <ProgressBar
                  progress={s.count / maxCount}
                  color={palette.acc}
                  style={styles.bar}
                />
                <Text variant="bodySmall" style={styles.speciesCount}>{s.count}</Text>
              </View>
            ))}
          </Card.Content>
        </Card>
      )}
    </ScrollView>
  );
}

type Styles = ReturnType<typeof makeStyles>;

/** A total, or a dash when the server didn't report it: never a made-up 0. */
function TotalCard({ styles, label, value, color }: { styles: Styles; label: string; value: number | null; color: string }) {
  return (
    <View style={[styles.totalCard, { borderColor: color }]}>
      <Text variant="displaySmall" style={[styles.totalValue, { color }]}>{value ?? '–'}</Text>
      <Eyebrow style={styles.totalLabel}>{label}</Eyebrow>
    </View>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  almanacCard: { marginBottom: 14, borderRadius: 12, backgroundColor: p.card },
  almanacTitle: { color: p.acc, fontFamily: f.display, marginTop: 4 },
  almanacSub: { color: p.sub, marginTop: 4, lineHeight: 18 },
  container: { flex: 1, backgroundColor: p.bg },
  content: { padding: 12, paddingBottom: 48 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  totalsRow: { flexDirection: 'row', gap: 12, marginBottom: 12 },
  totalCard: {
    flex: 1, alignItems: 'center', padding: 16, borderRadius: 12,
    backgroundColor: p.card, borderWidth: 2, elevation: 2,
  },
  totalValue: { fontWeight: '700', fontFamily: f.numeric },
  totalLabel: { marginTop: 2 },
  card: { marginBottom: 12, borderRadius: 12, backgroundColor: p.card },
  cardTitle: { fontFamily: f.display, color: p.ink },
  envRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: p.line2 },
  envLabel: { color: p.ink, flex: 1 },
  envCount: { fontWeight: '700', color: p.acc, fontFamily: f.numeric },
  emptyNote: { color: p.sub, lineHeight: 18 },
  speciesRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8, gap: 8 },
  speciesName: { width: 110, color: p.ink },
  bar: { flex: 1, height: 8, borderRadius: 4 },
  speciesCount: { width: 24, textAlign: 'right', fontWeight: '700', color: p.acc, fontFamily: f.numeric },
});
