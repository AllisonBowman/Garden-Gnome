declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');

// Every control on the property setup and Land screens, and in the pieces
// they share, carries an accessibility label (build spec section 6). A
// source scan: each opening tag of a touchable or input must name one.

const ROOT = path.join(__dirname, '..');
const FILES = [
  'screens/PropertySetupScreen.tsx',
  'screens/LandScreen.tsx',
  'components/TopDownImage.tsx',
  'land/PinMarker.tsx',
  'land/CorrectionControl.tsx',
];
const CONTROLS = ['Button', 'Chip', 'Pressable', 'TextInput', 'TouchableRipple', 'ZoomButton'];

/** The text of each opening tag of a control, braces respected. */
function openingTags(source: string): Array<{ tag: string; text: string }> {
  const out: Array<{ tag: string; text: string }> = [];
  const re = new RegExp(`<(${CONTROLS.join('|')})\\b`, 'g');
  let m: RegExpExecArray | null;
  while ((m = re.exec(source))) {
    let depth = 0;
    let i = m.index + 1;
    for (; i < source.length; i++) {
      const c = source[i];
      if (c === '{') depth++;
      else if (c === '}') depth--;
      else if (c === '>' && depth === 0 && source[i - 1] !== '=') break;
    }
    out.push({ tag: m[1], text: source.slice(m.index, i + 1) });
  }
  return out;
}

test.each(FILES)('every control in %s has an accessibility label', (file) => {
  const source = fs.readFileSync(path.join(ROOT, file), 'utf8');
  const tags = openingTags(source);
  const missing = tags
    .filter((t) => !/accessibilityLabel=|\ba11y=/.test(t.text))
    .map((t) => t.text.split('\n')[0]);
  expect(missing).toEqual([]);
});

test('owner-facing copy has no em dashes', () => {
  for (const file of FILES) {
    expect(fs.readFileSync(path.join(ROOT, file), 'utf8')).not.toContain('—');
  }
});
