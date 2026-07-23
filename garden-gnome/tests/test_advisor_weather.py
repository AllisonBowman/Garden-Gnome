"""Advisor × weather grounding (Phase D).

The advisor threads a plant's grow environment and the local forecast into both
the LLM prompt and the deterministic stub — but only for plants the outside
world actually reaches. These tests pin the gate (weather_applies), the prompt
blocks, and each stub nudge, and confirm an indoor/sheltered plant is untouched.
"""
import pytest

from app.models.models import (
    Species, Plant, Environment, LightNeed, MaturityStage,
    Shelter, TempExposure, SunExposure,
)
from app.services.advisor import (
    weather_applies, _build_prompt, _advise_stub, _weather_nudges, get_care_advice,
)


def make_species(temp_f_min=60, temp_f_max=85, toxic=False):
    return Species(
        common_name="Test Fern",
        scientific_name="Testus fernus",
        light_need=LightNeed.bright_indirect,
        humidity_pct_min=40,
        humidity_pct_max=60,
        temp_f_min=temp_f_min,
        temp_f_max=temp_f_max,
        soil_type="well-draining",
        toxic_to_pets=toxic,
    )


def make_plant():
    return Plant(nickname="Ferny", species_id=1, maturity_stage=MaturityStage.mature)


def make_env(shelter=Shelter.exposed, temp=TempExposure.outdoor, sun=SunExposure.full_sun):
    return Environment(
        name="Balcony", shelter=shelter, temp_exposure=temp, sun_exposure=sun,
        lat=37.77, lng=-122.42,
    )


def weather(*, now_uv=6, days=None):
    return {
        "current": {"temp_f": 78, "humidity_pct": 45, "uv_index": now_uv, "condition": "Clear"},
        "daily": days if days is not None else [
            {"date": "2026-07-24", "high_f": 82, "low_f": 66, "precip_chance_pct": 10,
             "uv_max": 7, "daylight_hours": 14.2, "condition": "Clear"},
        ],
        "attribution": {"text": " Weather", "url": "https://example/legal"},
    }


# --- the gate ---------------------------------------------------------------

@pytest.mark.parametrize("shelter,temp,expected", [
    (Shelter.sheltered, TempExposure.indoor, False),   # desk plant — weather irrelevant
    (Shelter.sheltered, TempExposure.outdoor, True),   # feels outside air
    (Shelter.partial,   TempExposure.indoor, True),    # some rain/wind reaches it
    (Shelter.exposed,   TempExposure.indoor, True),
    (Shelter.exposed,   TempExposure.outdoor, True),
])
def test_weather_applies(shelter, temp, expected):
    env = make_env(shelter=shelter, temp=temp)
    assert weather_applies(env) is expected


def test_weather_applies_none():
    assert weather_applies(None) is False


# --- prompt blocks ----------------------------------------------------------

def test_prompt_includes_environment_and_weather_for_exposed():
    prompt = _build_prompt(
        make_species(), make_plant(), [], [], "",
        environment=make_env(), weather=weather(),
    )
    assert "GROW ENVIRONMENT" in prompt
    assert "LOCAL WEATHER" in prompt
    assert "exposed" in prompt
    assert "82" in prompt  # a forecast high made it in


def test_prompt_omits_weather_for_indoor_sheltered():
    prompt = _build_prompt(
        make_species(), make_plant(), [], [], "",
        environment=make_env(shelter=Shelter.sheltered, temp=TempExposure.indoor),
        weather=weather(),
    )
    assert "LOCAL WEATHER" not in prompt
    assert "GROW ENVIRONMENT" not in prompt


def test_prompt_unchanged_without_weather():
    prompt = _build_prompt(make_species(), make_plant(), [], [], "", environment=make_env())
    assert "LOCAL WEATHER" not in prompt


# --- stub nudges ------------------------------------------------------------

def test_stub_rain_nudge_when_unsheltered():
    days = [{"date": "2026-07-24", "high_f": 80, "low_f": 66, "precip_chance_pct": 70,
             "uv_max": 5, "daylight_hours": 14.0, "condition": "Rain"}]
    out = _advise_stub(make_species(), make_plant(), [], [], "",
                       environment=make_env(), weather=weather(days=days))
    assert "Rain likely" in out
    assert "70%" in out


def test_stub_heat_nudge_when_outdoor():
    days = [{"date": "2026-07-24", "high_f": 99, "low_f": 70, "precip_chance_pct": 0,
             "uv_max": 6, "daylight_hours": 14.0, "condition": "Clear"}]
    out = _advise_stub(make_species(temp_f_max=85), make_plant(), [], [], "",
                       environment=make_env(), weather=weather(days=days))
    assert "Heat ahead" in out
    assert "99" in out


def test_stub_cold_nudge_when_outdoor():
    days = [{"date": "2026-07-24", "high_f": 70, "low_f": 41, "precip_chance_pct": 0,
             "uv_max": 3, "daylight_hours": 10.0, "condition": "Clear"}]
    out = _advise_stub(make_species(temp_f_min=55), make_plant(), [], [], "",
                       environment=make_env(), weather=weather(days=days))
    assert "Cold night ahead" in out
    assert "41" in out


def test_stub_uv_nudge_when_open_sun():
    days = [{"date": "2026-07-24", "high_f": 80, "low_f": 66, "precip_chance_pct": 0,
             "uv_max": 10, "daylight_hours": 14.0, "condition": "Clear"}]
    out = _advise_stub(make_species(), make_plant(), [], [], "",
                       environment=make_env(sun=SunExposure.full_sun), weather=weather(days=days))
    assert "Very high UV" in out


def test_stub_sheltered_outdoor_gets_heat_not_rain():
    """A roofed-but-outdoor plant feels temperature swings but not rain."""
    days = [{"date": "2026-07-24", "high_f": 99, "low_f": 70, "precip_chance_pct": 90,
             "uv_max": 6, "daylight_hours": 14.0, "condition": "Rain"}]
    out = _advise_stub(
        make_species(temp_f_max=85), make_plant(), [], [], "",
        environment=make_env(shelter=Shelter.sheltered, temp=TempExposure.outdoor),
        weather=weather(days=days),
    )
    assert "Heat ahead" in out
    assert "Rain likely" not in out


def test_stub_indoor_sheltered_gets_no_nudges():
    days = [{"date": "2026-07-24", "high_f": 110, "low_f": 20, "precip_chance_pct": 100,
             "uv_max": 11, "daylight_hours": 14.0, "condition": "Rain"}]
    out = _advise_stub(
        make_species(), make_plant(), [], [], "",
        environment=make_env(shelter=Shelter.sheltered, temp=TempExposure.indoor,
                             sun=SunExposure.shade),
        weather=weather(days=days),
    )
    for marker in ("Rain likely", "Heat ahead", "Cold night ahead", "Very high UV"):
        assert marker not in out


def test_stub_no_weather_has_no_nudges():
    out = _advise_stub(make_species(), make_plant(), [], [], "", environment=make_env())
    for marker in ("Rain likely", "Heat ahead", "Cold night ahead", "Very high UV"):
        assert marker not in out


def test_weather_nudges_empty_without_env_or_weather():
    assert _weather_nudges(make_species(), None, weather()) == []
    assert _weather_nudges(make_species(), make_env(), None) == []


# --- end-to-end through get_care_advice (stub backend) ----------------------

def test_get_care_advice_threads_weather(monkeypatch):
    monkeypatch.setattr("app.services.advisor.BACKEND", "stub")
    days = [{"date": "2026-07-24", "high_f": 80, "low_f": 66, "precip_chance_pct": 80,
             "uv_max": 5, "daylight_hours": 14.0, "condition": "Rain"}]
    result = get_care_advice(
        make_species(), make_plant(), [], [], "",
        environment=make_env(), weather=weather(days=days),
    )
    assert result["backend"] == "stub"
    assert "Rain likely" in result["advice"]
