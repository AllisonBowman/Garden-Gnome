import React, { useState, useEffect, useMemo } from 'react';
import {
  ScrollView, View, StyleSheet, Alert, KeyboardAvoidingView, Platform,
} from 'react-native';
import {
  Text, TextInput, Button, SegmentedButtons,
  HelperText,
} from 'react-native-paper';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { RouteProp, useNavigation, useRoute } from '@react-navigation/native';
import * as ImagePicker from 'expo-image-picker';
import { fetchSpeciesList } from '../api/species';
import {
  identifySpeciesPhoto, IdentifyResponse, photoIdAvailable,
} from '../photoId/identify';
import { fetchGrowingAreas, fetchSpeciesFit } from '../api/growingAreas';
import { serverMessage } from '../api/errorMessage';
import { ensureCameraPermission } from '../photoPermissions';
import { createPlant } from '../api/plants';
import ReportResult from '../components/ReportResult';
import { rescheduleAllReminders } from '../notifications/reminders';
import { CARE_TASKS_QUERY_KEY } from '../care/useCareTasks';
import { Species, GrowingArea } from '../types';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import Eyebrow from '../components/Eyebrow';
import FitFindingRow from '../components/FitFindingRow';
import { NO_AREA_NOTE, areasFailedNote, placementAreaId } from '../growingAreas/placement';
import type { PlantsStackParamList } from '../../App';
import {
  CHECK_FAILED, misfitIntro, misfitsOf, speciesFitNote,
} from '../growingAreas/fitFindings';

export default function AddPlantScreen() {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const navigation = useNavigation();
  // Opened from an area's own screen, Add Plant starts on that area: the
  // gardener was just looking at it, and the oldest area is somewhere else.
  const route = useRoute<RouteProp<PlantsStackParamList, 'AddPlant'>>();
  const fromAreaId = route.params?.growingAreaId ?? null;
  const queryClient = useQueryClient();

  const [nickname, setNickname]       = useState('');
  const [quantity, setQuantity]       = useState('1');
  // An empty or nonsense field means one plant, not zero — the server rejects
  // anything below 1 and the caretaker plainly has at least one.
  const quantityValue = Math.max(1, parseInt(quantity, 10) || 1);
  const [speciesId, setSpeciesId]     = useState<number | null>(null);
  const [envId, setEnvId]             = useState<number | null>(fromAreaId);
  const [location, setLocation]       = useState('');
  const [condition, setCondition]     = useState('good');
  const [speciesSearch, setSpeciesSearch] = useState('');

  const { data: speciesList = [] } = useQuery({
    queryKey: ['species'],
    queryFn: fetchSpeciesList,
  });

  const {
    data: growingAreas = [], isPending: areasPending, isError: areasFailed,
  } = useQuery({
    queryKey: ['growingAreas'],
    queryFn: fetchGrowingAreas,
  });

  // Preselect where the plant goes: the area it was added from, while that
  // still exists, and otherwise the one the server would have picked on its
  // own — the oldest (`plants._resolve_growing_area_id`), not whichever came
  // first in the list. Leaving this blank did not mean "no area": the plant
  // silently landed in that oldest one, so the only thing the blank achieved
  // was hiding where the plant went. Until the list answers, the area asked
  // for stands: a failed load still saves to it, and the note says so.
  useEffect(() => {
    if (areasPending || areasFailed) return;
    const id = placementAreaId(growingAreas, envId);
    if (id !== envId) setEnvId(id);
  }, [growingAreas, envId, areasPending, areasFailed]);
  const chosenArea = growingAreas.find((e) => e.id === envId) ?? null;

  // What the chosen spot would have against this species, every axis, from
  // the server. Asked before the plant is saved, because "your Hosta is in
  // the wrong place" is worth far more before it is planted than after.
  const {
    data: speciesFit, isLoading: fitLoading, isError: fitFailed, refetch: refetchFit,
  } = useQuery({
    queryKey: ['speciesFit', envId, speciesId],
    queryFn: () => fetchSpeciesFit(envId as number, speciesId as number),
    // Only for an area on screen: the answer is shown under its name.
    enabled: chosenArea != null && speciesId != null,
  });
  const fitMisfits = speciesFit ? misfitsOf(speciesFit.findings) : [];

  const mutation = useMutation({
    mutationFn: () => createPlant({
      nickname,
      species_id: speciesId!,
      quantity: quantityValue,
      growing_area_id: envId ?? undefined,
      location,
      // The backend prefixes "Intake condition:" and logs this as the
      // plant's first timeline entry
      intake_notes: condition,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plants'] });
      // The area it went into now has one more plant, maybe one more thing
      // needing addressing, and more care on its calendar.
      queryClient.invalidateQueries({ queryKey: ['growingAreas'] });
      queryClient.invalidateQueries({ queryKey: ['growingArea'] });
      queryClient.invalidateQueries({ queryKey: ['growingAreaMisfits'] });
      queryClient.invalidateQueries({ queryKey: CARE_TASKS_QUERY_KEY });
      // New plant may introduce new due dates (anchored to acquisition)
      void rescheduleAllReminders();
      navigation.goBack();
    },
    onError: (err) =>
      Alert.alert(
        "Couldn't save",
        serverMessage(
          err,
          "This plant couldn't be saved just now. Check your connection and try again — nothing was lost.",
        ),
      ),
  });

  const [identifyResult, setIdentifyResult] = useState<IdentifyResponse | null>(null);
  // Whether on-device photo ID can run here. When false we hide the button
  // entirely (never a dead button) and users rely on the search below.
  const [aiIdAvailable, setAiIdAvailable] = useState(false);
  useEffect(() => { photoIdAvailable().then(setAiIdAvailable); }, []);

  const identifyMutation = useMutation({
    mutationFn: (photo: { uri: string; mimeType?: string; fileName?: string | null }) =>
      identifySpeciesPhoto(photo, speciesList),
    onSuccess: (result) => {
      setIdentifyResult(result);
      // Auto-select the top candidate; the user can still tap another chip
      if (result.candidates.length > 0) {
        setSpeciesId(result.candidates[0].id);
        setSpeciesSearch(result.candidates[0].common_name);
      }
    },
    onError: (err) =>
      Alert.alert(
        'No match just now',
        serverMessage(
          err,
          "The Gnome couldn't read this photo just now — you can still pick the species from the search below.",
        ),
      ),
  });

  const pickAndIdentify = async (useCamera: boolean) => {
    // allowsEditing opens the OS crop/zoom step so the user can frame the
    // plant's distinctive features (a leaf, the flower). On-device ID is far
    // more accurate on a tight crop than on a wide scene where the plant is
    // small — this is the whole point of capturing up close.
    if (useCamera && !(await ensureCameraPermission())) return;
    const res = useCamera
      ? await ImagePicker.launchCameraAsync({ quality: 0.8, allowsEditing: true })
      : await ImagePicker.launchImageLibraryAsync({
          mediaTypes: ['images'], quality: 0.8, allowsEditing: true,
        });
    if (res.canceled || !res.assets?.length) return;
    identifyMutation.mutate(res.assets[0]);
  };

  const filteredSpecies = speciesList.filter((s: Species) =>
    s.common_name.toLowerCase().includes(speciesSearch.toLowerCase()) ||
    s.scientific_name.toLowerCase().includes(speciesSearch.toLowerCase()),
  );

  const selectedSpecies = speciesList.find((s: Species) => s.id === speciesId);

  // Nickname is no longer required: a planting has no name of its own, and the
  // server fills in one from the species and place ("Tomatoes — south fence")
  // so every surface that addresses a plant by name still has something to say.
  // Not before the areas have answered, either: a save sent while they load
  // carries no area, and the plant lands in one the screen never showed.
  const canSubmit = speciesId !== null && !areasPending;

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <Eyebrow style={styles.sectionLabel}>Plant details</Eyebrow>

        <TextInput
          label="Nickname"
          value={nickname}
          onChangeText={setNickname}
          mode="outlined"
          style={styles.input}
          placeholder="e.g. Sunny, Big Fern, Corner Cactus"
        />

        {/* A row of twelve tomatoes is one thing to the person who planted it,
            not twelve. Leaving this at 1 keeps the old behaviour exactly — a
            single plant you can name. */}
        <TextInput
          label="How many?"
          value={quantity}
          onChangeText={(t) => setQuantity(t.replace(/[^0-9]/g, ''))}
          mode="outlined"
          keyboardType="number-pad"
          style={styles.input}
          placeholder="1"
        />
        {quantityValue > 1 && (
          <Text style={styles.quantityHint}>
            Kept together as one planting — care you log covers all
            {' '}{quantityValue}.
          </Text>
        )}

        <Eyebrow style={styles.sectionLabel}>Species *</Eyebrow>

        {aiIdAvailable && (
          <>
            <View style={styles.identifyBtnRow}>
              {Platform.OS !== 'web' && (
                <Button
                  mode="contained"
                  icon="camera"
                  onPress={() => pickAndIdentify(true)}
                  loading={identifyMutation.isPending}
                  disabled={identifyMutation.isPending}
                  style={styles.identifyBtn}
                >
                  Take photo
                </Button>
              )}
              <Button
                mode="outlined"
                icon="image"
                onPress={() => pickAndIdentify(false)}
                loading={identifyMutation.isPending && Platform.OS === 'web'}
                disabled={identifyMutation.isPending}
                style={styles.identifyBtn}
              >
                Choose photo
              </Button>
            </View>
            <HelperText type="info" style={styles.identifyHint}>
              Tip: zoom and crop close to a leaf or the flower — identification is
              much more accurate on the plant's distinctive features than on a
              wide shot.
            </HelperText>
          </>
        )}

        {identifyResult && (
          <View style={styles.identifyBox}>
            {identifyResult.candidates.length > 0 ? (
              <>
                <Text variant="bodySmall" style={styles.identifyLabel}>
                  Best matches — tap to choose:
                </Text>
                <View style={styles.suggestionBox}>
                  {identifyResult.candidates.map((c) => (
                    <Button
                      key={c.id}
                      mode={speciesId === c.id ? 'contained' : 'outlined'}
                      onPress={() => { setSpeciesId(c.id); setSpeciesSearch(c.common_name); }}
                      style={styles.suggestion}
                      compact
                    >
                      {c.common_name}
                    </Button>
                  ))}
                </View>
              </>
            ) : (
              <Text variant="bodySmall" style={styles.identifyObservation}>
                {identifyResult.observation}
              </Text>
            )}
            {identifyResult.debugRawText != null && (
              <Text variant="bodySmall" style={styles.debugRawText}>
                raw: {identifyResult.debugRawText}
              </Text>
            )}
            <ReportResult
              surfaceLabel="identification"
              result={[
                identifyResult.observation,
                ...(identifyResult.candidates.length > 0
                  ? [`Candidates: ${identifyResult.candidates.map((c) => c.common_name).join(', ')}`]
                  : []),
              ].join('\n')}
            />
          </View>
        )}

        <TextInput
          label="Search species"
          value={speciesSearch}
          onChangeText={setSpeciesSearch}
          mode="outlined"
          style={styles.input}
          left={<TextInput.Icon icon="magnify" />}
        />

        {speciesSearch.length > 0 && (
          <View style={styles.suggestionBox}>
            {filteredSpecies.slice(0, 6).map((s: Species) => (
              <Button
                key={s.id}
                mode={speciesId === s.id ? 'contained' : 'outlined'}
                onPress={() => { setSpeciesId(s.id); setSpeciesSearch(s.common_name); }}
                style={styles.suggestion}
                compact
              >
                {s.common_name}
              </Button>
            ))}
          </View>
        )}

        {selectedSpecies && (
          <HelperText type="info">
            {selectedSpecies.scientific_name}
            {selectedSpecies.toxic_to_pets ? '  ⚠️ toxic to pets' : ''}
          </HelperText>
        )}

        {/* Always shown once the areas have answered: where the plant goes is
            never left for the server to decide out of sight. */}
        {!areasPending && (
          <>
            <Eyebrow style={styles.sectionLabel}>Growing area</Eyebrow>
            {areasFailed ? (
              <Text style={styles.areaNote}>{areasFailedNote(envId != null)}</Text>
            ) : growingAreas.length === 0 ? (
              <Text style={styles.areaNote}>{NO_AREA_NOTE}</Text>
            ) : (
              <View style={styles.envGrid}>
                {growingAreas.map((e: GrowingArea) => (
                  <Button
                    key={e.id}
                    mode={envId === e.id ? 'contained' : 'outlined'}
                    onPress={() => setEnvId(e.id)}
                    style={styles.envBtn}
                    compact
                  >
                    {e.name}
                  </Button>
                ))}
              </View>
            )}

            {/* The spot's answer for this species, before anything is saved.
                Misfits one by one, in the server's words; otherwise one line
                that keeps "confirmed" and "nothing known" apart. */}
            {chosenArea && speciesId != null ? (
              fitLoading ? (
                <Text style={styles.fitQuiet}>{`Checking ${chosenArea.name}…`}</Text>
              ) : fitFailed ? (
                <View>
                  <Text style={styles.fitQuiet}>{CHECK_FAILED}</Text>
                  <Button compact onPress={() => refetchFit()} style={styles.retry}>
                    Try again
                  </Button>
                </View>
              ) : speciesFit && fitMisfits.length > 0 ? (
                <View style={styles.fitBox}>
                  <Text style={styles.fitTitle}>{misfitIntro(chosenArea.name)}</Text>
                  {fitMisfits.map((f, i) => (
                    <FitFindingRow key={`${f.axis}-${i}`} finding={f} />
                  ))}
                  <Text style={styles.fitFoot}>
                    You can still save it here, or pick another spot.
                  </Text>
                </View>
              ) : speciesFit ? (
                <Text style={styles.fitQuiet}>{speciesFitNote(speciesFit, chosenArea.name)}</Text>
              ) : null
            ) : null}
          </>
        )}

        <Eyebrow style={styles.sectionLabel}>Location note</Eyebrow>
        <TextInput
          label="Where in the space?"
          value={location}
          onChangeText={setLocation}
          mode="outlined"
          style={styles.input}
          placeholder="e.g. South window, bathroom shelf"
        />

        <Eyebrow style={styles.sectionLabel}>Initial condition</Eyebrow>
        <SegmentedButtons
          value={condition}
          onValueChange={setCondition}
          buttons={[
            { value: 'excellent', label: 'Excellent' },
            { value: 'good',      label: 'Good'      },
            { value: 'fair',      label: 'Fair'      },
            { value: 'poor',      label: 'Poor'      },
          ]}
          style={styles.segmented}
        />

        <Button
          mode="contained"
          onPress={() => mutation.mutate()}
          disabled={!canSubmit || mutation.isPending}
          loading={mutation.isPending}
          style={styles.saveBtn}
          contentStyle={styles.saveBtnContent}
          buttonColor={palette.acc}
          textColor={palette.btnInk}
        >
          Save plant
        </Button>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  container: { flex: 1, backgroundColor: p.bg },
  content: { padding: 16, paddingBottom: 48 },
  sectionLabel: { marginTop: 20, marginBottom: 8 },
  quantityHint: {
    color: p.sub, fontSize: 13, fontStyle: 'italic',
    marginTop: -4, marginBottom: 8,
  },
  input: { marginBottom: 4 },
  suggestionBox: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 4 },
  suggestion: { marginBottom: 4 },
  identifyBtnRow: { flexDirection: 'row', gap: 8 },
  identifyBtn: { flex: 1 },
  identifyHint: { marginBottom: 8 },
  identifyBox: {
    backgroundColor: p.accSoft,
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  identifyLabel: { color: p.sub, marginBottom: 8, fontWeight: '600' },
  identifyObservation: { color: p.ink, lineHeight: 19 },
  debugRawText: { fontFamily: 'monospace', fontSize: 11, color: p.faint, marginTop: 4 },
  envGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 4 },
  envBtn: { marginBottom: 4 },
  areaNote: { color: p.sub, fontSize: 13, lineHeight: 19, marginBottom: 4 },
  fitQuiet: { color: p.sub, fontSize: 13, lineHeight: 19, marginTop: 6 },
  fitBox: {
    backgroundColor: p.warnSoft,
    borderRadius: 12,
    padding: 12,
    marginTop: 8,
  },
  fitTitle: { color: p.warn, fontWeight: '700', fontSize: 14, marginBottom: 8 },
  fitFoot: { color: p.sub, fontSize: 12.5, lineHeight: 18, marginTop: 2 },
  retry: { alignSelf: 'flex-start', marginTop: 4 },
  segmented: { marginBottom: 8 },
  saveBtn: { marginTop: 24, borderRadius: 8 },
  saveBtnContent: { paddingVertical: 6 },
});
