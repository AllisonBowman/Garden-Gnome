import { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import {
  isRetryableError, retryOnceIfPassing, serverAnswered, serverMessage,
} from './errorMessage';
import { SessionRenewalDeferred } from '../auth/refreshPolicy';

const config = { headers: {} } as InternalAxiosRequestConfig;

function answered(status: number, data: unknown = {}): AxiosError {
  const response = { status, data, statusText: '', headers: {}, config } as AxiosResponse;
  return new AxiosError(`Request failed with status code ${status}`, 'ERR_BAD_RESPONSE', config, null, response);
}
const timedOut = () => new AxiosError('timeout of 15000ms exceeded', AxiosError.ECONNABORTED, config);
const offline = () => new AxiosError('Network Error', AxiosError.ERR_NETWORK, config);

// --- one automatic retry, only where it can help -----------------------------

test('a dropped connection or a timeout is worth one more try', () => {
  expect(isRetryableError(offline())).toBe(true);
  expect(isRetryableError(timedOut())).toBe(true);
});

test.each([408, 429, 500, 502, 503, 504])('a %i is worth one more try', (status) => {
  // 502-504 are what a scaled-to-zero machine answers while it boots.
  expect(isRetryableError(answered(status))).toBe(true);
});

test.each([400, 401, 403, 404, 409, 422])('a %i will answer the same again, so no retry', (status) => {
  expect(isRetryableError(answered(status))).toBe(false);
});

test('a session that could not be renewed just now is worth one more try', () => {
  expect(isRetryableError(new SessionRenewalDeferred(timedOut()))).toBe(true);
});

test('the query retry rule allows exactly one retry, and only for a passing failure', () => {
  // The first request after a quiet spell meets a machine still waking up.
  expect(retryOnceIfPassing(0, timedOut())).toBe(true);
  expect(retryOnceIfPassing(0, answered(502))).toBe(true);
  // ...but a second failure goes to the screen's error card, not a third try.
  expect(retryOnceIfPassing(1, timedOut())).toBe(false);
  // ...and an answer that will repeat goes there straight away.
  expect(retryOnceIfPassing(0, answered(404))).toBe(false);
});

test('a bug in our own code is not retried', () => {
  expect(isRetryableError(new TypeError("Cannot read properties of undefined (reading 'map')"))).toBe(false);
  expect(isRetryableError(undefined)).toBe(false);
});

// --- what a caretaker reads ---------------------------------------------------

test('a user-presentable server detail is shown as is', () => {
  expect(serverMessage(answered(503, { detail: 'Photo check-ups are resting.' }), 'fallback'))
    .toBe('Photo check-ups are resting.');
});

test('anything else gets the caller\'s own words', () => {
  expect(serverMessage(offline(), 'fallback')).toBe('fallback');
  // Pydantic's 422 detail is a list of field errors, not a sentence.
  expect(serverMessage(answered(422, { detail: [{ loc: ['body'], msg: 'too long' }] }), 'fallback'))
    .toBe('fallback');
  expect(serverMessage(new SessionRenewalDeferred(offline()), 'fallback')).toBe('fallback');
});

test('a refusal is told apart from an unreachable server', () => {
  expect(serverAnswered(answered(422))).toBe(true);
  expect(serverAnswered(offline())).toBe(false);
  expect(serverAnswered(timedOut())).toBe(false);
  expect(serverAnswered(new Error('x'))).toBe(false);
});
