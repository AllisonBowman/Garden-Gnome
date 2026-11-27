import React from 'react';
import { Pressable, StyleSheet, Text } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation/types';
import { HowWeKnowSection, setHowWeKnow } from '../howWeKnow/store';
import { useAppTheme } from '../theme/ThemeProvider';
import { t } from '../i18n';

/**
 * The one labeled way into a screen's "How we know" sheet. `sections` is
 * called on tap, so it reads what the screen shows at that moment.
 */
export default function HowWeKnowButton({ sections }: { sections: () => HowWeKnowSection[] }) {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { palette, display } = useAppTheme();
  return (
    <Pressable
      onPress={() => { setHowWeKnow(sections()); navigation.navigate('HowWeKnow'); }}
      accessibilityRole="button"
      accessibilityLabel={t('howWeKnow.buttonA11y')}
      accessibilityHint={t('howWeKnow.buttonHint')}
      style={({ pressed }) => [styles.btn, {
        borderColor: palette.tileBorder, backgroundColor: pressed ? palette.desk : palette.tile,
      }]}
    >
      <Text style={[styles.text, { color: palette.tileInk, fontWeight: display.boldText ? '800' : '700' }]}>
        {`🔎 ${t('howWeKnow.button')}`}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  btn: {
    minHeight: 48, borderWidth: 1.5, borderRadius: 12, paddingHorizontal: 16, paddingVertical: 10,
    justifyContent: 'center', alignSelf: 'stretch', marginTop: 18,
  },
  text: { fontSize: 16, textAlign: 'center' },
});
