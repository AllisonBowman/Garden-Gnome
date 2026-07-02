import React from 'react';
import { ScrollView, View, StyleSheet, Alert } from 'react-native';
import { Text, Card, Button, ActivityIndicator, ProgressBar, useTheme } from 'react-native-paper';
import { useQuery, useMutation } from '@tanstack/react-query';
import { fetchCensusSummary, syncCensus } from '../api/census';

const ENV_LABEL: Record<string, string> = {
  home: '🏠 Home', nursery: '🌱 Nursery',
  community_garden: '🌳 Community garden',
  conservation: '🌿 Conservation', research: '🔬 Research',
};

export default function CensusScreen() {
  const theme = useTheme();

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
        <Text style={{ color: '#c00', textAlign: 'center' }}>
          Could not load census. Check your API URL in Settings.
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
        <TotalCard label="Plants" value={summary.total_plants} color={theme.colors.primary} />
        <TotalCard label="Environments" value={summary.total_environments} color="#52796F" />
      </View>

      {/* Environments by type */}
      <Card style={styles.card}>
        <Card.Title title="Environments by type" titleVariant="titleMedium" />
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
        <Card.Title title="Top species" titleVariant="titleMedium" />
        <Card.Content>
          {topSpecies.map((s) => (
            <View key={s.species_id} style={styles.speciesRow}>
              <Text variant="bodySmall" style={styles.speciesName} numberOfLines={1}>
                {s.common_name}
              </Text>
              <ProgressBar
                progress={s.count / maxCount}
                color={theme.colors.primary}
                style={styles.bar}
              />
              <Text variant="bodySmall" style={styles.speciesCount}>{s.count}</Text>
            </View>
          ))}
        </Card.Content>
      </Card>

      {/* Sync */}
      <Card style={styles.card}>
        <Card.Title title="Census sync" titleVariant="titleMedium" />
        <Card.Content>
          <Text variant="bodySmall" style={styles.syncNote}>
            Push anonymised plant data to the central census server (if configured).
          </Text>
          <Button
            mode="contained"
            onPress={() => syncMutation.mutate()}
            loading={syncMutation.isPending}
            style={styles.syncBtn}
            buttonColor="#52796F"
          >
            Sync now
          </Button>
        </Card.Content>
      </Card>
    </ScrollView>
  );
}

function TotalCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View style={[styles.totalCard, { borderColor: color }]}>
      <Text variant="displaySmall" style={{ color, fontWeight: '700' }}>{value}</Text>
      <Text variant="labelMedium" style={{ color: '#555' }}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6FAF7' },
  content: { padding: 12, paddingBottom: 48 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  totalsRow: { flexDirection: 'row', gap: 12, marginBottom: 12 },
  totalCard: {
    flex: 1, alignItems: 'center', padding: 16, borderRadius: 12,
    backgroundColor: '#fff', borderWidth: 2, elevation: 2,
  },
  card: { marginBottom: 12, borderRadius: 12 },
  envRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#eee' },
  envLabel: { color: '#333', flex: 1 },
  envCount: { fontWeight: '700', color: '#2D6A4F' },
  speciesRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8, gap: 8 },
  speciesName: { width: 110, color: '#333' },
  bar: { flex: 1, height: 8, borderRadius: 4 },
  speciesCount: { width: 24, textAlign: 'right', fontWeight: '700', color: '#2D6A4F' },
  syncNote: { color: '#666', marginBottom: 12 },
  syncBtn: { borderRadius: 8 },
});
