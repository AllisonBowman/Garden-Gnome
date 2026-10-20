import { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import {
  LOAD_FAILED, REFRESH_FAILED, loadFailedAdvice, loadFailedBody, loadFailedTitle,
  loadFailure, loadView,
} from './loadFailed';
import { SessionRenewalDeferred } from '../auth/refreshPolicy';

// Read the screens: the rule is about how each one handles a failed query,
// which a unit test of the copy alone cannot see. Declared locally rather
// than pulling in @types/node, which conflicts with React Native's typings.
declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');
const read = (rel: string): string => fs.readFileSync(path.join(__dirname, rel), 'utf8');

const config = { headers: {} } as InternalAxiosRequestConfig;
const answered = (status: number) => new AxiosError(
  `Request failed with status code ${status}`, 'ERR_BAD_RESPONSE', config, null,
  { status, data: {}, statusText: '', headers: {}, config } as AxiosResponse,
);
const offline = () => new AxiosError('Network Error', AxiosError.ERR_NETWORK, config);
const timedOut = () => new AxiosError('timeout of 15000ms exceeded', AxiosError.ECONNABORTED, config);

// --- the copy -----------------------------------------------------------------

test('the copy names no backend and offers a way out', () => {
  for (const line of [LOAD_FAILED.body, LOAD_FAILED.gone, LOAD_FAILED.answered,
    LOAD_FAILED.other, REFRESH_FAILED.line]) {
    expect(line).not.toMatch(/backend|api|url|server is running|\d{3}/i);
  }
  expect(LOAD_FAILED.action).toBe('Try again');
  expect(REFRESH_FAILED.action).toBe('Try again');
  expect(loadFailedTitle('this plant')).toBe('Couldn’t load this plant');
});

// --- the reason fits the failure ---------------------------------------------
// "Check your connection" sends someone off to fix their signal. It is the
// right advice only when the server was never reached.

test('a request that never reached the server is told to check the connection', () => {
  expect(loadFailure(offline())).toBe('unreached');
  expect(loadFailure(timedOut())).toBe('unreached');
  expect(loadFailure(new SessionRenewalDeferred(offline()))).toBe('unreached');
  expect(loadFailedBody(offline())).toBe(LOAD_FAILED.body);
  expect(loadFailedBody(offline())).toMatch(/Check your connection/);
  expect(loadFailedAdvice(offline())).toBe('Check your connection and try again.');
});

test('a server that answered is not blamed on the connection', () => {
  for (const status of [500, 502, 503, 422, 401]) {
    expect(loadFailure(answered(status))).toBe('answered');
    expect(loadFailedBody(answered(status))).not.toMatch(/connection/i);
    expect(loadFailedAdvice(answered(status))).not.toMatch(/connection/i);
  }
  expect(loadFailedBody(answered(500))).toBe(LOAD_FAILED.answered);
});

test('one thing that is gone says it may have been removed; a list never does', () => {
  expect(loadFailure(answered(404))).toBe('gone');
  expect(loadFailedBody(answered(404))).toBe(LOAD_FAILED.gone);
  expect(loadFailedBody(answered(404), 'list')).toBe(LOAD_FAILED.answered);
  expect(loadFailedAdvice(answered(404))).toBe(LOAD_FAILED.answered);
});

test('a failure that isn’t the network at all says neither', () => {
  const bug = new TypeError("Cannot read properties of undefined (reading 'map')");
  expect(loadFailure(bug)).toBe('other');
  expect(loadFailedBody(bug)).not.toMatch(/connection|server/i);
  expect(loadFailedAdvice(bug)).not.toMatch(/connection|server/i);
});

// --- what to draw ---------------------------------------------------------------
// The app refreshes on its own when it comes back to the foreground, often
// with no signal. A refresh that fails must not take away what is on screen.

test('content that loaded stays on screen when a later refresh fails', () => {
  expect(loadView(true, true)).toBe('shown');
  expect(loadView(true, false)).toBe('shown');
});

test('the error takes the screen only when there is nothing to show', () => {
  expect(loadView(false, true)).toBe('failed');
  expect(loadView(false, false)).toBe('loading');
});

// --- the screens follow the rules ---------------------------------------------

const SCREENS = [
  '../screens/PlantDetailScreen.tsx',
  '../screens/SpeciesDetailScreen.tsx',
  '../screens/GrowingAreaDetailScreen.tsx',
  '../screens/AlmanacScreen.tsx',
  '../screens/SpeciesScreen.tsx',
];

test.each(SCREENS)('%s shows a retry when its first load fails', (rel) => {
  const src = read(rel);
  expect(src).toMatch(/<EmptyState[\s\S]*?LOAD_FAILED\.action[\s\S]*?onAction=\{\(\) => refetch\w*\(\)\}/);
});

test.each(SCREENS)('%s says why its load failed, from the error', (rel) => {
  const src = read(rel);
  expect(src).toMatch(/body=\{loadFailedBody\(/);
  expect(src).not.toMatch(/body=\{LOAD_FAILED\.body\}/);
});

test.each([...SCREENS, '../screens/CensusScreen.tsx'])(
  '%s keeps what it loaded when a refresh fails, and says so',
  (rel) => {
    const src = read(rel);
    // `isLoading || !data` spins forever once the query errors;
    // `isError || !data` swaps loaded content for the error card.
    expect(src).not.toMatch(/if \(isLoading \|\| !\w+\)/);
    expect(src).not.toMatch(/if \(isError \|\| !\w+\)/);
    expect(src).toMatch(/loadView\(/);
    expect(src).toMatch(/<RefreshFailed\b/);
  },
);

const LOAD_ERROR_SCREENS = [
  '../screens/PlantsScreen.tsx',
  '../screens/GrowingAreasScreen.tsx',
  '../screens/CensusScreen.tsx',
  '../screens/AddPlantScreen.tsx',
  '../screens/CaptureGardenScreen.tsx',
];

test.each(LOAD_ERROR_SCREENS)('%s lets the error choose the advice', (rel) => {
  const blocks = read(rel).match(/<LoadError[\s\S]*?\/>/g) ?? [];
  expect(blocks.length).toBeGreaterThan(0);
  for (const block of blocks) {
    expect(block).toMatch(/error=\{/);
    expect(block).not.toMatch(/connection/i);
  }
});
