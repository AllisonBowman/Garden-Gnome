// MapLegend: what the colours of the chosen map layer mean, what the layer
// does not count, and its "Why and data source" (map and visuals spec
// sections 1 and 2). The swatch colours are the server's own legend, the same
// numbers it drew the picture with, so the two cannot disagree.
//
// Usage, under the map and the chips:
//
//   <MapLegend layer={chosen.layer} />                 // nothing for Aerial
//   <MapLegend layer={chosen.layer} showExplained={false} />  // legend and notes only
//
// The legend is one accessible element with a sentence (legendA11y).

import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Text } from 'react-native-paper';
import { MapLayer } from '../types/site';
import { layerReady, legendA11y, legendSteps } from '../land/mapLayers';
import ExplainedBlock from './ExplainedBlock';
import { useAppTheme } from '../theme/ThemeProvider';
import { t } from '../i18n';

export interface MapLegendProps {
  /** The layer drawn on the map; null (Aerial) or a layer not ready draws nothing. */
  layer: MapLayer | null | undefined;
  /** Show the layer's ExplainedBlock under the legend (default true). */
  showExplained?: boolean;
  /** Show the layer's notes, such as "Buildings are not counted." (default true). */
  showNotes?: boolean;
}

export default function MapLegend({ layer, showExplained = true, showNotes = true }: MapLegendProps) {
  const { palette } = useAppTheme();
  if (!layer || !layerReady(layer)) return null;
  const steps = legendSteps(layer);
  return (
    <View style={styles.wrap}>
      {steps.length > 0 ? (
        <View style={styles.steps} accessible accessibilityLabel={legendA11y(layer)}>
          {steps.map((s) => (
            <View key={`${s.color}-${s.label}`} style={styles.step}>
              <View style={[styles.swatch, { backgroundColor: s.color, borderColor: palette.line }]} />
              <Text style={[styles.stepText, { color: palette.ink }]}>{s.label}</Text>
            </View>
          ))}
        </View>
      ) : null}
      {showNotes ? layer.notes.filter((n) => n.trim()).map((n) => (
        <Text key={n} style={[styles.note, { color: palette.sub }]}>{n}</Text>
      )) : null}
      {showExplained ? <ExplainedBlock explained={layer.explained} title={t('land.layerBlockTitle', { title: layer.title })} /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { marginTop: 8, gap: 4 },
  steps: { flexDirection: 'row', flexWrap: 'wrap', columnGap: 12, rowGap: 6 },
  step: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  swatch: { width: 16, height: 16, borderRadius: 4, borderWidth: StyleSheet.hairlineWidth },
  stepText: { fontSize: 12.5 },
  note: { fontSize: 12.5, lineHeight: 18 },
});
