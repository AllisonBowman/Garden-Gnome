import React, { useState, useMemo } from 'react';
import {
  ScrollView, View, StyleSheet, Alert, Platform,
} from 'react-native';
import {
  Text, Card, Button, Chip, Divider, List,
  ActivityIndicator, Surface, TextInput, Snackbar,
} from 'react-native-paper';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { RouteProp, useRoute } from '@react-navigation/native';
import * as ImagePicker from 'expo-image-picker';
import {
  fetchPlant, logCare, fetchCareLogs, getAdvice, AdviceResponse,
  diagnosePlantPhoto, DiagnosisResponse,
} from '../api/plants';
import { rescheduleAllReminders } from '../notifications/reminders';
import { gnomeVoice } from '../gnomeVoice/restyle';
import { serverMessage } from '../api/errorMessage';
import { ensureCameraPermission } from '../photoPermissions';
import ReportResult from '../components/ReportResult';
import { CareType } from '../types';
import { PlantsStackParamList } from '../../App';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import Eyebrow from '../components/Eyebrow';
import Pill from '../components/Pill';

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
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
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
      // Care history changed — recompute reminder schedule in the background
      void rescheduleAllReminders();
    },
    onError: () => Alert.alert('Error', 'Could not log care action.'),
    onSettled: () => setLoggingType(null),
  });

  const [symptoms, setSymptoms] = useState('');
  const [advice, setAdvice] = useState<(AdviceResponse & { gnomeStyled: boolean }) | null>(null);
  const adviceMutation = useMutation({
    mutationFn: async () => {
      // The rule engine determines WHAT to say; the on-device gnome only
      // restyles HOW it's said (and falls back to the flat text everywhere
      // the model can't run or drifts from the given facts).
      const result = await getAdvice(plantId, symptoms);
      const voiced = await gnomeVoice(result.advice, plant?.nickname);
      return { ...result, advice: voiced.text, gnomeStyled: voiced.styled };
    },
    onSuccess: setAdvice,
    onError: (err) =>
      Alert.alert(
        'No advice just now',
        serverMessage(
          err,
          "The Gnome couldn't put together advice just now. Please try again in a few minutes.",
        ),
      ),
  });

  const [diagnosisNotes, setDiagnosisNotes] = useState('');
  const [diagnosis, setDiagnosis] = useState<DiagnosisResponse | null>(null);
  const diagnoseMutation = useMutation({
    mutationFn: (asset: { uri: string; mimeType?: string; fileName?: string | null }) =>
      diagnosePlantPhoto(plantId, asset, diagnosisNotes),
    onSuccess: (result) => {
      setDiagnosis(result);
      // The diagnosis is auto-logged to the timeline by the backend
      queryClient.invalidateQueries({ queryKey: ['careLogs', plantId] });
    },
    onError: (err) =>
      Alert.alert(
        'No reading just now',
        serverMessage(
          err,
          "The Gnome couldn't examine this photo just now. Your photo was not analyzed — please try again in a few minutes.",
        ),
      ),
  });

  const pickAndDiagnose = async (useCamera: boolean) => {
    // launchCameraAsync requires camera permission and does not request it;
    // without this the button silently does nothing (see photoPermissions.ts).
    if (useCamera && !(await ensureCameraPermission())) return;
    const res = useCamera
      ? await ImagePicker.launchCameraAsync({ quality: 0.8 })
      : await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.8 });
    if (res.canceled || !res.assets?.length) return;
    diagnoseMutation.mutate(res.assets[0]);
  };

  if (isLoading || !plant) {
    return <ActivityIndicator style={styles.center} size="large" />;
  }

  const { species } = plant;

  return (
    <View style={styles.container}>
    <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
      {/* Header */}
      <Surface style={styles.header} elevation={1}>
        <Text variant="headlineSmall" style={styles.plantName}>
          {plant.nickname}
        </Text>
        {species && (
          <Text variant="bodyMedium" style={styles.scientific}>
            {species.scientific_name}
          </Text>
        )}
      </Surface>

      {/* Quick-log care */}
      <Card style={styles.card}>
        <Card.Title title="Log care" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
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
        <Card.Title title="Ask the Gnome 🧙" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
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
          {!advice && !adviceMutation.isPending && (
            <Text style={styles.adviceHint}>
              Care tips for {plant.nickname}, grounded in its species and history.
              Mention anything that looks off above.
            </Text>
          )}
          {advice && (
            <View style={styles.adviceBox}>
              {advice.advice.split('\n').filter((l) => l.trim()).map((line, i) => (
                <Text
                  key={i}
                  variant="bodyMedium"
                  style={[
                    styles.adviceText,
                    advice.gnomeStyled && styles.gnomeVoiceText,
                    line.startsWith('⚠️') && styles.adviceWarningText,
                  ]}
                >
                  {line}
                </Text>
              ))}
              <View style={styles.resultMetaRow}>
                <Pill tone="neutral" filled style={styles.metaPill}>
                  {(advice.backend === 'stub' ? 'rule-based' : advice.backend)
                    + (advice.gnomeStyled ? ' • gnome voice' : '')}
                </Pill>
                <ReportResult
                  surfaceLabel="care advice"
                  result={advice.advice}
                  context={[
                    `Plant: ${plant.nickname}`,
                    ...(species ? [`Species: ${species.common_name} (${species.scientific_name})`] : []),
                  ]}
                />
              </View>
            </View>
          )}
        </Card.Content>
      </Card>

      {/* Photo diagnosis — specimen-card styling from the landing page */}
      <Card style={styles.specimenCard}>
        <View style={styles.specimenHeader}>
          <Eyebrow color={palette.warn}>SPECIMEN CHECK-UP</Eyebrow>
          <Text style={styles.specimenTitle}>Photo diagnosis 📷</Text>
          <Text style={styles.specimenSub}>
            Snap the whole plant or a close-up of what worries you — the Gnome
            reads it against {species?.common_name ?? 'this species'}&apos;s care
            facts and this plant&apos;s history, then files it to the timeline.
          </Text>
        </View>
        <Card.Content style={styles.specimenBody}>
          <TextInput
            label="Anything specific you noticed? (optional)"
            value={diagnosisNotes}
            onChangeText={setDiagnosisNotes}
            mode="outlined"
            style={styles.diagnosisInput}
            outlineColor={palette.line}
            activeOutlineColor={palette.warn}
            textColor={palette.ink}
            placeholder="e.g. brown spots since last week"
          />
          <View style={styles.diagnosisBtnRow}>
            {Platform.OS !== 'web' && (
              <Button
                mode="contained"
                icon="camera"
                onPress={() => pickAndDiagnose(true)}
                disabled={diagnoseMutation.isPending}
                buttonColor={palette.hedge}
                textColor={palette.btnInk}
                style={styles.diagnosisBtn}
              >
                Take photo
              </Button>
            )}
            <Button
              mode={Platform.OS === 'web' ? 'contained' : 'outlined'}
              icon="image"
              onPress={() => pickAndDiagnose(false)}
              loading={diagnoseMutation.isPending}
              disabled={diagnoseMutation.isPending}
              buttonColor={Platform.OS === 'web' ? palette.hedge : undefined}
              textColor={Platform.OS === 'web' ? palette.btnInk : palette.warn}
              style={styles.diagnosisBtn}
            >
              Choose photo
            </Button>
          </View>
          {diagnoseMutation.isPending && (
            <Text style={styles.diagnosisPending}>
              Examining the specimen… this can take a moment.
            </Text>
          )}
          {diagnosis && (
            <View style={styles.testimony}>
              <Eyebrow color={palette.warn}>GNOME&apos;S FINDINGS</Eyebrow>
              {diagnosis.diagnosis.split('\n').filter((l) => l.trim()).map((line, i) => (
                <Text key={i} style={styles.testimonyText}>{line}</Text>
              ))}
              <View style={styles.resultMetaRow}>
                <Pill tone="neutral" filled style={styles.metaPill}>
                  {diagnosis.backend === 'stub' ? 'diagnosis not enabled yet' : diagnosis.backend}
                </Pill>
                <ReportResult
                  surfaceLabel="diagnosis"
                  result={diagnosis.diagnosis}
                  textColor={palette.warn}
                  context={[
                    `Plant: ${plant.nickname}`,
                    ...(species ? [`Species: ${species.common_name} (${species.scientific_name})`] : []),
                  ]}
                />
              </View>
            </View>
          )}
        </Card.Content>
      </Card>

      {/* Species details */}
      {species && (
        <Card style={styles.card}>
          <Card.Title title="Care guide" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
          <Card.Content>
            <Text variant="bodyMedium" style={styles.careNotes}>{species.care_notes}</Text>
            <Divider style={styles.divider} />
            <View style={styles.statRow}>
              <Stat label="Light"     value={species.light_need.replace('_', ' ')} />
              <Stat label="Humidity"  value={`${species.humidity_pct_min}–${species.humidity_pct_max}%`} />
              <Stat label="Temp (°F)" value={`${species.temp_f_min}–${species.temp_f_max}`} />
            </View>
            {species.toxic_to_pets && (
              <Chip icon="alert" style={styles.toxicChip} textStyle={{ color: palette.warn }}>
                ⚠️ Caution: toxic to pets
              </Chip>
            )}
          </Card.Content>
        </Card>
      )}

      {/* Care log */}
      <Card style={styles.card}>
        <Card.Title title="Recent care log" titleVariant="titleMedium" titleStyle={styles.cardTitle} />
        <Card.Content>
          {(!logs || logs.length === 0) ? (
            <Text style={styles.empty}>
              No care logged yet — tap a care action above and {plant.nickname}&apos;s
              timeline starts here.
            </Text>
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
      <Text style={styles.snackbarText}>{confirmation}</Text>
    </Snackbar>
    </View>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  return (
    <View style={styles.stat}>
      <Text variant="labelSmall" style={styles.statLabel}>{label}</Text>
      <Text variant="bodyMedium" style={styles.statValue}>{value}</Text>
    </View>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  container: { flex: 1, backgroundColor: p.bg },
  content: { padding: 12, paddingBottom: 48 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { borderRadius: 12, padding: 16, marginBottom: 12 },
  plantName: { color: p.acc, fontFamily: f.display },
  scientific: { fontStyle: 'italic', color: p.sub, marginTop: 2, fontFamily: f.display },
  card: { marginBottom: 12, borderRadius: 12 },
  cardTitle: { fontFamily: f.display },
  careGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  careBtn: { marginBottom: 4 },
  careBtnLabel: { fontSize: 13 },
  careNotes: { lineHeight: 22, color: p.ink },
  divider: { marginVertical: 12 },
  statRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  stat: { alignItems: 'center', flex: 1 },
  statLabel: { color: p.faint, marginBottom: 2 },
  statValue: { fontWeight: '600', fontFamily: f.numeric, color: p.ink },
  toxicChip: { backgroundColor: p.warnSoft, alignSelf: 'flex-start' },
  logItem: { paddingVertical: 2 },
  empty: { color: p.faint, fontStyle: 'italic' },
  scroll: { flex: 1 },
  symptomsInput: { marginBottom: 12 },
  adviceBtn: { borderRadius: 8 },
  adviceHint: { marginTop: 12, fontSize: 13, lineHeight: 19, color: p.sub, fontStyle: 'italic' },
  adviceBox: {
    marginTop: 16,
    backgroundColor: p.accSoft,
    borderRadius: 10,
    padding: 14,
    gap: 10,
  },
  adviceText: { lineHeight: 21, color: p.ink },
  gnomeVoiceText: { fontStyle: 'italic', fontSize: 14.5 },
  adviceWarningText: { color: p.warn, fontWeight: '600' },
  metaPill: { marginTop: 2 },
  resultMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: 8,
  },
  snackbar: { backgroundColor: p.acc },
  snackbarText: { color: p.btnInk },

  // Specimen card — field-notebook look (paper/gold/clay) mapped to tokens
  specimenCard: { marginBottom: 12, borderRadius: 12, backgroundColor: p.desk },
  specimenHeader: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderStyle: 'dashed',
    borderBottomColor: p.line,
  },
  specimenTitle: { fontSize: 19, fontWeight: '600', color: p.ink, marginTop: 4, fontFamily: f.display },
  specimenSub: { fontSize: 13, lineHeight: 19, color: p.sub, marginTop: 6 },
  specimenBody: { paddingTop: 14 },
  diagnosisInput: { marginBottom: 12, backgroundColor: p.card },
  diagnosisBtnRow: { flexDirection: 'row', gap: 10, flexWrap: 'wrap' },
  diagnosisBtn: { borderRadius: 6, borderColor: p.warn },
  diagnosisPending: { marginTop: 12, fontStyle: 'italic', color: p.sub, fontSize: 13 },
  testimony: {
    marginTop: 16,
    backgroundColor: p.card2,
    borderLeftWidth: 2,
    borderLeftColor: p.hedge,
    borderTopRightRadius: 2,
    borderBottomRightRadius: 2,
    padding: 14,
    gap: 8,
  },
  testimonyText: { fontStyle: 'italic', lineHeight: 21, color: p.ink, fontSize: 14.5 },
});
