import React, { useCallback, useMemo, useState } from 'react';
import {
  Pressable, RefreshControl, ScrollView, StyleSheet, View,
} from 'react-native';
import { ActivityIndicator, Button, Card, Text } from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RootStackParamList, ScreenName } from '../navigation/types';
import {
  SITE_QUERY_KEYS, fetchSiteProfile, fetchVitalsOrOff,
} from '../api/properties';
import { fetchGrowingAreas, fetchGrowingAreaWeather } from '../api/growingAreas';
import { useCareTasks } from '../care/useCareTasks';
import { unreadLine, unscheduledLine } from '../care/schedule';
import { VitalCard, VitalSpace } from '../types/site';
import { homeForm, offersAddLand, usesLegacyRoutes } from '../home/form';
import { mergeThisWeek, moreCareLine, weekCounts, WeekItem } from '../home/week';
import { pickHeadline, HeadlineDay } from '../home/headline';
import { legacyWeatherCards, weatherCards, seasonCard } from '../home/weather';
import { landLines } from '../home/land';
import { orderSpaces, spaceLine, spacesFromAreas } from '../home/spaces';
import { EVENT_STATUS_WORDS, profileProgressLine, seasonAhead } from '../home/season';
import ExplainedBlock from '../components/ExplainedBlock';
import ConfidenceChip from '../components/ConfidenceChip';
import Eyebrow from '../components/Eyebrow';
import LoadError from '../components/LoadError';
import RefreshFailed from '../components/RefreshFailed';
import WeatherCredit from '../components/WeatherCredit';
import { WHY_LABEL, disclosureLines } from '../components/explainedText';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';

type Nav = NativeStackNavigationProp<RootStackParamList, 'Home'>;

// Home: the vitals report the app opens on (build spec section 6). Top to
// bottom: a headline about today, weather vitals, "This week" (seasonal tasks
// merged with plant care that is due), "The season ahead", "Your land",
// "Your growing spaces", and quiet links to the rest of the app.
//
// Three forms (home/form.ts): with land; with no property (weather, care and
// spaces, and one calm "Add your land" card); and for a server with the new
// routes off, the same no-property report built from the routes the app used
// before, with the card hidden.

const SCREENS_NEEDING_PROPERTY = new Set<ScreenName>(['Land', 'Season', 'ZoneMap']);

export default function HomeScreen() {
  const navigation = useNavigation<Nav>();
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const [pulling, setPulling] = useState(false);

  const vitalsQ = useQuery({ queryKey: SITE_QUERY_KEYS.vitals, queryFn: () => fetchVitalsOrOff() });
  const vitals = vitalsQ.data;
  const form = homeForm({ vitals, failed: vitalsQ.isError });
  const legacy = usesLegacyRoutes(form);
  const property = vitals?.property ?? null;

  const care = useCareTasks();

  const profileQ = useQuery({
    queryKey: SITE_QUERY_KEYS.siteProfile(property?.id ?? -1),
    queryFn: () => fetchSiteProfile(property!.id),
    enabled: property != null,
  });

  // The routes the app used before, for a server with the new ones off.
  const areasQ = useQuery({
    queryKey: ['growingAreas'],
    queryFn: fetchGrowingAreas,
    enabled: legacy,
  });
  const weatherArea = legacy
    ? (areasQ.data ?? []).find((a) => a.lat != null && a.lng != null) ?? null
    : null;
  const weatherQ = useQuery({
    queryKey: ['growingAreaWeather', weatherArea?.id ?? -1],
    queryFn: () => fetchGrowingAreaWeather(weatherArea!.id),
    enabled: weatherArea != null,
    staleTime: 30 * 60 * 1000, // weather is cached hourly server-side
  });
  const legacyWeather = weatherQ.data?.available ? weatherQ.data.weather : null;

  const week = useMemo(
    () => mergeThisWeek(vitals?.this_week ?? [], care.tasks),
    [vitals, care.tasks],
  );
  const counts = weekCounts(week);

  const cards: VitalCard[] = useMemo(() => {
    if (legacy) return legacyWeather && weatherArea ? legacyWeatherCards(legacyWeather, weatherArea.name) : [];
    return weatherCards(vitals?.cards ?? []);
  }, [legacy, legacyWeather, weatherArea, vitals]);

  const headlineDays: HeadlineDay[] = legacy
    ? (legacyWeather?.daily ?? []).map((d) => ({ date: d.date, low_f: d.low_f }))
    : (vitals?.forecast?.days ?? []);
  const headline = pickHeadline({
    serverHeadline: legacy ? null : vitals?.headline,
    days: headlineDays,
    careDue: counts.careDue,
    openSeasonTasks: counts.openSeason,
  });

  const spaces: VitalSpace[] = orderSpaces(
    legacy ? spacesFromAreas(areasQ.data ?? []) : (vitals?.spaces ?? []));
  const land = property ? landLines(profileQ.data, vitals?.cards ?? []) : [];
  const ahead = seasonAhead(vitals?.season_ahead ?? []);
  const season = seasonCard(vitals?.cards ?? []);
  const progress = profileProgressLine(profileQ.data?.status ?? property?.profile_status);

  const go = useCallback((screen: ScreenName, extra?: { eventKey?: string; field?: string }) => {
    if (SCREENS_NEEDING_PROPERTY.has(screen)) {
      if (!property) return;
      if (screen === 'Season') navigation.navigate('Season', { propertyId: property.id, eventKey: extra?.eventKey });
      else if (screen === 'Land') navigation.navigate('Land', { propertyId: property.id, field: extra?.field });
      else navigation.navigate('ZoneMap', { propertyId: property.id });
      return;
    }
    // Screens without required params. The cast is to the subset that has none.
    (navigation.navigate as (name: ScreenName) => void)(screen);
  }, [navigation, property]);

  const linkTarget = (link: string | null | undefined): ScreenName | null => {
    if (!link) return null;
    const known: ScreenName[] = ['Home', 'PropertySetup', 'Land', 'ZoneMap', 'Season', 'Spaces',
      'Plants', 'CaptureGarden', 'Species', 'Settings', 'Census', 'AddPlant'];
    return (known as string[]).includes(link) ? link as ScreenName : null;
  };

  const onRefresh = useCallback(async () => {
    setPulling(true);
    try {
      await Promise.all([
        vitalsQ.refetch(),
        care.refetch(),
        property ? profileQ.refetch() : null,
        legacy ? areasQ.refetch() : null,
        weatherArea ? weatherQ.refetch() : null,
      ]);
    } finally {
      setPulling(false);
    }
  }, [vitalsQ, care, profileQ, areasQ, weatherQ, property, legacy, weatherArea]);

  if (form === 'loading') {
    return <ActivityIndicator style={styles.center} size="large" />;
  }
  if (form === 'failed') {
    // Home is the only way into the rest of the app, so a report that will
    // not load must not strand the person: plants, species and settings
    // (where the sign-out and server settings live) stay one tap away.
    return (
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={vitalsQ.isRefetching} onRefresh={() => { void vitalsQ.refetch(); }} />}
      >
        <LoadError
          inline
          message="Couldn’t load today’s report."
          error={vitalsQ.error}
          onRetry={() => vitalsQ.refetch()}
          retrying={vitalsQ.isRefetching}
        />
        <View style={styles.links}>
          <Button mode="text" compact onPress={() => navigation.navigate('Plants')} textColor={palette.sub}>Plants</Button>
          <Button mode="text" compact onPress={() => navigation.navigate('Species')} textColor={palette.sub}>Species</Button>
          <Button mode="text" compact onPress={() => navigation.navigate('Settings')} textColor={palette.sub}>Settings</Button>
        </View>
      </ScrollView>
    );
  }

  const careNotes = [unscheduledLine(care.unscheduled), unreadLine(care.unreadCount),
    moreCareLine(week.moreCare)].filter((l): l is string => l != null);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={pulling} onRefresh={onRefresh} />}
    >
      {vitalsQ.isError && <RefreshFailed onRetry={() => vitalsQ.refetch()} retrying={vitalsQ.isRefetching} />}

      <Text style={styles.headline} accessibilityRole="header">{headline}</Text>
      {property ? <Text style={styles.place}>{placeLine(property)}</Text> : null}

      {/* ── Weather vitals ── */}
      {cards.length > 0 && (
        <View style={styles.section}>
          <Eyebrow style={styles.eyebrow}>Weather</Eyebrow>
          {cards.map((c) => (
            <VitalCardView key={c.key} card={c} styles={styles} onOpen={linkTarget(c.link)
              ? () => go(linkTarget(c.link)!) : undefined} />
          ))}
          {legacy
            ? <WeatherCredit attribution={legacyWeather?.attribution} />
            : vitals?.forecast
              ? <Text style={styles.quiet}>{`Forecast: ${vitals.forecast.provider_name}.`}</Text>
              : null}
        </View>
      )}
      {legacy && !weatherArea && areasQ.data && (
        <Text style={styles.quietBlock}>
          Give a growing space a location and its weather shows here.
        </Text>
      )}

      {/* ── This week ── */}
      <View style={styles.section}>
        <Eyebrow style={styles.eyebrow}>This week</Eyebrow>
        {care.isLoading && !care.loaded ? <ActivityIndicator style={styles.inlineSpin} /> : null}
        {care.isError && !care.loaded ? (
          <LoadError inline message="Couldn’t load your plants’ care." error={null}
            onRetry={() => care.refetch()} retrying={care.isRefetching} />
        ) : null}
        {week.items.length === 0 && care.loaded ? (
          <Text style={styles.quiet}>Nothing is due this week.</Text>
        ) : null}
        {week.items.map((item) => (
          <WeekRow
            key={item.key}
            item={item}
            styles={styles}
            onPress={() => {
              if (item.kind === 'care') navigation.navigate('PlantDetail', { plantId: item.plantId });
              else go('Season', { eventKey: item.eventKey ?? undefined });
            }}
          />
        ))}
        {careNotes.map((l) => <Text key={l} style={styles.quiet}>{l}</Text>)}
      </View>

      {/* ── The season ahead ── */}
      {property && (ahead.length > 0 || season) ? (
        <View style={styles.section}>
          <Eyebrow style={styles.eyebrow}>The season ahead</Eyebrow>
          {season ? <VitalCardView card={season} styles={styles} onOpen={() => go('Season')} /> : null}
          {ahead.map((e) => (
            <Pressable
              key={e.event_key}
              onPress={() => go('Season', { eventKey: e.event_key })}
              accessibilityRole="button"
              accessibilityLabel={`${e.title}. ${EVENT_STATUS_WORDS[e.status]} ${e.window.text}. Opens the seasonal plan.`}
              style={styles.row}
            >
              <View style={styles.rowText}>
                <Text style={styles.rowTitle}>{e.title}</Text>
                <Text style={styles.rowDetail}>{`${EVENT_STATUS_WORDS[e.status]}: ${e.window.text}`}</Text>
              </View>
              <ConfidenceChip confidence={e.explained.confidence} label={e.explained.confidence_label} />
            </Pressable>
          ))}
          <Button mode="text" compact onPress={() => go('Season')} textColor={palette.acc} style={styles.more}>
            The whole season
          </Button>
        </View>
      ) : null}

      {/* ── Your land ── */}
      {property ? (
        <View style={styles.section}>
          <Eyebrow style={styles.eyebrow}>Your land</Eyebrow>
          {progress ? <Text style={styles.quiet}>{progress}</Text> : null}
          {profileQ.isError && !profileQ.data && land.length === 0 ? (
            <LoadError inline message="Couldn’t load what is known about your land." error={profileQ.error}
              onRetry={() => profileQ.refetch()} retrying={profileQ.isRefetching} />
          ) : null}
          {land.map((l) => (
            <ExplainedBlock
              key={l.key}
              title={l.title}
              explained={l.explained}
              onPress={() => go('Land', { field: l.field })}
            />
          ))}
          <Button mode="text" compact onPress={() => go('Land')} textColor={palette.acc} style={styles.more}>
            Everything about your land
          </Button>
        </View>
      ) : null}

      {offersAddLand(form, vitals) ? (
        <Card style={styles.addLand} mode="contained">
          <Card.Content>
            <Text style={styles.addLandTitle}>Have a yard or garden beds?</Text>
            <Text style={styles.addLandBody}>
              Add your land and PlantAdvocate reads its soil, sun and typical frost dates
              from public maps, then plans the season with you. Pots on a balcony or a
              windowsill need nothing more.
            </Text>
            <Button
              mode="outlined"
              onPress={() => navigation.navigate('PropertySetup')}
              textColor={palette.acc}
              style={styles.addLandBtn}
              accessibilityLabel="Add your land"
            >
              Add your land
            </Button>
          </Card.Content>
        </Card>
      ) : null}

      {/* ── Your growing spaces ── */}
      <View style={styles.section}>
        <Eyebrow style={styles.eyebrow}>Your growing spaces</Eyebrow>
        {legacy && areasQ.isError && !areasQ.data ? (
          <LoadError inline message="Couldn’t load your growing spaces." error={areasQ.error}
            onRetry={() => areasQ.refetch()} retrying={areasQ.isRefetching} />
        ) : null}
        {spaces.map((s) => (
          <Pressable
            key={s.growing_area_id}
            onPress={() => navigation.navigate('SpaceDetail', { growingAreaId: s.growing_area_id, name: s.name })}
            accessibilityRole="button"
            accessibilityLabel={`${s.name}. ${spaceLine(s)}.`}
            style={styles.row}
          >
            <View style={styles.rowText}>
              <Text style={styles.rowTitle}>{s.name}</Text>
              <Text style={styles.rowDetail}>{spaceLine(s)}</Text>
            </View>
            <Text style={styles.chevron}>›</Text>
          </Pressable>
        ))}
        <Button mode="text" compact onPress={() => navigation.navigate('Spaces')} textColor={palette.acc} style={styles.more}>
          {spaces.length === 0 ? 'Add a growing space' : 'All growing spaces'}
        </Button>
      </View>

      {(vitals?.notes ?? []).map((n) => <Text key={n} style={styles.quietBlock}>{n}</Text>)}

      {/* ── Quiet links ── */}
      <View style={styles.links}>
        <Button mode="text" compact onPress={() => navigation.navigate('Plants')} textColor={palette.sub}>Plants</Button>
        <Button mode="text" compact onPress={() => navigation.navigate('Species')} textColor={palette.sub}>Species</Button>
        <Button mode="text" compact onPress={() => navigation.navigate('Settings')} textColor={palette.sub}>Settings</Button>
      </View>
    </ScrollView>
  );
}

function placeLine(p: { name: string; city?: string | null; region?: string | null }): string {
  const where = [p.city, p.region].filter(Boolean).join(', ');
  return where && where !== p.name ? `${p.name}, ${where}` : p.name;
}

type Styles = ReturnType<typeof makeStyles>;

function VitalCardView({ card, styles, onOpen }: {
  card: VitalCard; styles: Styles; onOpen?: () => void;
}) {
  const toneStyle = card.tone === 'act' ? styles.toneAct : card.tone === 'watch' ? styles.toneWatch : null;
  if (card.explained) {
    return (
      <View style={[styles.vital, toneStyle]}>
        <ExplainedBlock
          title={card.title}
          explained={{ ...card.explained, display: card.value_text }}
          onPress={onOpen}
        >
          {card.detail ? <Text style={styles.rowDetail}>{card.detail}</Text> : null}
        </ExplainedBlock>
      </View>
    );
  }
  const body = (
    <>
      <Text style={styles.vitalTitle}>{card.title}</Text>
      <Text style={styles.vitalValue}>{card.value_text}</Text>
      {card.detail ? <Text style={styles.rowDetail}>{card.detail}</Text> : null}
    </>
  );
  return onOpen ? (
    <Pressable onPress={onOpen} accessibilityRole="button"
      accessibilityLabel={`${card.title}. ${card.value_text}. ${card.detail}`}
      style={[styles.vital, toneStyle]}>
      {body}
    </Pressable>
  ) : (
    <View accessible accessibilityLabel={`${card.title}. ${card.value_text}. ${card.detail}`}
      style={[styles.vital, toneStyle]}>
      {body}
    </View>
  );
}

function WeekRow({ item, styles, onPress }: {
  item: WeekItem; styles: Styles; onPress: () => void;
}) {
  const [open, setOpen] = useState(false);
  if (item.kind === 'care') {
    return (
      <Pressable onPress={onPress} accessibilityRole="button"
        accessibilityLabel={`${item.text}. ${item.detail}. Opens the plant.`} style={styles.row}>
        <View style={styles.rowText}>
          <Text style={styles.rowTitle}>{item.text}</Text>
          <Text style={[styles.rowDetail, item.overdue && styles.overdue]}>{item.detail}</Text>
        </View>
        <Text style={styles.chevron}>›</Text>
      </Pressable>
    );
  }
  const settled = item.state !== 'open';
  const lines = disclosureLines(item);
  return (
    <View style={styles.taskWrap}>
      <Pressable onPress={onPress} accessibilityRole="button"
        accessibilityLabel={`${item.text}.${settled ? ' Done.' : ''} Opens the seasonal plan.`} style={styles.row}>
        <View style={styles.rowText}>
          <Text style={[styles.rowTitle, settled && styles.settled]}>
            {settled ? `✓ ${item.text}` : item.text}
          </Text>
          {item.lowImpactNote ? <Text style={styles.rowDetail}>{item.lowImpactNote}</Text> : null}
        </View>
        <Text style={styles.chevron}>›</Text>
      </Pressable>
      <Pressable onPress={() => setOpen((o) => !o)} accessibilityRole="button"
        accessibilityState={{ expanded: open }}
        accessibilityLabel={`${WHY_LABEL}. ${open ? 'Hide' : 'Show'}.`} hitSlop={8}>
        <Text style={styles.why}>{`${open ? '▾' : '▸'} ${WHY_LABEL}`}</Text>
      </Pressable>
      {open && (
        <View style={styles.whyBody}>
          <Text style={styles.rowDetail}>{lines.reason}</Text>
          {lines.sources.map((s) => <Text key={s} style={styles.quiet}>{`Data: ${s}`}</Text>)}
        </View>
      )}
    </View>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  container: { flex: 1, backgroundColor: p.bg },
  content: { padding: 16, paddingBottom: 48 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  headline: { color: p.acc, fontFamily: f.display, fontSize: 22, fontWeight: '700', lineHeight: 29 },
  place: { color: p.sub, marginTop: 4 },
  section: {
    marginTop: 18, backgroundColor: p.card, borderRadius: 14, padding: 14,
    borderWidth: 1, borderColor: p.line2,
  },
  eyebrow: { marginBottom: 8 },
  vital: { paddingVertical: 6, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: p.line2 },
  toneAct: { borderLeftWidth: 3, borderLeftColor: p.warn, paddingLeft: 8 },
  toneWatch: { borderLeftWidth: 3, borderLeftColor: p.hedge, paddingLeft: 8 },
  vitalTitle: { color: p.faint, fontFamily: f.label, fontSize: 12 },
  vitalValue: { color: p.ink, fontSize: 17, fontWeight: '600', fontFamily: f.numeric, marginVertical: 1 },
  row: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, gap: 8, minHeight: 44 },
  rowText: { flex: 1 },
  rowTitle: { color: p.ink, fontSize: 15, lineHeight: 21 },
  rowDetail: { color: p.sub, fontSize: 13, lineHeight: 19 },
  overdue: { color: p.warn },
  settled: { color: p.sub },
  chevron: { color: p.faint, fontSize: 20 },
  taskWrap: { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: p.line2, paddingBottom: 6 },
  why: { color: p.acc, fontSize: 13, fontWeight: '600' },
  whyBody: { marginTop: 4, paddingLeft: 10, borderLeftWidth: 2, borderLeftColor: p.line, gap: 3 },
  quiet: { color: p.faint, fontSize: 12.5, lineHeight: 18, marginTop: 6 },
  quietBlock: { color: p.faint, fontSize: 13, lineHeight: 19, marginTop: 14, paddingHorizontal: 4 },
  more: { alignSelf: 'flex-start', marginTop: 4 },
  inlineSpin: { marginVertical: 8 },
  addLand: { marginTop: 18, borderRadius: 14, backgroundColor: p.accSoft },
  addLandTitle: { color: p.acc, fontFamily: f.display, fontSize: 17, fontWeight: '700', marginBottom: 6 },
  addLandBody: { color: p.sub, lineHeight: 20 },
  addLandBtn: { alignSelf: 'flex-start', marginTop: 12, borderRadius: 8 },
  links: { flexDirection: 'row', justifyContent: 'center', marginTop: 24, gap: 8 },
});
