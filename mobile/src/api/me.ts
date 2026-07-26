import { apiClient } from './client';
import { AuthUser } from '../auth/tokenStorage';

/**
 * Update the signed-in caretaker's own profile.
 *
 * `census_opt_in` is the consent switch behind the community census: the
 * backend counts a user's plants only while this is true, and it defaults to
 * false for every new account (app/models/models.py). Until this call existed
 * the column could not be changed from the app at all — the privacy policy
 * promised a control that had no way to be operated.
 */
export async function updateMe(
  patch: Partial<Pick<AuthUser, 'display_name' | 'census_opt_in'>>,
): Promise<AuthUser> {
  const client = await apiClient();
  const { data } = await client.patch<AuthUser>('/me', patch);
  return data;
}
