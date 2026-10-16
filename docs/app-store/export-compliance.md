# Export compliance for 1.1.3

## The answer

PlantAdvocate uses no encryption except what iOS itself provides, so it
needs no export documentation. `mobile/app.json:15` sets
`ITSAppUsesNonExemptEncryption` to `false` in the app's Info.plist. App
Store Connect reads that key from each uploaded build and doesn't ask the
encryption questions at all.

If App Store Connect asks anyway, the key didn't make it into the build.
Check the archive's Info.plist. Until it's fixed, answer the questions like
this:

- **Does your app use encryption?** Yes. Every app that makes an HTTPS
  connection does.
- **What type of encryption algorithms does your app implement?** None of
  the algorithms mentioned above. PlantAdvocate implements none of its own.
  It uses only the encryption built into iOS.

No documents to upload, no year-end self-classification report, and no
French declaration.

## Why

All of the app's cryptography is Apple's operating system, or a standard
use of it that U.S. export rules exempt:

- **HTTPS.** Every request goes over HTTPS through iOS networking, to
  `https://garden-gnome-api.fly.dev` (`mobile/src/api/client.ts:12`) and to
  Apple and Google for sign-in.
- **The Keychain.** Sign-in tokens and a few preferences are stored with
  `expo-secure-store`, which is the iOS Keychain
  (`mobile/src/auth/tokenStorage.ts:15-23`).
- **A SHA-256 hash for Sign in with Apple.** `expo-crypto` makes a random
  nonce and hashes it, through iOS (`mobile/src/auth/signIn.ts:41-43`). This
  is hashing for authentication, not encryption of data.
- **Google Sign-In.** The Google SDK signs in over HTTPS, using iOS
  networking.

The server encrypts Apple's refresh token at rest with Fernet
(`garden-gnome/app/routers/auth.py:153, 240`). That code runs on the server,
not in the app, so it has no bearing on the app's export classification.

## When this would change

Look again if the app ever adds its own encryption: end-to-end encrypted
notes, an encrypted local database, a VPN, or a crypto library that doesn't
call into iOS. Until then, the plist key stays `false` and nothing more is
needed.
