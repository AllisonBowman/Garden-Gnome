"""Vision service (photo diagnosis / identification) + /ai/status.

The Ollama backend is exercised against an httpx.MockTransport — no live
Ollama needed. Config is read at call time, so each test selects its backend
with monkeypatch.setenv.
"""
import io
import json

import httpx
import pytest

import app.services.vision as vision
from app.models.models import (
    CareSchedule,
    CareType,
    LightNeed,
    Plant,
    Species,
)


def _install_transport(monkeypatch, handler):
    """Route every httpx.AsyncClient the vision module creates through a
    MockTransport driven by `handler`."""
    real_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(*args, **kwargs)

    monkeypatch.setattr("app.services.vision.httpx.AsyncClient", factory)


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


# --- diagnose: stub -------------------------------------------------------

@pytest.mark.asyncio
async def test_stub_diagnose_is_default(sunflower, plant, schedules):
    result = await vision.diagnose_photo(sunflower, plant, schedules, b"12345")
    assert result["backend"] == "stub"
    assert "not analyzed" in result["diagnosis"]


# --- diagnose: ollama -----------------------------------------------------

@pytest.mark.asyncio
async def test_ollama_diagnose_happy_path(monkeypatch, sunflower, plant, schedules):
    monkeypatch.setenv("VISION_BACKEND", "ollama")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["payload"] = json.loads(request.content)
        seen["path"] = request.url.path
        return httpx.Response(
            200, json={"message": {"role": "assistant",
                                   "content": "  Leaves look healthy overall.  "}}
        )

    _install_transport(monkeypatch, handler)
    result = await vision.diagnose_photo(
        sunflower, plant, schedules, b"raw-photo-bytes", "brown spots"
    )

    assert result == {"backend": "ollama", "diagnosis": "Leaves look healthy overall."}
    assert seen["path"] == "/api/chat"
    payload = seen["payload"]
    assert payload["model"] == vision.DEFAULT_VISION_MODEL
    assert payload["stream"] is False
    assert payload["keep_alive"] == vision.KEEP_ALIVE
    system, user = payload["messages"]
    assert system["role"] == "system"
    assert user["images"], "photo must be attached to the user turn"
    assert "Sunflower" in user["content"]
    assert "brown spots" in user["content"]
    assert "every 35-35 days" in user["content"], "schedules are in the grounding facts"


@pytest.mark.asyncio
async def test_ollama_down_raises_user_safe_error(monkeypatch, sunflower, plant, schedules):
    monkeypatch.setenv("VISION_BACKEND", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    _install_transport(monkeypatch, handler)
    with pytest.raises(vision.VisionUnavailable) as exc:
        await vision.diagnose_photo(sunflower, plant, schedules, b"bytes")

    message = str(exc.value)
    assert "try again" in message
    # The user-facing message must not carry setup/ops vocabulary.
    for jargon in ("VISION_BACKEND", "ollama", "backend", "env", "serve"):
        assert jargon.lower() not in message.lower()


@pytest.mark.asyncio
async def test_ollama_model_not_pulled_raises_user_safe_error(
    monkeypatch, sunflower, plant, schedules
):
    monkeypatch.setenv("VISION_BACKEND", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "model 'moondream' not found"})

    _install_transport(monkeypatch, handler)
    with pytest.raises(vision.VisionUnavailable) as exc:
        await vision.diagnose_photo(sunflower, plant, schedules, b"bytes")
    assert "pull" not in str(exc.value).lower()


@pytest.mark.asyncio
async def test_ollama_empty_answer_raises(monkeypatch, sunflower, plant, schedules):
    monkeypatch.setenv("VISION_BACKEND", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": "   "}})

    _install_transport(monkeypatch, handler)
    with pytest.raises(vision.VisionUnavailable):
        await vision.diagnose_photo(sunflower, plant, schedules, b"bytes")


# --- image preprocessing --------------------------------------------------

def _png_bytes(width: int, height: int) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(20, 120, 40)).save(buf, format="PNG")
    return buf.getvalue()


def test_prepare_image_downscales_and_reencodes():
    from PIL import Image

    original = _png_bytes(3000, 2000)
    prepared = vision.prepare_image(original)

    assert len(prepared) < len(original)
    img = Image.open(io.BytesIO(prepared))
    assert img.format == "JPEG"
    assert max(img.size) == vision.MAX_IMAGE_DIM


def test_prepare_image_leaves_undecodable_bytes_alone():
    junk = b"definitely not an image"
    assert vision.prepare_image(junk) == junk


@pytest.mark.asyncio
async def test_diagnose_sends_downscaled_photo(monkeypatch, sunflower, plant, schedules):
    monkeypatch.setenv("VISION_BACKEND", "ollama")
    original = _png_bytes(3000, 2000)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["images"] = json.loads(request.content)["messages"][1]["images"]
        return httpx.Response(200, json={"message": {"content": "ok"}})

    _install_transport(monkeypatch, handler)
    await vision.diagnose_photo(sunflower, plant, schedules, original)

    # base64 of the prepared JPEG must be far smaller than the 3000px original
    assert len(seen["images"][0]) < len(original)


# --- identify -------------------------------------------------------------

@pytest.mark.asyncio
async def test_identify_stub_returns_no_candidates(sunflower):
    result = await vision.identify_species(b"bytes", [sunflower])
    assert result["backend"] == "stub"
    assert result["candidate_ids"] == []


@pytest.mark.asyncio
async def test_identify_matches_names_to_catalog_ids(monkeypatch, sunflower):
    monkeypatch.setenv("VISION_BACKEND", "ollama")
    other = Species(
        id=2, common_name="Snake Plant", scientific_name="Dracaena trifasciata",
        light_need=LightNeed.low, humidity_pct_min=30, humidity_pct_max=50,
        temp_f_min=60, temp_f_max=85, soil_type="cactus mix",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content":
            "Sunflower\nSnake Plant\nOBSERVED: tall stem, broad yellow bloom"}})

    _install_transport(monkeypatch, handler)
    result = await vision.identify_species(b"bytes", [sunflower, other])

    assert result["candidate_ids"] == [1, 2]
    assert "OBSERVED" in result["observation"]


@pytest.mark.asyncio
async def test_identify_unknown_yields_no_candidates(monkeypatch, sunflower):
    monkeypatch.setenv("VISION_BACKEND", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content":
            "UNKNOWN\nOBSERVED: photo too blurry to identify"}})

    _install_transport(monkeypatch, handler)
    result = await vision.identify_species(b"bytes", [sunflower])
    assert result["candidate_ids"] == []


# --- readiness ------------------------------------------------------------

@pytest.mark.asyncio
async def test_status_stub_reports_not_ready():
    status = await vision.vision_status()
    assert status["backend"] == "stub"
    assert status["ready"] is False


@pytest.mark.asyncio
async def test_status_ready_when_model_pulled(monkeypatch):
    monkeypatch.setenv("VISION_BACKEND", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return httpx.Response(200, json={"models": [{"name": "moondream:latest"}]})

    _install_transport(monkeypatch, handler)
    status = await vision.vision_status()
    assert status == {
        "backend": "ollama", "model": "moondream", "ready": True, "detail": "ok",
    }


@pytest.mark.asyncio
async def test_status_reports_missing_model(monkeypatch):
    monkeypatch.setenv("VISION_BACKEND", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"models": [{"name": "llama3.2:latest"}]})

    _install_transport(monkeypatch, handler)
    status = await vision.vision_status()
    assert status["ready"] is False
    assert "not pulled" in status["detail"]


@pytest.mark.asyncio
async def test_status_reports_unreachable_ollama(monkeypatch):
    monkeypatch.setenv("VISION_BACKEND", "ollama")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    _install_transport(monkeypatch, handler)
    status = await vision.vision_status()
    assert status["ready"] is False
    assert "not reachable" in status["detail"]


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
