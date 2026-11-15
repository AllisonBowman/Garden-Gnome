import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  GestureResponderEvent, Image, LayoutChangeEvent, PanResponder, PanResponderGestureState,
  Pressable, StyleProp, StyleSheet, Text, View, ViewStyle,
} from 'react-native';
import { Imagery } from '../types/site';
import { Point } from '../land/imageGeometry';
import {
  ViewTransform, clampTransform, fitTransform, focusTransform, isTap, panBy, pinch, toImage, toView, touchPair,
} from '../land/viewTransform';
import { useAppTheme } from '../theme/ThemeProvider';

/** What an overlay gets to place itself: `scale` is view pixels per image
 *  pixel; `toView` and `toImage` convert points between image pixels and
 *  view pixels (relative to this component's top-left corner). */
export interface TopDownImageContext {
  scale: number;
  toView: (p: { x: number; y: number }) => { x: number; y: number };
  toImage: (p: { x: number; y: number }) => { x: number; y: number };
}

export interface TopDownImageProps {
  imagery: Imagery;
  imageUri: string;
  headers?: Record<string, string>;
  /** Overlays (pins, boxes), drawn in view pixels above the image. They are
   *  not scaled with the image, so a pin keeps its size while zooming. */
  children?: (ctx: TopDownImageContext) => React.ReactNode;
  /** One finger pans, two fingers pinch to zoom, with zoom buttons for
   *  anyone who cannot pinch. Off: this component claims no touches except
   *  taps (when onTapPoint is set), so overlays can handle their own. */
  gesturesEnabled?: boolean;
  /** A tap on the image, in image pixels. */
  onTapPoint?: (imagePoint: { x: number; y: number }) => void;
  style?: ViewStyle;
  /** What a screen reader hears for the image itself. */
  accessibilityLabel?: string;
  /** True while a finger is on the image, false when it lifts. A screen
   *  inside a ScrollView can turn scrolling off meanwhile. */
  onGestureActive?: (active: boolean) => void;
  /** Where the view starts: centred on this image point, with about `span`
   *  image pixels across. Without it the whole image is shown. */
  initialFocus?: { x: number; y: number; span: number };
}

type Gesture =
  | { kind: 'none' }
  | { kind: 'pan'; start: ViewTransform; startedAt: number; touches: number }
  | { kind: 'pinch'; start: ViewTransform; focal: Point; distance: number };

/**
 * A top-down aerial image from our server (Imagery), drawn with a plain
 * Image and panned and pinch-zoomed with JavaScript gesture handling (the
 * built-in PanResponder; no native module). Used by property setup (the pin)
 * and the zone map (boxes over beds).
 */
export default function TopDownImage({
  imagery, imageUri, headers, children, gesturesEnabled = true, onTapPoint, style,
  accessibilityLabel, onGestureActive, initialFocus,
}: TopDownImageProps) {
  const { palette } = useAppTheme();
  const image = useMemo(() => ({ width: imagery.width, height: imagery.height }), [imagery.width, imagery.height]);
  const [view, setView] = useState({ width: 0, height: 0 });
  const [t, setT] = useState<ViewTransform>({ scale: 1, tx: 0, ty: 0 });
  const tRef = useRef(t);
  tRef.current = t;
  const viewRef = useRef(view);
  viewRef.current = view;
  const origin = useRef({ x: 0, y: 0 });
  const box = useRef<View>(null);
  const gesture = useRef<Gesture>({ kind: 'none' });
  const tapRef = useRef(onTapPoint);
  tapRef.current = onTapPoint;
  const enabledRef = useRef(gesturesEnabled);
  enabledRef.current = gesturesEnabled;
  const activeRef = useRef(onGestureActive);
  activeRef.current = onGestureActive;
  const focusRef = useRef(initialFocus);
  focusRef.current = initialFocus;
  const startTransform = (v: { width: number; height: number }): ViewTransform => (
    focusRef.current ? focusTransform(v, image, focusRef.current) : fitTransform(v, image)
  );

  const onLayout = useCallback((e: LayoutChangeEvent) => {
    const { width, height } = e.nativeEvent.layout;
    setView({ width, height });
    setT(startTransform({ width, height }));
    box.current?.measureInWindow((x, y) => { origin.current = { x, y }; });
  }, [image]);

  // A different image (a new block): start again from the fit.
  useEffect(() => {
    if (viewRef.current.width > 0) setT(startTransform(viewRef.current));
  }, [image, imagery.tile_key]);

  // Touch positions relative to this component.
  const local = (e: GestureResponderEvent): Point[] => {
    const touches = e.nativeEvent.touches.length > 0 ? e.nativeEvent.touches : [e.nativeEvent];
    return touches.map((p) => ({ x: p.pageX - origin.current.x, y: p.pageY - origin.current.y }));
  };

  const responder = useMemo(() => PanResponder.create({
    onStartShouldSetPanResponder: () => enabledRef.current || tapRef.current != null,
    onMoveShouldSetPanResponder: () => enabledRef.current,
    onPanResponderTerminationRequest: () => false,
    onPanResponderGrant: (e) => {
      activeRef.current?.(true);
      box.current?.measureInWindow((x, y) => { origin.current = { x, y }; });
      gesture.current = {
        kind: 'pan', start: tRef.current, startedAt: Date.now(), touches: e.nativeEvent.touches.length,
      };
    },
    onPanResponderMove: (e, g: PanResponderGestureState) => {
      if (!enabledRef.current) return;
      const pts = local(e);
      const v = viewRef.current;
      if (pts.length >= 2) {
        const pair = touchPair(pts[0], pts[1]);
        if (gesture.current.kind !== 'pinch') {
          gesture.current = { kind: 'pinch', start: tRef.current, focal: pair.focal, distance: pair.distance };
          return;
        }
        const s = gesture.current;
        setT(pinch(s.start, s.focal, s.distance, pair.focal, pair.distance, v, image));
        return;
      }
      if (gesture.current.kind === 'pan') {
        setT(panBy(gesture.current.start, g.dx, g.dy, v, image));
      } else if (gesture.current.kind === 'pinch') {
        // A finger lifted mid-pinch: carry on as a pan from here.
        gesture.current = { kind: 'pan', start: tRef.current, startedAt: 0, touches: 2 };
      }
    },
    onPanResponderRelease: (e, g) => {
      activeRef.current?.(false);
      const s = gesture.current;
      gesture.current = { kind: 'none' };
      if (s.kind !== 'pan' || s.touches > 1 || !s.startedAt) return;
      if (!isTap(g.dx, g.dy, Date.now() - s.startedAt)) return;
      const tap = tapRef.current;
      if (!tap) return;
      const [p] = local(e);
      const q = toImage(tRef.current, p);
      if (q.x < 0 || q.y < 0 || q.x > image.width || q.y > image.height) return;
      tap(q);
    },
    onPanResponderTerminate: () => { activeRef.current?.(false); gesture.current = { kind: 'none' }; },
  }), [image]);

  const zoom = (factor: number) => {
    const v = viewRef.current;
    const centre = { x: v.width / 2, y: v.height / 2 };
    setT((cur) => pinch(cur, centre, 1, centre, factor, v, image));
  };
  const reset = () => setT(fitTransform(viewRef.current, image));

  const ctx: TopDownImageContext = useMemo(() => ({
    scale: t.scale,
    toView: (p) => toView(t, p),
    toImage: (p) => toImage(t, p),
  }), [t]);

  const fitted = fitTransform(view, image).scale;
  const zoomed = view.width > 0 && t.scale > fitted * 1.01;
  const ready = view.width > 0;

  return (
    <View
      ref={box}
      onLayout={onLayout}
      style={[styles.wrap, { aspectRatio: image.width / image.height, backgroundColor: palette.desk }, style]}
      {...(gesturesEnabled || onTapPoint ? responder.panHandlers : {})}
    >
      {ready ? (
        <Image
          source={{ uri: imageUri, headers }}
          style={{
            position: 'absolute', left: t.tx, top: t.ty,
            width: image.width * t.scale, height: image.height * t.scale,
          }}
          resizeMode="stretch"
          accessible
          accessibilityRole="image"
          accessibilityLabel={accessibilityLabel ?? `Top-down aerial image. ${imagery.source.name}.`}
        />
      ) : null}
      {ready && children ? (
        <View style={StyleSheet.absoluteFill} pointerEvents="box-none">{children(ctx)}</View>
      ) : null}
      {gesturesEnabled && ready ? (
        <View style={styles.zoomBar} pointerEvents="box-none">
          <ZoomButton label="+" a11y="Zoom in" onPress={() => zoom(1.6)} palette={palette} />
          <ZoomButton label="−" a11y="Zoom out" onPress={() => zoom(1 / 1.6)} palette={palette} />
          {zoomed ? <ZoomButton label="⤢" a11y="Show the whole image" onPress={reset} palette={palette} /> : null}
        </View>
      ) : null}
    </View>
  );
}

function ZoomButton({ label, a11y, onPress, palette }: {
  label: string; a11y: string; onPress: () => void;
  palette: { card: string; ink: string; line: string };
}) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={a11y}
      hitSlop={6}
      style={[styles.zoomBtn, { backgroundColor: palette.card, borderColor: palette.line }]}
    >
      <Text style={[styles.zoomText, { color: palette.ink }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  wrap: { width: '100%', overflow: 'hidden', borderRadius: 12 },
  zoomBar: { position: 'absolute', right: 8, top: 8, gap: 6 },
  zoomBtn: {
    width: 36, height: 36, borderRadius: 18, borderWidth: 1,
    alignItems: 'center', justifyContent: 'center', opacity: 0.92,
  },
  zoomText: { fontSize: 20, fontWeight: '600', lineHeight: 22 },
});
