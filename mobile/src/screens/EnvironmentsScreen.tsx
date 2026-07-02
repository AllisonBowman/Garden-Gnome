import React, { useState } from 'react';
import { ScrollView, View, StyleSheet, Alert } from 'react-native';
import {
  Text, Card, Button, TextInput, SegmentedButtons,
  ActivityIndicator, FAB, Portal, Modal,
} from 'react-native-paper';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchEnvironments, createEnvironment } from '../api/environments';
import { Environment, EnvironmentType } from '../types';

const ENV_TYPES: { value: EnvironmentType; label: string }[] = [
  { value: 'home',             label: '🏠 Home'        },
  { value: 'nursery',          label: '🌱 Nursery'     },
  { value: 'community_garden', label: '🌳 Community'   },
  { value: 'conservation',     label: '🌿 Conservation'},
  { value: 'research',         label: '🔬 Research'    },
];

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
        <Text variant="bodySmall" style={styles.uuid}>UUID: {env.uuid}</Text>
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

  const { data: environments = [], isLoading } = useQuery({
    queryKey: ['environments'],
    queryFn: fetchEnvironments,
  });

  const mutation = useMutation({
    mutationFn: () => createEnvironment({ name, type, city, region, country }),
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
            onValueChange={(v) => setType(v as EnvironmentType)}
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
  uuid: { color: '#bbb', fontFamily: 'monospace', fontSize: 10, marginTop: 4 },
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
