import React, { useEffect, useMemo, useState } from 'react';
import { View, ScrollView, StyleSheet } from 'react-native';
import {
  Text, Card, Searchbar, ActivityIndicator, Chip, Button,
} from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { RouteProp, useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { fetchSpeciesList } from '../api/species';
import { fetchPlants } from '../api/plants';
import {
  fetchGrowingAreas, fetchCandidates, EVERY_CANDIDATE, FitFinding,
} from '../api/growingAreas';
import { uncheckedNotes } from '../growingAreas/realEstate';
import { CHECK_FAILED, confirmedLine } from '../growingAreas/fitFindings';
import { RANK_ORDER, inRankOrder } from '../growingAreas/ranking';
import { Species } from '../types';
import { tierOf, fingerprint, matchesQuery, TIER_LABELS, Tier } from '../almanac/tier';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import Eyebrow from '../components/Eyebrow';
import Pill from '../components/Pill';
import type { CensusStackParamList } from '../../App';

// Registered in more than one tab's stack, with the same params in each;
// typed against the Census stack, where it began.
type Nav = NativeStackNavigationProp<CensusStackParamList, 'Almanac'>;
type Route = RouteProp<CensusStackParamList, 'Almanac'>;
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
  species, owned, fits, onPress,
}: {
  species: Species; owned: boolean;
  /** The confirmed findings for the chosen area, when one is chosen. */
  fits?: FitFinding[];
  onPress: () => void;
}) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const tier = tierOf(species);
  const fp = fingerprint(species);
  const confirmed = fits ? confirmedLine(fits) : null;

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

        {confirmed ? <Text style={styles.confirmed}>{confirmed}</Text> : null}
        {owned ? <Text style={styles.owned}>✿ you keep this one</Text> : null}
      </Card.Content>
    </Card>
  );
}

export default function AlmanacScreen() {
  const navigation = useNavigation<Nav>();
  const route = useRoute<Route>();
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<Filter>('all');
  // Which growing area to narrow the catalog to, or null for the whole thing.
  // Opened from an area's screen, it starts narrowed to that area: the rest
  // of the candidates that screen showed the first few of.
  const openedFor = route.params?.growingAreaId ?? null;
  const [areaId, setAreaId] = useState<number | null>(openedFor);
  useEffect(() => {
    if (openedFor != null) setAreaId(openedFor);
  }, [openedFor]);

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

  const { data: areas = [] } = useQuery({
    queryKey: ['growingAreas'],
    queryFn: fetchGrowingAreas,
  });

  // An area deleted elsewhere stops being a filter rather than becoming one
  // that matches nothing.
  const area = areas.find((a) => a.id === areaId) ?? null;
  useEffect(() => {
    if (areaId != null && areas.length > 0 && area == null) setAreaId(null);
  }, [areaId, areas, area]);

  // The fit rules live on the server and are asked for, not re-implemented
  // here. There is no mirrored TS fit engine, on purpose: `care/facts.ts`
  // mirrors the backend's *wording*, which can drift harmlessly; a verdict
  // cannot — two places deciding what suits a space would eventually
  // disagree about it, and the user would see both. React Query's cache
  // covers the offline case that a local copy would have. Every candidate,
  // not the best few: the endpoint truncates after ranking, and a species
  // cut off the end would vanish from this filter as if it did not fit.
  const {
    // First load only: a background refetch keeps the cached list and notes
    // on screen rather than blanking them.
    data: candidates = [], isLoading: fitLoading, isError: fitFailed, refetch: refetchFit,
  } = useQuery({
    queryKey: ['growingAreaCandidates', areaId, 'every'],
    queryFn: () => fetchCandidates(areaId as number, EVERY_CANDIDATE),
    enabled: areaId != null,
  });
  const fitsById = useMemo(
    () => new Map(candidates.map((c) => [c.species_id, c.fits])),
    [candidates],
  );
  // Which axes the chosen area turns on that nothing on its list could
  // confirm — the same notes the area's own screen shows, so a thin list
  // here is not read as a verdict on the space either.
  const notes = area != null && !fitLoading && !fitFailed
    ? uncheckedNotes(area, candidates) : [];

  const shown = useMemo(() => {
    const matching = species.filter((s) =>
      matchesQuery(s, query)
      && (filter === 'all' || tierOf(s) === filter)
      && (areaId == null || fitsById.has(s.id)));
    // Narrowed to an area, the species go in the order the area's own screen
    // ranks them, so "see all" carries on from where that list stopped.
    return areaId == null ? matching : inRankOrder(matching, candidates);
  }, [species, query, filter, areaId, fitsById, candidates]);

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

        {areas.length > 0 ? (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filters}>
            <Chip
              selected={areaId === null}
              onPress={() => setAreaId(null)}
              style={styles.filterChip}
              compact
            >
              Anywhere
            </Chip>
            {areas.map((a) => (
              <Chip
                key={a.id}
                selected={areaId === a.id}
                onPress={() => setAreaId(a.id)}
                style={styles.filterChip}
                compact
              >
                {`Fits ${a.name}`}
              </Chip>
            ))}
          </ScrollView>
        ) : null}

        <Eyebrow style={styles.eyebrow}>Species · {fitFailed ? 0 : shown.length} shown</Eyebrow>

        {area != null && !fitLoading && !fitFailed ? (
          <>
            <Text style={styles.fitNote}>
              Showing species with nothing on record against {area.name} and at
              least one thing confirmed. A plant missing from here may simply be
              one the catalog can’t judge for this spot yet. {RANK_ORDER}
            </Text>
            {notes.map((note, i) => (
              <Text key={i} style={styles.caveat}>{note}</Text>
            ))}
          </>
        ) : null}

        {area != null && fitFailed ? (
          // Not an empty list: an empty list here would read as "nothing
          // suits this spot", and a request that failed has judged nothing.
          <View style={styles.failed}>
            <Text style={styles.empty}>{CHECK_FAILED}</Text>
            <Button compact onPress={() => refetchFit()}>Try again</Button>
          </View>
        ) : shown.length === 0 ? (
          <Text style={styles.empty}>
            {fitLoading
              ? 'Checking what suits that spot…'
              : 'Nothing matches that. Try a different name, or widen the filter.'}
          </Text>
        ) : (
          shown.map((s) => (
            <SpeciesCard
              key={s.id}
              species={s}
              owned={ownedIds.has(s.id)}
              fits={areaId != null ? fitsById.get(s.id) : undefined}
              // Filtered to an area, the species page shows how it suits that
              // area in full — the detail behind the card's "Confirmed here".
              onPress={() => navigation.navigate('SpeciesDetail', {
                speciesId: s.id, growingAreaId: areaId ?? undefined,
              })}
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
  confirmed: { color: p.sub, fontSize: 12, lineHeight: 17, marginTop: 8 },
  empty: { color: p.faint, fontStyle: 'italic', textAlign: 'center', marginTop: 32 },
  failed: { alignItems: 'center', gap: 8 },
  fitNote: { color: p.faint, fontSize: 12.5, lineHeight: 18, marginBottom: 10 },
  caveat: { color: p.warn, fontSize: 12.5, lineHeight: 18, marginBottom: 10 },
});
