# TestFlight 1.1.1 (build 13) — what to test

Paste the block below into the build's **What to Test** field in App Store
Connect. Build 12 (1.1.0) never had notes written and is superseded by this one
— skip it and release this instead.

**Two new permission prompts appear in this build** — microphone and speech
recognition. Neither has ever been asked for before, so testers will see them
the first time they open Walk the garden. That is expected.

---

```
PlantAdvocate 1.1.1 — what's new

1. Walk the garden. From the Plants tab, tap "Walk the garden". Point the
   camera at what's growing and say what's there, in plain words:

       "Twelve tomatoes along the south fence, a rosemary bush by the
        gate, and three basil in pots"

   It splits that into separate plants, works out how many of each, and
   matches them to the catalogue. Check the list it builds, fix anything
   it got wrong, then tap Add these.

   It will ask for the microphone and for speech recognition the first
   time. Speech is transcribed on your device where your phone supports
   it — the screen tells you which is happening.

   You can also just type into the box if you'd rather not talk.

2. Plants can have a count now. A row can read "12 × Tomatoes — south
   fence" instead of twelve separate entries. Watering it waters the
   group. Existing plants are unchanged and still stand for one plant
   each.

3. The catalogue tells cultivars apart. Searching "tomato" used to show
   five identical rows reading "Tomato". They now read "Tomato 'Sungold'",
   "Tomato 'Big Beef'" and so on, and plain "Tomatoes" is its own row.
   511 rows were renamed this way.

4. Weather. Apple's weather service has a fault on Apple's side that we
   can't fix in the app, so forecasts now come from the National Weather
   Service. Expected side effect: no UV index and no "hours of daylight"
   for any environment. That is not a bug — please don't report it.

Worth trying on a real phone:
- Describe a few plants out loud and see how much it gets right. Odd
  results are useful — send the exact words you said.
- Try it somewhere with no signal. It should still hear you and only
  need a connection when you tap Add these.
- Sign in with Apple, which can't be tested any other way.
- Add a plant by photo, if your phone is an iPhone 15 Pro or newer.
```

---

## What we know is untested

The speech module compiled and ran for the first time in this build. On the
simulator we could confirm three things and only three: the module links, both
permissions are requested with the right wording, and failure is graceful.

**No word has ever been transcribed by this app.** The simulator has no audio
input device to open — Apple's own audio server times out there and aborts the
process — so a real phone is the first time anyone will see it work at all.

If it fails on device, the useful things to report are: what you said, what
appeared in the box, and whether the screen claimed on-device or Apple
transcription.
