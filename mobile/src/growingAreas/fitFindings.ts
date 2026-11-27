// How a fit finding is introduced on screen: which axis it is about, and
// whose word it rests on. Pure, so every surface that shows findings — the
// area's two cards, the Almanac, Add Plant — labels them the same way.
//
// What this module never does is word a verdict. The sentence a person reads
// is the server's (`FitFinding.sentence`), shown as-is, borrowed label and
// all: a second copy of the fit rules here would sooner or later disagree
// with the first, and the gardener would see both.

import type { Candidate, FitAxis, FitFinding, SpeciesFit } from '../api/growingAreas';
import { goalPhrase } from './realEstate';
import { t } from '../i18n';

export const AXIS_LABEL: Record<FitAxis, string> = {
  indoor_outdoor: t('areas.axis.indoor_outdoor'),
  sun: t('areas.axis.sun'),
  soil: t('areas.axis.soil'),
  footprint: t('areas.axis.footprint'),
  upkeep: t('areas.axis.upkeep'),
  goal: t('areas.axis.goal'),
};

const capitalize = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

/** What a finding is about: its axis, or for a goal, the goal itself —
 *  "Something to eat" says more than "What it’s for" when there are two. */
export function findingLabel(finding: FitFinding): string {
  if (finding.goal) return capitalize(goalPhrase(finding.goal));
  // An axis a newer server added: still readable, never a raw token.
  return AXIS_LABEL[finding.axis] ?? capitalize(String(finding.axis).replace(/_/g, ' '));
}

/** The line over a finding's sentence: the axis, then whose word it is —
 *  "Sun · NC State Extension". No authority means nothing about this
 *  species was cited for it, and the line says only the axis rather than
 *  inventing a "sources" for it. */
export function findingHeading(finding: FitFinding): string {
  const who = finding.authorities ?? [];
  return who.length > 0
    ? `${findingLabel(finding)} · ${who.join(', ')}`
    : findingLabel(finding);
}

/** "a", "a and b", "a, b and c" ("a, b y c" in Spanish). */
export function joinAnd(items: string[]): string {
  if (items.length <= 1) return items.join('');
  return t('areas.listAnd', { head: items.slice(0, -1).join(', '), last: items[items.length - 1] });
}

/** The labels of the findings with one verdict, once each, lower-cased for
 *  the middle of a sentence. */
function labelsWith(findings: FitFinding[], verdict: FitFinding['verdict']): string[] {
  return [...new Set(findings
    .filter((f) => f.verdict === verdict)
    .map((f) => findingLabel(f).toLowerCase()))];
}

/** What a candidate was confirmed on, as one line under its name in the
 *  Almanac: "Confirmed here: sun, soil and size." Only `fits` count — an
 *  unknown is never a reason — so a list with none of them says nothing. */
export function confirmedLine(findings: FitFinding[]): string | null {
  const labels = labelsWith(findings, 'fits');
  return labels.length > 0 ? t('areas.confirmedHere', { list: joinAnd(labels) }) : null;
}

/** The findings Add Plant lists one by one: the misfits, and only those. */
export function misfitsOf(findings: FitFinding[]): FitFinding[] {
  return findings.filter((f) => f.verdict === 'misfits');
}

/** The confirmed findings, each of which a screen may show with its source. */
export function fitsOf(findings: FitFinding[]): FitFinding[] {
  return findings.filter((f) => f.verdict === 'fits');
}

/** What nobody could judge here, as one line under what was: "Not known
 *  here: soil and something to eat." An unknown is never shown as a row of
 *  its own — it has no source to name and is no reason for or against — but
 *  it is not hidden either. Null when every axis was answered. */
export function notKnownLine(findings: FitFinding[]): string | null {
  const unknown = labelsWith(findings, 'unknown');
  return unknown.length > 0 ? t('areas.notKnownHere', { list: joinAnd(unknown) }) : null;
}

/** The heading over an Add Plant answer that has misfits in it. */
export function misfitIntro(areaName: string): string {
  return t('areas.misfitIntro', { area: areaName });
}

/** What Add Plant says when the chosen spot has nothing on record against
 *  the species. Two different situations, never one sentence: something was
 *  confirmed and nothing contradicts it — or nothing was judged at all,
 *  which is an absence of evidence and not a recommendation. Whichever it
 *  is rests on the server's `candidate`, not on a rule re-run here. Null
 *  when there are misfits: those are listed one by one instead. */
export function speciesFitNote(fit: SpeciesFit, areaName: string): string | null {
  if (misfitsOf(fit.findings).length > 0) return null;
  if (!fit.candidate) {
    return t('areas.cantJudge', { area: areaName });
  }
  const confirmed = labelsWith(fit.findings, 'fits');
  const unknown = labelsWith(fit.findings, 'unknown');
  const said = t('areas.nothingAgainst', { area: areaName, list: joinAnd(confirmed) });
  return unknown.length > 0
    ? t('areas.twoSentences', { first: said, second: t('areas.notKnown', { list: joinAnd(unknown) }) })
    : said;
}

/** How a plant is named on the "needs addressing" card: its nickname, and
 *  the species beside it only where the nickname doesn't already say it. A
 *  plant saved without a nickname is named by the server from its species —
 *  "Hosta", or "Hosta — south fence" (`plants._default_nickname`) — and the
 *  card read "Hosta  Hosta". */
export function plantTitle(
  nickname: string | null | undefined, commonName: string,
): { name: string; species: string | null } {
  const name = (nickname ?? '').trim();
  if (!name) return { name: commonName, species: null };
  const said = name.toLowerCase();
  const common = commonName.trim().toLowerCase();
  const named = said === common || said.startsWith(`${common} — `);
  return { name, species: named ? null : commonName };
}

/** Shown in place of a fit answer the app could not fetch. A failed request
 *  has checked nothing, so it must never fall through to an empty list's
 *  all-clear wording ("nothing here contradicts the space"). */
export const CHECK_FAILED = t('areas.checkFailed');

/** The caution a candidate carries, or null. The server writes the line
 *  ("Toxic to pets and people if eaten.") and the screens show it as-is on
 *  every row that lists the candidate — never dropped for space, because a
 *  recommendation that leaves out a hazard reads as an all-clear. A blank
 *  line is no line; a server too old to send one sends nothing. */
export function candidateHazard(candidate: Pick<Candidate, 'hazard'>): string | null {
  const line = candidate.hazard?.trim();
  return line ? line : null;
}
