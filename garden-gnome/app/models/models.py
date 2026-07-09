from datetime import datetime, date
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship


class MaturityStage(str, Enum):
    seedling = "seedling"
    juvenile = "juvenile"
    mature = "mature"
    flowering = "flowering"


class LightNeed(str, Enum):
    low = "low"
    medium = "medium"
    bright_indirect = "bright_indirect"
    direct = "direct"


class CareType(str, Enum):
    water = "water"
    fertilize = "fertilize"
    mist = "mist"
    prune = "prune"
    repot = "repot"
    rotate = "rotate"
    clean = "clean"
    other = "other"


class SoilMoisture(str, Enum):
    dry = "dry"
    moist = "moist"
    wet = "wet"


class LeafCondition(str, Enum):
    healthy = "healthy"
    yellowing = "yellowing"
    browning = "browning"
    wilting = "wilting"
    pest_damage = "pest_damage"
    dropping = "dropping"


class EnvironmentType(str, Enum):
    home = "home"
    nursery = "nursery"
    community_garden = "community_garden"
    conservation = "conservation"
    research = "research"


class SpeciesSource(str, Enum):
    curated = "curated"            # hand-written original catalog
    perenual = "perenual"          # mapped from the Perenual API
    llm_generated = "llm_generated"  # drafted by /species/generate — heavier review


class ReviewStatus(str, Enum):
    approved = "approved"          # passed automated validation
    needs_review = "needs_review"  # flagged by validation; in the review queue
    verified = "verified"          # manually cross-checked against an authority


class Species(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    common_name: str = Field(index=True)
    scientific_name: str = Field(index=True)

    light_need: LightNeed
    humidity_pct_min: int
    humidity_pct_max: int
    temp_f_min: int
    temp_f_max: int
    soil_type: str
    toxic_to_pets: bool = False
    care_notes: str = ""

    # Provenance + review trail for catalog expansion
    source: SpeciesSource = SpeciesSource.curated
    source_ref: str = ""           # e.g. Perenual species id, for traceability
    review_status: ReviewStatus = ReviewStatus.approved
    review_note: str = ""          # citation from manual verification (source + URL)

    plants: list["Plant"] = Relationship(back_populates="species")
    care_schedules: list["CareSchedule"] = Relationship(back_populates="species")
    traits: list["SpeciesTrait"] = Relationship(back_populates="species")


class CareSchedule(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("species_id", "care_type"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    species_id: int = Field(foreign_key="species.id")
    care_type: CareType
    interval_days_min: int
    interval_days_max: int
    notes: str = ""

    species: Optional[Species] = Relationship(back_populates="care_schedules")


class SpeciesTrait(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("species_id", "trait"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    species_id: int = Field(foreign_key="species.id")
    trait: str = Field(index=True)
    value: str
    unit: str = ""

    species: Optional[Species] = Relationship(back_populates="traits")


class Environment(SQLModel, table=True):
    """A physical place where plants are kept and stewarded.

    Separate from stewardship (who cares for the plant) so that the same
    location can host plants across multiple stewards over time, and so
    census queries can index over geography and environment type
    independently of ownership history."""
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid4()), unique=True)
    name: str
    type: EnvironmentType = EnvironmentType.home
    city: str = ""
    region: str = ""
    country: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    plants: list["Plant"] = Relationship(back_populates="environment")


class Plant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Canonical UUID: never changes, even when the plant is transferred to a
    # new owner or installation. Census aggregators use this to deduplicate.
    plant_uuid: str = Field(default_factory=lambda: str(uuid4()), unique=True)
    nickname: str
    species_id: int = Field(foreign_key="species.id")
    environment_id: Optional[int] = Field(default=None, foreign_key="environment.id")

    location: str = ""
    maturity_stage: MaturityStage = MaturityStage.juvenile
    acquired_on: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Intake snapshot — condition captured once at add-time, not a recurring
    # event like CareLog. Surfaced as the plant's first timeline entry.
    soil_moisture_at_acquisition: Optional[SoilMoisture] = None
    leaf_condition_at_acquisition: Optional[LeafCondition] = None
    pest_observed_at_acquisition: bool = False
    intake_notes: str = ""

    species: Optional[Species] = Relationship(back_populates="plants")
    environment: Optional[Environment] = Relationship(back_populates="plants")
    # A plant's history is meaningless without the plant; delete it together
    care_logs: list["CareLog"] = Relationship(back_populates="plant", cascade_delete=True)
    stewardship_records: list["StewardshipRecord"] = Relationship(back_populates="plant", cascade_delete=True)


class CareLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plant_id: int = Field(foreign_key="plant.id")
    action: CareType
    notes: str = ""
    logged_at: datetime = Field(default_factory=datetime.utcnow)

    plant: Optional[Plant] = Relationship(back_populates="care_logs")


class StewardshipRecord(SQLModel, table=True):
    """Chain-of-custody record: who had a plant, in which environment, and when.

    Stewardship (who cares for it) and location (where it lives) are captured
    as separate dimensions so census queries can ask independently: "how many
    stewards has this plant had?" vs "which environments has it lived in?"

    ended_at=None means this is the current active stewardship. A plant
    with stewardship_count > 1 has been transferred; its plant_uuid persists
    across transfers so the census never double-counts it."""
    id: Optional[int] = Field(default=None, primary_key=True)
    plant_id: int = Field(foreign_key="plant.id")
    environment_id: int = Field(foreign_key="environment.id")
    # Which GardenGnome installation holds this stewardship
    installation_uuid: str = Field(default="", index=True)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    transfer_notes: str = ""

    plant: Optional[Plant] = Relationship(back_populates="stewardship_records")
