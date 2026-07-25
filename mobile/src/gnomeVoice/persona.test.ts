import { PERSONA_CONTRACT, SIGN_OFF, appendSignOff } from './persona';

// The persona contract is the single definition of voice. These tests pin the
// clauses the drift guard depends on: if a clause is dropped from the prompt,
// the guard is still enforcing a rule the model was never told about, which is
// how the screenshot letter happened in the first place.

describe('PERSONA_CONTRACT', () => {
  it('addresses the caretaker in the second person', () => {
    expect(PERSONA_CONTRACT).toMatch(/Speak to the caretaker as "you"/);
  });

  it('refers to the plant in the third person', () => {
    expect(PERSONA_CONTRACT).toMatch(/third\s+person by its name/);
  });

  it('forbids the gnome performing care itself', () => {
    expect(PERSONA_CONTRACT).toMatch(/never water, fertilize, prune, or repot/);
  });

  it('forbids promising app behaviour', () => {
    expect(PERSONA_CONTRACT).toMatch(/Never promise app behaviour/);
  });

  it('forbids letter scaffolding and placeholders', () => {
    expect(PERSONA_CONTRACT).toMatch(/no greeting line, no closing, no /);
    expect(PERSONA_CONTRACT).toMatch(/placeholders in brackets/);
  });

  it('demands digits, which is what makes the number guard verifiable', () => {
    expect(PERSONA_CONTRACT).toMatch(/never "thirty-five days"/);
  });

  it('never asks the model to sign off — code does that', () => {
    expect(PERSONA_CONTRACT).not.toContain(SIGN_OFF);
  });
});

describe('appendSignOff', () => {
  it('appends the one fixed sign-off', () => {
    expect(appendSignOff('Your fern looks happy.')).toBe(
      `Your fern looks happy.\n${SIGN_OFF}`,
    );
  });

  it('is idempotent, so a re-styled note never doubles the signature', () => {
    const once = appendSignOff('All good.');
    expect(appendSignOff(once)).toBe(once);
  });

  it('leaves empty text alone rather than emitting a bare signature', () => {
    expect(appendSignOff('   ')).toBe('');
  });

  it('uses "the Gnome", never the pre-rebrand "Garden Gnome"', () => {
    expect(SIGN_OFF).toContain('the Gnome');
    expect(SIGN_OFF).not.toMatch(/Garden Gnome/i);
  });
});
