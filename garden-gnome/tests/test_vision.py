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
    assert plant.nickname in result["diagnosis"]


@pytest.mark.asyncio
async def test_stub_diagnose_leaks_no_developer_text(sunflower, plant, schedules):
    """Regression for docs/screenshots/2026-07-20-photo-diagnosis-stub.png,
    where a build showed a user `[STUB] ... Set VISION_BACKEND=ollama and pull
    a vision model (`ollama pull moondream`)`. Setup instructions belong in
    the server log, never in a consumer-facing string."""
    result = await vision.diagnose_photo(sunflower, plant, schedules, b"12345")
    text = result["diagnosis"].lower()
    for leak in ("[stub]", "vision_backend", "ollama", "backend", "pull", "configured"):
        assert leak not in text, f"developer text {leak!r} reached the user"


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


# --- stub diagnosis must not reach the plant's timeline -------------------

def test_stub_diagnosis_files_no_care_log(migrated_db_url):
    """Phase 0 accept criterion: a stub diagnosis run leaves no CareLog behind.

    Before this fix the route auto-logged `Photo diagnosis: {text}` for every
    backend, so the `[STUB] ... Set VISION_BACKEND=ollama` string was filed to
    the plant's permanent timeline (visible in
    docs/screenshots/2026-07-20-gnome-voice-letter.png) and then fed back to
    the advisor as if the owner had written it.
    """
    from fastapi.testclient import TestClient
    from sqlmodel import Session, create_engine, select

    from app.db.database import get_session
    from app.main import app
    from app.models.models import CareLog, Environment, EnvironmentType, User
    from app.services import tokens

    engine = create_engine(migrated_db_url, connect_args={"check_same_thread": False})

    def override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override
    try:
        with Session(engine) as s:
            species = s.exec(select(Species)).first()
            if species is None:
                species = Species(
                    common_name="Log Fern", scientific_name="Logus testus",
                    light_need="medium", humidity_pct_min=40, humidity_pct_max=60,
                    temp_f_min=60, temp_f_max=80, soil_type="mix",
                )
                s.add(species)
                s.flush()
            user = User(email="stub-log@example.com")
            s.add(user)
            s.flush()
            env = Environment(name="home", type=EnvironmentType.home, user_id=user.id)
            s.add(env)
            s.flush()
            plant = Plant(
                nickname="Stub Subject", species_id=species.id,
                environment_id=env.id, user_id=user.id,
            )
            s.add(plant)
            s.commit()
            plant_id, user_id = plant.id, user.id

        headers = {"Authorization": f"Bearer {tokens.issue_access_token(user_id)}"}
        resp = TestClient(app).post(
            f"/plants/{plant_id}/diagnose-photo",
            files={"photo": ("p.png", _png_bytes(40, 40), "image/png")},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["backend"] == "stub"

        with Session(engine) as s:
            logs = s.exec(select(CareLog).where(CareLog.plant_id == plant_id)).all()
        assert logs == [], f"stub diagnosis filed {len(logs)} care log(s)"
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


# --- anthropic vision backend --------------------------------------------

class _FakeTextBlock:
    type = "text"

    def __init__(self, text: str):
        self.text = text


class _FakeUsage:
    input_tokens = 2300
    output_tokens = 350


class _FakeMessage:
    def __init__(self, text: str = "", stop_reason: str = "end_turn"):
        self.content = [_FakeTextBlock(text)] if text else []
        self.stop_reason = stop_reason
        self.usage = _FakeUsage()


def _install_anthropic(monkeypatch, message: _FakeMessage, captured: dict | None = None):
    """Point vision.py's `import anthropic` at a fake AsyncAnthropic."""
    import anthropic

    class _FakeMessages:
        async def create(self, **kwargs):
            if captured is not None:
                captured.update(kwargs)
            return message

    class _FakeClient:
        def __init__(self, *a, **kw):
            self.messages = _FakeMessages()

    monkeypatch.setenv("VISION_BACKEND", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setattr(anthropic, "AsyncAnthropic", _FakeClient)


@pytest.mark.asyncio
async def test_anthropic_diagnose_happy_path(monkeypatch, sunflower, plant, schedules):
    seen: dict = {}
    _install_anthropic(monkeypatch, _FakeMessage("Lower leaves are yellowing."), seen)

    result = await vision.diagnose_photo(
        sunflower, plant, schedules, _png_bytes(80, 80), "brown spots"
    )

    assert result == {"backend": "anthropic", "diagnosis": "Lower leaves are yellowing."}
    assert seen["model"] == vision.DEFAULT_ANTHROPIC_VISION_MODEL
    assert seen["thinking"] == {"type": "adaptive"}
    assert seen["output_config"] == {"effort": "medium"}
    # Sonnet 5 rejects sampling parameters -- they must never be sent.
    for banned in ("temperature", "top_p", "top_k"):
        assert banned not in seen

    blocks = seen["messages"][0]["content"]
    assert blocks[0]["type"] == "image"
    assert blocks[0]["source"]["media_type"] == "image/jpeg"  # prepare_image re-encodes
    assert "brown spots" in blocks[1]["text"]
    assert "every 35-35 days" in blocks[1]["text"], "care schedules ground the diagnosis"


@pytest.mark.asyncio
async def test_anthropic_identify_matches_catalog(monkeypatch, sunflower):
    other = Species(
        id=2, common_name="Snake Plant", scientific_name="Dracaena trifasciata",
        light_need=LightNeed.low, humidity_pct_min=30, humidity_pct_max=50,
        temp_f_min=60, temp_f_max=85, soil_type="sandy",
    )
    seen: dict = {}
    _install_anthropic(
        monkeypatch, _FakeMessage("Sunflower\nOBSERVED: broad leaves, tall stem"), seen
    )

    result = await vision.identify_species(b"bytes", [sunflower, other])

    assert result["backend"] == "anthropic"
    assert result["candidate_ids"] == [1]
    # Every catalog species is offered as a candidate -- the design that makes
    # a 129-species catalog work without a retrieval index.
    prompt = seen["messages"][0]["content"][1]["text"]
    assert "Sunflower" in prompt and "Snake Plant" in prompt


@pytest.mark.asyncio
async def test_anthropic_without_key_raises_user_safe_error(monkeypatch, sunflower, plant, schedules):
    monkeypatch.setenv("VISION_BACKEND", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(vision.VisionUnavailable) as exc:
        await vision.diagnose_photo(sunflower, plant, schedules, b"bytes")
    for jargon in ("ANTHROPIC_API_KEY", "api key", "backend", "anthropic"):
        assert jargon.lower() not in str(exc.value).lower()


@pytest.mark.asyncio
async def test_anthropic_refusal_raises_user_safe_error(monkeypatch, sunflower, plant, schedules):
    """A safety decline returns HTTP 200 with empty content, not an exception."""
    _install_anthropic(monkeypatch, _FakeMessage("", stop_reason="refusal"))

    with pytest.raises(vision.VisionUnavailable):
        await vision.diagnose_photo(sunflower, plant, schedules, b"bytes")


@pytest.mark.asyncio
async def test_anthropic_status_reports_key_presence(monkeypatch):
    monkeypatch.setenv("VISION_BACKEND", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    ready = await vision.vision_status()
    assert ready["ready"] is True
    assert ready["model"] == vision.DEFAULT_ANTHROPIC_VISION_MODEL

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    missing = await vision.vision_status()
    assert missing["ready"] is False
    assert "sk-ant" not in str(missing), "status must never echo a key"


def test_media_type_sniffing():
    """prepare_image falls back to original bytes when Pillow can't decode, so
    the media type has to be sniffed rather than assumed to be JPEG."""
    assert vision._media_type(_png_bytes(10, 10)) == "image/png"
    assert vision._media_type(b"\xff\xd8\xff\xe0 jpeg-ish") == "image/jpeg"
    assert vision._media_type(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "image/webp"
