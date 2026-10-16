# Age rating for 1.1.3

App Store Connect > App Information > Age Rating. The questions are the
ones on Apple's "Age ratings values and definitions" page as it read on
15 October 2026. Answers are checked against the code at `b083a90`.

The expected result is **4+**. Nothing below is answered in a way that
raises it.

## In-App Controls

| Question | Answer | Why |
|---|---|---|
| Parental Controls | No | The app has no settings for a parent to restrict a child's use |
| Age Assurance | No | The app never asks or checks anyone's age |

## Capabilities

| Question | Answer | Why |
|---|---|---|
| Unrestricted Web Access | No | There is no in-app browser or web view. Source links, the weather credit and support links open in Safari (`mobile/src/components/CareFacts.tsx:115`, `components/WeatherCredit.tsx:39`, `support.ts:17-19`) |
| User-Generated Content | No | Nicknames, notes, care logs and growing areas are private to the account and are never shown to anyone else. The census, for people who join it, is counted by the operator. No one else ever sees it in the app (`garden-gnome/app/routers/census.py:34-84` serves only the caller's own summary) |
| Social Media | No | No feed, likes, follows or sharing |
| Social Media Disabled for Users Under 13 | No | There is no social media to disable |
| Messaging and Chat | No | People can't contact each other in the app. Support is an email to PlantAdvocate |
| Advertising | No | No ads and no ad SDK (`mobile/package.json`) |

## Mature Themes

| Question | Answer | Why |
|---|---|---|
| Profanity or Crude Humor | None | Plain, polite copy throughout. The Gnome's on-device voice is held to the facts and falls back to plain text if it strays (`mobile/src/gnomeVoice/restyle.ts`) |
| Horror/Fear Themes | None | |
| Alcohol, Tobacco, or Drug Use or References | None | The catalog has ornamental plants with "tobacco" in their names (Flowering Tobacco, Woodland Tobacco Plant). That is a plant's name, not a reference to smoking. A search of every name, and every seed care note, for alcohol, tobacco and drug words found nothing else |

## Medical or Wellness

| Question | Answer | Why |
|---|---|---|
| Medical or Treatment Information | None | The app is about plant care. Hazard notes say what a cited source records a plant can do to people or pets, and which parts. For a serious hazard they say to get help quickly (`garden-gnome/app/services/toxicity.py:302-307`). They don't diagnose, triage or give treatment steps. Photo check-ups of a plant are not offered in this version |
| Health or Wellness Topics | No | No diet, exercise or self-care content. "Something to eat" is a growing goal for what to plant (`mobile/src/growingAreas/realEstate.ts:53-58`), not dietary advice |

If App Review disagrees about the hazard notes, the alternative answer is
"Infrequent" for Medical or Treatment Information, and the rating becomes
13+. Ask App Review before choosing that. A gardening app rated 13+ for
warning people about foxglove would be a strange result.

## Sexuality or Nudity

| Question | Answer | Why |
|---|---|---|
| Mature or Suggestive Themes | None | |
| Sexual Content or Nudity | None | |
| Graphic Sexual Content and Nudity | None | |

## Violence

| Question | Answer | Why |
|---|---|---|
| Cartoon or Fantasy Violence | None | |
| Realistic Violence | None | |
| Prolonged Graphic or Sadistic Realistic Violence | None | |
| Guns or Other Weapons | None | The only blade is the scissors icon on the Pruned button (`mobile/src/screens/PlantDetailScreen.tsx:45`) |

## Chance-Based Activities

| Question | Answer | Why |
|---|---|---|
| Gambling | No | |
| Simulated Gambling | None | |
| Contests | None | Streak badges such as First Sprout and Green Thumb mark a person's own care record (`mobile/src/streaks/streaks.ts:200-215`). There is no event, ranking or competition between people. Even "Infrequent" would still give 4+ |
| Loot Boxes | No | |

## The rest of the page

Made for Kids: **No**. It isn't designed for children, and it requires an
account.

Age rating override: none. Leave the calculated 4+.
