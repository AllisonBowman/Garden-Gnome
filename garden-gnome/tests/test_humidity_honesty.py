"""Plan 1.6: fabricated humidity reaches no surface as fact.

The Perenual import had no humidity field — every imported row derives its
percentages from a watering category and carries a `humidity_source` trait
saying so. These tests pin the three suppression points: the advisor prompt,
the vision prompt, and the API's humidity_sourced flag.
"""
from app.models.models import (
    LightNeed, MaturityStage, Plant, Species, SpeciesTrait,
)
from app.services.advisor import _build_prompt
from app.services.vision import _build_context


def make_species(traits=()):
    s = Species(
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
    s.traits = [
        SpeciesTrait(trait=t, value="derived from watering category "
                     "(no source humidity data)", unit="")
        for t in traits
    ]
    return s


def make_plant():
    return Plant(
        nickname="Ferny", species_id=1, maturity_stage=MaturityStage.mature)


def test_curated_species_keeps_humidity_in_the_advisor_prompt():
    prompt = _build_prompt(make_species(), make_plant(), [], [])
    assert "- Humidity: 40-60%" in prompt


def test_derived_humidity_never_enters_the_advisor_prompt():
    species = make_species(traits=("humidity_source",))
    prompt = _build_prompt(species, make_plant(), [], [])
    assert "Humidity" not in prompt
    # The rest of the fact block is intact
    assert "- Temperature: 60-85 F" in prompt
    assert "- Light need: bright_indirect" in prompt


def test_vision_context_applies_the_same_rule():
    curated = _build_context(make_species(), make_plant(), [])
    derived = _build_context(
        make_species(traits=("humidity_source",)), make_plant(), [])
    assert "- Humidity: 40-60%" in curated
    assert "Humidity" not in derived


def test_other_traits_do_not_suppress_humidity():
    species = make_species(traits=("growth_rate",))
    prompt = _build_prompt(species, make_plant(), [], [])
    assert "- Humidity: 40-60%" in prompt


def test_humidity_sourced_property():
    assert make_species().humidity_sourced is True
    assert make_species(
        traits=("humidity_source",)).humidity_sourced is False


def test_api_flags_derived_humidity(migrated_db_url):
    """GET /species/ and /species/{id} both carry humidity_sourced, and the
    list route computes it without touching the lazy traits relation."""
    from fastapi.testclient import TestClient
    from sqlmodel import Session, create_engine

    from app.db.database import get_session
    from app.main import app
    from app.models.models import User
    from app.services import tokens

    engine = create_engine(
        migrated_db_url, connect_args={"check_same_thread": False})

    def override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override
    try:
        with Session(engine) as s:
            curated = make_species()
            imported = make_species(traits=("humidity_source",))
            imported.scientific_name = "Importus derivus"
            imported.common_name = "Imported Fern"
            s.add(curated)
            s.add(imported)
            user = User(email="humidity@example.com")
            s.add(user)
            s.commit()
            curated_id, imported_id = curated.id, imported.id
            headers = {
                "Authorization":
                    f"Bearer {tokens.issue_access_token(user.id)}"}

        client = TestClient(app)
        by_id = {sp["id"]: sp for sp in client.get(
            "/species/", headers=headers).json()}
        assert by_id[curated_id]["humidity_sourced"] is True
        assert by_id[imported_id]["humidity_sourced"] is False

        detail = client.get(
            f"/species/{imported_id}", headers=headers).json()
        assert detail["humidity_sourced"] is False
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
