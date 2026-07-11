import { Platform } from 'react-native';
import { Species } from '../types';
import { isAvailable, identify } from '../../modules/plant-id';
import { matchSpecies, classifyMatches } from './fuzzyMatch';

// Single entry point the "Identify from a photo" UI calls. It hides which
// on-device backend ran (Apple Foundation Models on iOS, Gemini Nano on
// Android) and — crucially — never returns the model's raw text as
// authoritative: the answer is fuzzy-matched against the curated catalog and
// only a real record (with real care data) is offered as a selectable species.

export interface IdentifyCandidate {
  id: number;
  common_name: string;
  scientific_name: string;
}

export interface IdentifyResponse {
  backend: string;
  observation: string;
  candidates: IdentifyCandidate[];
}

const PROMPT =
  'Identify this plant species. Respond with just the most likely species name.';

function backendLabel(): string {
  return Platform.OS === 'ios' ? 'apple-foundation-models'
    : Platform.OS === 'android' ? 'gemini-nano'
    : 'unavailable';
}

export type PhotoAsset = { uri: string; mimeType?: string; fileName?: string | null };

/**
 * Identify a plant from a photo using on-device AI, grounded in the catalog.
 * Always resolves (never throws) with an IdentifyResponse the existing UI
 * understands — empty candidates means "fall back to manual search".
 */
export async function identifySpeciesPhoto(
  photo: PhotoAsset,
  speciesList: Species[],
): Promise<IdentifyResponse> {
  const backend = backendLabel();

  // 1. Graceful degradation: no on-device AI here (web, older hardware,
  //    Apple Intelligence off, non-AICore Android, or not a dev/prebuild build).
  if (!(await isAvailable())) {
    return {
      backend: 'unavailable',
      observation:
        "On-device plant identification isn't available on this device — search for your plant below.",
      candidates: [],
    };
  }

  // 2. On-device inference (no network).
  let aiText: string | null = null;
  try {
    aiText = await identify(photo.uri, PROMPT);
  } catch {
    return {
      backend,
      observation: "Couldn't read the photo this time — search for your plant below.",
      candidates: [],
    };
  }
  if (!aiText || !aiText.trim()) {
    return {
      backend,
      observation: "The model couldn't name this plant — search for it below.",
      candidates: [],
    };
  }

  // 3. Ground the model's text in the curated catalog.
  const { tier, candidates } = classifyMatches(matchSpecies(aiText, speciesList));
  const toCandidate = (m: { species: Species }): IdentifyCandidate => ({
    id: m.species.id,
    common_name: m.species.common_name,
    scientific_name: m.species.scientific_name,
  });

  if (tier === 'confident') {
    return {
      backend,
      observation: 'Identified on-device — tap to confirm, or pick another below.',
      candidates: candidates.map(toCandidate),
    };
  }
  if (tier === 'plausible') {
    return {
      backend,
      observation: 'Best guesses from the photo — tap one, or search below.',
      candidates: candidates.map(toCandidate),
    };
  }

  // 4. No confident catalog match: surface the model's guess but flag that we
  //    have no curated care data for it, and hand off to manual search.
  return {
    backend,
    observation:
      `The photo looks like “${aiText.trim()}”, but that isn't in our care ` +
      `database yet — search below to pick the closest match.`,
    candidates: [],
  };
}

/** Whether the "Identify from a photo" button should be offered at all. */
export async function photoIdAvailable(): Promise<boolean> {
  return isAvailable();
}
