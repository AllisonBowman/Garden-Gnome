import React, { useState, useMemo } from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { Text, Button } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';

interface Slide {
  emoji: string;
  title: string;
  body: string;
}

// Minimal, calm — three beats of the core loop. Not a SaaS product tour.
const SLIDES: Slide[] = [
  {
    emoji: '🌱',
    title: 'Welcome to PlantAdvocate',
    body: 'A calm home for your plants and the care you give them.',
  },
  {
    emoji: '💧',
    title: 'Add plants, log care',
    body: "Add each plant, then tap to log watering, feeding, and more. PlantAdvocate keeps track so you don't have to.",
  },
  {
    emoji: '🧙',
    title: 'Ask the Gnome',
    body: "Not sure what a plant needs? Ask for advice grounded in its species and its own care history.",
  },
];

interface Props {
  onSkip: () => void;
  onAddPlant: () => void;
}

export default function Onboarding({ onSkip, onAddPlant }: Props) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const [index, setIndex] = useState(0);
  const isLast = index === SLIDES.length - 1;
  const slide = SLIDES[index];

  return (
    <SafeAreaView style={styles.overlay}>
      <View style={styles.skipRow}>
        <Pressable onPress={onSkip} hitSlop={12}>
          <Text style={styles.skip}>Skip</Text>
        </Pressable>
      </View>

      <View style={styles.content}>
        <Text style={styles.emoji}>{slide.emoji}</Text>
        <Text style={styles.title}>{slide.title}</Text>
        <Text style={styles.body}>{slide.body}</Text>
      </View>

      <View style={styles.footer}>
        <View style={styles.dots}>
          {SLIDES.map((_, d) => (
            <View key={d} style={[styles.dot, d === index && styles.dotActive]} />
          ))}
        </View>
        <Button
          mode="contained"
          onPress={isLast ? onAddPlant : () => setIndex((i) => i + 1)}
          style={styles.cta}
          contentStyle={styles.ctaContent}
          buttonColor={palette.btn}
          textColor={palette.btnInk}
        >
          {isLast ? 'Add your first plant' : 'Next'}
        </Button>
        {isLast ? (
          <Pressable onPress={onSkip} hitSlop={8}>
            <Text style={styles.later}>Maybe later</Text>
          </Pressable>
        ) : (
          <View style={styles.laterSpacer} />
        )}
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
  skipRow: { flexDirection: 'row', justifyContent: 'flex-end', padding: 18 },
  skip: { color: p.sub, fontSize: 15, fontWeight: '600' },
  content: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 36 },
  emoji: { fontSize: 72, marginBottom: 28 },
  title: {
    fontSize: 26, fontWeight: '700', color: p.acc, fontFamily: f.display,
    textAlign: 'center', marginBottom: 14,
  },
  body: { fontSize: 16, lineHeight: 24, color: p.sub, textAlign: 'center', maxWidth: 340 },
  footer: { paddingHorizontal: 28, paddingBottom: 28, alignItems: 'center' },
  dots: { flexDirection: 'row', gap: 8, marginBottom: 24 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: p.line },
  dotActive: { backgroundColor: p.acc, width: 22 },
  cta: { borderRadius: 10, alignSelf: 'stretch' },
  ctaContent: { paddingVertical: 8 },
  later: { color: p.sub, fontSize: 15, marginTop: 16 },
  laterSpacer: { height: 31, marginTop: 16 },
});
