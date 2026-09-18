import React, { useMemo, useState } from 'react';
import {
  ScrollView, View, StyleSheet, Platform, Alert,
} from 'react-native';
import {
  Text, Card, Chip, ActivityIndicator, Surface, Divider, Button,
} from 'react-native-paper';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { RouteProp, useRoute } from '@react-navigation/native';
import {
  fetchGrowingArea, fetchGrowingAreaWeather, updateGrowingArea,
  fetchCandidates, fetchMisfits,
} from '../api/growingAreas';
import { WeatherDay } from '../types';
import {
  conditionText, weekday, exposureSummary, translateWeather,
} from '../weather/translate';
import { GrowingAreasStackParamList } from '../../App';
import WeatherCredit from '../components/WeatherCredit';
import AddressPicker from '../components/AddressPicker';
import { ResolvedPlace } from '../location/geocode';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import { useCareTasks } from '../care/useCareTasks';
import CareCalendar from '../care/CareCalendar';
import {
  SURFACE_LABEL, GOALS, dimensionPrompts, uncheckedNotes,
} from '../growingAreas/realEstate';
import Eyebrow from '../components/Eyebrow';

type Route = RouteProp<GrowingAreasStackParamList, 'GrowingAreaDetail'>;

const AREA_TYPE_LABEL: Record<string, string> = {
  home: '🏠 Home',
  nursery: '🌱 Nursery',
  community_garden: '🌳 Community garden',
  conservation: '🌿 Conservation',
  research: '🔬 Research',
  balcony: '🪴 Balcony',
  greenhouse: '🏕️ Greenhouse',
  other: '📍 Other',
};
const SHELTER_LABEL: Record<string, string> = {
  sheltered: '🏠 Sheltered',
  partial: '⛱️ Partial cover',
  exposed: '🌤️ Exposed',
};
const TEMP_LABEL: Record<string, string> = {
  indoor: '🌡️ Indoor temp',
  outdoor: '🍃 Outdoor temp',
};
const SUN_LABEL: Record<string, string> = {
  full_sun: '☀️ Full sun',
  partial_sun: '🌤️ Partial sun',
  shade: '🌥️ Shade',
};

function ForecastDay({ day }: { day: WeatherDay }) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  return (
    <View style={styles.foreDay}>
      <Text style={styles.foreDow}>{weekday(day.date)}</Text>
      <Text style={styles.foreTemp}>
        {day.high_f != null ? `${day.high_f}°` : '—'}
      </Text>
      <Text style={styles.foreLow}>
        {day.low_f != null ? `${day.low_f}°` : '—'}
      </Text>
      <Text style={styles.foreMeta}>💧{day.precip_chance_pct ?? 0}%</Text>
      {day.uv_max != null ? <Text style={styles.foreMeta}>UV {day.uv_max}</Text> : null}
    </View>
  );
}

export default function GrowingAreaDetailScreen() {
  const route = useRoute<Route>();
  const { growingAreaId } = route.params;
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const queryClient = useQueryClient();

  const { data: env, isLoading } = useQuery({
    queryKey: ['growingArea', growingAreaId],
    queryFn: () => fetchGrowingArea(growingAreaId),
  });

  const { data: weatherResp, isLoading: weatherLoading } = useQuery({
    queryKey: ['growingAreaWeather', growingAreaId],
    queryFn: () => fetchGrowingAreaWeather(growingAreaId),
    staleTime: 30 * 60 * 1000, // weather is cached hourly server-side
  });

  // Care schedule for the plants living in THIS growing area (scoped by id).
  const { tasks: careTasks, isLoading: careLoading } = useCareTasks(growingAreaId);

  // What doesn't suit this space, and what would. Two reads of the same
  // comparison, so they are fetched together and shown together.
  const { data: misfitRows = [], isLoading: misfitsLoading } = useQuery({
    queryKey: ['growingAreaMisfits', growingAreaId],
    queryFn: () => fetchMisfits(growingAreaId),
  });
  const { data: candidateRows = [], isLoading: candidatesLoading } = useQuery({
    queryKey: ['growingAreaCandidates', growingAreaId],
    queryFn: () => fetchCandidates(growingAreaId, 12),
  });

  // Setting a location on a growing area that has none. GrowingAreas created
  // before the address picker existed have no coordinates, and until now there
  // was no screen anywhere that could add them — granting location permission
  // did nothing for them, because permission is only consulted inside the
  // picker at creation time.
  const [place, setPlace] = useState<ResolvedPlace | null>(null);
  const saveLocation = useMutation({
    mutationFn: () => updateGrowingArea(growingAreaId, {
      city: place?.city ?? '',
      region: place?.region ?? '',
      country: place?.country ?? '',
      lat: place?.lat,
      lng: place?.lng,
    }),
    onSuccess: () => {
      setPlace(null);
      queryClient.invalidateQueries({ queryKey: ['growingArea', growingAreaId] });
      queryClient.invalidateQueries({ queryKey: ['growingAreaWeather', growingAreaId] });
      queryClient.invalidateQueries({ queryKey: ['growingAreas'] });
    },
    onError: () => Alert.alert(
      'Could not save that place',
      'PlantAdvocate could not reach the server. Check your connection and try again.',
    ),
  });

  if (isLoading || !env) {
    return <ActivityIndicator style={styles.center} size="large" />;
  }

  const weather = weatherResp?.available ? weatherResp.weather : null;
  const cur = weather?.current;
  const location = [env.city, env.region].filter(Boolean).join(', ');
  // Distinguishes "we don't know where this is" from "the weather service
  // didn't answer" — they look identical to a caretaker but only one of them
  // is theirs to fix.
  const hasCoords = env.lat != null && env.lng != null;

  // Measured and unmeasured are shown separately and on purpose. A blank
  // rendered as "0 sq ft" would read as a bed with no room in it; naming what
  // nobody has measured is the honest version, and it is also the prompt.
  // Which axes this space turns on that the catalog simply cannot answer.
  // Shown above the list, because a short list is otherwise read as a verdict
  // on the space rather than as a gap in the evidence.
  const caveats = candidatesLoading ? [] : uncheckedNotes(env, candidateRows);

  const prompts = dimensionPrompts(env.surface ?? null);
  const dims = [
    { label: prompts.area.label, raw: env.area_sqft, unit: 'sq ft' },
    { label: prompts.headroom.label, raw: env.headroom_in, unit: 'in' },
    { label: prompts.depth.label, raw: env.soil_depth_in, unit: 'in' },
  ];
  const measurements = dims
    .filter((d) => d.raw != null)
    .map((d) => ({ label: d.label.replace(/ \(.*\)$/, ''), value: `${d.raw} ${d.unit}` }));
  const unmeasured = dims
    .filter((d) => d.raw == null)
    .map((d) => d.label.replace(/ \(.*\)$/, '').toLowerCase());

  return (
    <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
      {/* Header */}
      <Surface style={styles.header} elevation={1}>
        <Text variant="headlineSmall" style={styles.envName}>
          {env.name}
        </Text>
        <Text variant="bodyMedium" style={styles.subtle}>
          {AREA_TYPE_LABEL[env.type] ?? env.type}
        </Text>
        {location ? <Text variant="bodySmall" style={styles.subtle}>📍 {location}</Text> : null}
      </Surface>

      {/* The space itself — what there is to plant into, and what it is for */}
      <Card style={styles.card}>
        <Card.Title title="The space" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          <View style={styles.chipRow}>
            {env.surface ? (
              <Chip compact style={styles.chip}>{SURFACE_LABEL[env.surface]}</Chip>
            ) : null}
            <Chip compact style={styles.chip}>{SHELTER_LABEL[env.shelter] ?? env.shelter}</Chip>
            <Chip compact style={styles.chip}>{TEMP_LABEL[env.temp_exposure] ?? env.temp_exposure}</Chip>
            <Chip compact style={styles.chip}>{SUN_LABEL[env.sun_exposure] ?? env.sun_exposure}</Chip>
          </View>

          {measurements.length > 0 ? (
            <View style={styles.measureRow}>
              {measurements.map((m) => (
                <View key={m.label} style={styles.measure}>
                  <Text style={styles.measureValue}>{m.value}</Text>
                  <Text style={styles.measureLabel}>{m.label}</Text>
                </View>
              ))}
            </View>
          ) : null}

          {unmeasured.length > 0 ? (
            <Text style={styles.unmeasured}>
              Not measured yet: {unmeasured.join(', ')}. Until it is, nothing is
              recommended or ruled out on size here.
            </Text>
          ) : null}

          {env.goals != null ? (
            <>
              <Eyebrow style={styles.goalsLabel}>What it’s for</Eyebrow>
              {env.goals.length === 0 ? (
                <Text style={styles.unmeasured}>
                  Nothing in particular — anything that fits the space.
                </Text>
              ) : (
                <View style={styles.chipRow}>
                  {GOALS.filter((g) => env.goals!.includes(g.value)).map((g) => (
                    <Chip key={g.value} compact style={styles.chip}>{g.label}</Chip>
                  ))}
                </View>
              )}
            </>
          ) : null}
        </Card.Content>
      </Card>

      {/* Needs addressing — the specific ways a plant here doesn't suit the
          space. First card on the screen: it is the one thing on this page
          that asks the caretaker to do something. */}
      <Card style={styles.card}>
        <Card.Title
          title="Needs addressing"
          titleVariant="titleMedium"
          titleStyle={styles.cardTitle}
        />
        <Card.Content>
          {misfitsLoading ? (
            <ActivityIndicator style={{ marginVertical: 16 }} />
          ) : misfitRows.length === 0 ? (
            <Text style={styles.unavailable}>
              Nothing here contradicts the space. Plants the catalog can’t
              judge aren’t listed as fine — they’re just not listed.
            </Text>
          ) : (
            misfitRows.map((m) => (
              <View key={m.plant_id} style={styles.misfit}>
                <Text style={styles.misfitName}>
                  {m.nickname || m.common_name}
                  {m.nickname ? <Text style={styles.misfitSpecies}>{`  ${m.common_name}`}</Text> : null}
                </Text>
                {m.misfits.map((f, i) => (
                  <Text key={i} style={styles.misfitReason}>• {f.sentence}</Text>
                ))}
              </View>
            ))
          )}
        </Card.Content>
      </Card>

      {/* Good candidates — species with nothing against them here AND at
          least one axis the catalog actually confirmed. */}
      <Card style={styles.card}>
        <Card.Title
          title="Good candidates here"
          titleVariant="titleMedium"
          titleStyle={styles.cardTitle}
        />
        <Card.Content>
          {caveats.map((note, i) => (
            <Text key={i} style={styles.caveat}>{note}</Text>
          ))}
          {candidatesLoading ? (
            <ActivityIndicator style={{ marginVertical: 16 }} />
          ) : candidateRows.length === 0 ? (
            <Text style={styles.unavailable}>
              Nothing to put forward yet. A species only appears here once a
              source has confirmed it suits this spot — an unresearched plant
              isn’t a recommendation.
            </Text>
          ) : (
            candidateRows.map((c) => (
              <View key={c.species_id} style={styles.candidate}>
                <Text style={styles.candidateName}>{c.common_name}</Text>
                <Text style={styles.candidateLatin}>{c.scientific_name}</Text>
                {c.fits.map((f, i) => (
                  <Text key={i} style={styles.candidateWhy}>• {f.sentence}</Text>
                ))}
              </View>
            ))
          )}
        </Card.Content>
      </Card>

      {/* Care calendar — the schedule for plants living in this growing area */}
      <Card style={styles.card}>
        <Card.Title title="Care calendar" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          {careLoading ? (
            <ActivityIndicator style={{ marginVertical: 16 }} />
          ) : careTasks.length === 0 ? (
            <Text style={styles.unavailable}>
              No care scheduled here yet. Add plants to this growing area and their
              watering, feeding and grooming schedule fills in the calendar.
            </Text>
          ) : (
            <CareCalendar tasks={careTasks} />
          )}
        </Card.Content>
      </Card>

      {/* Weather strip */}
      <Card style={styles.card}>
        <Card.Title title="Local weather" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          {weatherLoading ? (
            <ActivityIndicator style={{ marginVertical: 16 }} />
          ) : !hasCoords ? (
            // The fix belongs where the problem is stated. Telling someone to
            // add a location without giving them a way to do it is how this
            // looked like a broken feature rather than an unfinished setup.
            <View>
              <Text style={styles.unavailable}>
                This growingArea has no place yet, so there’s no forecast to
                show. Set where it is and the weather follows.
              </Text>
              <AddressPicker onChange={setPlace} />
              <Button
                mode="contained"
                disabled={!place || saveLocation.isPending}
                loading={saveLocation.isPending}
                onPress={() => saveLocation.mutate()}
                style={styles.saveLocationBtn}
              >
                Save this place
              </Button>
            </View>
          ) : !weather ? (
            <Text style={styles.unavailable}>
              {weatherResp?.detail ?? 'Weather isn’t available for this spot yet.'}
            </Text>
          ) : (
            <>
              {/* Now */}
              <View style={styles.nowRow}>
                <View style={styles.nowMain}>
                  <Text style={styles.nowTemp}>
                    {cur?.temp_f != null ? `${cur.temp_f}°F` : '—'}
                  </Text>
                  <Text style={styles.nowCond}>{conditionText(cur?.condition ?? null)}</Text>
                </View>
                <View style={styles.nowStats}>
                  {cur?.humidity_pct != null ? (
                    <Text style={styles.nowStat}>💧 {cur.humidity_pct}% humidity</Text>
                  ) : null}
                  {cur?.uv_index != null ? (
                    <Text style={styles.nowStat}>😎 UV {cur.uv_index}</Text>
                  ) : null}
                </View>
              </View>

              {weather.daily.length > 0 && (
                <>
                  <Divider style={styles.divider} />
                  <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.foreRow}>
                    {weather.daily.map((d) => <ForecastDay key={d.date} day={d} />)}
                  </ScrollView>
                </>
              )}

              {/* Apple Weather attribution — required wherever WeatherKit data shows */}
              <WeatherCredit attribution={weather.attribution} style={styles.attribution} />
            </>
          )}
        </Card.Content>
      </Card>

      {/* OUTSIDE → IN HERE translation */}
      {weather && (
        <Card style={styles.specimenCard}>
          <View style={styles.specimenHeader}>
            <Text style={styles.specimenLabel}>OUTSIDE → IN HERE</Text>
            <Text style={styles.specimenSub}>{exposureSummary(env)}</Text>
          </View>
          <Card.Content style={styles.specimenBody}>
            {translateWeather(env, weather).map((line, i) => (
              <Text key={i} style={styles.translateLine}>{line}</Text>
            ))}
            <Text style={styles.translateFootnote}>
              Per-plant timing lives in each plant’s “Ask the Gnome” advice.
            </Text>
          </Card.Content>
        </Card>
      )}
    </ScrollView>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  scroll: { flex: 1, backgroundColor: p.bg },
  content: { padding: 12, paddingBottom: 48 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { borderRadius: 12, padding: 16, marginBottom: 12, backgroundColor: p.card },
  envName: { color: p.acc, fontFamily: f.display },
  subtle: { color: p.sub, marginTop: 2 },
  card: { marginBottom: 12, borderRadius: 12, backgroundColor: p.card },
  cardTitle: { color: p.ink, fontFamily: f.display },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { backgroundColor: p.accSoft },
  unavailable: { color: p.sub, fontStyle: 'italic', lineHeight: 20 },
  measureRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 20, marginTop: 14 },
  measure: {},
  measureValue: { fontSize: 17, fontWeight: '700', color: p.ink, fontFamily: f.numeric },
  measureLabel: { fontSize: 11.5, color: p.faint, marginTop: 2 },
  unmeasured: { color: p.sub, fontStyle: 'italic', lineHeight: 19, marginTop: 12, fontSize: 13 },
  goalsLabel: { marginTop: 16, marginBottom: 8 },

  misfit: { marginBottom: 16 },
  misfitName: { fontSize: 15, fontWeight: '700', color: p.ink, marginBottom: 5 },
  misfitSpecies: { fontSize: 13, fontWeight: '400', color: p.faint },
  misfitReason: { fontSize: 14, lineHeight: 20, color: p.sub, marginBottom: 3 },
  candidate: { marginBottom: 16 },
  candidateName: { fontSize: 15, fontWeight: '700', color: p.ink },
  candidateLatin: { fontSize: 12.5, fontStyle: 'italic', color: p.faint, marginBottom: 5 },
  candidateWhy: { fontSize: 14, lineHeight: 20, color: p.sub, marginBottom: 3 },
  caveat: { fontSize: 13, lineHeight: 19, color: p.warn, marginBottom: 12 },

  nowRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  nowMain: {},
  nowTemp: { fontSize: 34, fontWeight: '700', color: p.ink, fontFamily: f.numeric },
  nowCond: { color: p.sub, marginTop: 2 },
  nowStats: { alignItems: 'flex-end', gap: 4 },
  nowStat: { color: p.sub, fontSize: 13 },

  divider: { marginVertical: 12 },
  foreRow: { gap: 14, paddingVertical: 2 },
  foreDay: { alignItems: 'center', minWidth: 52 },
  foreDow: { fontSize: 12, color: p.faint, marginBottom: 4, fontWeight: '600' },
  foreTemp: { fontSize: 16, fontWeight: '700', color: p.ink, fontFamily: f.numeric },
  foreLow: { fontSize: 13, color: p.faint, fontFamily: f.numeric },
  foreMeta: { fontSize: 11, color: p.sub, marginTop: 3 },

  attribution: { marginTop: 14 },
  saveLocationBtn: { marginTop: 12, borderRadius: 8 },

  // Notebook "outside → in here" card
  specimenCard: { marginBottom: 12, borderRadius: 12, backgroundColor: p.desk },
  specimenHeader: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderStyle: 'dashed',
    borderBottomColor: p.line,
  },
  specimenLabel: {
    fontSize: 11,
    letterSpacing: 1.5,
    color: p.warn,
    fontWeight: '600',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  specimenSub: { fontSize: 13, lineHeight: 19, color: p.sub, marginTop: 6 },
  specimenBody: { paddingTop: 14, gap: 8 },
  translateLine: { lineHeight: 21, color: p.ink, fontSize: 14.5 },
  translateFootnote: { marginTop: 6, fontSize: 12, fontStyle: 'italic', color: p.sub },
});
