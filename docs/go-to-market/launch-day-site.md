# The launch-day site

Written 2026-10-31 about branch `claude/launch-day-site`, the reviewed
launch-day edits to `site/`. The branch sits on the ship tip `2ac7b19` and
holds the six commits listed under "The commits". Nothing on it is deployed,
and nothing on it may be merged into `care-advice-honesty` or `master` or
deployed before launch morning, because every page on it says the app is on
the App Store. [launch-day-runbook.md](launch-day-runbook.md), "L: release
day", says when it merges and when the site deploys; this file says what it
changes, which of Apple's rules it follows, what was checked, and what comes
after.

The draft, `fa4076b` from 2026-10-26, was made by a lane that stopped before
its reviews. On 2026-10-30 a second lane rebased it onto the ship tip of that
morning and fixed what its honesty and wording passes found, then lost its
connection before writing this file or committing the README's new check
lines. On 2026-10-31 the branch was rebased onto `2ac7b19`, the README commit
was finished, the whole diff was read again against Apple's pages and
[product-truth.md](product-truth.md), and an adversarial review ran over it
(four lenses, every finding challenged by two refuters). The findings and
what was done about them are under "What was checked".

## What the branch changes

Every page, the 13 and the new press page:

- In the `head`, the Smart App Banner tag,
  `<meta name="apple-itunes-app" content="app-id=6792203800">`, and Open
  Graph and Twitter tags: `og:type` website, `og:site_name`, `og:title` and
  `twitter:title` equal to the page's `<title>`, `og:description` and
  `twitter:description` equal to the page's `<meta name="description">`,
  `og:url` the page's extensionless address (`https://plantadvocate.ai/` for
  the homepage, `https://plantadvocate.ai/about` and so on, which is how
  Cloudflare serves them), and `twitter:card` summary. There is no `og:image`
  or `twitter:image`, because the site has no image to point at.
- The nav button "Get early access →", which pointed at the homepage's
  sign-up section, becomes "Get the app →" and links to the product page,
  `https://apps.apple.com/us/app/id6792203800`.
- The footer gains a Press link and, on its last line, Apple's credit line:
  "Apple, iPhone and iPad are trademarks of Apple Inc., registered in the U.S. and other countries. App Store is a service mark of Apple Inc., registered in the U.S. and other countries. Apple Intelligence is a trademark of Apple Inc."
- Counts are written as digits ("5 species", "4 layers", "3 weeks").

Page by page:

- `index.html`: a `<meta name="description">`, which the homepage lacked.
  The hero button "Join the beta" becomes "Download from the App Store". The
  sign-up section's tag "Early access" becomes "Get the app", its paragraph
  reads "PlantAdvocate for iPhone is available on the App Store in the United
  States. It's free, with no ads and no in-app purchases, and you sign in
  with Apple or Google. Photo suggestions work only on iPhone models with
  Apple Intelligence.", its button becomes "Download from the App Store", and
  the line under it reads "Questions, or a fact that reads wrong?
  support@plantadvocate.ai · A real person reads it, usually within 2
  business days."
- `faq.html`: the question "When can I actually use this?" becomes "Where do
  I get it?", answered "PlantAdvocate for iPhone is available on the App
  Store in the United States. It's free, and you sign in with Apple or
  Google. On iPad it runs as an iPhone app, and there is no Android app.
  Photo suggestions work only on iPhone models with Apple Intelligence."
- `about.html`: the closing question "Want to see it before anyone else
  does?" becomes "Want to see it for yourself?", and its "Join the beta"
  button "Download from the App Store".
- `how-it-works.html` and `pricing.html`: the "Join the beta" and "Get early
  access" buttons become "Download from the App Store". Pricing's photo line
  says "iPhone models with Apple Intelligence" instead of "iPhones with
  Apple Intelligence".
- `support.html`: "the PlantAdvocate iPhone app" becomes "PlantAdvocate for
  iPhone"; "iPhones with Apple Intelligence" becomes "iPhone models with
  Apple Intelligence"; "your iPhone's Settings" becomes "Settings on your
  iPhone", twice.
- `conservation.html`, `nurseries.html` and `resources.html`: their `<meta
  name="description">` lines say what the pages say. Conservation's names
  intentions rather than partnerships, Nurseries' says the program doesn't
  exist yet, and Resources' says the catalog cites these organizations
  rather than that they are "behind" it.
- `press.html`, new: a fact sheet for anyone writing about PlantAdvocate.
  An "At a glance" table (the app and version, availability, who makes it, price, platform, sign-in, the connection it needs, photo suggestions and the Gnome's voice, which need Apple Intelligence turned on and iOS 26 or later, language and units, category, species, check schedules, weather, support), then what it does, what it doesn't do,
  where the facts come from, privacy, links and the press contact. Every
  figure and claim on it comes from [product-truth.md](product-truth.md)
  and [launch-kit/fact-sheet.md](launch-kit/fact-sheet.md). It links to
  Apple's list of Apple Intelligence models
  (https://support.apple.com/en-us/121115), the product page, the privacy
  and support pages, and support@plantadvocate.ai.
- `privacy.html`: the tags, the nav button and the footer only. The
  policy's wording is byte for byte the ship branch's, and its effective
  date stays October 20, 2026. The campaign-label clause the strategy
  planned for launch day is not on this branch; see "What comes after".
- `site/README-SITE.md`: 14 pages, a history entry for the launch-day
  site, and an "After launch day" group in the verify block, printed below.

What the branch does not do: no App Store badge (text links only), no
`og:image`, no campaign token on any link, no change to any policy wording,
no change to anything under `garden-gnome/` or `mobile/`.

## The commits

On `claude/launch-day-site`, oldest first, each on top of `2ac7b19`:

1. "Point the site at the App Store for launch day (unreviewed draft)", the
   2026-10-26 draft, rebased.
2. "Link the store buttons to the US product page, and give each page its
   address": every store link is `https://apps.apple.com/us/app/id6792203800`,
   and every page has its `og:url`.
3. "Write Apple's names the way Apple's marketing rules ask": "PlantAdvocate
   for iPhone", "iPhone models", "Settings on your iPhone", the credit line
   in Apple's international form.
4. "Make the press page and the store lines say only what the app does":
   the press page and the availability paragraphs checked line by line
   against the truth sheet.
5. "Write counts as digits on the launch-day pages".
6. "Add the after-launch-day checks to the site README".

Anything the 2026-10-31 review changed is a seventh commit or later; the
finish-line handoff's 2026-10-31 block records the tip.

## Apple's rules the branch follows

Read on 2026-10-31 from Apple's public pages. The wording in quotation marks
is Apple's.

From the [App Store Marketing Guidelines](https://developer.apple.com/app-store/marketing/guidelines/):

- It is correct to say that an app is "available on the App Store" or "can
  be downloaded from the App Store"; don't say "at the App Store", and don't
  use "downloadable". The buttons read "Download from the App Store" and the
  availability lines "available on the App Store".
- "Always typeset App Store with an uppercase A and an uppercase S followed
  by lowercase letters", with only the article "the" before it, never
  "Apple App Store" or "iPhone App Store", always in English and never in
  all capitals. The site never writes it any other way.
- Use Apple product names "in a referential phrase": "app name for iPhone",
  "works with iPhone", never "iPhone app name". So "PlantAdvocate for
  iPhone", and the support page no longer says "the PlantAdvocate iPhone
  app". "List all the Apple products that your app runs on", and avoid
  referring to iOS in marketing communications; the pages name iPhone, and
  iPad only to say the app runs on it as an iPhone app. The two remaining
  "iOS" mentions on the site are the support page's bug-report line ("your
  iOS version") and the privacy policy's voice paragraph, both on the ship
  branch already and neither marketing copy.
- Marks are singular and never possessive; "modifiers such as model,
  device, or collection can be plural or possessive". So "iPhone models with
  Apple Intelligence" and "Settings on your iPhone" rather than "iPhones"
  and "your iPhone's Settings".
- Credit lines: "Use the appropriate credit lines in all communications
  worldwide, listing all the Apple trademarks and products included in your
  communication", "Include the credit lines only once in your communication
  or website, and place the credit lines wherever you provide legal
  notification." Every page's footer carries the site's copyright notice,
  which is where it gives legal notification, so the credit line sits
  there, once per page. If Apple or you would rather it appeared on one page
  only, the homepage's footer is the place, and the other 13 footers can
  lose the line in one commit.
- The international template is "___ and ___ are trademarks of Apple Inc.,
  registered in the U.S. and other countries." for registered marks, and
  "___ is a trademark of Apple Inc." for the rest. Trademark symbols belong
  only in material distributed in the United States alone and never in
  headlines, so the site uses none.
- The badge: "Use only the badge artwork provided in these guidelines", the
  preferred black badge, one per layout, in a subordinate position, at least
  40 px high onscreen, unmodified, and "When the App Store badge is used,
  credit both Apple and the Apple Logo." The branch uses no badge, so the
  credit line names Apple but not the logo. The badge is a follow-up, below.

From the [Guidelines for Using Apple Trademarks and Copyrights](https://www.apple.com/legal/intellectual-property/guidelinesfor3rdparties.html):
trademarks are adjectives, never plural or possessive, spelled and
capitalized as the trademark list shows, never abbreviated, and never used
"in a manner that would imply Apple's affiliation with or endorsement,
sponsorship, or support". Nothing on the site suggests Apple's endorsement.

From [Apple's trademark list](https://www.apple.com/legal/intellectual-property/trademark/appletmlist.html):
Apple, iPhone and iPad are registered trademarks, App Store is a registered service mark (the marketing guidelines page's own footer reads "App Store is a service mark of Apple Inc., registered in the U.S. and other countries"), and Apple Intelligence is a trademark but not registered, which is why the credit line has three sentences. "Apple Weather" and "Sign in with Apple" are not on the
list, so the credit line doesn't name them; the list says its absence of a
name is no waiver, so if Apple asks for either, add it to the second
sentence.

From [Promoting Apps with Smart App Banners](https://developer.apple.com/documentation/webkit/promoting-apps-with-smart-app-banners):
the tag is `<meta name="apple-itunes-app" content="app-id=myAppStoreID,
app-argument=myURL">`, "in the head element of each page where you'd like
the banner to appear"; `app-id` is required and `app-argument` optional, and
the branch uses the id alone. "If your app is unavailable in the user's
location, the banner doesn't appear", so a visitor outside the United States
sees no banner, and "Banners don't appear in the iOS simulator", which is why
the runbook has you check it on a phone.

From [Campaign links](https://developer.apple.com/help/app-store-connect-analytics/acquisition/campaign-links/):
a campaign link cannot be made until the app has been live with downloads
for about 24 hours, so on L the links are the plain product URL, in the US
storefront form `https://apps.apple.com/us/app/id6792203800`. The `site`
token is an L+1 or L+2 change ([launch-day-runbook.md](launch-day-runbook.md#give-the-sites-buttons-the-site-token)).

## What was checked

On the branch as it stands, on 2026-10-31:

- The link check in `site/README-SITE.md` ends `14 pages, 0 broken`.
- The after-launch-day verify lines, run against the files rather than the
  live site: every page has the store link and none has "early access",
  "Join the beta" or "in beta"; the homepage has the banner tag and the
  credit line once each; the press page has its own line.
- `site/privacy.html` differs from the ship branch's only in the tags, the
  nav button and the footer.
- A wording scan over the 14 pages: no "Apple App Store", "at the App
  Store", "downloadable", "APP STORE", "iPhone PlantAdvocate", "smartphone"
  or "tablet"; the banner tag identical on all 14 pages; one credit line
  wording on all 14; `og:url` set on all 14.
- Every statement on the press page and in the availability paragraphs read
  against [product-truth.md](product-truth.md): the 990 species, the 129
  uncited check schedules, the 8 cited organizations, 2 business days, the
  5-day snapshots, coordinates rounded to about a kilometer, Fly.io in the
  United States, Lifestyle then Reference, feet, inches and Fahrenheit, the
  sole proprietor line, and that PlantAdvocate never receives the dictation
  audio or transcript (the policy's own words).
- Apple's support link on the press page answers 200. The product page
  answers 404, as it must until Release.
- The adversarial review: see the next section.

Not checked, because it can't be yet: the Smart App Banner on a phone (the
app has to be live), the Open Graph previews, the product page itself, and
the two things the press page states as fact before the page exists, the
privacy label and the category. The runbook's read of the product page on L
covers all of them; if the label or the category on the live page differs,
the press page changes in the same deploy.

### The adversarial review

Four reviewers read the branch through one lens each (honesty against the
truth sheet, Apple's rules, structure and links, voice and consistency with
the ship branch's copy), and two refuters challenged every finding. Of 24
findings, 21 were fixed in the branch's seventh commit before the refuters
read it (the service mark, the iOS 26 condition, the numerals, the README
lines, the Almanac and Gnome's voice explanations) or refuted; the 3 that
stood are the README's merge timing (fixed in the same commit), the Mac and
Apple Vision Pro availability boxes in App Store Connect (now in the
finish-line handoff's step 4 and the runbook's approval-day check) and a
possessive in the privacy policy, left for its next revision. The
finish-line handoff's 2026-10-31 block records the same.

## Launch morning

The steps are in [launch-day-runbook.md](launch-day-runbook.md); in short,
and in order: merge the branch's pull request into `master` first thing on
L, which redeploys the backend with the same code and deploys no site; press
Release; wait until the product page answers; install from the store on a
clean phone; deploy `site/` from `origin/master` with the commands under
"Deploy the launch-day site"; then run `site/README-SITE.md`'s verify block,
both groups. The after-launch-day group, as the branch's README prints it:

```bash
for p in index how-it-works pricing nurseries community-garden faq about contact support privacy recommendations resources conservation press; do check "https://plantadvocate.ai/$p.html" 'apps.apple.com/.*id6792203800' present; check "https://plantadvocate.ai/$p.html" '[Ee]arly access\|Join the beta\|in beta' absent; done
check https://plantadvocate.ai/index.html 'app-id=6792203800' present
check https://plantadvocate.ai/index.html 'trademarks of Apple Inc' present
check https://plantadvocate.ai/press.html 'for anyone writing about PlantAdvocate' present
```

`check` is the function the block defines at its top; run that line first.
Then:

```bash
curl -s -o /dev/null -w '%{http_code} %{url_effective}\n' -L https://apps.apple.com/us/app/id6792203800
```

It should print `200`, on an address that ends in `id6792203800`. Last, on
a phone, open https://plantadvocate.ai in Safari and look for the banner at
the top, tap a "Download from the App Store" button and land on the product
page, and open the privacy page: still October 20 and its "What changed"
line, because the branch changes no policy wording.

## What comes after

- **The `site` token and the campaign-label clause, L+1 or L+2.** One small
  pull request: every store button gets the `site` campaign link, the
  privacy policy's website paragraph gains the clause [strategy.md](strategy.md#measurement-without-adding-trackers)
  words ("Links from this site to the App Store carry a campaign label, so
  Apple can tell us in aggregate how many downloads came from the site."),
  the policy's effective date and "What changed" line move to that day, and
  `site/README-SITE.md`'s `Effective Date` check line moves with them, plus
  `check https://plantadvocate.ai/privacy.html 'campaign label' present`.
  The clause and the labels go live in the same deploy, which is what the
  README asks: the policy changes in the same change as the thing it
  describes. The Smart App Banner keeps `app-id` alone, because Apple's
  banner page documents no token parameter.
- **The badge.** Once the app is live, download the black "Download on the
  App Store" badge from [App Store Marketing Tools](https://toolbox.marketingtools.apple.com/en-us/app-store/us),
  put one per page in place of the text buttons or beside the hero, at
  least 40 px high with clear space a quarter of its height, and add "the
  Apple logo" to the credit line's first sentence, as the guidelines ask
  whenever the badge is used.
- **`og:image`.** A 1200 by 630 image per page, or one for the site, once
  there is artwork; until then the tags are omitted rather than pointed at a
  missing file.
- **A mailing service in the policy**, before any waitlist send through one:
  [launch-kit/waitlist-email.md](launch-kit/waitlist-email.md) has the line.
  It goes in the same change as the campaign-label clause if the send
  follows the links, or in its own.
- **Two phrases in the privacy policy**, at its next revision: "the
  PlantAdvocate iPhone app" becomes "PlantAdvocate for iPhone", and "in
  your iPhone's Settings" becomes "in Settings on your iPhone", the forms
  Apple's marketing rules prefer and the support page already uses. The
  policy is not marketing copy and neither phrase is wrong, so neither
  waits for launch day.
