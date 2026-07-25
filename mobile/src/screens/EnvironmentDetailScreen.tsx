import React, { useMemo } from 'react';
import {
  ScrollView, View, StyleSheet, Linking, Platform, Pressable,
} from 'react-native';
import {
  Text, Card, Chip, ActivityIndicator, Surface, Divider,
} from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { RouteProp, useRoute } from '@react-navigation/native';
import {
  fetchEnvironment, fetchEnvironmentWeather,
} from '../api/environments';
import { WeatherDay } from '../types';
import {
  conditionText, weekday, exposureSummary, translateWeather,
} from '../weather/translate';
import { EnvironmentsStackParamList } from '../../App';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';

type Route = RouteProp<EnvironmentsStackParamList, 'EnvironmentDetail'>;

const ENV_TYPE_LABEL: Record<string, string> = {
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

export default function EnvironmentDetailScreen() {
  const route = useRoute<Route>();
  const { environmentId } = route.params;
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);

  const { data: env, isLoading } = useQuery({
    queryKey: ['environment', environmentId],
    queryFn: () => fetchEnvironment(environmentId),
  });

  const { data: weatherResp, isLoading: weatherLoading } = useQuery({
    queryKey: ['environmentWeather', environmentId],
    queryFn: () => fetchEnvironmentWeather(environmentId),
    staleTime: 30 * 60 * 1000, // weather is cached hourly server-side
  });

  if (isLoading || !env) {
    return <ActivityIndicator style={styles.center} size="large" />;
  }

  const weather = weatherResp?.available ? weatherResp.weather : null;
  const cur = weather?.current;
  const location = [env.city, env.region].filter(Boolean).join(', ');

  return (
    <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
      {/* Header */}
      <Surface style={styles.header} elevation={1}>
        <Text variant="headlineSmall" style={styles.envName}>
          {env.name}
        </Text>
        <Text variant="bodyMedium" style={styles.subtle}>
          {ENV_TYPE_LABEL[env.type] ?? env.type}
        </Text>
        {location ? <Text variant="bodySmall" style={styles.subtle}>📍 {location}</Text> : null}
      </Surface>

      {/* Climate characteristics */}
      <Card style={styles.card}>
        <Card.Title title="Climate" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          <View style={styles.chipRow}>
            <Chip compact style={styles.chip}>{SHELTER_LABEL[env.shelter] ?? env.shelter}</Chip>
            <Chip compact style={styles.chip}>{TEMP_LABEL[env.temp_exposure] ?? env.temp_exposure}</Chip>
            <Chip compact style={styles.chip}>{SUN_LABEL[env.sun_exposure] ?? env.sun_exposure}</Chip>
          </View>
        </Card.Content>
      </Card>

      {/* Weather strip */}
      <Card style={styles.card}>
        <Card.Title title="Local weather" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          {weatherLoading ? (
            <ActivityIndicator style={{ marginVertical: 16 }} />
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
              <Pressable
                onPress={() => weather.attribution?.url && Linking.openURL(weather.attribution.url)}
                style={styles.attribution}
              >
                <Text style={styles.attributionText}>
                  {(weather.attribution?.text ?? ' Weather').trim() || 'Weather'} ›
                </Text>
              </Pressable>
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

  attribution: { marginTop: 14, alignSelf: 'flex-start' },
  attributionText: { fontSize: 12, color: p.faint },

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
