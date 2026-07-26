import React, { useMemo } from 'react';
import { Pressable, StyleSheet, Linking, StyleProp, ViewStyle } from 'react-native';
import { Text } from 'react-native-paper';
import { WeatherAttribution } from '../types';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette } from '../theme/tokens';

// The Apple Weather credit. WeatherKit's terms require it wherever its data is
// displayed — which includes advice that restates the forecast in words, not
// only a temperature readout.
//
// One component rather than markup copied per screen: this is a compliance
// element, so the failure mode of a divergent copy is a missing credit on the
// screen nobody thought to check.

/** Fallback if the server ever sends an empty label. The API supplies
 *  " Weather" (the Apple logo glyph); it renders as a blank box on a device
 *  without the glyph, so never show the raw string alone. */
const FALLBACK = 'Weather';

export default function WeatherCredit({
  attribution, style,
}: {
  attribution: WeatherAttribution | null | undefined;
  style?: StyleProp<ViewStyle>;
}) {
  const { palette } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette), [palette]);

  // No attribution means no weather data was used — showing the credit anyway
  // would claim a source that did not contribute.
  if (!attribution) return null;

  const label = attribution.text?.trim() || FALLBACK;
  const url = attribution.url;

  return (
    <Pressable
      onPress={() => url && void Linking.openURL(url)}
      disabled={!url}
      style={[styles.wrap, style]}
      accessibilityRole="link"
      accessibilityLabel={`${label}. Opens Apple's weather data legal attribution.`}
    >
      <Text style={styles.text}>{label}{url ? ' ›' : ''}</Text>
    </Pressable>
  );
}

const makeStyles = (p: Palette) => StyleSheet.create({
  // 44px min target: the credit is a link, and Apple's own guidance applies to
  // it like any other tappable row.
  wrap: { alignSelf: 'flex-start', minHeight: 44, justifyContent: 'center' },
  text: { fontSize: 12, color: p.faint },
});
