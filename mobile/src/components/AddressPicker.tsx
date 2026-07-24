import React, { useRef, useState } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import {
  TextInput, Button, Text, ActivityIndicator, TouchableRipple,
} from 'react-native-paper';
import { ensureLocationPermission } from '../location/permissions';
import { searchAddress, locateMe } from '../location/lookup';
import { ResolvedPlace } from '../location/geocode';

const DEBOUNCE_MS = 600;
const MIN_CHARS = 4;

/**
 * A validated place picker: the user types an address (resolved against the
 * device geocoder, so only real places can be selected) or taps "Use my
 * location". `onChange` fires with a ResolvedPlace once one is chosen, or null
 * while nothing valid is selected — the parent uses that to gate saving.
 */
export default function AddressPicker({
  onChange,
}: {
  onChange: (place: ResolvedPlace | null) => void;
}) {
  const [query, setQuery] = useState('');
  const [suggestion, setSuggestion] = useState<ResolvedPlace | null>(null);
  const [selected, setSelected] = useState<ResolvedPlace | null>(null);
  const [searching, setSearching] = useState(false);
  const [locating, setLocating] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const scheduleSearch = (text: string) => {
    if (timer.current) clearTimeout(timer.current);
    if (text.trim().length < MIN_CHARS) { setSuggestion(null); return; }
    timer.current = setTimeout(async () => {
      setSearching(true);
      const place = await searchAddress(text);
      setSuggestion(place);
      setSearching(false);
    }, DEBOUNCE_MS);
  };

  const onType = (text: string) => {
    setQuery(text);
    // Editing invalidates a previous pick until a new place is confirmed.
    if (selected) { setSelected(null); onChange(null); }
    scheduleSearch(text);
  };

  const pick = (place: ResolvedPlace) => {
    setSelected(place);
    setSuggestion(null);
    setQuery(place.address);
    onChange(place);
  };

  const useMyLocation = async () => {
    if (!(await ensureLocationPermission())) return;
    setLocating(true);
    const place = await locateMe();
    setLocating(false);
    if (place) pick(place);
    else Alert.alert(
      'Location unavailable',
      "Couldn't determine your address from your location. Try typing it instead.",
    );
  };

  const noMatch =
    !selected && !suggestion && !searching && query.trim().length >= MIN_CHARS;

  return (
    <View>
      <TextInput
        label="Address or place (optional)"
        value={query}
        onChangeText={onType}
        mode="outlined"
        autoCapitalize="words"
        style={styles.input}
        right={searching ? <TextInput.Icon icon={() => <ActivityIndicator size={18} />} /> : undefined}
      />

      <Button
        icon="crosshairs-gps"
        mode="text"
        compact
        onPress={useMyLocation}
        loading={locating}
        disabled={locating}
        style={styles.gpsBtn}
      >
        Use my location
      </Button>

      {suggestion && !selected ? (
        <TouchableRipple onPress={() => pick(suggestion)} style={styles.suggestion}>
          <View>
            <Text variant="bodyMedium" style={styles.suggestionText}>📍 {suggestion.address}</Text>
            <Text variant="bodySmall" style={styles.suggestionHint}>Tap to use this place</Text>
          </View>
        </TouchableRipple>
      ) : null}

      {selected ? (
        <Text variant="bodySmall" style={styles.confirmed}>
          ✓ Location set{selected.city ? ` — ${selected.city}${selected.region ? `, ${selected.region}` : ''}` : ''}
        </Text>
      ) : null}

      {noMatch ? (
        <Text variant="bodySmall" style={styles.noMatch}>
          No match yet — keep typing the full address, or use your location.
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  input: { marginBottom: 4 },
  gpsBtn: { alignSelf: 'flex-start', marginBottom: 4 },
  suggestion: {
    backgroundColor: '#EFF6F0',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  suggestionText: { color: '#2F3E36' },
  suggestionHint: { color: '#6b7d6e', marginTop: 2 },
  confirmed: { color: '#2D6A4F', marginBottom: 8, fontWeight: '600' },
  noMatch: { color: '#8a8a8a', marginBottom: 8, fontStyle: 'italic' },
});
