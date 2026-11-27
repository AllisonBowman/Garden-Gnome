// English strings: capture (Walk the garden, and saving what it found).
// The source of truth; es/capture.ts mirrors its keys.
const capture = {
  save: {
    nothingSaved: 'Nothing was saved',
    savedSome: 'Saved {{saved}} of {{total}}',
    signedOut: 'You’ve been signed out, so the rest weren’t saved. Sign in again to add them.',
    listStillHere: 'Your list is still here.',
    othersStillHere_one: 'The other {{count}} is still here.',
    othersStillHere_other: 'The other {{count}} are still here.',
    tryAgainSoon: 'Try again in a moment.',
    unreachable: 'PlantAdvocate couldn’t reach the server.',
    somethingWrong: 'Something went wrong while saving them.',
    serverBusy: 'The server couldn’t take them just now.',
    refused: 'The server didn’t accept them as they are. A species or growing area in the list may have changed since you started.',
    checkList: 'Check the list, then try again.',
  },
  walk: {
    micNeeded: 'PlantAdvocate needs the microphone to listen. You can still type.',
    listeningOnDevice: 'Listening — say what’s planted. Nothing leaves your phone.',
    listeningApple: 'Listening — this device sends audio to Apple to transcribe it.',
    cantListen: 'Couldn’t start listening. You can still type.',
    nothingToAdd: 'Nothing to add there — try naming a plant.',
    eyebrow: 'WALK AND SAY WHAT YOU SEE',
    placeholder: 'Twelve tomatoes along the south fence, a rosemary bush by the gate…',
    label: 'What’s planted here?',
    keyboardMic: 'Tap the microphone on your keyboard to speak instead of typing.',
    listening: '● Listening — tap the square to stop.',
    catalogFailed: 'Couldn’t load the plant catalog, so nothing you say can be matched yet. What you’ve typed stays here.',
    loadingCatalog: 'Loading the catalog…',
    addThese: 'Add these',
    cameraOn: 'Turn the camera on',
    addAll: 'Add {{n}} to the garden',
    addSome: 'Add {{ready}} of {{total}} — pick a species for the rest',
    howMany: 'How many',
    cantPlace: 'Couldn’t place this one — search below.',
    pickOne: 'Pick which one you meant.',
    searchCatalog: 'Search the catalog',
  },
};

export default capture;
