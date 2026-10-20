// The boundary's own logic, without a renderer: this jest setup is
// deliberately React-Native-free (see jest.config.js), so the native and UI
// modules are stood in for by name and the class is driven directly.
jest.mock('react-native', () => ({
  Platform: { OS: 'ios' },
  StyleSheet: { create: (s: unknown) => s, hairlineWidth: 1 },
  View: 'View',
}));
jest.mock('react-native-paper', () => ({ Button: 'Button', Text: 'Text' }));
jest.mock('../theme/ThemeProvider', () => ({ useAppTheme: jest.fn() }));
jest.mock('../support', () => ({
  APP_VERSION: '1.1.3',
  SUPPORT_EMAIL: 'support@plantadvocate.ai',
  openExternal: jest.fn(),
}));

import React from 'react';
import ErrorBoundary, { guarded } from './ErrorBoundary';

type Element = React.ReactElement<Record<string, unknown>>;

function boundary(props: Partial<React.ComponentProps<typeof ErrorBoundary>> = {}) {
  const child = React.createElement('Screen');
  const instance = new ErrorBoundary({ where: 'Census', children: child, ...props });
  instance.setState = jest.fn() as never;
  return { instance, child };
}

test('a render error flips the boundary to its card', () => {
  const err = new TypeError('Cannot convert undefined or null to object');
  expect(ErrorBoundary.getDerivedStateFromError(err)).toEqual({ error: err, failed: true, retrying: false });
});

test('until something fails, the boundary renders the screen untouched', () => {
  const { instance, child } = boundary();
  expect(instance.render()).toBe(child);
});

test('once failed, it renders the card in the screen\'s place, naming where', () => {
  const { instance } = boundary();
  const err = new Error('boom');
  instance.state = { ...instance.state, ...ErrorBoundary.getDerivedStateFromError(err) };
  const card = instance.render() as Element;
  expect((card.type as { name?: string }).name).toBe('ErrorCard');
  expect(card.props.where).toBe('Census');
  expect(card.props.error).toBe(err);
  expect(typeof card.props.onRetry).toBe('function');
  expect(card.props.retrying).toBe(false);
});

/** A failed boundary whose setState really updates its state, recording each
 *  update in order alongside whatever else the test logs. */
function failedBoundary(onReset: () => void | Promise<unknown>) {
  const log: unknown[] = [];
  const { instance } = boundary({ onReset });
  instance.state = { ...instance.state, ...ErrorBoundary.getDerivedStateFromError(new Error('boom')) };
  (instance.setState as unknown as jest.Mock).mockImplementation((patch: object) => {
    log.push(patch);
    instance.state = { ...instance.state, ...patch };
  });
  return { instance, log };
}

test('Try again refreshes the data first, then shows the screen again', async () => {
  const { instance, log } = failedBoundary(() => { log.push('refresh'); });
  await instance['retry']();
  expect(log).toEqual([
    { retrying: true },
    'refresh',
    { error: null, failed: false, retrying: false },
  ]);
});

test('the screen is redrawn only once the refresh has come back, busy meanwhile', async () => {
  let done!: () => void;
  const refreshed = new Promise<void>((resolve) => { done = resolve; });
  const { instance } = failedBoundary(() => refreshed);

  const retry = instance['retry']();
  expect(instance.state).toMatchObject({ failed: true, retrying: true });
  expect((instance.render() as Element).props.retrying).toBe(true);
  // A second tap while it runs starts nothing new.
  await instance['retry']();
  expect(instance.state.failed).toBe(true);

  done();
  await retry;
  expect(instance.state).toMatchObject({ failed: false, retrying: false });
});

test('Try again still redraws, and never throws, when refreshing the data fails', async () => {
  // A throw out of a button handler is an uncaught error: fatal in a
  // release build, which is the crash the boundary exists to prevent.
  const thrown = failedBoundary(() => { throw new Error('cache gone'); });
  await expect(thrown.instance['retry']()).resolves.toBeUndefined();
  expect(thrown.instance.state.failed).toBe(false);

  const rejected = failedBoundary(() => Promise.reject(new Error('offline')));
  await expect(rejected.instance['retry']()).resolves.toBeUndefined();
  expect(rejected.instance.state.failed).toBe(false);
});

test('logging a caught error never throws, in dev or out of it', () => {
  const { instance } = boundary();
  expect(() => instance.componentDidCatch(new Error('x'), { componentStack: '' })).not.toThrow();
});

test('guarded wraps a screen in a boundary named for it, passing its props through', () => {
  const Screen = (props: { route: string }) => React.createElement('Screen', props);
  const onReset = () => {};
  const Guarded = guarded(Screen, 'Plant', onReset) as (p: { route: string }) => Element;

  const out = Guarded({ route: 'PlantDetail' });
  expect(out.type).toBe(ErrorBoundary);
  expect(out.props.where).toBe('Plant');
  expect(out.props.onReset).toBe(onReset);
  const inner = out.props.children as Element;
  expect(inner.type).toBe(Screen);
  expect(inner.props.route).toBe('PlantDetail');
  expect((Guarded as unknown as { displayName: string }).displayName).toBe('Guarded(Plant)');
});
