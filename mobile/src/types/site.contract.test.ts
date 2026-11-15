// Every literal union in types/site.ts is the build spec's own list (section
// 4). Read from both sources the way support.version.test.ts reads app.json:
// a member added on one side and not the other fails here, before the
// screens that switch on it meet a value they have no words for.
import { CONFIDENCE_LABELS, LOT_CONTENTS } from './site';

declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');

const spec: string = fs.readFileSync(
  path.join(__dirname, '../../../docs/design/2026-11-15-overhaul-build-spec.md'), 'utf8');
const types: string = fs.readFileSync(path.join(__dirname, 'site.ts'), 'utf8');

/** The quoted literals of the union right after `anchor` in the spec,
 *  across lines that end in "|". */
function specLiterals(anchor: string): string[] {
  const at = spec.indexOf(anchor);
  if (at < 0) throw new Error(`spec has no ${anchor}`);
  let text = '';
  for (const line of spec.slice(at + anchor.length).split('\n')) {
    text += line.trim();
    if (!line.trimEnd().endsWith('|')) break;
  }
  const union = /^("[^"]+"(?:\|"[^"]+")*)/.exec(text);
  if (!union) throw new Error(`no union after ${anchor}`);
  return [...union[1].matchAll(/"([^"]+)"/g)].map((m) => m[1]);
}

/** The single-quoted literals of `export type Name = ...;` in site.ts. */
function typeLiterals(name: string): string[] {
  const m = new RegExp(`export type ${name} =([^;]+);`).exec(types);
  if (!m) throw new Error(`site.ts has no type ${name}`);
  return [...m[1].matchAll(/'([^']+)'/g)].map((x) => x[1]);
}

const PAIRS: Array<[string, string]> = [
  ['PinSource', 'pin_source: '],
  ['FrostBias', 'frost_bias?: '],
  ['OverrideMethod', 'field, value, method: '],
  ['SeasonEventState', 'body {state: '],
  ['ProfileStepStatus', 'profile_status values: '],
  ['BoundarySource', 'boundary_source: '],
  ['VegetationType', 'vegetation_type: '],
  ['LeafHabit', 'leaf_habit: '],
  ['Confidence', 'confidence: '],
  ['ConfidenceLabel', 'confidence_label: '],
  ['Provenance', '           provenance: '],
  ['OverrideKind', 'override_kind: '],
  ['SiteField', '           field: '],
  ['FrostRisk', 'frost_risk: '],
  ['AppliesToKind', 'applies_to: {kind: '],
  ['TaskState', 'ids: [int]}, state: '],
  ['SeasonEventType', '            type: '],
  ['SeasonEventStatus', '            status: '],
  ['VitalTone', 'tone: '],
  ['VitalCardKey', '           key: '],
  ['VitalSpaceKind', 'growing_area_id, name, kind: '],
];

test.each(PAIRS)('%s matches the spec', (name, anchor) => {
  expect(typeLiterals(name).sort()).toEqual(specLiterals(anchor).filter((v) => v !== 'null').sort());
});

test('owner actions come from the spec line, quoted without bars', () => {
  // "any of" lists them comma-separated rather than as a union.
  const line = spec.slice(spec.indexOf('owner_actions: any of '), spec.indexOf('\n', spec.indexOf('owner_actions: any of ')));
  const listed = [...line.matchAll(/"([^"]+)"/g)].map((m) => m[1]);
  expect(typeLiterals('OwnerAction').sort()).toEqual(listed.sort());
});

test('lot contents are the spec list', () => {
  const at = spec.indexOf('lot_contents values: ');
  const block = spec.slice(at, spec.indexOf('profile_status values', at));
  const listed = [...block.matchAll(/"([^"]+)"/g)].map((m) => m[1]);
  expect([...LOT_CONTENTS].sort()).toEqual(listed.sort());
  expect(typeLiterals('LotContent').sort()).toEqual(listed.sort());
});

test('every confidence has the label the spec pairs it with, in order', () => {
  expect(Object.keys(CONFIDENCE_LABELS)).toEqual(specLiterals('confidence: '));
  expect(Object.values(CONFIDENCE_LABELS)).toEqual(specLiterals('confidence_label: '));
});
