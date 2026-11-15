import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, View } from 'react-native';
import { ActivityIndicator, Button, Chip, Text, TextInput } from 'react-native-paper';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation/types';
import {
  SITE_QUERY_KEYS, deleteOverride, fetchProperty, fetchSiteProfile, putOverride, refreshHome,
  refreshSiteProfile, updateProperty,
} from '../api/properties';
import { serverMessage } from '../api/errorMessage';
import { FrostBias, LotContent, PropertyPatch, SiteProfile, SiteValue } from '../types/site';
import ExplainedBlock from '../components/ExplainedBlock';
import Eyebrow from '../components/Eyebrow';
import LoadError from '../components/LoadError';
import RefreshFailed from '../components/RefreshFailed';
import CorrectionControl from '../land/CorrectionControl';
import {
  FROST_BIAS_CHOICES, cleanName, drawnZones, groupValues, overrideBody, refetchEvery, sectionOf,
  wholeLotValues,
} from '../land/profileRows';
import { lotContentChoices, toggleLotContent } from '../land/setup';
import { profileProgressLine } from '../home/season';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';

type Nav = NativeStackNavigationProp<RootStackParamList, 'Land'>;
type Route = RouteProp<RootStackParamList, 'Land'>;

// Land: the site profile of one property (build spec section 6). Each value
// with its confidence, reason and source, and the owner's correction where
// the server allows one, grouped sun, soil and drainage, where water
// collects, slope and facing, flooding, hardiness zone, frost dates, then
// the land cover around. Then each drawn zone's values, with the zone map
// a tap away, and the property's own settings: name, pin, lot contents and
// the frost earlier or later setting. Refreshes itself while the server is
// still reading.

export default function LandScreen() {
  const navigation = useNavigation<Nav>();
  const { propertyId, zoneId, field } = useRoute<Route>().params;
  const queryClient = useQueryClient();
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const [pulling, setPulling] = useState(false);

  const profileKey = SITE_QUERY_KEYS.siteProfile(propertyId);
  const profileQ = useQuery({
    queryKey: profileKey,
    queryFn: () => fetchSiteProfile(propertyId),
    refetchInterval: (q) => refetchEvery(q.state.data?.status),
  });
  const propertyQ = useQuery({
    queryKey: SITE_QUERY_KEYS.property(propertyId),
    queryFn: () => fetchProperty(propertyId),
  });
  const profile = profileQ.data;
  const property = propertyQ.data;

  // ── Corrections ──
  const afterProfile = useCallback(async (next: SiteProfile) => {
    queryClient.setQueryData(profileKey, next);
    await refreshHome(queryClient);
  }, [queryClient, profileKey]);
  const setM = useMutation({
    mutationFn: (a: { v: SiteValue; value: unknown; zoneId?: number }) =>
      putOverride(propertyId, overrideBody(a.v, a.value, a.zoneId)),
    onSuccess: afterProfile,
  });
  const clearM = useMutation({
    mutationFn: (a: { v: SiteValue; zoneId?: number }) =>
      deleteOverride(propertyId, a.v.field, a.zoneId ?? a.v.zone_id ?? undefined),
    onSuccess: afterProfile,
  });
  const correcting = setM.isPending || clearM.isPending;

  // ── Property settings ──
  const patchM = useMutation({
    mutationFn: (patch: PropertyPatch) => updateProperty(propertyId, patch),
    onSuccess: async (p) => {
      queryClient.setQueryData(SITE_QUERY_KEYS.property(propertyId), p);
      await refreshHome(queryClient);
    },
  });
  const readAgainM = useMutation({
    mutationFn: () => refreshSiteProfile(propertyId),
    onSuccess: () => { void profileQ.refetch(); },
  });

  const [name, setName] = useState<string | null>(null);
  const [lot, setLot] = useState<LotContent[] | null>(null);
  useEffect(() => {
    if (property && name == null) setName(property.name);
    if (property && lot == null) setLot(property.lot_contents);
  }, [property, name, lot]);
  const lotChanged = property != null && lot != null
    && [...lot].sort().join(',') !== [...property.lot_contents].sort().join(',');

  // ── Opening at one value or one zone ──
  const scroll = useRef<ScrollView>(null);
  const offsets = useRef<Record<string, number>>({});
  const scrolled = useRef(false);
  const target = zoneId != null ? `zone-${zoneId}` : sectionOf(field);
  const remember = (key: string, y: number) => {
    offsets.current[key] = y;
    if (!scrolled.current && key === target) {
      scrolled.current = true;
      setTimeout(() => scroll.current?.scrollTo({ y: Math.max(0, y - 12), animated: true }), 50);
    }
  };

  const onRefresh = useCallback(async () => {
    setPulling(true);
    try { await Promise.all([profileQ.refetch(), propertyQ.refetch()]); } finally { setPulling(false); }
  }, [profileQ, propertyQ]);

  if (profileQ.isLoading) return <ActivityIndicator style={styles.center} size="large" />;
  if (!profile) {
    return (
      <LoadError message="Couldn’t load what is known about your land." error={profileQ.error}
        onRetry={() => profileQ.refetch()} retrying={profileQ.isRefetching} />
    );
  }

  const sections = groupValues(wholeLotValues(profile));
  const zones = drawnZones(profile);
  const progress = profileProgressLine(profile.status);
  const saveError = setM.error ?? clearM.error;

  const row = (v: SiteValue, zone?: number) => (
    <ExplainedBlock
      key={`${v.field}-${zone ?? v.zone_id ?? 'lot'}`}
      title={v.title}
      explained={v}
      initiallyOpen={zone == null && field === v.field}
    >
      <CorrectionControl
        value={v}
        busy={correcting}
        onSet={(value) => setM.mutate({ v, value, zoneId: zone })}
        onClear={() => clearM.mutate({ v, zoneId: zone })}
      />
    </ExplainedBlock>
  );

  return (
    <ScrollView
      ref={scroll}
      style={styles.container}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
      refreshControl={<RefreshControl refreshing={pulling} onRefresh={onRefresh} />}
    >
      {profileQ.isError ? <RefreshFailed onRetry={() => profileQ.refetch()} retrying={profileQ.isRefetching} /> : null}

      <Text style={styles.title} accessibilityRole="header">{property?.name ?? 'Your land'}</Text>
      {progress ? (
        <View style={styles.progress} accessible accessibilityLabel={progress}>
          {stillBusy(profile) ? <ActivityIndicator size={14} /> : null}
          <Text style={styles.quiet}>{progress}</Text>
        </View>
      ) : null}
      {saveError ? (
        <Text style={styles.error}>{serverMessage(saveError, 'Couldn’t save that change. Try again.')}</Text>
      ) : null}

      {sections.length === 0 ? (
        <Text style={styles.quietBlock}>
          {stillBusy(profile)
            ? 'Nothing has arrived yet. Values appear here as the public maps answer.'
            : 'No values could be read for this place. Outside the United States the public land maps do not reach; you can still describe each zone yourself on the zone map.'}
        </Text>
      ) : null}

      {sections.map((s) => (
        <View key={s.key} style={styles.section} onLayout={(e) => remember(s.key, e.nativeEvent.layout.y)}>
          <Eyebrow style={styles.eyebrow}>{s.title}</Eyebrow>
          {s.values.map((v) => row(v))}
        </View>
      ))}

      {profile.notes.map((n) => <Text key={n} style={styles.quietBlock}>{n}</Text>)}

      {/* ── Zones ── */}
      <View style={styles.section} onLayout={(e) => remember('zones', e.nativeEvent.layout.y)}>
        <Eyebrow style={styles.eyebrow}>Your zones</Eyebrow>
        {zones.length === 0 ? (
          <Text style={styles.quiet}>
            Draw a box over a bed, a lawn or a tree on the aerial image, and each one gets its own sun,
            soil and drainage values here.
          </Text>
        ) : null}
        {zones.map((z) => (
          <View key={z.zone_id} style={styles.zone} onLayout={(e) => remember(`zone-${z.zone_id}`, e.nativeEvent.layout.y + (offsets.current.zones ?? 0))}>
            <Text style={styles.zoneName} accessibilityRole="header">{z.name}</Text>
            {groupValues(z.values).flatMap((s) => s.values).map((v) => row(v, z.zone_id))}
            {z.values.length === 0 ? <Text style={styles.quiet}>No values for this zone yet.</Text> : null}
            <Button mode="text" compact textColor={palette.acc} style={styles.more}
              onPress={() => navigation.navigate('ZoneMap', { propertyId, zoneId: z.zone_id })}
              accessibilityLabel={`Show ${z.name} on the zone map`}>
              Show on the zone map
            </Button>
          </View>
        ))}
        <Button mode="outlined" textColor={palette.acc} style={styles.action}
          onPress={() => navigation.navigate('ZoneMap', { propertyId })}
          accessibilityLabel="Open the zone map to draw or change zones">
          {zones.length === 0 ? 'Draw zones on the map' : 'Open the zone map'}
        </Button>
      </View>

      {/* ── The property ── */}
      <View style={styles.section}>
        <Eyebrow style={styles.eyebrow}>This property</Eyebrow>

        <Text style={styles.label}>Name</Text>
        <View style={styles.inline}>
          <TextInput
            mode="outlined"
            dense
            value={name ?? ''}
            onChangeText={setName}
            style={styles.grow}
            accessibilityLabel="Property name"
          />
          <Button
            mode="outlined"
            textColor={palette.acc}
            disabled={patchM.isPending || !property || cleanName(name ?? '') == null || cleanName(name ?? '') === property.name}
            onPress={() => { const n = cleanName(name ?? ''); if (n) patchM.mutate({ name: n }); }}
            accessibilityLabel="Save the property name"
          >
            Save
          </Button>
        </View>

        <Text style={styles.label}>Pin</Text>
        <Text style={styles.quiet}>
          The pin on your home is the one place PlantAdvocate stores. Moving it reads the land again.
        </Text>
        <Button mode="outlined" textColor={palette.acc} style={styles.action}
          onPress={() => navigation.navigate('PropertySetup', { propertyId })}
          accessibilityLabel="Move the pin on your home">
          Move the pin
        </Button>

        <Text style={styles.label}>What’s on your lot</Text>
        <View style={styles.chips}>
          {lotContentChoices().map((c) => {
            const on = (lot ?? []).includes(c.value);
            return (
              <Chip key={c.value} selected={on} showSelectedCheck compact
                onPress={() => setLot((cur) => toggleLotContent(cur ?? [], c.value))}
                accessibilityLabel={`${c.label}. ${on ? 'Selected' : 'Not selected'}.`}
                accessibilityState={{ selected: on }}>
                {c.label}
              </Chip>
            );
          })}
        </View>
        {lotChanged ? (
          <Button mode="outlined" textColor={palette.acc} style={styles.action}
            disabled={patchM.isPending}
            onPress={() => patchM.mutate({ lot_contents: lot ?? [] })}
            accessibilityLabel="Save what is on your lot">
            Save lot contents
          </Button>
        ) : null}

        <Text style={styles.label}>Frost in your yard</Text>
        <Text style={styles.quiet}>
          Low spots and open ground often frost before the neighbourhood; ground near buildings often
          frosts later. This moves your frost warnings and tasks a little earlier or later. It does not
          change your hardiness zone.
        </Text>
        <View style={styles.chips}>
          {FROST_BIAS_CHOICES.map((c) => {
            const on = (property?.frost_bias ?? null) === c.value;
            return (
              <Chip key={c.label} selected={on} showSelectedCheck compact
                disabled={patchM.isPending || !property}
                onPress={() => { if (!on) patchM.mutate({ frost_bias: c.value as FrostBias | null }); }}
                accessibilityLabel={`${c.a11y}. ${on ? 'Selected' : 'Not selected'}.`}
                accessibilityState={{ selected: on }}>
                {c.label}
              </Chip>
            );
          })}
        </View>
        {patchM.isError ? (
          <Text style={styles.error}>{serverMessage(patchM.error, 'Couldn’t save that change. Try again.')}</Text>
        ) : null}

        <Button mode="text" textColor={palette.sub} style={styles.action}
          loading={readAgainM.isPending}
          disabled={readAgainM.isPending || stillBusy(profile)}
          onPress={() => readAgainM.mutate()}
          accessibilityLabel="Read the public maps for your land again">
          Read the public maps again
        </Button>
      </View>
    </ScrollView>
  );
}

function stillBusy(p: SiteProfile): boolean {
  return refetchEvery(p.status) !== false;
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  container: { flex: 1, backgroundColor: p.bg },
  content: { padding: 20, paddingBottom: 48 },
  center: { flex: 1, justifyContent: 'center', backgroundColor: p.bg },
  title: { color: p.acc, fontFamily: f.display, fontSize: 22, fontWeight: '700', marginBottom: 6 },
  progress: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 },
  section: { marginTop: 18 },
  eyebrow: { marginBottom: 4 },
  quiet: { color: p.sub, fontSize: 13, lineHeight: 19 },
  quietBlock: { color: p.sub, fontSize: 14, lineHeight: 20, marginTop: 12 },
  error: { color: p.warn, fontSize: 14, marginTop: 6 },
  zone: { marginTop: 10, paddingTop: 8, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: p.line },
  zoneName: { color: p.ink, fontFamily: f.display, fontSize: 17, fontWeight: '600' },
  more: { alignSelf: 'flex-start' },
  action: { alignSelf: 'flex-start', marginTop: 8 },
  label: { color: p.faint, fontFamily: f.label, fontSize: 13, marginTop: 14, marginBottom: 4 },
  inline: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  grow: { flex: 1 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 4 },
});
