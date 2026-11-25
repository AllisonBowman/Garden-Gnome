// The "How we know" sections for each screen: everything a screen used to
// show as confidence chips, "Why and data source" disclosures, source and
// credit lines, method notes and slow-service wording, gathered in one
// place. Pure, so it can be pinned that nothing the faces dropped is lost.
import type {
  Explained, MapLayer, SeasonEvent, SeasonEventSummary, SiteProfile, SiteValue, Source, VitalCard, Vitals,
} from '../types/site';
import type { WeekItem } from '../home/week';
import { drawnZones, groupValues, wholeLotValues } from '../land/profileRows';
import { HowWeKnowSection, section } from './store';
import { getTempUnit } from '../units/temperature';
import { t } from '../i18n';
import { sourceText } from '../components/explainedText';

/** What "est." and "Checking" mean, said once at the foot of every sheet,
 *  plus the °F note when temperatures are shown in °C. */
export function marksSection(): HowWeKnowSection {
  return section('marks', t('howWeKnow.sections.marks'), [
    t('howWeKnow.estBody'),
    t('howWeKnow.checkingBody'),
    getTempUnit() === 'C' ? t('howWeKnow.unitsNote') : null,
  ]);
}

/** A season task's reason and sources as an explained value, so the sheet
 *  shows it the same way as every other. */
export function taskExplained(text: string, reason: string, sources: Source[]): Explained {
  return {
    display: text,
    confidence: 'good_estimate',
    confidence_label: 'Good estimate',
    reason,
    sources,
    provenance: 'modelled',
  };
}

const explainedCards = (cards: VitalCard[]) => cards
  .filter((c): c is VitalCard & { explained: Explained } => c.explained != null)
  .map((c) => ({ title: c.title, explained: { ...c.explained, display: c.value_text } }));

export interface HomeSheetInput {
  vitals: Vitals | null | undefined;
  /** Home's almanac line came from the server's headline (and its full text). */
  headline: { fromServer: boolean; full: string | null };
  weatherCards: VitalCard[];
  /** The land values Home glances at, with their full explanation. */
  land: { title: string; explained: Explained }[];
  /** "Still reading your land…" and other slow-service lines. */
  progress: string | null;
  week: WeekItem[];
  seasonAhead: SeasonEventSummary[];
  /** The older weather route's credit, when Home read it. */
  legacyCredit: string | null;
  forecastWhen: string | null;
}

export function homeSections(i: HomeSheetInput): HowWeKnowSection[] {
  const v = i.vitals;
  const tasks = i.week.filter((w): w is Extract<WeekItem, { kind: 'season' }> => w.kind === 'season');
  return [
    section('almanac', t('howWeKnow.sections.almanac'), [
      t('howWeKnow.weekMethod'),
      i.headline.fromServer && i.headline.full
        ? t('howWeKnow.headlineFrom', { text: i.headline.full })
        : t('howWeKnow.headlineLocal'),
    ]),
    section('weather', t('howWeKnow.sections.weather'), [
      v?.forecast && i.forecastWhen
        ? t('howWeKnow.forecastFetched', { name: v.forecast.provider_name, when: i.forecastWhen })
        : v?.forecast ? t('season.credit.forecastBy', { name: v.forecast.provider_name }) : null,
      i.legacyCredit,
      ...i.weatherCards.filter((c) => !c.explained).map((c) => [c.title, c.value_text, c.detail].filter(Boolean).join('. ')),
    ], explainedCards(i.weatherCards)),
    section('land', t('howWeKnow.sections.land'), [i.progress], i.land),
    section('tasks', t('howWeKnow.sections.tasks'), [],
      tasks.map((w) => ({ explained: taskExplained(w.text, w.reason, w.sources) }))),
    section('season', t('howWeKnow.sections.season'), [],
      i.seasonAhead.map((e) => ({ title: e.title, explained: e.explained }))),
    section('notes', t('howWeKnow.sections.notes'), v?.notes ?? []),
    marksSection(),
  ];
}

export function landSections(input: {
  profile: SiteProfile; progress: string | null; layer: MapLayer | null;
}): HowWeKnowSection[] {
  const { profile } = input;
  const item = (v: SiteValue) => ({ title: v.title, explained: v as Explained });
  const lot = groupValues(wholeLotValues(profile));
  return [
    section('land', t('howWeKnow.sections.land'), [input.progress], lot.flatMap((s) => s.values.map(item))),
    section('map', t('howWeKnow.sections.map'), input.layer?.notes ?? [],
      input.layer ? [{ title: input.layer.title, explained: input.layer.explained }] : []),
    ...drawnZones(profile).map((z) => section(`zone-${z.zone_id}`, z.name, [], z.values.map(item))),
    section('notes', t('howWeKnow.sections.notes'), profile.notes),
    marksSection(),
  ];
}

export function seasonSections(input: {
  events: SeasonEvent[]; forecastCredit: string | null; notes?: string[];
}): HowWeKnowSection[] {
  return [
    section('weather', t('howWeKnow.sections.weather'), [input.forecastCredit]),
    ...input.events.map((e) => section(`event-${e.event_key}`, e.title, [],
      [
        { title: e.title, explained: e.explained },
        ...e.tasks.map((task) => ({ explained: taskExplained(task.text, task.reason, task.sources) })),
      ])),
    section('notes', t('howWeKnow.sections.notes'), input.notes ?? []),
    marksSection(),
  ];
}

export function zoneSections(input: { name: string; values: (Explained & { title?: string })[] }): HowWeKnowSection[] {
  return [
    section('zone', input.name, [], input.values.map((v) => ({ title: v.title, explained: v }))),
    marksSection(),
  ];
}

/** Sources as one-line text (used by tests to check nothing is lost). */
export function allSourceLines(sections: HowWeKnowSection[]): string[] {
  return sections.flatMap((s) => s.items.flatMap((i) => i.explained.sources.map(sourceText)));
}
