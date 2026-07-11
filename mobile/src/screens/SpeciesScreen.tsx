import React, { useState, useCallback } from 'react';
import { FlatList, View, StyleSheet, TouchableOpacity } from 'react-native';
import {
  Text, Searchbar, Card, Chip, ActivityIndicator, useTheme,
} from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { fetchSpeciesList } from '../api/species';
import { Species } from '../types';
import { SpeciesStackParamList } from '../../App';

type Nav = NativeStackNavigationProp<SpeciesStackParamList, 'SpeciesList'>;

const LIGHT_ICON: Record<string, string> = {
  low: '🌑', medium: '🌤', bright_indirect: '☁️', direct: '☀️',
};

function SpeciesCard({ species, onPress }: { species: Species; onPress: () => void }) {
  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.85}>
      <Card style={styles.card} mode="elevated">
        <Card.Content>
          <Text variant="titleSmall">{species.common_name}</Text>
          <Text variant="bodySmall" style={styles.scientific}>{species.scientific_name}</Text>
          <View style={styles.chipRow}>
            <Chip compact style={styles.chip}>
              {LIGHT_ICON[species.light_need]} {species.light_need.replace('_', ' ')}
            </Chip>
            <Chip compact style={styles.chip}>
              🌡 {species.temp_f_min}–{species.temp_f_max}°F
            </Chip>
            {species.toxic_to_pets && (
              <Chip compact style={styles.toxicChip} icon="alert">Pet caution</Chip>
            )}
          </View>
        </Card.Content>
      </Card>
    </TouchableOpacity>
  );
}

export default function SpeciesScreen() {
  const theme = useTheme();
  const navigation = useNavigation<Nav>();
  const [search, setSearch] = useState('');

  const { data: speciesList = [], isLoading, isError } = useQuery({
    queryKey: ['species'],
    queryFn: fetchSpeciesList,
  });

  const filtered = speciesList.filter((s: Species) =>
    s.common_name.toLowerCase().includes(search.toLowerCase()) ||
    s.scientific_name.toLowerCase().includes(search.toLowerCase()),
  );

  const renderItem = useCallback(({ item }: { item: Species }) => (
    <SpeciesCard
      species={item}
      onPress={() => navigation.navigate('SpeciesDetail', { speciesId: item.id })}
    />
  ), [navigation]);

  if (isLoading) return <ActivityIndicator style={styles.center} size="large" />;

  if (isError) {
    return (
      <View style={styles.center}>
        <Text style={{ color: '#c00', textAlign: 'center' }}>
          Could not load species.{' '}
          {__DEV__ ? 'Check the API URL in Settings.' : 'Please check your connection and try again.'}
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Searchbar
        placeholder="Search species…"
        value={search}
        onChangeText={setSearch}
        style={styles.searchbar}
      />
      <FlatList
        data={filtered}
        keyExtractor={(s) => String(s.id)}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <Text style={styles.empty}>No species match "{search}".</Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6FAF7' },
  searchbar: { margin: 12, borderRadius: 10 },
  list: { paddingHorizontal: 12, paddingBottom: 24 },
  card: { marginBottom: 8, borderRadius: 10 },
  scientific: { fontStyle: 'italic', color: '#666', marginTop: 2 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 6, gap: 4 },
  chip: { marginRight: 4 },
  toxicChip: { backgroundColor: '#FFE0E0', marginRight: 4 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  empty: { textAlign: 'center', color: '#888', marginTop: 48 },
});
