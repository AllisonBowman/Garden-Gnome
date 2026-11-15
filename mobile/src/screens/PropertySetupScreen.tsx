import React, { useEffect, useMemo, useState } from 'react';
import { ScrollView, StyleSheet, View } from 'react-native';
import { ActivityIndicator, Button, Chip, Text } from 'react-native-paper';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation/types';
import {
  SITE_QUERY_KEYS, createProperty, fetchBlockImagery, fetchProperty, fetchPropertyImagery,
  fetchSiteProfile, refreshHome, updateProperty,
} from '../api/properties';
import { serverMessage } from '../api/errorMessage';
import { Imagery, LotContent, Property } from '../types/site';
import { ResolvedPlace } from '../location/geocode';
import AddressPicker from '../components/AddressPicker';
import TopDownImage from '../components/TopDownImage';
import LoadError from '../components/LoadError';
import { sourceText } from '../components/explainedText';
import PinMarker from '../land/PinMarker';
import { useImagerySource } from '../land/useImagerySource';
import {
  LatLng, clampToImage, latLngToPixel, pixelToLatLng,
} from '../land/imageGeometry';
import {
  Direction, MOVED_METRES, POLL_MS, createBody, editPatch, inUnitedStates, lotContentChoices,
  metresBetween, nudge, pinSourceFor, readingLines, stillReading, toggleLotContent,
} from '../land/setup';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';

type Nav = NativeStackNavigationProp<RootStackParamList, 'PropertySetup'>;
type Route = RouteProp<RootStackParamList, 'PropertySetup'>;
type Step = 'address' | 'pin' | 'lot' | 'reading';

// Property setup (build spec section 6): an address or "Use my location",
// then the pin on the top-down image, then "What's on your lot?" (skippable),
// then the profile being read, then Home. With a `propertyId` it goes back
// over that property's pin and lot contents instead, and saves the changes.
//
// The address only centres the image. What is stored is the pin the owner
// confirms; the address, city and country never reach our server.

export default function PropertySetupScreen() {
  const navigation = useNavigation<Nav>();
  const route = useRoute<Route>();
  const editingId = route.params?.propertyId ?? null;
  const queryClient = useQueryClient();
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);

  const [step, setStep] = useState<Step>(editingId == null ? 'address' : 'pin');
  const [place, setPlace] = useState<ResolvedPlace | null>(null);
  const [origin, setOrigin] = useState<'typed' | 'device'>('typed');
  const [start, setStart] = useState<LatLng | null>(null);
  const [pin, setPin] = useState<LatLng | null>(null);
  const [lot, setLot] = useState<LotContent[]>([]);
  const [created, setCreated] = useState<Property | null>(null);
  const [touching, setTouching] = useState(false);

  // ── Editing an existing property ──
  const propertyQ = useQuery({
    queryKey: SITE_QUERY_KEYS.property(editingId ?? -1),
    queryFn: () => fetchProperty(editingId!),
    enabled: editingId != null,
  });
  useEffect(() => {
    const p = propertyQ.data;
    if (!p || start) return;
    const at = { lat: p.pin_lat, lng: p.pin_lng };
    setStart(at); setPin(at); setLot(p.lot_contents);
  }, [propertyQ.data, start]);

  const covered = editingId != null
    ? (propertyQ.data ? inUnitedStates({ country: propertyQ.data.country, lat: propertyQ.data.pin_lat, lng: propertyQ.data.pin_lng }) : true)
    : place ? inUnitedStates(place) : true;

  // ── The image: around the chosen place, or around the property ──
  const imageryQ = useQuery<Imagery>({
    queryKey: editingId != null
      ? SITE_QUERY_KEYS.imagery(editingId)
      : ['imageryBlock', place?.lat ?? 0, place?.lng ?? 0],
    queryFn: () => (editingId != null ? fetchPropertyImagery(editingId) : fetchBlockImagery(place!.lat, place!.lng)),
    enabled: step === 'pin' && covered && (editingId != null ? propertyQ.data != null : place != null),
    retry: 1,
    staleTime: 60 * 60 * 1000,
  });
  const imagery = imageryQ.data ?? null;
  const src = useImagerySource(imagery);

  const onPlace = (p: ResolvedPlace | null, how?: 'typed' | 'device') => {
    setPlace(p);
    setOrigin(how ?? 'typed');
    if (p) { const at = { lat: p.lat, lng: p.lng }; setStart(at); setPin(at); }
  };

  const moved = pin != null && start != null && metresBetween(pin, start) >= MOVED_METRES;

  // ── Saving ──
  const createM = useMutation({
    mutationFn: () => createProperty(createBody(pin!, pinSourceFor(origin, moved), lot)),
    onSuccess: async (p) => {
      setCreated(p);
      setStep('reading');
      await refreshHome(queryClient);
    },
  });
  const editM = useMutation({
    mutationFn: () => updateProperty(editingId!, editPatch(
      { pin: start!, lotContents: propertyQ.data?.lot_contents ?? [] },
      { pin: pin!, lotContents: lot },
    )),
    onSuccess: async () => {
      await refreshHome(queryClient);
      navigation.goBack();
    },
  });

  // ── Reading the land after creating ──
  const profileQ = useQuery({
    queryKey: SITE_QUERY_KEYS.siteProfile(created?.id ?? -1),
    queryFn: () => fetchSiteProfile(created!.id),
    enabled: created != null,
    refetchInterval: (q) => (stillReading(q.state.data?.status ?? created?.profile_status) ? POLL_MS : false),
  });
  const status = profileQ.data?.status ?? created?.profile_status ?? null;

  const goHome = async () => {
    await refreshHome(queryClient);
    navigation.popTo('Home');
  };

  // ── Steps ──
  if (editingId != null && propertyQ.isLoading) {
    return <ActivityIndicator style={styles.center} size="large" />;
  }
  if (editingId != null && propertyQ.isError) {
    return (
      <LoadError message="Couldn’t load your land." error={propertyQ.error}
        onRetry={() => propertyQ.refetch()} retrying={propertyQ.isRefetching} />
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled"
      scrollEnabled={!touching}>
      {step === 'address' && (
        <View>
          <Text style={styles.title} accessibilityRole="header">Add your land</Text>
          <Text style={styles.body}>
            Type your address or use your location. The address is only used on this phone to find
            the right aerial image. You then put a pin on your home, and the pin is what PlantAdvocate stores.
          </Text>
          <AddressPicker onChange={onPlace} />
          <Button
            mode="contained"
            disabled={!place}
            onPress={() => setStep('pin')}
            style={styles.primary}
            accessibilityLabel="Next: put the pin on your home"
          >
            Next
          </Button>
        </View>
      )}

      {step === 'pin' && (
        <View>
          <Text style={styles.title} accessibilityRole="header">
            {editingId != null ? 'Move the pin' : 'Put the pin on your home'}
          </Text>
          {!covered ? (
            <Text style={styles.body}>
              The public land maps PlantAdvocate reads cover the United States only. You can still save
              this place: the seasonal plan will run on the weather forecast, and you can tell PlantAdvocate
              about your sun and soil yourself.
            </Text>
          ) : null}

          {covered && imageryQ.isLoading ? <ActivityIndicator style={styles.spin} /> : null}

          {covered && imagery && src.uri && pin ? (
            <PinOnImage imagery={imagery} uri={src.uri} headers={src.headers} pin={pin} onPin={setPin}
              onGestureActive={setTouching} palette={palette} styles={styles} />
          ) : null}

          {covered && imageryQ.isError ? (
            <Text style={styles.body}>
              The aerial image is not available right now. You can confirm the pin without it: it is
              placed where {editingId != null ? 'it was before' : 'the address search found'}, and you can
              move it later from Your land.
            </Text>
          ) : null}

          <Text style={styles.note}>
            The pin is what gets stored, not an address. Public soil, elevation and land maps are asked
            only about an area about 500 metres across that contains it.
          </Text>

          {(createM.isError || editM.isError) ? (
            <Text style={styles.error}>
              {serverMessage(createM.error ?? editM.error, 'Couldn’t save your land. Check your connection and try again.')}
            </Text>
          ) : null}

          <Button
            mode="contained"
            disabled={!pin}
            onPress={() => setStep('lot')}
            style={styles.primary}
            accessibilityLabel="Confirm the pin and continue"
          >
            This is my home
          </Button>
          {editingId == null ? (
            <Button mode="text" onPress={() => setStep('address')} textColor={palette.sub}
              accessibilityLabel="Back to the address">
              Back
            </Button>
          ) : null}
        </View>
      )}

      {step === 'lot' && (
        <View>
          <Text style={styles.title} accessibilityRole="header">What’s on your lot?</Text>
          <Text style={styles.body}>
            Tap any that apply. This is optional and you can change it later.
          </Text>
          <View style={styles.chips}>
            {lotContentChoices().map((c) => {
              const on = lot.includes(c.value);
              return (
                <Chip
                  key={c.value}
                  selected={on}
                  showSelectedCheck
                  onPress={() => setLot((cur) => toggleLotContent(cur, c.value))}
                  accessibilityLabel={`${c.label}. ${on ? 'Selected' : 'Not selected'}.`}
                  accessibilityState={{ selected: on }}
                  style={styles.chip}
                >
                  {c.label}
                </Chip>
              );
            })}
          </View>
          {(createM.isError || editM.isError) ? (
            <Text style={styles.error}>
              {serverMessage(createM.error ?? editM.error, 'Couldn’t save your land. Check your connection and try again.')}
            </Text>
          ) : null}
          <Button
            mode="contained"
            loading={createM.isPending || editM.isPending}
            disabled={createM.isPending || editM.isPending || !pin}
            onPress={() => (editingId != null ? editM.mutate() : createM.mutate())}
            style={styles.primary}
            accessibilityLabel={editingId != null ? 'Save the changes' : 'Save your land'}
          >
            {editingId != null ? 'Save' : 'Save your land'}
          </Button>
          {editingId == null && lot.length === 0 ? (
            <Button mode="text" onPress={() => createM.mutate()} disabled={createM.isPending}
              textColor={palette.sub} accessibilityLabel="Skip this and save your land">
              Skip
            </Button>
          ) : null}
          <Button mode="text" onPress={() => setStep('pin')} textColor={palette.sub}
            accessibilityLabel="Back to the pin">
            Back
          </Button>
        </View>
      )}

      {step === 'reading' && status && (
        <View>
          <Text style={styles.title} accessibilityRole="header">Reading your land</Text>
          <Text style={styles.body}>
            PlantAdvocate is reading public maps for the area around your pin. You do not need to wait:
            values fill in on Home and in Your land as they arrive.
          </Text>
          {readingLines(status).map((l) => (
            <View key={l.key} style={styles.readRow} accessible
              accessibilityLabel={`${l.what}. ${l.state}.`}>
              <Text style={styles.readMark}>{l.done ? '✓' : '…'}</Text>
              <View style={styles.readText}>
                <Text style={styles.readWhat}>{l.what}</Text>
                <Text style={styles.readState}>{l.state}</Text>
              </View>
            </View>
          ))}
          {stillReading(status) ? <ActivityIndicator style={styles.spin} /> : null}
          {(profileQ.data?.notes ?? []).map((n) => <Text key={n} style={styles.note}>{n}</Text>)}
          <Button mode="contained" onPress={() => void goHome()} style={styles.primary}
            accessibilityLabel="Go to Home">
            See your report
          </Button>
        </View>
      )}
    </ScrollView>
  );
}

type Styles = ReturnType<typeof makeStyles>;

function PinOnImage({ imagery, uri, headers, pin, onPin, onGestureActive, palette, styles }: {
  imagery: Imagery; uri: string; headers?: Record<string, string>;
  pin: LatLng; onPin: (p: LatLng) => void; onGestureActive: (active: boolean) => void;
  palette: Palette; styles: Styles;
}) {
  const { bounds, width, height } = imagery;
  const size = { width, height };
  const at = clampToImage(width, height, latLngToPixel(bounds, width, height, pin.lat, pin.lng));
  const fromPixel = (p: { x: number; y: number }) => {
    const q = clampToImage(width, height, p);
    onPin(pixelToLatLng(bounds, width, height, q.x, q.y));
  };
  const move = (d: Direction) => {
    const next = nudge(pin, d);
    const px = latLngToPixel(bounds, width, height, next.lat, next.lng);
    if (px.x < 0 || px.y < 0 || px.x > width || px.y > height) return;
    onPin(next);
  };
  return (
    <View>
      <Text style={styles.body}>Drag the pin onto your roof, or tap where your home is.</Text>
      <TopDownImage
        imagery={imagery}
        imageUri={uri}
        headers={headers}
        onTapPoint={fromPixel}
        onGestureActive={onGestureActive}
        accessibilityLabel="Aerial image of the area around your address, with a pin on your home"
      >
        {(ctx) => (
          <PinMarker ctx={ctx} at={at} imageSize={size} onMove={fromPixel}
            color={palette.warn} ring={palette.card} onGestureActive={onGestureActive} />
        )}
      </TopDownImage>
      <Text style={styles.credit}>
        {`Image: ${sourceText(imagery.source)}${imagery.captured ? `, taken ${imagery.captured}` : ''}.`}
      </Text>
      <View style={styles.nudges}>
        {(['north', 'west', 'east', 'south'] as Direction[]).map((d) => (
          <Button key={d} mode="outlined" compact onPress={() => move(d)} textColor={palette.acc}
            accessibilityLabel={`Move the pin a few metres ${d}`}>
            {d === 'north' ? '↑' : d === 'south' ? '↓' : d === 'east' ? '→' : '←'}
          </Button>
        ))}
      </View>
    </View>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  container: { flex: 1, backgroundColor: p.bg },
  content: { padding: 20, paddingBottom: 48 },
  center: { flex: 1, justifyContent: 'center', backgroundColor: p.bg },
  title: { color: p.acc, fontFamily: f.display, fontSize: 22, fontWeight: '700', marginBottom: 8 },
  body: { color: p.sub, fontSize: 15, lineHeight: 21, marginBottom: 12 },
  note: { color: p.faint, fontSize: 13, lineHeight: 19, marginTop: 10 },
  credit: { color: p.faint, fontSize: 12, marginTop: 6 },
  error: { color: p.warn, fontSize: 14, marginTop: 10 },
  primary: { marginTop: 16 },
  spin: { marginVertical: 16 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { marginBottom: 2 },
  nudges: { flexDirection: 'row', gap: 8, marginTop: 10, justifyContent: 'center' },
  readRow: { flexDirection: 'row', gap: 10, paddingVertical: 8 },
  readMark: { color: p.good, fontSize: 18, width: 20, textAlign: 'center' },
  readText: { flex: 1 },
  readWhat: { color: p.ink, fontSize: 15 },
  readState: { color: p.sub, fontSize: 13 },
});
