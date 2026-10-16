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
