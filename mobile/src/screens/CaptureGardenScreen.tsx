import React, { useMemo, useState, useCallback } from 'react';
import {
  View, StyleSheet, ScrollView, Alert, Platform,
} from 'react-native';
import {
  Text, TextInput, Button, Card, Chip, IconButton, ActivityIndicator, Snackbar,
} from 'react-native-paper';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useIsFocused, useNavigation } from '@react-navigation/native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchSpeciesList } from '../api/species';
import { fetchEnvironments } from '../api/environments';
import { createPlantsBulk, PlantDraft } from '../api/plants';
import { Species } from '../types';
import { splitUtterance } from '../capture/splitUtterance';
import { groundEntries, GroundedEntry, effectiveCount } from '../capture/ground';
import { CARE_TASKS_QUERY_KEY } from '../care/useCareTasks';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';
import Eyebrow from '../components/Eyebrow';

// Walk the garden and say what's in it.
//
// The camera is deliberately NOT doing the identifying — it can't. Apple's
// Vision classifier reduces a photo to a handful of coarse labels before the
// on-device model ever sees it, so a Pothos and a Heartleaf Philodendron are
// literally the same input. The person holding the phone already knows what
// they planted, so they are the recognizer here; the preview is for orientation
// and for keeping your hands and eyes where the plants are.
//
// Everything up to saving runs on-device: splitting the sentence, and matching
// each part against the cached catalog. That matters because gardens and
// allotments routinely have no signal, which is exactly where someone would be
// standing when they use this.

/** One row the caretaker is about to commit to. */
interface Draft extends GroundedEntry {
  id: string;
  speciesId: number | null;
  count: number;
}

let seq = 0;
const nextId = () => `d${seq++}`;

function toDraft(g: GroundedEntry): Draft {
  return {
    ...g,
    id: nextId(),
    // Only a confident match is pre-filled. A plausible one is offered but not
    // chosen, because a wrong species silently attaches wrong care data.
    speciesId: g.tier === 'confident' ? g.candidates[0].species.id : null,
    count: effectiveCount(g.entry),
  };
}

export default function CaptureGardenScreen() {
  const navigation = useNavigation();
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const queryClient = useQueryClient();
  const isFocused = useIsFocused();

  const [permission, requestPermission] = useCameraPermissions();
  const [heard, setHeard] = useState('');
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [note, setNote] = useState<string | null>(null);

  const { data: catalog = [], isLoading: catalogLoading } = useQuery({
    queryKey: ['species'],
    queryFn: fetchSpeciesList,
  });
  const { data: environments = [] } = useQuery({
    queryKey: ['environments'],
    queryFn: fetchEnvironments,
  });
  const [envId, setEnvId] = useState<number | null>(null);
  const targetEnv = envId ?? environments[0]?.id ?? null;

  const add = useCallback(() => {
    const grounded = groundEntries(splitUtterance(heard), catalog);
    if (!grounded.length) {
      setNote('Nothing to add there — try naming a plant.');
      return;
    }
    setDrafts((prev) => [...prev, ...grounded.map(toDraft)]);
    setHeard('');
  }, [heard, catalog]);

  const update = (id: string, patch: Partial<Draft>) =>
    setDrafts((prev) => prev.map((d) => (d.id === id ? { ...d, ...patch } : d)));
  const discard = (id: string) =>
    setDrafts((prev) => prev.filter((d) => d.id !== id));

  const ready = drafts.filter((d) => d.speciesId != null);

  const save = useMutation({
    mutationFn: () => createPlantsBulk(ready.map((d): PlantDraft => ({
      species_id: d.speciesId as number,
      quantity: d.count,
      location: d.entry.location,
      ...(targetEnv != null ? { environment_id: targetEnv } : {}),
    }))),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['plants'] });
      queryClient.invalidateQueries({ queryKey: CARE_TASKS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ['environments'] });
      setDrafts([]);
      navigation.goBack();
      void res;
    },
    onError: () => Alert.alert(
      'Nothing was saved',
      "PlantAdvocate couldn't reach the server, so your garden is still here — try again in a moment.",
    ),
  });

  const cameraUsable = permission?.granted && isFocused && Platform.OS !== 'web';

  return (
    <View style={styles.screen}>
      {/* Backdrop. The flow works without it — on the simulator, without
          permission, or on web there simply is no preview, and nothing else
          changes. */}
      {cameraUsable ? (
        <CameraView style={StyleSheet.absoluteFill} facing="back" />
      ) : (
        <View style={[StyleSheet.absoluteFill, styles.noCamera]} />
      )}
      <View style={[StyleSheet.absoluteFill, styles.scrim]} />

      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Eyebrow color={palette.btnInk}>WALK AND SAY WHAT YOU SEE</Eyebrow>

        {environments.length > 1 && (
          <View style={styles.envRow}>
            {environments.map((e) => (
              <Chip
                key={e.id}
                compact
                selected={targetEnv === e.id}
                onPress={() => setEnvId(e.id)}
                style={styles.envChip}
              >
                {e.name}
              </Chip>
            ))}
          </View>
        )}

        <TextInput
          mode="outlined"
          multiline
          value={heard}
          onChangeText={setHeard}
          placeholder="Twelve tomatoes along the south fence, a rosemary bush by the gate…"
          label="What's planted here?"
          style={styles.input}
          right={<TextInput.Icon icon="microphone" onPress={() => setNote(
            'Tap the microphone on your keyboard to speak instead of typing.',
          )} />}
        />
        <Button
          mode="contained"
          onPress={add}
          disabled={!heard.trim() || catalogLoading}
          style={styles.addBtn}
        >
          {catalogLoading ? 'Loading the catalog…' : 'Add these'}
        </Button>

        {permission && !permission.granted && (
          <Button mode="text" onPress={requestPermission} textColor={palette.btnInk}>
            Turn the camera on
          </Button>
        )}

        {drafts.map((d) => (
          <DraftCard
            key={d.id}
            draft={d}
            catalog={catalog}
            onChange={(patch) => update(d.id, patch)}
            onDiscard={() => discard(d.id)}
          />
        ))}

        {drafts.length > 0 && (
          <Button
            mode="contained"
            onPress={() => save.mutate()}
            loading={save.isPending}
            disabled={!ready.length || save.isPending}
            style={styles.saveBtn}
          >
            {ready.length === drafts.length
              ? `Add ${ready.length} to the garden`
              : `Add ${ready.length} of ${drafts.length} — pick a species for the rest`}
          </Button>
        )}
      </ScrollView>

      <Snackbar visible={note !== null} onDismiss={() => setNote(null)} duration={2600}>
        <Text style={styles.snackText}>{note}</Text>
      </Snackbar>
    </View>
  );
}

function DraftCard({
  draft, catalog, onChange, onDiscard,
}: {
  draft: Draft;
  catalog: Species[];
  onChange: (patch: Partial<Draft>) => void;
  onDiscard: () => void;
}) {
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const [search, setSearch] = useState('');

  const chosen = catalog.find((s) => s.id === draft.speciesId) ?? null;
  // A hand search is always available. "Peppermint" scores Peppers above Mint
  // on character overlap and no amount of splitting fixes a single word, so
  // there has to be a way through that doesn't depend on the match being right.
  const results = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return [];
    return catalog
      .filter((s) => s.common_name.toLowerCase().includes(q)
        || s.scientific_name.toLowerCase().includes(q))
      .slice(0, 6);
  }, [search, catalog]);

  return (
    <Card style={styles.card} mode="elevated">
      <Card.Content>
        <View style={styles.cardHead}>
          <Text style={styles.heard}>“{draft.entry.raw}”</Text>
          <IconButton icon="close" size={18} onPress={onDiscard} style={styles.discard} />
        </View>

        <View style={styles.fieldRow}>
          <TextInput
            mode="outlined"
            dense
            keyboardType="number-pad"
            value={String(draft.count)}
            onChangeText={(t) => onChange({ count: Math.max(1, parseInt(t, 10) || 1) })}
            style={styles.countInput}
            label="How many"
          />
          <View style={styles.speciesCell}>
            {chosen ? (
              <Chip
                compact
                icon="leaf"
                onClose={() => onChange({ speciesId: null })}
                style={styles.chosenChip}
              >
                {chosen.common_name}
              </Chip>
            ) : (
              <Text style={styles.unplaced}>
                {draft.tier === 'none'
                  ? 'Couldn’t place this one — search below.'
                  : 'Pick which one you meant.'}
              </Text>
            )}
          </View>
        </View>

        {draft.entry.location ? (
          <Text style={styles.place}>📍 {draft.entry.location}</Text>
        ) : null}

        {!chosen && (
          <>
            <View style={styles.candidates}>
              {draft.candidates.map((c) => (
                <Chip
                  key={c.species.id}
                  compact
                  onPress={() => onChange({ speciesId: c.species.id })}
                  style={styles.candidateChip}
                >
                  {c.species.common_name}
                </Chip>
              ))}
            </View>
            <TextInput
              mode="outlined"
              dense
              value={search}
              onChangeText={setSearch}
              placeholder="Search the catalog"
              style={styles.search}
            />
            {results.map((s) => (
              <Chip
                key={s.id}
                compact
                onPress={() => { onChange({ speciesId: s.id }); setSearch(''); }}
                style={styles.candidateChip}
              >
                {s.common_name}
              </Chip>
            ))}
          </>
        )}
      </Card.Content>
    </Card>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  screen: { flex: 1, backgroundColor: p.bg },
  noCamera: { backgroundColor: p.desk },
  // Keeps the overlaid text legible whether the backdrop is a live preview or
  // a flat colour.
  scrim: { backgroundColor: 'rgba(0,0,0,0.45)' },
  content: { padding: 16, paddingBottom: 48, gap: 10 },
  envRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  envChip: { backgroundColor: p.card },
  input: { backgroundColor: p.card },
  addBtn: { borderRadius: 8 },
  saveBtn: { borderRadius: 8, marginTop: 6 },
  card: { borderRadius: 12, backgroundColor: p.card },
  cardHead: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between' },
  heard: { flex: 1, fontStyle: 'italic', color: p.sub, fontSize: 13, lineHeight: 18 },
  discard: { margin: 0 },
  fieldRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 8 },
  countInput: { width: 90, backgroundColor: p.card },
  speciesCell: { flex: 1 },
  chosenChip: { alignSelf: 'flex-start', backgroundColor: p.accSoft },
  unplaced: { color: p.warn, fontSize: 13 },
  place: { color: p.faint, fontSize: 12, marginTop: 6 },
  candidates: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 8 },
  candidateChip: { backgroundColor: p.card2, marginTop: 4 },
  search: { marginTop: 8, backgroundColor: p.card },
  snackText: { color: p.btnInk },
});
