import React, { useMemo, useState } from 'react';
import { View, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import {
  Text, Card, IconButton, ActivityIndicator, Snackbar,
} from 'react-native-paper';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { logCare } from '../api/plants';
import { CareType } from '../types';
import { rescheduleAllReminders } from '../notifications/reminders';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import { useCareTasks, CARE_TASKS_QUERY_KEY } from './useCareTasks';
import { careTaskDueLabel } from './schedule';
import { CARE_PRESENTATION } from './labels';

// The "what needs doing right now" list at the top of the Plants tab: every
// plant × care-type that is overdue or due today, most-overdue first. Checking
// a row logs that care (which re-anchors its schedule, so the row clears) and
// deep-links into the plant. Upcoming care is intentionally NOT shown here —
// that lives on the environment calendar; this list stays a short, honest
// "do these today".
export default function CareTodos({
  onOpenPlant,
}: {
  onOpenPlant: (plantId: number) => void;
}) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const queryClient = useQueryClient();
  const { tasks, isLoading } = useCareTasks();
  const [doneMsg, setDoneMsg] = useState<string | null>(null);
  const [pendingKey, setPendingKey] = useState<string | null>(null);

  const todos = useMemo(
    () => tasks
      .filter((t) => t.status === 'overdue' || t.status === 'due')
      .sort((a, b) => a.daysUntilDue - b.daysUntilDue),
    [tasks],
  );

  const logMutation = useMutation({
    mutationFn: ({ plantId, careType }: { plantId: number; careType: CareType; key: string }) =>
      logCare(plantId, careType),
    onMutate: ({ key }) => setPendingKey(key),
    onSuccess: (_data, { careType, plantId }) => {
      queryClient.invalidateQueries({ queryKey: CARE_TASKS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ['careLogs', plantId] });
      queryClient.invalidateQueries({ queryKey: ['plants'] });
      const p = CARE_PRESENTATION[careType];
      setDoneMsg(`${p.icon} ${p.verb}ed — logged and rescheduled`);
      void rescheduleAllReminders(); // keep notifications in step with the log
    },
    onError: () => Alert.alert('Error', 'Could not log that care action.'),
    onSettled: () => setPendingKey(null),
  });

  // While the first load is in flight, render nothing — StreakBadges sits above
  // this and the plant list below, so a spinner here would just jitter layout.
  if (isLoading) return null;

  // Empty garden (no scheduled care at all) → let the screen's own empty state
  // speak; don't stack an "all caught up" on top of "your garden's empty".
  if (tasks.length === 0) return null;

  if (todos.length === 0) {
    return (
      <Card style={styles.caughtUpCard} mode="contained">
        <Card.Content style={styles.caughtUpContent}>
          <Text style={styles.caughtUpText}>🌿 All caught up — nothing due today.</Text>
        </Card.Content>
      </Card>
    );
  }

  return (
    <>
      <Card style={styles.card} mode="elevated">
        <Card.Title
          title="To-do today"
          titleVariant="titleMedium"
          titleStyle={styles.cardTitle}
          right={() => (
            <View style={styles.countPill}>
              <Text style={styles.countPillText}>{todos.length}</Text>
            </View>
          )}
        />
        <Card.Content style={styles.list}>
          {todos.map((t) => {
            const key = `${t.plantId}-${t.careType}`;
            const p = CARE_PRESENTATION[t.careType];
            const busy = pendingKey === key;
            return (
              <View key={key} style={styles.row}>
                <TouchableOpacity
                  style={styles.rowMain}
                  activeOpacity={0.6}
                  onPress={() => onOpenPlant(t.plantId)}
                >
                  <Text style={styles.rowEmoji}>{p.icon}</Text>
                  <View style={styles.rowText}>
                    <Text style={styles.rowTitle}>{p.verb} {t.nickname}</Text>
                    <Text style={[
                      styles.rowWhen,
                      t.status === 'overdue' && { color: palette.warn },
                    ]}>
                      {careTaskDueLabel(t)}
                    </Text>
                  </View>
                </TouchableOpacity>
                {busy ? (
                  <ActivityIndicator style={styles.rowCheck} size={20} color={palette.acc} />
                ) : (
                  <IconButton
                    icon="check-circle-outline"
                    size={26}
                    iconColor={palette.good}
                    style={styles.rowCheck}
                    disabled={pendingKey !== null}
                    onPress={() => logMutation.mutate({ plantId: t.plantId, careType: t.careType, key })}
                    accessibilityLabel={`Mark ${p.verb} ${t.nickname} done`}
                  />
                )}
              </View>
            );
          })}
        </Card.Content>
      </Card>
      <Snackbar
        visible={doneMsg !== null}
        onDismiss={() => setDoneMsg(null)}
        duration={2200}
        style={styles.snackbar}
      >
        <Text style={styles.snackbarText}>{doneMsg}</Text>
      </Snackbar>
    </>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  card: { marginBottom: 12, borderRadius: 12 },
  cardTitle: { color: p.acc, fontFamily: f.display },
  list: { gap: 2, paddingBottom: 8 },
  row: {
    flexDirection: 'row', alignItems: 'center',
    borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: p.line2,
  },
  rowMain: {
    flex: 1, flexDirection: 'row', alignItems: 'center', gap: 10,
    paddingVertical: 8,
  },
  rowEmoji: { fontSize: 20 },
  rowText: { flex: 1 },
  rowTitle: { fontSize: 15, color: p.ink },
  rowWhen: { fontSize: 12, color: p.sub, marginTop: 1, fontWeight: '600' },
  rowCheck: { margin: 0 },

  countPill: {
    backgroundColor: p.acc, borderRadius: 999,
    minWidth: 24, paddingHorizontal: 7, paddingVertical: 2, marginRight: 16,
    alignItems: 'center', justifyContent: 'center',
  },
  countPillText: { color: p.btnInk, fontWeight: '700', fontSize: 13 },

  caughtUpCard: { marginBottom: 12, borderRadius: 12, backgroundColor: p.accSoft },
  caughtUpContent: { paddingVertical: 12 },
  caughtUpText: { color: p.sub, fontSize: 14, textAlign: 'center' },

  snackbar: { backgroundColor: p.acc },
  snackbarText: { color: p.btnInk },
});
