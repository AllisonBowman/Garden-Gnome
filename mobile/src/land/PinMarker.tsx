import React, { useMemo, useRef } from 'react';
import { PanResponder, StyleSheet, Text, View } from 'react-native';
import { Point } from './imageGeometry';
import { TopDownImageContext } from '../components/TopDownImage';
import { t } from '../i18n';

const SIZE = 36;

/**
 * The home pin over a TopDownImage, placed in view pixels with the image's
 * context. It can be dragged: the drag moves it in image pixels, so it
 * follows the finger at any zoom. `onMove` gets the new image point.
 */
export default function PinMarker({
  ctx, at, imageSize, onMove, color, ring, onGestureActive,
}: {
  ctx: TopDownImageContext;
  at: Point;
  imageSize: { width: number; height: number };
  onMove: (p: Point) => void;
  color: string;
  ring: string;
  /** True while the pin is being dragged. */
  onGestureActive?: (active: boolean) => void;
}) {
  const scaleRef = useRef(ctx.scale);
  scaleRef.current = ctx.scale;
  const atRef = useRef(at);
  atRef.current = at;
  const start = useRef<Point>(at);
  const moveRef = useRef(onMove);
  moveRef.current = onMove;
  const activeRef = useRef(onGestureActive);
  activeRef.current = onGestureActive;

  const responder = useMemo(() => PanResponder.create({
    onStartShouldSetPanResponder: () => true,
    onMoveShouldSetPanResponder: () => true,
    onPanResponderTerminationRequest: () => false,
    onPanResponderGrant: () => { start.current = atRef.current; activeRef.current?.(true); },
    onPanResponderRelease: () => { activeRef.current?.(false); },
    onPanResponderTerminate: () => { activeRef.current?.(false); },
    onPanResponderMove: (_e, g) => {
      const s = scaleRef.current || 1;
      const x = Math.min(Math.max(start.current.x + g.dx / s, 0), imageSize.width);
      const y = Math.min(Math.max(start.current.y + g.dy / s, 0), imageSize.height);
      moveRef.current({ x, y });
    },
  }), [imageSize.width, imageSize.height]);

  const v = ctx.toView(at);
  return (
    <View
      {...responder.panHandlers}
      accessible
      accessibilityRole="adjustable"
      accessibilityLabel={t('land.pinA11y')}
      hitSlop={12}
      style={[styles.pin, { left: v.x - SIZE / 2, top: v.y - SIZE, }]}
    >
      <View style={[styles.head, { backgroundColor: color, borderColor: ring }]}>
        <Text style={[styles.glyph, { color: ring }]}>⌂</Text>
      </View>
      <View style={[styles.stem, { backgroundColor: color }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  pin: { position: 'absolute', width: SIZE, height: SIZE, alignItems: 'center' },
  head: {
    width: 26, height: 26, borderRadius: 13, borderWidth: 2,
    alignItems: 'center', justifyContent: 'center',
  },
  glyph: { fontSize: 14, fontWeight: '700', lineHeight: 16 },
  stem: { width: 3, height: 10, borderRadius: 1.5 },
});
