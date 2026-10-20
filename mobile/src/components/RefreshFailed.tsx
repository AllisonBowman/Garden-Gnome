import React, { useMemo } from 'react';
import { StyleProp, StyleSheet, View, ViewStyle } from 'react-native';
import { Button, Text } from 'react-native-paper';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette } from '../theme/tokens';
import { REFRESH_FAILED } from '../care/loadFailed';

interface Props {
  onRetry: () => void;
  /** True while the retry is running, so a second tap can't stack another. */
  retrying?: boolean;
  /** Where it sits: padding to line it up with the screen's content. */
  style?: StyleProp<ViewStyle>;
}

/**
 * One quiet line over content a screen kept when a refresh behind it failed.
 *
 * The app asks again whenever it comes back to the foreground, which is
 * often somewhere with no signal. The plant, species or area already on
 * screen stays there; this says it may be out of date, and offers to ask
 * again, without taking the screen over the way a failed first load does.
 */
export default function RefreshFailed({ onRetry, retrying = false, style }: Props) {
  const { palette } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette), [palette]);
  return (
    <View style={[styles.row, style]}>
      <Text style={styles.line}>{REFRESH_FAILED.line}</Text>
      <Button
        compact
        mode="text"
        onPress={onRetry}
        loading={retrying}
        disabled={retrying}
        textColor={palette.acc}
      >
        {REFRESH_FAILED.action}
      </Button>
    </View>
  );
}

const makeStyles = (p: Palette) => StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', marginBottom: 8, gap: 4 },
  line: { flexShrink: 1, color: p.sub, fontSize: 13, lineHeight: 18 },
});
