import { Alert, Linking } from 'react-native';
import * as Location from 'expo-location';

/**
 * Ask for foreground location access before reading the device position.
 *
 * Mirrors ensureCameraPermission: request once, and if it was permanently
 * denied, point the user at Settings instead of leaving a dead button.
 * Returns true only if the location may actually be read.
 */
export async function ensureLocationPermission(): Promise<boolean> {
  const current = await Location.getForegroundPermissionsAsync();
  if (current.granted) return true;

  if (current.canAskAgain) {
    const asked = await Location.requestForegroundPermissionsAsync();
    if (asked.granted) return true;
    // Declined at the system prompt — they made a choice; the user can still
    // type an address instead, so say nothing.
    return false;
  }

  // Previously denied — iOS won't prompt again, so Settings is the only route.
  Alert.alert(
    'Location access is off',
    "PlantAdvocate can't read your location because location access is turned off. "
    + 'You can turn it on in Settings, or just type the address instead.',
    [
      { text: 'Not now', style: 'cancel' },
      { text: 'Open Settings', onPress: () => { void Linking.openSettings(); } },
    ],
  );
  return false;
}
