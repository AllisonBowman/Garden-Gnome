// The width a view was laid out at, for charts that draw to fit.
//
// onLayout alone is not enough. In the compiled release build on iOS the
// forecast bars and the season timeline never received a layout event: their
// width stayed 0 and they drew nothing, although the same code drew in the
// development build and in the web preview (found on the iOS Simulator,
// 2026-11-16). So this hook also asks the view for its size once it has
// mounted, and takes whichever answer arrives. Give the returned props to
// the view to measure; `collapsable={false}` keeps React Native from
// flattening a view that has no drawing of its own.
import { useCallback, useEffect, useRef, useState } from 'react';
import type { LayoutChangeEvent, View } from 'react-native';

export interface MeasuredWidth {
  width: number;
  /** Spread onto the view to measure. */
  measureProps: {
    ref: React.RefObject<View | null>;
    onLayout: (e: LayoutChangeEvent) => void;
    collapsable: false;
  };
}

/** How long after mounting to ask again, for a view not laid out yet. */
export const ASK_AGAIN_MS = [0, 120, 500, 1500];

export function useMeasuredWidth(): MeasuredWidth {
  const ref = useRef<View>(null);
  const [width, setWidth] = useState(0);

  const take = useCallback((w: number) => {
    if (!(w > 0)) return;
    setWidth((prev) => (Math.abs(prev - w) < 0.5 ? prev : w));
  }, []);

  const onLayout = useCallback((e: LayoutChangeEvent) => take(e.nativeEvent.layout.width), [take]);

  useEffect(() => {
    let live = true;
    const ask = () => {
      const node = ref.current;
      if (!live || !node || typeof node.measure !== 'function') return;
      node.measure((_x, _y, w) => { if (live) take(w); });
    };
    const timers = ASK_AGAIN_MS.map((ms) => setTimeout(ask, ms));
    return () => {
      live = false;
      timers.forEach(clearTimeout);
    };
  }, [take]);

  return { width, measureProps: { ref, onLayout, collapsable: false } };
}
