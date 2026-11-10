// What the photo "what is this plant?" feature says.
//
// It is a suggestion, never an identification. On iOS the phone reduces the
// photo to a handful of coarse labels before its language model sees it (a
// Pothos and a Heartleaf Philodendron are the same input), and the "best"
// tier is a string match between that model's answer and catalog names. So
// every line here asks the gardener to confirm, nothing is chosen for them,
// and no line claims the phone knows. Kept apart from identify.ts, which
// loads the native module, so jest can pin the wording.

/** Above the suggested species, when the catalog has matches. */
export const PHOTO_SUGGESTIONS_LABEL =
  'Suggested from the photo. Tap the one that matches, and check it’s right before you save.';

/** Kept for the report email: what the gardener was shown. */
export const SUGGESTED_OBSERVATION =
  'Suggested from the photo — confirm it’s right, or pick another below.';

export const UNAVAILABLE_OBSERVATION =
  'Your phone can’t suggest plants from photos. Search for yours below.';

export const UNREADABLE_OBSERVATION =
  'Couldn’t read the photo this time. Search for your plant below.';

export const NO_NAME_OBSERVATION =
  'Your phone couldn’t suggest a name for this one. Search for it below.';

/** The phone named something the catalog doesn't hold. */
export function notInCatalogObservation(suggested: string): string {
  return `Your phone suggested “${suggested}”, but that isn’t in the catalog yet. `
    + 'Search below for the closest match.';
}
