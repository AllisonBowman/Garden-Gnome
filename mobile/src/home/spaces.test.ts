import { orderSpaces, spaceLine, spacesFromAreas } from './spaces';
import { GrowingArea } from '../types';
import { VitalSpace } from '../types/site';

const area = (id: number, temp: 'indoor' | 'outdoor', plants: number): GrowingArea => ({
  id, uuid: `u${id}`, name: `Area ${id}`, type: 'home', city: '', region: '', country: '',
  shelter: 'sheltered', temp_exposure: temp, sun_exposure: 'partial_sun',
  created_at: '', plant_count: plants,
});

test('growing areas become spaces, indoor where they say so', () => {
  expect(spacesFromAreas([area(1, 'indoor', 2), area(2, 'outdoor', 0)])).toEqual([
    { growing_area_id: 1, name: 'Area 1', kind: 'space', vegetation_type: null, indoor: true, plant_count: 2 },
    { growing_area_id: 2, name: 'Area 2', kind: 'space', vegetation_type: null, indoor: false, plant_count: 0 },
  ]);
});

test('zones first, then outdoor spaces, then indoor ones, keeping order within each', () => {
  const s = (id: number, kind: 'zone' | 'space', indoor: boolean): VitalSpace =>
    ({ growing_area_id: id, name: String(id), kind, indoor, plant_count: 0 });
  expect(orderSpaces([s(1, 'space', true), s(2, 'zone', false), s(3, 'space', false), s(4, 'zone', false)])
    .map((x) => x.growing_area_id)).toEqual([2, 4, 3, 1]);
});

test('space lines', () => {
  const s = (plant_count: number, kind: 'zone' | 'space', indoor: boolean): VitalSpace =>
    ({ growing_area_id: 1, name: 'x', kind, indoor, plant_count });
  expect(spaceLine(s(0, 'space', true))).toBe('No plants yet, indoors');
  expect(spaceLine(s(1, 'space', false))).toBe('1 plant, outdoors');
  expect(spaceLine(s(5, 'zone', false))).toBe('5 plants, part of your land');
});
