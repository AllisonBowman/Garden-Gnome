import { requireOptionalNativeModule } from 'expo-modules-core';

// Hands-free dictation for the walk-the-garden flow.
//
// requireOptional* returns null rather than throwing when the module isn't
// linked — on web, in Expo Go, or before a prebuild — which is the first line
// of graceful degradation. Every export below short-circuits on that null, so
// callers can simply fall back to typing (or the keyboard's own dictation key,
// which needs none of this).

export interface TranscriptEvent {
  /** The whole utterance heard so far, not just the newest words. */
  text: string;
  /** True when the recognizer considers the phrase finished. */
  isFinal: boolean;
}

export interface SpeechErrorEvent {
  message: string;
}

interface Subscription { remove(): void }

interface PlantSpeechNativeModule {
  isAvailable(): Promise<boolean>;
  /** Whether recognition can run without a network round-trip here. */
  supportsOnDevice(): Promise<boolean>;
  /** Asks for speech + microphone. True only when both were granted. */
  requestPermission(): Promise<boolean>;
  /** Begins listening. Resolves true when running on-device. */
  start(): Promise<boolean>;
  stop(): Promise<void>;
  addListener(
    event: 'onTranscript' | 'onSpeechError',
    listener: (payload: never) => void,
  ): Subscription;
}

const PlantSpeech = requireOptionalNativeModule<PlantSpeechNativeModule>('PlantSpeech');

/** True when the native module is linked into this build at all. */
export const isLinked = PlantSpeech != null;

export async function isAvailable(): Promise<boolean> {
  if (!PlantSpeech) return false;
  try {
    return await PlantSpeech.isAvailable();
  } catch {
    return false;
  }
}

export async function supportsOnDevice(): Promise<boolean> {
  if (!PlantSpeech) return false;
  try {
    return await PlantSpeech.supportsOnDevice();
  } catch {
    return false;
  }
}

export async function requestPermission(): Promise<boolean> {
  if (!PlantSpeech) return false;
  try {
    return await PlantSpeech.requestPermission();
  } catch {
    return false;
  }
}

/** Start listening. Resolves true when recognition is running on-device, false
 *  when it fell back to the network — the caller should say which, rather than
 *  letting someone assume their garden audio stayed on the phone. */
export async function start(): Promise<boolean> {
  if (!PlantSpeech) throw new Error('Speech recognition is not available in this build.');
  return PlantSpeech.start();
}

export async function stop(): Promise<void> {
  if (!PlantSpeech) return;
  await PlantSpeech.stop();
}

export function onTranscript(listener: (e: TranscriptEvent) => void): Subscription {
  if (!PlantSpeech) return { remove() {} };
  return PlantSpeech.addListener(
    'onTranscript',
    listener as unknown as (payload: never) => void,
  );
}

export function onSpeechError(listener: (e: SpeechErrorEvent) => void): Subscription {
  if (!PlantSpeech) return { remove() {} };
  return PlantSpeech.addListener(
    'onSpeechError',
    listener as unknown as (payload: never) => void,
  );
}
