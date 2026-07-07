import axios from 'axios';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

// Hosted backend (Fly.io). iOS release builds block plain http to
// non-localhost hosts (ATS), so the default must be https. For local dev,
// point at your machine via Settings (e.g. http://192.168.1.119:8000).
const DEFAULT_BASE_URL = 'https://garden-gnome-api.fly.dev';
const BASE_URL_KEY = 'garden_gnome_api_url';

// expo-secure-store has no web implementation (not a supported platform in
// SDK 57), so the browser dev preview falls back to localStorage.
export async function getBaseUrl(): Promise<string> {
  const stored = Platform.OS === 'web'
    ? localStorage.getItem(BASE_URL_KEY)
    : await SecureStore.getItemAsync(BASE_URL_KEY);
  return stored ?? DEFAULT_BASE_URL;
}

export async function setBaseUrl(url: string): Promise<void> {
  const value = url.replace(/\/$/, '');
  if (Platform.OS === 'web') {
    localStorage.setItem(BASE_URL_KEY, value);
  } else {
    await SecureStore.setItemAsync(BASE_URL_KEY, value);
  }
}

// Build a fresh axios instance pointed at the current configured URL.
// Call this before each request batch rather than caching at module load time
// so URL changes in Settings take effect immediately.
export async function apiClient() {
  const baseURL = await getBaseUrl();
  return axios.create({
    baseURL,
    timeout: 15000,
    headers: { 'Content-Type': 'application/json' },
  });
}
