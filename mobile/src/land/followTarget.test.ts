import { TARGET_MARGIN, followTarget } from './followTarget';

function setup() {
  const scrolled: number[] = [];
  const queue: (() => void)[] = [];
  const f = followTarget((y) => scrolled.push(y), (run) => queue.push(run));
  const flush = () => { while (queue.length) queue.shift()!(); };
  return { f, scrolled, flush };
}

describe('followTarget', () => {
  test('scrolls again when the target moves down after the first scroll', () => {
    // The map placeholder (120 pt) grows to the full image (about 280 pt).
    const { f, scrolled, flush } = setup();
    f.place(400);
    flush();
    f.place(560);
    flush();
    expect(scrolled).toEqual([400 - TARGET_MARGIN, 560 - TARGET_MARGIN]);
  });

  test('only the latest place is scrolled to when several arrive at once', () => {
    const { f, scrolled, flush } = setup();
    f.place(300);
    f.place(470);
    flush();
    expect(scrolled).toEqual([470 - TARGET_MARGIN]);
  });

  test('the same place twice scrolls once, and unknown places are ignored', () => {
    const { f, scrolled, flush } = setup();
    f.place(undefined);
    f.place(null);
    f.place(Number.NaN);
    f.place(200);
    flush();
    f.place(200.4);
    flush();
    expect(scrolled).toEqual([200 - TARGET_MARGIN]);
  });

  test('stops once the owner touches the scroll view', () => {
    const { f, scrolled, flush } = setup();
    f.place(300);
    flush();
    f.release();
    f.place(500);
    flush();
    expect(scrolled).toEqual([300 - TARGET_MARGIN]);
    expect(f.released).toBe(true);
  });

  test('a release before a scheduled scroll runs cancels it, and the top is not passed', () => {
    const { f, scrolled, flush } = setup();
    f.place(5);
    flush();
    expect(scrolled).toEqual([0]);
    f.place(300);
    f.release();
    flush();
    expect(scrolled).toEqual([0]);
  });
});
