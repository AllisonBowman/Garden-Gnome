# PlantAdvocate 1.1.3: the product truth sheet

Written 2026-10-23 against the ship tip `3f6d7da` (branch
`claude/go-to-market-strategy-56bf52`, the same code as PR #22). Paths are
relative to the repository root. Where a line number is given it was read
today; where a file is still moving, the function is named instead.

Every piece of marketing copy, every post, pitch, caption and reply gets
checked against this sheet before it goes anywhere. Where this sheet quotes
exact wording, copy it as written. Where this sheet and a cited file
disagree, the file wins, and Allison should hear about the disagreement.
Nothing here has been run on a phone: the 1.1.3 build doesn't exist yet
(section 6), so some of these facts are facts about the code, not about an
app anyone has installed.

The two documents that already say what the app does in public words are
`docs/app-store/listing.md` (the App Store text) and the pages in `site/`.
Prefer their sentences to new ones. They were checked line by line against
the code, and new sentences haven't been.

## 1. What 1.1.3 does

### Sign-in and the account

PlantAdvocate signs in only with Sign in with Apple or Google. There is no
password, no email sign-up and no demo account (`mobile/src/auth/LoginScreen.tsx`,
`docs/app-store/review-notes.md:12-18`). Sign-in comes before anything else
in the app. A new account opens with one empty indoor growing area called My
Home (`review-notes.md:36`, `garden-gnome/app/routers/auth.py`, `_sign_in`).
The account and everything in it can be deleted from Settings > Account >
Delete account, which also asks Apple to revoke the sign-in
(`mobile/src/screens/SettingsScreen.tsx:95-114, 211-221`).

The listing says: "Sign in with Apple or Google; there is no password to
remember." and "You can delete your account, and everything in it, from
Settings." (`listing.md:119`). The login screen says: "Signing in creates
your account, so your plants, care log and growing areas follow you to a new
phone." (`mobile/src/auth/loginCopy.ts:10-11`).

The app needs its server for nearly everything, and the server sleeps when
idle, so the first request after a lull can take several seconds
(`review-notes.md:39`, `garden-gnome/fly.toml`).

### Growing areas

A growing area is a place someone grows: its surface, its size, indoors or
out, its sun, its shelter, and what the person wants from it
(`CONTEXT.md:86-95`). The surfaces are in-ground bed, raised bed, containers,
windowsill, shelf or floor, hanging basket, greenhouse bench and pond. The
three goals are "Something to eat", "Low upkeep" and "Feeds pollinators"
(`mobile/src/growingAreas/realEstate.ts:12-68`, labels at `:56`, `:61`, `:66`).
Measurements are optional, in square feet and inches (`realEstate.ts:163,
171`). A blank measurement counts as unknown, never as zero
(`GrowingAreasScreen.tsx:273-276`).

The listing's heading is **DESCRIBE WHERE YOU GROW**, and its key lines are
"Set up a growing area for each place you grow." and "Leave a measurement
blank and it counts as unknown. Nothing is recommended on a guess."
(`listing.md:95`). The What's New text says "A blank measurement counts as
unknown, never as 0." (`listing.md:161`). The first-run tips say "A
windowsill isn't a back bed." (`mobile/src/onboarding/slides.ts:27`).

Plants can move between a person's own growing areas and keep their whole
history (`README.md:150-153`; `site/community-garden.html`, "A plant can even
move between them and keep its full history intact").

### What suits each spot (the fit engine)

For every plant in a growing area, the server compares what the catalog
records for the species against the area, axis by axis: indoors or out, sun,
soil, space (footprint and headroom), upkeep and goals
(`garden-gnome/app/services/fit.py:76-83`). Each axis comes back as fits,
misfits or unknown, with a sentence and the name of the source behind it.
Unknown is never a pass (`CONTEXT.md:102-105`). Findings are worked out on
every request and never stored (`CONTEXT.md:97-100`).

The growing area page shows a **Needs addressing** card (only real misfits)
and a **Good candidates here** list (`mobile/src/screens/GrowingAreaDetailScreen.tsx:306,
352`). A candidate has nothing on record against the spot and at least one
thing confirmed for it (`fit.py`, `is_candidate`; `CONTEXT.md:112-119`). A
species a source rates as a serious or fatal poison for people, records as a
noxious weed, or tags as invasive is never put forward, except a food crop
whose eaten part is named, which appears with its hazard line
(`garden-gnome/app/services/toxicity.py:925-937`, `never_put_forward`;
handoff `docs/2026-10-16-app-store-finish-line-handoff.md:305-310, 341-345`).
The same check runs in Add plant before saving and on each plant's own page
(`AddPlantScreen.tsx:392-418`, `PlantDetailScreen.tsx:497`).

The listing's heading is **SEE WHAT SUITS IT**: "Each growing area lists
what needs addressing among its plants, with the reason and the source. A
shade fern in full sun is flagged. So is a climber that will outgrow a 7 ft
fence. Each area also puts forward good candidates: species with nothing on
record against that spot and at least 1 thing confirmed for it. You get the
same check before you save a new plant, and again on each plant's own page."
(`listing.md:98`). The subtitle is "What suits each spot you grow"
(`listing.md:40`). The real finding sentences, from a scratch sync, are "This
spot gets 6+ hours of direct sun; sources record it for part shade, full
shade." and "Outgrows this spot: climbs to 25 ft and there is 7 ft of
headroom" (`listing.md:238`).

The fit engine deliberately does not judge cold. It never says whether a
plant will survive a winter outdoors where you live, and there is no
hardiness-zone matching (`fit.py:41-49`, citing ADR 0006).

### The Species Almanac and species pages

The Species tab searches the catalog. Its top card opens the Species
Almanac, which can be narrowed to what fits one of your growing areas
(`SpeciesScreen.tsx:133-154`, `AlmanacScreen.tsx:242-271`). The Almanac's
Beginner, Intermediate and Fussy grades are worked out by PlantAdvocate from
each species' care facts. No source assigns them (`mobile/src/almanac/tier.ts:1-26`).
Species with nothing to grade are counted and left out of every grade
(`AlmanacScreen.tsx:278`).

Each species page shows facts such as light, water, soil, temperature and
size, and a **Sources** card whose rows open the source's own page in
Safari (`SpeciesDetailScreen.tsx:147`, `components/CareFacts.tsx:106-124`).
It shows no cold hardiness: the Temperature row gives where cold damage
begins for 75 of the 999 researched records, which ADR 0006 says is not a
survival floor, and the Cold row reads a field no researched record holds
(`mobile/src/care/facts.ts`; `fit.py:41-49`). This sheet and the listing
said "cold hardiness" until 2026-10-30.
The status line reads like "Care facts cited to NC State Extension and 2
more" (`mobile/src/care/facts.ts:331-335`). A value borrowed from the genus
wears a "genus-inferred" pill, and older values no claim backs sit under
"From the catalog — not yet cited" (`facts.ts:44-52`).

The listing's heading is **MORE THAN 990 SPECIES, WITH SOURCES**: "The
Species Almanac covers houseplants, herbs, vegetables, perennials, shrubs,
trees, bulbs and climbers. Narrow it to what fits a growing area of yours.
Each species page shows facts such as light, water, soil, temperature and
size, and lists where they came from. A fact borrowed from the plant's
genus is labelled as borrowed. Anything not yet cited says so. The check
schedules that reminders follow were written by PlantAdvocate for 129 common
plants and are not cited." (`listing.md:101`). The screenshot caption is
"Each cited fact names the source behind it." and the reason it says "each
cited fact" rather than "every fact" is written down at
`docs/app-store/screenshots.md:150-153`.

Settings credits older data: "Species data provided in part by Perenual
(perenual.com)." (`SettingsScreen.tsx:417`).

Since 2026-10-30 a "Report a fact" link sits at the foot of each species
page's Sources card, or in the same spot when a species has no sources yet.
It opens a prefilled email to support naming the species and listing the
facts the page shows (`mobile/src/components/ReportFact.tsx`,
`mobile/src/care/factReport.ts`).

### Hazards and edibility

Where a cited source records a plant as harmful to people or pets, the
species page says so in plain sentences, with the source's severity rating
for people where it gives one, and the parts where the source names them. A
severity word such as "Seriously" belongs to people only, because NC State's
Poison Severity rating is a rating for people (`CONTEXT.md:42-49`;
`toxicity.py`, `describe`). Where people are at risk, the note ends with
"If you suspect poisoning, call Poison Control (US 1-800-222-1222) or your
local poison centre right away", or "Poison Control (US 1-800-222-1222),
your local poison centre or a vet" where animals are named too; the local
poison centre was added on 2026-10-30 (`toxicity.py`, `LOCAL_POISON_CENTRE`).
Where a source's claim settled the pet verdict, the note names it: "For
pets, the source is NC State Extension." And words that come from the
code's own tables rather than a cited passage, such as the arum family's
calcium oxalate wording, follow as "PlantAdvocate's own summary: ..."
(both 2026-10-30; `toxicity.py`, `_pets_source`, `_summary_sentence`). A
plant is shown as edible only with its source's conditions
(`toxicity.py`, `edibility_note`).

Where nothing is recorded, the app says so and never calls the plant safe:
"No toxicity is recorded for {plant} in our sources yet. That is not a
guarantee of safety — keep it away from pets that chew plants." and, where a
source does record no toxicity to pets, "{Source} records no toxicity to
pets for {plant}. That is not a guarantee of safety"
(`toxicity.py:843-860`).

Under each hazard note, on species pages, plant pages and Add plant, the app
says "These notes repeat what the sources publish. They are not medical or
veterinary advice." That line was added on 2026-10-30
(`mobile/src/care/notAdvice.ts`); before then it was in the listing and the
review notes but on no app screen.

The listing's heading is **HAZARDS, STATED PLAINLY**: "If a source records a
plant as harmful to people or pets, its page says so, gives the source's
severity rating for people where it has one, and names the parts where the
source does. A plant is shown as edible only with the conditions its source
gives. Under each hazard note, the app says: These notes repeat what the
sources publish. They are not medical or veterinary advice." (`listing.md`,
HAZARDS, STATED PLAINLY). The opening paragraph ends "Where
there is no record, PlantAdvocate says so. A missing record is never treated
as safe." (`listing.md:92`). The FAQ says "no record never means safe" and
"The app is not a substitute for a vet, a doctor or poison control."
(`site/faq.html:265`).

Most hazard sentences name no parts, because most sources don't
(`listing.md:84-88`), so never promise that a page names the poisonous part.

### Checks, reminders and the care log

The app schedules checks, not chores: it says when a plant is worth a look,
not when to water it (`CONTEXT.md:67-75`; `site/faq.html:257`). A watering
check on the **Checks for today** card asks you to feel the soil, then tap
**Watered** or **Still damp**, and either keeps your streak
(`mobile/src/care/CareTodos.tsx:148, 219-244`). Nothing is called overdue
inside its care window (`mobile/src/care/schedule.ts:133-150`). Repotting is
a February look at the roots, ending Repotted, Top-dressed or All fine, and
the setting is called "Spring repot check" (`notifications/plan.ts:55-60`,
`SettingsScreen.tsx:37`). Feeding reminders run March to October and rest
November to February (`plan.ts:29-31`). Reminders are local notifications,
optional and set per care type (`notifications/reminders.ts:191`).

Reminders exist only for species that have a check schedule, and 129 species
do (`plan.ts:154-157`; `garden-gnome/app/data/species_catalog.json`, 129
entries). For a plant without one, the Checks for today card says it is left
out, and "All caught up" doesn't appear while one is (`CareTodos.tsx:121-128`).

"Let weather adjust watering" is a Settings switch: "Nudges watering
reminders by a day or two for outdoor, unsheltered plants — later before
rain, sooner in a heat spike. Needs a location on the growing area."
(`SettingsScreen.tsx:323-335`).

Care can be logged with a tap, and each plant keeps a timeline. Six badges
mark a person's own record: First Sprout, Plant Parent, Green Thumb,
Botanist, Consistent Carer and Century Club (`mobile/src/streaks/streaks.ts:196-214`).
There is no ranking or competition between people (`docs/app-store/age-rating.md:71`).

The listing's heading is **CHECKS, NOT CHORES**: "When a plant comes due,
feel the soil, then tap Watered or Still damp. Either keeps your streak.
Nothing is called overdue while it is still inside its care window.
Repotting is a look at the roots once a year, in February. Feeding reminders
rest from November to February. Reminders are optional and set per care
type. They follow a species' care window wherever the catalog holds a
schedule for it, and can move an outdoor watering reminder by 1 or 2 days
around rain and heat." (`listing.md:107`). The caption is "A check, not a
chore: look, then log." (`screenshots.md:141`).

### Walk the garden

From the Plants tab, Walk the garden takes a typed or spoken description of
what's planted, splits it into plants with counts and spots, and asks you to
confirm each one before adding them all (`CaptureGardenScreen.tsx:256-346`).
Speech goes through Apple's Speech framework, on the phone where it can and
otherwise on Apple's servers, and the screen says which: "Listening — say
what's planted. Nothing leaves your phone." or "Listening — this device sends
audio to Apple to transcribe it." (`CaptureGardenScreen.tsx:144-145`).
PlantAdvocate never receives the audio or the transcript, only the plants
you confirm (`docs/app-store/app-privacy.md:68`). The camera is only a
backdrop and isn't recorded (`CaptureGardenScreen.tsx:27-34`).

The listing's heading is **WALK THE GARDEN**: "Add plants by hand, or walk
your garden and say what's there: "12 tomatoes along the south fence, a
rosemary by the gate." Type it or dictate it, confirm each plant, and add
them all at once." (`listing.md:110`). The caption is "Walk the garden and
say what is growing." (`screenshots.md:206`).

### Photo matching (Apple Intelligence iPhones only)

In Add plant, Take photo and Choose photo appear only where Apple
Intelligence is available and turned on, which means iOS 26 or later on
hardware Apple supports (`modules/plant-id/ios/PlantIdModule.swift:78-89`;
`AddPlantScreen.tsx:136-140`). The handoff's phone test names an iPhone 15
Pro or newer (`handoff:978-985`). The phone's own model reads the photo, the
photo is never uploaded, and the suggestions are limited to species in the
catalog, with nothing pre-selected: "Suggested from the photo. Tap the one
that matches, and check it's right before you save."
(`mobile/src/photoId/copy.ts:13`; `photoId/identify.ts:56-117`). On other
phones the buttons are absent by design and search works instead
(`review-notes.md:52`). No accuracy figure has ever been measured.

The listing says: "On iPhones with Apple Intelligence, Add plant can also
suggest likely matches from a photo. The photo is read on your phone and
never uploaded, and you confirm the species before you save."
(`listing.md:110`). The pricing page says: "Identify a plant from a photo,
on your phone (iPhones with Apple Intelligence)" (`site/pricing.html`).

### Ask the Gnome

On any plant, Get care advice returns advice built on the server, by fixed
rules, from the species' facts and that plant's own care log. It carries a
"rule-based" pill (`mobile/src/care/resultLabels.ts:12-13`;
`site/privacy.html`, AI Processing, "Care advice is built on our server, by
fixed rules"). On iPhones with Apple Intelligence, the phone rewrites the
same advice in the Gnome's voice and the pill reads "rule-based • gnome
voice". A drift guard throws the rewrite away and shows the plain text if
the rewrite adds or changes any number or care action, and hazard lines are
never rewritten (`mobile/src/gnomeVoice/persona.ts:1-20`,
`gnomeVoice/restyle.ts:1-10`). Each result has a "Report this result" link
that opens a prefilled email (`components/ReportResult.tsx:35`).

The listing's heading is **ASK THE GNOME**: "On any plant, the Gnome gives
care advice built from its species' facts and that plant's own care log. On
iPhones with Apple Intelligence, the Gnome can say it in its own voice,
worked out on your phone, without changing the facts." (`listing.md:113`).
The homepage specimen shows a real advice line: "💧 Watering: logged 8 days
ago, inside the 7–12 day window. Check, and act only if it's needed."
(`site/index.html:314`).

### Local weather

Give a growing area a place, typed or from "Use my location", and it gets a
local forecast (`GrowingAreaDetailScreen.tsx:456-538`). The server asks
Apple Weather first, then the U.S. National Weather Service, then
Open-Meteo, and credits whichever answered under the forecast
(`garden-gnome/app/services/weather.py:376-396`,
`components/WeatherCredit.tsx`). Location permission is "when in use" only,
asked on tap (`mobile/app.json:142-145`).

Apple's WeatherKit has refused PlantAdvocate's requests since July, ruled an
Apple-side fault, so in practice forecasts have come from the National
Weather Service in the US and Open-Meteo elsewhere
(`docs/2026-07-30-weatherkit-401-closed.md:1-25`). Never write "powered by
Apple Weather".

The listing's heading is **LOCAL WEATHER**: "Give a growing area a place and
it gets a local forecast, with what the weather means for that spot."
(`listing.md:116`).

### The Census tab and the community census

The Census tab is a summary of your own garden and a way into the Almanac
(`CensusScreen.tsx:50-102`). The community census is a separate switch,
"Join the community census", in Settings > Privacy & data, off by default
(`mobile/src/consent/copy.ts:266-277`; `garden-gnome/app/models/models.py:268`).
Section 5 says exactly what it counts. Nothing in the app lets anyone see
another person's garden.

### Settings, themes and support

Settings has reminders per care type, the weather switch, a privacy summary
that lists where each kind of data goes, the census switch, support links,
Sign out and Delete account (`SettingsScreen.tsx:150-167, 296-405`). There
are two themes: "Almanac is the warm field-notebook look; Observatory is a
dark, colorblind-safe night theme." (`SettingsScreen.tsx:241-242`; the
accents are the Okabe-Ito palette, `mobile/src/theme/tokens.ts:4`). The app
picks its theme from this switch, not from the phone's dark mode
(`mobile/app.json:8`).

### Price

PlantAdvocate is free, with no ads, no in-app purchases and no
subscriptions. There is no purchase library in `mobile/package.json`
(`listing.md:205-207`). The listing's heading is **FREE, WITH NO ADS**:
"PlantAdvocate is free, with no ads and no in-app purchases."
(`listing.md:119`). The pricing page's rule is "Care that keeps a plant
alive is never behind a paywall." and "If that ever changes, the care that
keeps a plant alive — cited species facts, care logging and check reminders
— stays free." (`site/pricing.html:279`).

## 2. What it does not do, and must never be claimed

Each of these is a claim a marketer will reach for. Each is false today, or
true only with a condition the claim drops.

| Tempting claim | What is true | Say instead |
|---|---|---|
| "Identify any plant from a photo", "plant ID app", "snap to identify" | Photo matching exists only on iPhones with Apple Intelligence (iOS 26 or later, turned on). It suggests catalog species to confirm and has no measured accuracy. "identify" was kept out of the keywords on purpose (`listing.md:142-144`) | "On iPhones with Apple Intelligence, Add plant can also suggest likely matches from a photo." |
| "Every fact cited", "fully cited", "100% sourced" | Researched facts are cited. Older imported values are labelled "From the catalog — not yet cited", and the check schedules for 129 common plants were written by PlantAdvocate and are not cited (`listing.md:101`; `README.md:29-31`). The live homepage still says "EVERY FACT CITED" and is being replaced for exactly this reason (section 6) | "Each cited fact names the source behind it." or "care facts cited to the sources that published them" |
| "Verified", "vetted", "botanist-verified", "fact-checked" | `CONTEXT.md:51-54` bans "verified" for care data; the app says "cited" and "borrowed", never "verified" (`facts.ts:10-12`). Nobody outside PlantAdvocate has checked the catalog | "cited", "researched", "names its sources" |
| "Expert-approved", "recommended by NC State", "backed by the RHS", "in partnership with" | No organization has reviewed, endorsed or partnered with PlantAdvocate (`listing.md:121`) | Name the organization as a source, with the independence line (section 4) |
| "AI plant doctor", "diagnose your plant", "AI symptom checker", "photo check-up" | Photo check-ups and reading typed symptoms are built but switched off; production's `/ai/status` reported every backend `stub` and vision `ready: false` on 2026-10-23, and the app hides both (`mobile/src/care/aiCapabilities.ts:45-55`). The listing says nothing about them on purpose (`listing.md:125-129`) | Nothing. Leave them out until Allison switches them on, updates App Privacy and ships consent (`app-privacy.md:136-150`) |
| "AI-powered care advice", "AI gardener", "ChatGPT for plants" | Care advice is rule-based, on the server (`site/privacy.html`, AI Processing). The only AI in 1.1.3 runs on the phone: photo suggestions and the Gnome's wording, on Apple Intelligence iPhones. House rule: "care engine", not "AI" (`docs/plantadvocate-alignment-plan.md:30-31`) | "Its advice is never made up on the spot." (`listing.md:92`) |
| "Safe for pets", "pet-safe plants", "non-toxic", "child-safe" for any plant | The app never calls a plant safe. No record reads as unknown, and even a source's "no toxicity to pets" reads "not a guarantee of safety" (`toxicity.py:843-860`) | "A missing record is never treated as safe." |
| "Tells you if a plant is safe to eat", "foraging", "medical guidance", "what to do if your dog eats it" | Hazard notes repeat sources and point to Poison Control or a vet. They are not medical or veterinary advice, and the age rating answers Medical "None" on that basis (`listing.md:104`; `age-rating.md:40`). Support says "Never rely on it to decide whether a plant is safe to eat or touch." | "These notes repeat what the sources publish. They are not medical or veterinary advice." |
| "Android", "coming to Android", "Google Play" | iPhone only. Android code exists in the repo and the in-app privacy text mentions Gemini Nano on Android (`consent/copy.ts:126`), but no Android app is planned in any doc | "PlantAdvocate is an iPhone app." |
| "iPad app", "Mac app", "Vision Pro" | `ios.supportsTablet` is false. On iPad it runs as an iPhone app in an iPhone-shaped window (`listing.md:183`; `app.json:10`; handoff `:986-987`). Nothing says Mac | "iPhone only" |
| "Works offline" | Sign-in is required, the catalog and advice come from the server, and a screen can say it couldn't reach the server (`review-notes.md:39`) | Say nothing about offline |
| "Reminders for every plant", "smart watering schedule for 990 species" | Reminders exist only for species with a check schedule: 129 of them, written by PlantAdvocate, not cited (`plan.ts:154-157`; `listing.md:101`) | "They follow a species' care window wherever the catalog holds a schedule for it" |
| "Tells you when to water" | It schedules checks: feel the soil, then Watered or Still damp (`site/faq.html:257`) | "it tells you when to look at a plant, not when to water it" |
| "Matched to your hardiness zone", "will it survive your winter", "shows cold hardiness" | The fit engine deliberately doesn't judge cold (`fit.py:41-49`), and no species page shows a survival floor: the Temperature row gives where cold damage begins, for some species | "Each species page shows facts such as light, water, soil, temperature and size" |
| "Only recommends safe plants", "guaranteed to thrive", "the perfect plant for any spot" | Candidates can carry hazard lines (potato, tomatillo, lily of the valley can appear), and a candidate needs only one confirmed fit (`handoff:196-212, 305-310`) | "good candidates: species with nothing on record against that spot and at least 1 thing confirmed for it" |
| "Expert difficulty ratings" | Beginner, Intermediate and Fussy are PlantAdvocate's own calculation (`almanac/tier.ts:1-26`) | "an Almanac you can narrow to what fits a growing area" |
| "Powered by Apple Weather" | WeatherKit has refused requests since July; NWS or Open-Meteo answer (`docs/2026-07-30-weatherkit-401-closed.md`) | "a local forecast", with the credit the app shows |
| "Anonymous census", "anonymized data" | The policy promises only that no identifier links two exports, and says someone who knew your city and exactly what you grow could in principle recognize your garden (`site/privacy.html`, Community census; `consent/copy.ts:112-116`). The login footer's "anonymized census" (`LoginScreen.tsx:113`) goes further than the policy | "off unless you turn it on", "with no name, email, notes, exact dates or coordinates" |
| "Join a community of gardeners", "share your garden" | No social features, no user-generated content shown to others, no messaging (`age-rating.md:22-25`) | Don't describe the census as a community you join |
| "Free forever" | The pricing page promises that if anything ever costs money, the care that keeps a plant alive stays free. It doesn't promise everything stays free (`site/pricing.html:279`) | "Free, with no ads and no in-app purchases." |
| "Metric", "made for UK gardens" | Measurements are in feet, inches and °F (`realEstate.ts:163, 171`; `facts.ts:253`), the hazard number is US Poison Control (since 2026-10-30 with "or your local poison centre" after it), and the app is in English only (no localization in `mobile/src`) | Name the RHS as a source, not as a market |
| "Thousands of species", "about 1,000 species", "nearly 2,000 plants" | The safe figure is "more than 990" researched species. Production also lists about 1,900 older uncited rows, but "more than 990" counts researched species, not rows (`listing.md:13-21`; `handoff:234-239`) | "More than 990 species" |
| "Nursery partners", "conservation partners" | The nursery program doesn't exist ("None of this exists yet", `site/nurseries.html:256`), and the conservation page "reflects intentions, not active partnerships yet" (`site/conservation.html:248`) | Describe them as plans, or leave them out |

No testimonials, user counts, ratings, reviews, download figures, press
quotes or awards exist. The placeholder testimonials page was deleted on
2026-10-16 (`site/README-SITE.md:38-44`). Until the App Store shows real
ratings, nothing about popularity can be said at all.

## 3. Numbers that may be quoted

These come from `listing.md` and the code. Quote them in these words, and
only these.

| Number | Exact safe wording | Where it comes from |
|---|---|---|
| Species | "More than 990 species, with care facts cited to the sources that published them." (promotional text, `listing.md:78`) | 134 files in `garden-gnome/app/data/verified/` hold 999 records; 4 are genus-level and never become rows, leaving 995 researched species (`listing.md:13-21`; recounted today). Never round up to 1,000 |
| Check schedules | "The check schedules that reminders follow were written by PlantAdvocate for 129 common plants and are not cited." (`listing.md:101`) | `garden-gnome/app/data/species_catalog.json`, 129 entries, each with schedules. Always say they are not cited |
| Sources, short form | "such as NC State Extension, the Royal Horticultural Society and Missouri Botanical Garden" (`listing.md:92`) | The three most-cited authorities in `verified/*.json`: by URL count today, NC State about 13,700, RHS about 4,800, Missouri Botanical Garden about 2,300 |
| Sources, full list | "NC State Extension, the Royal Horticultural Society, Missouri Botanical Garden, and the Clemson, UF/IFAS, UGA, Penn State and University of Maryland extension services" (`site/faq.html`) | `garden-gnome/app/data/claims/authorities.py:52-80`. Eight organizations are cited |
| Fence example | "a climber that will outgrow a 7 ft fence" (`listing.md:98`) | Chinese Wisteria under 84 in of headroom: "climbs to 25 ft and there is 7 ft of headroom" (`listing.md:238`) |
| Weather nudge | "can move an outdoor watering reminder by 1 or 2 days around rain and heat" (`listing.md:107`) | `SettingsScreen.tsx:323-335` |
| Repot check | "once a year, in February" with "3 endings: Repotted, Top-dressed or All fine" (`listing.md:107, 173`) | `notifications/plan.ts:55-60` |
| Feeding rest | "Feeding reminders rest from November to February." (`listing.md:107`) | `plan.ts:29-31` |
| Candidate rule | "at least 1 thing confirmed for it" (`listing.md:98`) | `fit.py`, `is_candidate` |
| Walk the garden example | "12 tomatoes along the south fence, a rosemary by the gate" (`listing.md:110`) | Gives 2 confident matches on a scratch catalog (`review-notes.md:82`) |
| Price | "free, with no ads and no in-app purchases" / "$0" (`listing.md:119`; `site/pricing.html`) | No purchase library in `mobile/package.json` |
| Weather services | 3: Apple Weather, the U.S. National Weather Service, Open-Meteo (`site/privacy.html`) | `weather.py:376-396` |
| Retention | "up to 5 days" for hosting snapshots; "up to 30 days" for an encrypted Apple sign-in grant awaiting revoke (`site/privacy.html`, Keeping and Deleting) | Fly default retention, not yet confirmed (`handoff:298-301`); `auth.py`, `delete_me` |
| Age rating | Expected 4+, not yet assigned (`age-rating.md:7`) | Only App Store Connect assigns it |
| Support reply time | "usually within 2 business days" (`site/contact.html:254`) | Allison's own published promise. Never make it faster |

Never quote these, even though they appear in internal docs: the 10,681
claims (a claim is one citation's value for one field, not a distinct fact,
`CONTEXT.md:12-15`); the 997 or 995 row counts; the roughly 1,900 uncited
production rows; production's total species count, which nobody knows until
the deploy; the 378 species with a hazard line or the 30 that name parts;
test counts; any tester count; any accuracy figure for photo matching,
since none exists.

## 4. Naming the cited organizations without implying endorsement

The independence line is the last sentence of the App Store description,
and when this sheet was written it was the only place it appeared:

> PlantAdvocate is independent. The organizations it cites have not reviewed or endorsed it.

(`docs/app-store/listing.md`, the description's last line). On 2026-10-23 no
page in `site/` carried it. Since the 2026-10-30 site fixes, the home page,
About, the FAQ and Plant resources do, live with step 3. Any
piece of copy that names an organization should carry that line, word for
word, wherever the format allows it: a blog post, a press note, a pitch, a
video description. Where it can't fit, a social post for instance, name the
organization only as a source of facts, in the listing's pattern: "Care
facts come from the organizations that publish them, such as NC State
Extension, the Royal Horticultural Society and Missouri Botanical Garden,
and each species page names its sources." (`listing.md:92`).

Organizations are named as publishers whose facts the app cites with
attribution. Their words stay on the server and never reach the app
(`authorities.py:21-27`, ADR 0003). So never write "data from NC State" in a
way that suggests a data feed or a licence, and never quote a source's prose
in marketing. Never use an organization's logo, seal or typeface. Never
write "partnered with", "in collaboration with", "trusted by", "approved
by", "recommended by" or "as used by". Never pitch an organization as if it
might promote the app because it is cited.

Use the names exactly as the app writes them (`authorities.py:52-80`): NC
State Extension, Royal Horticultural Society, Missouri Botanical Garden,
Clemson Cooperative Extension, UF/IFAS Extension, Penn State Extension,
University of Maryland Extension, UGA Cooperative Extension. The USDA PLANTS
Database is registered but cited by nothing in the catalog today (no
`plants.usda.gov` URL in `verified/*.json`), so don't name it. Perenual is
credited in Settings as a partial data source for older rows
(`SettingsScreen.tsx:417`); it is not one of the cited organizations, and
its rows are the ones labelled not yet cited.

The site's resources page describes each organization ("the source behind
most of the catalog's citations", `site/resources.html`), and that is fine
as description. The about page's "Modeled on how botanical institutions keep
their collections" (`site/about.html:291`) is an analogy. Don't stretch it
into a connection with any institution.

## 5. Privacy facts a marketer could touch

These are stated exactly, from `docs/app-store/app-privacy.md` and the
binding policy, `site/privacy.html` (`README.md:138-141`).

No ads, no tracking, no analytics. The policy's short version is:
"PlantAdvocate is free. It has no ads, no tracking, no analytics or
crash-reporting software, no in-app purchases and no subscriptions. We
don't sell your data, and we don't share it with advertisers or data
brokers." The code agrees. `mobile/package.json` has no analytics, ad,
crash-reporting or attribution SDK, and a grep of `mobile/src`, `modules`
and the configs for Sentry, Firebase, Amplitude, Mixpanel, Segment,
Crashlytics, Bugsnag, PostHog, AppsFlyer, Facebook and AdMob found nothing
today. The privacy manifest sets `NSPrivacyTracking` false with no tracking
domains (`mobile/app.json:14-16`). The one third-party SDK that touches
personal data is Google Sign-In, and it only signs in (`app-privacy.md:105-108`).
There is no advertising ID, vendor ID or push token; reminders are local
notifications (`app-privacy.md:72`).

What the App Store label will say: "Data Linked to You: Contact Info,
Identifiers, Location, User Content", and nothing under "Data Used to Track
You" (`app-privacy.md:78-84`). The seven collected types are name, email
address, user ID, precise location (an optional growing area's
coordinates), coarse location (its city, region and country), customer
support messages, and other user content (plants, notes, care logs, growing
areas) (`app-privacy.md:41-49`).

What never leaves the phone: the photo used for photo matching ("The photo
is read on your phone and never uploaded", `consent/copy.ts:123`); search
terms ("Species search filters the list already on the phone",
`app-privacy.md:71`); care reminders. PlantAdvocate never receives Walk the
garden's audio or transcript, only the plants you confirm. Apple may
transcribe speech on its own servers when the phone can't
(`app-privacy.md:68`).

What goes to other companies: Fly.io hosts the server and stores data in the
United States, encrypted at rest. Apple and Google confirm sign-in. Apple
Weather, the U.S. National Weather Service and Open-Meteo receive a growing
area's coordinates, rounded to about a kilometer. Cloudflare serves the
website (`site/privacy.html`, Data Sharing). Today no feature sends anything
to Anthropic or any other outside AI service. The policy already says
Anthropic would read photo check-ups and typed questions once those are
switched on (`site/privacy.html`, AI Processing).

The community census is the only thing App Privacy counts as Analytics, and
it is off unless the person turns it on (`app-privacy.md:51-54`). In the
app's words, if someone joins, "Each of your plantings is counted: its
species, how many there are, its growth stage, the month you got it and how
it looked then (soil, leaves, any pests), how many times each kind of care
was logged in each month, how many growing areas it has been in and the
months it moved between them, which planting it was split from if it was,
and its growing area's type, city, region and country. There is no name, no
email, no nicknames, no notes, no exact dates and no coordinates."
(`consent/copy.ts:96-106, 266-270`). The promise has a stated limit: "Each
planting and growing area gets a new label in every export, and the records
are shuffled, so no identifier links one export to another. That is the
promise, and no more: a planting's monthly care counts could still look
alike from one export to the next." (`consent/copy.ts:112-116`). Only
PlantAdvocate can export it, the routes answer 404 to everyone while no
operator token is set, and it goes to no other organization
(`app-privacy.md:154-167`; `handoff:176-180`). Its purpose, in the policy,
is "to improve care advice for everyone". Never call it anonymous, and never
say census data is shared with researchers.

Two promises bind marketing directly. First, the policy says of account
information: "We use account information only to run the App. We never use
it for marketing or advertising, and we don't send marketing email."
(`site/privacy.html:138`). The 2026-10-30 site fixes narrowed its last part
on the ship branch, live with step 3, to: "We never use it for marketing or
advertising, and we never add the address you sign in with to a mailing
list. We send news about PlantAdvocate, such as its launch, only to people
who asked for it, like those on the early-access list described under "This
Website" below." Either way, the email addresses of people who sign in can
never be used for a newsletter, a launch announcement or a survey. Second,
the early-access list: "If you joined our early-access list on an earlier
version of this site, we use that address only to tell you about
PlantAdvocate, and we'll remove it if you ask." (`site/privacy.html:187`).
Since the same fixes it goes on to say that a removed address leaves only a
one-way fingerprint, used only to keep that address off anything sent to
the list. A launch note to that list fits the promise; anything not about
PlantAdvocate doesn't, and an unsubscribe request has to be honoured.

The website's own promise is "plantadvocate.ai has no analytics, ads or
tracking." Cloudflare may set a cookie to protect the site, the fonts come
from Google Fonts, and the community garden demo keeps its plots in the
visitor's browser (`site/privacy.html:187`). Adding an analytics script, an
ad pixel or a tracking link service to the site, or any SDK to the app,
would make these sentences false. The rule in `site/README-SITE.md:164-172`
applies: change `privacy.html`, its effective date and its "What changed"
line in the same change, before the new thing goes live.

PlantAdvocate "is not directed at children under 13" (`site/privacy.html`,
Children's Privacy), and the listing answers Made for Kids "No"
(`age-rating.md:76-77`). Don't market to children.

## 6. Status facts, with dates

| Date | Fact | Source |
|---|---|---|
| Before 2026-07-30 | TestFlight builds 3 to 11, under versions 1.0.0 and 1.0.1 | `docs/2026-07-30-ship-1.1.0-testflight.md:40` |
| About 2026-07-30 | 1.1.0 (build 12) to TestFlight, never given notes, superseded by 1.1.1. The date is that of its ship doc | `docs/2026-08-01-testflight-1.1.1-notes.md:3-5` |
| About 2026-08-01 | 1.1.1 (build 13) to TestFlight: Walk the garden and its microphone prompts | `docs/2026-08-01-testflight-1.1.1-notes.md` |
| 2026-08-02 | 1.1.2 (build 15), the newest TestFlight build, to internal testers only | `docs/2026-08-02-testflight-1.1.2-notes.md`; `docs/2026-09-03-ios-debugging-handoff.md:27-34` |
| 2026-10-20 | The 1.1.3 production build was attempted from the Mac and stopped at Apple's certificate check. It needs Allison's Apple sign-in, and will come out as build 17 or higher | `handoff:15-39` |
| 2026-10-23 | PR #22 (the ship branch) is open with CI green, per the orchestrator; not re-checked here | orchestrator context |
| 2026-10-23 | Not on the App Store. The iTunes Lookup API returns no result for app id 6792203800, and a search for "PlantAdvocate" finds nothing. Never submitted to App Review | checked today; `handoff:110-111` |
| 2026-10-23 | Production still runs the old backend: `GET /` answers version 0.2.0 with no catalog block, `openapi.json` has 29 paths and none under `/growing-areas`, and `/ai/status` reports every backend `stub` with vision `ready: false` | checked today against `https://garden-gnome-api.fly.dev` |
| 2026-10-30 | The go-to-market branch is folded into `care-advice-honesty` at `b6fee6b`. That day's changes land on top: curated care notes without safety claims, the boot-time refresh of curated prose, the three hazard-sentence changes, the not-advice line and the Report a fact link in the app, and the site fixes. The live site still serves the October 16 rewrite. The 1.1.3 build has still not been started | `docs/2026-10-16-app-store-finish-line-handoff.md`, "Update, 2026-10-30" |
| Launch day L | Allison releases manually after approval, which is the recommended setting | `handoff:855-856` |

The store name is "PlantAdvocate: Garden Care", or "PlantAdvocate" if that
name is taken (`listing.md:28-34`). Until App Store Connect accepts it,
write "PlantAdvocate" alone. The store link will be
`https://apps.apple.com/app/id6792203800`, but don't publish it until it
answers after release. Territory availability is still a choice: the
listing says Free "in every territory" (`listing.md:205`), and the handoff
raises US-only as an alternative, because the Poison Control number in
hazard notes is American (`handoff:264-268`).

### The live site versus `site/`

The live site at https://plantadvocate.ai is no longer the July 17 build.
Read today, its index, pricing, support, privacy, FAQ, how-it-works and
about pages match `site/` as it stood at `307930e` (2026-10-19), apart from
Cloudflare's email obfuscation. Someone deployed the October 16 rewrite after
the handoff's 2026-10-20 note, which still described July pages
(`handoff:52-53`). So the subscription copy, Restore Purchases, the paid
tiers and the "we don't collect your precise location" line are already gone
from the live site.

What the live site still lacks is the 2026-10-20 work in commits `ce7f636`
and `a472101`. Four lines of the verification block in
`site/README-SITE.md:133-147` fail today:

| Page | Live today (`307930e`) | `site/` at the tip |
|---|---|---|
| index.html, hero | "NO GUESSWORK · EVERY FACT CITED · CHECKS, NOT CHORES" | "NO GUESSWORK · SOURCES NAMED · CHECKS, NOT CHORES" (`site/index.html:298`) |
| index.html, hero text | "grounded in a care catalog whose facts are cited" | "the catalog's researched facts are cited to the sources that published them" |
| index.html, specimen card | "You noted: Lower leaves yellowing", and a note in the plant's own voice. The app takes no symptom note in 1.1.3 | the real advice line, "💧 Watering: logged 8 days ago, inside the 7–12 day window. Check, and act only if it's needed." (`site/index.html:314`) |
| index.html, "Grounded in fact" | "every care fact is cited", "Every care recommendation is traceable to a specific, cited fact" | researched facts cited, older ones labelled, 129 schedules not cited (`site/index.html:379`) |
| faq, how-it-works, about, pricing, support | "every care value is cited" and similar | "researched" added, the 129 uncited schedules named |
| privacy.html | Effective October 16, 2026; census described before export 4.1; nothing about the 30-day Apple grant | Effective October 20, 2026; monthly care counts and fresh identifiers; the 30-day grant (`site/privacy.html:129`) |

So until `site/` is deployed again, the live homepage overclaims in exactly
the way section 2 forbids. Don't point anyone at the live homepage or FAQ
as proof of the citation claims until the check block prints all `ok`.

Both versions still say "PlantAdvocate is in beta on iPhone", "Join the
beta", "Get early access" and "Email us for early access"
(`site/index.html:284, 295, 394`). At launch these become the App Store
link, which is why the handoff recommends a manual release
(`handoff:295-297`).

The live homepage no longer posts to `/api/waitlist`; early access is a
mailto link. A GET of `/api/waitlist` serves the homepage today. Read-only
requests can't tell whether the old Pages Function still exists behind POST,
and nothing here tried one. Whatever it stored stays in Cloudflare's KV or
D1 until Allison exports it (`handoff:224-230`; `site/README-SITE.md:112-119`).
The old `testimonials.html` path now serves the homepage.

## 7. Voice

### The caretaker voice

The app and site speak to a caretaker: the person who does the care. The
domain words come from `CONTEXT.md`. Use "check", never "task" or "chore"
(`CONTEXT.md:67-71`). A check that ends in "looked, and it didn't need
doing" is a complete outcome, not a skipped one (`CONTEXT.md:73-75`). Use
"growing area", never "environment" (`CONTEXT.md:92-95`). Use "cited" and
"borrowed", never "verified" (`CONTEXT.md:51-54`). A climber "climbs to 25
ft", never "reaches 25 ft" (`CONTEXT.md:121-127`). Unknown is said out loud
and never passed off as fine. The leak scan's last line sums the voice up:
"Rewrite in caretaker voice." (`.claude/bin/leak-scan.sh`).

The site's register is calm and specific. It names what the app does, says
what it can't check, and admits what isn't built yet: "This is a short,
fixed list." (`site/recommendations.html:267`); "None of this exists yet"
(`site/nurseries.html:256`); "We'd rather list this as a direction we're
building toward than overstate a partnership that doesn't exist yet."
(`site/conservation.html`). The hard things are said plainly and early:
"Advice can still be wrong, so never rely on it to decide whether a plant is
safe to eat or touch." (`site/faq.html`).

### The Gnome

The product is PlantAdvocate. The Gnome (🧙) is its mascot and the voice of
its advice, as in "Ask the Gnome", and is never the product's name
(`README.md:5-8`). Never write "Garden Gnome" in public copy: the rebrand
audit forbids it, which is why the sign-off reads "— the Gnome 🧙" and not
"your Garden Gnome" (`mobile/src/gnomeVoice/persona.ts:23-27`;
`docs/plantadvocate-alignment-plan.md:30-31`). The `garden-gnome` names in
the repo, the Fly app and the API host are internal.

The persona contract (`persona.ts:33-50`) is "a warm, whimsical gnome who
lovingly watches over houseplants". It speaks to the caretaker as "you" and
refers to the plant by name. It observes, advises and celebrates. It never
waters, feeds, prunes or repots anything, and never says it did or will. It
never promises app behaviour such as reminders, writes no greeting or
signature, keeps every number in digits, and never softens a hazard. Hazard
lines are kept away from the model and appended word for word
(`persona.ts:17-20`). The login screen's line is "Plant care that knows what
it's talking about — with a gnome who never guesses." (`LoginScreen.tsx:55-57`).
The about page calls the Gnome "a small, stubborn advocate for the plant
that can't speak for itself" (`site/about.html`).

In marketing the Gnome can be the face, but never a character who does more
than the app does. It doesn't diagnose, guarantee, remember things the app
doesn't store, or speak for a plant beyond the facts. Most phones show the
advice in plain words; only Apple Intelligence iPhones get the Gnome's own
voice (`README.md:58-65`). So never promise that everyone hears the Gnome
talk.

### Do and don't, from the real copy

| Do (real copy) | Don't | Why |
|---|---|---|
| "Its advice is never made up on the spot." (`listing.md:92`) | "AI-powered plant care that knows everything" | The advice is rule-based, and the house rule is "care engine", not "AI" |
| "Each cited fact names the source behind it." (`screenshots.md:157`) | "Every fact cited", the line the live homepage still carries | Older values aren't cited yet, and neither are the 129 schedules |
| "Where there is no record, PlantAdvocate says so. A missing record is never treated as safe." (`listing.md:92`) | "Find pet-safe plants", or the recommendations page's "a safe bet for most rooms" about pothos (`site/recommendations.html:281`) | "Safe" next to a plant's name reads as a hazard verdict. Pothos is recorded as toxic to cats, dogs and people (`handoff:935-937`) |
| "A check, not a chore: look, then log." (`screenshots.md:141`) | "Never forget to water again!" | The app schedules looking, not watering, and only 129 species have schedules |
| "Nothing here contradicts the space. Plants the catalog can't judge aren't listed as fine — they're just not listed." (`GrowingAreaDetailScreen.tsx:325-326`) | "The perfect plant for every spot, guaranteed" | Unknown is never a pass, and a candidate needs only one confirmed fit |
| "On iPhones with Apple Intelligence, Add plant can also suggest likely matches from a photo." (`listing.md:110`) | "Snap a photo and know any plant instantly" | Most iPhones don't have the feature, and it only suggests catalog matches to confirm |
| "PlantAdvocate is independent. The organizations it cites have not reviewed or endorsed it." (`listing.md:121`) | "Backed by NC State and the RHS" | No organization has reviewed, endorsed or partnered with it |
| The Gnome "observes, advises, and celebrates" and signs "— the Gnome 🧙" (`persona.ts:27, 42-44`) | "Your Garden Gnome will water your ferns and remind you every morning!" | The Gnome never performs care or promises app behaviour, and "Garden Gnome" is banned in user-facing copy |
| "Couldn't load the care calendar just now — that isn't an all-clear." (`GrowingAreaDetailScreen.tsx:437`) | "Everything's fine!" for a screen that failed to load | A missing answer is never presented as a good one |
| "PlantAdvocate is free, with no ads and no in-app purchases." (`listing.md:119`) | "Free forever, no catch" | The pricing page promises only that the care that keeps a plant alive stays free if anything ever costs money |

### About Allison

Two pages carry everything published about Allison, and nothing may be
added to them. The privacy policy says "PlantAdvocate is operated by
Allison Bowman, a sole proprietor, based in the United States."
(`site/privacy.html:133`). The about page carries a first-person origin
story signed "— Allison Bowman, Founder": a first home, a garden, and
contradictory advice (`site/about.html:256-259`). Support says "Bug reports
and ideas go straight to the person who builds PlantAdvocate." The footer
reads "© 2026 PlantAdvocate · An Ocean Dweller Media project"
(`site/index.html:434`). Quote these as written. Don't add a city, a
profession, a team, a backstory or a description of Ocean Dweller Media.

## Loose ends found while writing this

None of these block marketing, but each is a place where public or in-app
copy says a little more than the code, and Allison may want to fix it.

The login footer says "the anonymized census is strictly opt-in"
(`mobile/src/auth/LoginScreen.tsx:113`), which goes further than the
policy's "no identifier links one export to another". "the census is off
unless you turn it on" would match.

No page on the site carries the independence line. The resources page,
which names all eight organizations, is the natural place for it. (Fixed on
the ship branch on 2026-10-30, on four pages, live with step 3.)

`site/about.html:272` says "Species data comes from vetted horticultural
sources", and `:282` says "Every piece of advice can be traced back to a
specific fact in the database". Settings credits Perenual for part of the
older data, and the 129 schedules aren't cited. "Traced to the catalog" is
true; "traced to a cited source" isn't always. `site/how-it-works.html:303`
("Every recommendation can point back to the specific fact") has the same
reach. (Fixed on the ship branch on 2026-10-30.)

`site/recommendations.html:281` calls pothos "a safe bet for most rooms".
It means light, but it puts "safe" beside a plant the app records as toxic.
(Fixed on the ship branch on 2026-10-30.)

The in-app privacy summary mentions "Gemini Nano on Android"
(`mobile/src/consent/copy.ts:126`), which an iPhone user will read in
Settings. (Still there on 2026-10-30, and so is the login footer's
"anonymized census" above.)

`site/README-SITE.md:49-50` says the policy's effective date "stays October
16", but `site/privacy.html:129` says October 20, and the verification block
checks for October 20. The handoff's phone check (`handoff:761-762`) also
says October 16. The file is right; the two notes are stale. (Both notes
were corrected on 2026-10-30.)
