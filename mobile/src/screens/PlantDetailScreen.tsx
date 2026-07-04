import React, { useState } from 'react';
import {
  ScrollView, View, StyleSheet, Alert,
} from 'react-native';
import {
  Text, Card, Button, Chip, Divider, List,
  ActivityIndicator, useTheme, Surface, TextInput, Snackbar,
} from 'react-native-paper';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { RouteProp, useRoute } from '@react-navigation/native';
import { fetchPlant, logCare, fetchCareLogs, getAdvice, AdviceResponse } from '../api/plants';
import { CareType } from '../types';
import { PlantsStackParamList } from '../../App';

type Route = RouteProp<PlantsStackParamList, 'PlantDetail'>;

const CARE_ACTIONS: { type: CareType; icon: string; label: string }[] = [
  { type: 'water',     icon: '💧', label: 'Watered'    },
  { type: 'fertilize', icon: '🌿', label: 'Fertilized' },
  { type: 'mist',      icon: '💨', label: 'Misted'     },
  { type: 'prune',     icon: '✂️', label: 'Pruned'     },
  { type: 'repot',     icon: '🪴', label: 'Repotted'   },
  { type: 'rotate',    icon: '🔄', label: 'Rotated'    },
];

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short', day: 'numeric', year: 'numeric',
  });
}

export default function PlantDetailScreen() {
  const route = useRoute<Route>();
  const { plantId } = route.params;
  const theme = useTheme();
  const queryClient = useQueryClient();
  const [loggingType, setLoggingType] = useState<CareType | null>(null);

  const { data: plant, isLoading } = useQuery({
    queryKey: ['plant', plantId],
    queryFn: () => fetchPlant(plantId),
  });

  const { data: logs } = useQuery({
    queryKey: ['careLogs', plantId],
    queryFn: () => fetchCareLogs(plantId),
  });

  const [confirmation, setConfirmation] = useState<string | null>(null);
  const logMutation = useMutation({
    mutationFn: ({ type }: { type: CareType }) => logCare(plantId, type),
    onMutate: ({ type }) => setLoggingType(type),
    onSuccess: (_data, { type }) => {
      queryClient.invalidateQueries({ queryKey: ['careLogs', plantId] });
      queryClient.invalidateQueries({ queryKey: ['plants'] });
      const action = CARE_ACTIONS.find((a) => a.type === type);
      setConfirmation(
        `${action?.icon ?? '✅'} ${action?.label ?? 'Care'} — added to ${plant?.nickname ?? 'plant'}'s log`,
      );
    },
    onError: () => Alert.alert('Error', 'Could not log care action.'),
    onSettled: () => setLoggingType(null),
  });

  const [symptoms, setSymptoms] = useState('');
  const [advice, setAdvice] = useState<AdviceResponse | null>(null);
  const adviceMutation = useMutation({
    mutationFn: () => getAdvice(plantId, symptoms),
    onSuccess: setAdvice,
    onError: () => Alert.alert('Error', 'Could not get advice.'),
  });

  if (isLoading || !plant) {
    return <ActivityIndicator style={styles.center} size="large" />;
  }

  const { species } = plant;

  return (
    <View style={styles.container}>
    <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
      {/* Header */}
      <Surface style={styles.header} elevation={1}>
        <Text variant="headlineSmall" style={{ color: theme.colors.primary }}>
          {plant.nickname}
        </Text>
        {species && (
          <Text variant="bodyMedium" style={styles.scientific}>
            {species.scientific_name}
          </Text>
        )}
        <Text variant="bodySmall" style={styles.uuid}>UUID: {plant.plant_uuid}</Text>
      </Surface>

      {/* Quick-log care */}
      <Card style={styles.card}>
        <Card.Title title="Log care" titleVariant="titleMedium" />
        <Card.Content>
          <View style={styles.careGrid}>
            {CARE_ACTIONS.map((a) => (
              <Button
                key={a.type}
                mode="outlined"
                compact
                loading={loggingType === a.type}
                disabled={loggingType !== null}
                onPress={() => logMutation.mutate({ type: a.type })}
                style={styles.careBtn}
                labelStyle={styles.careBtnLabel}
              >
                {a.icon} {a.label}
              </Button>
            ))}
          </View>
        </Card.Content>
      </Card>

      {/* Care advice */}
      <Card style={styles.card}>
        <Card.Title title="Ask the Gnome 🧙" titleVariant="titleMedium" />
        <Card.Content>
          <TextInput
            label="Anything wrong? (optional)"
            value={symptoms}
            onChangeText={setSymptoms}
            mode="outlined"
            multiline
            numberOfLines={2}
            placeholder="e.g. leaves turning yellow at the base"
            style={styles.symptomsInput}
          />
          <Button
            mode="contained"
            onPress={() => adviceMutation.mutate()}
            loading={adviceMutation.isPending}
            disabled={adviceMutation.isPending}
            style={styles.adviceBtn}
          >
            Get care advice
          </Button>
          {advice && (
            <View style={styles.adviceBox}>
              {advice.advice.split('\n').filter((l) => l.trim()).map((line, i) => (
                <Text
                  key={i}
                  variant="bodyMedium"
                  style={[
                    styles.adviceText,
                    line.startsWith('⚠️') && styles.adviceWarningText,
                  ]}
                >
                  {line}
                </Text>
              ))}
              <Chip compact style={styles.backendChip} textStyle={styles.backendChipText}>
                {advice.backend === 'stub' ? 'rule-based' : advice.backend}
              </Chip>
            </View>
          )}
        </Card.Content>
      </Card>

      {/* Species details */}
      {species && (
        <Card style={styles.card}>
          <Card.Title title="Care guide" titleVariant="titleMedium" />
          <Card.Content>
            <Text variant="bodyMedium" style={styles.careNotes}>{species.care_notes}</Text>
            <Divider style={styles.divider} />
            <View style={styles.statRow}>
              <Stat label="Light"     value={species.light_need.replace('_', ' ')} />
              <Stat label="Humidity"  value={`${species.humidity_pct_min}–${species.humidity_pct_max}%`} />
              <Stat label="Temp (°F)" value={`${species.temp_f_min}–${species.temp_f_max}`} />
            </View>
            {species.toxic_to_pets && (
              <Chip icon="alert" style={styles.toxicChip} textStyle={{ color: '#900' }}>
                ⚠️ Caution: toxic to pets
              </Chip>
            )}
          </Card.Content>
        </Card>
      )}

      {/* Care log */}
      <Card style={styles.card}>
        <Card.Title title="Recent care log" titleVariant="titleMedium" />
        <Card.Content>
          {(!logs || logs.length === 0) ? (
            <Text style={styles.empty}>No care logged yet.</Text>
          ) : (
            logs.slice(0, 10).map((log) => (
              <List.Item
                key={log.id}
                title={log.action.charAt(0).toUpperCase() + log.action.slice(1)}
                description={log.notes || formatDate(log.logged_at)}
                left={(props) => <List.Icon {...props} icon="check-circle-outline" />}
                style={styles.logItem}
              />
            ))
          )}
        </Card.Content>
      </Card>
    </ScrollView>
    <Snackbar
      visible={confirmation !== null}
      onDismiss={() => setConfirmation(null)}
      duration={2500}
      style={styles.snackbar}
    >
      {confirmation}
    </Snackbar>
    </View>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.stat}>
      <Text variant="labelSmall" style={styles.statLabel}>{label}</Text>
      <Text variant="bodyMedium" style={styles.statValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6FAF7' },
  content: { padding: 12, paddingBottom: 48 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { borderRadius: 12, padding: 16, marginBottom: 12 },
  scientific: { fontStyle: 'italic', color: '#555', marginTop: 2 },
  uuid: { color: '#aaa', fontFamily: 'monospace', marginTop: 4, fontSize: 11 },
  card: { marginBottom: 12, borderRadius: 12 },
  careGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  careBtn: { marginBottom: 4 },
  careBtnLabel: { fontSize: 13 },
  careNotes: { lineHeight: 22, color: '#333' },
  divider: { marginVertical: 12 },
  statRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  stat: { alignItems: 'center', flex: 1 },
  statLabel: { color: '#888', marginBottom: 2 },
  statValue: { fontWeight: '600' },
  toxicChip: { backgroundColor: '#FFE0E0', alignSelf: 'flex-start' },
  logItem: { paddingVertical: 2 },
  empty: { color: '#aaa', fontStyle: 'italic' },
  scroll: { flex: 1 },
  symptomsInput: { marginBottom: 12 },
  adviceBtn: { borderRadius: 8 },
  adviceBox: {
    marginTop: 16,
    backgroundColor: '#EFF6F0',
    borderRadius: 10,
    padding: 14,
    gap: 10,
  },
  adviceText: { lineHeight: 21, color: '#2F3E36' },
  adviceWarningText: { color: '#9A4D00', fontWeight: '600' },
  backendChip: { alignSelf: 'flex-start', marginTop: 2, backgroundColor: '#E1EDE4' },
  backendChipText: { fontSize: 11, color: '#52796F' },
  snackbar: { backgroundColor: '#2D6A4F' },
});
