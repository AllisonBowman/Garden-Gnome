// English strings: almanac. The source of truth; es/almanac.ts mirrors its keys.
const almanac = {
  tiers: {
    beginner: 'Beginner',
    intermediate: 'Intermediate',
    fussy: 'Fussy',
  },
  light: {
    low: '◐ low',
    medium: '◑ medium',
    bright_indirect: '☀ bright indirect',
    direct: '☀☀ direct sun',
    noDirect: '☀ no direct sun',
    upTo: '☀ up to {{hours}}h direct sun',
    footcandles: '☀ {{fc}}+ footcandles',
  },
  regime: {
    keep_moist: '💧 evenly moist',
    keep_barely_moist: '💧 barely moist',
    dry_surface_between: '💧 top dries between',
    dry_thoroughly_between: '💧 dries out between',
    every: '💧 every {{min}}–{{max}}d',
  },
  screen: {
    all: 'All',
    owned: '✿ you keep this one',
    /** Fills "Couldn't load {{what}}" in care/loadFailed. */
    loadFailedName: 'the Almanac',
    intro_one: 'A living count of what growers keep — {{count}} species in the catalog. Read any species to learn its ways.',
    intro_other: 'A living count of what growers keep — {{count}} species in the catalog. Read any species to learn its ways.',
    introOwned_one: 'A living count of what growers keep — {{count}} species in the catalog, {{owned}} of them on your shelf. Read any species to learn its ways.',
    introOwned_other: 'A living count of what growers keep — {{count}} species in the catalog, {{owned}} of them on your shelf. Read any species to learn its ways.',
    search_one: 'Search {{count}} species…',
    search_other: 'Search {{count}} species…',
    anywhere: 'Anywhere',
    fits: 'Fits {{name}}',
    gradedOnly: 'Graded only where the catalog records humidity, temperature or light.',
    gradedOnlyUngraded_one: 'Graded only where the catalog records humidity, temperature or light — {{count}} species have nothing to grade yet and aren’t in any grade.',
    gradedOnlyUngraded_other: 'Graded only where the catalog records humidity, temperature or light — {{count}} species have nothing to grade yet and aren’t in any grade.',
    shown_one: 'Species · {{count}} shown',
    shown_other: 'Species · {{count}} shown',
    fitNote: 'Showing species with nothing on record against {{area}} and at least one thing confirmed. A plant missing from here may simply be one the catalog can’t judge for this spot yet. {{rankOrder}}',
    tryAgain: 'Try again',
    checking: 'Checking what suits that spot…',
    noMatch: 'Nothing matches that. Try a different name, or widen the filter.',
  },
};

export default almanac;
