// MapLabels: zone names drawn over the aerial photograph, placed by
// mapLayout.placeLabels (wrapped only at spaces, at most two lines, inside
// the box or just outside it, inside the view, off the pin). Shared by
// LandMap and the zone map so both draw names the same way. Decorative: the
// map's own accessibility label names every zone.

import React from 'react';
import { StyleSheet, Text } from 'react-native';
import { LABEL_STYLE, PlacedLabel } from '../land/mapLayout';

export interface MapLabelsProps {
  labels: PlacedLabel[];
  /** The overlay's width in view pixels. */
  width: number;
  /** From mapInk: the text colour and the halo behind it. */
  ink: { line: string; halo: string };
}

export default function MapLabels({ labels, width, ink }: MapLabelsProps) {
  return (
    <>
      {labels.map((l) => (
        // The rows are already broken at spaces; no fixed width, so the text
        // sizes to its own lines and is never broken inside a word.
        <Text
          key={l.id}
          pointerEvents="none"
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
          style={[styles.label, {
            left: l.left, top: l.top, maxWidth: Math.max(0, width - l.left), color: ink.line,
            fontSize: LABEL_STYLE.fontSize, lineHeight: LABEL_STYLE.lineHeight, textShadowColor: ink.halo,
            // A see-through plate in the halo colour, so an outline that runs
            // behind the name does not strike through it.
            backgroundColor: /^#[0-9a-fA-F]{6}$/.test(ink.halo) ? `${ink.halo}B3` : undefined,
          }]}
        >
          {l.rows.join('\n')}
        </Text>
      ))}
    </>
  );
}

const styles = StyleSheet.create({
  label: {
    position: 'absolute', fontWeight: '700', textShadowRadius: 3, textShadowOffset: { width: 0, height: 1 },
    paddingHorizontal: 3, marginLeft: -3, borderRadius: 4, overflow: 'hidden',
  },
});
