// Device-geocoder lookups (keyless — uses the OS geocoder via expo-location).
// Kept apart from the pure geocode helpers so those stay unit-testable.
import * as Location from 'expo-location';
import { resolvePlace, ResolvedPlace } from './geocode';

/**
 * Resolve a typed address to a real place, or null if it doesn't geocode.
 * Forward-geocode the text to coordinates (this is the validation step — only
 * real, resolvable addresses come back), then reverse-geocode those coordinates
 * to a canonical address we can display and store.
 */
export async function searchAddress(query: string): Promise<ResolvedPlace | null> {
  const q = query.trim();
  if (q.length < 4) return null;
  try {
    const hits = await Location.geocodeAsync(q);
    if (!hits.length) return null;
    const { latitude, longitude } = hits[0];
    const [addr] = await Location.reverseGeocodeAsync({ latitude, longitude });
    return resolvePlace(addr ?? {}, latitude, longitude);
  } catch {
    return null;
  }
}

/** Reverse-geocode the device's current position to a place, or null. Caller
 *  must have already secured permission (see ensureLocationPermission). */
export async function locateMe(): Promise<ResolvedPlace | null> {
  try {
    const pos = await Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.Balanced,
    });
    const { latitude, longitude } = pos.coords;
    const [addr] = await Location.reverseGeocodeAsync({ latitude, longitude });
    return resolvePlace(addr ?? {}, latitude, longitude);
  } catch {
    return null;
  }
}
