// Pure helpers for turning a device-geocoder result into the fields an
// Environment stores. No expo/react-native imports so they unit-test directly.
// (The actual geocoder calls live in lookup.ts.)

// Mirrors the shape of expo-location's LocationGeocodedAddress (only the fields
// we use). Declared locally to keep this module dependency-free.
export interface GeocodedAddress {
  name?: string | null;
  street?: string | null;
  streetNumber?: string | null;
  city?: string | null;
  district?: string | null;
  subregion?: string | null;
  region?: string | null;
  postalCode?: string | null;
  country?: string | null;
  isoCountryCode?: string | null;
  formattedAddress?: string | null; // Android provides this pre-composed
}

export interface ResolvedPlace {
  address: string; // one-line display string (not persisted server-side)
  city: string;
  region: string;
  country: string;
  lat: number;
  lng: number;
}

function clean(s?: string | null): string {
  return (s ?? '').trim();
}

/** A single-line, human-readable address. Uses Android's pre-composed string
 *  when present, otherwise builds one from parts and drops empties/duplicates. */
export function formatAddress(a: GeocodedAddress): string {
  if (clean(a.formattedAddress)) return clean(a.formattedAddress);

  const line1 = [a.streetNumber, a.street].map(clean).filter(Boolean).join(' ')
    || clean(a.name);
  const parts = [line1, clean(a.city), clean(a.region), clean(a.country)].filter(Boolean);

  // Drop a component that repeats the one before it (e.g. name === city).
  const out: string[] = [];
  for (const p of parts) if (out[out.length - 1] !== p) out.push(p);
  return out.join(', ');
}

/** Combine a geocoder result + coordinates into the stored Environment fields.
 *  City falls back to district/subregion for rural places that report no city. */
export function resolvePlace(a: GeocodedAddress, lat: number, lng: number): ResolvedPlace {
  return {
    address: formatAddress(a),
    city: clean(a.city) || clean(a.district) || clean(a.subregion),
    region: clean(a.region),
    country: clean(a.country),
    lat,
    lng,
  };
}
