// First-run onboarding, in the order it is read. Pure data, so the claims
// in it can be checked against the screens they point to (slides.test.ts).
//
// Short and plain: what the app is, then the land, then what the land shows,
// then the plants. The land comes before the plants because Home is a report
// on the land: with no land yet, Home shows one "Add your land" card, which
// is where the last slide's button leads.

export interface Slide {
  emoji: string;
  title: string;
  body: string;
}

/** The Spaces screen's title. App.tsx titles that screen from this constant;
 *  the slides no longer mention it, since there are no tabs any more. */
export const GROWING_AREAS_TAB = 'Growing areas';

/** Where the last slide's button leads, and what it says. Home, because the
 *  app is land-first: a new account's Home starts with "Add your land". */
export const FINISH: { route: 'Home'; label: string } = {
  route: 'Home',
  label: 'Get started',
};

export const SLIDES: Slide[] = [
  {
    emoji: '🌱',
    title: 'Welcome to PlantAdvocate',
    body: 'PlantAdvocate helps you look after your land and the plants on it, through the seasons.',
  },
  {
    emoji: '📍',
    title: 'Add your land',
    // The public maps are asked only about United States pins
    // (garden-gnome/app/services/coverage.py); setup says the same.
    body: 'Type an address or use your location, then put a pin on your home. '
      + 'PlantAdvocate reads public maps to estimate sun, where water collects, soil, '
      + 'hardiness zone and frost dates. Each estimate says how sure it is and where it came from, '
      + 'and you can correct any of them. The maps cover land in the United States.',
  },
  {
    emoji: '🗺️',
    title: 'See your land',
    body: 'Home shows a map of your land with Sun, Trees and Water layers, the weather forecast, '
      + 'and a season timeline. Each step on it says what to do and why.',
  },
  {
    emoji: '💧',
    title: 'Add plants, log care',
    // Advice: the plant page's "Get care advice" is always offered and is
    // rule-based (care/resultLabels.ts). Photo check-ups and free-text
    // questions are switched off, so they are not mentioned.
    body: 'Add each plant where it grows, then tap to log watering, feeding and more. '
      + 'Each species has care facts and hazards, with sources where they are known. '
      + 'A plant’s page also gives care tips, worked out by set rules from its species and its care log.',
  },
];
