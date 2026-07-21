"""Vision service (photo diagnosis / identification) + /ai/status.

Only the stub backend is registered (no hosted vision backend by design —
species ID runs on-device in the mobile app). These tests pin the stub
behavior, the catalog-constrained candidate matching, and the status
surfaces a future backend must keep honest.
"""
import pytest

import app.services.vision as vision
from app.models.models import (
    CareSchedule,
    CareType,
    LightNeed,
    Plant,
    Species,
)


@pytest.fixture()
def sunflower() -> Species:
    return Species(
        id=1,
        common_name="Sunflower",
        scientific_name="Helianthus annuus",
        light_need=LightNeed.direct,
        humidity_pct_min=30,
        humidity_pct_max=60,
        temp_f_min=45,
        temp_f_max=90,
        soil_type="loamy, well-draining",
        toxic_to_pets=False,
        care_notes="Pet-safe annual.",
    )


@pytest.fixture()
def plant() -> Plant:
    return Plant(id=1, nickname="Front yard sunflower", species_id=1, location="Front yard")


@pytest.fixture()
def schedules() -> list[CareSchedule]:
    return [
        CareSchedule(species_id=1, care_type=CareType.water,
                     interval_days_min=2, interval_days_max=5),
        CareSchedule(species_id=1, care_type=CareType.fertilize,
                     interval_days_min=35, interval_days_max=35),
    ]


# --- diagnose -------------------------------------------------------------

@pytest.mark.asyncio
async def test_stub_diagnose_is_default(sunflower, plant, schedules):
    result = await vision.diagnose_photo(sunflower, plant, schedules, b"12345")
    assert result["backend"] == "stub"
    assert "not analyzed" in result["diagnosis"]


@pytest.mark.asyncio
async def test_unknown_backend_falls_back_to_stub(monkeypatch, sunflower, plant, schedules):
    monkeypatch.setenv("VISION_BACKEND", "something-else")
    result = await vision.diagnose_photo(sunflower, plant, schedules, b"bytes")
    assert "not analyzed" in result["diagnosis"]


@pytest.mark.asyncio
async def test_stub_diagnose_never_mentions_setup_tooling(sunflower, plant, schedules):
    # Server setup vocabulary must not reach the consumer UI.
    result = await vision.diagnose_photo(sunflower, plant, schedules, b"bytes")
    for jargon in ("ollama", "VISION_BACKEND", "pull", "env"):
        assert jargon.lower() not in result["diagnosis"].lower()


# --- identify -------------------------------------------------------------

@pytest.mark.asyncio
async def test_identify_stub_returns_no_candidates(sunflower):
    result = await vision.identify_species(b"bytes", [sunflower])
    assert result["backend"] == "stub"
    assert result["candidate_ids"] == []
    assert "search below" in result["observation"]


@pytest.mark.asyncio
async def test_identify_matches_backend_names_to_catalog_ids(monkeypatch, sunflower):
    # The candidate-matching loop is what keeps any future backend
    # catalog-constrained; exercise it through a fake backend.
    other = Species(
        id=2, common_name="Snake Plant", scientific_name="Dracaena trifasciata",
        light_need=LightNeed.low, humidity_pct_min=30, humidity_pct_max=50,
        temp_f_min=60, temp_f_max=85, soil_type="cactus mix",
    )

    async def fake_backend(image_bytes, catalog):
        return "OBSERVED: tall stem", ["Sunflower", "Snake Plant", "Sunflower"]

    monkeypatch.setenv("VISION_BACKEND", "fake")
    monkeypatch.setitem(vision._IDENTIFY_BACKENDS, "fake", fake_backend)
    result = await vision.identify_species(b"bytes", [sunflower, other])
    assert result["candidate_ids"] == [1, 2]  # ordered, deduplicated


# --- readiness ------------------------------------------------------------

@pytest.mark.asyncio
async def test_status_reports_not_ready():
    status = await vision.vision_status()
    assert status["backend"] == "stub"
    assert status["ready"] is False
    assert status["model"] is None


# --- /ai/status endpoint --------------------------------------------------

def test_ai_status_endpoint():
    from fastapi.testclient import TestClient

    from app.main import app

    resp = TestClient(app).get("/ai/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["advisor_backend"] == "stub"
    assert body["vision"]["backend"] == "stub"
    assert body["vision"]["ready"] is False
