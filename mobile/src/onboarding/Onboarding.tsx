import React, { useState, useMemo } from 'react';
import { View, StyleSheet, Pressable, ScrollView } from 'react-native';
import { Text, Button } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { NavigationProp, useNavigation } from '@react-navigation/native';
import type { RootStackParamList } from '../navigation/types';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import { FINISH, SLIDES } from './slides';
import { t } from '../i18n';

interface Props {
  /** Marks onboarding as seen and hides it. */
  onSkip: () => void;
}

export default function Onboarding({ onSkip }: Props) {
  // Rendered inside the NavigationContainer but outside the stack, so this is
  // the container's own navigation object.
  const navigation = useNavigation<NavigationProp<RootStackParamList>>();
  const finish = () => {
    onSkip();
    navigation.navigate(FINISH.route);
  };
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const [index, setIndex] = useState(0);
  const isLast = index === SLIDES.length - 1;
  const slide = SLIDES[index];

  return (
    <SafeAreaView style={styles.overlay}>
      <View style={styles.skipRow}>
        <Pressable onPress={onSkip} hitSlop={12} accessibilityRole="button" style={styles.skipBtn}>
          <Text style={styles.skip}>{t('onboarding.skip')}</Text>
        </Pressable>
      </View>

      <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
        <Text style={styles.emoji} accessibilityElementsHidden importantForAccessibility="no">{slide.emoji}</Text>
        <Text style={styles.title} accessibilityRole="header">{slide.title}</Text>
        <Text style={styles.body}>{slide.body}</Text>
      </ScrollView>

      <View style={styles.footer}>
        <View style={styles.dots} accessible accessibilityLabel={t('onboarding.slideOf', { n: index + 1, total: SLIDES.length })}>
          {SLIDES.map((_, d) => (
            <View key={d} style={[styles.dot, d === index && styles.dotActive]} />
          ))}
        </View>
        <Button
          mode="contained"
          onPress={isLast ? finish : () => setIndex((i) => i + 1)}
          style={styles.cta}
          contentStyle={styles.ctaContent}
          buttonColor={palette.btn}
          textColor={palette.btnInk}
        >
          {isLast ? FINISH.label : t('onboarding.next')}
        </Button>
        {/* The last button already ends onboarding on Home, so no second
            "Maybe later" link that would do the same; Skip stays at the top. */}
        <View style={styles.laterSpacer} />
      </View>
    </SafeAreaView>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  overlay: {
    position: 'absolute',
    top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: p.bg,
    zIndex: 100,
    elevation: 100,
    justifyContent: 'space-between',
  },
  scroll: { flex: 1 },
  skipRow: { flexDirection: 'row', justifyContent: 'flex-end', padding: 18 },
  skipBtn: { minHeight: 44, minWidth: 44, justifyContent: 'center', paddingHorizontal: 8 },
  skip: { color: p.ink, fontSize: 16, fontWeight: '700' },
  content: { flexGrow: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 28 },
  emoji: { fontSize: 72, marginBottom: 28 },
  title: {
    fontSize: 26, fontWeight: '700', color: p.acc, fontFamily: f.display,
    textAlign: 'center', marginBottom: 14,
  },
  body: { fontSize: 17, lineHeight: 25, color: p.ink, textAlign: 'center', maxWidth: 360 },
  footer: { paddingHorizontal: 28, paddingBottom: 28, alignItems: 'center' },
  dots: { flexDirection: 'row', gap: 8, marginBottom: 24 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: p.line },
  dotActive: { backgroundColor: p.acc, width: 22 },
  cta: { borderRadius: 10, alignSelf: 'stretch' },
  ctaContent: { paddingVertical: 8 },
  laterSpacer: { height: 31, marginTop: 16 },
});
