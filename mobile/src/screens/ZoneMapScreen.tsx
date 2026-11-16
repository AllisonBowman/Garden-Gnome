import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert, LayoutChangeEvent, PanResponder, ScrollView, StyleSheet, View,
} from 'react-native';
import { ActivityIndicator, Button, Card, Chip, Text, TextInput } from 'react-native-paper';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { RouteProp, useRoute } from '@react-navigation/native';
import type { RootStackParamList } from '../navigation/types';
import {
  SITE_QUERY_KEYS, createZone, deleteZone, fetchProperty, fetchPropertyImagery, fetchSiteProfile,
  fetchZones, putOverride, refreshHome, updateZone,
} from '../api/properties';
import { Box, Imagery, SiteProfile, Zone } from '../types/site';
import TopDownImage, { TopDownImageContext } from '../components/TopDownImage';
import ExplainedBlock from '../components/ExplainedBlock';
import Eyebrow from '../components/Eyebrow';
import LoadError from '../components/LoadError';
import { useImagerySource } from '../land/useImagerySource';
import { pixelRectToBox } from '../land/imageGeometry';
import {
  ZoneRect, mapInk, placeLabels, viewRect, yardFocus, zoneRects as layoutZoneRects,
} from '../land/mapLayout';
import MapLabels from '../components/MapLabels';
import {
  HANDLES, HANDLE_NAMES, Handle, Point, Rect, contains, handlePoint, hitHandle, hitZone,
  isUsableRect, moveHandle, moveRect, rectFromCorners, scaleRect,
} from '../zones/boxEdit';
import {
  DELETE_REFUSED, LEAF_HABIT_CHOICES, VEGETATION_CHOICES, VEGETATION_WORDS, ZoneDraft,
  correctionQuestions, defaultZoneBox, deleteBlockedReason, draftFromZone,
  draftProblem, emptyDraft, leafHabitApplies, mapZoneLabel, zoneA11yLabel, zoneLabel,
  zoneShownValues, zoneValuesPending,
} from '../zones/describe';
import { AnswersNotSaved, saveZone } from '../zones/save';
import { useAppTheme } from '../theme/ThemeProvider';
import { Palette, Fonts } from '../theme/tokens';

type Route = RouteProp<RootStackParamList, 'ZoneMap'>;
type Styles = ReturnType<typeof makeStyles>;

// The zone map (build spec section 6): the property's top-down image with
// its zones drawn as labelled boxes. "Add a bed or area" stretches a box
// (pan and zoom are off while drawing; corner handles adjust it), then the
// owner describes it by taps: what grows there, leaf habit for trees and
// shrubs, and optional sun and soil corrections. "Add a zone without
// drawing" makes the same zone from the same taps with a default box. A tap
// on a box opens it to rename, redescribe, redraw or delete. After saving,
// the zone's sun estimate and where water collects show with their
// confidence once the server has them.

type Mode =
  | { kind: 'view' }
  | { kind: 'draw'; zone: Zone | null }
  | { kind: 'describe'; zone: Zone | null; noDraw: boolean };

/** How close, in view pixels, a finger must land to grab a corner handle. */
const HANDLE_GRAB_PX = 28;
const HANDLE_SIZE = 22;
/** Re-ask for a new zone's values this often, this many times. */
const VALUES_POLL_MS = 5000;
const VALUES_POLL_TRIES = 12;

export default function ZoneMapScreen() {
  const { params } = useRoute<Route>();
  const { propertyId } = params;
  const { palette, fonts } = useAppTheme();
  const styles = useMemo(() => makeStyles(palette, fonts), [palette, fonts]);
  const ink = mapInk(palette);
  const queryClient = useQueryClient();

  const imageryQ = useQuery({
    queryKey: SITE_QUERY_KEYS.imagery(propertyId),
    queryFn: () => fetchPropertyImagery(propertyId),
    retry: 1,
  });
  const propertyQ = useQuery({
    queryKey: SITE_QUERY_KEYS.property(propertyId),
    queryFn: () => fetchProperty(propertyId),
  });
  const profileQ = useQuery({
    queryKey: SITE_QUERY_KEYS.siteProfile(propertyId),
    queryFn: () => fetchSiteProfile(propertyId),
  });

  const [savedZoneId, setSavedZoneId] = useState<number | null>(null);
  const [polls, setPolls] = useState(0);
  const zonesQ = useQuery({
    queryKey: SITE_QUERY_KEYS.zones(propertyId),
    queryFn: () => fetchZones(propertyId),
    refetchInterval: (q) => {
      if (savedZoneId == null || polls >= VALUES_POLL_TRIES) return false;
      const z = q.state.data?.find((x) => x.id === savedZoneId);
      return z && zoneValuesPending(z.values) ? VALUES_POLL_MS : false;
    },
  });
  useEffect(() => {
    if (savedZoneId != null && zonesQ.dataUpdatedAt) setPolls((n) => n + 1);
  }, [zonesQ.dataUpdatedAt, savedZoneId]);

  const imagery = imageryQ.data ?? null;
  const { uri, headers } = useImagerySource(imagery);
  const zones = zonesQ.data ?? [];

  const [mode, setMode] = useState<Mode>({ kind: 'view' });
  const [rect, setRectState] = useState<Rect | null>(null);
  // Whether the owner drew or adjusted the box in this edit. Only then is a
  // box sent, so opening the approximate yard never turns it into a drawing.
  const [boxEdited, setBoxEdited] = useState(false);
  const setRect = (r: Rect | null) => { setRectState(r); setBoxEdited(true); };
  const [draft, setDraft] = useState<ZoneDraft>(emptyDraft());
  const [saving, setSaving] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  // Zones as image rectangles, for drawing and for taps.
  const zoneRects = useMemo(() => (imagery ? layoutZoneRects(imagery, zones) : []), [zones, imagery]);

  const openZone = (z: Zone) => {
    setDraft(draftFromZone(z));
    const zr = zoneRects.find((r) => r.id === z.id);
    setRectState(zr ? zr.rect : null);
    setBoxEdited(false);
    setProblem(null);
    setSavedZoneId(null);
    setMode({ kind: 'describe', zone: z, noDraw: false });
  };

  // Home or Land can open one zone directly.
  const opened = useRef(false);
  useEffect(() => {
    if (opened.current || params.zoneId == null || !zonesQ.data) return;
    const z = zonesQ.data.find((x) => x.id === params.zoneId);
    if (z) { opened.current = true; openZone(z); }
    // openZone is stable enough for a one-time open.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.zoneId, zonesQ.data, zoneRects]);

  const startDrawing = (zone: Zone | null) => {
    if (!zone) { setDraft(emptyDraft()); setRectState(null); setBoxEdited(false); }
    setProblem(null);
    setSavedZoneId(null);
    setMode({ kind: 'draw', zone });
  };

  const startWithoutDrawing = () => {
    setDraft(emptyDraft());
    setRectState(null);
    setBoxEdited(false);
    setProblem(null);
    setSavedZoneId(null);
    setMode({ kind: 'describe', zone: null, noDraw: true });
  };

  const cancel = () => {
    setMode({ kind: 'view' });
    setRectState(null);
    setBoxEdited(false);
    setProblem(null);
  };

  /** The box to save, in degrees. */
  const boxToSave = (): Box | null => {
    if (mode.kind !== 'describe') return null;
    if (boxEdited && rect && imagery && isUsableRect(rect)) {
      return pixelRectToBox(imagery.bounds, imagery.width, imagery.height, rect);
    }
    if (mode.zone) return mode.zone.box ?? null;
    if (mode.noDraw) {
      const pin = propertyQ.data ? { lat: propertyQ.data.pin_lat, lng: propertyQ.data.pin_lng } : null;
      return pin || imagery?.default_footprint ? defaultZoneBox(imagery, pin ?? { lat: 0, lng: 0 }) : null;
    }
    return null;
  };

  const save = async () => {
    if (mode.kind !== 'describe') return;
    const box = boxToSave();
    // The whole-lot zone has no vegetation type to choose, and keeps its box.
    const why = mode.zone?.is_whole_lot
      ? null
      : draftProblem(draft, box) ?? (box ? null : 'The map has not loaded yet. Try again in a moment.');
    if (why) { setProblem(why); return; }
    setSaving(true);
    setProblem(null);
    const remember = (saved: Zone) => {
      queryClient.setQueryData<Zone[]>(SITE_QUERY_KEYS.zones(propertyId), (old) => {
        const list = old ?? [];
        return list.some((z) => z.id === saved.id) ? list.map((z) => (z.id === saved.id ? saved : z)) : [...list, saved];
      });
    };
    try {
      const { zone, profile } = await saveZone({
        createZone: (body) => createZone(propertyId, body),
        updateZone: (zoneId, patch) => updateZone(propertyId, zoneId, patch),
        putOverride: (body) => putOverride(propertyId, body),
      }, {
        existing: mode.zone, draft, box, boxEdited, noDraw: mode.noDraw,
        existingNames: zones.map((z) => z.name),
      }, (created) => {
        // The zone exists now: if an answer fails, Save again edits this
        // zone instead of creating a second one.
        remember(created);
        setMode({ kind: 'describe', zone: created, noDraw: mode.noDraw });
      });
      if (profile) queryClient.setQueryData(SITE_QUERY_KEYS.siteProfile(propertyId), profile);
      remember(zone);
      setPolls(0);
      setSavedZoneId(zone.id);
      setMode({ kind: 'view' });
      setRectState(null);
      setBoxEdited(false);
      // The zone is saved; a Home refresh that fails is not a failed save.
      await refreshHome(queryClient).catch(() => undefined);
    } catch (err) {
      setProblem(err instanceof AnswersNotSaved
        ? 'The zone was saved, but your answers about it were not. Check your connection and tap Save again.'
        : 'That zone was not saved. Check your connection and try again.');
    } finally {
      setSaving(false);
    }
  };

  const remove = (z: Zone) => {
    const blocked = deleteBlockedReason(z);
    if (blocked) { Alert.alert('This zone stays', blocked); return; }
    Alert.alert('Delete this zone?', `"${z.name}" and its corrections will be removed.`, [
      { text: 'Keep it', style: 'cancel' },
      {
        text: 'Delete', style: 'destructive', onPress: async () => {
          try {
            await deleteZone(propertyId, z.id);
            queryClient.setQueryData<Zone[]>(SITE_QUERY_KEYS.zones(propertyId), (old) => (old ?? []).filter((x) => x.id !== z.id));
            cancel();
            await refreshHome(queryClient);
          } catch (err) {
            const refused = axios.isAxiosError(err) && err.response?.status === 409;
            Alert.alert('Not deleted', refused ? DELETE_REFUSED : 'The zone was not deleted. Check your connection and try again.');
          }
        },
      },
    ]);
  };

  if (zonesQ.isLoading) return <ActivityIndicator style={styles.center} size="large" />;
  if (!zonesQ.data) {
    return (
      <LoadError
        message="Couldn’t load your zones."
        error={zonesQ.error}
        onRetry={() => zonesQ.refetch()}
        retrying={zonesQ.isRefetching}
      />
    );
  }

  const drawing = mode.kind === 'draw';
  const editingId = mode.kind !== 'view' ? mode.zone?.id ?? null : null;
  const savedZone = savedZoneId != null ? zones.find((z) => z.id === savedZoneId) ?? null : null;
  const lotValues = profileQ.data?.values ?? null;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} scrollEnabled={!drawing}>
      <Text style={styles.headline} accessibilityRole="header">Your zones</Text>
      <Text style={styles.intro}>
        {drawing
          ? 'Drag across the image to stretch a box over the bed or area. Drag a corner to adjust it, or drag the middle to move it.'
          : 'Each box is a part of your land. Tap one to change it.'}
      </Text>

      {imagery && uri ? (
        <TopDownImage
          imagery={imagery}
          imageUri={uri}
          headers={headers}
          gesturesEnabled={!drawing}
          initialFocus={yardFocus(imagery)}
          onTapPoint={drawing ? undefined : (p) => {
            const hit = hitZone(zoneRects, p);
            if (hit) openZone(hit.zone);
          }}
          accessibilityLabel={`Top-down aerial image of your land. ${imagery.source.name}${imagery.captured ? `, ${imagery.captured}` : ''}.`}
        >
          {(ctx) => (
            <>
              {zoneRects.map((zr) => (
                <ZoneBox
                  key={zr.id}
                  zone={zr.zone}
                  rect={zr.id === editingId && rect ? rect : zr.rect}
                  ctx={ctx}
                  active={zr.id === editingId}
                  styles={styles}
                />
              ))}
              <ZoneLabels
                rects={zoneRects.filter((zr) => zr.id !== editingId)}
                ctx={ctx}
                ink={ink}
              />
              {mode.kind !== 'view' && !editingId && rect ? <DraftBox rect={rect} ctx={ctx} styles={styles} /> : null}
              {drawing ? (
                <DrawLayer imagery={imagery} rect={rect} onRect={setRect} ctx={ctx} styles={styles} />
              ) : null}
            </>
          )}
        </TopDownImage>
      ) : imageryQ.isLoading || (imagery && !uri) ? (
        <ActivityIndicator style={styles.inlineSpin} />
      ) : (
        <Text style={styles.quietBlock}>
          The aerial image is not available right now, so boxes cannot be drawn. You can still add a zone without drawing.
        </Text>
      )}
      {imagery ? (
        <Text style={styles.credit}>
          {`Image: ${imagery.source.name}${imagery.captured ? `, ${imagery.captured}` : ''}.`}
        </Text>
      ) : null}

      {/* Screen-reader and no-gesture path to every zone. */}
      {mode.kind === 'view' && (
        <View style={styles.section}>
          <Eyebrow style={styles.eyebrow}>Zones</Eyebrow>
          {zones.map((z) => (
            <Button
              key={z.id}
              mode="text"
              compact
              onPress={() => openZone(z)}
              accessibilityLabel={zoneA11yLabel(z)}
              contentStyle={styles.zoneRowContent}
              style={styles.zoneRow}
              textColor={palette.ink}
            >
              {`${zoneLabel(z)}${z.vegetation_type && VEGETATION_WORDS[z.vegetation_type] !== zoneLabel(z) ? ` · ${VEGETATION_WORDS[z.vegetation_type]}` : ''}`}
            </Button>
          ))}
          <View style={styles.actions}>
            <Button
              mode="contained"
              icon="vector-square"
              disabled={!imagery || !uri}
              onPress={() => startDrawing(null)}
              accessibilityLabel="Add a bed or area by drawing a box on the image"
              buttonColor={palette.btn}
              textColor={palette.btnInk}
            >
              Add a bed or area
            </Button>
            <Button
              mode="outlined"
              onPress={startWithoutDrawing}
              accessibilityLabel="Add a zone without drawing"
            >
              Add a zone without drawing
            </Button>
          </View>
        </View>
      )}

      {drawing && imagery && (
        <View style={styles.section}>
          <View style={styles.actions}>
            <Button
              mode="contained"
              disabled={!isUsableRect(rect)}
              onPress={() => setMode({ kind: 'describe', zone: mode.zone, noDraw: false })}
              accessibilityLabel="Done drawing. Describe this area next."
              buttonColor={palette.btn}
              textColor={palette.btnInk}
            >
              Done drawing
            </Button>
            <Button
              mode="outlined"
              disabled={!rect}
              onPress={() => rect && setRect(scaleRect(rect, 1.25, imagery.width, imagery.height))}
              accessibilityLabel="Make the box bigger"
            >
              Bigger
            </Button>
            <Button
              mode="outlined"
              disabled={!rect}
              onPress={() => rect && setRect(scaleRect(rect, 0.8, imagery.width, imagery.height))}
              accessibilityLabel="Make the box smaller"
            >
              Smaller
            </Button>
            <Button
              mode="text"
              disabled={!rect || !!mode.zone}
              onPress={() => setRect(null)}
              accessibilityLabel="Start the box over"
            >
              Start over
            </Button>
            <Button mode="text" onPress={cancel} accessibilityLabel="Cancel drawing">Cancel</Button>
          </View>
        </View>
      )}

      {mode.kind === 'describe' && (
        <DescribePanel
          mode={mode}
          draft={draft}
          setDraft={setDraft}
          lotValues={lotValues}
          canRedraw={!!imagery && !!uri}
          onRedraw={() => startDrawing(mode.zone)}
          onSave={save}
          onCancel={cancel}
          onDelete={mode.zone ? () => remove(mode.zone!) : undefined}
          saving={saving}
          problem={problem}
          styles={styles}
        />
      )}

      {mode.kind === 'view' && savedZone && (
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.cardTitle} accessibilityRole="header">{`Saved: ${savedZone.name}`}</Text>
            {zoneShownValues(savedZone.values).map((v) => (
              <ExplainedBlock key={v.field} explained={v} title={v.title} />
            ))}
            {zoneValuesPending(savedZone.values) ? (
              <Text style={styles.quiet} accessibilityLiveRegion="polite">
                {polls < VALUES_POLL_TRIES
                  ? 'Working out the sun and where water collects for this zone. They show here when ready.'
                  : 'Some values for this zone are not ready yet. They will show on your land page when they are.'}
              </Text>
            ) : null}
          </Card.Content>
        </Card>
      )}
    </ScrollView>
  );
}

// ── Boxes ────────────────────────────────────────────────────────────────────

function ZoneBox({ zone, rect, ctx, active, styles }: {
  zone: Zone; rect: Rect; ctx: TopDownImageContext; active: boolean; styles: Styles;
}) {
  const approximate = zone.is_whole_lot && zone.boundary_source === 'default';
  return (
    <View
      pointerEvents="none"
      style={[styles.box, approximate && styles.boxApprox, active && styles.boxActive, viewRect(rect, ctx)]}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {/* Only the box being edited carries its name inside it; the others
          are named by ZoneLabels, placed so names never break inside a word. */}
      {active ? <Text style={styles.boxLabel} numberOfLines={2}>{mapZoneLabel(zone)}</Text> : null}
    </View>
  );
}

/**
 * The names of the boxes not being edited, placed the way LandMap places
 * them (mapLayout.placeLabels, MapLabels): wrapped only at spaces, at most
 * two lines, outside the box when it does not fit, inside the view, on a
 * see-through plate. Drawn zones come before the whole lot so their names
 * win. Decorative and touch-transparent: taps still reach the image.
 */
function ZoneLabels({ rects, ctx, ink }: {
  rects: ZoneRect[]; ctx: TopDownImageContext; ink: { line: string; halo: string };
}) {
  const [size, setSize] = useState({ width: 0, height: 0 });
  const onLayout = (e: LayoutChangeEvent) => {
    const { width, height } = e.nativeEvent.layout;
    setSize({ width, height });
  };
  const ordered = [...rects].sort((a, b) => Number(a.zone.is_whole_lot) - Number(b.zone.is_whole_lot));
  const labels = size.width > 0
    ? placeLabels(ordered.map((r) => ({ id: r.id, text: mapZoneLabel(r.zone), box: viewRect(r.rect, ctx) })), size)
    : [];
  return (
    <View
      style={StyleSheet.absoluteFill}
      pointerEvents="none"
      onLayout={onLayout}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <MapLabels labels={labels} width={size.width} ink={ink} />
    </View>
  );
}

function DraftBox({ rect, ctx, styles }: { rect: Rect; ctx: TopDownImageContext; styles: Styles }) {
  return <View pointerEvents="none" style={[styles.box, styles.boxActive, viewRect(rect, ctx)]} />;
}

type Drag =
  | { kind: 'new'; start: Point }
  | { kind: 'handle'; handle: Handle }
  | { kind: 'move'; start: Point; from: Rect };

/**
 * The drawing surface: one plain view over the image that owns every touch
 * while drawing (the image's own pan and zoom are off). A drag on empty
 * image stretches a new box; a drag near a corner moves that corner; a drag
 * inside the box moves it.
 */
function DrawLayer({ imagery, rect, onRect, ctx, styles }: {
  imagery: Imagery; rect: Rect | null; onRect: (r: Rect | null) => void;
  ctx: TopDownImageContext; styles: Styles;
}) {
  const live = useRef({ rect, ctx, onRect });
  live.current = { rect, ctx, onRect };
  const drag = useRef<Drag | null>(null);
  const { width, height } = imagery;

  const responder = useMemo(() => PanResponder.create({
    onStartShouldSetPanResponder: () => true,
    onMoveShouldSetPanResponder: () => true,
    onPanResponderTerminationRequest: () => false,
    onPanResponderGrant: (e) => {
      const { rect: r, ctx: c } = live.current;
      const p = c.toImage({ x: e.nativeEvent.locationX, y: e.nativeEvent.locationY });
      const handle = r ? hitHandle(r, p, HANDLE_GRAB_PX / c.scale) : null;
      if (r && handle) drag.current = { kind: 'handle', handle };
      else if (r && contains(r, p)) drag.current = { kind: 'move', start: p, from: r };
      else drag.current = { kind: 'new', start: p };
    },
    onPanResponderMove: (e) => {
      const d = drag.current;
      const { rect: r, ctx: c, onRect: set } = live.current;
      if (!d) return;
      const p = c.toImage({ x: e.nativeEvent.locationX, y: e.nativeEvent.locationY });
      if (d.kind === 'new') set(rectFromCorners(d.start, p, width, height));
      else if (d.kind === 'handle' && r) set(moveHandle(r, d.handle, p, width, height));
      else if (d.kind === 'move') set(moveRect(d.from, p.x - d.start.x, p.y - d.start.y, width, height));
    },
    onPanResponderRelease: () => {
      const d = drag.current;
      drag.current = null;
      // A tap on empty image, not a stretch: leave no box behind.
      if (d?.kind === 'new' && !isUsableRect(live.current.rect)) live.current.onRect(null);
    },
    onPanResponderTerminate: () => { drag.current = null; },
  }), [width, height]);

  return (
    <View
      style={StyleSheet.absoluteFill}
      {...responder.panHandlers}
      accessible
      accessibilityLabel="Drawing area. Drag to stretch a box. Use the Bigger and Smaller buttons below to adjust it without dragging."
    >
      {rect ? HANDLES.map((h) => {
        const q = ctx.toView(handlePoint(rect, h));
        return (
          <View
            key={h}
            pointerEvents="none"
            accessibilityLabel={`${HANDLE_NAMES[h]} corner handle`}
            style={[styles.handle, { left: q.x - HANDLE_SIZE / 2, top: q.y - HANDLE_SIZE / 2 }]}
          />
        );
      }) : null}
    </View>
  );
}

// ── Describing ───────────────────────────────────────────────────────────────

function DescribePanel({
  mode, draft, setDraft, lotValues, canRedraw, onRedraw, onSave, onCancel, onDelete, saving,
  problem, styles,
}: {
  mode: Extract<Mode, { kind: 'describe' }>;
  draft: ZoneDraft;
  setDraft: (d: ZoneDraft) => void;
  lotValues: SiteProfile['values'] | null;
  canRedraw: boolean;
  onRedraw: () => void;
  onSave: () => void;
  onCancel: () => void;
  onDelete?: () => void;
  saving: boolean;
  problem: string | null;
  styles: Styles;
}) {
  const zone = mode.zone;
  const questions = correctionQuestions(zone?.values, lotValues);
  const blocked = zone ? deleteBlockedReason(zone) : null;
  const wholeLot = !!zone?.is_whole_lot;

  return (
    <Card style={styles.card}>
      <Card.Content>
        <Text style={styles.cardTitle} accessibilityRole="header">
          {zone ? `Change ${zone.name}` : 'Describe this area'}
        </Text>
        {mode.noDraw ? (
          <Text style={styles.quiet}>
            Without a drawing, this zone covers your whole approximate yard. Draw its box later to make its values more exact.
          </Text>
        ) : null}

        <TextInput
          label="Name (optional)"
          value={draft.name}
          onChangeText={(name) => setDraft({ ...draft, name })}
          mode="outlined"
          style={styles.input}
          accessibilityLabel="Zone name, optional"
        />

        {!wholeLot && (
          <>
            <Text style={styles.question}>What grows there?</Text>
            <View style={styles.chips}>
              {VEGETATION_CHOICES.map((c) => (
                <Chip
                  key={c.value}
                  selected={draft.vegetation === c.value}
                  onPress={() => setDraft({ ...draft, vegetation: c.value })}
                  accessibilityLabel={`${c.label}. ${c.hint}`}
                  accessibilityState={{ selected: draft.vegetation === c.value }}
                  style={styles.chip}
                >
                  {c.label}
                </Chip>
              ))}
            </View>
          </>
        )}

        {leafHabitApplies(draft.vegetation) && (
          <>
            <Text style={styles.question}>Do they lose their leaves?</Text>
            <View style={styles.chips}>
              {LEAF_HABIT_CHOICES.map((c) => (
                <Chip
                  key={c.value}
                  selected={draft.leafHabit === c.value}
                  onPress={() => setDraft({ ...draft, leafHabit: draft.leafHabit === c.value ? null : c.value })}
                  accessibilityLabel={c.label}
                  accessibilityState={{ selected: draft.leafHabit === c.value }}
                  style={styles.chip}
                >
                  {c.label}
                </Chip>
              ))}
            </View>
          </>
        )}

        {questions.map((q) => (
          <View key={q.field}>
            <Text style={styles.question}>{q.title}</Text>
            <View style={styles.chips}>
              {q.choices.map((c) => {
                const on = draft.corrections[q.field] === c.value;
                return (
                  <Chip
                    key={c.value}
                    selected={on}
                    onPress={() => setDraft({
                      ...draft, corrections: { ...draft.corrections, [q.field]: on ? '' : c.value },
                    })}
                    accessibilityLabel={`${q.title.replace(' (optional)', '')}: ${c.label}`}
                    accessibilityState={{ selected: on }}
                    style={styles.chip}
                  >
                    {c.label}
                  </Chip>
                );
              })}
            </View>
          </View>
        ))}

        {problem ? <Text style={styles.error} accessibilityLiveRegion="polite">{problem}</Text> : null}

        <View style={styles.actions}>
          <Button
            mode="contained"
            onPress={onSave}
            loading={saving}
            disabled={saving}
            accessibilityLabel="Save this zone"
            style={styles.saveBtn}
          >
            Save
          </Button>
          {zone && canRedraw ? (
            <Button mode="outlined" onPress={onRedraw} disabled={saving} accessibilityLabel="Change the box on the image">
              Change the box
            </Button>
          ) : null}
          <Button mode="text" onPress={onCancel} disabled={saving} accessibilityLabel="Cancel without saving">
            Cancel
          </Button>
        </View>
        {zone && onDelete ? (
          blocked ? (
            <Text style={styles.quiet}>{blocked}</Text>
          ) : (
            <Button mode="text" onPress={onDelete} disabled={saving} accessibilityLabel={`Delete ${zone.name}`} style={styles.deleteBtn}>
              Delete this zone
            </Button>
          )
        ) : null}
      </Card.Content>
    </Card>
  );
}

const makeStyles = (p: Palette, f: Fonts) => StyleSheet.create({
  center: { flex: 1, marginTop: 64 },
  container: { flex: 1, backgroundColor: p.bg },
  content: { padding: 16, paddingBottom: 48 },
  headline: { color: p.acc, fontFamily: f.display, fontSize: 22, fontWeight: '700' },
  intro: { color: p.sub, fontSize: 14, lineHeight: 20, marginTop: 4, marginBottom: 12 },
  credit: { color: p.faint, fontSize: 12, marginTop: 6 },
  section: { marginTop: 16 },
  eyebrow: { marginBottom: 6 },
  zoneRow: { alignSelf: 'stretch' },
  zoneRowContent: { justifyContent: 'flex-start' },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 12 },
  card: { backgroundColor: p.card, marginTop: 16 },
  cardTitle: { color: p.ink, fontFamily: f.display, fontSize: 17, fontWeight: '700', marginBottom: 6 },
  input: { marginTop: 8 },
  question: { color: p.ink, fontSize: 15, fontWeight: '600', marginTop: 14, marginBottom: 6 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  chip: { marginBottom: 2 },
  error: { color: p.warn, fontSize: 13.5, marginTop: 12 },
  quiet: { color: p.sub, fontSize: 13.5, lineHeight: 19, marginTop: 8 },
  quietBlock: { color: p.sub, fontSize: 14, lineHeight: 20, marginVertical: 16 },
  inlineSpin: { marginVertical: 24 },
  saveBtn: {},
  deleteBtn: { alignSelf: 'flex-start', marginTop: 8 },
  box: {
    position: 'absolute', borderWidth: 2, borderColor: '#FFFDF6', backgroundColor: 'rgba(255,253,246,0.12)',
    padding: 3,
  },
  boxApprox: { borderStyle: 'dashed', backgroundColor: 'transparent' },
  boxActive: { borderColor: '#F2C14E', backgroundColor: 'rgba(242,193,78,0.18)' },
  boxLabel: {
    color: '#FFFDF6', fontSize: 11.5, fontWeight: '700',
    textShadowColor: 'rgba(0,0,0,0.8)', textShadowRadius: 3, textShadowOffset: { width: 0, height: 1 },
  },
  handle: {
    position: 'absolute', width: HANDLE_SIZE, height: HANDLE_SIZE, borderRadius: HANDLE_SIZE / 2,
    backgroundColor: '#F2C14E', borderWidth: 2, borderColor: '#2F4A33',
  },
});
