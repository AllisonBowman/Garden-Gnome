// SeasonTimeline: the season's events as bands on a month axis, a single
// date as a dot, today as a line (map and visuals spec section 1). The maths
// is in season/timeline.ts. The axis shows short month names; the span with
// its years is one caption under the chart. The today line is drawn behind
// the bands and titles, and each title has a halo in the card colour so the
// line never strikes through it. Events with no dates are not drawn; they stay in
// the list the screen shows under it.
//
// Usage (top of Home's "The season ahead", or above Season's sections):
//
//   <SeasonTimeline events={vitals.season_ahead} />
//   <SeasonTimeline events={plan.events} onPressEvent={(key) => openEvent(key)} />
//
// Each drawn event is one accessible element with a sentence (title, when,
// status); with `onPressEvent` it is a button with a 44 point target.
// Colours by tone: frost warn, autumn hedge, spring good, settled line.

import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useMeasuredWidth } from './useMeasuredWidth';
import { Text } from 'react-native-paper';
import Svg, { Circle, Line, Rect } from 'react-native-svg';
import { SeasonEventSummary } from '../types/site';
import {
  TIMELINE_CHAR_SHARE, TIMELINE_GEOMETRY, TimelineTone, seasonTimeline, timelineHeight, titleRect, todayCaptionRect,
} from '../season/timeline';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette } from '../theme/tokens';
import { t } from '../i18n';

export interface SeasonTimelineProps {
  /** Full events (Season) or the summaries Home has; both carry `window`. */
  events: SeasonEventSummary[];
  /** A tap on an event, such as opening it in the Season screen. */
  onPressEvent?: (eventKey: string) => void;
  /** For tests and previews; defaults to now. */
  today?: Date;
}

const AXIS_H = TIMELINE_GEOMETRY.axisH;
const ROW_H = TIMELINE_GEOMETRY.rowH;
const BAND_H = TIMELINE_GEOMETRY.bandH;
const FOOT_H = TIMELINE_GEOMETRY.footH; // "Today" under the rows
const TITLE_SIZE = TIMELINE_GEOMETRY.titleSize;
const CHAR_W = TITLE_SIZE * TIMELINE_CHAR_SHARE;

function toneColor(tone: TimelineTone, p: Palette): string {
  switch (tone) {
    case 'frost': return p.warn;
    case 'autumn': return p.hedge;
    case 'spring': return p.good;
    case 'settled': return p.line;
  }
}

export default function SeasonTimeline({ events, onPressEvent, today }: SeasonTimelineProps) {
  const { palette, fonts } = useAppTheme();
  const { width, measureProps } = useMeasuredWidth();
  const layout = width > 0 ? seasonTimeline(events, { width, charWidth: CHAR_W }, today) : null;
  if (layout && layout.items.length === 0) return null;
  const height = timelineHeight(layout ? layout.rows : 1);
  const todayBox = layout ? todayCaptionRect(layout, width) : null;

  return (
    <View style={styles.wrap}>
    <View {...measureProps} style={{ width: '100%', height }}>
      {layout ? (
        <>
          <View
            style={StyleSheet.absoluteFill}
            pointerEvents="none"
            accessibilityElementsHidden
            importantForAccessibility="no-hide-descendants"
          >
            <Svg width={width} height={height}>
              {layout.months.map((m, i) => (
                <React.Fragment key={m.label + i}>
                  {i % 2 === 1 ? (
                    <Rect x={m.x} y={AXIS_H} width={m.width} height={height - AXIS_H - FOOT_H} fill={palette.accSoft} opacity={0.5} />
                  ) : null}
                  <Line x1={m.x} x2={m.x} y1={AXIS_H - 4} y2={height - FOOT_H} stroke={palette.line2} strokeWidth={1} />
                </React.Fragment>
              ))}
              {/* Today, behind the bands and the titles. */}
              {layout.todayX != null ? (
                <Line x1={layout.todayX} x2={layout.todayX} y1={AXIS_H - 6} y2={height - FOOT_H}
                  stroke={palette.ink} strokeWidth={2} />
              ) : null}
              {layout.items.map((it) => {
                const y = AXIS_H + it.row * ROW_H + ROW_H - BAND_H - 4;
                const color = toneColor(it.tone, palette);
                return it.kind === 'band' ? (
                  <Rect key={it.event_key} x={it.x0} y={y} width={Math.max(3, it.x1 - it.x0)} height={BAND_H}
                    rx={BAND_H / 2} fill={color} opacity={it.live ? 1 : 0.8}
                    stroke={it.live ? palette.ink : undefined} strokeWidth={it.live ? 1.5 : 0} />
                ) : (
                  <Circle key={it.event_key} cx={it.x0} cy={y + BAND_H / 2} r={BAND_H / 2 + 1}
                    fill={color} stroke={it.live ? palette.ink : undefined} strokeWidth={it.live ? 1.5 : 0} />
                );
              })}
            </Svg>
            {layout.months.map((m, i) => (
              <Text key={`l${m.label}${i}`} numberOfLines={1}
                style={[styles.month, { left: m.x + 3, width: Math.max(0, m.width - 3), color: palette.faint, fontFamily: fonts.label }]}>
                {m.width >= 22 ? m.label : m.label.slice(0, 1)}
              </Text>
            ))}
            {todayBox ? (
              <Text style={[styles.today, { top: todayBox.top, left: todayBox.left, width: todayBox.width, color: palette.ink }]}>
                {t('season.dates.today')}
              </Text>
            ) : null}
          </View>
          {layout.items.map((it) => {
            const top = AXIS_H + it.row * ROW_H;
            const left = Math.min(it.x0, it.labelX);
            const right = Math.max(it.kind === 'mark' ? it.x0 + BAND_H : it.x1, it.labelX + it.labelWidth);
            const box = { position: 'absolute' as const, top, left, width: Math.max(1, right - left), height: ROW_H };
            const r = titleRect(it);
            // A halo in the card colour, so the today line behind never
            // strikes through the words.
            const title = (
              <Text numberOfLines={1}
                style={[styles.title, {
                  left: r.left - left, top: r.top - top, width: r.width, height: r.height,
                  paddingHorizontal: TIMELINE_GEOMETRY.haloPad, color: palette.ink, backgroundColor: palette.card,
                }]}>
                {it.title}
              </Text>
            );
            return onPressEvent ? (
              <Pressable key={it.event_key} style={box} hitSlop={{ top: 5, bottom: 5 }}
                onPress={() => onPressEvent(it.event_key)}
                accessibilityRole="button" accessibilityLabel={it.a11y} accessibilityHint={t('season.timeline.opensEvent')}>
                {title}
              </Pressable>
            ) : (
              <View key={it.event_key} style={box} accessible accessibilityLabel={it.a11y}>
                {title}
              </View>
            );
          })}
        </>
      ) : null}
    </View>
    {layout ? (
      <Text style={[styles.caption, { color: palette.sub }]}>{layout.spanText}</Text>
    ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { width: '100%', marginVertical: 6 },
  month: { position: 'absolute', top: 2, fontSize: TIMELINE_GEOMETRY.monthSize },
  today: { position: 'absolute', textAlign: 'center', fontSize: 9.5, fontWeight: '700' },
  title: {
    position: 'absolute', fontSize: TITLE_SIZE, lineHeight: TIMELINE_GEOMETRY.titleH, borderRadius: 4,
    overflow: 'hidden',
  },
  caption: { fontSize: 12.5, lineHeight: 18, marginTop: 2 },
});
