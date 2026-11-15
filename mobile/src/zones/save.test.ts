import { AnswersNotSaved, ZoneSaveApi, saveZone } from './save';
import { emptyDraft } from './describe';
import { SiteProfile, Zone } from '../types/site';

const BOX = { west: -76.968, south: 38.912, east: -76.9679, north: 38.9121 };
const ZONE: Zone = {
  id: 9, growing_area_id: 9, property_id: 1, name: 'Garden bed', vegetation_type: 'garden_bed',
  is_whole_lot: false, box: BOX, boundary_source: 'owner', leaf_habit: null, plant_count: 0, values: [],
};
const PROFILE = { values: [] } as unknown as SiteProfile;

function fakeApi(failOverrides = 0) {
  let fails = failOverrides;
  const calls: string[] = [];
  const api: ZoneSaveApi = {
    createZone: jest.fn(async (body) => { calls.push(`create drawn=${body.drawn}`); return ZONE; }),
    updateZone: jest.fn(async (id) => { calls.push(`update ${id}`); return ZONE; }),
    putOverride: jest.fn(async (body) => {
      calls.push(`override ${body.field}`);
      if (fails > 0) { fails -= 1; throw new Error('offline'); }
      return PROFILE;
    }),
  };
  return { api, calls };
}

const draft = { ...emptyDraft(), vegetation: 'garden_bed' as const, corrections: { sun: 'shade' } };

describe('saveZone', () => {
  it('marks a zone added without drawing as not drawn', async () => {
    const { api, calls } = fakeApi();
    await saveZone(api, { existing: null, draft, box: BOX, boxEdited: false, noDraw: true, existingNames: [] });
    expect(calls[0]).toBe('create drawn=false');
  });

  it('marks a drawn box as drawn, also after "without drawing" when the owner then drew', async () => {
    const { api, calls } = fakeApi();
    await saveZone(api, { existing: null, draft, box: BOX, boxEdited: true, noDraw: true, existingNames: [] });
    await saveZone(api, { existing: null, draft, box: BOX, boxEdited: true, noDraw: false, existingNames: [] });
    expect(calls.filter((c) => c.startsWith('create'))).toEqual(['create drawn=true', 'create drawn=true']);
  });

  it('a failed answer after the zone was created does not create a second zone on retry', async () => {
    const { api, calls } = fakeApi(1);
    let editing: Zone | null = null;
    const input = { existing: null, draft, box: BOX, boxEdited: true, noDraw: false, existingNames: [] };
    await expect(saveZone(api, input, (z) => { editing = z; })).rejects.toBeInstanceOf(AnswersNotSaved);
    expect(editing).toEqual(ZONE);
    // The screen now edits the created zone; Save again only resends the answer.
    const out = await saveZone(api, { ...input, existing: editing, boxEdited: false });
    expect(out.zone.id).toBe(9);
    expect(api.createZone).toHaveBeenCalledTimes(1);
    expect(calls).toEqual(['create drawn=true', 'override sun', 'override sun']);
  });

  it('a failed create is a plain failure', async () => {
    const { api } = fakeApi();
    (api.createZone as jest.Mock).mockRejectedValueOnce(new Error('offline'));
    const input = { existing: null, draft, box: BOX, boxEdited: true, noDraw: false, existingNames: [] };
    await expect(saveZone(api, input)).rejects.not.toBeInstanceOf(AnswersNotSaved);
  });
});
