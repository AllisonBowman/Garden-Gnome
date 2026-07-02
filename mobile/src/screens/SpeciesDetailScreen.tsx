import React from 'react';
import { ScrollView, View, StyleSheet } from 'react-native';
import {
  Text, Card, Chip, Divider, List, ActivityIndicator, useTheme,
} from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { RouteProp, useRoute } from '@react-navigation/native';
import { fetchSpecies } from '../api/species';
import { SpeciesStackParamList } from '../../App';

type Route = RouteProp<SpeciesStackParamList, 'SpeciesDetail'>;

const CARE_ICON: Record<string, string> = {
  water: '💧', fertilize: '🌿', mist: '💨', prune: '✂️',
  repot: '🪴', rotate: '🔄', clean: '🧹', other: '•',
};

export default function SpeciesDetailScreen() {
  const route = useRoute<Route>();
  const { speciesId } = route.params;
  const theme = useTheme();

  const { data: species, isLoading } = useQuery({
    queryKey: ['species', speciesId],
    queryFn: () => fetchSpecies(speciesId),
  });

  if (isLoading || !species) {
    return <ActivityIndicator style={styles.center} size="large" />;
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <Text variant="headlineSmall" style={{ color: theme.colors.primary }}>
          {species.common_name}
        </Text>
        <Text variant="bodyMedium" style={styles.scientific}>
          {species.scientific_name}
        </Text>
        {species.toxic_to_pets && (
          <Chip icon="alert" style={styles.toxicChip} textStyle={{ color: '#900' }}>
            ⚠️ Toxic to pets
          </Chip>
        )}
      </View>

      {/* Care summary stats */}
      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.statRow}>
            <Stat label="Light"    value={species.light_need.replace(/_/g, ' ')} />
            <Stat label="Humidity" value={`${species.humidity_pct_min}–${species.humidity_pct_max}%`} />
            <Stat label="Temp"     value={`${species.temp_f_min}–${species.temp_f_max}°F`} />
          </View>
          <Divider style={styles.divider} />
          <Text variant="labelSmall" style={styles.soilLabel}>Soil</Text>
          <Text variant="bodySmall">{species.soil_type}</Text>
        </Card.Content>
      </Card>

      {/* Care notes */}
      <Card style={styles.card}>
        <Card.Title title="Care notes" titleVariant="titleMedium" />
        <Card.Content>
          <Text variant="bodyMedium" style={styles.notes}>{species.care_notes}</Text>
        </Card.Content>
      </Card>

      {/* Schedules */}
      {species.care_schedules && species.care_schedules.length > 0 && (
        <Card style={styles.card}>
          <Card.Title title="Recommended schedule" titleVariant="titleMedium" />
          <Card.Content>
            {species.care_schedules.map((sched) => (
              <List.Item
                key={sched.id}
                title={`${CARE_ICON[sched.care_type] ?? '•'} ${sched.care_type.charAt(0).toUpperCase() + sched.care_type.slice(1)}`}
                description={
                  `Every ${sched.interval_days_min}–${sched.interval_days_max} days` +
                  (sched.notes ? `\n${sched.notes}` : '')
                }
                descriptionNumberOfLines={4}
                style={styles.listItem}
              />
            ))}
          </Card.Content>
        </Card>
      )}

      {/* Traits */}
      {species.traits && species.traits.length > 0 && (
        <Card style={styles.card}>
          <Card.Title title="Plant traits" titleVariant="titleMedium" />
          <Card.Content>
            {species.traits.map((t) => (
              <View key={t.id} style={styles.traitRow}>
                <Text variant="labelMedium" style={styles.traitKey}>
                  {t.trait.replace(/_/g, ' ')}
                </Text>
                <Text variant="bodySmall">
                  {t.value}{t.unit ? ` ${t.unit}` : ''}
                </Text>
              </View>
            ))}
          </Card.Content>
        </Card>
      )}
    </ScrollView>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.stat}>
      <Text variant="labelSmall" style={styles.statLabel}>{label}</Text>
      <Text variant="bodyMedium" style={styles.statValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6FAF7' },
  content: { padding: 12, paddingBottom: 48 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { marginBottom: 12 },
  scientific: { fontStyle: 'italic', color: '#555', marginTop: 2, marginBottom: 8 },
  toxicChip: { backgroundColor: '#FFE0E0', alignSelf: 'flex-start' },
  card: { marginBottom: 12, borderRadius: 12 },
  statRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  stat: { alignItems: 'center', flex: 1 },
  statLabel: { color: '#888', marginBottom: 2 },
  statValue: { fontWeight: '600', textTransform: 'capitalize' },
  divider: { marginBottom: 12 },
  soilLabel: { color: '#888', marginBottom: 4 },
  notes: { lineHeight: 22, color: '#333' },
  listItem: { paddingVertical: 4 },
  traitRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#eee' },
  traitKey: { color: '#555', textTransform: 'capitalize', flex: 1 },
});
