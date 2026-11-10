// The guard is pure logic, but it lives beside gnomeVoice() in restyle.ts,
// which pulls in the native plant-id module. Stub it so these tests exercise
// the guard without a native runtime.
jest.mock('../../modules/plant-id', () => ({
  isAvailable: jest.fn().mockResolvedValue(false),
  generate: jest.fn(),
}));

import {
  driftReasons, driftsFromFact, gnomeVoice, normalizeNumberWords, splitSafetyLines,
} from './restyle';
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

// The audit's failing examples, each of which the v2 guard passed: every
// stem the old checks looked for was present, and the advice was reversed.
describe('a restyle that reverses a safety fact', () => {
  it('rejects "non-toxic" written over a toxicity warning', () => {
    expect(driftReasons(
      'Toxic to cats and dogs (ASPCA).',
      'Ferny is non-toxic, so your cats can nibble freely.',
    )).toContain('safety-claim');
  });

  it('rejects "safe" written over "no record" — no record is not safe', () => {
    expect(driftReasons(
      'No toxicity record for this species.',
      'Ferny is perfectly safe around pets and children.',
    )).toContain('safety-claim');
  });

  it('rejects reassurance invented from facts that never mentioned harm', () => {
    expect(driftReasons(SUNFLOWER_FACT, 'It is pet-friendly, and it was watered 2 days ago.'))
      .toContain('safety-claim');
  });

  it('lets a note repeat a reassurance the facts did make', () => {
    expect(driftReasons(
      'Recorded as non-toxic to cats and dogs.',
      'The record says it is non-toxic to cats and dogs.',
    )).not.toContain('safety-claim');
  });
});

describe('a restyle that reverses the advice', () => {
  it('rejects "water it today" written over "hold off"', () => {
    expect(driftReasons(SUNFLOWER_FACT, 'Water Ferny today.')).toEqual(['polarity']);
  });

  it('rejects "it can wait" written over "likely due"', () => {
    const due = '💧 Watering: done 12 days ago — past the 10 day mark. Likely due.';
    expect(driftReasons(due, 'Hold off on watering Ferny for a while.'))
      .toContain('polarity');
  });

  it('rejects a dry-out written over a keep-moist regime', () => {
    const moist = '💧 From its sources: keep the medium evenly moist.';
    expect(driftReasons(moist, 'Let Ferny dry out completely between drinks.'))
      .toContain('polarity');
  });

  it('rejects keeping a dry-between plant wet', () => {
    const dry = '💧 From its sources: let the medium dry thoroughly between waterings.';
    expect(driftReasons(dry, 'Keep the soil wet at all times, and it will thrive.'))
      .toContain('polarity');
  });

  it('accepts a paraphrase that keeps the direction', () => {
    expect(driftReasons(
      SUNFLOWER_FACT,
      'Ferny had a drink 2 days ago, so hold off on watering for 3 more days.',
    )).toEqual([]);
    const moist = '💧 From its sources: keep the medium evenly moist.';
    expect(driftReasons(moist, 'Keep it evenly moist and never let it dry out.'))
      .not.toContain('polarity');
  });
});

describe('safety lines never reach the model', () => {
  const WITH_WARNING = [
    '💧 Watering: done 2 days ago. Next window opens in 3 days — hold off.',
    '⚠️ Ferny is toxic to pets.',
  ].join('\n');

  it('splits warnings and toxicity lines from the rest, word for word', () => {
    expect(splitSafetyLines(WITH_WARNING)).toEqual({
      styleable: '💧 Watering: done 2 days ago. Next window opens in 3 days — hold off.',
      safety: ['⚠️ Ferny is toxic to pets.'],
    });
    expect(splitSafetyLines('Sap is poisonous if eaten.\nRotate weekly.').safety)
      .toEqual(['Sap is poisonous if eaten.']);
  });

  it('keeps the warning out of the prompt and appends it verbatim before the sign-off', async () => {
    mockAvailable.mockResolvedValue(true);
    mockGenerate.mockResolvedValue(
      'Ferny had a drink 2 days ago, so the next watering window opens in 3 days.');
    const result = await gnomeVoice(WITH_WARNING, 'Ferny');

    const prompt = mockGenerate.mock.calls[mockGenerate.mock.calls.length - 1][0];
    expect(prompt).not.toMatch(/toxic/i);
    expect(result.styled).toBe(true);
    expect(result.text.split('\n')).toEqual([
      'Ferny had a drink 2 days ago, so the next watering window opens in 3 days.',
      '⚠️ Ferny is toxic to pets.',
      SIGN_OFF,
    ]);
  });

  it('falls back flat, warning and all, when the model mentions a hazard it was never shown', async () => {
    mockAvailable.mockResolvedValue(true);
    mockGenerate.mockResolvedValue('Ferny is non-toxic; the next watering window opens in 3 days.');
    const result = await gnomeVoice(WITH_WARNING, 'Ferny');
    expect(result).toEqual({ text: WITH_WARNING, styled: false });
  });

  it('does not run the model at all when every line is a warning', async () => {
    mockAvailable.mockResolvedValue(true);
    mockGenerate.mockClear();
    const result = await gnomeVoice('⚠️ Ferny is toxic to pets.');
    expect(result).toEqual({ text: '⚠️ Ferny is toxic to pets.', styled: false });
    expect(mockGenerate).not.toHaveBeenCalled();
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
