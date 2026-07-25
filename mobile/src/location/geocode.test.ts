import { formatAddress, resolvePlace, GeocodedAddress } from './geocode';

describe('formatAddress', () => {
  test('prefers Android pre-composed formattedAddress', () => {
    expect(formatAddress({ formattedAddress: '123 Main St, Denver, CO, USA', city: 'Denver' }))
      .toBe('123 Main St, Denver, CO, USA');
  });

  test('composes from street/city/region/country when no formattedAddress', () => {
    const a: GeocodedAddress = {
      streetNumber: '123', street: 'Main St', city: 'Denver', region: 'CO', country: 'United States',
    };
    expect(formatAddress(a)).toBe('123 Main St, Denver, CO, United States');
  });

  test('drops a part that repeats the previous one (name === city)', () => {
    const a: GeocodedAddress = { name: 'Denver', city: 'Denver', region: 'CO', country: 'USA' };
    expect(formatAddress(a)).toBe('Denver, CO, USA');
  });

  test('falls back to name when there is no street', () => {
    expect(formatAddress({ name: 'Central Park', country: 'USA' })).toBe('Central Park, USA');
  });

  test('trims and skips empty parts', () => {
    expect(formatAddress({ street: '  ', city: 'Austin', region: '', country: 'USA' }))
      .toBe('Austin, USA');
  });
});

describe('resolvePlace', () => {
  test('maps fields and carries coordinates', () => {
    const a: GeocodedAddress = {
      streetNumber: '1', street: 'Elm', city: 'Boulder', region: 'CO', country: 'USA',
    };
    expect(resolvePlace(a, 40.01, -105.27)).toEqual({
      address: '1 Elm, Boulder, CO, USA',
      city: 'Boulder',
      region: 'CO',
      country: 'USA',
      lat: 40.01,
      lng: -105.27,
    });
  });

  test('city falls back to district then subregion for placeless rural spots', () => {
    expect(resolvePlace({ district: 'Weld County', region: 'CO', country: 'USA' }, 1, 2).city)
      .toBe('Weld County');
    expect(resolvePlace({ subregion: 'Larimer', region: 'CO', country: 'USA' }, 1, 2).city)
      .toBe('Larimer');
  });

  test('missing components become empty strings, coords still set', () => {
    const r = resolvePlace({}, 12.34, 56.78);
    expect(r).toEqual({ address: '', city: '', region: '', country: '', lat: 12.34, lng: 56.78 });
  });
});
