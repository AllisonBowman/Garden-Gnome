import React, { useState } from 'react';
import { ScrollView, View, StyleSheet, Alert } from 'react-native';
import {
  Text, Card, Button, TextInput, SegmentedButtons,
  ActivityIndicator, FAB, Portal, Modal,
} from 'react-native-paper';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchEnvironments, createEnvironment } from '../api/environments';
import {
  Environment, EnvironmentType, Shelter, TempExposure, SunExposure,
} from '../types';

const ENV_TYPES: { value: EnvironmentType; label: string }[] = [
  { value: 'home',             label: '🏠 Home'        },
  { value: 'nursery',          label: '🌱 Nursery'     },
  { value: 'community_garden', label: '🌳 Community'   },
  { value: 'conservation',     label: '🌿 Conservation'},
  { value: 'research',         label: '🔬 Research'    },
];

// Sensible climate defaults per environment type — presets the toggles so most
// users don't have to think about it, but they can still adjust.
type Climate = { shelter: Shelter; temp_exposure: TempExposure; sun_exposure: SunExposure };
const CLIMATE_PRESETS: Record<EnvironmentType, Climate> = {
  home:             { shelter: 'sheltered', temp_exposure: 'indoor',  sun_exposure: 'partial_sun' },
  nursery:          { shelter: 'partial',   temp_exposure: 'outdoor', sun_exposure: 'full_sun'    },
  community_garden: { shelter: 'exposed',   temp_exposure: 'outdoor', sun_exposure: 'full_sun'    },
  conservation:     { shelter: 'exposed',   temp_exposure: 'outdoor', sun_exposure: 'full_sun'    },
  research:         { shelter: 'sheltered', temp_exposure: 'indoor',  sun_exposure: 'partial_sun' },
};

function EnvironmentCard({ env }: { env: Environment }) {
  const typeLabel = ENV_TYPES.find((t) => t.value === env.type)?.label ?? env.type;
  return (
    <Card style={styles.card} mode="elevated">
      <Card.Content>
        <Text variant="titleMedium">{env.name}</Text>
        <Text variant="bodySmall" style={styles.meta}>{typeLabel}</Text>
        {env.city ? (
          <Text variant="bodySmall" style={styles.meta}>📍 {env.city}{env.region ? `, ${env.region}` : ''}</Text>
        ) : null}
        <Text variant="bodySmall" style={styles.count}>{env.plant_count} plant{env.plant_count !== 1 ? 's' : ''}</Text>
      </Card.Content>
    </Card>
  );
}

export default function EnvironmentsScreen() {
  const queryClient = useQueryClient();
  const [modalVisible, setModalVisible] = useState(false);
  const [name, setName]     = useState('');
  const [type, setType]     = useState<EnvironmentType>('home');
  const [city, setCity]     = useState('');
  const [region, setRegion] = useState('');
  const [country, setCountry] = useState('');
  const [shelter, setShelter] = useState<Shelter>('sheltered');
  const [tempExposure, setTempExposure] = useState<TempExposure>('indoor');
  const [sunExposure, setSunExposure] = useState<SunExposure>('partial_sun');

  // Changing the type presets the climate toggles; the user can still tweak.
  const applyType = (t: EnvironmentType) => {
    setType(t);
    const preset = CLIMATE_PRESETS[t];
    if (preset) {
      setShelter(preset.shelter);
      setTempExposure(preset.temp_exposure);
      setSunExposure(preset.sun_exposure);
    }
  };

  const { data: environments = [], isLoading } = useQuery({
    queryKey: ['environments'],
    queryFn: fetchEnvironments,
  });

  const mutation = useMutation({
    mutationFn: () => createEnvironment({
      name, type, city, region, country,
      shelter, temp_exposure: tempExposure, sun_exposure: sunExposure,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environments'] });
      setModalVisible(false);
      setName(''); setCity(''); setRegion(''); setCountry('');
    },
    onError: () => Alert.alert('Error', 'Could not create environment.'),
  });

  if (isLoading) return <ActivityIndicator style={styles.center} size="large" />;

  return (
    <View style={{ flex: 1, backgroundColor: '#F6FAF7' }}>
      <ScrollView contentContainerStyle={styles.content}>
        {environments.length === 0 ? (
          <Text style={styles.empty}>No environments yet. Create one to get started.</Text>
        ) : (
          environments.map((e: Environment) => <EnvironmentCard key={e.id} env={e} />)
        )}
      </ScrollView>

      <FAB
        icon="plus"
        style={styles.fab}
        label="New environment"
        onPress={() => setModalVisible(true)}
      />

      <Portal>
        <Modal
          visible={modalVisible}
          onDismiss={() => setModalVisible(false)}
          contentContainerStyle={styles.modal}
        >
          <Text variant="titleLarge" style={styles.modalTitle}>New environment</Text>

          <TextInput label="Name *" value={name} onChangeText={setName} mode="outlined" style={styles.input} />

          <Text variant="labelMedium" style={styles.label}>Type</Text>
          <SegmentedButtons
            value={type}
            onValueChange={(v) => applyType(v as EnvironmentType)}
            buttons={[
              { value: 'home',    label: '🏠' },
              { value: 'nursery', label: '🌱' },
              { value: 'community_garden', label: '🌳' },
              { value: 'conservation', label: '🌿' },
              { value: 'research', label: '🔬' },
            ]}
            style={styles.segmented}
          />

          <TextInput label="City"    value={city}    onChangeText={setCity}    mode="outlined" style={styles.input} />
          <TextInput label="Region"  value={region}  onChangeText={setRegion}  mode="outlined" style={styles.input} />
          <TextInput label="Country" value={country} onChangeText={setCountry} mode="outlined" style={styles.input} />

          <Text variant="labelMedium" style={styles.label}>Shelter</Text>
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

          <Text variant="labelMedium" style={styles.label}>Temperature</Text>
          <SegmentedButtons
            value={tempExposure}
            onValueChange={(v) => setTempExposure(v as TempExposure)}
            buttons={[
              { value: 'indoor',  label: 'Indoor'  },
              { value: 'outdoor', label: 'Outdoor' },
            ]}
            style={styles.segmented}
          />

          <Text variant="labelMedium" style={styles.label}>Sun</Text>
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

          <Button
            mode="contained"
            onPress={() => mutation.mutate()}
            disabled={!name.trim() || mutation.isPending}
            loading={mutation.isPending}
            style={styles.saveBtn}
          >
            Create
          </Button>
        </Modal>
      </Portal>
    </View>
  );
}

const styles = StyleSheet.create({
  content: { padding: 12, paddingBottom: 96 },
  card: { marginBottom: 10, borderRadius: 12 },
  meta: { color: '#666', marginTop: 2 },
  count: { color: '#2D6A4F', marginTop: 4, fontWeight: '600' },
  fab: { position: 'absolute', right: 16, bottom: 24, backgroundColor: '#2D6A4F' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  empty: { textAlign: 'center', color: '#888', marginTop: 48 },
  modal: { backgroundColor: '#fff', margin: 20, borderRadius: 12, padding: 20 },
  modalTitle: { marginBottom: 16, fontWeight: '700' },
  label: { color: '#555', marginBottom: 6, marginTop: 8 },
  input: { marginBottom: 10 },
  segmented: { marginBottom: 12 },
  saveBtn: { marginTop: 8 },
});
