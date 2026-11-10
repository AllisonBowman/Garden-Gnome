import React, { useMemo, useState } from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { Text, Card, Divider, ActivityIndicator } from 'react-native-paper';
import { readablePlants } from '../api/plants';
import { useGardenCareData } from '../care/useCareTasks';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import Eyebrow from '../components/Eyebrow';
import {
  computeStreak, computeMetrics, computeBadges, Badge,
} from './streaks';

/**
 * Derives the household care streak and badges from existing care-log data
 * (no backend storage). Reads the same shared load as the to-do list and the
 * reminder planner (useGardenCareData), so the badges cost no requests of
 * their own.
 */
function useStreakBadges() {
  const { data, isLoading } = useGardenCareData();

  // Memoized because computeStreak walks up to a year of days against every
  // plant × care type. On a shelf of five that is nothing; on a garden it is
  // millions of operations, and without this it re-ran on every render —
  // including the pure-UI one that fires when a badge is tapped. A plant whose
  // log couldn't be read is left out rather than counted as never cared for.
  const derived = useMemo(() => {
    if (!data) return null;
    const plants = readablePlants(data);
    const streak = computeStreak({
      plants, logsByPlant: data.logsByPlant, speciesById: data.speciesById,
    });
    const badges = computeBadges(computeMetrics(plants, data.logsByPlant, streak.best));
    return { streak, badges };
  }, [data]);

  const plants = data?.plants;
  if (!plants || !derived) {
    return { loading: isLoading, hasPlants: !!plants?.length, streak: null, badges: [] as Badge[] };
  }
  return {
    loading: false,
    hasPlants: plants.length > 0,
    streak: derived.streak,
    badges: derived.badges,
  };
}

export default function StreakBadges() {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const { loading, hasPlants, streak, badges } = useStreakBadges();
  const [selected, setSelected] = useState<Badge | null>(null);

  if (loading) {
    return <ActivityIndicator style={styles.loading} color={palette.acc} />;
  }
  if (!hasPlants || !streak) return null; // nothing to celebrate yet

  const earnedCount = badges.filter((b) => b.earned).length;

  return (
    <Card style={styles.card} mode="elevated">
      <Card.Content>
        {/* Streak */}
        <View style={styles.streakRow}>
          <Text style={styles.streakEmoji}>{streak.current > 0 ? '🌿' : '🌱'}</Text>
          <View style={styles.streakText}>
            {streak.current > 0 ? (
              <>
                <Text style={styles.streakNum}>
                  {streak.current}-day care streak
                </Text>
                <Text style={styles.streakSub}>
                  {streak.best > streak.current
                    ? `Your best is ${streak.best} days — keep it going.`
                    : 'Every plant is on track. Nice work.'}
                </Text>
              </>
            ) : streak.behindCount > 0 && streak.trackedCount > 1 ? (
              // With more than a couple of plants something is nearly always a
              // day late, so "no streak" would be the permanent state and would
              // read as a scolding. Show how much of the garden IS in hand —
              // that number moves when the caretaker does something, which is
              // the whole point of showing it.
              <>
                <Text style={styles.streakNum}>
                  {streak.onTrackPct}% of your garden is on track
                </Text>
                <Text style={styles.streakSub}>
                  {streak.behindCount === 1
                    ? 'One planting is past its window — it’s in your to-dos.'
                    : `${streak.behindCount} plantings are past their window — they’re in your to-dos.`}
                </Text>
              </>
            ) : (
              <>
                <Text style={styles.streakNum}>No active streak</Text>
                <Text style={styles.streakSub}>
                  A little care gets one going — no pressure.
                </Text>
              </>
            )}
          </View>
        </View>

        <Divider style={styles.divider} />

        {/* Badges */}
        <Eyebrow style={styles.badgesHeading}>Badges · {earnedCount} of {badges.length}</Eyebrow>
        <View style={styles.badgeGrid}>
          {badges.map((b) => (
            <Pressable
              key={b.id}
              onPress={() => setSelected((cur) => (cur?.id === b.id ? null : b))}
              style={[styles.badge, selected?.id === b.id && styles.badgeSelected]}
            >
              <Text style={[styles.badgeEmoji, !b.earned && styles.badgeLocked]}>
                {b.emoji}
              </Text>
              <Text style={[styles.badgeName, !b.earned && styles.badgeNameLocked]}>
                {b.name}
              </Text>
            </Pressable>
          ))}
        </View>
        {selected && (
          <Text style={styles.badgeDesc}>
            {selected.earned ? '✓ ' : '🔒 '}{selected.description}
          </Text>
        )}
      </Card.Content>
    </Card>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  loading: { marginVertical: 20 },
  card: { marginBottom: 12, borderRadius: 12, backgroundColor: p.card },
  streakRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  streakEmoji: { fontSize: 34 },
  streakText: { flex: 1 },
  streakNum: { fontSize: 18, fontWeight: '700', color: p.acc, fontFamily: f.display },
  streakSub: { fontSize: 13, color: p.sub, marginTop: 2 },
  divider: { marginVertical: 14 },
  badgesHeading: { marginBottom: 10 },
  badgeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  badge: {
    width: '31%', alignItems: 'center', paddingVertical: 10, paddingHorizontal: 4,
    borderRadius: 10, backgroundColor: p.desk,
  },
  badgeSelected: { backgroundColor: p.accSoft },
  badgeEmoji: { fontSize: 26, marginBottom: 4 },
  badgeLocked: { opacity: 0.28 },
  badgeName: { fontSize: 11, textAlign: 'center', color: p.ink, fontWeight: '600' },
  badgeNameLocked: { color: p.faint, fontWeight: '400' },
  badgeDesc: {
    marginTop: 12, fontSize: 13, color: p.ink, lineHeight: 18,
    backgroundColor: p.desk, padding: 10, borderRadius: 8,
  },
});
