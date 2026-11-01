// Saving a walked garden in pieces the server will take.
//
// POST /plants/bulk takes at most 200 plants (PlantBulkCreate in
// garden-gnome/app/models/schemas.py) and is all-or-nothing within one call.
// A long walk can name more than that, and sending them all at once got a 422
// the screen reported as "couldn't reach the server": the garden could never
// be saved, and the message pointed at the network.
//
// So the drafts go in order, in batches of at most the limit, each batch
// still all-or-nothing. The first batch that fails stops the run: what landed
// is reported as saved and leaves the screen, and everything from that batch
// on stays on screen to try again. Nothing is half-saved and nothing is lost.
//
// Pure on purpose (no React Native imports) so jest can pin it.
import axios from 'axios';
import { isRetryableError, serverMessage } from '../api/errorMessage';

/** The most plants one POST /plants/bulk accepts. */
export const BULK_LIMIT = 200;

export function chunk<T>(items: T[], size: number): T[][] {
  if (!Number.isInteger(size) || size < 1) throw new Error(`chunk size must be a positive integer, got ${size}`);
  const out: T[][] = [];
  for (let i = 0; i < items.length; i += size) out.push(items.slice(i, i + size));
  return out;
}

export interface ChunkedSave<T> {
  /** Items whose batch the server accepted. */
  saved: T[];
  /** Items not saved: the batch that failed and every one after it. */
  unsaved: T[];
  /** Why the run stopped, or null when everything landed. */
  error: unknown;
}

export async function saveInChunks<T>(
  items: T[],
  saveBatch: (batch: T[]) => Promise<unknown>,
  size: number = BULK_LIMIT,
): Promise<ChunkedSave<T>> {
  const batches = chunk(items, size);
  const saved: T[] = [];
  for (let i = 0; i < batches.length; i++) {
    try {
      await saveBatch(batches[i]);
    } catch (error) {
      return { saved, unsaved: batches.slice(i).flat(), error };
    }
    saved.push(...batches[i]);
  }
  return { saved, unsaved: [], error: null };
}

// ── What the caretaker is told when a batch didn't land ─────────────────────
// The reason, in the caretaker's words, and advice that can work. The
// server's own `detail` is shown only for a 503, the one status whose detail
// is written for an end user (api/errorMessage.ts): a 400's "species_id
// does not exist" is a field name, and "try again in a moment" can't fix it.

function sentence(text: string): string {
  return /[.!?…]$/.test(text) ? text : `${text}.`;
}

export interface SaveFailureAlert {
  title: string;
  body: string;
}

export function saveFailureAlert(
  error: unknown,
  savedCount: number,
  unsavedCount: number,
): SaveFailureAlert {
  const title = savedCount === 0
    ? 'Nothing was saved'
    : `Saved ${savedCount} of ${savedCount + unsavedCount}`;
  const status = axios.isAxiosError(error) ? error.response?.status : undefined;

  // The session ended under the save: the app is signing out, so the list
  // won't be here to try again from.
  if (status === 401) {
    return {
      title,
      body: 'You’ve been signed out, so the rest weren’t saved. Sign in again to add them.',
    };
  }

  const left = savedCount === 0
    ? 'Your list is still here.'
    : `The other ${unsavedCount} ${unsavedCount === 1 ? 'is' : 'are'} still here.`;

  let why: string;
  let advice = 'Try again in a moment.';
  if (status === undefined) {
    why = axios.isAxiosError(error) || isRetryableError(error)
      ? 'PlantAdvocate couldn’t reach the server.'
      : 'Something went wrong while saving them.';
  } else if (status === 503) {
    why = sentence(serverMessage(error, 'The server couldn’t take them just now.'));
  } else if (isRetryableError(error)) {
    why = 'The server couldn’t take them just now.';
  } else {
    // A refusal that will be the same next time: something in the list no
    // longer matches the server (a species or growing area changed since
    // the walk began).
    why = 'The server didn’t accept them as they are. A species or growing area in the list '
      + 'may have changed since you started.';
    advice = 'Check the list, then try again.';
  }
  return { title, body: `${why} ${left} ${advice}` };
}
