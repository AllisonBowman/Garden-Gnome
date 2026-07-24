import React, { useMemo } from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Button } from 'react-native-paper';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';

interface Props {
  emoji: string;
  title: string;
  body: string;
  actionLabel?: string;
  onAction?: () => void;
}

/** Calm, reusable empty state — a friendly icon, a line of reassurance, and
 *  an optional call to action. Matches the app's low-pressure tone. */
export default function EmptyState({ emoji, title, body, actionLabel, onAction }: Props) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  return (
    <View style={styles.container}>
      <Text style={styles.emoji}>{emoji}</Text>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.body}>{body}</Text>
      {actionLabel && onAction ? (
        <Button
          mode="contained"
          onPress={onAction}
          style={styles.button}
          buttonColor={palette.acc}
          textColor={palette.btnInk}
          contentStyle={styles.buttonContent}
        >
          {actionLabel}
        </Button>
      ) : null}
    </View>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  container: { alignItems: 'center', paddingHorizontal: 32, paddingVertical: 56 },
  emoji: { fontSize: 46, marginBottom: 16 },
  title: { fontSize: 19, fontWeight: '700', color: p.acc, fontFamily: f.display, marginBottom: 8, textAlign: 'center' },
  body: { fontSize: 14.5, lineHeight: 21, color: p.sub, textAlign: 'center', maxWidth: 320 },
  button: { marginTop: 22, borderRadius: 8 },
  buttonContent: { paddingVertical: 4, paddingHorizontal: 8 },
});
