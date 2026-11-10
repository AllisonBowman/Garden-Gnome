import { Alert, Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { QUESTION_NOTICE } from './copy';

// Same storage pattern as photoUpload.ts, onboarding/storage.ts and the
// reminder prefs.
const KEY = 'garden_gnome_question_consent';

async function readConsent(): Promise<boolean> {
  try {
    const v = Platform.OS === 'web'
      ? localStorage.getItem(KEY)
      : await SecureStore.getItemAsync(KEY);
    return v === 'true';
  } catch {
    // An unreadable keychain (a locked phone) is not a yes: ask.
    return false;
  }
}

async function rememberConsent(): Promise<void> {
  try {
    if (Platform.OS === 'web') localStorage.setItem(KEY, 'true');
    else await SecureStore.setItemAsync(KEY, 'true');
  } catch {
    // Not remembered this time; the notice comes back next time. The
    // question still goes, because the caretaker just said yes to it.
  }
}

/**
 * The question that would leave the phone: the box's words, only while the
 * box is offered (care/aiCapabilities.ts symptomsOffered) and only when
 * there are words in it. Empty means advice is asked for without one.
 */
export function questionToSend(offered: boolean, text: string): string {
  return offered ? text.trim() : '';
}

/**
 * Ask, once, before the first question in the caretaker's own words leaves
 * the phone, the way photoUpload.ts asks before the first photo.
 *
 * A question goes to an outside AI service with the plant's nickname, care
 * log and growing area, and the switch that turns the box on is the
 * server's, not an app update's. So the app asks at the moment it applies,
 * rather than relying on a policy read at sign-up. Remembered once granted.
 * "Not now" is remembered only until next time, and sends nothing.
 *
 * True when advice may be asked for: there is no question, or the caretaker
 * agreed to send it.
 */
export async function mayAskWith(question: string): Promise<boolean> {
  if (!question) return true;
  if (await readConsent()) return true;
  const granted = await confirmSend();
  if (granted) await rememberConsent();
  return granted;
}

function confirmSend(): Promise<boolean> {
  const { title, body, confirmLabel, cancelLabel } = QUESTION_NOTICE;

  // Alert.alert's buttons are no-ops on react-native-web (same reason
  // SettingsScreen has its own confirmDialog).
  if (Platform.OS === 'web') {
    return Promise.resolve(window.confirm(`${title}\n\n${body}`));
  }
  return new Promise((resolve) => {
    Alert.alert(title, body, [
      { text: cancelLabel, style: 'cancel', onPress: () => resolve(false) },
      { text: confirmLabel, onPress: () => resolve(true) },
    ], { cancelable: true, onDismiss: () => resolve(false) });
  });
}
