import React, { useMemo } from 'react';
import { Linking, Pressable, StyleProp, StyleSheet, View, ViewStyle } from 'react-native';
import { Text } from 'react-native-paper';
import { Explained } from '../types/site';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import ConfidenceChip from './ConfidenceChip';
import EstTag from './EstTag';
import { disclosureLines, faceA11yLabel, faceDisplay, faceMark, localConfidenceLabel } from './explainedText';
import { t } from '../i18n';

interface Props {
  explained: Explained;
  /** A short name for the value ("Sun", "Soil"), shown before it. */
  title?: string;
  /** Tap on the value itself (opens it where it can be changed). */
  onPress?: () => void;
  /**
   * `face` (the default) is what a screen shows: the value in one plain line
   * and a small "est." or "Checking" mark. `full` is the How we know sheet:
   * the value, how sure it is, the reason, and every source. Nothing is
   * dropped between the two; the face's justification lives in the sheet.
   */
  variant?: 'face' | 'full';
  /** Something the owner can do here, such as a correction, under the value.
   *  Corrections are controls, so they stay on the face. */
  children?: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

/**
 * One explained value. Used for site values, seasonal events, map layers
 * and the vitals cards, so every value reads the same way: on the screen,
 * the value; behind "How we know", why and from where.
 */
export default function ExplainedBlock({
  explained, title, onPress, variant = 'face', children, style,
}: Props) {
  const { palette, fonts, display } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts, display.boldText), [palette, fonts, display.boldText]);

  if (variant === 'full') {
    const lines = disclosureLines(explained);
    return (
      <View style={[styles.wrap, style]}>
        <View accessible accessibilityLabel={[title, explained.display].filter(Boolean).join('. ')}>
          {title ? <Text style={styles.title}>{title}</Text> : null}
          <Text style={styles.display}>{explained.display}</Text>
        </View>
        <View style={styles.sureRow}>
          <Text style={styles.reason}>{t('howWeKnow.howSureLead')}</Text>
          <ConfidenceChip
            confidence={explained.confidence}
            label={localConfidenceLabel(explained.confidence_label, explained.confidence)}
          />
        </View>
        {lines.reason ? <Text style={styles.reason}>{lines.reason}</Text> : null}
        {explained.sources.length > 0
          ? explained.sources.map((s, i) => (
            <Text
              key={`${s.name}-${i}`}
              style={styles.source}
              onPress={s.url ? () => void Linking.openURL(s.url!) : undefined}
              accessibilityRole={s.url ? 'link' : 'text'}
            >
              {`${t('land.dataLine', { source: lines.sources[i] })}${s.url ? ' ›' : ''}`}
            </Text>
          ))
          : <Text style={styles.source}>{lines.sources[0]}</Text>}
        {children}
      </View>
    );
  }

  const mark = faceMark(explained.confidence);
  const head = (
    <View style={styles.head}>
      <View style={styles.headText}>
        {title ? <Text style={styles.title}>{title}</Text> : null}
        <Text style={styles.display}>{faceDisplay(explained)}</Text>
      </View>
      {mark ? <EstTag checking={mark === 'checking'} /> : null}
    </View>
  );

  return (
    <View style={[styles.wrap, style]}>
      {onPress ? (
        <Pressable
          onPress={onPress}
          accessibilityRole="button"
          accessibilityLabel={faceA11yLabel(title, explained)}
          accessibilityHint={t('land.opensDetails')}
          style={styles.pressable}
        >
          {head}
        </Pressable>
      ) : (
        <View accessible accessibilityLabel={faceA11yLabel(title, explained)}>
          {head}
        </View>
      )}
      {children}
    </View>
  );
}

const makeStyles = (p: Palette, f: Fonts, bold: boolean) => StyleSheet.create({
  wrap: { paddingVertical: 6 },
  pressable: { minHeight: 44, justifyContent: 'center' },
  head: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, flexWrap: 'wrap' },
  headText: { flex: 1, minWidth: 160 },
  title: { color: p.faint, fontFamily: f.label, fontSize: 13, marginBottom: 1, fontWeight: bold ? '700' : undefined },
  display: { color: p.ink, fontSize: 16, lineHeight: 22, fontWeight: bold ? '700' : undefined },
  sureRow: { flexDirection: 'row', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginTop: 6 },
  reason: { color: p.sub, fontSize: 14, lineHeight: 20, marginTop: 4 },
  source: { color: p.sub, fontSize: 13.5, lineHeight: 19, marginTop: 4 },
});
