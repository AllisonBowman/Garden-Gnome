"""Groundedness guard for server-side model output.

The phone has `driftsFromFact` in ``mobile/src/gnomeVoice/restyle.ts``; until
now server LLM output reached users on prompt discipline alone. This is the
Python counterpart, shared by the advisor and the vision backend, and it
enforces the same persona contract those prompts state (see
``app.services.persona``).

Ground rule: every check fails CLOSED. A false positive costs the user only
the plain rule-based wording; a false negative ships unverified model output
with an authoritative badge on it, which is exactly the failure the alignment
plan exists to prevent.
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger("plantadvocate.grounding")

# Care activities a model could plausibly invent. Stems, so "watering",
# "fertilise"/"fertilize", "repotted" all match. Mirrors CARE_STEMS in
# restyle.ts -- keep the two lists in step.
CARE_STEMS = (
    "water", "fertili", "feed", "mist", "humidif", "prune", "trim", "repot",
    "rotate", "clean", "toxic", "poison",
)

_ONES = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}

# Longest-first so "seventeen" never matches as "seven".
_TENS_ALT = "|".join(sorted(_TENS, key=len, reverse=True))
_ONES_ALT = "|".join(sorted(_ONES, key=len, reverse=True))

_COMPOUND_RE = re.compile(rf"\b({_TENS_ALT})[\s-]+({_ONES_ALT})\b", re.I)
_TENS_RE = re.compile(rf"\b({_TENS_ALT})\b", re.I)
_ONES_RE = re.compile(rf"\b({_ONES_ALT})\b", re.I)
_DIGITS_RE = re.compile(r"\d+")

_PLACEHOLDER_RE = re.compile(r"\[[^\]]*\]|\{[^}]*\}")
_PLACEHOLDER_WORDS_RE = re.compile(r"\b(your name|plant owner|insert)\b", re.I)
_FIRST_PERSON_RE = re.compile(r"\bi\b", re.I)
_PROMISE_RE = re.compile(r"\bi(?:'ll|\s+will)\b[^.!?]*\b(send|remind|notify|alert)", re.I)
_REMINDER_RE = re.compile(r"\b(reminders?|notifications?)\b", re.I)
_GREETING_RE = re.compile(r"^dear\b", re.I)
_CLOSING_RE = re.compile(
    r"^(love|sincerely|yours(?:\s+truly)?|warmly|fondly)\s*[,.]?$", re.I
)
_SENTENCE_SPLIT_RE = re.compile(r"[.!?\n]+")


def normalize_number_words(text: str) -> str:
    """"thirty-five days" -> "35 days", so the digit-subset rule can see it."""
    text = _COMPOUND_RE.sub(
        lambda m: str(_TENS[m.group(1).lower()] + _ONES[m.group(2).lower()]), text
    )
    text = _TENS_RE.sub(lambda m: str(_TENS[m.group(1).lower()]), text)
    return _ONES_RE.sub(lambda m: str(_ONES[m.group(1).lower()]), text)


def _numbers(text: str) -> list[str]:
    return _DIGITS_RE.findall(normalize_number_words(text))


def grounding_failures(
    facts: str,
    output: str,
    *,
    check_care_stems: bool = True,
    max_chars: int | None = None,
) -> list[str]:
    """Every way ``output`` departs from ``facts``. Empty list means grounded.

    ``check_care_stems`` is disabled for vision, where the model legitimately
    describes what it sees in a photo (spots, wilting) that no fact mentions;
    the number, template, and first-person checks still apply there because
    those are care *claims*, not observations.
    """
    stripped = output.strip()
    if not stripped:
        return ["empty"]

    failures: list[str] = []
    facts_lower = facts.lower()
    out_lower = stripped.lower()

    limit = max_chars if max_chars is not None else max(600, len(facts) * 4)
    if len(stripped) > limit:
        failures.append("too-long")

    fact_numbers = set(_numbers(facts_lower))
    if any(n not in fact_numbers for n in _numbers(out_lower)):
        failures.append("invented-number")

    if check_care_stems and any(
        stem in out_lower and stem not in facts_lower for stem in CARE_STEMS
    ):
        failures.append("invented-care-activity")

    if _PLACEHOLDER_RE.search(stripped) or _PLACEHOLDER_WORDS_RE.search(stripped):
        failures.append("placeholder")

    # The caretaker performs all care; the gnome only observes and advises.
    for sentence in _SENTENCE_SPLIT_RE.split(stripped):
        if _FIRST_PERSON_RE.search(sentence) and any(
            stem in sentence.lower() for stem in CARE_STEMS
        ):
            failures.append("first-person-care")
            break

    # Reminders and notifications are the app's job; a model cannot know one
    # is actually scheduled.
    if _PROMISE_RE.search(stripped) or (
        _REMINDER_RE.search(stripped) and not _REMINDER_RE.search(facts)
    ):
        failures.append("commitment")

    lines = [ln.strip() for ln in stripped.splitlines() if ln.strip()]
    if (lines and _GREETING_RE.search(lines[0])) or any(
        _CLOSING_RE.match(ln) for ln in lines
    ):
        failures.append("letter-scaffolding")

    return failures


def is_grounded(facts: str, output: str, **kwargs) -> bool:
    return not grounding_failures(facts, output, **kwargs)


def log_rejection(surface: str, failures: list[str], output: str) -> None:
    """Record a guarded rejection for prompt tuning.

    Logs the reasons and a short excerpt only -- never the full output, which
    may quote owner-recorded history, and never the photo.
    """
    excerpt = output.strip().replace("\n", " ")[:120]
    logger.warning(
        "grounding guard rejected %s output (%s): %r", surface, ", ".join(failures), excerpt
    )
