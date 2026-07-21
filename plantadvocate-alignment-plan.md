# PlantAdvocate — AI Alignment Fix Plan

Implementation plan for Claude Code. Scope: every place a model's output can
drift from the facts it was given, misattribute who did what, or leak
developer-facing text to an end user. Triggered by two screenshots from the
current build (committed as evidence and regression fixtures):

- `docs/screenshots/2026-07-20-gnome-voice-letter.png` — the on-device gnome
  voice restyled rule-based advice into a fill-in-the-blank letter: signed
  "Love, **[Your Name]**", spelled every number as words ("thirty-five
  days"), claimed the gnome performed the owner's care ("**I've watered**
  your lovely Front Yard Sunflower"), and promised app behavior that isn't a
  care fact ("**I'll send you a reminder** when it's time to fertilize").
  The `rule-based • gnome voice` badge confirms the drift guard passed it.
- `docs/screenshots/2026-07-20-photo-diagnosis-stub.png` — "Gnome's
  Findings" rendered `[STUB] … Set VISION_BACKEND=ollama and pull a vision
  model…` — server setup instructions shown to a consumer.

Work phases in order; each ends with the backend suite green and the mobile
typecheck clean. Follows the handoff rules (rebrand: no "Garden Gnome"
strings in user-facing copy; "care engine" not "AI"; gnome = mascot).

## Ground rules

- **Guards fail closed to the flat text.** Every check may false-positive;
  the cost is only that the user sees the plain rule-based wording. Never
  ship a check whose failure mode is showing unverified model output.
- **Tone may never change substance.** The rule engine and curated catalog
  are the sole sources of facts, actions, and commitments. Any restyle that
  adds, changes, or re-attributes one is discarded.
- **Developer text never reaches users or the data layer.** Setup
  instructions, env var names, and tool names live in server logs only.
- No schema migrations in this plan.

## Already done (this branch)

The Ollama backend has since been **removed entirely** (Allison's call:
"scrub the llama framework") — vision is stub-only, the advisor is
stub/anthropic, and the stub texts no longer name any setup tooling.
`/ai/status` + `vision_status()` report readiness (always not-ready today).
With diagnosis shipping disabled, **Phase 0 items 1 and 4 below are
pre-iOS-build blockers** — the stub is the experience users will see.

---

## Phase 0 — Stop shipping developer text (smallest, do first)

1. **Rewrite the diagnosis stub copy** (`vision._diagnose_stub`) in the
   voice of the identify stub: photo received, check-ups aren't enabled yet.
   The `[STUB]` marker and byte count go to a `logger.info` instead. The
   mobile "diagnosis not enabled yet" chip already covers status.
2. **The advisor backend gets a friendly-failure treatment.**
   `_advise_anthropic` raises RuntimeErrors whose text ("Check
   ANTHROPIC_API_KEY in .env") flows through the router's 503 `detail` to
   the client. Introduce one `AdvisorUnavailable` with a user-presentable
   message, technical cause logged. Same for
   `catalog.generate_species_profile`'s 503 path.
3. **Mobile error copy.** Replace "Could not diagnose the photo. Check the
   backend connection." and the advice/identify equivalents with
   caretaker-appropriate copy ("The Gnome couldn't examine the photo just
   now — try again in a few minutes."). Surface the server's 503 `detail`
   only if present (it is now user-safe); never invent dev instructions.
4. **Keep dev/stub text out of the care history.** The diagnose router
   auto-logs `Photo diagnosis: {text}` as a CareLog note — including stub
   text, so `[STUB]…` is filed to the plant's permanent timeline (visible in
   the first screenshot's history) **and** fed back into future LLM prompts
   via `recent_logs` in `advisor._build_prompt`. Fix both ends:
   - only auto-log when `backend != "stub"` and the call succeeded;
   - when building advisor prompts, exclude `CareLog` notes that begin with
     `Photo diagnosis:` from verbatim inclusion (summarize to "photo
     check-up filed N days ago") so model output never becomes model input
     masquerading as owner history.

**Accept when:** grep of user-visible strings (mobile + API responses) finds
no env var names, no `[STUB]`, no model-server or `API key` strings; a stub
diagnosis run leaves no `[STUB]` CareLog behind; suite green.

## Phase 1 — One persona contract (extends 1.0.1 plan Phase 1)

The 1.0.1 plan already calls for a single persona module; this phase makes
the *alignment rules* part of that contract, because three of the four
screenshot defects are persona violations the prompt never forbade.

- `mobile/src/gnome/persona.ts` + a matching backend preamble
  (`app/services/persona.py`) used by advisor and vision prompts. The
  contract, stated in the prompt AND enforced by Phase 2/3 guards:
  - Speak **to the caretaker** (second person); the plant is third person,
    by nickname.
  - **The caretaker performs all care.** The gnome observes, advises, and
    celebrates — it never waters, fertilizes, or claims to ("I've watered…"
    is forbidden by construction).
  - **No promises about app behavior.** Reminders/notifications are the
    app's job; care facts in, care advice out. If it's not in the CARE
    FACTS, it's not in the note.
  - **No letter scaffolding**: no greeting lines, no closings, no
    signature placeholders. One fixed sign-off, appended **by code, not by
    the model**: `— the Gnome 🧙`. (The 1.0.1 plan's suggested "your Garden
    Gnome" signature conflicts with the rebrand audit's no-"Garden Gnome"
    rule — use "the Gnome".)
  - **Numbers stay digits** ("35 days", never "thirty-five days") — this is
    what makes the Phase 2 number guard verifiable.
- Route every gnome-voiced surface through it; delete inline persona
  fragments (`restyle.ts` PERSONA, advisor/vision SYSTEM_INSTRUCTIONs gain
  the shared preamble).

**Accept when:** one persona definition per platform; snapshot tests assert
second-person address, third-person plant, code-appended sign-off; no other
prompt text defines voice.

## Phase 2 — Drift guard v2 (mobile `restyle.ts`)

`driftsFromFact` only checks digit sequences and care-activity stems — the
screenshot letter walked through it. Extend it; every new check fails closed
to the flat text:

1. **Number-word normalization.** Before the digit check, normalize spelled
   numbers in the styled text ("one"…"ninety-nine", hyphenated compounds,
   "a week"/"a day" → 7/1 is out of scope — keep to cardinal words). After
   normalization, the existing rule applies: every number in the styled text
   must literally appear in the fact. "thirty-five days" then either
   verifies as 35 or kills the restyle.
2. **Placeholder/template detection.** Reject styled text containing `[`…`]`
   or `{`…`}` spans, or case-insensitive `your name` / `plant owner` /
   `insert` — a template artifact is never a valid note. (Catches "Love,
   [Your Name]" and "Dear Plant Owner".)
3. **First-person action claims.** Reject when a first-person subject
   (`I`, `I've`, `I'll`, `I have`, `I will`, `I just`) occurs in the same
   sentence as a care stem (existing `CARE_STEMS` list). The gnome may say
   "you watered it 2 days ago", never "I've watered it" or "I'll hold off
   on watering".
4. **Commitment language.** Reject `I'll/I will + send/remind/notify/alert`
   and the words `reminder`/`notification` when absent from the fact — the
   restyle layer cannot know whether a reminder is actually scheduled.
5. **Letter scaffolding.** Reject `dear `-prefixed first lines and
   `love,`/`sincerely`/`yours` closings; the sign-off is appended by code
   (Phase 1), so any model-written signature is drift.
6. **Regression fixture:** the exact letter from
   `docs/screenshots/2026-07-20-gnome-voice-letter.png` (transcribed into
   the test) must be rejected by at least three independent checks; the
   legitimate flat stub output for the same plant must still pass restyle
   when the model behaves.

**Accept when:** the screenshot letter can never render again (test-proven),
existing well-behaved restyle fixtures still style, typecheck clean.

## Phase 3 — Server-side groundedness guard

Today `driftsFromFact` exists only on the phone; server LLM output
(`_advise_anthropic`, and any future vision backend) reaches users on
prompt discipline alone.

- Port the guard to Python (`app/services/grounding.py`), shared by advisor
  and vision: number-subset check (against the prompt's fact block),
  care-stem check, template/placeholder check, first-person action-claim
  check, length bounds.
- **Advisor:** guard failure falls back to `_advise_stub` output (always
  computable) with the backend reported as `stub` plus a `guarded: true`
  flag so the client badge stays honest.
- **Vision diagnosis (when a backend returns):** the model legitimately
  describes photo observations that aren't in the facts, so scope the guard
  to *care claims*: numbers must come from the fact block, no invented
  schedule intervals, no template artifacts. On failure, retry once, then
  return a user-safe unavailable message rather than an ungrounded
  diagnosis.
- Log every guarded rejection (`logger.warning` with the offending span,
  not the full photo/PII) — these are the training set for tightening
  prompts, and the counterpart to the in-app "Report this result" queue.

**Accept when:** unit tests feed adversarial model outputs (invented
numbers, "I watered it", `[Your Name]`, invented "repot now") through both
paths and the user-visible result is always either grounded text or the
honest fallback; suite green.

## Phase 4 — Verification sweep

1. Golden-path tests: stub advice → restyle-accepted fixture → rendered
   output carries the code-appended sign-off and the `gnome voice` badge;
   guard-rejected fixture renders flat text with no badge.
2. Cross-surface audit (one checklist, committed with results): every
   AI-touched surface — advice card, diagnosis card, identify chips,
   timeline notes, notifications — checked against the persona contract and
   the no-dev-text rule.
3. Re-run the handoff section 2 audit (report affordances present, no
   "Garden Gnome" user-facing strings — including the new sign-off).

**Accept when:** checklist committed with all boxes ticked; both screenshots
re-taken on a dev build show the fixed behavior (grounded gnome note with
sign-off; friendly not-enabled diagnosis copy).

---

## Explicit non-goals

- Improving model *quality* (better restyles, smarter diagnoses) — this
  plan only ensures bad output can't reach users.
- Verifying spelled-out numbers beyond cardinal words ("a fortnight") —
  the persona demands digits; normalization is belt-and-suspenders.
- Cloud advisor enablement decisions (1.0.1 plan Phase 3 item 5) —
  unchanged.

## Suggested kickoff prompt

> Read plantadvocate-alignment-plan.md. Implement Phase 0 and Phase 1, run
> the backend suite and mobile typecheck, and stop. Report the Phase 0
> accept-when grep results before starting Phase 2.
