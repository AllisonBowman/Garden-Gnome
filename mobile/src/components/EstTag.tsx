import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { useAppTheme } from '../theme/ThemeProvider';
import { t } from '../i18n';

/**
 * The small mark on an estimated value's face: "est." in words, never a
 * color alone. Its reason and confidence live in the How we know sheet.
 * Decorative to a screen reader: the value's own label says "estimated".
 */
export default function EstTag({ checking = false }: { checking?: boolean }) {
  const { palette, display } = useAppTheme();
  return (
    <View
      importantForAccessibility="no-hide-descendants"
      accessibilityElementsHidden
      style={[styles.tag, { borderColor: palette.tileBorder, backgroundColor: palette.tile }]}
    >
      <Text style={[styles.text, { color: palette.tileInk, fontWeight: display.boldText ? '800' : '600' }]}>
        {checking ? t('howWeKnow.checking') : t('howWeKnow.est')}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  tag: { borderWidth: 1, borderRadius: 6, paddingHorizontal: 5, paddingVertical: 1, alignSelf: 'center' },
  text: { fontSize: 12 },
});
