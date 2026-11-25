import React, { useMemo } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import ExplainedBlock from '../components/ExplainedBlock';
import { getHowWeKnow } from '../howWeKnow/store';
import { useAppTheme } from '../theme/ThemeProvider';
import { Fonts, Palette } from '../theme/tokens';
import { t } from '../i18n';

/**
 * "How we know": one sheet per screen with the sources, sample and fetch
 * times, method, confidence and disclaimers that used to sit on the face of
 * each value. Presented as a form sheet (App.tsx), so VoiceOver announces
 * it as a sheet and the header's Done closes it.
 */
export default function HowWeKnowScreen() {
  const { palette, fonts, display } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts, display.boldText), [palette, fonts, display.boldText]);
  const sections = getHowWeKnow();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.intro}>{t('howWeKnow.intro')}</Text>
      {sections.length === 0 ? <Text style={styles.line}>{t('howWeKnow.empty')}</Text> : null}
      {sections.map((s) => (
        <View key={s.key} style={styles.section}>
          <Text style={styles.heading} accessibilityRole="header">{s.heading}</Text>
          {s.lines.map((l, i) => <Text key={`${s.key}-l${i}`} style={styles.line}>{l}</Text>)}
          {s.items.map((it, i) => (
            <View key={`${s.key}-i${i}`} style={i > 0 || s.lines.length > 0 ? styles.itemRule : undefined}>
              <ExplainedBlock variant="full" title={it.title} explained={it.explained} />
            </View>
          ))}
        </View>
      ))}
    </ScrollView>
  );
}

const makeStyles = (p: Palette, f: Fonts, bold: boolean) => StyleSheet.create({
  container: { flex: 1, backgroundColor: p.bg },
  content: { padding: 16, paddingBottom: 48 },
  intro: { color: p.ink, fontSize: 16, lineHeight: 23, fontWeight: bold ? '700' : undefined },
  section: {
    marginTop: 16, backgroundColor: p.card, borderRadius: 14, padding: 14,
    borderWidth: 1, borderColor: p.tileBorder,
  },
  heading: {
    color: p.ink, fontFamily: f.display, fontSize: 18, fontWeight: '700', marginBottom: 4,
  },
  line: { color: p.sub, fontSize: 15, lineHeight: 21, marginTop: 6, fontWeight: bold ? '600' : undefined },
  itemRule: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: p.line, marginTop: 6 },
});
