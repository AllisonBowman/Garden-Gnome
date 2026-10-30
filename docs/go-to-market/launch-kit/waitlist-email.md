# The July waitlist: keeping it, and the two emails to it

Written 2026-10-24 against the ship tip `3f6d7da`, for the launch plan in [strategy.md](../strategy.md) ("The waitlist"). It has three parts: how to get the early-access addresses out of Cloudflare before the handoff's step 3 deploy retires `/api/waitlist`, the launch email to that list, and one short note for the spring push. Nothing here has been sent, exported or changed. Every claim in the emails was checked against [product-truth.md](../product-truth.md) and `docs/app-store/listing.md`, and where they disagree the truth sheet wins. Commands follow the handoff's convention: zsh on this Mac, one command per block, no `#` comments. Names in capitals, such as `PROJECT`, are placeholders you fill in, as in the handoff.

I am not a lawyer. The email rules below are a reading of the CAN-SPAM Act and the FTC's guide as summarized in [launch-playbook.md](../research/launch-playbook.md), plus one clause of the Act read directly ([15 U.S.C. 7704](https://www.law.cornell.edu/uscode/text/15/7704), read 2026-10-24).

## The decision is yours

Whether to keep the list at all is handoff decision 9, and it is Allison's. The handoff recommends leaving the `/api/waitlist` endpoint retired, and nothing here brings it back. That is a decision about the endpoint, not about the addresses already collected, which stay in Cloudflare's KV or D1 until someone exports or deletes them.

My recommendation, the strategy's, is to export them this week, before step 3, and decide about sending once the July form's wording has been checked and a postal address is in hand. By my estimate the export takes about half an hour, and it keeps every choice open. If you decide not to email the list, the cleaner end is to delete the store in Cloudflare once you're sure, so the addresses aren't held for nothing. That deletion is also yours to make, and it can't be undone.

[launch-playbook.md](../research/launch-playbook.md) says to do it now rather than alongside the deploy. The live site has already changed since July, so the endpoint may already be gone, or may still take stray posts, and nobody can tell from outside without submitting to it. The addresses don't depend on the endpoint: bindings are set per project in the dashboard, and the store is an account resource the deploy doesn't touch, though no Cloudflare page says so in as many words. Doing it before step 3 also means the count is known before anything else leans on it, and the way to send depends on the count.

## Before step 3: get the list out of Cloudflare

### A private folder outside the repository

The export is personal data. It goes in a folder of its own in your home folder, not in the repository and not in a folder that syncs to iCloud, such as Desktop or Documents if those sync. Step 3 begins with `git status --short` printing nothing, which also confirms none of these files landed in the repository.

```bash
mkdir -p -m 700 "$HOME/PlantAdvocate-private"
```

```bash
cd "$HOME/PlantAdvocate-private"
```

Don't paste the export, or any address from it, into a Claude session, an issue or a doc. The check below prints counts, endings, the table definition and one sample entry with every stored value hidden, so a session can help read its output without seeing anyone's address. Look at the sample entry before sharing the output all the same. In a format the masking doesn't expect, such as unquoted comma-separated values, a name could still show, and then share everything except that line.

### Sign in and find the store

The handoff found Wrangler's token on this Mac expired, so sign in first. It is the same sign-in step 3 starts with, so doing it now costs nothing.

```bash
npx wrangler login
```

That opens a browser. If npx asks to install wrangler, answer `y`.

```bash
npx wrangler pages project list
```

Find the project whose domains include `plantadvocate.ai`. Below it's `PROJECT`, as in step 3.

Then, in the Cloudflare dashboard, open Workers & Pages, then `PROJECT`, then Settings, then Bindings, and look at the production bindings. You are looking for a KV namespace or a D1 database. Note which it is and its name.

If the dashboard has moved things, Wrangler has an experimental command that downloads the project's settings as a Wrangler configuration file. Cloudflare's page doesn't say where it writes the file, so run it from the private folder, where you already are, and list the folder afterwards. Open the new file and look for a `kv_namespaces` or `d1_databases` entry.

```bash
npx wrangler pages download config PROJECT
```

```bash
ls -la "$HOME/PlantAdvocate-private"
```

To get the id Wrangler needs, list what the account holds. For KV, the namespace's `id` is `NAMESPACE_ID` below. For D1, the database's name is `DATABASE_NAME`.

```bash
npx wrangler kv namespace list
```

```bash
npx wrangler d1 list
```

If the project has no KV or D1 binding at all, the July Function may never have stored addresses in Cloudflare. It may have mailed them somewhere or written them to another service. The desktop generator's old source, which `site/README-SITE.md` says lives on the desktop machine, is then the place to find out. Stop here until you know.

### Read what the July form promised

The form's wording decides what the list may be used for ([launch-playbook.md](../research/launch-playbook.md)). launch-playbook.md couldn't find it at first, but the best copy there is sits in git. Commit `25f370f`, "site: recovered from production", made on 19 July 2026, holds the homepage as Cloudflare served it then, and the same wording stayed on this branch until `3c1d4fe` on 16 October, which replaced the form. This prints the early-access section, lines 391 to 402:

```bash
git -C "$HOME/Developer/Garden-Gnome" show 25f370f:site/index.html | sed -n '391,402p'
```

The section asks people to "Join the beta", the button says "Request access", the confirmation reads "You're on the list. We'll be in touch before the first plant does.", and the note under the form says "No spam. No card required. Just an update when the beta opens." The FAQ in the same commit adds "Join the beta list and you'll be among the first invited as new capabilities roll out." (`site/faq.html`, line 281). So the list was promised an update when a beta opened. No beta ever opened to it, as far as the record goes: 1.1.0 to 1.1.2 went to TestFlight only, and there are no external testers on record ([launch-playbook.md](../research/launch-playbook.md)). If the list was ever invited to a beta, change the launch email's reason sentence, which rests on it. The launch email below is written as the promised update, and the spring note goes only to people who ask for more.

One caveat. That copy's form posts nowhere (`onsubmit="return false;"`), while the July build that collected addresses posted them to `/api/waitlist`, so that build's form may have been worded differently. Confirm the wording against a July deployment if one can be opened. The Wayback Machine's capture index returned nothing for plantadvocate.ai on 2026-10-24, so Cloudflare's deployment history is the likeliest place.

```bash
npx wrangler pages deployment list --project-name=PROJECT
```

Find the production deployments from July to mid-October, before the October rewrite went live. In the dashboard, the project's Deployments tab lists the same ones, and a deployment that kept its own `pages.dev` address can be opened from there. Cloudflare documents those addresses for preview deployments and doesn't say for production ones, so one may or may not be there. If it is, open the July homepage in Safari, compare the text around the email field with the git copy, and copy any difference, and anything else it said about what you would send, into a note in the private folder. Read it only. Don't type into that form, because it may still post to `/api/waitlist` and add a row.

If no July deployment can be opened, the desktop generator's source is the other place to look. If neither can be read, the git copy is the best record there is, and the emails below rest on it. The privacy policy's sentence that an early-access address is used "only to tell you about PlantAdvocate" (`site/privacy.html:187`) isn't in the policy committed with the July pages, so it narrows what the list may be used for but doesn't widen what the form promised.

### Export it: KV

If the Function used each address as its key, the key list is the whole export. The `--remote` flag matters: Cloudflare's page lists both `--local` and `--remote` and doesn't say which is the default.

```bash
npx wrangler kv key list --namespace-id=NAMESPACE_ID --remote > "$HOME/PlantAdvocate-private/waitlist-keys.json"
```

Run the check below on `waitlist-keys.json`. If it says there are no addresses in the file, the keys are IDs and the addresses are in the values. For a short list, the dashboard shows the values too: Workers KV, the namespace, then the KV Pairs tab. For a file, first write the key names out:

```bash
python3 - "$HOME/PlantAdvocate-private/waitlist-keys.json" <<'EOF'
import pathlib, re, sys
src = pathlib.Path(sys.argv[1])
keys = re.findall(r'"name"\s*:\s*"([^"]+)"', src.read_text(encoding="utf-8"))
(src.parent / "waitlist-keynames.txt").write_text("".join(k + "\n" for k in keys), encoding="utf-8")
print(f"{len(keys)} keys written to waitlist-keynames.txt")
EOF
```

Then read each value. It takes a few seconds a key, which is fine for a list of dozens. For hundreds, Wrangler's `kv bulk get` reads many at once, but Cloudflare's page doesn't describe the file it takes, so read `npx wrangler kv bulk get --help` before using it.

```bash
while read -r k; do npx wrangler kv key get "$k" --namespace-id=NAMESPACE_ID --remote --text < /dev/null; echo; done < "$HOME/PlantAdvocate-private/waitlist-keynames.txt" > "$HOME/PlantAdvocate-private/waitlist-values.txt"
```

Then run the check on `waitlist-values.txt`.

### Export it: D1

This writes the schema and the data to one file in the private folder.

```bash
npx wrangler d1 export DATABASE_NAME --remote --output="$HOME/PlantAdvocate-private/waitlist.sql"
```

Then run the check on `waitlist.sql`.

### Check the export

Replace `EXPORT_FILE` with `waitlist-keys.json`, `waitlist-values.txt` or `waitlist.sql`. The check is written to print no address or other stored value. It prints how many addresses it found and how many repeat, the table definition or the number of KV entries, the first entry with every stored value hidden (its column names or JSON keys show whether rows carry a date, a source or a consent field), and a count of addresses by ending. It then writes three files next to the export. `send-list.txt` holds the unique addresses to consider sending to. `set-aside.txt` holds addresses ending in `.ca`, `.uk` or an EU country code, which stay out of the first send unless the July form clearly covered them, because Canada's CASL and the UK's rules differ from US law ([launch-playbook.md](../research/launch-playbook.md)). `check-by-eye.txt` holds anything that looks like a test address, for you to keep or drop.

```bash
python3 - "$HOME/PlantAdvocate-private/EXPORT_FILE" <<'EOF'
import collections, pathlib, re, sys
src = pathlib.Path(sys.argv[1]).expanduser()
text = src.read_text(encoding="utf-8", errors="replace")
pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
found = [a.lower().strip(".") for a in pattern.findall(text)]
unique = sorted(set(found))
print(f"addresses found: {len(found)}, unique: {len(unique)}, repeats: {len(found) - len(unique)}")
if not unique:
    print("no addresses in this file: the keys may be IDs, with the addresses in the values")
    sys.exit()
schema = re.findall(r"CREATE TABLE[^;]*;", text)
for s in schema:
    print("table:", s)
names = re.findall(r'"name"\s*:\s*"', text)
if names and src.suffix == ".json":
    print(f"KV entries listed: {len(names)}")
first = next((line for line in text.splitlines() if pattern.search(line)), "")
masked = pattern.sub("<address>", first.strip())
masked = re.sub(r"'(?:[^']|'')*'", "'<value>'", masked)
masked = re.sub(r'(:\s*)"[^"]*"', r'\1"<value>"', masked)
masked = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", "<ip>", masked)
print("first entry, values hidden:", masked[:300])
ending = lambda a: a.rsplit(".", 1)[-1]
aside_endings = {"ca", "uk", "eu", "at", "be", "bg", "hr", "cy", "cz", "dk", "ee", "fi", "fr", "de", "gr", "hu", "ie", "it", "lv", "lt", "lu", "mt", "nl", "pl", "pt", "ro", "sk", "si", "es", "se"}
looks_like_a_test = lambda a: "test" in a or "example." in a
aside = [a for a in unique if ending(a) in aside_endings]
check = [a for a in unique if a not in aside and looks_like_a_test(a)]
send = [a for a in unique if a not in aside and a not in check]
print("endings:", dict(collections.Counter(ending(a) for a in unique).most_common()))
print(f"other two-letter endings in the send list, worth a look: {sorted({ending(a) for a in send if len(ending(a)) == 2})}")
for name, rows in (("send-list.txt", send), ("set-aside.txt", aside), ("check-by-eye.txt", check)):
    (src.parent / name).write_text("".join(a + "\n" for a in rows), encoding="utf-8")
    print(f"{name}: {len(rows)}")
EOF
```

An ending such as `.com` says nothing about where someone lives, so the US-only split is rough. If the first entry shows a date, look at when the last real signup came in. The live homepage stopped using the form when the October rewrite was deployed, so a row dated after that is probably not a person. Look at it by eye. The total also decides how to send, below.

Last, make two empty files. `removed-hashes.txt` is the removal list. It holds no addresses, only a SHA-256 fingerprint of each removed one, so it can outlive every copy of the list without keeping anyone's address. `later-releases.txt` holds the addresses of people who reply to the launch email asking for news of later releases, the only people the spring note can go to.

```bash
touch "$HOME/PlantAdvocate-private/removed-hashes.txt"
```

```bash
touch "$HOME/PlantAdvocate-private/later-releases.txt"
```

Don't delete anything in Cloudflare yet. The data stays there after step 3; only the endpoint goes. Keep it until the launch email has gone. After that, each removal deletes that one address from Cloudflare as well ([Removals and replies](#removals-and-replies)). If step 3 slips by more than a week or two, run the same export once more just before it, to a new file name such as `waitlist-2.sql`, and run the check on that. If the count went up, look at the new rows by eye.

Then step 3 can go ahead as the handoff writes it.

## Before anything is sent

Six things have to be true before the launch email goes. The first three are the strategy's "three things" ([strategy.md](../strategy.md), "Before the site deploy"). The other three come from its launch-day plan.

1. The July form's wording supports one update. The git copy promised "Just an update when the beta opens", and the launch email is written as that update. If a July deployment shows different wording, read the email against it, and if that wording can't support a launch note, the email doesn't go.
2. There is a postal address for the footer. CAN-SPAM requires a valid physical postal address in every commercial email: a street address, a USPS post office box, or a private mailbox registered with a commercial mail receiving agency. The site lists none today, and a home address shouldn't go into anyone's inbox. The draft carries `[POSTAL ADDRESS]` until then. If no address is available, the email doesn't go, and neither do the replies to people who emailed for early access.
3. The privacy policy carries a clause that points account holders' "we don't send marketing email" (`site/privacy.html:138`) at the early-access paragraph, so nobody can quote one against the other. The strategy first put it in the launch-day site edit. The 2026-10-30 site fixes made it on the ship branch instead, so it goes live with step 3: the account paragraph now says the address you sign in with never goes on a mailing list and news about PlantAdvocate goes only to people who asked for it, and the early-access paragraph says a removal keeps only a one-way fingerprint, which is what the removal steps below do. The effective date stays October 20, and `site/README-SITE.md`'s check block tests both. If a mailing service sends the email, the same edit names it before any address is imported: in Data Sharing, which lists every company that receives data and names no mailing service today, with a line such as "[SERVICE] sends our early-access email and holds that list's addresses only for that.", and in the This Website paragraph. With individual sends, no change is needed.
4. The app is live, its product page loads, and the clean install from the store has passed: sign-in, a growing area, the Almanac and a hazard note. The 33 "Pet-safe" care notes are fixed in production, which the strategy requires before release anyway.
5. App Store Connect has given you a campaign link with the token `waitlist`. Apple says the Campaigns add button appears only once the app has analytics data, and to keep checking after the app has been live and getting downloads for at least 24 hours, which is why the email goes on L+1 or L+2. In App Store Connect, that is Analytics, then Acquisition, then Campaigns. The link has the shape `https://apps.apple.com/app/apple-store/id6792203800?pt=PROVIDER_TOKEN&ct=waitlist&mt=8`. Copy the one App Store Connect makes rather than building it by hand. If Campaigns still hasn't appeared by L+3, send with the plain `https://apps.apple.com/app/id6792203800` once it loads, because the list was promised an update (my judgement).
6. The sending route is chosen, and one test copy has gone to yourself and been opened on an iPhone, where the link opens the product page.

## How to send it

How to send depends on the count, which nobody knows until the export. The split is the strategy's judgement. For a few dozen addresses, send separate individual emails from support@plantadvocate.ai, the address people will reply to, one message per person, with nobody else's address in To, Cc or Bcc. That works only if your mail setup can send as that address. If it only forwards incoming mail, use a mailing service instead. For more than a few dozen, use a mailing service that adds the unsubscribe link and the postal address and handles opt-outs, once the privacy policy names it (item 3 above). Buttondown is free for up to 100 subscribers, and MailerLite's free plan allows 250 subscribers and 2,500 emails a month, both read by the strategy on 2026-10-24 ([Buttondown pricing](https://buttondown.com/pricing), [MailerLite pricing](https://www.mailerlite.com/pricing)). Check before choosing.

A service will ask you to verify plantadvocate.ai with DNS records in Cloudflare. That is what lets Gmail accept the mail, since every sender needs SPF or DKIM ([launch-playbook.md](../research/launch-playbook.md)). Import only `send-list.txt`, after running the fingerprint check in [Removals and replies](#removals-and-replies). Don't add the list to any automation, welcome sequence or second list. Use a mailing service only if it lets you turn off both open and click tracking for this send, and turn both off before sending. If the free plan you'd use can't, send individual emails from support@plantadvocate.ai instead. Click tracking would route the App Store link through the service's own redirect, the privacy policy says PlantAdvocate has "no tracking" (`site/privacy.html:134`), and a list built on that promise shouldn't be tracked. The campaign token still works without it. Set the From address and the Reply-To to support@plantadvocate.ai, with PlantAdvocate as the From name, never the service's own no-reply address, because CAN-SPAM wants header information that identifies the sender and the footer's reply opt-out has to reach you for at least 30 days. Paste the email as plain text, or pick the plainest template the service has.

Never add the addresses of people who signed in to the app. The privacy policy says account information is used only to run the app, and since the 2026-10-30 site fixes it says the address you sign in with never goes on a mailing list ([product-truth.md](../product-truth.md), section 5).

## The launch email, on L+1 or L+2

### Subject

Pick one. None of them misleads about what's inside, which is what CAN-SPAM requires of a subject line.

```text
PlantAdvocate is now available on the App Store
```
Characters: 47.

```text
PlantAdvocate for iPhone is ready
```
Characters: 33.

```text
From the PlantAdvocate early-access list: it's ready
```
Characters: 52.

The first is from the strategy's first draft of this email and follows Apple's naming exactly. The second is the shortest, for phones that cut a subject off early. The third reminds a reader who signed up months ago why it's in their inbox (my guess is that this helps with spam reports).

### Preview text

A mailing service has a separate field for this. In an individual send there is no such field, and the inbox shows the body's first line instead, which is why the body opens with the news.

```text
It's free, for iPhone, with no ads and no in-app purchases.
```
Characters: 59.

### Body

Fill in `[APP STORE LINK]` with the campaign link. Keep the bracketed United States line only if 1.1.3 is available in the United States alone, as the strategy recommends. Keep the unsubscribe-link line only if a mailing service sends it, and drop the brackets from "or use the unsubscribe link below" to match.

```text
PlantAdvocate for iPhone is now available on the App Store, free, with no ads and no in-app purchases:
[APP STORE LINK]

[For now it is available on the App Store in the United States.]

You're getting this email because you joined the PlantAdvocate early-access list on plantadvocate.ai, which promised an update when the beta opened. There was no open beta in the end, so this is that update. PlantAdvocate won't write to this list again. If you'd like news of later releases, reply and say so.

PlantAdvocate helps you look after the places you grow, from a windowsill to a back bed. Set up a growing area for each one, and it lists what needs addressing among its plants, with the reason and the source. A shade fern in full sun is flagged. So is a climber that will outgrow a 7 ft fence. Each area also puts forward good candidates: species with nothing on record against that spot and at least 1 thing confirmed for it. Add plant runs the same check before you save. The Species Almanac covers more than 990 species, with care facts cited to the sources that published them, and you can narrow it to what fits a growing area.

When a plant comes due, a check asks you to feel the soil, then tap Watered or Still damp. Either keeps your streak. Where a source records a plant as harmful to people or pets, its page says so, and a missing record is never treated as safe. Hazard notes are not medical or veterinary advice.

A few things to know before you install. It runs on iPhone only, and you sign in with Apple or Google. Older imported facts are labelled as not yet cited. The check schedules that reminders follow were written by PlantAdvocate for 129 common plants and are not cited. On iPhone models with Apple Intelligence, Add plant can also suggest likely matches from a photo, and you confirm the species before you save. On other iPhone models, you search instead.

If something reads wrong, or a plant you grow isn't there, reply to this email. It comes straight to the person who builds PlantAdvocate. And once you've used it for a while, a rating or review on the App Store, whatever you make of it, helps other people decide whether it's for them.

Thank you for waiting.

Allison Bowman
PlantAdvocate

--
This email is an advertisement for PlantAdvocate. You're receiving it because you joined the PlantAdvocate early-access list on plantadvocate.ai, which is used only to tell you about PlantAdvocate. To come off the list, reply and say so [or use the unsubscribe link below], and your address will be removed.
[UNSUBSCRIBE LINK, only if a mailing service sends this]
PlantAdvocate, [POSTAL ADDRESS]
```

### Why it reads the way it does

The reason sentence restates what the July form promised, "Just an update when the beta opens", and says the beta never opened, rather than calling a launch the news the list signed up for. Every product sentence comes from `docs/app-store/listing.md` or product-truth.md: the windowsill-to-back-bed opening, the needs-addressing list with the reason and the source, the shade fern and the 7 ft fence, good candidates with the truth sheet's rule and the check before saving, the Almanac line with the one species figure that may be quoted (listing.md, MORE THAN 990 SPECIES and the promotional text), Watered or Still damp, the hazard paragraph and its not-advice sentence, the labelled older facts, the 129 uncited schedules in the truth sheet's exact words, and photo suggestions only on iPhone models with Apple Intelligence, which you confirm before saving. The hazard paragraph leaves out listing.md's "These notes repeat what the sources publish", because some hazard clauses come from tables in the code rather than a cited page: the lily wording in `SPECIES_SPECIFIC_RISK` and the arum family's in `AROID_TOXICITY` (`garden-gnome/app/services/toxicity.py`), which strategy.md planned to cite or label by the end of February. Since 2026-10-30 they are labelled "PlantAdvocate's own summary" in the sentence, so once step 2's deploy is live listing.md's sentence, and the identical line the app now shows under each hazard note, no longer have that gap. The email can keep its shorter wording ([listing-proposals.md](listing-proposals.md) says why the listing quotes the app). The email names no organization, so it doesn't need the independence line. It follows Apple's naming: "PlantAdvocate for iPhone", "available on the App Store", "iPhone models with Apple Intelligence" ([launch-playbook.md](../research/launch-playbook.md)). It says nothing about AI, photo check-ups or symptoms, and it never calls a plant safe.

The limits paragraph is there on purpose. The strategy expects the first complaints to be the sign-in wall, a missing species and a pet plant with no record. Saying the limits before someone installs is cheaper than a one-star review from someone who expected a camera verdict. The "plant you grow isn't there" invitation turns the missing-species complaint into a reply instead of a review.

The rating line differs from the strategy's first draft, which said "if PlantAdvocate turns out to be useful, a rating on the App Store helps other people find it"; strategy.md now points here instead of carrying a draft. This version asks everyone the same way, "whatever you make of it", so it can't be read as asking only the people who liked the app. The FTC says asking only likely-happy customers "could violate the FTC Act", and Apple's guidelines bar filtered feedback ([launch-playbook.md](../research/launch-playbook.md)). It offers nothing in return, and it goes to every address on the send list.

The footer covers what CAN-SPAM asks of a commercial email: who sent it, that it is an advertisement, why the person is getting it, how to opt out, and a postal address. The Act lets a sender drop the advertisement label for someone who gave "prior affirmative consent" to the message ([15 U.S.C. 7704(a)(5)(B)](https://www.law.cornell.edu/uscode/text/15/7704)). The July form asked people to join a beta, which isn't plainly consent to a launch announcement, and the label costs one sentence, so it stays. The opt-out and the address are required either way. The opt-out takes a reply in any words, because CAN-SPAM allows asking for no more than a reply email and any request to stop counts. The footer says the address will be removed, which is what the privacy policy promises ("we'll remove it if you ask", `site/privacy.html:187`), and the removal steps below make it true: the address goes from Cloudflare, the private folder and any mailing service, and only a one-way fingerprint stays, which is enough to keep it from being emailed again by mistake. The email's one promise about the future is in the body: the list won't hear from PlantAdvocate again, except people who reply asking for news of later releases.

## Removals and replies

The reply address has to keep accepting opt-out replies for at least 30 days after the send, and each opt-out has to be honoured within 10 business days ([launch-playbook.md](../research/launch-playbook.md)). Treat any request to stop, however it's worded, as a removal. The privacy policy says of an early-access address that "we'll remove it if you ask" (`site/privacy.html:187`), so a removal takes the address out of everything that holds it, keeping only its fingerprint, and you send nothing more to it, not even a confirmation. Do the same for an unsubscribe recorded by a mailing service, and take bounced addresses off the same way.

First, delete it in Cloudflare. In KV, if the keys are addresses, this deletes it. If the keys are IDs, find the entry in the dashboard (Workers KV, the namespace, the KV Pairs tab) and delete it there.

```bash
npx wrangler kv key delete 'ADDRESS' --namespace-id=NAMESPACE_ID --remote
```

In D1, use the table and column names the check printed.

```bash
npx wrangler d1 execute DATABASE_NAME --remote --command="DELETE FROM TABLE_NAME WHERE lower(COLUMN_NAME) = lower('ADDRESS')"
```

In a mailing service, delete the subscriber rather than only unsubscribing them; its help pages say how. Then run this, with the address in place of `ADDRESS`. It records the address's fingerprint in `removed-hashes.txt` and deletes every line that holds the address from every file in the private folder, including the exports, `send-list.txt`, `set-aside.txt`, `check-by-eye.txt` and `later-releases.txt`. It prints file names and line counts, never the address.

```bash
python3 - "$HOME/PlantAdvocate-private" 'ADDRESS' <<'EOF'
import hashlib, pathlib, re, sys
folder, address = pathlib.Path(sys.argv[1]), sys.argv[2].strip().lower()
pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
digest = hashlib.sha256(address.encode("utf-8")).hexdigest()
hashes = folder / "removed-hashes.txt"
hashes.touch()
if digest not in hashes.read_text(encoding="utf-8").split():
    with hashes.open("a", encoding="utf-8") as f:
        f.write(digest + "\n")
for path in sorted(folder.iterdir()):
    if not path.is_file() or path.name == hashes.name:
        continue
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    kept = [line for line in lines if address not in {a.lower().strip(".") for a in pattern.findall(line)}]
    if len(kept) != len(lines):
        path.write_text("".join(kept), encoding="utf-8")
        print(f"{path.name}: {len(lines) - len(kept)} line(s) removed")
print("fingerprint recorded in removed-hashes.txt")
EOF
```

Before any send, the launch email or the spring note, run the fingerprint check. It drops from `send-list.txt` and `later-releases.txt` any address whose fingerprint is in `removed-hashes.txt`, which catches an address that came back through a fresh export, and prints counts only.

```bash
python3 - "$HOME/PlantAdvocate-private" <<'EOF'
import hashlib, pathlib, sys
folder = pathlib.Path(sys.argv[1])
gone = set((folder / "removed-hashes.txt").read_text(encoding="utf-8").split())
for name in ("send-list.txt", "later-releases.txt"):
    path = folder / name
    if not path.exists():
        continue
    rows = path.read_text(encoding="utf-8").split()
    keep = [a for a in rows if hashlib.sha256(a.strip().lower().encode("utf-8")).hexdigest() not in gone]
    path.write_text("".join(a + "\n" for a in keep), encoding="utf-8")
    print(f"{name}: {len(keep)} to send, {len(rows) - len(keep)} dropped")
EOF
```

Both scripts were tested on fake data: mixed case and stray spaces in the address, an address that is part of a longer one (left alone), SQL rows and plain lists.

When someone replies asking for news of later releases, add their address on its own line to `later-releases.txt`, in a text editor, and nowhere else. That reply is the only consent the spring note rests on.

Reply to everything else that comes back, in the caretaker voice the strategy describes for review replies: thank the person, say what was fixed or what the app can't check, and never argue, promise a feature or soften a hazard. A reply about a wrong fact is worth more than a rating. Check it against the species page's sources and fix it in the catalog and in production.

## The spring note

The strategy allows the list one more email at most, and only for a genuine release. The July form narrows that further. It promised "Just an update when the beta opens", which the launch email is, and only the FAQ's "among the first invited as new capabilities roll out" could be stretched to cover a second email to everyone, which is a thin reading. So the launch email tells the list it won't hear from PlantAdvocate again, and this note goes only to the people in `later-releases.txt`, who replied asking for news of later releases. If a July deployment shows the form clearly promised more than one update, that could change; the git copy doesn't.

Send this one only if a version after 1.1.3 is live on the App Store by March 2027 and has at least one change a person would notice. The scene-adopted build Apple's April 2027 rule requires is that release. If its only changes are invisible, such as the scene life cycle and the ratings prompt, skip the note rather than dress it up. The window is March to mid-April, early in the spring push. Run the fingerprint check, then send it to the addresses in `later-releases.txt`, as individual emails if there are a few dozen or fewer, with the `waitlist` token again. A date range in App Analytics separates the two sends, and one token pooled across both is likelier to clear Apple's floor of five than two would be (my judgement).

The "What's new" line is copied from the What's New text App Review approved for that version, and nothing else. That is the one rule that keeps it true. It doesn't ask for a rating, because the same build asks returning users itself, through Apple's own sheet.

### Subject

```text
PlantAdvocate [VERSION] is now available
```
Characters: 40, with `[VERSION]` as written; the real version number is shorter.

```text
Before the spring beds: PlantAdvocate [VERSION]
```
Characters: 47, with `[VERSION]` as written.

### Preview text

```text
What changed, and how to check a bed before anything goes in.
```
Characters: 61.

### Body

```text
PlantAdvocate [VERSION] is now available on the App Store:
[APP STORE LINK]

You're getting this because you replied to the PlantAdvocate launch email in [LAUNCH MONTH] and asked for news of later releases.

What's new: [ONE TO THREE SENTENCES, COPIED FROM THIS VERSION'S APPROVED WHAT'S NEW TEXT]

If you're planting this spring, describe each bed once: whether it's in the ground or raised, how much room and headroom it has, and how much sun it gets. Add plant then checks each new plant against it before you save, with the reason and the source. A shade fern in full sun is flagged. So is a climber that will outgrow a 7 ft fence. The check looks at things such as sun, soil, space and headroom. It doesn't judge cold or give planting dates, so it can't tell you whether a plant will come through your winter.

If anything reads wrong, reply to this email. It still comes straight to the person who builds PlantAdvocate.

Allison Bowman
PlantAdvocate

--
This email is an advertisement for PlantAdvocate. You're receiving it because you asked for news of later PlantAdvocate releases, in reply to the launch email sent to the early-access list on plantadvocate.ai. To stop, reply and say so [or use the unsubscribe link below], and your address will be removed.
[UNSUBSCRIBE LINK, only if a mailing service sends this]
PlantAdvocate, [POSTAL ADDRESS]
```

The bed description uses the listing's own surfaces for a growing area (an in-ground bed, a raised bed), and the checks named are among the fit engine's real axes (`garden-gnome/app/services/fit.py`, `Axis`), which is why it says "things such as". The last sentence of that paragraph says plainly what the app doesn't do, because the fit engine deliberately doesn't judge cold (`fit.py:41-49`) and the strategy warns that spring readers may want a planner. The spring promotional text in [listing-proposals.md](listing-proposals.md) never mentions frost, zones or planting dates; this note, sent to people who asked to hear from PlantAdvocate, can say once, plainly, that the app doesn't answer them. Backend changes that ship without a build, such as a change to the hazard sentences, appear in no What's New text, so they stay out of this note.

## When the list is done

After the spring note goes, or by 30 June 2027 if it never does, the list has done what it was kept for. Decide then whether to delete it: the KV namespace or D1 database in Cloudflare, the files in the private folder, `later-releases.txt` among them, and the audience in any mailing service. `removed-hashes.txt` holds no address, so it can stay until the last copy of the list is gone; delete it last. Each of those deletions is yours, and none can be undone.

## The people who emailed for early access

People who wrote to support@plantadvocate.ai asking for early access are a separate group and are not on this list. The homepage told them "We'll write back when you can download PlantAdvocate", and the privacy policy says an address from a message is used "only to reply" ([launch-playbook.md](../research/launch-playbook.md)). So each gets an individual reply in their own thread, on L+1 to L+3. Keep it short and personal. Open with "You asked to hear when you could download PlantAdvocate. It's now available on the App Store:" and the `waitlist` campaign link, as the runbook says, since these people asked too. Add the launch email's limits paragraph ("A few things to know before you install...") and its reply line if you like, but not its list paragraph ("You're getting this email because..."). The reply still needs a short footer, because a launch note is commercial even when someone asked for it ([launch-playbook.md](../research/launch-playbook.md)), and the runbook puts the postal address under your name for the same reason. Under the signature, put "If you'd rather not hear from PlantAdvocate again, reply and say so." and then "PlantAdvocate, [POSTAL ADDRESS]". The advertisement label can go, since these people asked for the news. Like the launch email, these replies wait until there is a postal address. Don't add them to the list.

## The calendar

| When | What | Who |
|---|---|---|
| This week, before step 3 | Sign in, find the store, check the July form's wording against a deployment, export, run the check, make `removed-hashes.txt` and `later-releases.txt` | Allison, about half an hour (my estimate) |
| Just before step 3, if it slipped | Export once more and compare the count | Allison |
| Before L | A postal address, which the launch email and the early-access replies both wait on; the privacy clause, and the mailing service's name if one sends, drafted into the launch-day site edit; the sending route chosen | Allison |
| L | Release, the clean install, the launch-day site edit. Nothing is sent | Allison |
| L+1 or L+2 | The campaign link, the fingerprint check, a test to yourself, then the launch email | Allison |
| L+1 to L+3 | Individual replies to the early-access emailers | Allison |
| L+1 to L+30 | Removals within 10 business days, from Cloudflare and the private folder too; requests for later news into `later-releases.txt`; replies to everything else | Allison |
| March to mid-April 2027 | The spring note, only to `later-releases.txt` and only if a release with a visible change is live | Allison |
| By 30 June 2027 | Decide whether to delete the list | Allison |
