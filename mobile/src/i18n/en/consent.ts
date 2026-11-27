// English strings: consent. The source of truth; es/consent.ts mirrors its keys.
// Every sentence here must stay true of the code (see src/consent/copy.ts).
const consent = {
  destination: {
    device: 'Stays on your phone',
    server: 'Sent to our server',
    partner: 'Shared with another service',
  },
  census: {
    fields:
      'its species, how many there are, its growth stage, the month you got it and '
      + 'how it looked then (soil, leaves, any pests), how many times each kind of '
      + 'care was logged in each month, how many growing areas it has been in and '
      + 'the months it moved between them, which planting it was split from if it '
      + 'was, and its growing area’s type, city, region and country',
    leftOut:
      'There is no name, no email, no nicknames, no notes, no exact dates and no '
      + 'coordinates.',
    linking:
      'Each planting and growing area gets a new label in every export, and the '
      + 'records are shuffled, so no identifier links one export to another. That '
      + 'is the promise, and no more: a planting’s monthly care counts could still '
      + 'look alike from one export to the next.',
  },
  flows: {
    identify: {
      title: 'Identifying a plant from a photo',
      summary: 'The photo is read on your phone and never uploaded.',
      detail:
        'Your phone’s own AI looks at the picture and suggests a name — Apple '
        + 'Intelligence on iPhone, Gemini Nano on Android. The image is not sent '
        + 'to us, and it is not sent to anyone else. If your phone can’t do this, '
        + 'the feature simply says so rather than falling back to uploading.',
    },
    diagnose: {
      title: 'Asking the Gnome to look at an ailing plant',
      summary: 'This one does upload the photo. It is not kept.',
      detail:
        'Photo check-ups work differently from identification. The picture, and '
        + 'any note you add, goes to our server, which passes it to an outside AI '
        + 'service to be read. The photo is not saved to your account, and '
        + 'PlantAdvocate does not use it to train anything. Only the reading, as '
        + 'text, is saved to your plant’s timeline. The app asks before the first '
        + 'photo is sent.',
    },
    care: {
      title: 'Your plants and care log',
      summary: 'Nicknames, species, and what you did when.',
      detail:
        'Stored so your schedule survives a new phone, and so advice can account '
        + 'for what you have actually been doing rather than what the label says. '
        + 'This is your record; you can delete the whole account, and everything '
        + 'in it, from this screen.',
    },
    advice: {
      title: 'Free-text questions to the Gnome',
      summary: 'Your question goes to an outside AI service. Your photos don’t.',
      detail:
        'Care advice is built from the curated species database. When you add a '
        + 'question in your own words, our server sends it to an outside AI '
        + 'service to be answered. The plant’s nickname, species facts and recent '
        + 'care log go with it, and so do its growing area’s name, conditions and '
        + 'forecast. Your name, email and coordinates are not included. The app '
        + 'asks before the first question is sent.',
    },
    voice: {
      title: 'Walking the garden out loud',
      summary: 'Your speech becomes text on your phone, or at Apple. We never get the audio.',
      detail:
        'Walk the garden uses the microphone only while it says Listening. It '
        + 'stops when you tap stop or leave the screen. Your iPhone turns speech '
        + 'into text on the phone where it can. Where it can’t, iOS sends the '
        + 'audio to Apple’s speech service to transcribe, and the screen tells you '
        + 'which is happening. PlantAdvocate never receives the audio. Only the '
        + 'plants you confirm — species, how many, and any spot you named — reach '
        + 'your account, as text.',
    },
    location: {
      title: 'A growing area’s location',
      summary: 'Coordinates go to weather services. They never reach the census.',
      detail:
        'When you give a growing area an address or use your current location, '
        + 'your phone’s own map service turns it into a place. We store its city, '
        + 'region, country and coordinates. To get that spot’s forecast, our '
        + 'server asks weather services in turn and stops at the first that '
        + 'answers: Apple Weather, then the U.S. National Weather Service, then '
        + 'Open-Meteo, which also covers places outside the U.S. Each one asked '
        + 'gets the coordinates rounded to about a kilometer, and nothing else '
        + 'about you, and the forecast card names whichever one answered. '
        + 'Coordinates are left out of the community census by construction, not '
        + 'by policy.',
    },
    census: {
      title: 'The community census',
      summary: 'Off unless you turn it on.',
      detail:
        'The census asks what the whole community is growing and how it is '
        + 'faring, so care advice can improve for everyone. If you join, each of '
        + 'your plantings is counted: {{fields}}. {{leftOut}} '
        + '{{linking}} If you don’t join, none of your data is counted at all.',
    },
  },
  photoNotice: {
    title: 'This sends your photo off your phone',
    body:
      'A photo check-up is the one feature that uploads a picture. It goes to our '
      + 'server with any note you add, and on to an outside AI service that reads '
      + 'it. The photo isn’t saved, and PlantAdvocate doesn’t use it to train '
      + 'anything. Only the reading is kept, on your plant’s timeline.\n\n'
      + 'Identifying a plant is different — that happens entirely on your phone.',
    confirm: 'Send the photo',
    cancel: 'Not now',
  },
  questionNotice: {
    title: 'This sends your question off your phone',
    body:
      'A question in your own words goes to our server and on to an outside AI '
      + 'service to be answered. Your plant’s nickname, species facts and recent '
      + 'care log go with it, and so do its growing area’s name, conditions and '
      + 'forecast. Your name, email and coordinates are not included.\n\n'
      + '“Not now” sends nothing, and your question stays in the box.',
    confirm: 'Send my question',
    cancel: 'Not now',
  },
  censusConsent: {
    label: 'Join the community census',
    on: 'Each of your plantings is counted: {{fields}}. {{leftOut}} {{linking}}',
    off:
      'Your data is not counted. If you turn this on, each of your plantings is '
      + 'counted as “The community census” below lists it, with no name, email, '
      + 'notes, exact dates or coordinates. It helps the care advice get better '
      + 'for plants like yours; turning it back off stops it immediately. Counts '
      + 'already taken aren’t recalled.',
  },
  privacyIntro:
    'Plainly: what this app does with what you give it. The full policy is '
    + 'linked at the bottom and is the binding version.',
};

export default consent;
