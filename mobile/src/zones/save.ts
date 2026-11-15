import { Box, OverridePut, SiteProfile, Zone, ZoneCreate, ZonePatch } from '../types/site';
import { ZoneDraft, correctionBodies, zoneCreateBody, zonePatchBody } from './describe';

/** The calls a zone save makes, passed in so the order can be tested. */
export interface ZoneSaveApi {
  createZone(body: ZoneCreate): Promise<Zone>;
  updateZone(zoneId: number, patch: ZonePatch): Promise<Zone>;
  putOverride(body: OverridePut): Promise<SiteProfile>;
}

export interface ZoneSaveInput {
  /** The zone being edited, or null for a new one. */
  existing: Zone | null;
  draft: ZoneDraft;
  box: Box | null;
  /** The owner moved or drew the box on this step. */
  boxEdited: boolean;
  /** "Add a zone without drawing": the box is the approximate whole lot. */
  noDraw: boolean;
  existingNames: string[];
}

/** Thrown when the zone was created but an answer about it was not saved. */
export class AnswersNotSaved extends Error {
  constructor(readonly zone: Zone, readonly cause: unknown) {
    super('The zone was saved, but its answers were not.');
  }
}

/**
 * Create or update the zone, then send one correction per tapped answer.
 * `onCreated` runs as soon as a new zone exists, so the caller can switch to
 * editing it: a retry after a failed answer then patches that zone instead
 * of creating a second one.
 */
export async function saveZone(
  api: ZoneSaveApi, input: ZoneSaveInput, onCreated: (zone: Zone) => void = () => {},
): Promise<{ zone: Zone; profile: SiteProfile | null }> {
  const { existing, draft, box, boxEdited, noDraw, existingNames } = input;
  let zone: Zone;
  let created = false;
  if (existing) {
    const patch = zonePatchBody(existing, draft, boxEdited ? box : null);
    zone = Object.keys(patch).length > 0 ? await api.updateZone(existing.id, patch) : existing;
  } else {
    // A box the owner never drew is the approximate whole lot, and the
    // server must not count it as drawn.
    const drawn = !(noDraw && !boxEdited);
    zone = await api.createZone(zoneCreateBody(draft, box!, existingNames, drawn));
    created = true;
    onCreated(zone);
  }
  let profile: SiteProfile | null = null;
  try {
    for (const body of correctionBodies(zone.id, draft)) {
      profile = await api.putOverride(body);
    }
  } catch (err) {
    if (created) throw new AnswersNotSaved(zone, err);
    throw err;
  }
  return { zone, profile };
}
