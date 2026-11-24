import { Alert, Linking } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { t } from './i18n';

/**
 * Ask for camera access before opening the camera.
 *
 * expo-image-picker's launchCameraAsync REQUIRES camera permission and does
 * not request it for you — without a grant it resolves `{canceled: true}`,
 * which every caller treats as "user backed out". The result is a button that
 * does nothing at all, with no error and no system prompt. Route every camera
 * launch through here instead.
 *
 * Returns true only if the camera may actually be opened.
 */
export async function ensureCameraPermission(): Promise<boolean> {
  const current = await ImagePicker.getCameraPermissionsAsync();
  if (current.granted) return true;

  if (current.canAskAgain) {
    const asked = await ImagePicker.requestCameraPermissionsAsync();
    if (asked.granted) return true;
    // Declined at the system prompt: they made a choice, so say nothing and
    // let them use "Choose photo" instead.
    return false;
  }

  // Previously denied — iOS will not show the prompt again, so the only route
  // is Settings. Say so plainly rather than leaving a dead button.
  Alert.alert(
    t('common.cameraOff.title'),
    t('common.cameraOff.body'),
    [
      { text: t('common.notNow'), style: 'cancel' },
      { text: t('common.openSettings'), onPress: () => { void Linking.openSettings(); } },
    ],
  );
  return false;
}
