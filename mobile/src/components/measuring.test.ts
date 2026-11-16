// A view whose only job is to measure itself (style plus onLayout) is
// "layout only". In a release build React Native may flatten such a view
// away, and its onLayout then never fires: the forecast bars and the season
// timeline drew in development and were blank in the release build
// (found on the iOS Simulator, 2026-11-16). `collapsable={false}` keeps the
// view. This scans for a one-line <View ... onLayout=...> without it.
declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');

function tsxFiles(dir: string): string[] {
  const out: string[] = [];
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) out.push(...tsxFiles(full));
    else if (name.endsWith('.tsx')) out.push(full);
  }
  return out;
}

test('every one-line measuring view is kept in release builds', () => {
  const src = path.join(__dirname, '..');
  const missing: string[] = [];
  let seen = 0;
  for (const file of tsxFiles(src)) {
    const lines: string[] = fs.readFileSync(file, 'utf8').split('\n');
    lines.forEach((line, i) => {
      if (!/<View\b[^>]*\bonLayout=/.test(line)) return;
      seen += 1;
      if (!line.includes('collapsable={false}')) missing.push(`${path.relative(src, file)}:${i + 1}`);
    });
  }
  expect(seen).toBeGreaterThan(0);
  expect(missing).toEqual([]);
});

test('the charts that draw to fit use the shared measuring hook', () => {
  // onLayout alone never fired for these in the compiled iOS release build.
  for (const name of ['ForecastBars.tsx', 'SeasonTimeline.tsx', 'ReadingTile.tsx']) {
    const text: string = fs.readFileSync(path.join(__dirname, name), 'utf8');
    expect([name, text.includes('useMeasuredWidth()')]).toEqual([name, true]);
    expect([name, text.includes('{...measureProps}')]).toEqual([name, true]);
  }
});
