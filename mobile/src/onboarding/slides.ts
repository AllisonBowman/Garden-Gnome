// First-run onboarding, in the order it is read. Pure data, so the claims
// in it can be checked against the screens they point to.
//
// Minimal, calm — the beats of the core loop, not a SaaS product tour. The
// place comes before the plant: a plant is added to a growing area, and a
// first plant added before anyone has said where they grow lands in the one
// every account starts with, an indoor "My Home" with nothing measured.

export interface Slide {
  emoji: string;
  title: string;
  body: string;
}

/** The tab the growing-area slide sends people to, by the title it wears. */
export const GROWING_AREAS_TAB = 'Growing areas';

export const SLIDES: Slide[] = [
  {
    emoji: '🌱',
    title: 'Welcome to PlantAdvocate',
    body: 'A calm home for your plants and the care you give them.',
  },
  {
    emoji: '🌍',
    title: 'Describe where you grow',
    body: `A windowsill isn’t a back bed. In ${GROWING_AREAS_TAB}, describe each place you grow, `
      + 'and PlantAdvocate shows what suits it — and says what it can’t check.',
  },
  {
    emoji: '💧',
    title: 'Add plants, log care',
    body: "Add each plant where it grows, then tap to log watering, feeding, and more. PlantAdvocate keeps track so you don't have to.",
  },
  {
    emoji: '🧙',
    title: 'Ask the Gnome',
    body: "Not sure what a plant needs? Ask for advice grounded in its species and its own care history.",
  },
];
