import React, { useMemo, useState } from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { Text, IconButton } from 'react-native-paper';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import { CareTask, dayKey, startOfDay, careTaskDueLabel } from './schedule';
import { careActionLabel } from './labels';

const WEEKDAYS = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

type Cell = { date: Date; key: string } | null;

function monthCells(year: number, month: number): Cell[] {
  const startWeekday = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: Cell[] = [];
  for (let i = 0; i < startWeekday; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) {
    const date = new Date(year, month, d);
    cells.push({ date, key: dayKey(date) });
  }
  return cells;
}

/**
 * A month grid of a plant collection's next-due care. Each plant × care-type
 * marks its single next-due day (the app never fabricates a recurring series —
 * real intervals depend on when care is actually logged). Overdue tasks land on
 * their real past day and are also totalled in the banner so nothing hides off
 * the top of the calendar. `tasks` must already be scoped by the caller.
 */
export default function CareCalendar({ tasks }: { tasks: CareTask[] }) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);

  const today = startOfDay(new Date());
  const [view, setView] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1));
  const [selectedKey, setSelectedKey] = useState<string>(dayKey(today));

  const tasksByDay = useMemo(() => {
    const map = new Map<string, CareTask[]>();
    for (const t of tasks) {
      const k = dayKey(t.dueDate);
      const list = map.get(k);
      if (list) list.push(t); else map.set(k, [t]);
    }
    return map;
  }, [tasks]);

  const overdueCount = useMemo(
    () => tasks.filter((t) => t.status === 'overdue').length,
    [tasks],
  );

  const cells = useMemo(
    () => monthCells(view.getFullYear(), view.getMonth()),
    [view],
  );

  const shiftMonth = (delta: number) =>
    setView((v) => new Date(v.getFullYear(), v.getMonth() + delta, 1));

  const selected = tasksByDay.get(selectedKey) ?? [];
  const selectedIsToday = selectedKey === dayKey(today);

  return (
    <View>
      {/* Month header + nav */}
      <View style={styles.navRow}>
        <IconButton icon="chevron-left" size={22} onPress={() => shiftMonth(-1)} iconColor={palette.acc} />
        <Text style={styles.monthLabel}>
          {MONTHS[view.getMonth()]} {view.getFullYear()}
        </Text>
        <IconButton icon="chevron-right" size={22} onPress={() => shiftMonth(1)} iconColor={palette.acc} />
      </View>

      {overdueCount > 0 && (
        <TouchableOpacity
          style={styles.overdueBanner}
          activeOpacity={0.8}
          onPress={() => {
            setView(new Date(today.getFullYear(), today.getMonth(), 1));
            setSelectedKey(dayKey(today));
          }}
        >
          <Text style={styles.overdueBannerText}>
            ⚠️ {overdueCount} care {overdueCount === 1 ? 'task is' : 'tasks are'} overdue
          </Text>
        </TouchableOpacity>
      )}

      {/* Weekday labels */}
      <View style={styles.weekRow}>
        {WEEKDAYS.map((w, i) => (
          <Text key={i} style={styles.weekday}>{w}</Text>
        ))}
      </View>

      {/* Day grid */}
      <View style={styles.grid}>
        {cells.map((cell, i) => {
          if (!cell) return <View key={`b${i}`} style={styles.cell} />;
          const dayTasks = tasksByDay.get(cell.key) ?? [];
          const isToday = cell.key === dayKey(today);
          const isSelected = cell.key === selectedKey;
          const hasOverdue = dayTasks.some((t) => t.status === 'overdue');
          const dotColor = hasOverdue ? palette.warn : palette.acc;
          return (
            <TouchableOpacity
              key={cell.key}
              style={styles.cell}
              activeOpacity={dayTasks.length ? 0.6 : 1}
              onPress={() => setSelectedKey(cell.key)}
            >
              <View style={[
                styles.dayInner,
                isSelected && styles.daySelected,
                isToday && !isSelected && styles.dayToday,
              ]}>
                <Text style={[
                  styles.dayNum,
                  isSelected && styles.dayNumSelected,
                ]}>
                  {cell.date.getDate()}
                </Text>
                {dayTasks.length > 0 && (
                  <View style={[styles.dot, { backgroundColor: isSelected ? palette.btnInk : dotColor }]}>
                    {dayTasks.length > 1 && (
                      <Text style={[styles.dotCount, { color: isSelected ? palette.acc : palette.btnInk }]}>
                        {dayTasks.length}
                      </Text>
                    )}
                  </View>
                )}
              </View>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Selected-day agenda */}
      <View style={styles.agenda}>
        <Text style={styles.agendaTitle}>
          {selectedIsToday ? 'Today' : formatSelected(selectedKey)}
        </Text>
        {selected.length === 0 ? (
          <Text style={styles.agendaEmpty}>Nothing scheduled.</Text>
        ) : (
          selected
            .slice()
            .sort((a, b) => a.daysUntilDue - b.daysUntilDue)
            .map((t, i) => (
              <View key={`${t.plantId}-${t.careType}-${i}`} style={styles.agendaRow}>
                <Text style={styles.agendaAction}>
                  {careActionLabel(t.careType, t.nickname)}
                </Text>
                <Text style={[
                  styles.agendaWhen,
                  t.status === 'overdue' && { color: palette.warn },
                ]}>
                  {careTaskDueLabel(t)}
                </Text>
              </View>
            ))
        )}
      </View>
    </View>
  );
}

function formatSelected(key: string): string {
  const [y, m, d] = key.split('-').map(Number);
  return new Date(y, m, d).toLocaleDateString(undefined, {
    weekday: 'short', month: 'short', day: 'numeric',
  });
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  navRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  monthLabel: { fontSize: 17, fontWeight: '700', color: p.ink, fontFamily: f.display },

  overdueBanner: {
    backgroundColor: p.warnSoft, borderRadius: 8,
    paddingVertical: 8, paddingHorizontal: 12, marginBottom: 10,
  },
  overdueBannerText: { color: p.warn, fontSize: 13, fontWeight: '600' },

  weekRow: { flexDirection: 'row', marginBottom: 4 },
  weekday: {
    width: `${100 / 7}%`, textAlign: 'center',
    fontSize: 11, fontWeight: '700', color: p.faint,
  },

  grid: { flexDirection: 'row', flexWrap: 'wrap' },
  cell: { width: `${100 / 7}%`, aspectRatio: 1, padding: 2 },
  dayInner: {
    flex: 1, borderRadius: 8, alignItems: 'center', justifyContent: 'center',
    gap: 2,
  },
  daySelected: { backgroundColor: p.acc },
  dayToday: { borderWidth: 1, borderColor: p.acc },
  dayNum: { fontSize: 14, color: p.ink, fontFamily: f.numeric },
  dayNumSelected: { color: p.btnInk, fontWeight: '700' },
  dot: {
    minWidth: 6, height: 6, borderRadius: 3, paddingHorizontal: 2,
    alignItems: 'center', justifyContent: 'center',
  },
  dotCount: { fontSize: 8, fontWeight: '700', lineHeight: 10 },

  agenda: {
    marginTop: 12, borderTopWidth: 1, borderTopColor: p.line2, paddingTop: 12,
  },
  agendaTitle: { fontSize: 13, fontWeight: '700', color: p.sub, marginBottom: 8 },
  agendaEmpty: { color: p.faint, fontStyle: 'italic', fontSize: 13 },
  agendaRow: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: 6, gap: 12,
  },
  agendaAction: { color: p.ink, fontSize: 14, flexShrink: 1 },
  agendaWhen: { color: p.sub, fontSize: 12, fontWeight: '600' },
});
