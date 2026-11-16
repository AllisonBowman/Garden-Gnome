import { useEffect, useRef, useState } from 'react';
import { fetchSignedDataUri, imageHeaders, imageryUri } from '../api/properties';

/**
 * Where to show a picture from our server (an aerial image, a map layer),
 * once known. `path` is the server path, such as Imagery.image_path or
 * MapLayer.image_path; null shows nothing.
 *
 * First choice: the bytes fetched through the signed-in client and handed to
 * the image as a `data:` address, so a stale token is refreshed and no header
 * has to ride on the image element (the web preview cannot send one). If
 * that fails, fall back to the server address plus the sign-in header.
 * `failed` is true when neither worked, so a screen can say so in one line.
 *
 *   const { uri, headers } = useSignedImage(layer?.image_path ?? null);
 *   {uri ? <Image source={{ uri, headers }} /> : null}
 *
 * `reloadKey` loads the same path again when it changes (a pull to refresh
 * after a failed load, say).
 */
export function useSignedImage(path: string | null | undefined, reloadKey?: string | number): {
  uri: string | null; headers: Record<string, string> | undefined; failed: boolean;
} {
  const [uri, setUri] = useState<string | null>(null);
  const [headers, setHeaders] = useState<Record<string, string> | undefined>(undefined);
  const [failed, setFailed] = useState(false);
  const want = path || null;
  const last = useRef<string | null>(null);
  useEffect(() => {
    let live = true;
    setFailed(false);
    const samePath = last.current === want;
    last.current = want;
    if (!want) { setUri(null); setHeaders(undefined); return () => { live = false; }; }
    // A different picture: do not keep showing the last one meanwhile. The
    // same one loaded again (reloadKey) stays on screen until it is replaced.
    if (!samePath) setUri(null);
    void fetchSignedDataUri(want).then((dataUri) => {
      if (!live) return;
      setHeaders(undefined);
      setUri(dataUri);
    }).catch(() => Promise.all([imageryUri({ image_path: want }), imageHeaders()]).then(([u, h]) => {
      if (!live) return;
      setHeaders(h);
      setUri(u);
    })).catch(() => { if (live) { setUri(null); setFailed(true); } });
    return () => { live = false; };
  }, [want, reloadKey]);
  return { uri, headers, failed };
}
