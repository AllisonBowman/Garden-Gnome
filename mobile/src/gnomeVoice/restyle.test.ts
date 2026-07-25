// The guard is pure logic, but it lives beside gnomeVoice() in restyle.ts,
// which pulls in the native plant-id module. Stub it so these tests exercise
// the guard without a native runtime.
jest.mock('../../modules/plant-id', () => ({
  isAvailable: jest.fn().mockResolvedValue(false),
  generate: jest.fn(),
}));

import { driftReasons, driftsFromFact, gnomeVoice, normalizeNumberWords } from './restyle';
import { SIGN_OFF } from './persona';
import { isAvailable, generate } from '../../modules/plant-id';

const mockAvailable = isAvailable as jest.MockedFunction<typeof isAvailable>;
const mockGenerate = generate as jest.MockedFunction<typeof generate>;

// The flat, rule-based advice the engine produced for the Front Yard
// Sunflower — the authoritative facts the restyle was given.
const SUNFLOWER_FACT = [
  '💧 Watering: done 2 days ago. Next window opens in 3 days — hold off.',
  '🌿 Fertilizing: no log yet — recommended every 35–45 days.',
].join('\n');

// Transcribed verbatim from docs/screenshots/2026-07-20-gnome-voice-letter.png.
// This shipped to a user with a "rule-based • gnome voice" badge, meaning the
// v1 guard passed it. It must never render again.
const SCREENSHOT_LETTER = [
  'Dear Plant Owner,',
  '',
  "I've watered your lovely Front Yard Sunflower two days ago, and I'll hold",
  'off on watering it again until the next window opens in three days. I\'ve',
  "also noted that you haven't fertilized your plant yet, which is recommended",
  "every thirty-five days. I'll send you a reminder when it's time to fertilize",
  'your plant. Until then, take care of your plant.',
  '',
  'Love,',
  '',
  '[Your Name]',
].join('\n');

describe('normalizeNumberWords', () => {
  it('resolves hyphenated and spaced compounds', () => {
    expect(normalizeNumberWords('thirty-five days')).toBe('35 days');
    expect(normalizeNumberWords('thirty five days')).toBe('35 days');
  });

  it('resolves standalone cardinals', () => {
    expect(normalizeNumberWords('two days')).toBe('2 days');
    expect(normalizeNumberWords('nineteen')).toBe('19');
  });

  it('matches longest-first so teens survive', () => {
    expect(normalizeNumberWords('seventeen')).toBe('17');
    expect(normalizeNumberWords('sixteen')).toBe('16');
  });

  it('leaves number words embedded in other words alone', () => {
    expect(normalizeNumberWords('none of the tenants')).toBe('none of the tenants');
  });
});

describe('the screenshot letter', () => {
  const reasons = driftReasons(SUNFLOWER_FACT, SCREENSHOT_LETTER);

  it('is rejected', () => {
    expect(driftsFromFact(SUNFLOWER_FACT, SCREENSHOT_LETTER)).toBe(true);
  });

  it('is caught by at least three independent checks', () => {
    expect(new Set(reasons).size).toBeGreaterThanOrEqual(3);
  });

  it('flags the [Your Name] / Dear Plant Owner template artifacts', () => {
    expect(reasons).toContain('placeholder');
  });

  it("flags the gnome claiming it watered the plant", () => {
    expect(reasons).toContain('first-person-care');
  });

  it('flags the promise to send a reminder', () => {
    expect(reasons).toContain('commitment');
  });

  it('flags the letter greeting and closing', () => {
    expect(reasons).toContain('letter-scaffolding');
  });
});

describe('individual v2 checks', () => {
  it('catches a spelled-out number that is not in the fact', () => {
    // "forty" is nowhere in the fact; v1 saw no digits and let this through.
    expect(driftReasons(SUNFLOWER_FACT, 'Fertilize it every forty days.'))
      .toContain('invented-number');
  });

  it('accepts a spelled-out number that IS in the fact', () => {
    expect(driftReasons(SUNFLOWER_FACT, 'It was watered two days ago.'))
      .not.toContain('invented-number');
  });

  it('lets the caretaker be the one who acted', () => {
    expect(driftReasons(SUNFLOWER_FACT, 'You watered it 2 days ago.'))
      .not.toContain('first-person-care');
  });

  it('rejects a bare reminder claim even without a first-person verb', () => {
    expect(driftReasons(SUNFLOWER_FACT, 'A reminder is set for fertilizing.'))
      .toContain('commitment');
  });

  it('rejects curly-brace templates too', () => {
    expect(driftReasons(SUNFLOWER_FACT, 'Hello {{owner}}, water it in 3 days.'))
      .toContain('placeholder');
  });

  it('still rejects empty and rambling output', () => {
    expect(driftReasons(SUNFLOWER_FACT, '   ')).toEqual(['empty']);
    expect(driftReasons(SUNFLOWER_FACT, 'x'.repeat(5000))).toContain('too-long');
  });
});

describe('a well-behaved restyle', () => {
  // Same facts, obeying the persona contract: second person, plant in third
  // person, digits kept, no promises, no scaffolding.
  const GOOD = [
    'Your Front Yard Sunflower had a good drink 2 days ago, so it is content',
    'for now — the next watering window opens in 3 days. Fertilizing has not',
    'been logged yet; every 35 to 45 days keeps it well fed.',
  ].join(' ');

  it('passes every check', () => {
    expect(driftReasons(SUNFLOWER_FACT, GOOD)).toEqual([]);
  });

  it('still styles', () => {
    expect(driftsFromFact(SUNFLOWER_FACT, GOOD)).toBe(false);
  });
});

// Phase 4 golden path: what the user actually ends up reading, and whether the
// "gnome voice" badge that accompanies it is telling the truth.
describe('gnomeVoice end to end', () => {
  const GOOD =
    'Your Front Yard Sunflower had a drink 2 days ago; the next watering '
    + 'window opens in 3 days. Fertilizing runs every 35 to 45 days.';

  beforeEach(() => {
    jest.clearAllMocks();
    mockAvailable.mockResolvedValue(true);
  });

  it('accepted restyle carries the code-appended sign-off and claims the badge', async () => {
    mockGenerate.mockResolvedValue(GOOD);
    const result = await gnomeVoice(SUNFLOWER_FACT, 'Front Yard Sunflower');

    expect(result.styled).toBe(true);
    expect(result.text.endsWith(SIGN_OFF)).toBe(true);
  });

  it('the model never writes the signature — code appends exactly one', async () => {
    mockGenerate.mockResolvedValue(GOOD);
    const { text } = await gnomeVoice(SUNFLOWER_FACT);

    expect(text.split(SIGN_OFF)).toHaveLength(2);
  });

  it('guard-rejected output renders flat text, unsigned, with no badge', async () => {
    mockGenerate.mockResolvedValue(SCREENSHOT_LETTER);
    const result = await gnomeVoice(SUNFLOWER_FACT, 'Front Yard Sunflower');

    expect(result.styled).toBe(false);
    expect(result.text).toBe(SUNFLOWER_FACT);
    expect(result.text).not.toContain(SIGN_OFF);
  });

  it('falls back flat when the device cannot run the model', async () => {
    mockAvailable.mockResolvedValue(false);
    const result = await gnomeVoice(SUNFLOWER_FACT);

    expect(result).toEqual({ text: SUNFLOWER_FACT, styled: false });
    expect(mockGenerate).not.toHaveBeenCalled();
  });

  it('falls back flat when the model throws', async () => {
    mockGenerate.mockRejectedValue(new Error('inference failed'));
    const result = await gnomeVoice(SUNFLOWER_FACT);

    expect(result.styled).toBe(false);
    expect(result.text).toBe(SUNFLOWER_FACT);
  });
});
