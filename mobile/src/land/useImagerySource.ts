import { useEffect, useState } from 'react';
import { Imagery } from '../types/site';
import { fetchImageryDataUri, imageHeaders, imageryUri } from '../api/properties';

/**
 * Where to show an Imagery's picture from, once known.
 *
 * First choice: the bytes fetched through the signed-in client and handed to
 * the image as a `data:` address, so a stale token is refreshed and no header
 * has to ride on the image element. If that fails, fall back to the server
 * address plus the sign-in header.
 */
export function useImagerySource(imagery: Imagery | null | undefined): {
  uri: string | null; headers: Record<string, string> | undefined;
} {
  const [uri, setUri] = useState<string | null>(null);
  const [headers, setHeaders] = useState<Record<string, string> | undefined>(undefined);
  const path = imagery?.image_path ?? null;
  useEffect(() => {
    let live = true;
    if (!path) { setUri(null); return () => { live = false; }; }
    void fetchImageryDataUri({ image_path: path }).then((dataUri) => {
      if (!live) return;
      setHeaders(undefined);
      setUri(dataUri);
    }).catch(() => Promise.all([imageryUri({ image_path: path }), imageHeaders()]).then(([u, h]) => {
      if (!live) return;
      setHeaders(h);
      setUri(u);
    })).catch(() => { if (live) setUri(null); });
    return () => { live = false; };
  }, [path]);
  return { uri, headers };
}
