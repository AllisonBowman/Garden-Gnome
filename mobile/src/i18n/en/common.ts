// English strings: common. The source of truth; es/common.ts mirrors its keys.
// Shared words, the error card, permission alerts, photo ID and report emails.
const common = {
  tryAgain: 'Try again',
  notNow: 'Not now',
  openSettings: 'Open Settings',
  cancel: 'Cancel',
  ok: 'OK',
  errorCard: {
    title: 'Something went wrong here',
    body: 'This screen ran into a problem. Nothing you’ve saved is lost.',
    report: 'Report this problem',
  },
  cameraOff: {
    title: 'Camera access is off',
    body: 'PlantAdvocate can’t open the camera because camera access is turned off. You can turn it on in Settings, or use “Choose photo” to pick an existing picture.',
  },
  locationOff: {
    title: 'Location access is off',
    body: 'PlantAdvocate can’t read your location because location access is turned off. You can turn it on in Settings, or just type the address instead.',
  },
  link: {
    title: 'Could not open link',
    noMail: 'No mail app is set up on this device. You can reach us at {{email}}.',
    cannotOpen: 'Your device could not open {{url}}.',
  },
  report: {
    problemSubject: 'Report a problem in PlantAdvocate',
    problemPrompt: 'Tell us what you were doing when this happened:',
    factPrompt: 'Which fact looks wrong, and why? A link to where you read otherwise helps us check it.',
    resultPrompt: 'Tell us what was wrong or inappropriate about this result:',
    factSubject: 'Report a fact',
    resultSubject: 'Report a {{surface}} result',
  },
  photoId: {
    suggestions: 'Suggested from the photo. Tap the one that matches, and check it’s right before you save.',
    suggested: 'Suggested from the photo. Confirm it’s right, or pick another below.',
    unavailable: 'Your phone can’t suggest plants from photos. Search for yours below.',
    unreadable: 'Couldn’t read the photo this time. Search for your plant below.',
    noName: 'Your phone couldn’t suggest a name for this one. Search for it below.',
    notInCatalog: 'Your phone suggested “{{suggested}}”, but that isn’t in the catalog yet. Search below for the closest match.',
  },
};

export default common;
