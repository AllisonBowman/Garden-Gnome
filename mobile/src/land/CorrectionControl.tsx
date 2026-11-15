import React, { useMemo, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { Button, Chip, Text, TextInput } from 'react-native-paper';
import { SiteValue } from '../types/site';
import {
  USE_ESTIMATE_LABEL, correctionShowing, parseNumberOverride, publicLine, selectedChoice,
} from './profileRows';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette } from '../theme/tokens';

/**
 * The owner's correction under one site value: tap choices from the
 * server's `override_choices`, or a number field (a soil test). While a
 * correction shows, the public reading stays visible beside it with a way
 * back to it.
 */
export default function CorrectionControl({
  value, busy, onSet, onClear,
}: {
  value: SiteValue;
  busy: boolean;
  onSet: (v: unknown) => void;
  onClear: () => void;
}) {
  const { palette } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette), [palette]);
  const [text, setText] = useState('');
  const [problem, setProblem] = useState<string | null>(null);
  const showing = correctionShowing(value);
  const chosen = selectedChoice(value);
  const pub = publicLine(value);
  const title = value.title || 'this value';

  if (!value.can_override && !showing) return null;

  return (
    <View style={styles.wrap}>
      {pub ? <Text style={styles.public}>{pub}</Text> : null}

      {value.can_override && value.override_kind === 'choice' && value.override_choices.length > 0 ? (
        <View>
          <Text style={styles.ask}>{showing ? 'Change your answer:' : 'Know better? Tap what is true here:'}</Text>
          <View style={styles.chips}>
            {value.override_choices.map((c) => {
              const on = chosen === c.value;
              return (
                <Chip
                  key={c.value}
                  selected={on}
                  showSelectedCheck
                  disabled={busy}
                  onPress={() => { if (!on) onSet(c.value); }}
                  accessibilityLabel={`${title}: ${c.label}. ${on ? 'Your answer.' : 'Tap to set.'}`}
                  accessibilityState={{ selected: on, disabled: busy }}
                  compact
                >
                  {c.label}
                </Chip>
              );
            })}
          </View>
        </View>
      ) : null}

      {value.can_override && value.override_kind === 'number' ? (
        <View>
          <Text style={styles.ask}>
            {value.field === 'soil_ph'
              ? 'Have a soil test? Enter its soil acidity (pH) number.'
              : 'Have a measurement? Enter it.'}
          </Text>
          <View style={styles.numberRow}>
            <TextInput
              mode="outlined"
              dense
              value={text}
              onChangeText={(t) => { setText(t); setProblem(null); }}
              keyboardType="decimal-pad"
              placeholder={value.field === 'soil_ph' ? '6.5' : undefined}
              style={styles.number}
              accessibilityLabel={value.field === 'soil_ph' ? 'Soil acidity (pH) from your soil test' : `${title} you measured`}
            />
            <Button
              mode="outlined"
              disabled={busy || !text.trim()}
              onPress={() => {
                const r = parseNumberOverride(value.field, text);
                if (!r.ok) { setProblem(r.message); return; }
                onSet(r.value);
                setText('');
              }}
              textColor={palette.acc}
              accessibilityLabel={`Save ${title}`}
            >
              Save
            </Button>
          </View>
          {problem ? <Text style={styles.problem}>{problem}</Text> : null}
        </View>
      ) : null}

      {showing ? (
        <Button
          mode="text"
          compact
          disabled={busy}
          onPress={onClear}
          textColor={palette.sub}
          style={styles.clear}
          accessibilityLabel={`${USE_ESTIMATE_LABEL} for ${title}`}
        >
          {USE_ESTIMATE_LABEL}
        </Button>
      ) : null}
    </View>
  );
}

const makeStyles = (p: Palette) => StyleSheet.create({
  wrap: { marginTop: 6, gap: 4 },
  public: { color: p.sub, fontSize: 13, lineHeight: 19, fontStyle: 'italic' },
  ask: { color: p.faint, fontSize: 13, marginBottom: 4 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  numberRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  number: { width: 96 },
  problem: { color: p.warn, fontSize: 13 },
  clear: { alignSelf: 'flex-start' },
});
