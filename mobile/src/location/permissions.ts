import { Alert, Linking } from 'react-native';
import * as Location from 'expo-location';
import { t } from '../i18n';

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
    t('common.locationOff.title'),
    t('common.locationOff.body'),
    [
      { text: t('common.notNow'), style: 'cancel' },
      { text: t('common.openSettings'), onPress: () => { void Linking.openSettings(); } },
    ],
  );
  return false;
}
