import React from 'react';
import { Pressable, StyleSheet, Text } from 'react-native';
import { useAppTheme } from '../theme/ThemeProvider';

/** A header button that says what it does in words ("Settings", "Done"),
 *  on a solid fill, at least 44 points tall. */
export function HeaderTextButton({ label, a11yLabel, a11yHint, onPress }: {
  label: string; a11yLabel: string; a11yHint?: string; onPress: () => void;
}) {
  const { palette, display } = useAppTheme();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={a11yLabel}
      accessibilityHint={a11yHint}
      hitSlop={6}
      style={({ pressed }) => [styles.btn, {
        backgroundColor: palette.btnInk, opacity: pressed ? 0.85 : 1,
      }]}
    >
      <Text
        style={[styles.text, { color: palette.btn, fontWeight: display.boldText ? '800' : '700' }]}
        maxFontSizeMultiplier={1.6}
      >
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  btn: { minHeight: 36, minWidth: 44, paddingHorizontal: 12, borderRadius: 18, justifyContent: 'center' },
  text: { fontSize: 16 },
});
