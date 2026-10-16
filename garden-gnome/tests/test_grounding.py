"""Adversarial model output must never reach a user ungrounded.

Mirrors mobile/src/gnomeVoice/restyle.test.ts — the two guards enforce the
same persona contract, so they are tested against the same defects.
"""
import pytest

from app.services.grounding import (
    grounding_failures,
    is_grounded,
    normalize_number_words,
)

FACTS = (
    "SPECIES CARE FACTS (authoritative):\n"
    "- Common name: Sunflower\n"
    "CARE SCHEDULES (authoritative):\n"
    "- Watering: every 2-3 days\n"
    "- Fertilizing: every 35-45 days\n"
)

# The defect from docs/screenshots/2026-07-20-gnome-voice-letter.png, which
# shipped with an authoritative badge on it.
SCREENSHOT_LETTER = (
    "Dear Plant Owner,\n\n"
    "I've watered your lovely Front Yard Sunflower two days ago, and I'll "
    "hold off on watering it again until the next window opens in three "
    "days. I'll send you a reminder when it's time to fertilize your plant.\n\n"
    "Love,\n\n"
    "[Your Name]"
)


class TestNumberWords:
    def test_resolves_compounds(self):
        assert normalize_number_words("thirty-five days") == "35 days"
        assert normalize_number_words("thirty five days") == "35 days"

    def test_resolves_standalone_cardinals(self):
        assert normalize_number_words("two days") == "2 days"

    def test_matches_longest_first(self):
        assert normalize_number_words("seventeen") == "17"

    def test_leaves_embedded_words_alone(self):
        assert normalize_number_words("none of the tenants") == "none of the tenants"


class TestScreenshotLetter:
    def test_is_rejected(self):
        assert not is_grounded(FACTS, SCREENSHOT_LETTER)

    def test_trips_at_least_three_independent_checks(self):
        assert len(set(grounding_failures(FACTS, SCREENSHOT_LETTER))) >= 3

    def test_flags_each_defect(self):
        failures = grounding_failures(FACTS, SCREENSHOT_LETTER)
        assert "placeholder" in failures
        assert "first-person-care" in failures
        assert "commitment" in failures
        assert "letter-scaffolding" in failures


class TestAdversarialOutputs:
    def test_invented_number(self):
        assert "invented-number" in grounding_failures(
            FACTS, "Fertilize it every 90 days."
        )

    def test_invented_care_activity(self):
        assert "invented-care-activity" in grounding_failures(
            FACTS, "You should repot it this week."
        )

    def test_first_person_care_claim(self):
        assert "first-person-care" in grounding_failures(FACTS, "I watered it for you.")

    def test_caretaker_acting_is_fine(self):
        assert "first-person-care" not in grounding_failures(
            FACTS, "You watered it 2 days ago."
        )

    def test_invented_repot_advice(self):
        assert grounding_failures(FACTS, "Repot now — it needs a bigger pot.")

    def test_empty_output(self):
        assert grounding_failures(FACTS, "   ") == ["empty"]

    def test_rambling_output(self):
        assert "too-long" in grounding_failures(FACTS, "x" * 5000)


class TestVisionScope:
    """Vision describes what it sees; that is not drift."""

    def test_photo_observations_pass_without_care_stem_check(self):
        observation = (
            "The lower leaves show brown spots and slight curling, and the "
            "soil surface looks compacted."
        )
        assert is_grounded(FACTS, observation, check_care_stems=False)

    def test_care_claims_are_still_guarded_in_vision(self):
        assert "invented-number" in grounding_failures(
            FACTS, "Spots on the leaves. Water it every 90 days.", check_care_stems=False
        )

    def test_templates_still_rejected_in_vision(self):
        assert "placeholder" in grounding_failures(
            FACTS, "Hello [Owner], the leaves look pale.", check_care_stems=False
        )


class TestGroundedOutput:
    def test_a_well_behaved_answer_passes(self):
        good = (
            "Your Sunflower was watered 2 days ago, so it is content for now. "
            "Fertilizing runs every 35-45 days."
        )
        assert grounding_failures(FACTS, good) == []


# The audit's three inversions, which passed the stem check because the stem
# was present on both sides (mobile restyle.test.ts carries the same cases).
TOXIC_FACTS = (
    "SPECIES CARE FACTS (authoritative):\n"
    "- Common name: Fern\n"
    "- Toxic to pets: yes\n"
    "CARE SCHEDULES (authoritative):\n"
    "- Watering: every 7-10 days\n"
)
NO_RECORD_FACTS = TOXIC_FACTS.replace("- Toxic to pets: yes", "- Toxic to pets: no record")
HOLD_OFF_FACTS = (
    TOXIC_FACTS
    + "Rain likely (70% on 2026-07-24) — hold off watering; the sky may do it for you.\n"
)


class TestSafetyClaims:
    def test_a_warning_turned_into_an_assurance_is_rejected(self):
        failures = grounding_failures(
            TOXIC_FACTS, "Ferny is non-toxic, so your cats can nibble freely.")
        assert "safety-claim" in failures

    def test_no_record_turned_into_safe_is_rejected(self):
        failures = grounding_failures(
            NO_RECORD_FACTS, "Ferny is perfectly safe around pets and children.")
        assert "safety-claim" in failures

    @pytest.mark.parametrize("claim", [
        "It is harmless.", "A pet-friendly choice.", "The fronds are edible.",
        "It is not toxic.", "Nontoxic, so relax.",
    ])
    def test_each_assurance_word_is_caught(self, claim):
        assert "safety-claim" in grounding_failures(TOXIC_FACTS, claim)

    def test_a_term_the_facts_use_may_be_repeated(self):
        facts = TOXIC_FACTS + "- Edible: grown to eat\n"
        assert "safety-claim" not in grounding_failures(
            facts, "Fern is edible, as its sources say.")

    def test_safety_claims_are_checked_for_vision_too(self):
        assert "safety-claim" in grounding_failures(
            TOXIC_FACTS, "The leaves look healthy and the plant is harmless.",
            check_care_stems=False)


class TestPolarity:
    def test_hold_off_turned_into_water_now_is_rejected(self):
        assert "polarity" in grounding_failures(
            HOLD_OFF_FACTS.replace("- Watering: every 7-10 days\n", ""),
            "Water Ferny today.")

    def test_toxic_turned_into_not_toxic_is_rejected(self):
        failures = grounding_failures(TOXIC_FACTS, "Ferny is not toxic to your cats.")
        assert "polarity" in failures

    def test_a_plain_schedule_turned_into_skip_is_rejected(self):
        """Fails closed: the facts never say to skip, so neither may the
        model, even where skipping would be reasonable."""
        assert "polarity" in grounding_failures(
            TOXIC_FACTS, "Skip watering this week.")

    def test_a_clause_about_the_log_is_history_not_an_instruction(self):
        """'No watering logged yet' restates the history block; it is not
        'do not water'."""
        facts = TOXIC_FACTS + "RECENT CARE HISTORY: none logged yet.\n"
        assert "polarity" not in grounding_failures(
            facts, "Ferny has no watering logged yet; every 7-10 days suits it.")

    def test_the_same_polarity_passes(self):
        assert "polarity" not in grounding_failures(
            HOLD_OFF_FACTS, "Rain is likely, so hold off watering Ferny.")
        assert "polarity" not in grounding_failures(
            TOXIC_FACTS, "Ferny is toxic to pets, so keep it up high.")
