import React, { useState } from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { Text, Card, Divider, ActivityIndicator } from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { fetchPlants, fetchCareLogs } from '../api/plants';
import { fetchSpecies } from '../api/species';
import { CareLog, Species } from '../types';
import {
  computeStreak, computeMetrics, computeBadges, Badge,
} from './streaks';

/**
 * Derives the household care streak and badges from existing care-log data
 * (no backend storage). Fetches per-plant logs + species schedules once and
 * lets React Query cache them.
 */
function useStreakBadges() {
  const { data: plants } = useQuery({ queryKey: ['plants'], queryFn: fetchPlants });

  const ids = (plants ?? []).map((p) => p.id).join(',');
  const { data, isLoading } = useQuery({
    queryKey: ['streakData', ids],
    enabled: !!plants,
    staleTime: 60_000,
    queryFn: async () => {
      const list = plants ?? [];
      const logsByPlant: Record<number, CareLog[]> = {};
      await Promise.all(list.map(async (p) => {
        logsByPlant[p.id] = await fetchCareLogs(p.id);
      }));
      const speciesById: Record<number, Species> = {};
      await Promise.all([...new Set(list.map((p) => p.species_id))].map(async (sid) => {
        speciesById[sid] = await fetchSpecies(sid);
      }));
      return { logsByPlant, speciesById };
    },
  });

  if (!plants || !data) {
    return { loading: isLoading, hasPlants: !!plants?.length, streak: null, badges: [] as Badge[] };
  }
  const streak = computeStreak({ plants, ...data });
  const badges = computeBadges(computeMetrics(plants, data.logsByPlant, streak.best));
  return { loading: false, hasPlants: plants.length > 0, streak, badges };
}

export default function StreakBadges() {
  const { loading, hasPlants, streak, badges } = useStreakBadges();
  const [selected, setSelected] = useState<Badge | null>(null);

  if (loading) {
    return <ActivityIndicator style={styles.loading} color="#2D6A4F" />;
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
        <Text style={styles.badgesHeading}>Badges · {earnedCount} of {badges.length}</Text>
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

const styles = StyleSheet.create({
  loading: { marginVertical: 20 },
  card: { marginBottom: 12, borderRadius: 12, backgroundColor: '#FFFFFF' },
  streakRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  streakEmoji: { fontSize: 34 },
  streakText: { flex: 1 },
  streakNum: { fontSize: 18, fontWeight: '700', color: '#2D6A4F' },
  streakSub: { fontSize: 13, color: '#6b7d6e', marginTop: 2 },
  divider: { marginVertical: 14 },
  badgesHeading: {
    fontSize: 12, letterSpacing: 0.5, color: '#52796F',
    fontWeight: '600', marginBottom: 10, textTransform: 'uppercase',
  },
  badgeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  badge: {
    width: '31%', alignItems: 'center', paddingVertical: 10, paddingHorizontal: 4,
    borderRadius: 10, backgroundColor: '#F1F6F2',
  },
  badgeSelected: { backgroundColor: '#E1EDE4' },
  badgeEmoji: { fontSize: 26, marginBottom: 4 },
  badgeLocked: { opacity: 0.28 },
  badgeName: { fontSize: 11, textAlign: 'center', color: '#2F3E36', fontWeight: '600' },
  badgeNameLocked: { color: '#9aa89c', fontWeight: '400' },
  badgeDesc: {
    marginTop: 12, fontSize: 13, color: '#2F3E36', lineHeight: 18,
    backgroundColor: '#F1F6F2', padding: 10, borderRadius: 8,
  },
});
