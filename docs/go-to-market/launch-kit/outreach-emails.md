# Outreach notes

These are the drafts for the notes in [targets.md](../targets.md), which says who gets which one and when. Every one is a draft that Allison sends personally, one at a time, after reading it through and putting it in their own words where it doesn't yet sound like them. Nothing here has been sent, submitted or posted. Written 2026-10-24 against the ship tip `3f6d7da`; every product sentence comes from `docs/app-store/listing.md` or [product-truth.md](../product-truth.md), and where they and this file disagree, they win.

There are four templates, one for each audience the strategy reaches by note. A is for houseplant podcasts, which reach the indoor keepers the strategy puts first. B is for garden podcasts, which reach the spring bed growers. C is the article proposal to The American Gardener, the American Horticultural Society's magazine. D is an information-only note to an organization, which the strategy allows but doesn't plan. There is no template for pet owners, because the strategy reaches them through the store's pets page and pitches no safety organization, and none for makers, whose Product Hunt post is drafted in [community-posts.md](community-posts.md). The waitlist email and the individual replies owed to people who emailed for early access are in [waitlist-email.md](waitlist-email.md); neither is outreach, so neither is here. The Apple featuring nominations aren't emails; their drafts are in [research/aso.md](../research/aso.md).

## Before any note goes out

Each of these has to be true on the day a note is sent. The Apple nominations are the only outreach that goes before L, and none of this applies to them.

1. The app is live, its App Store page answers, the clean-install check on L passed, and App Store Connect has a campaign link with the `outreach` token. Apple offers the add button only after the app has had about 24 hours of downloads ([research/aso.md](../research/aso.md)).
2. There is a postal address for the footer: a USPS post office box, or a private mailbox registered with a commercial mail receiving agency, never a home address. No address, no note ([research/launch-playbook.md](../research/launch-playbook.md)).
3. The handoff's step 3 site deploy printed `ok` on every line of its check block, and the independence line is on the site pages that name organizations, because anyone who reads a note will open plantadvocate.ai next ([strategy.md](../strategy.md), the site fixes).
4. The 33 care notes that call a plant "Pet-safe" or "harmless" have been rewritten, and production's rows match.
5. A note that describes the app's hazard notes, as A does, waits for the three hazard-sentence changes the strategy wanted shipped by the end of February, and names no plant. Those changes landed on 2026-10-30 and ship with step 2's deploy, so from then this part of the condition is met. True lilies, daylilies and every aroid stay out of all outreach until their effect clauses are cited or labelled; since the same changes they are labelled "PlantAdvocate's own summary", but a note still names no plant. C is the one planned exception to naming a plant: it goes in January and names lily of the valley, because it is about what the sources say, not about the app's sentences.
6. Nothing has paused outreach. The strategy stops every push if the first 20 ratings average under 4.0, and pauses every hazard-led line if anyone reports a wrong hazard statement.
7. If the app is still available in the United States only, the note says so, so that nobody elsewhere goes looking for it.
8. The privacy page no longer says flatly that PlantAdvocate sends no marketing email. Its account paragraph ended "We never use it for marketing or advertising, and we don't send marketing email.", and a note that calls itself an advertisement, sent from the support address that same policy gives, would contradict it. The 2026-10-30 site fixes narrowed it on the ship branch: it now says the address you sign in with never goes on a mailing list, and that news about PlantAdvocate goes only to people who asked for it ([strategy.md](../strategy.md), "Before the site deploy"; [waitlist-email.md](waitlist-email.md), item 3). The effective date stays October 20, since that version hasn't been published, and the change goes live with step 3, before any note can go out. Check the live page says so on the day a note is sent.

Send each note on its own, from the support address with "Allison Bowman" as the sender's name, by email where the outlet publishes an address and through its own form where it doesn't. The nearest evidence on what gets read is about journalists, not hosts: Muck Rack's 2025 survey, as reported in [research/launch-playbook.md](../research/launch-playbook.md), found that the commonest reasons for deleting a pitch were irrelevance (86%), a promotional tone (71%) and feeling like a mass email (50%), that 69% prefer pitches under 200 words, and that 78% want them before noon. So send in the recipient's morning, keep each note short, and write the first line only if it is true. With the slots filled, A comes to about 225 words before the footer and B to about 210, a little over that mark because of the caveats they carry; B's short form version and D are well under 200. Keep a private log outside the repository with the date, the outlet, the route, the template and any reply. Keep the do-not-contact list next to it, and never delete it. The waitlist keeps its own removal list, `removed-hashes.txt`, which holds a fingerprint of each removed address and never the address itself ([waitlist-email.md](waitlist-email.md), "Removals and replies").

## What every note carries

[research/launch-playbook.md](../research/launch-playbook.md) reads the FTC's CAN-SPAM guide as covering every commercial email, including business-to-business email, and reads a note about a free app as commercial. That is a reading, not legal advice. So every template carries the same pieces.

The From and Reply-To lines say who it is from: Allison Bowman, at the address that reads the replies. Through a form, the signature and the opt-out line name the support address instead, because a reply to the form's notification may go to the form service and never reach Allison. The subject line says what is inside: every option for A, B and D says it is about an app, and C's say it is an article proposal. A plain sentence near the end says that Allison is treating the note as an advertisement under US email law, or for C as a solicitation, and says why. The footer gives the `[POSTAL ADDRESS]`. The opt-out is a reply or a short email, which costs the reader nothing. It has to keep working for at least 30 days after sending and be honored within 10 business days, and the address of anyone who opts out is never sold or passed on.

Write only to outlets made in the United States. If an outlet is based in Canada, the UK or the EU, or you can't tell, don't send. Canada's law requires consent ([research/launch-playbook.md](../research/launch-playbook.md) reads its sections 6, 11 and 13 for the waitlist), nobody here has read the EU's rules, and the UK regulator says marketing email to an individual or a sole trader needs consent or a soft opt-in, which a published address doesn't give ([ICO](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-direct-marketing-using-electronic-mail/how-do-we-comply-with-the-pecr-electronic-mail-marketing-rules/)).

Three more things travel with every note. Each one names the organizations the app cites, so each carries the independence line word for word: "PlantAdvocate is independent. The organizations it cites have not reviewed or endorsed it." And each App Store link carries the `outreach` campaign token, so App Analytics can say whether talking to people sent anyone, once that token clears Apple's floor of five first-time downloads. And if the launch-day site edit added the press page that [press-release.md](press-release.md) and [fact-sheet.md](fact-sheet.md) describe, the note may link it after the App Store link, for anyone who wants the facts in one place; nothing else from those files goes into a note.

## A. Houseplant podcasts

For a US houseplant show from targets.md's alternates (row 4), once its own site has been read. Spring.

The useful thing this note offers is plain information a host can pass on when listeners ask which app to try: one that sells nothing, asks you to look before you water, and says when it doesn't know. It asks for nothing.

Subject, either:

```text
A plant app that says when it doesn't know
```

```text
A plant app that asks you to feel the soil first
```

```text
Hello [THE HOST'S NAME AS THE SHOW PUBLISHES IT, OR THE SHOW'S NAME],

[ONE SHORT, TRUE SENTENCE ABOUT AN EPISODE YOU HEARD. LEAVE IT OUT RATHER THAN INVENT ONE.]

If your listeners ask which plant app to try, here is one that sells nothing and says when it doesn't know. I build PlantAdvocate on my own: a free app for iPhone only, with no ads and no in-app purchases. I'm not asking for a mention.

Describe each windowsill or shelf, and it checks each plant against that spot's room, soil and your goals, with the reason. It can't judge indoor light yet, and says so. When a plant with a check schedule comes due, you feel the soil, then tap Watered or Still damp.

Care facts come from the organizations that publish them, such as NC State Extension, the Royal Horticultural Society and Missouri Botanical Garden. Anything not yet cited says so. The check schedules that reminders follow were written by PlantAdvocate for 129 common plants and are not cited.

Where a source records a plant as harmful to people or pets, the plant's page says so, and a missing record is never treated as safe. Its hazard notes are not medical or veterinary advice.

You sign in with Apple or Google.[ It's available on the App Store in the United States only, for now.] [APP STORE LINK WITH THE outreach TOKEN]

PlantAdvocate is independent. The organizations it cites have not reviewed or endorsed it.

Allison Bowman
PlantAdvocate

This note is about my own app, so I'm treating it as an advertisement under US email law.
[POSTAL ADDRESS]
If you'd rather not hear from me again, reply "no thanks" and I won't write again.
```

The body is about 195 words before the footer, not counting the slots, so keep the episode sentence short; filled in, it comes to about 225. If it has to be shorter, shorten the episode sentence, never the indoor-light, 129-schedule or not-advice sentences. The slots are the host's name as the show itself publishes it (or the show's name, if in doubt), one sentence about an episode Allison actually heard, the United States line, the campaign link, and the postal address. The United States line is written ready to send: keep it while availability is US-only, and delete the whole bracket once it is worldwide. If no episode sentence is true, drop the line; a note that opens with the listeners' question is better than one that opens with something invented. If the show's own route turns out to be a form, use B's signature and opt-out lines, which name the support address.

Follow-up. The strategy allows one note per show, so there is no chaser. If the show doesn't answer, that is the answer; record it in the log. If it writes back, answer only what was asked, in listing.md's and product-truth.md's words, and offer the App Store screenshots in `docs/screenshots/1.1.3/` if a look would help. Give no host a TestFlight build, a gift, a payment or anything else of value, whether or not it is tied to a mention; the FTC counts early access and gifts as a connection the host would have to disclose ([research/launch-playbook.md](../research/launch-playbook.md)). If a host asks to try an unreleased version, the answer is no. If Allison ever decides otherwise, Allison tells the host in writing, before sending the invite, that any mention must say on air that the developer gave them early access, and listens to check that it does. If the app is mentioned on air, thank the show once, and don't quote the mention on the store page or the site without the show's permission, and never as if the show had checked the facts. If the show asks Allison on as a guest, weigh it against the strategy's spring hours before saying yes. A reply can be as short as this, and it carries the same footer:

```text
Thank you for writing back.

[ANSWER WHAT THEY ASKED, USING ONLY LISTING.MD AND PRODUCT-TRUTH.MD WORDING.]

The App Store page is here: [APP STORE LINK WITH THE outreach TOKEN]. If screenshots would help, I can send the ones from the App Store page.

Allison Bowman
PlantAdvocate

This note is about my own app, so I'm treating it as an advertisement under US email law.
[POSTAL ADDRESS]
If you'd rather not hear from me again, reply "no thanks" and I won't write again.
```

## B. Garden podcasts

For Just Grow Something (targets.md row 5), and in the short form version below for The joe gardener Show (row 6). Spring.

The useful thing this note offers is an honest account of a free tool for checking a bed before planting, including what it doesn't do, so a host can tell listeners who want a planting calendar to look elsewhere. It asks for nothing.

Subject, either:

```text
A garden app that names its sources and its gaps
```

```text
A free app that checks what suits each bed
```

```text
Hello [THE HOST'S NAME AS THE SHOW PUBLISHES IT, OR THE SHOW'S NAME],

[ONE SHORT, TRUE SENTENCE ABOUT AN EPISODE YOU HEARD. LEAVE IT OUT RATHER THAN INVENT ONE.]

I build PlantAdvocate on my own: a free app for iPhone only, with no ads and no in-app purchases. I'm not asking for a mention. [ONE SHORT SENTENCE, IN YOUR OWN WORDS, ON WHY THIS SHOW'S LISTENERS MIGHT WANT TO KNOW.] This is only in case it helps when they ask about garden apps.

You describe a bed once: what it is, how big, indoors or out, how much sun, and what you want from it. Each plant in it is then checked against that, with the reason and the source. A shade fern in full sun is flagged. A blank measurement counts as unknown.

Care facts come from the organizations that publish them, such as NC State Extension, the Royal Horticultural Society and Missouri Botanical Garden. Anything not yet cited says so. The check schedules that reminders follow were written by PlantAdvocate for 129 common plants and are not cited.

It doesn't give planting dates, frost dates or hardiness-zone matches. You sign in with Apple or Google.[ It's available on the App Store in the United States only, for now.] [APP STORE LINK WITH THE outreach TOKEN]

PlantAdvocate is independent. The organizations it cites have not reviewed or endorsed it.

Allison Bowman
PlantAdvocate
support@plantadvocate.ai

This note is about my own app, so I'm treating it as an advertisement under US email law.
[POSTAL ADDRESS]
If you'd rather not hear from me again, write "no thanks" to support@plantadvocate.ai and I won't write again.
```

The body is about 165 words before the footer, not counting its two sentence slots, so keep both short; filled in, it comes to about 210. The listing's fence example is left out to keep it there; it can go back after the fern, as "and so is a climber that will outgrow a 7 ft fence", if the episode sentence is dropped. The slots are the same as A's, plus one sentence on why this show. Write that sentence from what the show says about itself and nothing more. For Just Grow Something, that might be its evidence-based approach, since its own title says so. Don't praise a show for something you haven't heard. Just Grow Something's form has a subject field. Through a form, the signature and the opt-out line name the support address, because a reply to the form's notification may not reach Allison.

For The joe gardener Show, use this shorter version. Its form invites questions, comments and suggestions and says it can't reply to each message, so a full pitch is the wrong shape there. The form has no subject field, so paste the chosen subject line as the message's first line.

```text
Hello,

I build PlantAdvocate on my own, a free iPhone app with no ads and no in-app purchases. I'm not asking for a mention. You describe a bed once, and each plant in it is checked against the bed's sun, space and what you want from it, with the reason and the source named. It doesn't give planting dates or frost dates. In case it's useful when listeners ask about garden apps: [APP STORE LINK WITH THE outreach TOKEN][ It's available on the App Store in the United States only, for now.]

PlantAdvocate is independent. The organizations it cites have not reviewed or endorsed it.

Allison Bowman
PlantAdvocate
support@plantadvocate.ai

This note is about my own app, so I'm treating it as an advertisement under US email law.
[POSTAL ADDRESS]
If you'd rather not hear from me again, write "no thanks" to support@plantadvocate.ai and I won't write again.
```

Follow-up. One note per show, no chaser, as with A. The joe gardener contact page says it can't reply to each message, so silence is expected and is not a no. Just Grow Something has a sponsors-and-partners page; if a reply points there, sponsorship is paid and outside the $0 baseline, so thank them and leave it. If either show writes back with a question, answer as in A, with the same reply draft and the same rule about giving hosts nothing. If a host asks about planting dates or frost, say plainly that the app doesn't answer those, which is better than a one-star review from someone who wanted a planner ([strategy.md](../strategy.md)).

## C. The American Gardener article proposal

For the American Horticultural Society's magazine (targets.md row 3). Winter, in January. It goes by email to the editorial address on the [writer's guidelines page](https://ahsgardening.org/writers-guidelines/). These files call it The American Gardener, as strategy.md and channels.md do. targets.md found the magazine's own pages calling it American Gardener on 2026-10-24, so before sending, use whichever name its current issue prints, in the proposal and the follow-up alike.

This one isn't about the app. It offers the magazine's readers an article: what a gardener can do when two respected references disagree about how poisonous a plant is, with lily of the valley as the case. The guidelines ask for a description of the topic, why it would interest a national audience of knowledgeable gardeners, an outline, and, from a first-time writer, writing samples and a brief account of the writer's own experience with the subject, plus where photographs might come from. The draft below has each of those, and it is longer than the podcast notes for that reason.

Three conditions come first. The lily of the valley write-up the strategy describes exists in Allison's own words. Handoff decision 6 is settled. And both source pages have been re-read on the day the proposal goes, with the paraphrased clauses in the second paragraph corrected if either page has changed; on 2026-10-24 NC State's page tagged the plant poisonous, rated its severity low and said it is toxic only if large quantities are eaten. The strategy uses this story in at most two places, this proposal and later a page on plantadvocate.ai, so it appears in no other note. The proposal paraphrases both sources and quotes neither.

Subject, either:

```text
Proposal: when two trusted sources disagree about a poisonous plant
```

```text
Article proposal: lily of the valley and its two poison ratings
```

```text
Dear editors,

I'd like to propose an article for The American Gardener, either as a feature of about 1,500 words or as a column of 900 to 1,000 words, whichever suits you better.

The topic is what a gardener can do when two respected references disagree about how poisonous a plant is. Lily of the valley is the case. NC State Extension's Plant Toolbox lists it as poisonous but rates the severity for people as low, with harm only if a large amount is eaten, while Missouri Botanical Garden's Plant Finder says every part of the plant is very poisonous. A gardener who reads both gets answers that sit a long way apart.

[ONE SENTENCE NAMING THE NEAREST AREA THE GUIDELINES LIST, SUCH AS PEOPLE–PLANT RELATIONSHIPS OR PLANT LORE, OR DELETE IT.]

The question reaches well beyond one plant or one region. Any gardener with children or pets who looks a plant up can meet the same problem, because hazard entries differ in whether they rate harm to people or to animals, in what they measure, and in how often they name the poisonous parts. The article would help readers read any hazard entry with that in mind.

The outline:
1. The lily of the valley disagreement, set out from each source in paraphrase.
2. What each kind of rating measures, as far as each source explains it, and why careful sources can still differ.
3. Why "no record" is not the same as "safe".
4. A short way to read any plant's hazard entry: whose rating it is, whether it covers people or pets, which parts it names, and who to call if poisoning is suspected (in the US, Poison Control at 1-800-222-1222, or a vet).
5. Where readers can look further.
6. [A SHORT CONVERSATION WITH A POISON-INFORMATION SPECIALIST OR VETERINARY TOXICOLOGIST YOU HAVE ACTUALLY ARRANGED TO ASK, NOT A CITED SOURCE'S STAFF. DELETE THIS LINE IF THERE IS NONE.]

[TWO OR THREE SENTENCES, IN YOUR OWN WORDS, ON YOUR EXPERIENCE WITH THE SUBJECT. ADD NOTHING THAT ISN'T TRUE.]

[WRITING SAMPLES: LINKS, OR ONE PLAIN SENTENCE SAYING THIS WOULD BE YOUR FIRST MAGAZINE PIECE.]

Photographs: [YOUR OWN, IF YOU HAVE THEM, OR "I would need to arrange licensed images"]. I wouldn't use either source's images without its permission.

One disclosure. I build PlantAdvocate, a free app for iPhone that cites both of these sources. The article would not be about the app, and I'd want my connection to it disclosed in whatever way you prefer. PlantAdvocate is independent. The organizations it cites have not reviewed or endorsed it.

This proposal is with The American Gardener only.

With thanks,
Allison Bowman

This offers an article for payment and mentions my own app, so I'm treating it as a solicitation under US email law.
[POSTAL ADDRESS]
If you'd rather not hear from me again, a one-line reply saying so is enough.
```

The slots are the fit line, the interview line, Allison's own experience, the writing samples and the photographs, and each one is Allison's to fill truthfully, answer plainly or delete. The guidelines list the areas the magazine covers, and toxicity isn't one of them, so the fit line names the nearest honest one or goes. They also ask for lively quotes from interviews or written sources; the interview line stays only if someone has actually agreed to talk, and a request for an interview is about the subject, never the app. The About page's own heading, "It started with a new home, and a garden I didn't yet know how to keep.", may be quoted as written if it helps the experience paragraph; nothing may be added to that story ([product-truth.md](../product-truth.md), "About Allison"). An editor reads a proposal as a writing sample, so it should end up in Allison's voice, not this draft's. If the editor names themselves on the magazine's own masthead, the greeting can use that name.

Follow-up. The guidelines publish no response time. My suggestion is to wait six weeks, then send one note that asks once and sets a date, so the piece isn't left in limbo and nothing goes elsewhere while the magazine might still want it. With a January proposal, that lands in late February, leaving the site page free for April, as the strategy plans. The note itself says nothing about the site; the April plan stays in the strategy.

```text
Dear editors,

I wrote on [DATE OF THE PROPOSAL] to propose an article on lily of the valley and its two poison ratings. If it's still under consideration, I'm glad to wait. If I haven't heard by [A DATE TWO WEEKS AWAY], I'll take it that it isn't a fit for The American Gardener and will withdraw the proposal, with thanks.

With thanks,
Allison Bowman

This follows a proposal that offers an article for payment and mentions my own app, so I'm treating it as a solicitation under US email law.
[POSTAL ADDRESS]
If you'd rather not hear from me again, a one-line reply saying so is enough.
```

If the magazine says yes, ask what rights it buys before putting any version on plantadvocate.ai, and follow its own standards for quoting sources. If it says no, or the date passes, the write-up goes to the site in April, and that page is the one the strategy offers to Hacker News.

## D. Organizations, for information only

For the American Community Gardening Association and National Garden Clubs (targets.md rows 7 and 8). Spring, and optional. The strategy says that if Allison writes to either of them, the note is information only, carries the independence line, a postal address and a one-line opt-out, and gets no follow-up.

The useful thing this note offers is information the organization can pass to its members or not: a free tool that checks what suits a plot or a bed, names its sources, and says what it can't check. It makes no ask.

Subject, either:

```text
A free app for checking what suits a garden bed
```

```text
A plant-care app that names its sources
```

```text
Hello,

This is a short note for your information, and it needs no reply.

I build PlantAdvocate on my own. It's a free app for iPhone, with no ads and no in-app purchases. [ONE TRUE SENTENCE ON WHY YOU THOUGHT OF THIS ORGANIZATION'S MEMBERS.]

You describe each place you grow, such as a plot or a raised bed, and it shows what suits that spot, what doesn't, and why, with the source named. Care facts come from the organizations that publish them, such as NC State Extension, the Royal Horticultural Society and Missouri Botanical Garden, and anything not yet cited says so. The check schedules that reminders follow were written by PlantAdvocate for 129 common plants and are not cited. It doesn't give planting dates or frost dates. It runs on iPhone only, and you sign in with Apple or Google.[ It's available on the App Store in the United States only, for now.]

PlantAdvocate is independent. The organizations it cites have not reviewed or endorsed it.

If it's ever useful to your members, the App Store page is here: [APP STORE LINK WITH THE outreach TOKEN]

Allison Bowman
PlantAdvocate
support@plantadvocate.ai

This note is about my own app, so I'm treating it as an advertisement under US email law.
[POSTAL ADDRESS]
If you'd rather not hear from me again, write "no thanks" to support@plantadvocate.ai and I won't write again.
```

The body is about 155 words before the footer, not counting the slots, and about 185 filled in. The sentence on why this organization should be true and small: for either of them, that its members keep plots or beds whose sun and room they already know. Don't add praise you can't source. Both routes are web forms, so the signature and the opt-out line name the support address, because a reply to the form's notification may not reach Allison. Paste the subject line as the message's first line where there is no subject field. "Founder" answers a position field, which is how the About page signs; "Founder, PlantAdvocate" is fine if the form gives no other place to name the app. targets.md rows 7 and 8 say what else each form asks for and which boxes to leave unticked.

Follow-up. None, whatever happens; that is the strategy's rule for organizations. Silence is the expected outcome. If an organization writes back and asks for a line it could use in a resource list, this one stays inside what the listing says:

```text
PlantAdvocate, a free app for iPhone: describe each place you grow and see what suits it, what doesn't, and why, with the source named. PlantAdvocate is independent. The organizations it cites have not reviewed or endorsed it.
```

If an organization asks for anything that would read as a partnership, an endorsement, its logo beside the app's, or a mention in its own name, decline politely. If it says no or asks not to be contacted, add it to the do-not-contact list.

## What never to say

The full list of claims that are false or need a condition is in [product-truth.md](../product-truth.md), section 2, and it applies to every note and every reply. These are the ones outreach reaches for most.

Never suggest that a cited organization is behind the app. Don't write "partnered with", "in collaboration with", "trusted by", "approved by", "recommended by", "backed by" or "as used by", don't write "data from NC State" in a way that suggests a feed or a license, and use no logo, seal or source's prose. Never write to a cited organization or its Master Gardener program, and never pitch any organization as if being cited were a reason to promote the app. The independence line goes in every note that names one.

Never overclaim the facts. Not "every fact cited", "fully cited", "verified", "vetted", "fact-checked", "no guesswork" or "most plant apps guess"; say "anything not yet cited says so" and keep the 129 uncited check schedules in view, in product-truth.md's own sentence. Never call a plant safe, pet-safe or non-toxic, and never say the app tells you whether a plant is safe; say "a missing record is never treated as safe", and pair any hazard sentence with "They are not medical or veterinary advice." Say "more than 990 species", never "about 1,000" or "thousands".

Never overclaim the features. Leave photo matching out of outreach; if it must come up, it is "on iPhone models with Apple Intelligence" and it suggests matches for you to confirm. Never write "AI", "AI-powered", "plant doctor", "diagnose", "photo check-up" or "symptom checker"; the care advice is rule-based, and photo check-ups and symptom reading are switched off. Never say it tells you when to water, that it sets reminders for every plant, that it knows your zone, your frost dates or whether a plant will survive the winter, or that it can tell whether a windowsill or shelf is bright enough; indoors, light comes back as not known. Never claim an Android or iPad version, offline use, "free forever", an anonymous census, a community of gardeners, nursery or conservation partners, or "powered by Apple Weather". Never write "Garden Gnome".

Never claim popularity or credentials that don't exist. No user counts, download figures, ratings, reviews, testimonials, press quotes or awards, until the store shows them and then only as it shows them. Never add to what the About page and the privacy policy say about Allison.

Never ask for, or trade for, coverage. Don't ask for a mention, a review, a rating, a link or upvotes, don't give money, a gift, early access or anything else, in return or otherwise, and don't tie anything to a favorable word. Don't send the proposal to The American Gardener anywhere else while it waits, don't use the lily of the valley story in any note but that proposal, and don't send the same note to two outlets in a way that reads as a mass mailing. Never write to the addresses of people who signed in to the app, and never add anyone who replies to a note to a list.
