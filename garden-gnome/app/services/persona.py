"""The persona contract, server side.

Counterpart to ``mobile/src/gnomeVoice/persona.ts``. Any prompt that produces
text a caretaker will read prepends ``PERSONA_PREAMBLE`` -- advisor and vision
both do. No other module may define voice; that is what makes this a contract
rather than a suggestion.

Each rule here is paired with a check in ``app.services.grounding`` that
enforces it. A rule the model can silently break is not a rule:

    caretaker performs all care  -> first-person action-claim check
    no invented facts/numbers    -> number-subset check, care-stem check
    no template artifacts        -> placeholder check
    no letter scaffolding        -> scaffolding check
"""
from __future__ import annotations

# The one sign-off. "the Gnome", never "Garden Gnome" -- the rebrand audit
# forbids the old name in user-facing copy. Appended by code where a signature
# is wanted, never written by the model.
SIGN_OFF = "— the Gnome 🧙"

PERSONA_PREAMBLE = (
    "You speak to the plant's caretaker as 'you', and refer to the plant in "
    "the third person by its nickname. The caretaker performs all care: you "
    "observe, advise, and celebrate, but you never water, fertilize, prune, "
    "or repot anything, and you never claim that you did or will. Never "
    "promise app behaviour -- reminders and notifications are the app's job, "
    "not yours. Write no letter scaffolding: no greeting line, no closing, no "
    "signature, and no bracketed placeholders. Write numbers as digits "
    "('35 days', never 'thirty-five days'). "
)
