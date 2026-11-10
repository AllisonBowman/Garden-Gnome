import { adviceSourceLabel, diagnosisSourceLabel } from './resultLabels';

// Whatever the server reports as its backend, the pill says what kind of
// source it was — never the backend's own name. These are names the server
// sends today or could send tomorrow.
const BACKENDS = ['anthropic', 'claude-haiku', 'gemini', 'local-vision', 'openai'];

test('advice from the rule engine is labelled rule-based', () => {
  expect(adviceSourceLabel('stub', false)).toBe('rule-based');
  expect(adviceSourceLabel('stub', true)).toBe('rule-based • gnome voice');
});

test('advice from anything else is the care engine, never the backend by name', () => {
  for (const backend of BACKENDS) {
    const label = adviceSourceLabel(backend, false);
    expect(label).toBe('care engine');
    expect(label.toLowerCase()).not.toContain(backend);
  }
  expect(adviceSourceLabel('anthropic', true)).toBe('care engine • gnome voice');
});

test('a photo check-up reading is labelled as one, never by backend', () => {
  expect(diagnosisSourceLabel('stub')).toBe('not switched on yet');
  for (const backend of BACKENDS) {
    expect(diagnosisSourceLabel(backend)).toBe('photo check-up');
  }
});

test('a missing backend reads as the rule engine, not as a blank pill', () => {
  expect(adviceSourceLabel(undefined, false)).toBe('rule-based');
  expect(diagnosisSourceLabel('')).toBe('not switched on yet');
});

// The plant screen must route both pills through these, not print the field.
declare const require: (id: string) => any;
declare const __dirname: string;

test('the plant screen never prints a backend field raw', () => {
  const src: string = require('fs').readFileSync(
    require('path').join(__dirname, '../screens/PlantDetailScreen.tsx'), 'utf8');
  expect(src).toMatch(/adviceSourceLabel\(advice\.backend/);
  expect(src).toMatch(/diagnosisSourceLabel\(diagnosis\.backend\)/);
  expect(src).not.toMatch(/:\s*(advice|diagnosis)\.backend\b/);
});
