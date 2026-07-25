import React, { useMemo } from 'react';
import { ScrollView, View, StyleSheet, Alert } from 'react-native';
import { Text, Card, Button, ActivityIndicator, ProgressBar } from 'react-native-paper';
import { useQuery, useMutation } from '@tanstack/react-query';
import { fetchCensusSummary, syncCensus } from '../api/census';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import Eyebrow from '../components/Eyebrow';

const ENV_LABEL: Record<string, string> = {
  home: '🏠 Home', nursery: '🌱 Nursery',
  community_garden: '🌳 Community garden',
  conservation: '🌿 Conservation', research: '🔬 Research',
};

export default function CensusScreen() {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);

  const { data: summary, isLoading, isError, refetch } = useQuery({
    queryKey: ['census'],
    queryFn: fetchCensusSummary,
  });

  const syncMutation = useMutation({
    mutationFn: syncCensus,
    onSuccess: (res) => Alert.alert('Sync', res.message ?? res.status),
    onError: () => Alert.alert('Sync failed', 'Could not reach the census server.'),
  });

  if (isLoading) return <ActivityIndicator style={styles.center} size="large" />;

  if (isError || !summary) {
    return (
      <View style={styles.center}>
        <Text style={{ color: palette.warn, textAlign: 'center' }}>
          Could not load census.{' '}
          {__DEV__ ? 'Check the API URL in Settings.' : 'Please check your connection and try again.'}
        </Text>
        <Button onPress={() => refetch()} style={{ marginTop: 12 }}>Retry</Button>
      </View>
    );
  }

  const topSpecies = summary.species_distribution.slice(0, 8);
  const maxCount = Math.max(...topSpecies.map((s) => s.count), 1);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Totals */}
      <View style={styles.totalsRow}>
        <TotalCard styles={styles} label="Plants" value={summary.total_plants} color={palette.acc} />
        <TotalCard styles={styles} label="Environments" value={summary.total_environments} color={palette.sub} />
      </View>

      {/* Environments by type */}
      <Card style={styles.card}>
        <Card.Title title="Environments by type" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          {Object.entries(summary.environments_by_type).map(([type, count]) => (
            <View key={type} style={styles.envRow}>
              <Text variant="bodySmall" style={styles.envLabel}>
                {ENV_LABEL[type] ?? type}
              </Text>
              <Text variant="bodySmall" style={styles.envCount}>{count}</Text>
            </View>
          ))}
        </Card.Content>
      </Card>

      {/* Species distribution */}
      <Card style={styles.card}>
        <Card.Title title="Top species" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          {topSpecies.map((s) => (
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

      {/* Sync */}
      <Card style={styles.card}>
        <Card.Title title="Census sync" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          <Text variant="bodySmall" style={styles.syncNote}>
            Push anonymised plant data to the central census server (if configured).
          </Text>
          <Button
            mode="contained"
            onPress={() => syncMutation.mutate()}
            loading={syncMutation.isPending}
            style={styles.syncBtn}
            buttonColor={palette.acc}
            textColor={palette.btnInk}
          >
            Sync now
          </Button>
        </Card.Content>
      </Card>
    </ScrollView>
  );
}

type Styles = ReturnType<typeof makeStyles>;

function TotalCard({ styles, label, value, color }: { styles: Styles; label: string; value: number; color: string }) {
  return (
    <View style={[styles.totalCard, { borderColor: color }]}>
      <Text variant="displaySmall" style={[styles.totalValue, { color }]}>{value}</Text>
      <Eyebrow style={styles.totalLabel}>{label}</Eyebrow>
    </View>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
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
  speciesRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8, gap: 8 },
  speciesName: { width: 110, color: p.ink },
  bar: { flex: 1, height: 8, borderRadius: 4 },
  speciesCount: { width: 24, textAlign: 'right', fontWeight: '700', color: p.acc, fontFamily: f.numeric },
  syncNote: { color: p.sub, marginBottom: 12 },
  syncBtn: { borderRadius: 8 },
});
