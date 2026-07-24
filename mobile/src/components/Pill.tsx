import React from 'react';
import { View, Text, StyleProp, ViewStyle } from 'react-native';
import { useAppTheme } from '../theme/ThemeProvider';

export type PillTone = 'neutral' | 'accent' | 'warn' | 'good';

/**
 * A rounded status pill matching the design lab: bordered, with an optional
 * soft tint fill. `tone` sets the color; `filled` adds the soft background
 * (used for the emphatic "● due tomorrow" / "⚠ mist today" chips).
 */
export default function Pill({
  children,
  tone = 'neutral',
  filled = false,
  style,
}: {
  children: React.ReactNode;
  tone?: PillTone;
  filled?: boolean;
  style?: StyleProp<ViewStyle>;
}) {
  const { palette } = useAppTheme();

  const color =
    tone === 'warn' ? palette.warn
    : tone === 'accent' ? palette.acc
    : tone === 'good' ? palette.good
    : palette.sub;
  const borderColor = tone === 'neutral' ? palette.line : color;
  const backgroundColor = !filled
    ? 'transparent'
    : tone === 'warn' ? palette.warnSoft
    : tone === 'accent' ? palette.accSoft
    : palette.card2;

  return (
    <View
      style={[
        {
          alignSelf: 'flex-start',
          borderWidth: tone === 'neutral' ? 1 : 1.5,
          borderColor,
          backgroundColor,
          borderRadius: 999,
          paddingVertical: 3,
          paddingHorizontal: 9,
        },
        style,
      ]}
    >
      <Text style={{ fontSize: 11, fontWeight: '600', color }}>{children}</Text>
    </View>
  );
}
