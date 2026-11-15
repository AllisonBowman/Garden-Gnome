import {
  hitHandle, hitZone, isUsableRect, MIN_BOX_PX, moveHandle, moveRect, rectFromCorners, scaleRect,
} from './boxEdit';

const W = 400;
const H = 300;

describe('stretching a box', () => {
  it('makes the same box from corners in either order', () => {
    expect(rectFromCorners({ x: 50, y: 60 }, { x: 10, y: 20 }, W, H)).toEqual({ x: 10, y: 20, w: 40, h: 40 });
  });
  it('keeps the box inside the image', () => {
    expect(rectFromCorners({ x: -20, y: -5 }, { x: 900, y: 700 }, W, H)).toEqual({ x: 0, y: 0, w: W, h: H });
  });
  it('does not treat a tap as a box', () => {
    expect(isUsableRect(rectFromCorners({ x: 10, y: 10 }, { x: 12, y: 13 }, W, H))).toBe(false);
    expect(isUsableRect(null)).toBe(false);
    expect(isUsableRect({ x: 0, y: 0, w: MIN_BOX_PX, h: MIN_BOX_PX })).toBe(true);
  });
});

describe('adjusting with handles', () => {
  const r = { x: 100, y: 100, w: 100, h: 50 };
  it('moves one corner and keeps the opposite one', () => {
    expect(moveHandle(r, 'se', { x: 250, y: 180 }, W, H)).toEqual({ x: 100, y: 100, w: 150, h: 80 });
    expect(moveHandle(r, 'nw', { x: 80, y: 90 }, W, H)).toEqual({ x: 80, y: 90, w: 120, h: 60 });
  });
  it('never flips or shrinks below the minimum', () => {
    const out = moveHandle(r, 'se', { x: 0, y: 0 }, W, H);
    expect(out).toEqual({ x: 100, y: 100, w: MIN_BOX_PX, h: MIN_BOX_PX });
  });
  it('finds the handle under a finger', () => {
    expect(hitHandle(r, { x: 198, y: 152 }, 20)).toBe('se');
    expect(hitHandle(r, { x: 150, y: 125 }, 20)).toBeNull();
  });
  it('moves the whole box but not off the image', () => {
    expect(moveRect(r, 500, -500, W, H)).toEqual({ x: 300, y: 0, w: 100, h: 50 });
  });
  it('grows and shrinks about the centre', () => {
    expect(scaleRect(r, 2, W, H)).toEqual({ x: 50, y: 75, w: 200, h: 100 });
    expect(scaleRect(r, 0.5, W, H)).toEqual({ x: 125, y: 112.5, w: 50, h: 25 });
  });
});

describe('tapping a zone', () => {
  it('picks the smallest box under the tap', () => {
    const zones = [
      { id: 1, rect: { x: 0, y: 0, w: 400, h: 300 } },
      { id: 2, rect: { x: 100, y: 100, w: 50, h: 50 } },
    ];
    expect(hitZone(zones, { x: 120, y: 120 })?.id).toBe(2);
    expect(hitZone(zones, { x: 10, y: 10 })?.id).toBe(1);
    expect(hitZone(zones, { x: 500, y: 10 })).toBeNull();
  });
});
