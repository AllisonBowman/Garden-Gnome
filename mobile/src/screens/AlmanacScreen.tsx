import React, { useMemo, useState } from 'react';
import { View, ScrollView, StyleSheet } from 'react-native';
import {
  Text, Card, Searchbar, ActivityIndicator, Chip,
} from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { fetchSpeciesList } from '../api/species';
import { fetchPlants } from '../api/plants';
import { Species } from '../types';
import { tierOf, fingerprint, matchesQuery, TIER_LABELS, Tier } from '../almanac/tier';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import Eyebrow from '../components/Eyebrow';
import Pill from '../components/Pill';
import type { CensusStackParamList } from '../../App';

type Nav = NativeStackNavigationProp<CensusStackParamList, 'Almanac'>;
type Filter = 'all' | Tier;

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'beginner', label: TIER_LABELS.beginner },
  { value: 'intermediate', label: TIER_LABELS.intermediate },
  { value: 'fussy', label: TIER_LABELS.fussy },
];

const TIER_TONE: Record<Tier, 'good' | 'accent' | 'warn'> = {
  beginner: 'good',
  intermediate: 'accent',
  fussy: 'warn',
};

function SpeciesCard({
  species, owned, onPress,
}: {
  species: Species; owned: boolean; onPress: () => void;
}) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const tier = tierOf(species);
  const fp = fingerprint(species);

  return (
    <Card style={styles.card} mode="elevated" onPress={onPress}>
      <Card.Content>
        <View style={styles.cardHead}>
          <Text variant="titleMedium" style={styles.common}>{species.common_name}</Text>
          <Pill tone={TIER_TONE[tier]} filled>{TIER_LABELS[tier]}</Pill>
        </View>
        <Text variant="bodySmall" style={styles.latin}>{species.scientific_name}</Text>

        <View style={styles.fingerprint}>
          <Text style={styles.fpItem}>{fp.water}</Text>
          <Text style={styles.fpItem}>{fp.light}</Text>
          <Text style={styles.fpItem}>{fp.humidity}</Text>
        </View>

        {owned ? <Text style={styles.owned}>✿ you keep this one</Text> : null}
      </Card.Content>
    </Card>
  );
}

export default function AlmanacScreen() {
  const navigation = useNavigation<Nav>();
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<Filter>('all');

  const { data: species = [], isLoading } = useQuery({
    queryKey: ['species'],
    queryFn: fetchSpeciesList,
  });
  // Which species the caretaker already keeps — the almanac reads differently
  // when it can point at your own shelf.
  const { data: plants = [] } = useQuery({ queryKey: ['plants'], queryFn: fetchPlants });
  const ownedIds = useMemo(
    () => new Set(plants.map((p) => p.species_id)),
    [plants],
  );

  const shown = useMemo(
    () => species.filter((s) =>
      matchesQuery(s, query) && (filter === 'all' || tierOf(s) === filter)),
    [species, query, filter],
  );

  if (isLoading) return <ActivityIndicator style={styles.center} size="large" />;

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text variant="bodyMedium" style={styles.intro}>
          A living count of what growers keep — {species.length} species in the
          catalog{ownedIds.size > 0 ? `, ${ownedIds.size} of them on your shelf` : ''}.
          Read any species to learn its ways.
        </Text>

        <Searchbar
          placeholder={`Search ${species.length} species…`}
          value={query}
          onChangeText={setQuery}
          style={styles.search}
          inputStyle={styles.searchInput}
        />

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filters}>
          {FILTERS.map((f) => (
            <Chip
              key={f.value}
              selected={filter === f.value}
              onPress={() => setFilter(f.value)}
              style={styles.filterChip}
              compact
            >
              {f.label}
            </Chip>
          ))}
        </ScrollView>

        <Eyebrow style={styles.eyebrow}>Species · {shown.length} shown</Eyebrow>

        {shown.length === 0 ? (
          <Text style={styles.empty}>
            Nothing matches that. Try a different name, or widen the filter.
          </Text>
        ) : (
          shown.map((s) => (
            <SpeciesCard
              key={s.id}
              species={s}
              owned={ownedIds.has(s.id)}
              onPress={() => navigation.navigate('SpeciesDetail', { speciesId: s.id })}
            />
          ))
        )}
      </ScrollView>
    </View>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  container: { flex: 1, backgroundColor: p.bg },
  content: { padding: 12, paddingBottom: 48 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  intro: { color: p.sub, lineHeight: 20, marginBottom: 12 },
  search: { marginBottom: 10, backgroundColor: p.card },
  searchInput: { color: p.ink },
  filters: { gap: 8, paddingVertical: 2, marginBottom: 8 },
  filterChip: { backgroundColor: p.card2 },
  eyebrow: { marginBottom: 8 },
  card: { marginBottom: 10, borderRadius: 12, backgroundColor: p.card },
  cardHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8 },
  common: { color: p.ink, fontFamily: f.display, flexShrink: 1 },
  latin: { color: p.sub, fontStyle: 'italic', marginTop: 2 },
  fingerprint: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginTop: 8 },
  fpItem: { color: p.sub, fontSize: 12 },
  owned: { color: p.good, fontSize: 12, marginTop: 8, fontWeight: '600' },
  empty: { color: p.faint, fontStyle: 'italic', textAlign: 'center', marginTop: 32 },
});
