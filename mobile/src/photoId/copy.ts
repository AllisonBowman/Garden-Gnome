// What the photo "what is this plant?" feature says.
//
// It is a suggestion, never an identification. On iOS the phone reduces the
// photo to a handful of coarse labels before its language model sees it (a
// Pothos and a Heartleaf Philodendron are the same input), and the "best"
// tier is a string match between that model's answer and catalog names. So
// every line here asks the gardener to confirm, nothing is chosen for them,
// and no line claims the phone knows. Kept apart from identify.ts, which
// loads the native module, so jest can pin the wording.
import { t } from '../i18n';


/** Above the suggested species, when the catalog has matches. */
export const PHOTO_SUGGESTIONS_LABEL = t('common.photoId.suggestions');

/** Kept for the report email: what the gardener was shown. */
export const SUGGESTED_OBSERVATION = t('common.photoId.suggested');

export const UNAVAILABLE_OBSERVATION = t('common.photoId.unavailable');

export const UNREADABLE_OBSERVATION = t('common.photoId.unreadable');

export const NO_NAME_OBSERVATION = t('common.photoId.noName');

/** The phone named something the catalog doesn't hold. */
export function notInCatalogObservation(suggested: string): string {
  return t('common.photoId.notInCatalog', { suggested });
}
