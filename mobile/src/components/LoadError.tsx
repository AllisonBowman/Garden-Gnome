import React, { useMemo } from 'react';
import { StyleSheet, View } from 'react-native';
import { Button, Text } from 'react-native-paper';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';

interface Props {
  /** What failed, in the caretaker's words, and what to do about it:
   *  "Couldn't load your plants. Check your connection and try again." */
  message: string;
  onRetry: () => void;
  /** True while the retry is running, so a second tap can't stack another. */
  retrying?: boolean;
  /** Sit inside a form instead of filling the screen. */
  inline?: boolean;
}

/**
 * A failed load, said plainly, with a way out.
 *
 * Every first load can fail: no signal, or a server that scaled to zero and
 * is still waking up. An endless spinner or an empty list in its place
 * strands the person (or tells them they have no growing areas when they do),
 * so each screen that loads something shows this instead, with a button that
 * asks again.
 */
export default function LoadError({ message, onRetry, retrying = false, inline = false }: Props) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  return (
    <View style={inline ? styles.inline : styles.screen}>
      <Text style={[styles.message, inline && styles.messageInline]}>{message}</Text>
      <Button
        mode="outlined"
        icon="refresh"
        onPress={onRetry}
        loading={retrying}
        disabled={retrying}
        style={inline ? styles.buttonInline : styles.button}
        textColor={palette.acc}
      >
        Try again
      </Button>
    </View>
  );
}

const makeStyles = (p: Palette, _f: Fonts) => StyleSheet.create({
  screen: {
    flex: 1, justifyContent: 'center', alignItems: 'center',
    padding: 24, backgroundColor: p.bg,
  },
  inline: { marginVertical: 6 },
  message: {
    color: p.warn, textAlign: 'center', fontSize: 15, lineHeight: 22, maxWidth: 320,
  },
  messageInline: { textAlign: 'left', fontSize: 13, lineHeight: 19, maxWidth: undefined },
  button: { marginTop: 14, borderRadius: 8 },
  buttonInline: { alignSelf: 'flex-start', marginTop: 6, borderRadius: 8 },
});
