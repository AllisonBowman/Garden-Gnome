import { AREAS_FAILED_NOTE, FIRST_AREA_NAME, NO_AREA_NOTE, defaultAreaId } from './placement';

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

describe('what the picker says when it has nothing to show', () => {
  it('names the area the server will make, so the plant does not land unseen', () => {
    expect(FIRST_AREA_NAME).toBe('My Home');
    expect(NO_AREA_NOTE).toContain(`“${FIRST_AREA_NAME}”`);
  });

  it('points at setting a space up first — the made area cannot be described later', () => {
    expect(NO_AREA_NOTE).toMatch(/Set up a space under Growing areas first/);
  });

  it('says where the plant goes when the areas could not be loaded', () => {
    expect(AREAS_FAILED_NOTE).toMatch(/oldest one/);
  });
});
