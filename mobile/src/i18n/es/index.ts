// NEEDS NATIVE REVIEW. Every file in this folder is a careful first-pass
// Spanish (Mexican / U.S. neutral, tú form) written by Claude and not yet read
// by a native speaker. Until someone has, ES_META.needsReview stays true.
import type { Strings } from '../types';
import type en from '../en';
import common from './common';
import nav from './nav';
import auth from './auth';
import onboarding from './onboarding';
import consent from './consent';
import settings from './settings';
import home from './home';
import weather from './weather';
import season from './season';
import almanac from './almanac';
import notifications from './notifications';
import land from './land';
import zones from './zones';
import plants from './plants';
import care from './care';
import species from './species';
import census from './census';
import capture from './capture';
import areas from './areas';
import units from './units';
import controls from './controls';
import howWeKnow from './howWeKnow';

export const ES_META = {
  needsReview: true,
  register: 'tú',
  variety: 'Mexican / U.S. neutral',
  firstPass: '2026-11-24',
} as const;

const es: Strings<typeof en> = {
  common,
  nav,
  auth,
  onboarding,
  consent,
  settings,
  home,
  weather,
  season,
  almanac,
  notifications,
  land,
  zones,
  plants,
  care,
  species,
  census,
  capture,
  areas,
  units,
  controls,
  howWeKnow,
};

export default es;
