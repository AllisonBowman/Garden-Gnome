// Where Home keeps the plant checks skipped this week (a skip logs nothing;
// it only hides the row until the ISO week turns over).
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { isoWeek } from './homeTasks';

const SKIPS_KEY = 'garden_gnome_home_skips';

export async function loadSkips(today: Date = new Date()): Promise<Set<string>> {
  try {
    const raw = Platform.OS === 'web' ? localStorage.getItem(SKIPS_KEY) : await SecureStore.getItemAsync(SKIPS_KEY);
    const parsed = raw ? JSON.parse(raw) as { week?: string; keys?: string[] } : null;
    return parsed?.week === isoWeek(today) && Array.isArray(parsed.keys) ? new Set(parsed.keys) : new Set();
  } catch {
    return new Set();
  }
}

export async function saveSkips(keys: Set<string>, today: Date = new Date()): Promise<void> {
  const value = JSON.stringify({ week: isoWeek(today), keys: [...keys] });
  if (Platform.OS === 'web') localStorage.setItem(SKIPS_KEY, value);
  else await SecureStore.setItemAsync(SKIPS_KEY, value);
}
