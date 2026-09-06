import React, { useMemo } from 'react';
import { View, StyleSheet, Pressable, Linking, StyleProp, ViewStyle } from 'react-native';
import { Text } from 'react-native-paper';
import { CareSource, Species } from '../types';
import {
  CATALOG_LINE, careFactRows, careSourceLabels, careStatusLine, legacyStats,
} from '../care/facts';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import Eyebrow from './Eyebrow';
import Pill from './Pill';

// The care facts as a screen shows them. The species detail and the plant
// detail both describe a species, and both used to read the six legacy
// columns straight off the row. One component rather than two copies: the
// rules — a resolved concept replaces its legacy stat, a genus-borrowed row
// is labelled (ADR 0002), a source is a name and a link and never a passage
// (ADR 0003) — are the kind that drift apart when duplicated, and the failure
// is a screen nobody thought to re-check quietly showing a synthetic number
// beside a cited one.

/** One line on how well-backed the facts below are; nothing for a legacy
 *  row the recompute has not reached. */
export function CareStatusLine({ species, style }: {
  species: Species; style?: StyleProp<ViewStyle>;
}) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const line = careStatusLine(species);
  if (!line) return null;
  return (
    <View style={style}>
      <Text variant="bodySmall" style={styles.status}>{line}</Text>
    </View>
  );
}

/** The resolved facts, one row per concept; nothing when none resolved.
 *  `compact` is the plant detail's tighter spacing. */
export function CareFactList({ species, compact = false }: {
  species: Species; compact?: boolean;
}) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const rows = careFactRows(species);
  if (rows.length === 0) return null;
  return (
    <View>
      {rows.map((row) => (
        <View key={row.key} style={[styles.factRow, compact && styles.factRowCompact]}>
          <View style={styles.factHead}>
            <Eyebrow>{row.label}</Eyebrow>
            {/* Borrowed from the genus: honest to show, dishonest to hide. */}
            {row.inferred && <Pill style={styles.inferredPill}>genus-inferred</Pill>}
          </View>
          <Text variant={compact ? 'bodySmall' : 'bodyMedium'} style={styles.factValue}>
            {row.value}
          </Text>
        </View>
      ))}
    </View>
  );
}

/** The legacy stats, and only those whose concept nothing resolved has
 *  replaced: the short ones in a row, soil beneath. Nothing for a minted
 *  row. Captioned, because on a row that is also cited they sit under a
 *  "cited to …" line looking equally cited, and they are not. */
export function LegacyStatRow({ species }: { species: Species }) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const stats = legacyStats(species);
  if (stats.length === 0) return null;
  const short = stats.filter((s) => s.key !== 'soil');
  const soil = stats.find((s) => s.key === 'soil');
  return (
    <View>
      <Text variant="bodySmall" style={styles.legacyCaption}>{CATALOG_LINE}</Text>
      {short.length > 0 && (
        <View style={styles.statRow}>
          {short.map((s) => (
            <View key={s.key} style={styles.stat}>
              <Eyebrow style={styles.statLabel}>{s.label}</Eyebrow>
              <Text variant="bodyMedium" style={styles.statValue}>{s.value}</Text>
            </View>
          ))}
        </View>
      )}
      {soil && (
        <View style={styles.soil}>
          <Eyebrow style={styles.statLabel}>{soil.label}</Eyebrow>
          <Text variant="bodySmall" style={styles.soilValue}>{soil.value}</Text>
        </View>
      )}
    </View>
  );
}

/** Each page the values came from, as a link: the authority's name, a
 *  "(genus)" suffix when every field from that page was borrowed, and the
 *  URL behind the press — the honest "show the evidence" (ADR 0003). */
export function CareSourceRows({ sources }: { sources: CareSource[] }) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  if (sources.length === 0) return null;
  const labels = careSourceLabels(sources);
  return (
    <View>
      {sources.map((source, i) => {
        const label = labels[i];
        return (
          <Pressable
            key={`${source.authority}|${source.url}|${i}`}
            onPress={() => source.url && void Linking.openURL(source.url)}
            disabled={!source.url}
            style={styles.sourceRow}
            accessibilityRole="link"
            accessibilityLabel={`${label}. Opens the page these care facts came from.`}
          >
            <Text variant="bodyMedium" style={styles.sourceText}>
              {label}{source.url ? ' ›' : ''}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  status: { color: p.sub, lineHeight: 18 },
  factRow: { paddingVertical: 8, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: p.line2 },
  factRowCompact: { paddingVertical: 5 },
  factHead: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 3 },
  inferredPill: { paddingVertical: 1 },
  factValue: { color: p.ink, lineHeight: 20 },
  legacyCaption: { color: p.sub, lineHeight: 18, marginBottom: 8 },
  statRow: { flexDirection: 'row', justifyContent: 'space-between' },
  stat: { alignItems: 'center', flex: 1 },
  statLabel: { marginBottom: 2 },
  statValue: { fontFamily: f.numeric, fontWeight: '600', color: p.ink, textTransform: 'capitalize' },
  soil: { marginTop: 12 },
  soilValue: { color: p.ink },
  // 44px min target: a source is a link, and a link is a tappable row like
  // any other.
  sourceRow: { minHeight: 44, justifyContent: 'center', borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: p.line2 },
  sourceText: { color: p.acc },
});
