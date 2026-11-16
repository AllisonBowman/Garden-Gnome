// LandMap: the aerial image of a property with its zones outlined and
// labelled, the pin, and optionally one map layer (sun, trees, water) drawn
// exactly over the photograph (map and visuals spec section 4.3).
//
// Usage (Home, read-only, focused on the yard, tap opens Your land):
//
//   const imageryQ = useQuery({ queryKey: SITE_QUERY_KEYS.imagery(id), queryFn: () => fetchPropertyImagery(id) });
//   const zonesQ = useQuery({ queryKey: SITE_QUERY_KEYS.zones(id), queryFn: () => fetchZones(id) });
//   const layersQ = useQuery({ queryKey: SITE_QUERY_KEYS.mapLayers(id), queryFn: () => fetchMapLayersOrOff(id) });
//   const [chip, setChip] = useState<MapChipKey>('aerial');
//   const chips = mapChips(layersQ.data);
//   const chosen = chosenChip(chips, chip);
//   {imageryQ.data ? (
//     <LandMap imagery={imageryQ.data} zones={zonesQ.data ?? []} layer={chosen.layer}
//       onPress={() => navigation.navigate('Land')} pressHint="Opens your land" />
//   ) : imageryQ.isError ? <Text>The map could not be loaded.</Text> : null}
//   <LayerChips chips={chips} chosen={chosen.key} onChoose={setChip} />
//   <MapLegend layer={chosen.layer} />
//
// Your land: the same with `interactive` (pan, pinch and zoom buttons) and
// `onGestureActive` to pause the ScrollView while a finger is on the map.
//
// It loads both pictures itself through the signed-in client. If the aerial
// image cannot be loaded it shows one line instead of the map; if the layer
// cannot be loaded the map shows without it and one line says so.
// Colours: outlines and labels from the theme (mapInk), the layer's own
// colours from the server's picture. The outlines, labels and pin are
// decorative; the image carries one sentence (mapA11yLabel) for all of it.

import React, { useMemo, useState } from 'react';
import { LayoutChangeEvent, Pressable, StyleSheet, Text, View, ViewStyle } from 'react-native';
import Svg, { Circle, Rect as SvgRect } from 'react-native-svg';
import { Imagery, MapLayer, Zone } from '../types/site';
import TopDownImage, { TopDownImageContext } from './TopDownImage';
import { useSignedImage } from '../land/useSignedImage';
import { mapInk, pinPoint, placeLabels, viewRect, yardFocus, zoneRects } from '../land/mapLayout';
import { layerPicturePath, layerReady, mapA11yLabel, pictureLoadKey } from '../land/mapLayers';
import { mapZoneLabel, zoneLabel } from '../zones/describe';
import MapLabels from './MapLabels';
import { useAppTheme } from '../theme/ThemeProvider';

export interface LandMapProps {
  imagery: Imagery;
  /** The property's zones; those with a box are outlined. */
  zones?: Zone[];
  /** The layer to draw over the photograph, or null for the photograph alone.
   *  Drawn only when it is ready (mapLayers.layerReady). */
  layer?: MapLayer | null;
  /** Pan, pinch and zoom buttons (Your land). Off (Home): fixed on the yard. */
  interactive?: boolean;
  /** Read-only only: a tap on the map, such as opening Your land. */
  onPress?: () => void;
  /** What a screen reader hears after the map's sentence when it can be tapped. */
  pressHint?: string;
  /** True while a finger is on an interactive map. */
  onGestureActive?: (active: boolean) => void;
  /** Start on the yard (default) or show the whole image. */
  focusYard?: boolean;
  /** The imagery and layers queries' dataUpdatedAt: a new answer loads the
   *  pictures again, so one that failed once can come back on a refresh. */
  imageryVersion?: number;
  layersVersion?: number;
  style?: ViewStyle;
}

export default function LandMap({
  imagery, zones = [], layer = null, interactive = false, onPress, pressHint, onGestureActive,
  focusYard = true, style, imageryVersion, layersVersion,
}: LandMapProps) {
  const { palette } = useAppTheme();
  const { uri, headers, failed: fetchFailed } = useSignedImage(imagery.image_path, imageryVersion);
  const aerialKey = uri ? pictureLoadKey(uri, imageryVersion) : null;
  const [aerialBroken, setAerialBroken] = useState<string | null>(null);
  const failed = fetchFailed || (aerialKey != null && aerialBroken === aerialKey);
  const shownLayer = layerReady(layer) ? layer : null;
  // Keyed on the block (the tile key) and the layers answer: see layerPicturePath.
  const overlayPath = layerPicturePath(shownLayer, imagery);
  const overlayKey = pictureLoadKey(overlayPath, layersVersion);
  const overlay = useSignedImage(overlayPath, layersVersion);
  const [overlayBroken, setOverlayBroken] = useState<string | null>(null);
  const rects = useMemo(() => zoneRects(imagery, zones), [imagery, zones]);
  const ink = mapInk(palette);

  const label = mapA11yLabel({
    sourceName: imagery.source?.name,
    zoneNames: rects.map((r) => zoneLabel(r.zone)),
    hasPin: !!imagery.pin,
    layer: shownLayer && !overlay.failed && overlayBroken !== overlayKey ? shownLayer : null,
  });

  if (!uri || failed) {
    return (
      <View style={[styles.placeholder, { backgroundColor: palette.desk }, style]}>
        <Text style={{ color: palette.sub, fontSize: 13.5 }} accessibilityLiveRegion="polite">
          {failed ? 'The map could not be loaded.' : 'Loading the map.'}
        </Text>
      </View>
    );
  }

  const layerFailed = !!shownLayer && (overlay.failed || overlayBroken === overlayKey);
  const map = (
    <TopDownImage
      imagery={imagery}
      imageUri={uri}
      headers={headers}
      gesturesEnabled={interactive}
      onGestureActive={onGestureActive}
      initialFocus={focusYard ? yardFocus(imagery) : undefined}
      accessibilityLabel={label}
      overlayUri={layerFailed ? null : overlay.uri}
      overlayHeaders={overlay.headers}
      onOverlayError={() => setOverlayBroken(overlayKey)}
      onImageError={() => setAerialBroken(aerialKey)}
      style={style}
    >
      {(ctx) => <MapMarks ctx={ctx} imagery={imagery} rects={rects} ink={ink} pinColor={palette.warn} />}
    </TopDownImage>
  );

  return (
    <View>
      {onPress && !interactive ? (
        <Pressable
          onPress={onPress}
          accessibilityRole="button"
          accessibilityLabel={pressHint ? `${label} ${pressHint}.` : label}
        >
          {map}
        </Pressable>
      ) : map}
      {layerFailed ? (
        <Text style={[styles.note, { color: palette.sub }]}>
          {`The ${shownLayer!.title.toLowerCase()} layer could not be loaded, so the photograph shows alone.`}
        </Text>
      ) : null}
    </View>
  );
}

/** Outlines, labels and the pin, in view pixels over the image. Decorative. */
function MapMarks({ ctx, imagery, rects, ink, pinColor }: {
  ctx: TopDownImageContext;
  imagery: Imagery;
  rects: ReturnType<typeof zoneRects>;
  ink: { line: string; halo: string };
  pinColor: string;
}) {
  const [size, setSize] = useState({ width: 0, height: 0 });
  const onLayout = (e: LayoutChangeEvent) => {
    const { width, height } = e.nativeEvent.layout;
    setSize({ width, height });
  };
  // Drawn zones first so their labels win over the approximate yard's.
  const ordered = [...rects].sort((a, b) => Number(a.zone.is_whole_lot) - Number(b.zone.is_whole_lot));
  const boxes = ordered.map((r) => ({ r, box: viewRect(r.rect, ctx) }));
  const pin = size.width > 0 ? pinPoint(imagery, ctx, size) : null;
  // Wrapped only at spaces, inside the box or just outside it, off the pin.
  const labels = size.width > 0
    ? placeLabels(boxes.map(({ r, box }) => ({ id: r.id, text: mapZoneLabel(r.zone), box })), size, { pin })
    : [];

  return (
    <View
      style={StyleSheet.absoluteFill}
      pointerEvents="none"
      onLayout={onLayout}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {size.width > 0 ? (
        <Svg width={size.width} height={size.height} style={StyleSheet.absoluteFill}>
          {boxes.map(({ r, box }) => {
            const approximate = r.zone.is_whole_lot && r.zone.boundary_source === 'default';
            return (
              <React.Fragment key={r.id}>
                <SvgRect x={box.left} y={box.top} width={Math.max(0, box.width)} height={Math.max(0, box.height)}
                  fill="none" stroke={ink.halo} strokeOpacity={0.55} strokeWidth={4} />
                <SvgRect x={box.left} y={box.top} width={Math.max(0, box.width)} height={Math.max(0, box.height)}
                  fill="none" stroke={ink.line} strokeWidth={2}
                  strokeDasharray={approximate ? '6 4' : undefined} />
              </React.Fragment>
            );
          })}
          {pin ? (
            <>
              <Circle cx={pin.x} cy={pin.y} r={8} fill={ink.line} />
              <Circle cx={pin.x} cy={pin.y} r={5.5} fill={pinColor} />
            </>
          ) : null}
        </Svg>
      ) : null}
      <MapLabels labels={labels} width={size.width} ink={ink} />
    </View>
  );
}

const styles = StyleSheet.create({
  placeholder: {
    width: '100%', minHeight: 120, borderRadius: 12, alignItems: 'center', justifyContent: 'center', padding: 12,
  },
  note: { fontSize: 12.5, lineHeight: 18, marginTop: 6 },
});
