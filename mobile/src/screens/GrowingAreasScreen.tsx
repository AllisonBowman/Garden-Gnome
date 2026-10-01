import React, { useState, useMemo } from 'react';
import { ScrollView, View, StyleSheet, Alert } from 'react-native';
import {
  Text, Card, Button, TextInput, SegmentedButtons, Chip,
  ActivityIndicator, FAB, Portal, Modal,
} from 'react-native-paper';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { fetchGrowingAreas, createGrowingArea } from '../api/growingAreas';
import {
  GrowingArea, GrowingAreaType, Shelter, TempExposure, SunExposure,
  GrowingSurface, GrowingGoal,
} from '../types';
import AddressPicker from '../components/AddressPicker';
import { ResolvedPlace } from '../location/geocode';
import type { GrowingAreasStackParamList } from '../../App';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import Eyebrow from '../components/Eyebrow';
import {
  SURFACES, SURFACE_LABEL, GOALS, dimensionPrompts, climateForSurface,
  typeForSurface,
} from '../growingAreas/realEstate';

type Nav = NativeStackNavigationProp<GrowingAreasStackParamList, 'GrowingAreasList'>;

const AREA_TYPES: { value: GrowingAreaType; label: string }[] = [
  { value: 'home',             label: '🏠 Home'        },
  { value: 'nursery',          label: '🌱 Nursery'     },
  { value: 'community_garden', label: '🌳 Community'   },
  { value: 'conservation',     label: '🌿 Conservation'},
  { value: 'research',         label: '🔬 Research'    },
];

function GrowingAreaCard({ area, onPress }: { area: GrowingArea; onPress: () => void }) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const typeLabel = AREA_TYPES.find((t) => t.value === area.type)?.label ?? area.type;
  return (
    <Card style={styles.card} mode="elevated" onPress={onPress}>
      <Card.Content>
        <Text variant="titleMedium" style={styles.name}>{area.name}</Text>
        <Text variant="bodySmall" style={styles.meta}>
          {area.surface ? SURFACE_LABEL[area.surface] : typeLabel}
        </Text>
        {area.city ? (
          <Text variant="bodySmall" style={styles.meta}>📍 {area.city}{area.region ? `, ${area.region}` : ''}</Text>
        ) : null}
        <View style={styles.cardFooter}>
          <Text variant="bodySmall" style={styles.count}>{area.plant_count} plant{area.plant_count !== 1 ? 's' : ''}</Text>
          <Text variant="bodySmall" style={styles.weatherHint}>Weather ›</Text>
        </View>
      </Card.Content>
    </Card>
  );
}

/** A measurement field. Empty string stays empty — it is never sent as 0.
 *
 * The whole point of asking is that a number here is something the gardener
 * measured. A blank that arrived at the server as 0 would be indistinguishable
 * from "this bed has no room in it", and would quietly rule out every plant. */
function Measurement({
  label, hint, value, onChange,
}: {
  label: string; hint: string; value: string; onChange: (v: string) => void;
}) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  return (
    <View style={styles.measurement}>
      <TextInput
        label={label}
        value={value}
        onChangeText={(v) => onChange(v.replace(/[^0-9.]/g, ''))}
        keyboardType="decimal-pad"
        mode="outlined"
        dense
      />
      <Text variant="bodySmall" style={styles.measurementHint}>{hint}</Text>
    </View>
  );
}

const STEP_TITLES = ['The space', 'The conditions', 'What it’s for'];

export default function GrowingAreasScreen() {
  const queryClient = useQueryClient();
  const navigation = useNavigation<Nav>();
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const [modalVisible, setModalVisible] = useState(false);
  const [step, setStep] = useState(0);

  // Step 1 — the real estate
  const [name, setName] = useState('');
  const [surface, setSurface] = useState<GrowingSurface | null>(null);
  const [areaSqft, setAreaSqft] = useState('');
  const [headroomIn, setHeadroomIn] = useState('');
  const [soilDepthIn, setSoilDepthIn] = useState('');
  const [place, setPlace] = useState<ResolvedPlace | null>(null);
  // Bumped on reset to remount AddressPicker with fresh internal state.
  const [pickerKey, setPickerKey] = useState(0);

  // Step 2 — the conditions
  const [type, setType] = useState<GrowingAreaType>('home');
  const [shelter, setShelter] = useState<Shelter>('sheltered');
  const [tempExposure, setTempExposure] = useState<TempExposure>('indoor');
  const [sunExposure, setSunExposure] = useState<SunExposure>('partial_sun');

  // Step 3 — the goals
  const [goals, setGoals] = useState<GrowingGoal[]>([]);

  // Picking a surface presets the conditions, because a windowsill and a raised
  // bed disagree about all three and most people should not have to say so
  // twice. Every preset stays editable on the next step.
  const applySurface = (s: GrowingSurface) => {
    setSurface(s);
    const climate = climateForSurface(s);
    setShelter(climate.shelter);
    setTempExposure(climate.temp_exposure);
    setSunExposure(climate.sun_exposure);
    setType(typeForSurface(s));
  };

  const reset = () => {
    setStep(0);
    setName(''); setSurface(null);
    setAreaSqft(''); setHeadroomIn(''); setSoilDepthIn('');
    setPlace(null); setPickerKey((k) => k + 1);
    setType('home'); setShelter('sheltered');
    setTempExposure('indoor'); setSunExposure('partial_sun');
    setGoals([]);
  };

  const { data: growingAreas = [], isLoading } = useQuery({
    queryKey: ['growingAreas'],
    queryFn: fetchGrowingAreas,
  });

  // A blank measurement is left off the payload entirely rather than sent as
  // 0 — the server stores null, and the fit engine reads null as "unknown".
  const measured = (raw: string): number | undefined => {
    const n = parseFloat(raw);
    return Number.isFinite(n) && n > 0 ? n : undefined;
  };

  const mutation = useMutation({
    mutationFn: () => createGrowingArea({
      name, type,
      // Geography is derived from a validated, geocoded place (or blank).
      city: place?.city ?? '',
      region: place?.region ?? '',
      country: place?.country ?? '',
      lat: place?.lat,
      lng: place?.lng,
      shelter, temp_exposure: tempExposure, sun_exposure: sunExposure,
      surface: surface ?? undefined,
      area_sqft: measured(areaSqft),
      headroom_in: measured(headroomIn),
      soil_depth_in: measured(soilDepthIn),
      // Always sent, even empty: [] is "asked, nothing in particular", which
      // is a different answer from never having been asked.
      goals,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['growingAreas'] });
      setModalVisible(false);
      reset();
    },
    onError: () => Alert.alert('Error', 'Could not create growing area.'),
  });

  if (isLoading) return <ActivityIndicator style={styles.center} size="large" />;

  const prompts = dimensionPrompts(surface);
  const isLast = step === STEP_TITLES.length - 1;
  const canAdvance = step === 0 ? name.trim().length > 0 : true;

  const toggleGoal = (g: GrowingGoal) => setGoals(
    (cur) => (cur.includes(g) ? cur.filter((x) => x !== g) : [...cur, g]));

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        {growingAreas.length === 0 ? (
          <Text style={styles.empty}>No growing areas yet. Create one to get started.</Text>
        ) : (
          growingAreas.map((a: GrowingArea) => (
            <GrowingAreaCard
              key={a.id}
              area={a}
              onPress={() => navigation.navigate('GrowingAreaDetail', { growingAreaId: a.id, name: a.name })}
            />
          ))
        )}
      </ScrollView>

      <FAB
        icon="plus"
        style={styles.fab}
        color={palette.btnInk}
        label="New growing area"
        onPress={() => { reset(); setModalVisible(true); }}
      />

      <Portal>
        <Modal
          visible={modalVisible}
          onDismiss={() => setModalVisible(false)}
          contentContainerStyle={styles.modal}
        >
          <Eyebrow>{`Step ${step + 1} of ${STEP_TITLES.length}`}</Eyebrow>
          <Text variant="titleLarge" style={styles.modalTitle}>{STEP_TITLES[step]}</Text>

          <ScrollView style={styles.stepScroll} keyboardShouldPersistTaps="handled">
            {step === 0 && (
              <>
                <TextInput
                  label="Name *"
                  value={name}
                  onChangeText={setName}
                  mode="outlined"
                  style={styles.input}
                />

                <Eyebrow style={styles.label}>What will plants sit in?</Eyebrow>
                <View style={styles.chipWrap}>
                  {SURFACES.map((s) => (
                    <Chip
                      key={s}
                      compact
                      selected={surface === s}
                      showSelectedCheck={false}
                      onPress={() => applySurface(s)}
                      style={[styles.chip, surface === s && styles.chipOn]}
                      textStyle={surface === s ? styles.chipOnText : undefined}
                    >
                      {SURFACE_LABEL[s]}
                    </Chip>
                  ))}
                </View>

                <Eyebrow style={styles.label}>How much room is there?</Eyebrow>
                <Text variant="bodySmall" style={styles.hint}>
                  Leave anything you haven’t measured blank. Blank means unknown,
                  and nothing gets recommended on a guess.
                </Text>
                <Measurement
                  label={prompts.area.label} hint={prompts.area.hint}
                  value={areaSqft} onChange={setAreaSqft}
                />
                <Measurement
                  label={prompts.headroom.label} hint={prompts.headroom.hint}
                  value={headroomIn} onChange={setHeadroomIn}
                />
                <Measurement
                  label={prompts.depth.label} hint={prompts.depth.hint}
                  value={soilDepthIn} onChange={setSoilDepthIn}
                />

                <Eyebrow style={styles.label}>Location</Eyebrow>
                <Text variant="bodySmall" style={styles.hint}>
                  Set a place to unlock local weather. Search an address or use your
                  location — only a real, resolved place can be saved.
                </Text>
                <AddressPicker key={pickerKey} onChange={setPlace} />
              </>
            )}

            {step === 1 && (
              <>
                <Text variant="bodySmall" style={styles.hint}>
                  {surface
                    ? `Set from “${SURFACE_LABEL[surface]}”. Change anything that isn’t right.`
                    : 'Describe how much of the weather actually reaches this spot.'}
                </Text>

                <Eyebrow style={styles.label}>Shelter</Eyebrow>
                <SegmentedButtons
                  value={shelter}
                  onValueChange={(v) => setShelter(v as Shelter)}
                  buttons={[
                    { value: 'sheltered', label: 'Sheltered' },
                    { value: 'partial',   label: 'Partial'   },
                    { value: 'exposed',   label: 'Exposed'   },
                  ]}
                  style={styles.segmented}
                />

                <Eyebrow style={styles.label}>Temperature</Eyebrow>
                <SegmentedButtons
                  value={tempExposure}
                  onValueChange={(v) => setTempExposure(v as TempExposure)}
                  buttons={[
                    { value: 'indoor',  label: 'Indoor'  },
                    { value: 'outdoor', label: 'Outdoor' },
                  ]}
                  style={styles.segmented}
                />

                <Eyebrow style={styles.label}>Sun</Eyebrow>
                <SegmentedButtons
                  value={sunExposure}
                  onValueChange={(v) => setSunExposure(v as SunExposure)}
                  buttons={[
                    { value: 'full_sun',    label: 'Full sun' },
                    { value: 'partial_sun', label: 'Partial'  },
                    { value: 'shade',       label: 'Shade'    },
                  ]}
                  style={styles.segmented}
                />

                <Eyebrow style={styles.label}>Type</Eyebrow>
                <SegmentedButtons
                  value={type}
                  onValueChange={(v) => setType(v as GrowingAreaType)}
                  buttons={[
                    { value: 'home',    label: '🏠' },
                    { value: 'nursery', label: '🌱' },
                    { value: 'community_garden', label: '🌳' },
                    { value: 'conservation', label: '🌿' },
                    { value: 'research', label: '🔬' },
                  ]}
                  style={styles.segmented}
                />
              </>
            )}

            {step === 2 && (
              <>
                <Text variant="bodySmall" style={styles.hint}>
                  Pick any that apply, or none. These narrow what gets suggested
                  for this spot — they never loosen it.
                </Text>
                {GOALS.map((g) => (
                  <Chip
                    key={g.value}
                    selected={goals.includes(g.value)}
                    showSelectedCheck={false}
                    onPress={() => toggleGoal(g.value)}
                    style={[styles.goalChip, goals.includes(g.value) && styles.chipOn]}
                    textStyle={goals.includes(g.value) ? styles.chipOnText : undefined}
                  >
                    {g.label}
                  </Chip>
                ))}
                <Text variant="bodySmall" style={styles.goalNote}>
                  {goals.length === 0
                    ? 'Nothing in particular — you’ll see whatever fits the space.'
                    : GOALS.filter((g) => goals.includes(g.value))
                        .map((g) => g.hint).join(' ')}
                </Text>
              </>
            )}
          </ScrollView>

          <View style={styles.footer}>
            <Button
              mode="text"
              onPress={() => (step === 0 ? setModalVisible(false) : setStep((s) => s - 1))}
              disabled={mutation.isPending}
            >
              {step === 0 ? 'Cancel' : 'Back'}
            </Button>
            <Button
              mode="contained"
              onPress={() => (isLast ? mutation.mutate() : setStep((s) => s + 1))}
              disabled={!canAdvance || mutation.isPending}
              loading={mutation.isPending}
            >
              {isLast ? 'Create' : 'Next'}
            </Button>
          </View>
        </Modal>
      </Portal>
    </View>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  screen: { flex: 1, backgroundColor: p.bg },
  content: { padding: 12, paddingBottom: 96 },
  card: { marginBottom: 10, borderRadius: 12, backgroundColor: p.card },
  name: { fontFamily: f.display, color: p.ink },
  meta: { color: p.sub, marginTop: 2 },
  cardFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 },
  count: { color: p.acc, fontWeight: '600' },
  weatherHint: { color: p.faint },
  fab: { position: 'absolute', right: 16, bottom: 24, backgroundColor: p.acc },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  empty: { textAlign: 'center', color: p.faint, marginTop: 48 },
  modal: { backgroundColor: p.card, margin: 20, borderRadius: 12, padding: 20, maxHeight: '85%' },
  modalTitle: { marginBottom: 12, fontWeight: '700', fontFamily: f.display, color: p.ink },
  stepScroll: { flexGrow: 0 },
  label: { marginBottom: 6, marginTop: 14 },
  hint: { color: p.faint, marginBottom: 10, lineHeight: 18 },
  input: { marginBottom: 4 },
  segmented: { marginBottom: 4 },
  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 4 },
  chip: { backgroundColor: p.accSoft },
  chipOn: { backgroundColor: p.acc },
  chipOnText: { color: p.btnInk, fontWeight: '700' },
  goalChip: { marginBottom: 8, backgroundColor: p.accSoft },
  goalNote: { color: p.sub, fontStyle: 'italic', lineHeight: 18, marginTop: 4 },
  measurement: { marginBottom: 10 },
  measurementHint: { color: p.faint, marginTop: 3, lineHeight: 16 },
  footer: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', marginTop: 12,
  },
});
