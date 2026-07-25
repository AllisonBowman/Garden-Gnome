"""The advisor never hands a user ungrounded model output.

Phase 3 of the alignment plan: when a model backend drifts from the facts it
was given, the advice falls back to the deterministic stub and reports itself
as "stub", so the client badge describes what the user is actually reading.
"""
import pytest

from app.models.models import Species, Plant, LightNeed, MaturityStage, CareType, CareSchedule
from app.services import advisor
from app.services.advisor import get_care_advice


def make_species():
    return Species(
        common_name="Test Fern",
        scientific_name="Testus fernus",
        light_need=LightNeed.bright_indirect,
        humidity_pct_min=40,
        humidity_pct_max=60,
        temp_f_min=60,
        temp_f_max=85,
        soil_type="well-draining",
        toxic_to_pets=False,
    )


def make_plant():
    return Plant(nickname="Ferny", species_id=1, maturity_stage=MaturityStage.mature)


def make_schedules():
    return [CareSchedule(species_id=1, care_type=CareType.water,
                         interval_days_min=5, interval_days_max=9)]


@pytest.fixture
def fake_backend(monkeypatch):
    """Register a fake 'anthropic' backend returning whatever text we want."""
    def _install(text):
        monkeypatch.setitem(advisor._BACKENDS, "anthropic", lambda *a, **k: text)
        monkeypatch.setattr(advisor, "BACKEND", "anthropic")
        monkeypatch.setattr(advisor, "SYMPTOMS_BACKEND", "anthropic")
    return _install


def advise():
    return get_care_advice(make_species(), make_plant(), [], make_schedules())


def test_ungrounded_advice_falls_back_to_the_stub(fake_backend):
    fake_backend("I've watered Ferny for you. I'll send a reminder in 90 days.")
    result = advise()

    assert result["guarded"] is True
    # The badge must not claim a model wrote this.
    assert result["backend"] == "stub"
    assert "I've watered" not in result["advice"]
    # The fallback is the real stub output, not an error string.
    assert "Watering" in result["advice"]


def test_letter_scaffolding_is_rejected(fake_backend):
    fake_backend("Dear Plant Owner,\n\nWater it soon.\n\nLove,\n\n[Your Name]")
    result = advise()

    assert result["guarded"] is True
    assert "[Your Name]" not in result["advice"]


def test_grounded_model_advice_is_kept(fake_backend):
    # Every number here comes from the schedule block in the prompt.
    fake_backend("Ferny has no watering logged yet; every 5-9 days suits it.")
    result = advise()

    assert result["guarded"] is False
    assert result["backend"] == "anthropic"
    assert "Ferny" in result["advice"]


def test_stub_backend_is_not_second_guessed(monkeypatch):
    """The stub is derived from the data, so it is grounded by construction."""
    monkeypatch.setattr(advisor, "BACKEND", "stub")
    monkeypatch.setattr(advisor, "SYMPTOMS_BACKEND", "stub")
    result = advise()

    assert result["backend"] == "stub"
    assert result["guarded"] is False
