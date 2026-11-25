import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, View, Pressable } from 'react-native';
import { ActivityIndicator, Button, Card, Text } from 'react-native-paper';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { RouteProp, useRoute } from '@react-navigation/native';
import type { RootStackParamList } from '../navigation/types';
import {
  SITE_QUERY_KEYS, fetchSeasonalPlan, putSeasonEvent, refreshHome,
} from '../api/properties';
import { rescheduleAllReminders } from '../notifications/reminders';
import { Forecast, OwnerAction, SeasonEvent, SeasonTask, SeasonalPlan } from '../types/site';
import {
  ACTION_LABELS, STATUS_WORDS, TASK_STATE_WORDS, actionBody, forecastCredit,
  observedDayA11y, observedDayChoices, orderedActions, orderedTasks, seasonSections,
} from '../season/sections';
import { t } from '../i18n';
import ExplainedBlock from '../components/ExplainedBlock';
import ForecastBars from '../components/ForecastBars';
import { followTarget } from '../land/followTarget';
import { timelineDrawsAnything } from '../season/timeline';
import SeasonTimeline from '../components/SeasonTimeline';
import Eyebrow from '../components/Eyebrow';
import LoadError from '../components/LoadError';
import Pill from '../components/Pill';
import RefreshFailed from '../components/RefreshFailed';
import WeatherCredit from '../components/WeatherCredit';
import HowWeKnowButton from '../components/HowWeKnowButton';
import { seasonSections as seasonHowWeKnow } from '../howWeKnow/sections';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';

type Route = RouteProp<RootStackParamList, 'Season'>;
type Styles = ReturnType<typeof makeStyles>;

// Season: the full seasonal plan (build spec section 6). The forecast strip
// with its provider credit, then the events: what needs attention now first,
// then the next twelve months so an owner can plan ahead, then what has
// already happened or been settled. Each event shows its status, its window,
// "Why and data source", its tasks with their low-impact notes, and the
// owner's answers (happened or not yet, done, not needed, clear).
//
// Visuals (map and visuals spec section 4.4): the forecast is drawn as bars
// (each day keeps the text strip's spoken sentence), and the season's
// timeline sits above the sections; tapping an event on it scrolls to its
// card. Events with no dates are not drawn and stay in the list.

/** Apple's attribution page, linked whenever Apple Weather supplied the forecast. */
const APPLE_WEATHER_LEGAL = 'https://weatherkit.apple.com/legal-attribution.html';

function isAppleForecast(f: Forecast): boolean {
  return /weatherkit|apple/i.test(`${f.provider} ${f.provider_name}`);
}

export default function SeasonScreen() {
  const { params } = useRoute<Route>();
  const { propertyId, eventKey } = params;
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const queryClient = useQueryClient();
  const [pulling, setPulling] = useState(false);

  const planQ = useQuery({
    queryKey: SITE_QUERY_KEYS.seasonalPlan(propertyId),
    queryFn: () => fetchSeasonalPlan(propertyId),
  });
  const plan = planQ.data;

  const sections = useMemo(() => (plan ? seasonSections(plan.events) : []), [plan]);

  // Scroll to the event Home linked to, once it has been laid out.
  const scroller = useRef<ScrollView>(null);
  // An event's y is inside its section, so both offsets are needed.
  const sectionY = useRef<Record<string, number>>({});
  const targetY = useRef<{ section: string; y: number } | null>(null);
  // The bars and the timeline above take their full height after they are
  // measured, so the event is followed until the owner scrolls.
  const [follow] = useState(() => followTarget(
    (y) => scroller.current?.scrollTo({ y, animated: true }),
    (run) => { requestAnimationFrame(run); },
  ));
  const tryScroll = useCallback(() => {
    const t = targetY.current;
    const base = t ? sectionY.current[t.section] : undefined;
    if (!t || base == null) return;
    follow.place(base + t.y);
  }, [follow]);
  const onSectionLayout = useCallback((section: string, y: number) => {
    sectionY.current[section] = y;
    tryScroll();
  }, [tryScroll]);
  // Every event's place, for a tap on the timeline.
  const eventY = useRef<Record<string, { section: string; y: number }>>({});
  const scrollToEvent = useCallback((key: string) => {
    const at = eventY.current[key];
    const base = at ? sectionY.current[at.section] : undefined;
    if (!at || base == null) return;
    follow.release();   // the owner chose another place
    scroller.current?.scrollTo({ y: Math.max(0, base + at.y - 12), animated: true });
  }, [follow]);
  const onEventLayout = useCallback((section: string, key: string, y: number) => {
    eventY.current[key] = { section, y };
    if (eventKey && key === eventKey) {
      targetY.current = { section, y };
      tryScroll();
    }
  }, [eventKey, tryScroll]);

  const act = useMutation({
    mutationFn: ({ key, action, observedOn }: { key: string; action: OwnerAction; observedOn?: string }) =>
      putSeasonEvent(propertyId, key, actionBody(action, observedOn)),
    onSuccess: async (updated) => {
      queryClient.setQueryData<SeasonalPlan>(SITE_QUERY_KEYS.seasonalPlan(propertyId), (old) => old && {
        ...old,
        events: old.events.map((e) => (e.event_key === updated.event_key ? updated : e)),
      });
      await refreshHome(queryClient);
      // An owner answer can change which alerts the plan holds.
      void rescheduleAllReminders();
    },
  });

  const onRefresh = useCallback(async () => {
    setPulling(true);
    try { await planQ.refetch(); } finally { setPulling(false); }
  }, [planQ]);

  if (planQ.isLoading) return <ActivityIndicator style={styles.center} size="large" />;
  if (!plan) {
    return (
      <LoadError
        message={t('season.screen.loadFailed')}
        error={planQ.error}
        onRetry={() => planQ.refetch()}
        retrying={planQ.isRefetching}
      />
    );
  }

  return (
    <ScrollView
      ref={scroller}
      style={styles.container}
      contentContainerStyle={styles.content}
      onScrollBeginDrag={follow.release}
      refreshControl={<RefreshControl refreshing={pulling} onRefresh={onRefresh} />}
    >
      {planQ.isError && <RefreshFailed onRetry={() => planQ.refetch()} retrying={planQ.isRefetching} />}
      <Text style={styles.headline} accessibilityRole="header">{plan.season_label || t('season.screen.titleFallback')}</Text>

      {plan.forecast && plan.forecast.days.length > 0 ? (
        <ForecastStrip forecast={plan.forecast} styles={styles} />
      ) : (
        <Text style={styles.quiet}>
          {t('season.screen.noForecast')}
        </Text>
      )}

      {act.isError ? (
        <Text style={styles.error} accessibilityLiveRegion="polite">
          {t('season.screen.notSaved')}
        </Text>
      ) : null}

      {timelineDrawsAnything(plan.events) ? (
        <View style={styles.section}>
          <Eyebrow style={styles.eyebrow}>{t('season.screen.yearAtAGlance')}</Eyebrow>
          <SeasonTimeline events={plan.events} onPressEvent={scrollToEvent} />
        </View>
      ) : null}

      {sections.length === 0 ? (
        <Text style={styles.quietBlock}>{t('season.screen.empty')}</Text>
      ) : sections.map((s) => (
        <View key={s.key} style={styles.section} collapsable={false} onLayout={(ev) => onSectionLayout(s.key, ev.nativeEvent.layout.y)}>
          <Eyebrow style={styles.eyebrow}>{s.title}</Eyebrow>
          {s.events.map((e) => (
            <View key={e.event_key} collapsable={false} onLayout={(ev) => onEventLayout(s.key, e.event_key, ev.nativeEvent.layout.y)}>
              <EventCard
                event={e}
                highlighted={e.event_key === eventKey}
                busy={act.isPending && act.variables?.key === e.event_key}
                onAction={(action, observedOn) => act.mutate({ key: e.event_key, action, observedOn })}
                styles={styles}
              />
            </View>
          ))}
        </View>
      ))}

      <HowWeKnowButton sections={() => seasonHowWeKnow({
        events: plan.events,
        forecastCredit: plan.forecast ? forecastCredit(plan.forecast.provider_name, plan.forecast.fetched_at) : null,
        notes: plan.notes,
      })} />
    </ScrollView>
  );
}

function ForecastStrip({ forecast, styles }: { forecast: Forecast; styles: Styles }) {
  // The bars replace the text strip; each day's spoken sentence is the
  // strip's (forecastCells), and the rain and frost words stay on screen.
  return (
    <View style={styles.section}>
      <Eyebrow style={styles.eyebrow}>{t('season.screen.forecast')}</Eyebrow>
      <ForecastBars days={forecast.days} />
      <Text style={styles.quiet}>{forecastCredit(forecast.provider_name, forecast.fetched_at)}</Text>
      {isAppleForecast(forecast) ? (
        <WeatherCredit attribution={{ text: forecast.provider_name, url: APPLE_WEATHER_LEGAL }} />
      ) : null}
    </View>
  );
}

function EventCard({ event, highlighted, busy, onAction, styles }: {
  event: SeasonEvent;
  highlighted: boolean;
  busy: boolean;
  onAction: (a: OwnerAction, observedOn?: string) => void;
  styles: Styles;
}) {
  const [pickingDay, setPickingDay] = useState(false);
  const actions = orderedActions(event.owner_actions);
  useEffect(() => { if (!busy) setPickingDay(false); }, [busy, event.status]);

  return (
    <Card style={[styles.card, highlighted && styles.cardHighlight]}>
      <Card.Content>
        <View style={styles.eventHead}>
          <Text style={styles.eventTitle} accessibilityRole="header">{event.title}</Text>
          <Pill tone={event.status === 'forecast' || event.status === 'happening' ? 'warn' : 'neutral'}>
            {STATUS_WORDS[event.status]}
          </Pill>
        </View>
        {event.window.text ? <Text style={styles.window}>{event.window.text}</Text> : null}
        <ExplainedBlock explained={event.explained} />

        {event.tasks.length > 0 && (
          <View style={styles.tasks}>
            {orderedTasks(event.tasks).map((t) => <TaskRow key={t.task_key} task={t} styles={styles} />)}
          </View>
        )}

        {actions.length > 0 && (
          <View style={styles.actions}>
            {actions.map((a) => (
              <Button
                key={a}
                mode={a === 'clear' ? 'text' : 'outlined'}
                compact
                disabled={busy}
                onPress={() => (a === 'mark_happened' ? setPickingDay((p) => !p) : onAction(a))}
                accessibilityLabel={`${ACTION_LABELS[a]}: ${event.title}`}
                style={styles.actionBtn}
              >
                {ACTION_LABELS[a]}
              </Button>
            ))}
          </View>
        )}
        {pickingDay && (
          <View>
            <Text style={styles.pickLabel}>{t('season.screen.whenHappened')}</Text>
            <View style={styles.actions}>
              {observedDayChoices().map((d, i) => (
                <Button
                  key={d.value}
                  mode="outlined"
                  compact
                  disabled={busy}
                  onPress={() => onAction('mark_happened', d.value)}
                  accessibilityLabel={observedDayA11y(i, d.label)}
                  style={styles.actionBtn}
                >
                  {d.label}
                </Button>
              ))}
            </View>
          </View>
        )}
        {busy ? <ActivityIndicator style={styles.inlineSpin} /> : null}
      </Card.Content>
    </Card>
  );
}

function TaskRow({ task, styles }: { task: SeasonTask; styles: Styles }) {
  // The task's reason and sources live in How we know (one sheet per screen).
  const settled = task.state !== 'open';
  return (
    <View style={styles.task}>
      <View style={styles.taskHead} accessible accessibilityLabel={`${TASK_STATE_WORDS[task.state]}. ${task.text}`}>
        <Text style={styles.taskMark}>{settled ? '✓' : '○'}</Text>
        <Text style={[styles.taskText, settled && styles.taskSettled]}>{task.text}</Text>
      </View>
      {task.low_impact_note ? <Text style={styles.lowImpact}>{task.low_impact_note}</Text> : null}
    </View>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  center: { flex: 1, marginTop: 64 },
  container: { flex: 1, backgroundColor: p.bg },
  content: { padding: 16, paddingBottom: 48 },
  headline: { color: p.acc, fontFamily: f.display, fontSize: 22, fontWeight: '700', marginBottom: 8 },
  section: { marginTop: 16 },
  eyebrow: { marginBottom: 8 },
  quiet: { color: p.faint, fontSize: 12.5, marginTop: 6 },
  quietBlock: { color: p.sub, fontSize: 14, marginTop: 16 },
  error: { color: p.warn, fontSize: 13.5, marginTop: 12 },
  card: { backgroundColor: p.card, marginBottom: 12 },
  cardHighlight: { borderWidth: 2, borderColor: p.acc },
  eventHead: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  eventTitle: { color: p.ink, fontFamily: f.display, fontSize: 17, fontWeight: '700', flex: 1 },
  window: { color: p.sub, fontSize: 14, marginTop: 4 },
  tasks: { marginTop: 8, gap: 10 },
  task: { paddingTop: 6, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: p.line },
  taskHead: { flexDirection: 'row', gap: 8 },
  taskMark: { color: p.good, fontSize: 15, width: 16 },
  taskText: { color: p.ink, fontSize: 15, lineHeight: 21, flex: 1 },
  taskSettled: { color: p.sub },
  lowImpact: { color: p.sub, fontSize: 13.5, lineHeight: 19, marginLeft: 24, marginTop: 2 },
  toggle: { alignSelf: 'flex-start', marginLeft: 24, marginTop: 4, minHeight: 28, justifyContent: 'center' },
  toggleText: { color: p.acc, fontSize: 13, fontWeight: '600' },
  detail: { marginLeft: 24, paddingLeft: 10, borderLeftWidth: 2, borderLeftColor: p.line, gap: 4 },
  reason: { color: p.sub, fontSize: 13, lineHeight: 19 },
  source: { color: p.faint, fontSize: 12.5, lineHeight: 18 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 10 },
  actionBtn: { marginRight: 0 },
  pickLabel: { color: p.sub, fontSize: 13.5, marginTop: 8 },
  inlineSpin: { marginTop: 8 },
  note: { color: p.sub, fontSize: 13.5, lineHeight: 19, marginTop: 12 },
});
