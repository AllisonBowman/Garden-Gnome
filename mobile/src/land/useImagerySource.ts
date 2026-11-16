import { Imagery } from '../types/site';
import { useSignedImage } from './useSignedImage';

/**
 * Where to show an Imagery's picture from, once known: `useSignedImage` on
 * its `image_path`. Kept so the screens that show the aerial image read the
 * same as before.
 */
export function useImagerySource(imagery: Imagery | null | undefined): {
  uri: string | null; headers: Record<string, string> | undefined;
} {
  const { uri, headers } = useSignedImage(imagery?.image_path ?? null);
  return { uri, headers };
}
