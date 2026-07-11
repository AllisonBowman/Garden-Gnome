import React, { useCallback } from 'react';
import {
  FlatList, View, StyleSheet, RefreshControl, TouchableOpacity,
} from 'react-native';
import {
  Text, Card, FAB, Chip, ActivityIndicator, useTheme,
} from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { fetchPlants } from '../api/plants';
import { Plant } from '../types';
import { PlantsStackParamList } from '../../App';
import StreakBadges from '../streaks/StreakBadges';
import EmptyState from '../components/EmptyState';

type Nav = NativeStackNavigationProp<PlantsStackParamList, 'PlantsList'>;

const LIGHT_LABELS: Record<string, string> = {
  low: 'Low light',
  medium: 'Medium',
  bright_indirect: 'Bright indirect',
  direct: 'Direct sun',
};

function PlantCard({ plant, onPress }: { plant: Plant; onPress: () => void }) {
  const theme = useTheme();
  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.85}>
      <Card style={styles.card} mode="elevated">
        <Card.Content>
          <Text variant="titleMedium" style={{ color: theme.colors.primary }}>
            {plant.nickname}
          </Text>
          {plant.species && (
            <Text variant="bodySmall" style={styles.scientific}>
              {plant.species.scientific_name}
            </Text>
          )}
          <View style={styles.chipRow}>
            {plant.species && (
              <Chip compact icon="weather-sunny" style={styles.chip}>
                {LIGHT_LABELS[plant.species.light_need] ?? plant.species.light_need}
              </Chip>
            )}
            {plant.species?.toxic_to_pets && (
              <Chip compact icon="alert" style={[styles.chip, styles.toxicChip]}>
                Pet caution
              </Chip>
            )}
          </View>
          {plant.location ? (
            <Text variant="bodySmall" style={styles.location}>
              📍 {plant.location}
            </Text>
          ) : null}
        </Card.Content>
      </Card>
    </TouchableOpacity>
  );
}

export default function PlantsScreen() {
  const navigation = useNavigation<Nav>();
  const { data: plants, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ['plants'],
    queryFn: fetchPlants,
  });

  const renderItem = useCallback(({ item }: { item: Plant }) => (
    <PlantCard
      plant={item}
      onPress={() => navigation.navigate('PlantDetail', { plantId: item.id })}
    />
  ), [navigation]);

  if (isLoading) {
    return <ActivityIndicator style={styles.center} size="large" />;
  }

  if (isError) {
    return (
      <View style={styles.center}>
        <Text variant="bodyLarge" style={styles.errorText}>
          Could not reach the backend.{'\n'}Check your API URL in Settings.
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={plants}
        keyExtractor={(p) => String(p.id)}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        ListHeaderComponent={<StreakBadges />}
        ListEmptyComponent={
          <EmptyState
            emoji="🪴"
            title="Your garden's empty"
            body="Add your first plant and Garden Gnome will help you keep it thriving — gentle reminders when care is due, no pressure."
            actionLabel="Add your first plant"
            onAction={() => navigation.navigate('AddPlant')}
          />
        }
        refreshControl={
          <RefreshControl refreshing={isRefetching} onRefresh={refetch} />
        }
      />
      <FAB
        icon="plus"
        style={styles.fab}
        onPress={() => navigation.navigate('AddPlant')}
        label="Add plant"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6FAF7' },
  list: { padding: 12, paddingBottom: 96 },
  card: { marginBottom: 10, borderRadius: 12 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 6, gap: 4 },
  chip: { marginRight: 4 },
  toxicChip: { backgroundColor: '#FFE0E0' },
  scientific: { color: '#666', fontStyle: 'italic', marginTop: 2 },
  location: { color: '#888', marginTop: 4 },
  fab: { position: 'absolute', right: 16, bottom: 24, backgroundColor: '#2D6A4F' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  errorText: { textAlign: 'center', color: '#c00' },
  empty: { textAlign: 'center', color: '#888', marginTop: 48, fontSize: 15 },
});
