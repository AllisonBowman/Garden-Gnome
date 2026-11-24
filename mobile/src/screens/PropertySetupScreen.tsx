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
import { t } from '../i18n';

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
      <LoadError message={t('land.setup.loadFailed')} error={propertyQ.error}
        onRetry={() => propertyQ.refetch()} retrying={propertyQ.isRefetching} />
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled"
      scrollEnabled={!touching}>
      {step === 'address' && (
        <View>
          <Text style={styles.title} accessibilityRole="header">{t('land.setup.addTitle')}</Text>
          <Text style={styles.body}>
            {t('land.setup.addBody')}
          </Text>
          <AddressPicker onChange={onPlace} />
          <Button
            mode="contained"
            disabled={!place}
            onPress={() => setStep('pin')}
            style={styles.primary}
            accessibilityLabel={t('land.setup.nextA11y')}
          >
            {t('land.setup.next')}
          </Button>
        </View>
      )}

      {step === 'pin' && (
        <View>
          <Text style={styles.title} accessibilityRole="header">
            {editingId != null ? t('land.setup.movePin') : t('land.setup.putPin')}
          </Text>
          {!covered ? (
            <Text style={styles.body}>
              {t('land.setup.notCovered')}
            </Text>
          ) : null}

          {covered && imageryQ.isLoading ? <ActivityIndicator style={styles.spin} /> : null}

          {covered && imagery && src.uri && pin ? (
            <PinOnImage imagery={imagery} uri={src.uri} headers={src.headers} pin={pin} onPin={setPin}
              onGestureActive={setTouching} palette={palette} styles={styles} />
          ) : null}

          {covered && imageryQ.isError ? (
            <Text style={styles.body}>
              {editingId != null ? t('land.setup.noImageBefore') : t('land.setup.noImageFound')}
            </Text>
          ) : null}

          <Text style={styles.note}>
            {t('land.setup.pinNote')}
          </Text>

          {(createM.isError || editM.isError) ? (
            <Text style={styles.error}>
              {serverMessage(createM.error ?? editM.error, t('land.setup.saveFailed'))}
            </Text>
          ) : null}

          <Button
            mode="contained"
            disabled={!pin}
            onPress={() => setStep('lot')}
            style={styles.primary}
            accessibilityLabel={t('land.setup.confirmA11y')}
          >
            {t('land.setup.confirm')}
          </Button>
          {editingId == null ? (
            <Button mode="text" onPress={() => setStep('address')} textColor={palette.sub}
              accessibilityLabel={t('land.setup.backToAddressA11y')}>
              {t('land.setup.back')}
            </Button>
          ) : null}
        </View>
      )}

      {step === 'lot' && (
        <View>
          <Text style={styles.title} accessibilityRole="header">{t('land.setup.lotTitle')}</Text>
          <Text style={styles.body}>
            {t('land.setup.lotBody')}
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
                  accessibilityLabel={t(on ? 'land.selectedA11y' : 'land.notSelectedA11y', { label: c.label })}
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
              {serverMessage(createM.error ?? editM.error, t('land.setup.saveFailed'))}
            </Text>
          ) : null}
          <Button
            mode="contained"
            loading={createM.isPending || editM.isPending}
            disabled={createM.isPending || editM.isPending || !pin}
            onPress={() => (editingId != null ? editM.mutate() : createM.mutate())}
            style={styles.primary}
            accessibilityLabel={editingId != null ? t('land.setup.saveChangesA11y') : t('land.setup.saveLandA11y')}
          >
            {editingId != null ? t('land.setup.save') : t('land.setup.saveLand')}
          </Button>
          {editingId == null && lot.length === 0 ? (
            <Button mode="text" onPress={() => createM.mutate()} disabled={createM.isPending}
              textColor={palette.sub} accessibilityLabel={t('land.setup.skipA11y')}>
              {t('land.setup.skip')}
            </Button>
          ) : null}
          <Button mode="text" onPress={() => setStep('pin')} textColor={palette.sub}
            accessibilityLabel={t('land.setup.backToPinA11y')}>
            {t('land.setup.back')}
          </Button>
        </View>
      )}

      {step === 'reading' && status && (
        <View>
          <Text style={styles.title} accessibilityRole="header">{t('land.setup.readingTitle')}</Text>
          <Text style={styles.body}>
            {t('land.setup.readingBody')}
          </Text>
          {readingLines(status).map((l) => (
            <View key={l.key} style={styles.readRow} accessible
              accessibilityLabel={t('land.setup.readingA11y', { what: l.what, state: l.state })}>
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
            accessibilityLabel={t('land.setup.goHomeA11y')}>
            {t('land.setup.seeReport')}
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
      <Text style={styles.body}>{t('land.setup.dragPin')}</Text>
      <TopDownImage
        imagery={imagery}
        imageUri={uri}
        headers={headers}
        onTapPoint={fromPixel}
        onGestureActive={onGestureActive}
        accessibilityLabel={t('land.setup.imageA11y')}
      >
        {(ctx) => (
          <PinMarker ctx={ctx} at={at} imageSize={size} onMove={fromPixel}
            color={palette.warn} ring={palette.card} onGestureActive={onGestureActive} />
        )}
      </TopDownImage>
      <Text style={styles.credit}>
        {imagery.captured
          ? t('land.setup.creditTaken', { source: sourceText(imagery.source), captured: imagery.captured })
          : t('land.setup.credit', { source: sourceText(imagery.source) })}
      </Text>
      <View style={styles.nudges}>
        {(['north', 'west', 'east', 'south'] as Direction[]).map((d) => (
          <Button key={d} mode="outlined" compact onPress={() => move(d)} textColor={palette.acc}
            accessibilityLabel={t(`land.setup.nudge.${d}`)}>
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
