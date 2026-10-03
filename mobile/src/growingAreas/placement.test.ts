import {
  FIRST_AREA_NAME, NO_AREA_NOTE, areasFailedNote, defaultAreaId, placementAreaId,
} from './placement';

describe('the default area for a new plant', () => {
  it('is the oldest by id, whatever order the list arrives in', () => {
    // An edited row can come back last; "first in the list" is not the rule.
    expect(defaultAreaId([{ id: 9 }, { id: 3 }, { id: 5 }])).toBe(3);
    expect(defaultAreaId([{ id: 3 }, { id: 9 }])).toBe(3);
  });

  it('is nothing at all when there are no areas — not a made-up one', () => {
    expect(defaultAreaId([])).toBeNull();
  });
});

describe('the area shown selected', () => {
  const areas = [{ id: 3 }, { id: 5 }, { id: 9 }];

  it('is the area Add Plant was opened from, not the oldest', () => {
    expect(placementAreaId(areas, 9)).toBe(9);
  });

  it('falls back to the default when none was asked for', () => {
    expect(placementAreaId(areas, null)).toBe(3);
  });

  it('never keeps an area that is no longer in the list', () => {
    expect(placementAreaId(areas, 42)).toBe(3);
    expect(placementAreaId([], 42)).toBeNull();
  });
});

describe('what the picker says when it has nothing to show', () => {
  it('names the area the server will make, so the plant does not land unseen', () => {
    expect(FIRST_AREA_NAME).toBe('My Home');
    expect(NO_AREA_NOTE).toContain(`“${FIRST_AREA_NAME}”`);
  });

  it('points at setting a space up first — the made area cannot be described later', () => {
    expect(NO_AREA_NOTE).toMatch(/Set up a space under Growing areas first/);
  });

  it('says where the plant goes when the areas could not be loaded', () => {
    expect(areasFailedNote(false)).toMatch(/your oldest one/);
    // Opened from an area: the save still names that area, so the note does.
    expect(areasFailedNote(true)).toMatch(/the one you came from/);
  });
});
