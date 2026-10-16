// What a screen says when its first load failed. A failed request used to
// leave the detail screens on a spinner forever (`isLoading || !data` stays
// true once the query errors) and the catalog tabs on text with nothing to
// tap; a cold server or a dropped signal then looked like a broken app. Each
// screen now says it couldn't load, names no backend, and offers to try again.

export const LOAD_FAILED = {
  emoji: '🌧️',
  body: 'PlantAdvocate couldn’t reach the server just now. Check your connection and try again.',
  action: 'Try again',
} as const;

/** The heading for a screen about one thing: "Couldn’t load this plant". */
export function loadFailedTitle(what: string): string {
  return `Couldn’t load ${what}`;
}
