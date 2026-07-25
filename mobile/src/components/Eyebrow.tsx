import React from 'react';
import { Text, StyleProp, TextStyle } from 'react-native';
import { useAppTheme } from '../theme/ThemeProvider';

/**
 * A small uppercase, letter-spaced section label in the label font — the
 * "eyebrow" used throughout the design lab (e.g. "YOUR GROWING ENVIRONMENTS",
 * "TODAY'S DETERMINATION"). Defaults to the faint token color.
 */
export default function Eyebrow({
  children,
  color,
  style,
}: {
  children: React.ReactNode;
  color?: string;
  style?: StyleProp<TextStyle>;
}) {
  const { palette, fonts } = useAppTheme();
  return (
    <Text
      style={[
        {
          fontFamily: fonts.label,
          fontSize: 10.5,
          letterSpacing: 1.8,
          textTransform: 'uppercase',
          color: color ?? palette.faint,
        },
        style,
      ]}
    >
      {children}
    </Text>
  );
}
