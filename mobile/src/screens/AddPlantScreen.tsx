import React, { useState } from 'react';
import {
  ScrollView, View, StyleSheet, Alert, KeyboardAvoidingView, Platform,
} from 'react-native';
import {
  Text, TextInput, Button, SegmentedButtons, useTheme,
  HelperText,
} from 'react-native-paper';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import { fetchSpeciesList } from '../api/species';
import { fetchEnvironments } from '../api/environments';
import { createPlant } from '../api/plants';
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
      location_description: location,
      initial_condition: condition,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plants'] });
      navigation.goBack();
    },
    onError: () => Alert.alert('Error', 'Could not save plant. Check the backend connection.'),
  });

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
  envGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 4 },
  envBtn: { marginBottom: 4 },
  segmented: { marginBottom: 8 },
  saveBtn: { marginTop: 24, borderRadius: 8 },
  saveBtnContent: { paddingVertical: 6 },
});
