"""Seed species and default environment from the JSON catalog.

Species data lives in species_catalog.json — add new plants there without
touching Python. The seed function is idempotent per scientific name:
existing species are skipped, new ones are inserted. Re-run after adding
entries to the catalog to pick up the new species on an existing database.

Run via `python -m app.data.seed`.
"""
import json
import os
from pathlib import Path

from sqlmodel import Session, select

from app.db.database import engine, init_db, migrate_db
from app.models.models import (
    Species, CareSchedule, SpeciesTrait, LightNeed, CareType,
    Environment, EnvironmentType,
)


def _load_catalog() -> list[dict]:
    catalog_path = Path(__file__).parent / "species_catalog.json"
    with open(catalog_path, encoding="utf-8") as f:
        return json.load(f)


# Keep SEED_DATA for backwards compatibility; seed() now reads from the JSON file.
SEED_DATA = [
    {
        "species": dict(
            common_name="Snake Plant",
            scientific_name="Dracaena trifasciata",
            light_need=LightNeed.low,
            humidity_pct_min=30, humidity_pct_max=50,
            temp_f_min=60, temp_f_max=85,
            soil_type="Free-draining cactus/succulent mix",
            toxic_to_pets=True,
            care_notes="Extremely drought tolerant. Let soil dry fully between waterings; rot is the main risk. Tolerates neglect.",
        ),
        "schedules": [
            dict(care_type=CareType.water, interval_days_min=14, interval_days_max=21,
                 notes="Let soil dry completely. Overwatering causes root rot."),
            dict(care_type=CareType.fertilize, interval_days_min=60, interval_days_max=90,
                 notes="Half-strength balanced fertilizer during growing season only."),
            dict(care_type=CareType.repot, interval_days_min=730, interval_days_max=1095,
                 notes="Only when root-bound. Prefers being snug."),
        ],
        "traits": [
            dict(trait="growth_rate", value="slow"),
            dict(trait="max_height_inches", value="48", unit="inches"),
            dict(trait="native_region", value="West Africa"),
        ],
    },
    {
        "species": dict(
            common_name="Pothos",
            scientific_name="Epipremnum aureum",
            light_need=LightNeed.medium,
            humidity_pct_min=40, humidity_pct_max=60,
            temp_f_min=65, temp_f_max=85,
            soil_type="Standard well-draining potting mix",
            toxic_to_pets=True,
            care_notes="Forgiving vining plant. Let top 1-2 inches dry out. Leaves curl when thirsty.",
        ),
        "schedules": [
            dict(care_type=CareType.water, interval_days_min=7, interval_days_max=10,
                 notes="Let top 1-2 inches dry. Curling leaves signal thirst."),
            dict(care_type=CareType.fertilize, interval_days_min=30, interval_days_max=60,
                 notes="Balanced liquid fertilizer during spring/summer."),
            dict(care_type=CareType.prune, interval_days_min=30, interval_days_max=90,
                 notes="Trim leggy vines to encourage bushier growth. Cuttings root in water."),
        ],
        "traits": [
            dict(trait="growth_rate", value="fast"),
            dict(trait="propagation", value="stem cutting in water"),
            dict(trait="native_region", value="Southeast Asia"),
        ],
    },
    {
        "species": dict(
            common_name="Monstera",
            scientific_name="Monstera deliciosa",
            light_need=LightNeed.bright_indirect,
            humidity_pct_min=50, humidity_pct_max=70,
            temp_f_min=65, temp_f_max=85,
            soil_type="Chunky aroid mix (bark, perlite, coco coir)",
            toxic_to_pets=True,
            care_notes="Wants a moss pole to climb. Fenestrations develop with maturity and good light.",
        ),
        "schedules": [
            dict(care_type=CareType.water, interval_days_min=7, interval_days_max=12,
                 notes="Let top 2 inches dry. Yellowing lower leaves = overwatering."),
            dict(care_type=CareType.fertilize, interval_days_min=14, interval_days_max=30,
                 notes="Heavy feeder in growing season. Balanced or high-nitrogen liquid fertilizer."),
            dict(care_type=CareType.clean, interval_days_min=14, interval_days_max=30,
                 notes="Wipe large leaves with damp cloth to remove dust and improve photosynthesis."),
            dict(care_type=CareType.repot, interval_days_min=365, interval_days_max=730,
                 notes="Repot when roots circle the bottom or emerge from drainage holes."),
        ],
        "traits": [
            dict(trait="growth_rate", value="moderate"),
            dict(trait="max_height_inches", value="96", unit="inches"),
            dict(trait="propagation", value="stem cutting with node"),
            dict(trait="native_region", value="Central America"),
        ],
    },
    {
        "species": dict(
            common_name="ZZ Plant",
            scientific_name="Zamioculcas zamiifolia",
            light_need=LightNeed.low,
            humidity_pct_min=30, humidity_pct_max=50,
            temp_f_min=60, temp_f_max=85,
            soil_type="Free-draining mix",
            toxic_to_pets=True,
            care_notes="Stores water in rhizomes; overwatering is the top killer. Thrives on neglect.",
        ),
        "schedules": [
            dict(care_type=CareType.water, interval_days_min=14, interval_days_max=21,
                 notes="Rhizomes store water. Err on the dry side; yellow stems = overwatering."),
            dict(care_type=CareType.fertilize, interval_days_min=60, interval_days_max=90,
                 notes="Very light feeder. Dilute balanced fertilizer a few times per growing season."),
            dict(care_type=CareType.repot, interval_days_min=730, interval_days_max=1095,
                 notes="Slow grower; rarely needs repotting. Go up only one pot size."),
        ],
        "traits": [
            dict(trait="growth_rate", value="slow"),
            dict(trait="max_height_inches", value="36", unit="inches"),
            dict(trait="native_region", value="East Africa"),
        ],
    },
    {
        "species": dict(
            common_name="Peace Lily",
            scientific_name="Spathiphyllum wallisii",
            light_need=LightNeed.medium,
            humidity_pct_min=50, humidity_pct_max=70,
            temp_f_min=65, temp_f_max=85,
            soil_type="Moisture-retentive potting mix",
            toxic_to_pets=True,
            care_notes="Dramatically droops when thirsty, recovers fast after watering. Likes consistent moisture.",
        ),
        "schedules": [
            dict(care_type=CareType.water, interval_days_min=5, interval_days_max=8,
                 notes="Likes consistent moisture. Dramatic droop = thirsty; recovers quickly."),
            dict(care_type=CareType.fertilize, interval_days_min=42, interval_days_max=56,
                 notes="Every 6-8 weeks during growing season. Excess fertilizer causes brown leaf tips."),
            dict(care_type=CareType.mist, interval_days_min=2, interval_days_max=3,
                 notes="Appreciates regular misting or a pebble tray for humidity."),
        ],
        "traits": [
            dict(trait="growth_rate", value="moderate"),
            dict(trait="propagation", value="division"),
            dict(trait="native_region", value="Central and South America"),
        ],
    },
    {
        "species": dict(
            common_name="Spider Plant",
            scientific_name="Chlorophytum comosum",
            light_need=LightNeed.bright_indirect,
            humidity_pct_min=40, humidity_pct_max=60,
            temp_f_min=60, temp_f_max=80,
            soil_type="Standard well-draining mix",
            toxic_to_pets=False,
            care_notes="Pet-safe. Brown leaf tips usually mean fluoride/chloride in tap water; use filtered water.",
        ),
        "schedules": [
            dict(care_type=CareType.water, interval_days_min=7, interval_days_max=10,
                 notes="Let top inch dry. Use filtered water to avoid brown tips from chlorine."),
            dict(care_type=CareType.fertilize, interval_days_min=30, interval_days_max=60,
                 notes="Moderate feeder. Balanced liquid fertilizer in spring/summer."),
            dict(care_type=CareType.repot, interval_days_min=365, interval_days_max=730,
                 notes="Thick tuberous roots fill pots fast. Repot when roots push up through soil."),
        ],
        "traits": [
            dict(trait="growth_rate", value="fast"),
            dict(trait="propagation", value="plantlet division"),
            dict(trait="native_region", value="Southern Africa"),
        ],
    },
    {
        "species": dict(
            common_name="Fiddle Leaf Fig",
            scientific_name="Ficus lyrata",
            light_need=LightNeed.bright_indirect,
            humidity_pct_min=40, humidity_pct_max=60,
            temp_f_min=65, temp_f_max=80,
            soil_type="Well-draining potting mix",
            toxic_to_pets=True,
            care_notes="Hates being moved and hates drafts. Wants bright consistent light and a steady watering rhythm.",
        ),
        "schedules": [
            dict(care_type=CareType.water, interval_days_min=7, interval_days_max=10,
                 notes="Consistent schedule is key. Let top inch dry; brown spots can mean overwatering."),
            dict(care_type=CareType.fertilize, interval_days_min=30, interval_days_max=42,
                 notes="High-nitrogen fertilizer during growing season for leaf production."),
            dict(care_type=CareType.clean, interval_days_min=14, interval_days_max=30,
                 notes="Dust large leaves with damp cloth. Helps light absorption."),
            dict(care_type=CareType.rotate, interval_days_min=7, interval_days_max=14,
                 notes="Quarter-turn weekly for even growth. Hates full relocation but tolerates rotation."),
        ],
        "traits": [
            dict(trait="growth_rate", value="moderate"),
            dict(trait="max_height_inches", value="72", unit="inches"),
            dict(trait="native_region", value="West Africa"),
        ],
    },
    {
        "species": dict(
            common_name="Aloe Vera",
            scientific_name="Aloe barbadensis miller",
            light_need=LightNeed.direct,
            humidity_pct_min=20, humidity_pct_max=40,
            temp_f_min=55, temp_f_max=80,
            soil_type="Cactus/succulent mix",
            toxic_to_pets=True,
            care_notes="Succulent. Water deeply but infrequently; let soil dry fully. Wants direct sun.",
        ),
        "schedules": [
            dict(care_type=CareType.water, interval_days_min=14, interval_days_max=21,
                 notes="Soak and dry method. Water deeply, then let soil dry completely."),
            dict(care_type=CareType.fertilize, interval_days_min=90, interval_days_max=120,
                 notes="Very light feeder. Dilute succulent fertilizer a few times per year."),
            dict(care_type=CareType.repot, interval_days_min=730, interval_days_max=1095,
                 notes="Repot when offshoots crowd the pot. Separate pups during repotting."),
        ],
        "traits": [
            dict(trait="growth_rate", value="slow"),
            dict(trait="propagation", value="offshoot/pup separation"),
            dict(trait="native_region", value="Arabian Peninsula"),
        ],
    },
    {
        "species": dict(
            common_name="Rubber Plant",
            scientific_name="Ficus elastica",
            light_need=LightNeed.bright_indirect,
            humidity_pct_min=40, humidity_pct_max=60,
            temp_f_min=60, temp_f_max=80,
            soil_type="Well-draining potting mix",
            toxic_to_pets=True,
            care_notes="Wipe leaves to keep them glossy and dust-free. Let top inch dry between waterings.",
        ),
        "schedules": [
            dict(care_type=CareType.water, interval_days_min=7, interval_days_max=12,
                 notes="Let top inch dry between waterings. Drooping leaves = thirsty."),
            dict(care_type=CareType.fertilize, interval_days_min=14, interval_days_max=30,
                 notes="Moderate-to-heavy feeder in spring/summer. Balanced liquid fertilizer."),
            dict(care_type=CareType.clean, interval_days_min=7, interval_days_max=14,
                 notes="Wipe glossy leaves regularly. Dust blocks light on these broad surfaces."),
            dict(care_type=CareType.rotate, interval_days_min=7, interval_days_max=14,
                 notes="Quarter-turn regularly for even growth toward light."),
        ],
        "traits": [
            dict(trait="growth_rate", value="moderate"),
            dict(trait="max_height_inches", value="72", unit="inches"),
            dict(trait="propagation", value="stem cutting or air layering"),
            dict(trait="native_region", value="Southeast Asia"),
        ],
    },
    {
        "species": dict(
            common_name="Calathea",
            scientific_name="Goeppertia orbifolia",
            light_need=LightNeed.medium,
            humidity_pct_min=60, humidity_pct_max=80,
            temp_f_min=65, temp_f_max=80,
            soil_type="Moisture-retentive, airy mix",
            toxic_to_pets=False,
            care_notes="Pet-safe but fussy. Needs high humidity and distilled/filtered water; crispy edges signal low humidity or hard water.",
        ),
        "schedules": [
            dict(care_type=CareType.water, interval_days_min=4, interval_days_max=7,
                 notes="Keep soil lightly moist, never soggy. Use filtered or distilled water."),
            dict(care_type=CareType.fertilize, interval_days_min=30, interval_days_max=60,
                 notes="Light feeder. Dilute balanced fertilizer in growing season. Flush soil periodically."),
            dict(care_type=CareType.mist, interval_days_min=1, interval_days_max=2,
                 notes="Daily to every-other-day misting, or use a humidifier. Crispy edges = too dry."),
        ],
        "traits": [
            dict(trait="growth_rate", value="moderate"),
            dict(trait="propagation", value="division at repotting"),
            dict(trait="native_region", value="South America"),
        ],
    },
]


def seed_default_environment() -> None:
    """Create a default Environment for this installation if none exists yet.

    Called on every startup — safe to run repeatedly. The name and type can be
    pre-configured via DEFAULT_ENV_NAME / DEFAULT_ENV_TYPE env vars (useful for
    nursery or community-garden deployments that want a different default)."""
    with Session(engine) as session:
        existing = session.exec(select(Environment)).first()
        if existing:
            return
        env_name = os.getenv("DEFAULT_ENV_NAME", "My Garden")
        env_type_str = os.getenv("DEFAULT_ENV_TYPE", "home")
        try:
            env_type = EnvironmentType(env_type_str)
        except ValueError:
            env_type = EnvironmentType.home
        env = Environment(name=env_name, type=env_type)
        session.add(env)
        session.commit()
        print(f"Created default environment: '{env_name}' ({env_type.value})")


def seed() -> None:
    """Seed species from species_catalog.json.

    Idempotent per scientific name — existing species are skipped, missing
    ones are added. Run after editing the catalog to pick up new entries
    on an existing database without wiping anything."""
    init_db()
    # Add any columns introduced since the DB was created BEFORE querying the
    # tables — otherwise seeding an existing DB (e.g. the deployed one) crashes
    # selecting columns the old table lacks. The app lifespan also migrates,
    # but the Dockerfile runs this seed first, so it must migrate itself.
    migrate_db()
    catalog = _load_catalog()
    added = 0
    with Session(engine) as session:
        for entry in catalog:
            sci_name = entry["species"]["scientific_name"]
            if session.exec(select(Species).where(Species.scientific_name == sci_name)).first():
                continue

            s_dict = dict(entry["species"])
            s_dict["light_need"] = LightNeed(s_dict["light_need"])
            species = Species(**s_dict)
            session.add(species)
            session.flush()

            for sched in entry["schedules"]:
                sd = dict(sched)
                sd["care_type"] = CareType(sd["care_type"])
                session.add(CareSchedule(species_id=species.id, **sd))

            for trait in entry.get("traits", []):
                session.add(SpeciesTrait(species_id=species.id, **trait))

            added += 1

        session.commit()

    if added:
        print(f"Seeded {added} new species from catalog.")
    else:
        print("Species catalog already up to date.")


if __name__ == "__main__":
    seed()
    seed_default_environment()
