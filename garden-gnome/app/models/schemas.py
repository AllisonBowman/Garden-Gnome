from datetime import date, datetime
from typing import Optional

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.data.claims.recompute import SERVER_ONLY_FIELDS
from app.models.models import (
    MaturityStage, CareOutcome, CareType, LightNeed, SoilMoisture, LeafCondition, EnvironmentType,
    ReviewStatus, SpeciesSource, Shelter, TempExposure, SunExposure,
    CareDataStatus, FertilizeStrength, HumidityNeed, OutdoorSunExposure,
    SoilBase, SoilDrainage, WaterRegime,
)


# --- Auth (Phase 5) ---

class AppleSignInRequest(SQLModel):
    identity_token: str
    authorization_code: str
    raw_nonce: str
    # Apple sends the user's name ONLY on first authorization
    full_name: Optional[str] = None


class GoogleSignInRequest(SQLModel):
    id_token: str


class RefreshRequest(SQLModel):
    refresh_token: str


class LogoutRequest(SQLModel):
    refresh_token: str


class UserOut(SQLModel):
    id: str
    email: Optional[str]
    display_name: Optional[str]
    census_opt_in: bool
    created_at: datetime


class UserPatch(SQLModel):
    display_name: Optional[str] = None
    # Per-user census consent (decision 3) — settable only by the user
    census_opt_in: Optional[bool] = None


class AuthTokensOut(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


# --- Environment ---

class EnvironmentCreate(SQLModel):
    name: str
    type: EnvironmentType = EnvironmentType.home
    city: str = ""
    region: str = ""
    country: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    shelter: Shelter = Shelter.sheltered
    temp_exposure: TempExposure = TempExposure.indoor
    sun_exposure: SunExposure = SunExposure.partial_sun


class EnvironmentPatch(SQLModel):
    name: Optional[str] = None
    type: Optional[EnvironmentType] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    shelter: Optional[Shelter] = None
    temp_exposure: Optional[TempExposure] = None
    sun_exposure: Optional[SunExposure] = None


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
    shelter: Shelter
    temp_exposure: TempExposure
    sun_exposure: SunExposure
    created_at: datetime
    plant_count: int = 0  # computed in the router, not stored


# --- Plant ---

class PlantCreate(SQLModel):
    # Optional: a garden captured as plantings ("twelve tomatoes") has no
    # natural nickname. The router fills one in from the species and place so
    # notification bodies, to-do rows and the advisor prompts — all of which
    # address the plant by name — never have to render an empty string.
    nickname: str = ""
    species_id: int
    quantity: int = Field(default=1, ge=1)
    environment_id: Optional[int] = None  # defaults to the installation's primary environment
    location: str = ""
    maturity_stage: MaturityStage = MaturityStage.juvenile
    acquired_on: Optional[date] = None
    soil_moisture_at_acquisition: Optional[SoilMoisture] = None
    leaf_condition_at_acquisition: Optional[LeafCondition] = None
    pest_observed_at_acquisition: bool = False
    intake_notes: str = ""


class CareSourceRead(SQLModel):
    """Who said so, as much as a client may see: the authority's name, the
    page, and which fields that page settled. `inferred` marks a page whose
    every field came in at genus scope. No title -- the per-citation title is
    researcher prose, not a document name -- and never the quote (ADR 0003)."""
    authority: str
    url: str
    fields: list[str] = []
    inferred: bool = False


class SpeciesRead(SQLModel):
    """A species as a client sees it: identity, the resolved care values with
    their provenance, and the legacy columns where nothing better exists.

    Server-side only, deliberately absent: `toxicity_detail` and
    `water_dry_down_target` (verbatim passages, ADR 0003),
    `water_estimate_basis` and `cool_rest_note` (the researcher's
    assumptions), `resolver_version`, and the review trail (operator state)."""
    id: int
    common_name: str
    scientific_name: str
    # The tranche's accepted name when it differs from `scientific_name`; how
    # a row the catalog holds under an older name is linked to its evidence.
    # Never a rename.
    scientific_name_accepted: Optional[str] = None
    # Nullable since migration 0015: a claims-minted row (ADR 0005) carries
    # none of these, and a null toxic_to_pets means "no record", not "safe".
    light_need: Optional[LightNeed] = None
    humidity_pct_min: Optional[int] = None
    humidity_pct_max: Optional[int] = None
    temp_f_min: Optional[int] = None
    temp_f_max: Optional[int] = None
    soil_type: Optional[str] = None
    toxic_to_pets: Optional[bool] = None
    # Derived on the model — the sentence a person should read. toxic_to_pets
    # remains the raw flag for filtering.
    toxicity_description: str = ""
    # False when the humidity numbers were derived from a watering category
    # rather than a source (imported rows). Clients hide the stat and stop
    # sorting on it; the advisor omits it from the fact block.
    humidity_sourced: bool = True
    care_notes: str = ""
    # Derived by the recompute (ADR 0001): how well-backed the values are
    # and, per field, whether it was cited to this species or borrowed from
    # its genus -- which every surface must label (ADR 0002).
    care_data_status: Optional[CareDataStatus] = None
    care_provenance: Optional[dict[str, str]] = None
    # The resolved care columns, exactly as the claims settled them.
    light_fc_min: Optional[int] = None
    light_fc_good: Optional[int] = None
    direct_sun_hours_max: Optional[float] = None
    outdoor_sun_exposure: Optional[list[OutdoorSunExposure]] = None
    water_regime: Optional[WaterRegime] = None
    water_check_depth_cm: Optional[float] = None
    # Floats, although the model says int: the day counts are estimates and
    # the tranche carries a half-day (Carica papaya, 3.5), which SQLite keeps
    # as written. A serializer that refused it would 500 the whole list.
    water_growing_days_est: Optional[float] = None
    water_dormant_days_est: Optional[float] = None
    humidity_need: Optional[HumidityNeed] = None
    day_f_min: Optional[int] = None
    day_f_max: Optional[int] = None
    night_f_min: Optional[int] = None
    night_f_max: Optional[int] = None
    chill_damage_f: Optional[int] = None
    soil_base: Optional[SoilBase] = None
    soil_drainage: Optional[SoilDrainage] = None
    soil_ph_min: Optional[float] = None
    soil_ph_max: Optional[float] = None
    fertilize_active_months: Optional[list[int]] = None
    fertilize_interval_days: Optional[int] = None
    fertilize_strength: Optional[FertilizeStrength] = None
    hardiness_zones: Optional[list[int]] = None

    @field_validator("care_provenance", mode="before")
    @classmethod
    def _only_columns_the_client_has(cls, value):
        """The row's provenance names every resolved column, the server-only
        ones included. A client has no such column to attach an entry to, and
        the name alone announces what is being held back -- so those entries
        are dropped, and a provenance left empty reads as absent."""
        if not value:
            return value
        return {k: v for k, v in value.items() if k not in SERVER_ONLY_FIELDS} or None


class PlantRead(SQLModel):
    id: int
    plant_uuid: str
    nickname: str
    species_id: int
    quantity: int = 1
    split_from_uuid: Optional[str] = None
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


class PlantBulkCreate(SQLModel):
    """Create many plants in one transaction.

    A garden captured in one pass is a batch by nature: the offline queue
    flushes as a batch, and 300 single POSTs against a machine that has to
    cold-start reliably time out. Either every plant lands or none do, so a
    failure halfway through can't leave a half-imported garden."""
    plants: list[PlantCreate] = Field(min_length=1, max_length=200)


class PlantBulkResult(SQLModel):
    created: int
    plants: list["PlantRead"]


class PlantSplitRequest(SQLModel):
    """Move part of a planting out into its own row.

    Splitting is the only operation that gives a second plant_uuid to plants
    previously counted under one, so the new row records where it came from and
    the original's count drops by the same amount — the total is conserved."""
    quantity: int = Field(ge=1)
    to_environment_id: Optional[int] = None
    location: Optional[str] = None
    notes: str = ""


class PlantTransferRequest(SQLModel):
    """Move a plant to a different environment and open a new stewardship record.

    The plant's plant_uuid is preserved so census aggregators treat it as the
    same physical plant, not a new one."""
    to_environment_id: int
    transfer_notes: str = ""


# --- Care logs ---

class CareLogCreate(SQLModel):
    action: CareType
    # What the check ended in (watered / checked_not_needed, repotted /
    # top_dressed / checked_fine). Optional: quick-logs may omit it, and
    # actions outside OUTCOMES_BY_ACTION never carry one.
    outcome: Optional[CareOutcome] = None
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
    # None rather than False: an omitted flag is "no record". A default False
    # would mint the safety verdict ADR 0005 made the column nullable to avoid.
    toxic_to_pets: Optional[bool] = None
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


class SpeciesDetail(SpeciesRead):
    """The list shape plus what only the detail screen shows: the pages the
    values came from, the care schedules and the traits. The review trail
    (source, source_ref, review_status, review_note) is operator state and
    stays on the server, as it already did for the list."""
    care_sources: list[CareSourceRead] = []
    care_schedules: list[CareScheduleRead] = []
    traits: list[SpeciesTraitRead] = []

    @field_validator("care_sources", mode="before")
    @classmethod
    def _null_means_never_recomputed(cls, value):
        """A row the recompute has not reached holds null, not an empty
        list; a client gets the list either way, so nothing can 500 on it."""
        return [] if value is None else value


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
