// Opening a screen at one place (Land at a value or a zone, Season at an
// event) while what sits above it is still growing: the map, chips and
// legend, the forecast bars and the season timeline take their full height
// only after their data or their width arrives, which pushes the target
// down after the first scroll. This keeps scrolling to the target each time
// its place changes, until the owner touches the scroll view. Pure: no
// React Native imports.
//
//   const [follow] = useState(() => followTarget((y) => scroll.current?.scrollTo({ y, animated: true })));
//   <ScrollView onScrollBeginDrag={follow.release}> ... onLayout={() => follow.place(targetY)}

export interface TargetFollower {
  /** The target's y in the scroll content, each time it is known or moves.
   *  Null or undefined (not laid out yet) is ignored. */
  place(y: number | null | undefined): void;
  /** Stop following: the owner scrolled, or chose another place. */
  release(): void;
  readonly released: boolean;
}

/** Space left above the target when it is scrolled to. */
export const TARGET_MARGIN = 12;

export function followTarget(
  scrollTo: (y: number) => void,
  schedule: (run: () => void) => void = (run) => { setTimeout(run, 50); },
): TargetFollower {
  let lastY: number | null = null;
  let released = false;
  return {
    place(y) {
      if (released || y == null || !Number.isFinite(y)) return;
      if (lastY != null && Math.abs(y - lastY) < 1) return;
      lastY = y;
      // Only the latest place is scrolled to, and not after a release.
      schedule(() => { if (!released && lastY === y) scrollTo(Math.max(0, y - TARGET_MARGIN)); });
    },
    release() { released = true; },
    get released() { return released; },
  };
}
