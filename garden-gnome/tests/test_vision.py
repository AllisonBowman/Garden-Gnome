"""Vision service (photo diagnosis / identification) + /ai/status.

Two backends are registered: `stub` (the default — species ID also runs
on-device in the mobile app) and `anthropic` (opt-in cloud vision). The
Anthropic backend is exercised against a fake AsyncAnthropic client, so no
API key or network call is needed. Config is read at call time, so each test
selects its backend with monkeypatch.setenv.

These tests pin the stub behavior, the catalog-grounded candidate matching,
image preparation, and the status surface — including that it never echoes
a key.
"""
import io

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
    assert "Photo received" in result["diagnosis"]


@pytest.mark.asyncio
async def test_unknown_backend_falls_back_to_stub(monkeypatch, sunflower, plant, schedules):
    monkeypatch.setenv("VISION_BACKEND", "something-else")
    result = await vision.diagnose_photo(sunflower, plant, schedules, b"bytes")
    assert "Photo received" in result["diagnosis"]


@pytest.mark.asyncio
async def test_stub_diagnose_is_consumer_friendly(sunflower, plant, schedules):
    # No developer marker, no server-setup vocabulary reaches the UI.
    result = await vision.diagnose_photo(sunflower, plant, schedules, b"bytes")
    text = result["diagnosis"]
    assert "[STUB]" not in text
    for jargon in ("ollama", "vision_backend", "backend", "pull", "byte", "server"):
        assert jargon not in text.lower()


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


# --- router: stub diagnosis must not touch the timeline --------------------

@pytest.fixture()
def api(migrated_db_url):
    """A signed-in user with one owned plant, hitting the real router."""
    from fastapi.testclient import TestClient
    from sqlmodel import Session, create_engine, select

    from app.db.database import get_session
    from app.main import app
    from app.models.models import Environment, EnvironmentType, Plant, Species, User
    from app.services import tokens

    engine = create_engine(migrated_db_url, connect_args={"check_same_thread": False})

    def override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override

    with Session(engine) as s:
        species = s.exec(select(Species)).first()
        if species is None:
            species = Species(
                common_name="Sunflower", scientific_name="Helianthus annuus",
                light_need="direct", humidity_pct_min=30, humidity_pct_max=60,
                temp_f_min=45, temp_f_max=90, soil_type="loamy",
            )
            s.add(species)
            s.flush()
        user = User(email="diag@example.com")
        s.add(user)
        s.flush()
        env = Environment(name="home", type=EnvironmentType.home, user_id=user.id)
        s.add(env)
        s.flush()
        plant = Plant(nickname="Front yard sunflower", species_id=species.id,
                      environment_id=env.id, user_id=user.id)
        s.add(plant)
        s.commit()
        plant_id = plant.id
        headers = {"Authorization": f"Bearer {tokens.issue_access_token(user.id)}"}

    client = TestClient(app)
    try:
        yield client, plant_id, headers
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_stub_diagnosis_is_not_logged_to_timeline(api):
    client, plant_id, headers = api

    before = client.get(f"/plants/{plant_id}/logs", headers=headers).json()
    resp = client.post(
        f"/plants/{plant_id}/diagnose-photo",
        headers=headers,
        files={"photo": ("plant.jpg", b"\xff\xd8\xff\xe0 not-a-real-jpeg", "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["backend"] == "stub"

    after = client.get(f"/plants/{plant_id}/logs", headers=headers).json()
    # The stub never analyzed the photo, so it must add no timeline entry.
    assert len(after) == len(before)
    assert not any("Photo diagnosis" in (log.get("notes") or "") for log in after)


# --- image preparation ----------------------------------------------------

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
        monkeypatch,
        _FakeMessage("Helianthus annuus (Sunflower)\nOBSERVED: broad leaves, tall stem"),
        seen,
    )

    result = await vision.identify_species(b"bytes", [sunflower, other])

    assert result["backend"] == "anthropic"
    assert result["candidate_ids"] == [1]
    assert result["tier"] == "confident"

    # The catalog is deliberately NOT in the prompt. Listing ~1940 species
    # costs ~20k tokens (~$0.04) per identify; grounding happens afterwards in
    # name_match instead. Regression guard against reintroducing the list.
    prompt = seen["messages"][0]["content"][1]["text"]
    assert "Snake Plant" not in prompt
    assert "Dracaena" not in prompt
    assert len(prompt) < 200, f"identify prompt should stay tiny, got {len(prompt)} chars"


@pytest.mark.asyncio
async def test_identify_out_of_catalog_yields_no_candidates(monkeypatch, sunflower):
    """A plant we don't stock must degrade to manual search, never to a forced
    nearest match -- the model naming it correctly is not permission to offer
    care data we don't have."""
    _install_anthropic(monkeypatch, _FakeMessage("Ficus lyrata (Fiddle Leaf Fig)"))

    result = await vision.identify_species(b"bytes", [sunflower])

    assert result["candidate_ids"] == []
    assert result["tier"] == "none"


@pytest.mark.asyncio
async def test_identify_flags_unreviewed_matches(monkeypatch):
    """87% of the catalog is needs_review; a match against unchecked care data
    is reported so the client can hedge rather than assert."""
    unchecked = Species(
        id=7, common_name="Cape Primrose", scientific_name="Streptocarpus x hybridus",
        light_need=LightNeed.bright_indirect, humidity_pct_min=40, humidity_pct_max=60,
        temp_f_min=40, temp_f_max=85, soil_type="mix", review_status="needs_review",
    )
    _install_anthropic(monkeypatch, _FakeMessage("Streptocarpus x hybridus"))

    result = await vision.identify_species(b"bytes", [unchecked])

    assert result["candidate_ids"] == [7]
    assert result["unreviewed_ids"] == [7]


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
