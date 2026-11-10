import React from 'react';
import { StyleProp, StyleSheet, TextStyle } from 'react-native';
import { Text } from 'react-native-paper';
import { NOT_ADVICE_LINE } from '../care/notAdvice';
import { useAppTheme } from '../theme/ThemeProvider';

/**
 * The not-advice line, shown under a hazard sentence in the muted note style
 * the status line and the "not yet cited" caption use. One component, so the
 * screens that show a hazard sentence can't drift apart on the wording; each
 * passes only its own spacing.
 */
export default function NotAdviceNote({ style }: { style?: StyleProp<TextStyle> }) {
  const { palette } = useAppTheme();
  return (
    <Text variant="bodySmall" style={[styles.note, { color: palette.sub }, style]}>
      {NOT_ADVICE_LINE}
    </Text>
  );
}

const styles = StyleSheet.create({
  note: { lineHeight: 18 },
});
