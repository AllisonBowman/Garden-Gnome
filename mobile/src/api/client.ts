import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

const DEFAULT_BASE_URL = 'http://localhost:8000';
const BASE_URL_KEY = 'garden_gnome_api_url';

export async function getBaseUrl(): Promise<string> {
  const stored = await SecureStore.getItemAsync(BASE_URL_KEY);
  return stored ?? DEFAULT_BASE_URL;
}

export async function setBaseUrl(url: string): Promise<void> {
  await SecureStore.setItemAsync(BASE_URL_KEY, url.replace(/\/$/, ''));
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
