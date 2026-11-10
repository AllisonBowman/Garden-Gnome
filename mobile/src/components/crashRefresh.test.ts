// "Try again" on a crashed screen, against a real query cache. A mounted
// screen is an observer subscribed to its query; the screen that crashed has
// already unmounted under its boundary's card, so its queries have none.
import { QueryClient, QueryObserver } from '@tanstack/query-core';
import { refreshAfterCrash } from './crashRefresh';

const PLANTS = [{ id: 1, nickname: 'Ferny' }];

function setup() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  let plantsAsked = 0;
  let plantsAnswer: () => Promise<unknown> = async () => PLANTS;
  // The Plants tab, still mounted in its own tab, showing good content.
  const plantsTab = new QueryObserver(queryClient, {
    queryKey: ['plants'],
    queryFn: () => { plantsAsked += 1; return plantsAnswer(); },
    staleTime: 30_000,
  });
  const unsubscribe = plantsTab.subscribe(() => {});
  // The species page that crashed: its answer is still cached, but the
  // screen reading it is gone.
  queryClient.setQueryData(['species', 5], { id: 5, common_name: null });
  return {
    queryClient,
    plantsTab,
    unsubscribe,
    plantsAsked: () => plantsAsked,
    answerPlants: (f: () => Promise<unknown>) => { plantsAnswer = f; },
  };
}

test('the crashed screen’s own answers are dropped, to be fetched fresh', async () => {
  const t = setup();
  await t.plantsTab.refetch(); // its first load
  await refreshAfterCrash(t.queryClient);
  expect(t.queryClient.getQueryData(['species', 5])).toBeUndefined();
  expect(t.queryClient.getQueryState(['species', 5])?.status).toBe('pending');
  t.unsubscribe();
});

test('another tab keeps what it is showing, and is asked for again', async () => {
  const t = setup();
  await t.plantsTab.refetch(); // its first load
  const before = t.plantsAsked();
  const refresh = refreshAfterCrash(t.queryClient);
  // Not sent back to a spinner while it refreshes.
  expect(t.plantsTab.getCurrentResult().data).toEqual(PLANTS);
  expect(t.plantsTab.getCurrentResult().isLoading).toBe(false);
  await refresh;
  expect(t.plantsAsked()).toBe(before + 1);
  expect(t.queryClient.getQueryData(['plants'])).toEqual(PLANTS);
  t.unsubscribe();
});

test('with no signal, the other tab’s content survives the failed refresh', async () => {
  const t = setup();
  await t.plantsTab.refetch(); // its first load
  t.answerPlants(() => Promise.reject(new Error('Network Error')));
  await refreshAfterCrash(t.queryClient);
  const result = t.plantsTab.getCurrentResult();
  expect(result.isError).toBe(true);
  expect(result.data).toEqual(PLANTS);
  t.unsubscribe();
});

test('a refresh that hangs doesn’t hold the card on screen', async () => {
  const t = setup();
  await t.plantsTab.refetch(); // its first load
  t.answerPlants(() => new Promise(() => {}));
  const started = Date.now();
  await refreshAfterCrash(t.queryClient, 30);
  expect(Date.now() - started).toBeLessThan(2_000);
  t.unsubscribe();
  t.queryClient.clear();
});
