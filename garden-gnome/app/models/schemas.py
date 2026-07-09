from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models.models import (
    MaturityStage, CareType, LightNeed, SoilMoisture, LeafCondition, EnvironmentType,
    ReviewStatus, SpeciesSource,
)


# --- Environment ---

class EnvironmentCreate(SQLModel):
    name: str
    type: EnvironmentType = EnvironmentType.home
    city: str = ""
    region: str = ""
    country: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None


class EnvironmentRead(SQLModel):
    id: int
    uuid: str
    name: str
    type: EnvironmentType
    city: str
    region: str
    country: str
    lat: Optional[float]
    lng: Optional[float]
    created_at: datetime
    plant_count: int = 0  # computed in the router, not stored


# --- Plant ---

class PlantCreate(SQLModel):
    nickname: str
    species_id: int
    environment_id: Optional[int] = None  # defaults to the installation's primary environment
    location: str = ""
    maturity_stage: MaturityStage = MaturityStage.juvenile
    acquired_on: Optional[date] = None
    soil_moisture_at_acquisition: Optional[SoilMoisture] = None
    leaf_condition_at_acquisition: Optional[LeafCondition] = None
    pest_observed_at_acquisition: bool = False
    intake_notes: str = ""


class SpeciesRead(SQLModel):
    id: int
    common_name: str
    scientific_name: str
    light_need: LightNeed
    humidity_pct_min: int
    humidity_pct_max: int
    temp_f_min: int
    temp_f_max: int
    soil_type: str
    toxic_to_pets: bool
    care_notes: str


class PlantRead(SQLModel):
    id: int
    plant_uuid: str
    nickname: str
    species_id: int
    environment_id: Optional[int]
    location: str
    maturity_stage: MaturityStage
    acquired_on: Optional[date]
    soil_moisture_at_acquisition: Optional[SoilMoisture]
    leaf_condition_at_acquisition: Optional[LeafCondition]
    pest_observed_at_acquisition: bool
    intake_notes: str
    # Embedded so clients don't need a second request per plant
    species: Optional[SpeciesRead] = None


class PlantTransferRequest(SQLModel):
    """Move a plant to a different environment and open a new stewardship record.

    The plant's plant_uuid is preserved so census aggregators treat it as the
    same physical plant, not a new one."""
    to_environment_id: int
    transfer_notes: str = ""


# --- Care logs ---

class CareLogCreate(SQLModel):
    action: CareType
    notes: str = ""


# --- Advice ---

class AdviceRequest(SQLModel):
    symptoms: str = ""


# --- Stewardship ---

class StewardshipRecordRead(SQLModel):
    id: int
    plant_id: int
    environment_id: int
    installation_uuid: str
    started_at: datetime
    ended_at: Optional[datetime]
    transfer_notes: str


# --- Species write schemas ---

class CareScheduleCreate(SQLModel):
    care_type: CareType
    interval_days_min: int
    interval_days_max: int
    notes: str = ""


class SpeciesTraitCreate(SQLModel):
    trait: str
    value: str
    unit: str = ""


class SpeciesCreate(SQLModel):
    """Full species record with nested schedules and traits.
    Matches the shape of entries in species_catalog.json so the same
    structure works for API creation, bulk import, and LLM generation."""
    common_name: str
    scientific_name: str
    light_need: LightNeed
    humidity_pct_min: int
    humidity_pct_max: int
    temp_f_min: int
    temp_f_max: int
    soil_type: str
    toxic_to_pets: bool = False
    care_notes: str = ""
    source: SpeciesSource = SpeciesSource.curated
    source_ref: str = ""
    review_status: ReviewStatus = ReviewStatus.approved
    review_note: str = ""
    schedules: list[CareScheduleCreate] = []
    traits: list[SpeciesTraitCreate] = []


class SpeciesGenerateRequest(SQLModel):
    name: str  # common or scientific name to generate a profile for


# --- Species read schemas ---

class CareScheduleRead(SQLModel):
    id: int
    species_id: int
    care_type: CareType
    interval_days_min: int
    interval_days_max: int
    notes: str


class SpeciesTraitRead(SQLModel):
    id: int
    species_id: int
    trait: str
    value: str
    unit: str


class SpeciesDetail(SQLModel):
    id: int
    common_name: str
    scientific_name: str
    light_need: LightNeed
    humidity_pct_min: int
    humidity_pct_max: int
    temp_f_min: int
    temp_f_max: int
    soil_type: str
    toxic_to_pets: bool
    care_notes: str
    source: SpeciesSource = SpeciesSource.curated
    source_ref: str = ""
    review_status: ReviewStatus = ReviewStatus.approved
    review_note: str = ""
    care_schedules: list[CareScheduleRead] = []
    traits: list[SpeciesTraitRead] = []


# --- Timeline ---

class TimelineEntry(SQLModel):
    id: int
    action: CareType
    notes: str
    logged_at: datetime
    days_since_previous: Optional[int] = None  # gap from prior log of same care_type


class CareTypeSummary(SQLModel):
    care_type: CareType
    count: int
    last_logged_at: Optional[datetime] = None
    avg_interval_days: Optional[float] = None
    min_interval_days: Optional[int] = None
    max_interval_days: Optional[int] = None
    scheduled_interval_days_min: Optional[int] = None
    scheduled_interval_days_max: Optional[int] = None


class PlantTimelineSummary(SQLModel):
    plant_id: int
    nickname: str
    by_care_type: list[CareTypeSummary]
