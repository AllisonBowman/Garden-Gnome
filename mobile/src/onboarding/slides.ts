// First-run onboarding, in the order it is read. Pure data, so the claims
// in it can be checked against the screens they point to (slides.test.ts).
//
// Short and plain, around what Home now is: an almanac for the week, up to
// three things to do, the controls up front, then the land, then where the
// sources went (the How we know sheet). With no land yet, Home's almanac
// offers "Add your land", which is where the last slide's button leads.

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
    emoji: '🗓️',
    title: t('onboarding.almanacTitle'),
    // Home's almanac line (home/almanac.ts): date, week of the season, and
    // the one thing that matters.
    body: t('onboarding.almanacBody'),
  },
  {
    emoji: '✅',
    title: t('onboarding.tasksTitle'),
    // Home lists at most HOME_TASKS (home/homeTasks.ts) with Done and Skip.
    body: t('onboarding.tasksBody'),
  },
  {
    emoji: '🎛️',
    title: t('onboarding.controlsTitle'),
    // The Controls row (components/ControlsRow.tsx), each tile's state in words.
    body: t('onboarding.controlsBody'),
  },
  {
    emoji: '📍',
    title: t('onboarding.landTitle'),
    // The public maps are asked only about United States pins
    // (garden-gnome/app/services/coverage.py); setup says the same.
    body: t('onboarding.landBody'),
  },
  {
    emoji: '🔎',
    title: t('onboarding.howTitle'),
    // The How we know sheet (screens/HowWeKnowScreen.tsx).
    body: t('onboarding.howBody'),
  },
];
