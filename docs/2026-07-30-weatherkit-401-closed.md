# WeatherKit 401 — investigation closed, ball is with Apple

> **Status (2026-07-30): diagnosis complete. Nothing left to fix on our side.**
> Apple WeatherKit returns `401 {"reason": "NOT_ENABLED"}` for team
> `FK6E9XBY6Y` no matter what we send. The app now falls back to the U.S.
> National Weather Service, so environment weather works again without it.
> The only remaining action is an Apple Developer Support ticket (drafted at
> the bottom) — everything else has been tried and ruled out.

## What the app does now

`fetch_weather()` walks a provider chain and takes the first answer:

```
Apple WeatherKit  ->  U.S. National Weather Service  ->  Open-Meteo
```

NWS sits ahead of Open-Meteo because its data is public domain and
unrestricted for commercial use. It is US-only and supplies neither UV index
nor sunrise/sunset, so those fields come back `None` and the client hides
them — a real but acceptable content loss versus WeatherKit. Open-Meteo stays
last as the global net for coordinates NWS cannot serve. Each payload carries
its own attribution, so the on-screen credit always names whoever answered.

**If Apple ever fixes provisioning, WeatherKit resumes automatically** — it is
still first in the chain and needs no code change.

Two NWS specifics worth remembering, both learned the hard way:

- It returns **301** for coordinates with more than four decimal places.
  Geocoded environments carry more, so the request rounds to `%.4f`.
- It returns **403** without a descriptive `User-Agent`.

## What was ruled out (do not re-check these)

Every one of these was verified, not assumed:

| Suspect | Finding |
|---|---|
| JWT structure | **Correct.** Decoded the signed token in production: `alg ES256`, `kid`, `id FK6E9XBY6Y.<identifier>`, `iss FK6E9XBY6Y`, `sub <identifier>`, valid `iat`/`exp`. Apple parses it, then refuses the entitlement. |
| `sub` identifier | **Not the cause.** Tried the Services ID (`com.allisonbowman.plantadvocate.weather`) *and* the App ID (`com.allisonbowman.plantadvocate`). Identical `NOT_ENABLED` both times. |
| The signing key | **Not the cause.** Key `QR93DSP3U4` has the WeatherKit capability. Created a brand-new WeatherKit-only key `XZ6Q5TXP9L` (2026-07-30) — same `NOT_ENABLED`. `XZ6Q5TXP9L` is what is deployed now. |
| App ID capability | **Enabled and saved.** Confirmed in the portal with the Save button greyed out, i.e. no pending unsaved change. |
| Services ID | Exists, WeatherKit enabled. |
| License agreements | **Current.** Apple Developer Program License Agreement accepted 2026-07-06. No pending agreements. |
| Fly secrets | `WEATHERKIT_KEY_ID`, `WEATHERKIT_SERVICE_ID`, `WEATHERKIT_PRIVATE_KEY` all present and deployed. |

`NOT_ENABLED` means the token was accepted and the entitlement check then
failed — a provisioning state on Apple's side, not a configuration error here.

## Gotcha that cost an hour

```bash
flyctl secrets set WEATHERKIT_PRIVATE_KEY="$(cat wrong/path.p8)" -a garden-gnome-api
```

If the path is wrong, `cat` fails, `$( )` expands to an **empty string**, and
the secret is silently set to empty — while `flyctl` still reports "update
succeeded." Always guard first:

```bash
test -s ~/Downloads/AuthKey_XZ6Q5TXP9L.p8 && flyctl secrets set ...
```

The `.p8` is not on the Mac; it lives on the Windows box / was emailed. Never
paste key contents into a terminal argument, a chat, or this repo.

## The Apple Support ticket

File at **developer.apple.com/contact** → Development and Technical → WeatherKit.

> **Subject:** WeatherKit REST API returns 401 `{"reason":"NOT_ENABLED"}` despite fully correct, verified setup
>
> **Team ID:** FK6E9XBY6Y
>
> Every WeatherKit REST request returns `HTTP 401 {"reason": "NOT_ENABLED"}`. I have verified the entire setup, so this appears to be a server-side provisioning issue:
>
> - **App ID** `com.allisonbowman.plantadvocate` has the **WeatherKit** capability enabled and saved.
> - A dedicated **Services ID** `com.allisonbowman.plantadvocate.weather` exists.
> - **Two Auth Keys** carry the WeatherKit capability, including one created fresh: `QR93DSP3U4` (2026-07-23) and `XZ6Q5TXP9L` (2026-07-30). **Both** produce `NOT_ENABLED`.
> - Apple Developer Program License Agreement accepted 2026-07-06; membership active; no pending agreements.
> - The JWT is correct: ES256, header `{alg:ES256, kid:<keyID>, id:"FK6E9XBY6Y.<identifier>"}`, payload `{iss:"FK6E9XBY6Y", sub:"<identifier>", iat, exp}`. I confirmed the exact claims by decoding the signed token.
> - I tested `sub` as **both** the Services ID and the App ID/bundle ID — identical `NOT_ENABLED` for every key/identifier combination.
>
> **Example request:**
> `GET https://weatherkit.apple.com/api/v1/weather/en/38.98/-76.94?dataSets=currentWeather,forecastDaily`
> → `401 {"reason":"NOT_ENABLED"}`
>
> Since the token is structurally accepted and only the entitlement check fails, please enable/repair WeatherKit provisioning for this team and its keys.

## Optional cleanup

Key `QR93DSP3U4` can be revoked in the portal — `XZ6Q5TXP9L` is the deployed
one. Leave it until WeatherKit works, in case Apple asks about either.
