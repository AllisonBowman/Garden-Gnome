import React, { useMemo, useState } from 'react';
import { Pressable, StyleProp, StyleSheet, View, ViewStyle, Linking } from 'react-native';
import { Text } from 'react-native-paper';
import { Explained } from '../types/site';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import ConfidenceChip from './ConfidenceChip';
import { WHY_LABEL, disclosureLines, explainedA11yLabel, localConfidenceLabel } from './explainedText';
import { t } from '../i18n';

interface Props {
  explained: Explained;
  /** A short name for the value ("Sun", "Soil"), shown before it. */
  title?: string;
  /** Tap on the value itself (Home's land lines open Land). The disclosure
   *  stays its own control. */
  onPress?: () => void;
  /** Start with the reason and sources showing. */
  initiallyOpen?: boolean;
  /** Something the owner can do here, such as a correction, under the value. */
  children?: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

/**
 * One explained value: the sentence, how sure it is, and a "Why and data
 * source" disclosure that shows the reason and every source. Used for site
 * values, seasonal events and tasks, and the vitals cards, so every value in
 * the app explains itself the same way.
 */
export default function ExplainedBlock({
  explained, title, onPress, initiallyOpen = false, children, style,
}: Props) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const [open, setOpen] = useState(initiallyOpen);
  const lines = disclosureLines(explained);

  const head = (
    <View style={styles.head}>
      <View style={styles.headText}>
        {title ? <Text style={styles.title}>{title}</Text> : null}
        <Text style={styles.display}>{explained.display}</Text>
      </View>
      <ConfidenceChip
        confidence={explained.confidence}
        label={localConfidenceLabel(explained.confidence_label, explained.confidence)}
        style={styles.chip}
      />
    </View>
  );

  return (
    <View style={[styles.wrap, style]}>
      {onPress ? (
        <Pressable
          onPress={onPress}
          accessibilityRole="button"
          accessibilityLabel={explainedA11yLabel(title, explained)}
          accessibilityHint={t('land.opensDetails')}
        >
          {head}
        </Pressable>
      ) : (
        <View accessible accessibilityLabel={explainedA11yLabel(title, explained)}>
          {head}
        </View>
      )}
      {children}
      <Pressable
        onPress={() => setOpen((o) => !o)}
        accessibilityRole="button"
        accessibilityState={{ expanded: open }}
        accessibilityLabel={t(open ? 'land.whyHide' : 'land.whyShow', { why: WHY_LABEL })}
        hitSlop={8}
        style={styles.toggle}
      >
        <Text style={styles.toggleText}>{`${open ? '▾' : '▸'} ${WHY_LABEL}`}</Text>
      </Pressable>
      {open && (
        <View style={styles.detail}>
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
        </View>
      )}
    </View>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  wrap: { paddingVertical: 6 },
  head: { flexDirection: 'row', alignItems: 'flex-start', gap: 8 },
  headText: { flex: 1 },
  title: { color: p.faint, fontFamily: f.label, fontSize: 12, marginBottom: 1 },
  display: { color: p.ink, fontSize: 15, lineHeight: 21 },
  chip: { marginTop: 2 },
  toggle: { alignSelf: 'flex-start', marginTop: 4, minHeight: 28, justifyContent: 'center' },
  toggleText: { color: p.acc, fontSize: 13, fontWeight: '600' },
  detail: {
    marginTop: 4, paddingLeft: 10, borderLeftWidth: 2, borderLeftColor: p.line, gap: 4,
  },
  reason: { color: p.sub, fontSize: 13, lineHeight: 19 },
  source: { color: p.faint, fontSize: 12.5, lineHeight: 18 },
});
