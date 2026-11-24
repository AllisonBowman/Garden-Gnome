// ReadingTile and ReadingTileGrid: the land readings as small graphics with
// their confidence label (map and visuals spec section 1): sun hours as a
// gauge of a 12 hour day, the hardiness zone on a coldest-to-warmest scale
// (both with captions at the ends), where water collects as labelled steps
// with the current one filled, and the topsoil's sand, silt and clay as one
// bar. A value the app cannot read shows its text alone.
// The tiles come from land/readingTiles.ts.
//
// Usage (Home's "Your land", Your land screen):
//
//   const tiles = readingTiles(profileQ.data, vitals?.cards ?? []);
//   <ReadingTileGrid tiles={tiles} />
//
// Tapping a tile shows its ExplainedBlock (reason, data source, confidence)
// under the grid; tapping it again hides it. Pass `selected` and `onSelect`
// to control which is open from the screen, and `onOpen(tile)` to add a link
// under the open block (Home: "Open in Your land").

import React, { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { Button, Text } from 'react-native-paper';
import Svg, { Circle, Rect } from 'react-native-svg';
import { ReadingTile as Tile, ReadingTileKey, TileGauge, TileSteps } from '../land/readingTiles';
import ExplainedBlock from './ExplainedBlock';
import ConfidenceChip from './ConfidenceChip';
import Eyebrow from './Eyebrow';
import { useAppTheme } from '../theme/ThemeProvider';
import { useMeasuredWidth } from './useMeasuredWidth';
import { Palette } from '../theme/tokens';
import { t } from '../i18n';
import { localConfidenceLabel } from './explainedText';

export interface ReadingTileProps {
  tile: Tile;
  open?: boolean;
  onPress?: () => void;
}

const GAUGE_H = 10;

function gaugeColor(key: ReadingTileKey, p: Palette): string {
  switch (key) {
    case 'sun': return p.hedge;
    case 'hardiness': return p.acc;
    case 'drainage': return p.acc;
    case 'soil': return p.warn;
  }
}

/** A track with the reading's share filled, a dot at its end, and what
 *  each end of the track means under it. */
function Gauge({ gauge, color, palette }: { gauge: TileGauge; color: string; palette: Palette }) {
  const { width: w, measureProps } = useMeasuredWidth();
  const x = Math.max(GAUGE_H / 2, Math.min(w - GAUGE_H / 2, gauge.fraction * w));
  return (
    <View>
      <View {...measureProps} style={styles.gauge}>
        {w > 0 ? (
          <Svg width={w} height={GAUGE_H + 4}>
            <Rect x={0} y={2} width={w} height={GAUGE_H} rx={GAUGE_H / 2} fill={palette.line2} />
            <Rect x={0} y={2} width={x} height={GAUGE_H} rx={GAUGE_H / 2} fill={color} />
            <Circle cx={x} cy={2 + GAUGE_H / 2} r={GAUGE_H / 2 + 1} fill={palette.card} stroke={color} strokeWidth={2} />
          </Svg>
        ) : null}
      </View>
      <View style={styles.ends}>
        <Text style={[styles.end, { color: palette.sub }]}>{gauge.startLabel}</Text>
        <Text style={[styles.end, styles.endRight, { color: palette.sub }]}>{gauge.endLabel}</Text>
      </View>
    </View>
  );
}

/** Each step as a small square and its words, the current one filled. */
function Steps({ steps, color, palette }: { steps: TileSteps; color: string; palette: Palette }) {
  return (
    <View style={styles.steps}>
      {steps.labels.map((label, i) => {
        const on = i === steps.current;
        return (
          <View key={label} style={styles.step}>
            <View style={[styles.stepMark, {
              borderColor: on ? color : palette.line2, backgroundColor: on ? color : 'transparent',
            }]} />
            <Text style={[styles.stepText, { color: on ? palette.ink : palette.sub, fontWeight: on ? '700' : '400' }]}>
              {label}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

/** Sand, silt and clay side by side in one bar. */
function MixBar({ mix, palette }: { mix: NonNullable<Tile['mix']>; palette: Palette }) {
  const { width: w, measureProps } = useMeasuredWidth();
  const parts = [
    { share: mix.sand, color: palette.hedge },
    { share: mix.silt, color: palette.sub },
    { share: mix.clay, color: palette.warn },
  ];
  let x = 0;
  return (
    <View {...measureProps} style={styles.gauge}>
      {w > 0 ? (
        <Svg width={w} height={GAUGE_H + 4}>
          {parts.map((p, i) => {
            const width = (Math.max(0, p.share) / 100) * w;
            const r = <Rect key={i} x={x} y={2} width={width} height={GAUGE_H} fill={p.color} />;
            x += width;
            return r;
          })}
        </Svg>
      ) : null}
    </View>
  );
}

export function ReadingTile({ tile, open = false, onPress }: ReadingTileProps) {
  const { palette, fonts } = useAppTheme();
  const body = (
    <>
      <Eyebrow>{tile.title}</Eyebrow>
      <Text style={[styles.value, { color: palette.ink, fontFamily: fonts.display }]} numberOfLines={2}>{tile.valueText}</Text>
      <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
        {tile.gauge ? <Gauge gauge={tile.gauge} color={gaugeColor(tile.key, palette)} palette={palette} /> : null}
        {tile.steps ? <Steps steps={tile.steps} color={gaugeColor(tile.key, palette)} palette={palette} /> : null}
        {tile.mix ? <MixBar mix={tile.mix} palette={palette} /> : null}
      </View>
      {tile.detail ? <Text style={[styles.detail, { color: palette.sub }]} numberOfLines={3}>{tile.detail}</Text> : null}
      {/* "Not known yet" as the value needs no chip repeating it. */}
      {tile.confidenceLabel.trim().toLowerCase() === tile.valueText.trim().toLowerCase() ? null : (
        <ConfidenceChip confidence={tile.explained.confidence} label={localConfidenceLabel(tile.confidenceLabel, tile.explained.confidence)} style={styles.chip} />
      )}
    </>
  );
  const frame = [styles.tile, {
    backgroundColor: palette.card, borderColor: open ? palette.acc : palette.line2,
  }];
  return onPress ? (
    <Pressable
      onPress={onPress}
      style={frame}
      accessibilityRole="button"
      accessibilityLabel={tile.a11y}
      accessibilityHint={open ? t('land.tileHideHint') : t('land.tileShowHint')}
      accessibilityState={{ expanded: open }}
    >
      {body}
    </Pressable>
  ) : (
    <View style={frame} accessible accessibilityLabel={tile.a11y}>{body}</View>
  );
}

export interface ReadingTileGridProps {
  tiles: Tile[];
  /** Which tile's explanation is open; leave out to let the grid keep it. */
  selected?: ReadingTileKey | null;
  onSelect?: (key: ReadingTileKey | null) => void;
  /** A link under the open explanation, such as "Open in Your land". */
  onOpen?: (tile: Tile) => void;
  openLabel?: string;
}

/** Tiles in two columns, with the tapped tile's ExplainedBlock under them. */
export default function ReadingTileGrid({
  tiles, selected, onSelect, onOpen, openLabel = t('land.openInYourLand'),
}: ReadingTileGridProps) {
  const [own, setOwn] = useState<ReadingTileKey | null>(null);
  const current = selected !== undefined ? selected : own;
  const choose = (key: ReadingTileKey | null) => { if (selected === undefined) setOwn(key); onSelect?.(key); };
  if (tiles.length === 0) return null;
  const openTile = tiles.find((t) => t.key === current) ?? null;
  return (
    <View>
      <View style={styles.grid}>
        {tiles.map((t) => (
          <View key={t.key} style={styles.cell}>
            <ReadingTile tile={t} open={t.key === current} onPress={() => choose(t.key === current ? null : t.key)} />
          </View>
        ))}
      </View>
      {openTile ? (
        <View style={styles.explained}>
          <ExplainedBlock explained={openTile.explained} title={openTile.title} initiallyOpen />
          {onOpen ? (
            <Button mode="text" compact onPress={() => onOpen(openTile)} style={styles.openBtn}
              accessibilityLabel={t('land.openA11y', { label: openLabel, title: openTile.title })}>
              {openLabel}
            </Button>
          ) : null}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: { flexDirection: 'row', flexWrap: 'wrap', marginHorizontal: -4 },
  cell: { width: '50%', padding: 4 },
  tile: { borderRadius: 12, borderWidth: 1, padding: 10, minHeight: 44, gap: 4, flexGrow: 1 },
  value: { fontSize: 17, fontWeight: '700' },
  detail: { fontSize: 12, lineHeight: 16 },
  gauge: { width: '100%', height: GAUGE_H + 4, marginTop: 2 },
  ends: { flexDirection: 'row', justifyContent: 'space-between', gap: 6, marginBottom: 2 },
  end: { fontSize: 11, lineHeight: 14, flexShrink: 1 },
  endRight: { textAlign: 'right' },
  steps: { gap: 3, marginVertical: 2 },
  step: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  stepMark: { width: 10, height: 10, borderRadius: 2, borderWidth: 1.5 },
  stepText: { fontSize: 12, lineHeight: 15, flexShrink: 1 },
  chip: { alignSelf: 'flex-start', marginTop: 2 },
  explained: { marginTop: 8 },
  openBtn: { alignSelf: 'flex-start', minHeight: 44, justifyContent: 'center' },
});
