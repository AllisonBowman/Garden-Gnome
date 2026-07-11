import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

// Same storage pattern as api/client.ts and the reminder prefs.
const KEY = 'garden_gnome_onboarding_seen';

export async function getOnboardingSeen(): Promise<boolean> {
  const v = Platform.OS === 'web'
    ? localStorage.getItem(KEY)
    : await SecureStore.getItemAsync(KEY);
  return v === 'true';
}

export async function setOnboardingSeen(): Promise<void> {
  if (Platform.OS === 'web') {
    localStorage.setItem(KEY, 'true');
  } else {
    await SecureStore.setItemAsync(KEY, 'true');
  }
}
