import { requireOptionalNativeModule } from 'expo-modules-core';

// requireOptional* returns null (instead of throwing) when the native module
// isn't linked — i.e. on web, in Expo Go, or before a dev/prebuild build. That
// null is the first line of graceful degradation.
const PlantId = requireOptionalNativeModule<PlantIdNativeModule>('PlantId');

interface PlantIdNativeModule {
  /** Whether on-device generative AI can run on this device right now. */
  isAvailable(): Promise<boolean>;
  /**
   * Run on-device inference over a photo + text prompt and return the model's
   * raw text answer. Never treat this as authoritative — callers fuzzy-match it
   * against the curated catalog.
   */
  identify(imageUri: string, prompt: string): Promise<string>;
}

/** True when the native module is linked into this build at all. */
export const isLinked = PlantId != null;

export async function isAvailable(): Promise<boolean> {
  if (!PlantId) return false;
  try {
    return await PlantId.isAvailable();
  } catch {
    return false;
  }
}

export async function identify(imageUri: string, prompt: string): Promise<string | null> {
  if (!PlantId) return null;
  return PlantId.identify(imageUri, prompt);
}
