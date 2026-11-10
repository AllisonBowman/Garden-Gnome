// One sign-in at a time.
//
// A sign-in is a round-trip through Apple's or Google's sheet and then our
// server, which can take 20 seconds against a machine waking from zero. A
// second tap in that window used to start a second sheet or a parallel
// sign-in for the Apple button, which had no busy state at all. React state
// alone can't stop it: two taps can land before the re-render that disables
// the button. So the screen holds one of these, checked synchronously.
//
// Pure on purpose (no React Native imports) so jest can pin it.

export type Provider = 'apple' | 'google';

export interface SignInGate {
  /** Claim the gate for `provider`. False when a sign-in is already running. */
  tryStart(provider: Provider): boolean;
  /** Release the gate, however the sign-in ended. */
  finish(): void;
  /** Which provider holds the gate, if any. */
  current(): Provider | null;
}

export function createSignInGate(): SignInGate {
  let running: Provider | null = null;
  return {
    tryStart(provider) {
      if (running !== null) return false;
      running = provider;
      return true;
    },
    finish() {
      running = null;
    },
    current() {
      return running;
    },
  };
}
