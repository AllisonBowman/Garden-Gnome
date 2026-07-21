import React, { useState, useEffect } from 'react';
import {
  ScrollView, View, StyleSheet, Alert, KeyboardAvoidingView, Platform,
} from 'react-native';
import {
  Text, TextInput, Button, SegmentedButtons, useTheme,
  HelperText,
} from 'react-native-paper';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import * as ImagePicker from 'expo-image-picker';
import { fetchSpeciesList } from '../api/species';
import {
  identifySpeciesPhoto, IdentifyResponse, photoIdAvailable,
} from '../photoId/identify';
import { fetchEnvironments } from '../api/environments';
import { createPlant } from '../api/plants';
import ReportResult from '../components/ReportResult';
import { rescheduleAllReminders } from '../notifications/reminders';
import { Species, Environment } from '../types';

export default function AddPlantScreen() {
  const theme = useTheme();
  const navigation = useNavigation();
  const queryClient = useQueryClient();

  const [nickname, setNickname]       = useState('');
  const [speciesId, setSpeciesId]     = useState<number | null>(null);
  const [envId, setEnvId]             = useState<number | null>(null);
  const [location, setLocation]       = useState('');
  const [condition, setCondition]     = useState('good');
  const [speciesSearch, setSpeciesSearch] = useState('');

  const { data: speciesList = [] } = useQuery({
    queryKey: ['species'],
    queryFn: fetchSpeciesList,
  });

  const { data: environments = [] } = useQuery({
    queryKey: ['environments'],
    queryFn: fetchEnvironments,
  });

  const mutation = useMutation({
    mutationFn: () => createPlant({
      nickname,
      species_id: speciesId!,
      environment_id: envId ?? undefined,
      location,
      // The backend prefixes "Intake condition:" and logs this as the
      // plant's first timeline entry
      intake_notes: condition,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plants'] });
      // New plant may introduce new due dates (anchored to acquisition)
      void rescheduleAllReminders();
      navigation.goBack();
    },
    onError: () => Alert.alert('Error', 'Could not save plant. Check the backend connection.'),
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
    onError: () => Alert.alert('Error', 'Could not identify the photo. Check the backend connection.'),
  });

  const pickAndIdentify = async () => {
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.8,
    });
    if (res.canceled || !res.assets?.length) return;
    identifyMutation.mutate(res.assets[0]);
  };

  const filteredSpecies = speciesList.filter((s: Species) =>
    s.common_name.toLowerCase().includes(speciesSearch.toLowerCase()) ||
    s.scientific_name.toLowerCase().includes(speciesSearch.toLowerCase()),
  );

  const selectedSpecies = speciesList.find((s: Species) => s.id === speciesId);

  const canSubmit = nickname.trim().length > 0 && speciesId !== null;

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <Text variant="titleMedium" style={styles.sectionTitle}>Plant details</Text>

        <TextInput
          label="Nickname *"
          value={nickname}
          onChangeText={setNickname}
          mode="outlined"
          style={styles.input}
          placeholder="e.g. Sunny, Big Fern, Corner Cactus"
        />

        <Text variant="titleMedium" style={styles.sectionTitle}>Species *</Text>

        {aiIdAvailable && (
          <Button
            mode="outlined"
            icon="camera"
            onPress={pickAndIdentify}
            loading={identifyMutation.isPending}
            disabled={identifyMutation.isPending}
            style={styles.identifyBtn}
          >
            Identify from a photo
          </Button>
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

        {environments.length > 0 && (
          <>
            <Text variant="titleMedium" style={styles.sectionTitle}>Environment</Text>
            <View style={styles.envGrid}>
              {environments.map((e: Environment) => (
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
          </>
        )}

        <Text variant="titleMedium" style={styles.sectionTitle}>Location note</Text>
        <TextInput
          label="Where in the space?"
          value={location}
          onChangeText={setLocation}
          mode="outlined"
          style={styles.input}
          placeholder="e.g. South window, bathroom shelf"
        />

        <Text variant="titleMedium" style={styles.sectionTitle}>Initial condition</Text>
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
          buttonColor={theme.colors.primary}
        >
          Save plant
        </Button>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F6FAF7' },
  content: { padding: 16, paddingBottom: 48 },
  sectionTitle: { marginTop: 20, marginBottom: 8, fontWeight: '600', color: '#2D6A4F' },
  input: { marginBottom: 4 },
  suggestionBox: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 4 },
  suggestion: { marginBottom: 4 },
  identifyBtn: { marginBottom: 8, borderStyle: 'dashed' },
  identifyBox: {
    backgroundColor: '#EFF6F0',
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  identifyLabel: { color: '#52796F', marginBottom: 8, fontWeight: '600' },
  identifyObservation: { color: '#2F3E36', lineHeight: 19 },
  debugRawText: { fontFamily: 'monospace', fontSize: 11, color: '#6B7A70', marginTop: 4 },
  envGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 4 },
  envBtn: { marginBottom: 4 },
  segmented: { marginBottom: 8 },
  saveBtn: { marginTop: 24, borderRadius: 8 },
  saveBtnContent: { paddingVertical: 6 },
});
