// First-run onboarding, in the order it is read. Pure data, so the claims
// in it can be checked against the screens they point to (slides.test.ts).
//
// Short and plain: what the app is, then the land, then what the land shows,
// then the plants. The land comes before the plants because Home is a report
// on the land: with no land yet, Home shows one "Add your land" card, which
// is where the last slide's button leads.

import { t } from '../i18n';

export interface Slide {
  emoji: string;
  title: string;
  body: string;
}

/** The Spaces screen's title. App.tsx titles that screen from this constant;
 *  the slides no longer mention it, since there are no tabs any more. */
export const GROWING_AREAS_TAB = t('onboarding.growingAreasTab');

/** Where the last slide's button leads, and what it says. Home, because the
 *  app is land-first: a new account's Home starts with "Add your land". */
export const FINISH: { route: 'Home'; label: string } = {
  route: 'Home',
  label: t('onboarding.getStarted'),
};

export const SLIDES: Slide[] = [
  {
    emoji: '🌱',
    title: t('onboarding.welcomeTitle'),
    body: t('onboarding.welcomeBody'),
  },
  {
    emoji: '📍',
    title: t('onboarding.landTitle'),
    // The public maps are asked only about United States pins
    // (garden-gnome/app/services/coverage.py); setup says the same.
    body: t('onboarding.landBody'),
  },
  {
    emoji: '🗺️',
    title: t('onboarding.seeTitle'),
    body: t('onboarding.seeBody'),
  },
  {
    emoji: '💧',
    title: t('onboarding.plantsTitle'),
    // Advice: the plant page's "Get care advice" is always offered and is
    // rule-based (care/resultLabels.ts). Photo check-ups and free-text
    // questions are switched off, so they are not mentioned.
    body: t('onboarding.plantsBody'),
  },
];
