// ForecastBars: the forecast as one high-to-low bar per day on a shared °F
// scale, a dashed 32 °F line, frost nights marked with a snowflake, and a
// weather icon per day (map and visuals spec section 1). The maths is in
// home/forecastBars.ts.
//
// Usage (Home's Weather section, or in place of Season's text strip):
//
//   {vitals.forecast?.days.length ? <ForecastBars days={vitals.forecast.days} /> : null}
//   <WeatherCredit ... />   // the screen keeps its own credit line
//
// Each day is one accessible element whose sentence is the text strip's
// (forecastCells), so a screen reader hears the same as before. The scale
// lines and the 32 °F line are decorative. What the text strip said that a
// bar cannot (the chance of rain, and how hard each frost is) stays on
// screen: a rain line under the days and one sentence naming the frost
// nights.

import React from 'react';
import { StyleSheet, View } from 'react-native';
import { useMeasuredWidth } from './useMeasuredWidth';
import { Icon, Text } from 'react-native-paper';
import Svg, { Circle, Line, Rect } from 'react-native-svg';
import { ForecastDay } from '../types/site';
import {
  CHART_TEXT, FORECAST_HEAD, FORECAST_RAIN_ROW, FREEZING_LABEL, NO_TEMPERATURE_TEXT, forecastBars, forecastCaption,
  forecastChartHeight,
} from '../home/forecastBars';
import { frostNightsLine } from '../season/sections';
import { useAppTheme } from '../theme/ThemeProvider';

export interface ForecastBarsProps {
  days: ForecastDay[];
  /** The bars' drawing height in pixels, labels included (default 120). */
  height?: number;
  /** For tests and previews; defaults to now. */
  today?: Date;
}

const PAD = 16;
const HEAD = FORECAST_HEAD; // day name and icon above the bars

export default function ForecastBars({ days, height = 120, today }: ForecastBarsProps) {
  const { palette, fonts } = useAppTheme();
  const { width, measureProps } = useMeasuredWidth();
  if (days.length === 0) return null;
  const layout = forecastBars(days, { width: Math.max(width, 1), height, padTop: PAD, padBottom: PAD }, today);
  const anyRain = layout.days.some((d) => d.rainText);
  const frostLine = frostNightsLine(days, today);

  return (
    <View {...measureProps} style={styles.wrap}>
      {/* The chart's height is known before its width, so it is reserved on
          first paint and the notes below do not jump once it is measured. */}
      <View style={{ height: forecastChartHeight(height, anyRain) }}>
      {width > 0 ? (
        <View style={{ height: HEAD + height }}>
          {/* Scale lines and the 32 °F line, behind the days. */}
          <View
            style={[StyleSheet.absoluteFill, { top: HEAD }]}
            pointerEvents="none"
            accessibilityElementsHidden
            importantForAccessibility="no-hide-descendants"
          >
            <Svg width={width} height={height}>
              {layout.ticks.map((t) => (
                <Line key={t.value} x1={0} x2={width} y1={t.y} y2={t.y} stroke={palette.line2} strokeWidth={1} />
              ))}
              {layout.freezingY != null ? (
                <Line x1={0} x2={width} y1={layout.freezingY} y2={layout.freezingY}
                  stroke={palette.acc} strokeWidth={1.5} strokeDasharray="5 4" />
              ) : null}
            </Svg>
            {layout.freezingY != null ? (
              <Text style={[styles.freezeLabel, { top: layout.freezingY - 15, color: palette.acc, fontFamily: fonts.numeric }]}>
                {FREEZING_LABEL}
              </Text>
            ) : null}
          </View>
          <View style={styles.row}>
            {layout.days.map((d) => (
              <View key={d.date} style={{ width: d.columnWidth }} accessible accessibilityLabel={d.a11y}>
                <View style={styles.head}>
                  <Text style={[styles.day, { color: palette.sub, fontFamily: fonts.label }]} numberOfLines={1}>{d.day}</Text>
                  <Icon source={d.icon} size={18} color={palette.ink} />
                </View>
                <View style={{ height }}>
                  <Svg width={d.columnWidth} height={height}>
                    {d.shape === 'range' ? (
                      <Rect
                        x={d.columnWidth / 2 - d.barWidth / 2} y={d.yHigh!}
                        width={d.barWidth} height={Math.max(2, d.yLow! - d.yHigh!)}
                        rx={d.barWidth / 2} fill={d.frostMark ? palette.acc : palette.hedge}
                      />
                    ) : null}
                    {d.shape === 'high' || d.shape === 'low' ? (
                      <Circle cx={d.columnWidth / 2} cy={(d.yHigh ?? d.yLow)!} r={d.barWidth / 2}
                        fill={d.frostMark ? palette.acc : palette.hedge} />
                    ) : null}
                  </Svg>
                  {d.yHigh != null ? (
                    <Text style={[styles.temp, { top: d.yHigh - 15, color: palette.ink, fontFamily: fonts.numeric }]}>
                      {d.highText}
                    </Text>
                  ) : null}
                  {d.yLow != null ? (
                    <Text style={[styles.temp, { top: d.yLow + 1, color: d.frostMark ? palette.acc : palette.sub, fontFamily: fonts.numeric }]}>
                      {d.lowText}
                    </Text>
                  ) : null}
                  {d.frostMark && d.yLow != null ? (
                    <View style={[styles.frost, { top: d.yLow - 6, left: d.columnWidth / 2 + d.barWidth / 2 + 1 }]}>
                      <Icon source="snowflake" size={12} color={palette.acc} />
                    </View>
                  ) : null}
                  {d.shape === 'none' ? (
                    <Text style={[styles.none, { color: palette.faint }]}>{NO_TEMPERATURE_TEXT}</Text>
                  ) : null}
                </View>
              </View>
            ))}
          </View>
        </View>
      ) : null}
      {width > 0 && anyRain ? (
        <View style={[styles.row, { height: FORECAST_RAIN_ROW }]} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
          {layout.days.map((d) => (
            <Text key={d.date} style={[styles.rain, { width: d.columnWidth, color: palette.sub, fontFamily: fonts.numeric }]}
              numberOfLines={1}>
              {d.rainText ? d.rainText.replace(' rain', '') : ''}
            </Text>
          ))}
        </View>
      ) : null}
      </View>
      <Text style={[styles.note, { color: palette.sub }]}>{forecastCaption(anyRain)}</Text>
      {frostLine ? <Text style={[styles.note, { color: palette.sub }]}>{frostLine}</Text> : null}
      {layout.freezingNote ? (
        <Text style={[styles.note, { color: palette.sub }]}>{layout.freezingNote}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { width: '100%', marginVertical: 6 },
  row: { flexDirection: 'row' },
  head: { height: HEAD, alignItems: 'center', justifyContent: 'center', gap: 2 },
  day: { fontSize: CHART_TEXT.day },
  temp: { position: 'absolute', left: 0, right: 0, textAlign: 'center', fontSize: CHART_TEXT.temp },
  frost: { position: 'absolute' },
  none: { position: 'absolute', left: 0, right: 0, top: '40%', textAlign: 'center', fontSize: CHART_TEXT.none },
  freezeLabel: { position: 'absolute', left: 2, fontSize: 10 },
  rain: { textAlign: 'center', fontSize: CHART_TEXT.rain },
  note: { fontSize: 12.5, lineHeight: 18, marginTop: 4 },
});
