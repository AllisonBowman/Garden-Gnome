import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Pressable, RefreshControl, ScrollView, StyleSheet, View,
} from 'react-native';
import { ActivityIndicator, Button, Text } from 'react-native-paper';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation/types';
import {
  SITE_QUERY_KEYS, fetchSiteProfile, fetchVitalsOrOff, fetchZones, putSeasonEvent, refreshHome,
} from '../api/properties';
import { fetchGrowingAreas, fetchGrowingAreaWeather } from '../api/growingAreas';
import { logCare } from '../api/plants';
import { CARE_TASKS_QUERY_KEY, useCareTasks } from '../care/useCareTasks';
import { unreadLine, unscheduledLine } from '../care/schedule';
import { rescheduleAllReminders } from '../notifications/reminders';
import { homeForm, offersAddLand, usesLegacyRoutes } from '../home/form';
import { mergeThisWeek, moreCareLine, weekCounts, WeekItem } from '../home/week';
import { pickHeadline, HeadlineDay } from '../home/headline';
import { legacyWeatherCards, seasonCard, weatherCards } from '../home/weather';
import { profileProgressLine, seasonAhead } from '../home/season';
import { almanacDate, oneThing, seasonWeekLine } from '../home/almanac';
import { landGlance } from '../home/glance';
import { pickHomeTasks, taskAnswer, taskButtons } from '../home/homeTasks';
import { loadSkips, saveSkips } from '../home/homeSkips';
import { homeSections } from '../howWeKnow/sections';
import { valueFor } from '../land/readingTiles';
import { drawnZones } from '../land/profileRows';
import ControlsRow from '../components/ControlsRow';
import EstTag from '../components/EstTag';
import Eyebrow from '../components/Eyebrow';
import HowWeKnowButton from '../components/HowWeKnowButton';
import LoadError from '../components/LoadError';
import RefreshFailed from '../components/RefreshFailed';
import WeatherCredit from '../components/WeatherCredit';
import { APPLE_WEATHER_LEGAL, isAppleForecast } from '../weather/appleCredit';
import { formatServerTime } from '../home/serverTime';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import { getTempUnit } from '../units/temperature';
import { t } from '../i18n';

type Nav = NativeStackNavigationProp<RootStackParamList, 'Home'>;

// Home: "This week on your land", an almanac page for the week. Top to
// bottom (Controls first redesign, Nov 2026):
//
//   1. The almanac line: the date, the week of the season, and the one
//      thing that matters.
//   2. Up to three tasks for this week, each with Done and Skip.
//   3. The Controls row: frost alerts, your land, zones, fix a value,
//      °F or °C, task reminders. Settings is in the header, in words.
//   4. Your land at a glance: sun, water and soil, one word each, with
//      "est." where it is an estimate and "Not right? Fix it" on each.
//   5. How we know: one sheet with every source, method, confidence label
//      and note this screen used to show on its face.
//
// Then quiet text links to the rest of the app (Home has no tab bar, so it
// must stay the way in): the season and its forecast chart, the land and
// its map, growing spaces, plants and species.
//
// Three forms (home/form.ts): with land; with no property (the same almanac
// and tasks, and "Add your land"); and for a server with the new routes
// off, the same report built from the routes the app used before.

export default function HomeScreen() {
  const navigation = useNavigation<Nav>();
  const queryClient = useQueryClient();
  const { palette, fonts, display } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts, display.boldText), [palette, fonts, display.boldText]);
  const [pulling, setPulling] = useState(false);
  const [skipped, setSkipped] = useState<Set<string>>(new Set());
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [saveFailed, setSaveFailed] = useState(false);

  useEffect(() => { void loadSkips().then(setSkipped); }, []);

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
  const zonesQ = useQuery({
    queryKey: SITE_QUERY_KEYS.zones(property?.id ?? -1),
    queryFn: () => fetchZones(property!.id),
    enabled: property != null,
  });

  // The routes the app used before, for a server with the new ones off.
  const areasQ = useQuery({ queryKey: ['growingAreas'], queryFn: fetchGrowingAreas, enabled: legacy });
  const weatherArea = legacy
    ? (areasQ.data ?? []).find((a) => a.lat != null && a.lng != null) ?? null
    : null;
  const weatherQ = useQuery({
    queryKey: ['growingAreaWeather', weatherArea?.id ?? -1],
    queryFn: () => fetchGrowingAreaWeather(weatherArea!.id),
    enabled: weatherArea != null,
    staleTime: 30 * 60 * 1000,
  });
  const legacyWeather = weatherQ.data?.available ? weatherQ.data.weather : null;

  const week = useMemo(() => mergeThisWeek(vitals?.this_week ?? [], care.tasks), [vitals, care.tasks]);
  const counts = weekCounts(week);
  const tasks = pickHomeTasks(week.items, skipped);

  const headlineDays: HeadlineDay[] = legacy
    ? (legacyWeather?.daily ?? []).map((d) => ({ date: d.date, low_f: d.low_f }))
    : (vitals?.forecast?.days ?? []);
  const localHeadline = pickHeadline({
    serverHeadline: null, days: headlineDays, careDue: counts.careDue, openSeasonTasks: counts.openSeason,
  });
  const verdict = oneThing(legacy ? null : vitals?.headline, localHeadline, getTempUnit() === 'C');
  const today = new Date();
  const forecastWhen = vitals?.forecast?.fetched_at ? formatServerTime(vitals.forecast.fetched_at) : null;

  const glance = landGlance(profileQ.data);
  const progress = profileProgressLine(profileQ.data?.status ?? property?.profile_status);
  const zoneCount = profileQ.data ? drawnZones(profileQ.data).length : (zonesQ.data?.length ?? null);

  const answer = useMutation({
    mutationFn: async ({ item, button }: { item: WeekItem; button: 'done' | 'skip' }) => {
      const actions = item.kind === 'season'
        ? (vitals?.season_ahead ?? []).find((e) => e.event_key === item.eventKey)?.owner_actions ?? null
        : null;
      const a = taskAnswer(item, button, actions);
      if (a.kind === 'season') {
        if (!property || item.kind !== 'season' || !item.eventKey) return;
        await putSeasonEvent(property.id, item.eventKey, { state: a.state });
      } else if (a.kind === 'log' && item.kind === 'care') {
        await logCare(item.plantId, item.careType, '', a.outcome);
      } else {
        const next = new Set(skipped).add(item.key);
        setSkipped(next);
        await saveSkips(next);
      }
    },
    onMutate: ({ item }) => { setBusyKey(item.key); setSaveFailed(false); },
    onSuccess: async () => {
      await Promise.all([
        refreshHome(queryClient),
        queryClient.invalidateQueries({ queryKey: CARE_TASKS_QUERY_KEY }),
      ]);
      void rescheduleAllReminders();
    },
    onError: () => setSaveFailed(true),
    onSettled: () => setBusyKey(null),
  });

  const openItem = useCallback((item: WeekItem) => {
    if (item.kind === 'care') navigation.navigate('PlantDetail', { plantId: item.plantId });
    else if (property) navigation.navigate('Season', { propertyId: property.id, eventKey: item.eventKey ?? undefined });
  }, [navigation, property]);

  const sheet = () => homeSections({
    vitals,
    headline: verdict,
    weatherCards: legacy
      ? (legacyWeather && weatherArea ? legacyWeatherCards(legacyWeather, weatherArea.name) : [])
      : weatherCards(vitals?.cards ?? []),
    land: glance.flatMap((g) => {
      const v = profileQ.data ? valueFor(profileQ.data, g.field) : undefined;
      return v ? [{ title: v.title || g.title, explained: v }] : [];
    }),
    progress,
    week: week.items,
    seasonAhead: seasonAhead(vitals?.season_ahead ?? []),
    seasonCard: seasonCard(vitals?.cards ?? []),
    legacyCredit: legacy && legacyWeather?.attribution ? legacyWeather.attribution.text ?? null : null,
    forecastWhen,
  });

  const onRefresh = useCallback(async () => {
    setPulling(true);
    try {
      await Promise.all([
        vitalsQ.refetch(), care.refetch(),
        property ? profileQ.refetch() : null,
        property ? zonesQ.refetch() : null,
        legacy ? areasQ.refetch() : null,
        weatherArea ? weatherQ.refetch() : null,
      ]);
    } finally { setPulling(false); }
  }, [vitalsQ, care, profileQ, zonesQ, areasQ, weatherQ, property, legacy, weatherArea]);

  const links = (
    <View style={styles.links}>
      <Eyebrow style={styles.eyebrow}>{t('home.almanac.more')}</Eyebrow>
      {property ? (
        <>
          <TextLink label={t('home.almanac.season')} styles={styles}
            onPress={() => navigation.navigate('Season', { propertyId: property.id })} />
          <TextLink label={t('home.almanac.landMap')} styles={styles}
            onPress={() => navigation.navigate('Land', { propertyId: property.id })} />
        </>
      ) : null}
      <TextLink label={t('home.almanac.spaces')} styles={styles} onPress={() => navigation.navigate('Spaces')} />
      <TextLink label={t('home.screen.plants')} styles={styles} onPress={() => navigation.navigate('Plants')} />
      <TextLink label={t('home.screen.species')} styles={styles} onPress={() => navigation.navigate('Species')} />
      <TextLink label={t('home.screen.settings')} styles={styles} onPress={() => navigation.navigate('Settings')} />
    </View>
  );

  if (form === 'loading') return <ActivityIndicator style={styles.center} size="large" />;
  if (form === 'failed') {
    // Home is the only way into the rest of the app, so a report that will
    // not load must not strand the person.
    return (
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={vitalsQ.isRefetching} onRefresh={() => { void vitalsQ.refetch(); }} />}
      >
        <LoadError inline message={t('home.screen.loadFailed')} error={vitalsQ.error}
          onRetry={() => vitalsQ.refetch()} retrying={vitalsQ.isRefetching} />
        {links}
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

      {/* ── 1. The almanac line ── */}
      <View style={styles.almanac}>
        <Text style={styles.almanacTitle} accessibilityRole="header">
          {property ? t('home.almanac.title') : t('home.almanac.titleNoLand')}
        </Text>
        <View accessible accessibilityLabel={`${almanacDate(today)}. ${seasonWeekLine(today)}.`}>
          <Text style={styles.date} maxFontSizeMultiplier={2}>{almanacDate(today)}</Text>
          <Text style={styles.weekLine}>{seasonWeekLine(today)}</Text>
        </View>
        <Text style={styles.verdict} accessibilityRole="text" maxFontSizeMultiplier={2.2}>{verdict.line}</Text>
        {/* A date stamp is trust, not justification: it stays on the face. */}
        {forecastWhen ? <Text style={styles.quietTight}>{t('home.almanac.asOf', { when: forecastWhen })}</Text> : null}
        {/* The Apple Weather credit is a licence term wherever its data is
            shown, the line above included, so it never moves behind a tap. */}
        {legacy
          ? <WeatherCredit attribution={legacyWeather?.attribution} />
          : vitals?.forecast && isAppleForecast(vitals.forecast)
            ? <WeatherCredit attribution={{ text: vitals.forecast.provider_name, url: APPLE_WEATHER_LEGAL }} />
            : null}
      </View>

      {/* ── 2. Up to three tasks ── */}
      <View style={styles.section}>
        <Eyebrow style={styles.eyebrow}>{t('home.almanac.tasks')}</Eyebrow>
        {care.isLoading && !care.loaded ? <ActivityIndicator style={styles.inlineSpin} /> : null}
        {care.isError && !care.loaded ? (
          <LoadError inline message={t('home.screen.careFailed')} error={null}
            onRetry={() => care.refetch()} retrying={care.isRefetching} />
        ) : null}
        {tasks.shown.length === 0 && care.loaded ? <Text style={styles.body}>{t('home.almanac.noTasks')}</Text> : null}
        {tasks.shown.map((item) => (
          <TaskRow
            key={item.key}
            item={item}
            styles={styles}
            busy={busyKey === item.key}
            canAnswer
            onOpen={() => openItem(item)}
            onAnswer={(button) => answer.mutate({ item, button })}
          />
        ))}
        {saveFailed ? <Text style={styles.error} accessibilityLiveRegion="polite">{t('home.almanac.saveFailed')}</Text> : null}
        {tasks.more > 0 ? <Text style={styles.quiet}>{t('home.almanac.moreTasks', { count: tasks.more })}</Text> : null}
        {careNotes.map((l) => <Text key={l} style={styles.quiet}>{l}</Text>)}
      </View>

      {/* ── 3. Controls ── */}
      <View style={styles.controls}>
        <Eyebrow style={styles.eyebrow}>{t('controls.title')}</Eyebrow>
        <ControlsRow
          property={property ? { id: property.id, name: property.name } : null}
          zoneCount={zoneCount}
          canAddLand={offersAddLand(form, vitals)}
        />
      </View>

      {/* ── 4. Land at a glance ── */}
      {property ? (
        <View style={styles.section}>
          <Eyebrow style={styles.eyebrow}>{t('home.almanac.glance')}</Eyebrow>
          {profileQ.isLoading ? <ActivityIndicator style={styles.inlineSpin} /> : null}
          {profileQ.isError && !profileQ.data ? (
            <LoadError inline message={t('home.screen.landFailed')} error={profileQ.error}
              onRetry={() => profileQ.refetch()} retrying={profileQ.isRefetching} />
          ) : null}
          {glance.map((g) => (
            <View key={g.key} style={styles.glanceRow}>
              <Pressable
                onPress={() => navigation.navigate('Land', { propertyId: property.id, field: g.field })}
                accessibilityRole="button"
                accessibilityLabel={g.a11y}
                accessibilityHint={t('home.almanac.glanceHint')}
                style={styles.glanceMain}
              >
                <Text style={styles.glanceTitle}>{g.title}</Text>
                <View style={styles.glanceValue}>
                  <Text style={styles.glanceWord} maxFontSizeMultiplier={2.5}>{g.word}</Text>
                  {g.estimated || g.checking ? <EstTag checking={g.checking} /> : null}
                </View>
              </Pressable>
              {!g.checking ? (
                <Pressable
                  onPress={() => navigation.navigate('Land', { propertyId: property.id, field: g.field })}
                  accessibilityRole="button"
                  accessibilityLabel={t('home.almanac.fixItA11y', { title: g.title })}
                  style={styles.fixIt}
                  hitSlop={6}
                >
                  <Text style={styles.fixItText}>{t('home.almanac.fixIt')}</Text>
                </Pressable>
              ) : null}
            </View>
          ))}
        </View>
      ) : offersAddLand(form, vitals) ? (
        <View style={styles.section}>
          <Eyebrow style={styles.eyebrow}>{t('home.almanac.glance')}</Eyebrow>
          <Text style={styles.body}>{t('home.almanac.addLandGlance')}</Text>
          <Button mode="contained" onPress={() => navigation.navigate('PropertySetup')}
            buttonColor={palette.btn} textColor={palette.btnInk} style={styles.addLandBtn}
            contentStyle={styles.addLandContent} accessibilityLabel={t('home.screen.addLand')}>
            {t('home.screen.addLand')}
          </Button>
        </View>
      ) : null}

      {/* ── 5. How we know ── */}
      <HowWeKnowButton sections={sheet} />

      {links}
    </ScrollView>
  );
}

type Styles = ReturnType<typeof makeStyles>;

function TextLink({ label, onPress, styles }: { label: string; onPress: () => void; styles: Styles }) {
  return (
    <Pressable onPress={onPress} accessibilityRole="link" accessibilityLabel={label} style={styles.link}>
      <Text style={styles.linkText}>{`${label} ›`}</Text>
    </Pressable>
  );
}

function TaskRow({ item, styles, busy, canAnswer, onOpen, onAnswer }: {
  item: WeekItem; styles: Styles; busy: boolean; canAnswer: boolean;
  onOpen: () => void; onAnswer: (b: 'done' | 'skip') => void;
}) {
  const b = taskButtons(item);
  const detail = item.kind === 'care' ? item.detail : item.lowImpactNote;
  return (
    <View style={styles.task}>
      <Pressable onPress={onOpen} accessibilityRole="button"
        accessibilityLabel={t('home.almanac.openA11y', { text: [item.text, detail].filter(Boolean).join('. ') })}
        style={styles.taskMain}>
        <Text style={styles.taskText}>{item.text}</Text>
        {detail ? (
          <Text style={[styles.quietTight, item.kind === 'care' && item.overdue && styles.overdue]}>{detail}</Text>
        ) : null}
      </Pressable>
      {canAnswer ? (
        <View style={styles.taskButtons}>
          {busy ? <ActivityIndicator size={20} /> : (
            <>
              <Pressable onPress={() => onAnswer('done')} accessibilityRole="button" accessibilityLabel={b.doneA11y}
                style={[styles.taskBtn, styles.taskBtnDone]}>
                <Text style={styles.taskBtnDoneText}>{`✓ ${b.done}`}</Text>
              </Pressable>
              <Pressable onPress={() => onAnswer('skip')} accessibilityRole="button" accessibilityLabel={b.skipA11y}
                style={styles.taskBtn}>
                <Text style={styles.taskBtnText}>{b.skip}</Text>
              </Pressable>
            </>
          )}
        </View>
      ) : null}
    </View>
  );
}

const makeStyles = (p: Palette, f: Fonts, bold: boolean) => StyleSheet.create({
  container: { flex: 1, backgroundColor: p.bg },
  content: { padding: 16, paddingBottom: 48 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  almanac: {
    backgroundColor: p.card, borderRadius: 14, padding: 16, borderWidth: 1.5, borderColor: p.tileBorder,
  },
  almanacTitle: { color: p.ink, fontFamily: f.label, fontSize: 14, fontWeight: '700', letterSpacing: 0.5 },
  date: { color: p.ink, fontFamily: f.display, fontSize: 24, fontWeight: '700', lineHeight: 30, marginTop: 6 },
  weekLine: { color: p.sub, fontSize: 16, lineHeight: 22, fontWeight: bold ? '700' : '600' },
  verdict: { color: p.ink, fontFamily: f.display, fontSize: 21, fontWeight: '700', lineHeight: 28, marginTop: 10 },
  section: {
    marginTop: 16, backgroundColor: p.card, borderRadius: 14, padding: 14,
    borderWidth: 1, borderColor: p.tileBorder,
  },
  controls: { marginTop: 16 },
  eyebrow: { marginBottom: 8 },
  body: { color: p.ink, fontSize: 16, lineHeight: 22, fontWeight: bold ? '600' : undefined },
  quiet: { color: p.sub, fontSize: 14, lineHeight: 20, marginTop: 8, fontWeight: bold ? '600' : undefined },
  quietTight: { color: p.sub, fontSize: 14, lineHeight: 20, fontWeight: bold ? '600' : undefined },
  error: { color: p.warn, fontSize: 14, lineHeight: 20, marginTop: 8, fontWeight: '700' },
  overdue: { color: p.warn },
  inlineSpin: { marginVertical: 8 },
  task: { paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: p.line, gap: 8 },
  taskMain: { minHeight: 44, justifyContent: 'center' },
  taskText: { color: p.ink, fontSize: 17, lineHeight: 23, fontWeight: bold ? '700' : '600' },
  taskButtons: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  taskBtn: {
    minHeight: 44, minWidth: 88, paddingHorizontal: 16, borderRadius: 10, borderWidth: 2,
    borderColor: p.tileBorder, backgroundColor: p.tile, justifyContent: 'center', alignItems: 'center',
  },
  taskBtnDone: { backgroundColor: p.tileOn, borderColor: p.tileOn },
  taskBtnText: { color: p.tileInk, fontSize: 16, fontWeight: bold ? '800' : '700' },
  taskBtnDoneText: { color: p.tileOnInk, fontSize: 16, fontWeight: bold ? '800' : '700' },
  glanceRow: {
    flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between',
    paddingVertical: 6, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: p.line, gap: 6,
  },
  glanceMain: { minHeight: 44, justifyContent: 'center', flexGrow: 1, flexShrink: 1, minWidth: 150 },
  glanceTitle: { color: p.sub, fontSize: 14, fontWeight: bold ? '700' : '600' },
  glanceValue: { flexDirection: 'row', alignItems: 'center', gap: 8, flexWrap: 'wrap' },
  glanceWord: { color: p.ink, fontFamily: f.display, fontSize: 20, fontWeight: '700' },
  fixIt: { minHeight: 44, justifyContent: 'center', paddingHorizontal: 4 },
  fixItText: { color: p.ink, fontSize: 15, fontWeight: bold ? '800' : '700', textDecorationLine: 'underline' },
  addLandBtn: { alignSelf: 'flex-start', marginTop: 12, borderRadius: 10 },
  addLandContent: { minHeight: 48 },
  links: { marginTop: 24 },
  link: { minHeight: 44, justifyContent: 'center' },
  linkText: { color: p.acc, fontSize: 16, fontWeight: bold ? '800' : '600' },
});
