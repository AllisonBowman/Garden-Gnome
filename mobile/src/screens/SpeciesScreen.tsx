import React, { useState, useCallback, useMemo } from 'react';
import { FlatList, View, StyleSheet, TouchableOpacity } from 'react-native';
import {
  Text, Searchbar, Card, ActivityIndicator, useTheme,
} from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { fetchSpeciesList } from '../api/species';
import { Species } from '../types';
import { legacyStats, waterRegimeSentence } from '../care/facts';
import { SpeciesStackParamList } from '../../App';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import Pill from '../components/Pill';

type Nav = NativeStackNavigationProp<SpeciesStackParamList, 'SpeciesList'>;

const LIGHT_ICON: Record<string, string> = {
  low: '🌑', medium: '🌤', bright_indirect: '☁️', direct: '☀️',
};

function SpeciesCard({ species, onPress }: { species: Species; onPress: () => void }) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  // Legacy pills only where nothing resolved replaces them; the watering
  // pill only when the regime was cited to this species itself — a borrowed
  // regime is labelled on the detail screen, and a pill has no room for
  // the label (ADR 0002).
  const stats = legacyStats(species);
  const light = stats.find((s) => s.key === 'light');
  const temp = stats.find((s) => s.key === 'temperature');
  const watering = species.care_provenance?.water_regime === 'sourced'
    ? waterRegimeSentence(species) : null;
  const lightIcon = species.light_need ? LIGHT_ICON[species.light_need] ?? '' : '';
  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.85}>
      <Card style={styles.card} mode="elevated">
        <Card.Content>
          <Text variant="titleSmall" style={styles.name}>{species.common_name}</Text>
          <Text variant="bodySmall" style={styles.scientific}>{species.scientific_name}</Text>
          <View style={styles.chipRow}>
            {light && (
              <Pill>{lightIcon} {light.value}</Pill>
            )}
            {temp && (
              <Pill>🌡 {temp.value}</Pill>
            )}
            {watering && (
              <Pill>💧 {watering}</Pill>
            )}
            {/* "cited" only beside a value that is. The light and temp pills
                are catalog values, and a cited pill next to them alone would
                lend them a citation no source gave. */}
            {watering && species.care_data_status === 'sourced' && (
              <Pill tone="good">cited</Pill>
            )}
            {species.toxic_to_pets && (
              <Pill tone="warn" filled>Pet caution</Pill>
            )}
          </View>
        </Card.Content>
      </Card>
    </TouchableOpacity>
  );
}

export default function SpeciesScreen() {
  const theme = useTheme();
  const { palette, fonts } = useAppTheme();
  const navigation = useNavigation<Nav>();
  const [search, setSearch] = useState('');
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);

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
        <Text style={styles.error}>
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

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  container: { flex: 1, backgroundColor: p.bg },
  searchbar: { margin: 12, borderRadius: 10, backgroundColor: p.card },
  list: { paddingHorizontal: 12, paddingBottom: 24 },
  card: { marginBottom: 8, borderRadius: 12, backgroundColor: p.card },
  name: { fontFamily: f.display, color: p.ink },
  scientific: { fontStyle: 'italic', color: p.sub, marginTop: 2 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 6, gap: 4 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  error: { color: p.warn, textAlign: 'center' },
  empty: { textAlign: 'center', color: p.faint, marginTop: 48 },
});
