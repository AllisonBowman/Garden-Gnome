# TestFlight notes — 1.1.2

Paste the block below into the build's **What to Test** field in App Store
Connect, then add testers.

> **Pick the build by BUILD NUMBER, not the version string.** Build numbers do
> not reset per version — 1.0.0 alone held builds 3, 10 and 11.

---

```
PlantAdvocate 1.1.2 — what's new

This one is mostly fixes to Walk the garden, from testing 1.1.1 on a real
phone. Thank you — the microphone problem below was found that way.

1. Walk the garden now keeps every plant you name.
   Previously only the last one survived: the recogniser stops listening
   after each finished sentence, and the text was being overwritten each
   time you paused. Both are fixed. Walk a bed and name several plants in
   a row without stopping — all of them should be waiting for you.

2. Each plant appears as you say it.
   Rather than everything arriving in one heap at the end, a plant shows up
   to confirm while you're still standing in front of it. Check it, correct
   the count or the species, or discard it, and keep walking.
   If it can't match what you said, it keeps your words in the box instead
   of dropping them — so nothing is silently lost.

3. Plants can be moved between growing environments, and removed.
   Both are at the bottom of a plant's own screen.
   Moving keeps everything: the same plant, its whole care log and history,
   now in a different place.
   Removing takes the care log with it and asks first. It can't be undone.

Worth trying, in rough order of how much it would help:

- Walk and name four or five plants in one go, pausing between each. Every
  one should be there to confirm. This is the fix we most need checked.
- Say something with a count and a place: "twelve tomatoes along the south
  fence". The count and location should land in the right boxes.
- Say something it won't know, or mumble one. It should keep your words
  and say it couldn't place them, rather than guessing or losing them.
- Move a plant to another environment, then open it and confirm its care
  log came along.
- Remove a plant you don't want and confirm it asks first.

Still expected, not bugs:
- No UV reading and no "hours of daylight" on the weather card. Apple's
  weather service has a provisioning fault on their end, so weather comes
  from the National Weather Service, which doesn't publish those two.
- On a phone without Apple Intelligence, the photo-identify button in Add
  Plant simply isn't there. Manual species search works for everyone.
- Similar-looking species can still be confused by photo identification.
  That's a known limitation with a fix planned; no need to report it.
```

---

## What this build has NOT proven

Be honest with testers about where the real uncertainty is.

- **The microphone fix has never run anywhere but a phone.** A simulator has
  no audio device to open, so none of the speech path can be exercised there.
  This build is the first test of it.
- **The move/remove card was never seen rendering.** Typecheck is clean and it
  follows the patterns already on that screen, but the simulator session where
  it would have been confirmed went bad — three devices ended up booted at
  once and screenshot capture degraded. First real look is on a phone.

## What to report back

1. Did naming several plants in a row keep all of them?
2. If not — what you said, what appeared in the box, and whether the screen
   said on-device or Apple transcription.
3. Did moving a plant keep its care log?
4. Anything that looked wrong which isn't in the "still expected" list.
