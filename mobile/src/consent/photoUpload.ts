import { Alert, Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { PHOTO_DIAGNOSIS_NOTICE } from './copy';

// Same storage pattern as onboarding/storage.ts and the reminder prefs.
const KEY = 'garden_gnome_photo_upload_consent';

export async function getPhotoUploadConsent(): Promise<boolean> {
  const v = Platform.OS === 'web'
    ? localStorage.getItem(KEY)
    : await SecureStore.getItemAsync(KEY);
  return v === 'true';
}

export async function setPhotoUploadConsent(granted: boolean): Promise<void> {
  const value = granted ? 'true' : 'false';
  if (Platform.OS === 'web') {
    localStorage.setItem(KEY, value);
  } else {
    await SecureStore.setItemAsync(KEY, value);
  }
}

/**
 * Ask, once, before the first photo leaves the device.
 *
 * A photo check-up uploads the image; identifying a plant does not. Those two
 * buttons sit a thumb's width apart and look alike, so the difference has to
 * be stated at the moment it applies — the OS camera prompt says nothing about
 * where the picture goes, and a policy read at signup is not consent for an
 * upload happening weeks later.
 *
 * Remembered once granted, so it is a disclosure rather than a nag. Declining
 * is remembered too, but not permanently: the notice returns next time, since
 * "not right now" is the common reading of that button and a permanently dead
 * feature would be a worse outcome than asking twice.
 *
 * Returns true only if the upload may proceed.
 */
export async function ensurePhotoUploadConsent(): Promise<boolean> {
  if (await getPhotoUploadConsent()) return true;

  const granted = await confirmUpload();
  if (granted) await setPhotoUploadConsent(true);
  return granted;
}

function confirmUpload(): Promise<boolean> {
  const { title, body, confirmLabel, cancelLabel } = PHOTO_DIAGNOSIS_NOTICE;

  // Alert.alert's buttons are no-ops on react-native-web (same reason
  // SettingsScreen has its own confirmDialog).
  if (Platform.OS === 'web') {
    return Promise.resolve(window.confirm(`${title}\n\n${body}`));
  }
  return new Promise((resolve) => {
    Alert.alert(title, body, [
      { text: cancelLabel, style: 'cancel', onPress: () => resolve(false) },
      { text: confirmLabel, onPress: () => resolve(true) },
    ]);
  });
}
