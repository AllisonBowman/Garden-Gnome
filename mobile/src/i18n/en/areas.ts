// English strings: areas (growing areas: setup, the area's page, fit
// findings, ranking). The source of truth; es/areas.ts mirrors its keys.
const areas = {
  // growingAreas/fitFindings.ts
  axis: {
    indoor_outdoor: 'Indoors or out',
    sun: 'Sun',
    soil: 'Soil',
    footprint: 'Size',
    upkeep: 'Upkeep',
    goal: 'What it’s for',
  },
  /** The last joiner of a list: "a, b and c". */
  listAnd: '{{head}} and {{last}}',
  confirmedHere: 'Confirmed here: {{list}}.',
  notKnownHere: 'Not known here: {{list}}.',
  misfitIntro: 'Worth knowing before it goes in {{area}}',
  cantJudge: 'The catalog can’t judge it for {{area}} yet — nothing is on '
    + 'record for or against it there, so this is no recommendation either way.',
  nothingAgainst: 'Nothing on record against it in {{area}}. Confirmed: {{list}}.',
  notKnown: 'Not known: {{list}}.',
  checkFailed: 'Couldn’t reach the catalog to check this just now — that isn’t an all-clear. '
    + 'Try again in a moment.',

  // growingAreas/placement.ts
  noAreaNote: 'You have no growing areas yet, so this plant will go in a new one called '
    + '“{{name}}”. To have the space checked against this plant, first '
    + 'add a growing space from Home.',
  areasFailedFrom: 'Couldn’t load your growing areas just now, so this plant will go in '
    + 'the one you came from. You can move it from the plant’s page afterwards.',
  areasFailedOldest: 'Couldn’t load your growing areas just now, so this plant will go in '
    + 'your oldest one. You can move it from the plant’s page afterwards.',

  // growingAreas/ranking.ts
  rankOrder: 'The more that’s confirmed here, the higher a species sits; where they tie, it’s A to Z.',
  listIntroOne: 'One species has nothing on record against this spot and at least one '
    + 'thing confirmed.',
  listIntroMany: '{{total}} species have nothing on record against this spot and at least '
    + 'one thing confirmed. {{order}}',
  showingOf: 'Showing {{shown}} of {{total}}.',
  showingFirst: 'Showing the first {{shown}}.',
  cutTie: '{{showing}} The next one has as much confirmed as the last one here, so '
    + 'where this list stops is down to the alphabet, not the evidence.',
  cutLess: '{{showing}} Everything after these has less confirmed.',

  // growingAreas/realEstate.ts
  surface: {
    in_ground_bed: '🌍 In-ground bed',
    raised_bed: '🪵 Raised bed',
    containers: '🪴 Containers',
    windowsill: '🪟 Windowsill',
    shelf_or_floor: '🗄️ Shelf or floor',
    hanging: '🌿 Hanging',
    greenhouse_bench: '🏕️ Greenhouse bench',
    pond_or_water: '💧 Pond or water',
  },
  sunHint: 'Hours of direct sun a day: full sun is 6 or more, partial 3 to 6, shade under 3.',
  indoorOutdoorHint: 'Outdoors if it follows the outside temperature — a greenhouse does.',
  goal: {
    edible: { label: '🥕 Something to eat', hint: 'Only species grown to eat.' },
    low_upkeep: { label: '😌 Low upkeep', hint: 'Only species that tolerate being left alone.' },
    pollinators: {
      label: '🐝 Feeds pollinators',
      hint: 'Only species recorded as feeding bees, butterflies or hummingbirds.',
    },
  },
  areaType: {
    home: '🏠 Home',
    nursery: '🌱 Nursery',
    community_garden: '🌳 Community garden',
    conservation: '🌿 Conservation',
    research: '🔬 Research',
    balcony: '🪴 Balcony',
    greenhouse: '🏕️ Greenhouse',
    other: '📍 Other',
  },
  needName: 'Give it a name to go on — one you’ll know it by among your other spaces.',
  depthUnchecked: 'Kept with the space — no plant is checked against it yet.',
  dim: {
    areaLabel: 'Footprint (sq ft)',
    areaHintBed: 'Roughly how much bed there is to fill.',
    areaHintWater: 'Surface area of the water.',
    areaHintOther: 'How much shelf, sill or floor this spot gives you.',
    headroomLabel: 'Headroom (inches)',
    headroomHintBed: 'How tall something can get before it shades or crowds its neighbours.',
    headroomHintOther: 'Distance to the shelf, cupboard or ceiling above.',
    depthLabelBed: 'Soil depth (inches)',
    depthLabelWater: 'Water depth (inches)',
    depthLabelOther: 'Pot depth (inches)',
    depthHintBed: 'How far roots can run before they hit hardpan, liner or rock.',
    depthHintWater: 'Depth at the planting shelf, not the deepest point.',
    depthHintOther: 'Inside depth of the pots you’ll use here.',
  },
  /** A hint followed by another sentence. */
  twoSentences: '{{first}} {{second}}',
  measuredBoth: '{{said}} ({{inches}} in)',
  sqft: '{{n}} sq ft',
  lengthEcho: 'That’s {{said}}.',
  note: {
    indoorLight: 'Indoor light isn’t checked: nothing records how bright this spot is, '
      + 'so nothing here was matched on light.',
    goalsUnanswered: 'Nothing here is filtered by what you asked for ({{goals}}). '
      + 'Nothing on this list has a source that answers it yet, so the list '
      + 'honours the space but not the wish.',
    sizeUnchecked: 'Size isn’t checked against your measurements. Nothing on this list has '
      + 'a recorded mature size to set against them, so whether any of it would '
      + 'outgrow the space is unknown.',
    depthUnchecked: '{{depth}} isn’t checked: nothing on this list was compared with the '
      + '{{inches}} in you measured.',
  },

  // GrowingAreasScreen
  list: {
    plants_one: '{{count}} plant',
    plants_other: '{{count}} plants',
    weather: 'Weather ›',
    loadFailed: 'Couldn’t load your growing areas.',
    empty: 'No growing areas yet. Create one to get started.',
    newArea: 'New growing area',
  },
  setup: {
    stepTitles: {
      space: 'The space',
      conditions: 'The conditions',
      goals: 'What it’s for',
    },
    stepOf: 'Step {{step}} of {{total}}',
    name: 'Name *',
    surfaceQ: 'What will plants sit in?',
    roomQ: 'How much room is there?',
    roomHint: 'Leave anything you haven’t measured blank. Blank means unknown, '
      + 'and nothing gets recommended on a guess.',
    location: 'Location',
    locationHint: 'Set a place to unlock local weather. Search an address or use your '
      + 'location — only a real, resolved place can be saved.',
    presetFrom: 'Set from “{{surface}}”. Change anything that isn’t right.',
    conditionsHint: 'Describe how much of the weather actually reaches this spot.',
    shelter: 'Shelter',
    sheltered: 'Sheltered',
    partial: 'Partial',
    exposed: 'Exposed',
    indoorOrOut: 'Indoors or out',
    indoors: 'Indoors',
    outdoors: 'Outdoors',
    sun: 'Sun',
    fullSun: 'Full sun',
    shade: 'Shade',
    kindOfPlace: 'Kind of place',
    kindHint: 'Only used to group your spaces in the census — it doesn’t '
      + 'change what gets suggested.',
    goalsHint: 'Pick any that apply, or none. These narrow what gets suggested '
      + 'for this spot — they never loosen it.',
    noGoals: 'Nothing in particular — you’ll see whatever fits the space.',
    cancel: 'Cancel',
    back: 'Back',
    create: 'Create',
    next: 'Next',
    createFailedTitle: 'Couldn’t create it',
    createFailedBody: 'This growing area couldn’t be saved just now. Check your connection and '
      + 'try again — everything you entered is still here.',
  },

  // AreaFitCard
  fit: {
    inArea: 'In {{area}}',
    tryAgain: 'Try again',
    against: 'Against it here',
    confirmed: 'Confirmed here',
  },

  // GrowingAreaDetailScreen
  detail: {
    shelter: {
      sheltered: '🏠 Sheltered',
      partial: '⛱️ Partial cover',
      exposed: '🌤️ Exposed',
    },
    temp: {
      indoor: '🌡️ Indoors',
      outdoor: '🍃 Outdoors',
    },
    sun: {
      full_sun: '☀️ Full sun',
      partial_sun: '🌤️ Partial sun',
      shade: '🌥️ Shade',
    },
    thisArea: 'this growing area',
    saveFailedTitle: 'Could not save that place',
    saveFailedBody: 'PlantAdvocate could not reach the server. Check your connection and try again.',
    addPlantHere: 'Add a plant here',
    theSpace: 'The space',
    unmeasured: 'Not measured yet: {{list}}. Until it is, nothing is '
      + 'recommended or ruled out on size here.',
    whatFor: 'What it’s for',
    noGoals: 'Nothing in particular — anything that fits the space.',
    needsAddressing: 'Needs addressing',
    tryAgain: 'Try again',
    noPlantsYet: 'No plants here yet. Anything this space has against a plant '
      + 'you add here will show up on this card.',
    nothingContradicts: 'Nothing here contradicts the space. Plants the catalog can’t '
      + 'judge aren’t listed as fine — they’re just not listed.',
    goodCandidates: 'Good candidates here',
    noCandidates: 'Nothing to put forward yet. A species only appears here once a '
      + 'source has confirmed it suits this spot — an unresearched plant '
      + 'isn’t a recommendation.',
    opensSpecies: 'Opens {{name}}, with how it suits this space',
    seeAll: 'See all {{total}} in the Almanac',
    seeRest: 'See the rest in the Almanac',
    careCalendar: 'Care calendar',
    careFailed: 'Couldn’t load the care calendar just now — that isn’t an all-clear.',
    noChecksNoPlants: 'No checks scheduled here yet. Add plants to this growing area and '
      + 'their checks fill in the calendar.',
    nothingInSeason: 'Nothing in season to check here right now.',
    localWeather: 'Local weather',
    noPlace: 'This growing area has no place yet, so there’s no forecast to '
      + 'show. Set where it is and the weather follows.',
    savePlace: 'Save this place',
    noWeather: 'Weather isn’t available for this spot yet.',
    humidity: '💧 {{pct}}% humidity',
    outsideIn: 'OUTSIDE → IN HERE',
    perPlantTiming: 'Per-plant timing lives in each plant’s “Ask the Gnome” advice.',
  },
};

export default areas;
