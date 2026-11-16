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
  'screens/HomeScreen.tsx',
  'screens/SeasonScreen.tsx',
  'components/TopDownImage.tsx',
  'land/PinMarker.tsx',
  'land/CorrectionControl.tsx',
  'components/LandMap.tsx',
  'components/LayerChips.tsx',
  'components/MapLegend.tsx',
  'components/ForecastBars.tsx',
  'components/SeasonTimeline.tsx',
  'components/ReadingTile.tsx',
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

/** The text a person can see or hear in a source file: string literals
 *  (quotes and template text) and JSX text, with comments left out. An
 *  identifier such as metresBetween is code, not copy, and is not returned. */
function visibleText(source: string): string[] {
  const out: string[] = [];
  let code = '';
  for (let i = 0; i < source.length; i++) {
    const c = source[i];
    if (c === '/' && source[i + 1] === '/') {
      while (i < source.length && source[i] !== '\n') i++;
      code += '\n';
    } else if (c === '/' && source[i + 1] === '*') {
      const end = source.indexOf('*/', i + 2);
      i = end < 0 ? source.length : end + 1;
      code += ' ';
    } else if (c === "'" || c === '"' || c === '`') {
      let j = i + 1;
      for (; j < source.length && source[j] !== c; j++) if (source[j] === '\\') j++;
      out.push(source.slice(i + 1, j));
      code += '""';
      i = j;
    } else {
      code += c;
    }
  }
  const jsx = /> *([^<>{}]+?) *</g;
  let m: RegExpExecArray | null;
  while ((m = jsx.exec(code))) out.push(m[1]);
  return out;
}

const METRIC_WORDS = /\b(metres?|meters?|kilomet(er|re)s?|centimet(er|re)s?)\b/i;

test('the metric scan finds copy and passes code', () => {
  const sample = [
    'const d = metresBetween(a, b) >= MOVED_METRES; // a few metres',
    '/* about 500 metres */ const label = `Move the pin a few metres ${d}`;',
    '<Text>an area about 500 meters across</Text>',
  ].join('\n');
  expect(visibleText(sample).filter((t) => METRIC_WORDS.test(t))).toEqual([
    'Move the pin a few metres ${d}', 'an area about 500 meters across']);
});

test('owner-facing copy gives lengths in feet, not metres', () => {
  for (const file of FILES) {
    const found = visibleText(fs.readFileSync(path.join(ROOT, file), 'utf8'))
      .filter((t) => METRIC_WORDS.test(t));
    expect({ file, found }).toEqual({ file, found: [] });
  }
});
