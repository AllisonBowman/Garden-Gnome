// Words on the login screen, kept apart from the component so jest can pin
// them (this jest setup can't render React Native).

/**
 * Why an account is needed, and that signing in is how one is made, said
 * before anyone is asked to sign in. Even the catalog needs a signed-in
 * request, so the login comes before any content, and App Review
 * (guideline 5.1.1(v)) expects a required login to give its reason.
 */
export const SIGN_IN_REASON =
  'Signing in creates your account, so your plants, care log and growing areas follow you to a new phone.';
