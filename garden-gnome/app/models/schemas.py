from datetime import date, datetime
from typing import Optional

from pydantic import AliasChoices, computed_field, field_validator
from sqlmodel import Field, SQLModel

from app.data.claims.recompute import SERVER_ONLY_FIELDS
from app.models.models import (
    MaturityStage, CareOutcome, CareType, LightNeed, SoilMoisture, LeafCondition, GrowingAreaType,
    ReviewStatus, SpeciesSource, Shelter, TempExposure, SunExposure,
    CareDataStatus, FertilizeStrength, HumidityNeed, OutdoorSunExposure,
    SoilBase, SoilDrainage, WaterRegime, GrowingSurface, GrowingGoal,
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


# --- GrowingArea ---

class GrowingAreaCreate(SQLModel):
    name: str
    type: GrowingAreaType = GrowingAreaType.home
    city: str = ""
    region: str = ""
    country: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    shelter: Shelter = Shelter.sheltered
    temp_exposure: TempExposure = TempExposure.indoor
    sun_exposure: SunExposure = SunExposure.partial_sun

    # Real estate. Unset means unanswered, never a default dimension -- see
    # GrowingArea in models.py.
    surface: Optional[GrowingSurface] = None
    area_sqft: Optional[float] = None
    headroom_in: Optional[float] = None
    soil_depth_in: Optional[float] = None
    goals: Optional[list[GrowingGoal]] = None


class GrowingAreaPatch(SQLModel):
    name: Optional[str] = None
    type: Optional[GrowingAreaType] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    shelter: Optional[Shelter] = None
    temp_exposure: Optional[TempExposure] = None
    sun_exposure: Optional[SunExposure] = None
    surface: Optional[GrowingSurface] = None
    area_sqft: Optional[float] = None
    headroom_in: Optional[float] = None
    soil_depth_in: Optional[float] = None
    goals: Optional[list[GrowingGoal]] = None


class GrowingAreaRead(SQLModel):
    id: int
    uuid: str
    name: str
    type: GrowingAreaType
    city: str
    region: str
    country: str
    lat: Optional[float]
    lng: Optional[float]
    shelter: Shelter
    temp_exposure: TempExposure
    sun_exposure: SunExposure
    surface: Optional[GrowingSurface]
    area_sqft: Optional[float]
    headroom_in: Optional[float]
    soil_depth_in: Optional[float]
    goals: Optional[list[GrowingGoal]]
    created_at: datetime
    plant_count: int = 0  # computed in the router, not stored


# --- Fit (growing area <-> species) ---

class FitFindingRead(SQLModel):
    """One axis's verdict, and the sentence a person reads for it.

    `sentence` is the whole point: a bare verdict says a plant is wrong for a
    spot without saying how, which is not something anyone can act on. It
    already carries the genus-borrowed label when the value it rests on was
    inherited (ADR 0002), so a client renders it as-is.
    """
    axis: str
    verdict: str      # fits | misfits | unknown
    sentence: str
    borrowed: bool = False
    # Who said so: the authorities whose pages settled a value this finding
    # rests on, for this species itself. Empty for an unknown and for a value
    # only the genus answered -- `borrowed` carries that.
    authorities: list[str] = []
    # Which of the area's goals this finding answers (edible, low_upkeep,
    # pollinators), or null. Two goals share the `goal` axis.
    goal: Optional[str] = None


class CandidateRead(SQLModel):
    """A species put forward for a growing area, with why.

    `fits` holds only the confirmed axes -- never the unknown ones. A reader
    should be able to count the reasons, and "we have no idea about its
    mature size" is not a reason to plant something.
    """
    species_id: int
    common_name: str
    scientific_name: str
    score: int        # how many axes actually confirmed; unknowns never count
    fits: list[FitFindingRead]
    # One short caution when the species is recorded toxic to pets or to
    # people ("Toxic to pets and people."), null otherwise. Null is "no
    # record", never "safe". A recommendation that fits a space is still a
    # plant someone's dog or child can eat, and the row has to say so.
    hazard: Optional[str] = None


class PlantMisfitRead(SQLModel):
    """A plant already in the area, and what specifically doesn't suit it."""
    plant_id: int
    nickname: str
    species_id: int
    common_name: str
    misfits: list[FitFindingRead]


class SpeciesFitRead(SQLModel):
    """One species against one area, every axis -- what Add Plant asks
    before the plant is saved.

    `findings` holds fits, misfits AND unknowns, in reading order, so the
    client can show what is against it without being able to mistake
    silence for a pass. `candidate` is the server's own Candidate rule, so
    no client re-derives it."""
    species_id: int
    common_name: str
    scientific_name: str
    score: int
    candidate: bool
    findings: list[FitFindingRead]


# --- Pre-rename field names, for the TestFlight 1.1.2 client ---
#
# PR #20 renamed Environment to GrowingArea, and the build testers have
# installed predates it. That build sends `environment_id` when it adds a
# plant and `to_environment_id` when it moves one, and it reads
# `environment_id` off every plant to sort care lists, weather nudges and
# reminders into areas. Against the new names alone, a plant added from it
# lands in the oldest area instead of the one picked, every move is a 422,
# every per-area care list and weather nudge comes up empty, and the census
# screen, which counts areas under the old keys, throws.
#
# So for one release the old names travel with the new ones. A request may
# use either, and the new name wins when a client sends both; a response
# carries both, with the same value. The new name stays canonical: it is the
# only one the request schemas document, and the old one is marked
# deprecated wherever a response carries it.
#
# This is the field half of the deprecation whose route half is
# `legacy_router` in app/routers/growing_areas.py, and the two go together.
# Once the next build is the floor, delete legacy_router and its mount, then
# this section. Every schema and route still using it then fails at import,
# which is the list of what else comes out.

def _or_pre_rename(name: str, old: str) -> AliasChoices:
    """Let a request field arrive under its pre-rename name too. The current
    name is listed first, so it is the one the schema documents and the one
    that wins when a client sends both."""
    return AliasChoices(name, old)


def _pre_rename_copy(name: str) -> dict:
    """`computed_field` arguments for a response field that repeats `name`
    under its old name. Marked deprecated in the schema through
    json_schema_extra rather than `deprecated=True`, which would also raise a
    DeprecationWarning on every serialization -- that is, on every response."""
    return {
        "description": (
            f"Deprecated: the pre-rename name of `{name}`, always the same "
            "value. Kept for the TestFlight 1.1.2 client, and removed together "
            "with the /environments route alias."
        ),
        "json_schema_extra": {"deprecated": True},
    }


def with_pre_rename_census_keys(summary: dict) -> dict:
    """The census summary with its pre-rename keys alongside the new ones.
    It is a plain dict with no schema to carry them, so its route calls this."""
    return {
        **summary,
        "total_environments": summary["total_growing_areas"],
        "environments_by_type": summary["growing_areas_by_type"],
        "plants_by_environment_type": summary["plants_by_growing_area_type"],
    }


# --- Plant ---

class PlantCreate(SQLModel):
    # Optional: a garden captured as plantings ("twelve tomatoes") has no
    # natural nickname. The router fills one in from the species and place so
    # notification bodies, to-do rows and the advisor prompts — all of which
    # address the plant by name — never have to render an empty string.
    nickname: str = ""
    species_id: int
    quantity: int = Field(default=1, ge=1)
    # Defaults to the installation's primary growing_area.
    growing_area_id: Optional[int] = Field(
        default=None,
        validation_alias=_or_pre_rename("growing_area_id", "environment_id"))
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
    outdoor_temp_min_f: Optional[float] = None

    # Fit fields (0019) -- matched against a growing area's real estate.
    is_houseplant: Optional[bool] = None
    is_edible: Optional[bool] = None
    # Derived on the model: the condition on eating it, when there is one --
    # the plant is also recorded as poisonous, or its cited edibility
    # passage limits the parts or needs preparation. A client shows this in
    # place of "grown to eat" whenever it is set; the passage itself stays
    # on the server (ADR 0003).
    edibility_note: Optional[str] = None
    attracts_pollinators: Optional[bool] = None
    climbs: Optional[bool] = None
    mature_height_in_min: Optional[float] = None
    mature_height_in_max: Optional[float] = None
    mature_spread_in_min: Optional[float] = None
    mature_spread_in_max: Optional[float] = None

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
    growing_area_id: Optional[int]
    location: str
    maturity_stage: MaturityStage
    acquired_on: Optional[date]
    soil_moisture_at_acquisition: Optional[SoilMoisture]
    leaf_condition_at_acquisition: Optional[LeafCondition]
    pest_observed_at_acquisition: bool
    intake_notes: str
    # Embedded so clients don't need a second request per plant
    species: Optional[SpeciesRead] = None

    @computed_field(**_pre_rename_copy("growing_area_id"))
    @property
    def environment_id(self) -> Optional[int]:
        return self.growing_area_id


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
    to_growing_area_id: Optional[int] = Field(
        default=None,
        validation_alias=_or_pre_rename("to_growing_area_id", "to_environment_id"))
    location: Optional[str] = None
    notes: str = ""


class PlantTransferRequest(SQLModel):
    """Move a plant to a different growing area and open a new stewardship record.

    The plant's plant_uuid is preserved so census aggregators treat it as the
    same physical plant, not a new one."""
    to_growing_area_id: int = Field(
        validation_alias=_or_pre_rename("to_growing_area_id", "to_environment_id"))
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
    growing_area_id: int
    installation_uuid: str
    started_at: datetime
    ended_at: Optional[datetime]
    transfer_notes: str

    @computed_field(**_pre_rename_copy("growing_area_id"))
    @property
    def environment_id(self) -> int:
        return self.growing_area_id


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
    def _only_pages_and_fields_the_client_can_see(cls, value):
        """A row the recompute has not reached holds null, not an empty
        list; a client gets the list either way, so nothing can 500 on it.

        And each entry credits a page for the fields it settled. The
        recompute withholds the server-only ones when it writes the list
        (ADR 0003), but the row is what ships, and a row is only as clean as
        the resolver that last touched it -- so the same rule is applied here
        at the door, the way care_provenance is. A page left with nothing a
        reader can check is not listed at all, as the recompute would not
        list it."""
        kept = []
        for source in value or []:
            entry = source if isinstance(source, dict) else source.model_dump()
            fields = [f for f in entry.get("fields") or []
                      if f not in SERVER_ONLY_FIELDS]
            if fields:
                kept.append({**entry, "fields": fields})
        return kept


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


# --- Land stewardship (build spec section 4) -------------------------------------
#
# The whole contract the 1.2.0 app is typed against (mobile/src/types/site.ts).
# Field names and literal values are fixed by the spec; change neither without
# changing the spec. Dates are ISO YYYY-MM-DD, instants ISO 8601 in UTC.
# `Optional[...] = None` is the spec's "?": the key is always present and may
# be null.

from typing import Any, Literal  # noqa: E402

from pydantic import BaseModel, ConfigDict, model_validator  # noqa: E402

PinSourceLit = Literal["owner_pin", "device_location"]
LotContentLit = Literal[
    "trees_that_drop_leaves", "evergreens", "shrubs", "lawn", "garden_beds",
    "potted_plants", "vegetables", "mostly_paved"]
FrostBiasLit = Literal["earlier", "later"]
ProfileStatusLit = Literal["pending", "building", "ready", "partial", "failed"]
VegetationTypeLit = Literal["tree", "shrub", "grass", "garden_bed", "bare_hardscape"]
LeafHabitLit = Literal["drops_leaves", "evergreen", "mixed"]
BoundarySourceLit = Literal["default", "owner"]
ConfidenceLit = Literal[
    "you_told_us", "you_measured", "good_estimate", "area_estimate",
    "rough_estimate", "not_known_yet", "neighbourhood_context"]
ConfidenceLabelLit = Literal[
    "You told us", "You measured", "Good estimate", "Area estimate",
    "Rough estimate", "Not known yet", "Neighbourhood context"]
ProvenanceLit = Literal["owner", "public_map", "modelled", "default"]
SiteFieldLit = Literal[
    "sun", "soil_drainage", "water_collects", "soil_texture", "soil_ph",
    "disturbed_soil", "slope", "facing", "flooding", "land_cover",
    "hardiness_zone", "frost_dates"]
OverrideKindLit = Literal["choice", "number", "none"]
OverrideMethodLit = Literal["tap", "measured"]
FrostRiskLit = Literal["none", "frost", "freeze", "hard_freeze"]
TaskStateLit = Literal["open", "done", "not_needed"]
AppliesToKindLit = Literal["lot", "zones", "plants"]
SeasonEventTypeLit = Literal[
    "first_frost", "first_freeze", "hard_freeze", "fall_hardening",
    "leaf_drop", "dormancy", "last_frost", "spring_emergence",
    "tender_plants_out", "spring_cleanup"]
SeasonEventStatusLit = Literal[
    "happened", "happening", "forecast", "expected", "typically_around",
    "done", "not_needed"]
OwnerActionLit = Literal[
    "mark_happened", "mark_not_yet", "mark_done", "mark_not_needed", "clear"]
EventStateLit = Literal["done", "not_needed", "happened", "not_yet", "clear"]
VitalToneLit = Literal["ok", "watch", "act"]
VitalKeyLit = Literal[
    "weather_now", "frost", "rain", "heat", "sun", "soil", "drainage", "season"]
SpaceKindLit = Literal["zone", "space"]
#: Screen names from build spec section 6, for VitalCard.link.
ScreenLit = Literal[
    "Home", "PropertySetup", "Land", "ZoneMap", "Season", "Spaces",
    "SpaceDetail", "Plants", "PlantDetail", "AddPlant", "CaptureGarden",
    "Species", "SpeciesDetail", "Settings", "Census"]

#: The words shown for each confidence, fixed by the spec.
CONFIDENCE_LABELS: dict[str, str] = {
    "you_told_us": "You told us",
    "you_measured": "You measured",
    "good_estimate": "Good estimate",
    "area_estimate": "Area estimate",
    "rough_estimate": "Rough estimate",
    "not_known_yet": "Not known yet",
    "neighbourhood_context": "Neighbourhood context",
}

#: The values a site value may be read from, for override validation.
SITE_FIELDS: tuple[str, ...] = SiteFieldLit.__args__  # type: ignore[attr-defined]


class _Shape(BaseModel):
    """Contract shapes refuse keys they do not declare, so a typo in a
    service fails a test instead of reaching the app."""
    model_config = ConfigDict(extra="forbid")


class Box(_Shape):
    """Degrees. The server stores a zone's box as a GeoJSON Polygon."""
    west: float
    south: float
    east: float
    north: float

    @model_validator(mode="after")
    def _ordered(self):
        if not (-180 <= self.west < self.east <= 180):
            raise ValueError("a box needs -180 <= west < east <= 180")
        if not (-90 <= self.south < self.north <= 90):
            raise ValueError("a box needs -90 <= south < north <= 90")
        return self


class LatLng(_Shape):
    lat: float
    lng: float


class ProfileStatus(_Shape):
    fast: ProfileStatusLit = "pending"
    background: ProfileStatusLit = "pending"


class PropertyCreate(_Shape):
    name: Optional[str] = None
    pin_lat: float = Field(ge=-90, le=90)
    pin_lng: float = Field(ge=-180, le=180)
    pin_source: PinSourceLit
    lot_contents: Optional[list[LotContentLit]] = None


class PropertyPatch(_Shape):
    name: Optional[str] = None
    pin_lat: Optional[float] = Field(default=None, ge=-90, le=90)
    pin_lng: Optional[float] = Field(default=None, ge=-180, le=180)
    lot_contents: Optional[list[LotContentLit]] = None
    frost_bias: Optional[FrostBiasLit] = None


class PropertyOut(_Shape):
    id: int
    uuid: str
    name: str
    pin_lat: float
    pin_lng: float
    pin_source: PinSourceLit
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    lot_contents: list[LotContentLit] = []
    frost_bias: Optional[FrostBiasLit] = None
    whole_lot_zone_id: Optional[int] = None
    profile_status: ProfileStatus
    created_at: datetime


class SourceOut(_Shape):
    name: str
    detail: Optional[str] = None
    version: Optional[str] = None
    url: Optional[str] = None


class Explained(_Shape):
    """A value with its reason and sources (PLAN.md D25). `confidence_label`
    may be left out; it is filled from `confidence`, and a label that does
    not match its confidence is refused."""
    display: str
    confidence: ConfidenceLit
    confidence_label: Optional[ConfidenceLabelLit] = None
    reason: str
    sources: list[SourceOut]
    provenance: ProvenanceLit

    @model_validator(mode="after")
    def _label(self):
        want = CONFIDENCE_LABELS[self.confidence]
        if self.confidence_label is None:
            self.confidence_label = want
        elif self.confidence_label != want:
            raise ValueError(
                f"confidence {self.confidence!r} is shown as {want!r}, "
                f"not {self.confidence_label!r}")
        return self


class OverrideChoice(_Shape):
    value: Any
    label: str


class PublicReading(_Shape):
    display: str
    confidence_label: ConfidenceLabelLit


class SiteValue(Explained):
    field: SiteFieldLit
    title: str
    value: Optional[Any] = None
    # Numbers behind `display` that `value` does not carry, added alongside it
    # (sun: {"hours": 7.0}, since its value is the category word). None for an
    # owner's answer and for fields with nothing extra.
    facts: Optional[dict[str, Any]] = None
    zone_id: Optional[int] = None
    can_override: bool = False
    override_choices: list[OverrideChoice] = []
    override_kind: OverrideKindLit = "none"
    # The public-data reading, present only while an owner correction shows.
    public: Optional[PublicReading] = None


class ZoneValues(_Shape):
    zone_id: int
    name: str
    is_whole_lot: bool
    values: list[SiteValue] = []


class SiteProfileOut(_Shape):
    property_id: int
    status: ProfileStatus
    updated_at: Optional[datetime] = None
    values: list[SiteValue] = []
    zones: list[ZoneValues] = []
    notes: list[str] = []


class RefreshOut(_Shape):
    status: str


class OverrideIn(_Shape):
    zone_id: Optional[int] = None
    field: SiteFieldLit
    value: Any
    method: OverrideMethodLit


class ZoneCreate(_Shape):
    name: Optional[str] = None
    vegetation_type: VegetationTypeLit
    box: Box
    leaf_habit: Optional[LeafHabitLit] = None
    #: False when the owner did not draw the box (the approximate whole lot
    #: was used): the zone then counts as the default footprint.
    drawn: bool = True


class ZonePatch(_Shape):
    name: Optional[str] = None
    vegetation_type: Optional[VegetationTypeLit] = None
    box: Optional[Box] = None
    leaf_habit: Optional[LeafHabitLit] = None


class ZoneOut(_Shape):
    id: int
    growing_area_id: int          # the same number as id (PLAN.md D1)
    property_id: int
    name: str
    # Null only for the whole-lot zone, which is every kind of ground at once
    # until the owner describes it.
    vegetation_type: Optional[VegetationTypeLit] = None
    is_whole_lot: bool
    box: Optional[Box] = None
    boundary_source: BoundarySourceLit
    leaf_habit: Optional[LeafHabitLit] = None
    plant_count: int = 0
    values: list[SiteValue] = []


class ImageryOut(_Shape):
    tile_key: str
    image_path: str               # "/imagery/tiles/{tile_key}.jpg"
    width: int
    height: int
    bounds: Box
    source: SourceOut
    captured: Optional[str] = None
    pin: Optional[LatLng] = None
    default_footprint: Optional[Box] = None


#: Map layers over the aerial image (map and visuals spec, section 3).
MapLayerKindLit = Literal["sun", "trees", "water"]
MapLayerStatusLit = Literal["ready", "not_ready", "unavailable"]


class LegendStep(_Shape):
    color: str                    # "#RRGGBB"; the picture draws it semi-transparent
    label: str


class MapLayerOut(_Shape):
    kind: MapLayerKindLit
    title: str
    status: MapLayerStatusLit
    status_text: Optional[str] = None
    image_path: Optional[str] = None   # "/properties/{id}/layers/{kind}.png" when ready
    width: int
    height: int
    legend: list[LegendStep] = []
    explained: Explained
    notes: list[str] = []


class MapLayersOut(_Shape):
    property_id: int
    bounds: Box                   # the whole block, the same as ImageryOut.bounds
    layers: list[MapLayerOut] = []


class ForecastDay(_Shape):
    date: date
    high_f: Optional[float] = None
    low_f: Optional[float] = None
    precipitation_chance: Optional[float] = None
    summary: str
    frost_risk: FrostRiskLit


class ForecastOut(_Shape):
    provider: str
    provider_name: str
    fetched_at: datetime
    days: list[ForecastDay] = []


class AppliesTo(_Shape):
    kind: AppliesToKindLit
    ids: list[int] = []


class SeasonTask(_Shape):
    task_key: str
    text: str
    low_impact_note: Optional[str] = None
    reason: str
    sources: list[SourceOut]
    applies_to: AppliesTo
    state: TaskStateLit = "open"


class EventWindow(_Shape):
    start: Optional[date] = None
    end: Optional[date] = None
    text: str


class SeasonEventSummary(_Shape):
    """A SeasonEvent without its tasks (Vitals.season_ahead)."""
    event_key: str
    type: SeasonEventTypeLit
    title: str
    status: SeasonEventStatusLit
    window: EventWindow
    explained: Explained
    owner_actions: list[OwnerActionLit] = []
    sort_date: Optional[date] = None


class SeasonEvent(SeasonEventSummary):
    tasks: list[SeasonTask] = []


class SeasonEventStateIn(_Shape):
    state: EventStateLit
    observed_on: Optional[date] = None


class SeasonAlert(_Shape):
    alert_key: str
    event_key: str
    title: str
    body: str
    fire_at: datetime
    built_from_forecast_at: datetime


class SeasonalPlanOut(_Shape):
    property_id: int
    generated_at: datetime
    season_label: str
    forecast: Optional[ForecastOut] = None
    events: list[SeasonEvent] = []
    alerts: list[SeasonAlert] = []
    notes: list[str] = []


class VitalCard(_Shape):
    key: VitalKeyLit
    title: str
    value_text: str
    detail: str
    tone: VitalToneLit
    explained: Optional[Explained] = None
    link: Optional[ScreenLit] = None


class ThisWeekItem(_Shape):
    event_key: Optional[str] = None
    task: SeasonTask


class SpaceOut(_Shape):
    growing_area_id: int
    name: str
    kind: SpaceKindLit
    vegetation_type: Optional[VegetationTypeLit] = None
    indoor: bool
    plant_count: int = 0


class VitalsOut(_Shape):
    generated_at: datetime
    headline: str
    property: Optional[PropertyOut] = None
    forecast: Optional[ForecastOut] = None
    cards: list[VitalCard] = []
    this_week: list[ThisWeekItem] = []
    season_ahead: list[SeasonEventSummary] = []
    spaces: list[SpaceOut] = []
    notes: list[str] = []
    #: Whether this server can add a property (SITE_PROFILE_ENABLED), so
    #: Home offers "Add your land" only where it leads somewhere.
    can_add_land: bool = False
