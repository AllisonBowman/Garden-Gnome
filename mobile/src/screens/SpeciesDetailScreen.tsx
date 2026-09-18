import React, { useMemo } from 'react';
import { ScrollView, View, StyleSheet } from 'react-native';
import {
  Text, Card, Chip, List, ActivityIndicator,
} from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { RouteProp, useRoute } from '@react-navigation/native';
import { fetchSpecies } from '../api/species';
import { SpeciesStackParamList } from '../../App';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import { careFactRows, legacyStats } from '../care/facts';
import {
  CareFactList, CareSourceRows, CareStatusLine, LegacyStatRow,
} from '../components/CareFacts';

type Route = RouteProp<SpeciesStackParamList, 'SpeciesDetail'>;

const CARE_ICON: Record<string, string> = {
  water: '💧', fertilize: '🌿', mist: '💨', prune: '✂️',
  repot: '🪴', rotate: '🔄', clean: '🧹', other: '•',
};

export default function SpeciesDetailScreen() {
  const route = useRoute<Route>();
  const { speciesId } = route.params;
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);

  const { data: species, isLoading } = useQuery({
    queryKey: ['species', speciesId],
    queryFn: () => fetchSpecies(speciesId),
  });

  if (isLoading || !species) {
    return <ActivityIndicator style={styles.center} size="large" />;
  }

  // Which cards have anything to say. A row minted from the claim tranche
  // has facts and sources but no legacy stats; a legacy row the recompute
  // never reached has the reverse. Neither gets an empty card.
  const hasFacts = careFactRows(species).length > 0;
  const hasLegacy = legacyStats(species).length > 0;
  const sources = species.care_sources ?? [];
  const traits = (species.traits ?? []).filter((t) => t.trait !== 'humidity_source');

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <Text variant="headlineSmall" style={styles.title}>
          {species.common_name}
        </Text>
        <Text variant="bodyMedium" style={styles.scientific}>
          {species.scientific_name}
        </Text>
        <CareStatusLine species={species} style={styles.status} />
        {/* The generated sentence when the API supplies one — it distinguishes
            which parts are toxic and to which animals. Falls back to the flat
            chip on older API versions. */}
        {species.toxicity_description ? (
          <Text variant="bodySmall" style={styles.toxicityNote}>
            {species.toxicity_description}
          </Text>
        ) : species.toxic_to_pets ? (
          <Chip icon="alert" style={styles.toxicChip} textStyle={styles.toxicChipText}>
            ⚠️ Toxic to pets
          </Chip>
        ) : null}
      </View>

      {/* The resolved facts — what the claims settled, labelled where a value
          was borrowed from the genus. */}
      {hasFacts && (
        <Card style={styles.card}>
          <Card.Title title="Care facts" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
          <Card.Content>
            <CareFactList species={species} />
          </Card.Content>
        </Card>
      )}

      {/* Legacy stats, only where no resolved fact replaces them. */}
      {hasLegacy && (
        <Card style={styles.card}>
          <Card.Content>
            <LegacyStatRow species={species} />
          </Card.Content>
        </Card>
      )}

      {/* Care notes */}
      {species.care_notes ? (
        <Card style={styles.card}>
          <Card.Title title="Care notes" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
          <Card.Content>
            <Text variant="bodyMedium" style={styles.notes}>{species.care_notes}</Text>
          </Card.Content>
        </Card>
      ) : null}

      {/* Where the facts came from: names and links, never the passage. */}
      {sources.length > 0 && (
        <Card style={styles.card}>
          <Card.Title title="Sources" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
          <Card.Content>
            <CareSourceRows sources={sources} />
          </Card.Content>
        </Card>
      )}

      {/* Schedules */}
      {species.care_schedules && species.care_schedules.length > 0 && (
        <Card style={styles.card}>
          <Card.Title title="Recommended schedule" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
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

      {/* Traits. humidity_source is pipeline provenance ("derived from
          watering category…"), not a plant trait — rendering it verbatim was
          a developer-text leak. */}
      {traits.length > 0 && (
        <Card style={styles.card}>
          <Card.Title title="Plant traits" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
          <Card.Content>
            {traits.map((t) => (
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

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  container: { flex: 1, backgroundColor: p.bg },
  content: { padding: 12, paddingBottom: 48 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { marginBottom: 12 },
  title: { color: p.acc, fontFamily: f.display },
  scientific: { fontStyle: 'italic', color: p.sub, fontFamily: f.display, marginTop: 2, marginBottom: 6 },
  status: { marginBottom: 6 },
  toxicChip: { backgroundColor: p.warnSoft, alignSelf: 'flex-start' },
  toxicChipText: { color: p.warn },
  toxicityNote: { color: p.warn, marginTop: 4, lineHeight: 19 },
  card: { marginBottom: 12, borderRadius: 12, backgroundColor: p.card },
  cardTitle: { color: p.ink, fontFamily: f.display },
  notes: { lineHeight: 22, color: p.ink },
  listItem: { paddingVertical: 4 },
  traitRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: p.line2 },
  traitKey: { color: p.sub, textTransform: 'capitalize', flex: 1 },
});
