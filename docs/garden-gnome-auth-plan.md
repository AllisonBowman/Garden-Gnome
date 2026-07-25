# PlantAdvocate — User Accounts & Auth Implementation Plan

Implementation plan for Claude Code. Backend lives in `garden-gnome/`.
Work through phases in order; each phase ends with passing tests before moving on.

> **Rebrand note (2026-07-15, from the PLANTADVOCATE-HANDOFF doc in Drive):**
> the product is now **PlantAdvocate**; the gnome is the mascot, not the name.
> Repo paths, module names, and internal identifiers may stay as-is — but any
> **user-facing string** this work introduces (e.g. text inside emails or error
> messages returned to the client) must say PlantAdvocate. Bundle ID decision:
> **`com.allisonbowman.plantadvocate`** — update `app.json`
> `ios.bundleIdentifier` to match and regenerate EAS credentials if any were
> already provisioned for the old ID.

---

## Adopted decisions (2026-07-15) — override the phase text below where they conflict

Recorded from Allison's reconciliation review. These amend the original plan:

1. **Environment: EVOLVE the existing model** (the census/stewardship one),
   do not create a parallel table.
   - Add `user_id` (FK to user, **non-null**, backfill existing rows to the
     `dev@local` user).
   - **Keep the existing integer pk** — the plan's UUID-pk spec is amended to
     match (the model already carries a separate `uuid` string column).
   - Extend the existing `EnvironmentType` enum: keep ALL existing values
     (`community_garden` stays; the plan's `community_plot` maps to it;
     `nursery`, `conservation`, `research` remain) and add `balcony`,
     `greenhouse`, `other`.
   - Location fields (city/region/country/lat/lng) stay optional.
   - Known code conflicts with user ownership — to resolve explicitly in
     Phases 5–7, never silently:
     a. `POST /plants/` falls back to "first Environment in the DB" when no
        environment_id is given — cross-user leak once multi-user; must
        become "caller's default environment".
     b. `POST /plants/{id}/transfer` accepts any `to_environment_id` — Phase 6
        must require BOTH environments caller-owned (decision 4).
     c. Census export publishes stable environment UUIDs + geo (decision 3).
     d. `seed_default_environment()` creates a global "My Garden" — becomes
        dev-only (decision 5).
     e. `/environments` router is unauthenticated and returns all rows —
        Phase 6 scopes it.
2. **JWT issuer**: `iss="plantadvocate"` (renamed from the implemented
   `garden-gnome`), folded into the Phase 4 commit.
3. **Census privacy is in scope, not deferred**:
   - `User.census_opt_in` (bool, default **false**) — added in the next
     migration (0003).
   - `GET /census/export` and `POST /census/sync` include only opted-in
     users' data.
   - Environment UUIDs are dropped or per-export rotated (no stable
     pseudonymous identifiers).
   - `lat`/`lng` are dropped from the export; city-level geo stays, for
     opted-in users only.
4. **Transfers**: Phase 6 ownership checks cover `to_environment_id` too —
   both environments caller-owned; **no cross-account transfers in v1**.
5. **`seed_default_environment()` becomes dev-only**; a per-user
   "My Home" (kind=home) environment is created at sign-up in Phase 5.

Status at the time of these decisions: Phases 1–3 implemented and pushed
(`a8873ac`, `3716ee1`) with `iss="garden-gnome"` pending rename; the
"laptop user-profile code" mentioned in the handoff was NOT found on the
remote (no branches/stashes) — reconcile again if it surfaces.

---

## Context

The backend is FastAPI + SQLModel/SQLite (`app/`) with models for
Species, Plant, and CareLog, REST endpoints for plant inventory and care
logging, and a pluggable LLM advisor (`app/services/advisor.py`,
`POST /plants/{plant_id}/advice`). It was single-user: no User model,
no auth, plants not owned by anyone (until Phase 2 landed).

**Goal:** every App Store user gets their own account. Login via Sign in with
Apple and Google Sign-In only (no passwords). The client is the existing
Expo/React Native app (see Phase 8).

## Decisions (already made — do not revisit)

- **Self-hosted auth.** No Firebase/Auth0/Supabase. The backend verifies
  provider ID tokens directly and issues its own tokens.
- **Social login only.** No email/password. (Email magic-link may come later.)
- **Token model:** short-lived access JWT (30 min) + opaque rotating refresh
  token (90 days) stored hashed in the DB, with reuse detection.
- **SQLite stays for now.** Design the schema so a later Postgres move is a
  connection-string change. Flag anything SQLite-specific.

## App Store compliance constraints (non-negotiable)

1. **Guideline 4.8:** because the app offers Google Sign-In, it must also offer
   Sign in with Apple. Both are in scope.
2. **Guideline 5.1.1(v):** the app must offer in-app account deletion. Deletion
   must remove user data server-side AND revoke the user's Apple tokens via
   `POST https://appleid.apple.com/auth/revoke` (see Phase 7 and Apple TN3194).
   This is why the backend exchanges Apple's authorization code for a refresh
   token at sign-in and stores it encrypted.
3. **Privacy nutrition labels** (per handoff doc): with accounts, email and
   user content become "linked to identity" — nothing in this build may log or
   export user data in a way that contradicts that. The anonymized species
   "census" must contain no user identifiers.
4. **App Review notes:** login is social-only, so there is no demo
   username/password to hand Apple — reviewers sign in with their own Apple ID
   via Sign in with Apple. State this explicitly in the review notes and make
   sure a brand-new account lands in a usable (seeded or empty-but-guided)
   state.

---

## Phase 0 — Manual setup (Allison, not Claude Code)

Collect these before Phase 4 can be tested against real providers. Everything
before that works with mocked tokens.

**Apple Developer portal:**
- App ID `com.allisonbowman.plantadvocate` (explicit, not wildcard) with the
  Sign in with Apple capability enabled. Update `app.json`
  `ios.bundleIdentifier` to the same value.
- A Sign in with Apple key (`.p8` file) — record `APPLE_KEY_ID`,
  `APPLE_TEAM_ID`, and keep the `.p8` out of git.

**Google Cloud console:**
- OAuth consent screen configured.
- OAuth Client ID of type **iOS** bound to the bundle ID — record as
  `GOOGLE_CLIENT_ID`.

**Env vars** (add to `.env`, loaded via `app/config.py` Settings — done in Phase 1):

```
JWT_SECRET=<openssl rand -hex 32>
JWT_ALG=HS256
ACCESS_TOKEN_TTL_MIN=30
REFRESH_TOKEN_TTL_DAYS=90
APPLE_BUNDLE_ID=com.allisonbowman.plantadvocate
APPLE_TEAM_ID=...
APPLE_KEY_ID=...
APPLE_PRIVATE_KEY_PATH=secrets/AuthKey_XXXX.p8
GOOGLE_CLIENT_ID=....apps.googleusercontent.com
FERNET_KEY=<from cryptography.fernet.Fernet.generate_key()>
```

---

## Phase 1 — Dependencies, settings, migrations ✅ (a8873ac)

1. Add dependencies: `pyjwt[crypto]`, `httpx`, `cryptography`, `alembic`,
   `pydantic-settings`. Dev: `pytest`, `pytest-asyncio`.
2. `app/config.py` with a `pydantic-settings` `Settings` class; JWT_SECRET and
   FERNET_KEY fail fast at boot; provider credentials stay optional until
   Phase 4 uses them (deviation adopted: strict fail-fast on Apple/Google
   vars would brick boot before Phase 0 is done).
3. Alembic initialized against SQLModel metadata; `0001_baseline` matches the
   pre-auth schema; app lifespan runs migrations (stamps pre-Alembic DBs).

**Accepted:** fresh DB reaches full schema via `alembic upgrade head`; app
boots with settings from `.env`. ⚠️ Fly deploys need
`fly secrets set JWT_SECRET=... FERNET_KEY=...` before this code ships.

## Phase 2 — Data model ✅ (a8873ac), amended by decision 1

Implemented: `User` (uuid-string pk, soft-delete marker), `AuthIdentity`
(unique provider+provider_sub, encrypted Apple refresh token slot),
`RefreshToken` (sha256 hash only, rotation family), `Plant.user_id` FK
(schema-nullable — SQLite can't add NOT NULL to existing rows; enforce at the
app layer from Phase 6; revisit at the Postgres move, along with the reserved
`user` table name). Migration `0002_auth` backfills a `dev@local` user owning
all pre-auth plants.

Still to do under decision 1 (lands with Phase 5): `Environment.user_id`
(backfilled to dev@local, then non-null at app layer), extend
`EnvironmentType` with balcony/greenhouse/other, per-user default
environment at sign-up, and `Plant.user_id == environment.user_id`
invariant enforced in the service layer on create/move.

## Phase 3 — Token service ✅ (3716ee1)

`app/services/tokens.py`: issue/verify HS256 access JWTs (sub/iat/exp/iss,
30 s leeway, typed errors); opaque 256-bit refresh tokens stored as sha256,
rotation preserving family_id; reuse detection revokes the whole family;
idempotent logout revoke; revoke_all_for_user. `iss="plantadvocate"`
(decision 2; renamed in the Phase 4 commit).

## Phase 4 — Provider verification (`app/services/oauth/`)

Shared JWKS helper: fetch keys with `httpx`, kid lookup, cache keys ~6 h,
refetch once on unknown `kid` (handles provider key rotation).

**`apple.py`** — `verify_apple_token(identity_token, raw_nonce) -> AppleClaims`:
- JWKS: `https://appleid.apple.com/auth/keys`
- Require `iss == "https://appleid.apple.com"`, `aud == APPLE_BUNDLE_ID`,
  RS256, unexpired.
- Nonce check: token's `nonce` claim must equal `sha256(raw_nonce)`.
- Return `sub`, `email`, `email_verified`, `is_private_email`.

`exchange_apple_code(authorization_code) -> apple_refresh_token`:
- Build `client_secret`: ES256 JWT signed with the `.p8` key
  (`kid=APPLE_KEY_ID`, `iss=APPLE_TEAM_ID`, `sub=APPLE_BUNDLE_ID`,
  `aud="https://appleid.apple.com"`, exp ≤ 6 months).
- `POST https://appleid.apple.com/auth/token`
  (`grant_type=authorization_code`). Caller encrypts the refresh token with
  Fernet before storing on AuthIdentity (needed only for account-deletion
  revocation). If the exchange fails, log and continue sign-in.

**`google.py`** — `verify_google_token(id_token) -> GoogleClaims`:
- JWKS: `https://www.googleapis.com/oauth2/v3/certs`
- Require `iss in {"accounts.google.com", "https://accounts.google.com"}`,
  `aud == GOOGLE_CLIENT_ID`, unexpired, `email_verified == true`.
- Return `sub`, `email`, `name`, `picture`.

**Testing:** generate an RSA keypair in test fixtures, monkeypatch the JWKS
fetch, sign test tokens locally. Cover: valid, wrong aud, wrong iss, expired,
bad nonce (Apple), unverified email (Google), unknown kid → refetch path.

**Accept when:** all verification tests pass with zero real network calls.

## Phase 5 — Auth API (`app/routers/auth.py`)

Sign-in upsert logic (shared):
1. Look up `AuthIdentity(provider, sub)` — if found, that's the user; update
   `last_login_at`.
2. Else, if claims include a **verified** email exactly matching an existing
   user's email — link new identity to that user. (Apple private-relay emails
   simply won't match — they create a separate account; manual account linking
   is out of scope for v1.)
3. Else create User (+ identity) **and a default Environment**
   (`name="My Home", kind="home"`, owned by the new user — decision 5) so
   every account starts usable. Apple sends `full_name` **only on first
   authorization** — persist it immediately or it's gone.

Endpoints:

| Route | Body | Returns |
|---|---|---|
| `POST /auth/apple` | `identity_token, authorization_code, raw_nonce, full_name?` | `{access_token, refresh_token, user}` |
| `POST /auth/google` | `id_token` | same |
| `POST /auth/refresh` | `refresh_token` | rotated `{access_token, refresh_token}` |
| `POST /auth/logout` | `refresh_token` | 204, revokes that token |
| `GET /me` / `PATCH /me` | — / `display_name` | user profile |

Dependency `get_current_user` in `app/deps.py`: reads `Authorization: Bearer`,
verifies access JWT, loads active (non-deleted) User, else 401.

**Accept when:** integration tests (mocked providers) cover first sign-in,
repeat sign-in, email-based linking, refresh rotation, logout, and 401s.

## Phase 6 — Scope existing endpoints to the user

- Add `get_current_user` to all plant, care-log, and advice routes.
- Plant list/create/read/update/delete: filter and stamp `user_id`; return 404
  (not 403) for other users' plants to avoid ID probing. Fix the
  first-environment fallback in `POST /plants/` (decision 1a).
- Environments: `GET/POST /environments`, `PATCH /environments/{id}`, and
  plant create/update accepts `environment_id` (validated as caller-owned;
  moving a plant preserves its CareLog history). Deleting an environment that
  still contains plants → 409.
- Transfers: BOTH `from` and `to` environments must be caller-owned — no
  cross-account transfers in v1 (decision 4).
- Census (decision 3): export/sync cover opted-in users only; drop or rotate
  environment UUIDs; drop lat/lng; keep city-level geo.
- CareLog and `POST /plants/{id}/advice`: verify the plant belongs to the
  caller before proceeding.
- Species endpoints stay public/read-only.
- Update seed script: demo plants attach to the dev user;
  `seed_default_environment()` becomes dev-only (decision 5).

**Accept when:** tests prove user A cannot read, modify, or get advice for
user B's plants; existing test suite green.

## Phase 7 — Account deletion (App Store 5.1.1(v))

`DELETE /me`:
1. Decrypt stored Apple refresh token (if any) and call
   `POST https://appleid.apple.com/auth/revoke` with a fresh client_secret
   (`token_type_hint=refresh_token`). Treat non-200 as retryable: queue/log it,
   don't block deletion.
2. Revoke all refresh tokens; delete plants, care logs, environments, auth
   identities. Any census/analytics rows must already contain no user
   identifiers (decision 3 enforces this at the export layer).
3. Hard-delete the User row (default; simpler and Apple-compliant).
4. Return 204. Client then clears SecureStore and signs out of Google locally.

**Accept when:** test proves a deleted user's token is rejected and their data
is gone; Apple revoke call is invoked (mocked) exactly once.

## Phase 8 — Expo client (the existing React Native app)

- Prereq: `app.json` → `ios.bundleIdentifier: "com.allisonbowman.plantadvocate"`,
  `ios.usesAppleSignIn: true`, display name `PlantAdvocate`.
- **Apple:** `expo-apple-authentication`. Generate a random nonce, pass
  `sha256(nonce)` as the request nonce, send
  `identityToken + authorizationCode + raw nonce + fullName` to `/auth/apple`.
  Requires a dev/EAS build — Sign in with Apple does not work in Expo Go.
- **Google:** `@react-native-google-signin/google-signin` (config plugin, EAS
  build) with the iOS OAuth client ID; send the resulting `idToken` to
  `/auth/google`.
- Store access + refresh tokens with **expo-secure-store** (Keychain-backed —
  never AsyncStorage).
- API client wrapper: attach Bearer header; on 401, call `/auth/refresh` once
  (single-flight — concurrent 401s share one refresh) and retry; on refresh
  failure, sign out to the login screen.
- Settings screen: Sign out (calls `/auth/logout`) and **Delete account**
  (confirmation dialog → `DELETE /me`, then clear SecureStore + Google
  sign-out) — the delete button must be reachable in-app for App Review.
- All new user-facing strings say **PlantAdvocate**.

## Phase 9 — Hardening checklist (verify before merge)

- [ ] Rate-limit `/auth/*` (e.g. `slowapi`, per-IP).
- [ ] Tokens never logged; `.p8`, `.env`, `secrets/` git-ignored.
- [ ] JWT `iss` checked; clock-skew leeway ≤ 60 s.
- [ ] Refresh reuse detection revokes the whole family (Phase 3 test).
- [ ] HTTPS assumed in production (TLS terminates at the host — Fly.io).
- [ ] Apple refresh tokens encrypted at rest (Fernet), key from env only.
- [ ] `alembic upgrade head` documented in README alongside run instructions.

## Out of scope for v1 (noted for later)

Email magic-link login, manual account linking/merging UI, admin tooling,
Postgres migration (do this before real launch traffic), push-notification
identity (care scheduling will need device tokens per user), and web login
for the marketing site's Community Garden (`gg_gardener_id` cookie stays
separate for now — merge later via a "claim your garden" flow).
