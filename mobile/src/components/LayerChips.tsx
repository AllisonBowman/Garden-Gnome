// LayerChips: the row of chips that switch the layer drawn on the land map
// (map and visuals spec section 1): Aerial, then Sun, Trees and Water as the
// server offers them. A layer that is not ready shows as a dimmed chip and
// one line under the row says why.
//
// Usage:
//
//   const chips = mapChips(layersQ.data);            // land/mapLayers.ts
//   const chosen = chosenChip(chips, wanted);
//   <LayerChips chips={chips} chosen={chosen.key} onChoose={setWanted} />
//
// With only Aerial (an older server) the row is not drawn at all.

import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Chip, Text } from 'react-native-paper';
import { MapChip, MapChipKey, layerStatusLines } from '../land/mapLayers';
import { useAppTheme } from '../theme/ThemeProvider';

export interface LayerChipsProps {
  chips: MapChip[];
  chosen: MapChipKey;
  onChoose: (key: MapChipKey) => void;
  /** Show the "not ready" sentences under the chips (default true). */
  showStatus?: boolean;
}

export default function LayerChips({ chips, chosen, onChoose, showStatus = true }: LayerChipsProps) {
  const { palette } = useAppTheme();
  if (chips.length <= 1) return null;
  const lines = showStatus ? layerStatusLines(chips) : [];
  return (
    <View style={styles.wrap}>
      <View style={styles.row} accessibilityRole="radiogroup" accessibilityLabel="Map layer">
        {chips.map((c) => {
          const on = c.key === chosen;
          return (
            <Chip
              key={c.key}
              selected={on}
              showSelectedCheck
              compact
              disabled={!c.enabled}
              onPress={() => onChoose(c.key)}
              accessibilityRole="radio"
              accessibilityLabel={`${c.a11y} ${on ? 'Selected' : 'Not selected'}.`}
              accessibilityState={{ selected: on, disabled: !c.enabled }}
              style={styles.chip}
            >
              {c.label}
            </Chip>
          );
        })}
      </View>
      {lines.map((l) => (
        <Text key={l} style={[styles.status, { color: palette.sub }]}>{l}</Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { marginTop: 8 },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  chip: { minHeight: 44, justifyContent: 'center' },
  status: { fontSize: 12.5, lineHeight: 18, marginTop: 4 },
});
