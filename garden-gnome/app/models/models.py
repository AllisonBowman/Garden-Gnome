from datetime import datetime, date
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import JSON, Column, UniqueConstraint
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


class CareOutcome(str, Enum):
    """What a care to-do actually ended in.

    The reminder's verb is *check*, not *do* — so "I looked and it didn't
    need doing" is a first-class result, not a dismissal. A null outcome on
    old rows means the log predates outcomes; the action was done.
    """

    watered = "watered"
    checked_not_needed = "checked_not_needed"
    repotted = "repotted"
    top_dressed = "top_dressed"
    checked_fine = "checked_fine"


# Which outcomes make sense for which action. Actions absent here take no
# outcome at all — a pruning is just a pruning.
OUTCOMES_BY_ACTION: dict[CareType, set[CareOutcome]] = {
    CareType.water: {CareOutcome.watered, CareOutcome.checked_not_needed},
    CareType.repot: {
        CareOutcome.repotted,
        CareOutcome.top_dressed,
        CareOutcome.checked_fine,
    },
}


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
    community_garden = "community_garden"  # plan's "community_plot" maps here
    conservation = "conservation"
    research = "research"
    # Added 2026-07-15 (auth plan decision 1) — per-user growing environments
    balcony = "balcony"
    greenhouse = "greenhouse"
    other = "other"


# --- Environment climate characteristics (weather feature) ---
# These describe how much the outside world reaches a plant, so weather-driven
# advice applies only where it makes sense (an exposed balcony, not a desk).

class Shelter(str, Enum):
    sheltered = "sheltered"      # roofed/indoors — rain and wind don't reach it
    partial = "partial"          # covered balcony/porch — some exposure
    exposed = "exposed"          # open to the sky — full rain and wind


class TempExposure(str, Enum):
    indoor = "indoor"            # climate-controlled; stable ambient temperature
    outdoor = "outdoor"          # experiences the outside air temperature


class SunExposure(str, Enum):
    full_sun = "full_sun"        # 6+ hours of direct sun
    partial_sun = "partial_sun"  # 3–6 hours
    shade = "shade"              # under 3 hours of direct sun


class AuthProvider(str, Enum):
    apple = "apple"
    google = "google"


class WaterRegime(str, Enum):
    """How a species wants its medium managed — the species-level fact.

    This is the unit horticultural authorities actually publish. A day count is
    an estimate over pot, medium and light, which is why it lives beside this
    rather than instead of it (plan 2.1).
    """
    keep_moist = "keep_moist"
    keep_barely_moist = "keep_barely_moist"
    dry_surface_between = "dry_surface_between"
    dry_thoroughly_between = "dry_thoroughly_between"


class HumidityNeed(str, Enum):
    """UGA's bands: below 20% low, 40-50% average, above 50% high.

    A category, not a percentage — sources that publish a per-species number
    disagree by up to 40 points, and no user can act on the difference.
    """
    low = "low"
    average = "average"
    high = "high"


class SoilBase(str, Enum):
    standard_potting = "standard_potting"
    chunky_aroid = "chunky_aroid"
    cactus_succulent = "cactus_succulent"
    ericaceous = "ericaceous"
    orchid_bark = "orchid_bark"
    african_violet = "african_violet"
    semi_hydro = "semi_hydro"
    garden_bed = "garden_bed"


class SoilDrainage(str, Enum):
    fast = "fast"
    moderate = "moderate"
    moisture_retentive = "moisture_retentive"


class FertilizeStrength(str, Enum):
    full = "full"
    half = "half"
    quarter = "quarter"


class CareDataStatus(str, Enum):
    """How well-backed a species' care values are.

    A property of the data, and deliberately not the same thing as
    `ReviewStatus`, which is where a row sits in the operator's workflow. A row
    can be `approved` by validation and still `inferred`.
    """
    sourced = "sourced"      # at least one value cited to this species
    inferred = "inferred"    # has values, but every one is borrowed from genus
    none = "none"            # nothing to say


class OutdoorSunExposure(str, Enum):
    """The outdoor duration scale, kept strictly separate from indoor intensity.

    There is no valid transformation from hours of direct sun to interior light
    level; mapping one onto the other is what made 77% of the imported catalog
    claim `direct`. Stored so it is never mapped inward (plan 2.3).
    """
    full_sun = "full_sun"
    part_sun = "part_sun"
    part_shade = "part_shade"
    full_shade = "full_shade"


class SpeciesSource(str, Enum):
    curated = "curated"            # hand-written original catalog
    perenual = "perenual"          # mapped from the Perenual API
    llm_generated = "llm_generated"  # drafted by /species/generate — heavier review


class ReviewStatus(str, Enum):
    approved = "approved"          # passed automated validation
    needs_review = "needs_review"  # flagged by validation; in the review queue
    verified = "verified"          # manually cross-checked against an authority


class User(SQLModel, table=True):
    """An account holder. Social login only — no password column by design.

    Note: the table is named `user`, a reserved word in Postgres; SQLAlchemy
    quotes identifiers so it works, but consider renaming at the Postgres move.
    """
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    email: Optional[str] = Field(default=None, index=True)
    display_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    # Account deletion is HARD: DELETE /me removes this row and cascades
    # (see auth.delete_me; locked by test_account_deletion). This column is
    # kept as a defensive soft-deactivation guard — get_current_user, sign-in,
    # and the census export already reject/exclude any user whose deleted_at is
    # set — so a future soft-deactivation path would be safe by construction.
    # Nothing sets it today, so it is always None.
    deleted_at: Optional[datetime] = None
    # Census participation is per-user consent, default OFF (privacy decision
    # 2026-07-15). Export/sync include only opted-in users' data.
    census_opt_in: bool = Field(default=False)

    identities: list["AuthIdentity"] = Relationship(
        back_populates="user", cascade_delete=True)
    refresh_tokens: list["RefreshToken"] = Relationship(
        back_populates="user", cascade_delete=True)
    plants: list["Plant"] = Relationship(back_populates="user")
    environments: list["Environment"] = Relationship(back_populates="user")


class AuthIdentity(SQLModel, table=True):
    """One provider login (apple/google) linked to a User.

    A user may hold several identities (Apple + Google) but each provider
    subject maps to exactly one user — unique(provider, provider_sub)."""
    __table_args__ = (UniqueConstraint("provider", "provider_sub"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    provider: AuthProvider
    provider_sub: str
    email_at_signup: Optional[str] = None
    # Apple refresh token (Fernet-encrypted) — needed only to revoke the
    # user's Apple session on account deletion (App Store 5.1.1(v))
    apple_refresh_token_enc: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="identities")


class RefreshToken(SQLModel, table=True):
    """Opaque rotating refresh token, stored as a sha256 hash only.

    family_id groups a rotation chain; if a revoked token is presented again
    (reuse detection), the whole family is revoked — see Phase 3."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    token_hash: str = Field(unique=True)
    family_id: str = Field(default_factory=lambda: str(uuid4()), index=True)
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="refresh_tokens")


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

    # --- Phase 2 care fields (plan 2.1-2.7) ------------------------------
    # Every one is Optional, and that is the point: the tranche fills them
    # sparsely (night_f_max on 3 of 40 researched species) because that is how
    # much the sources actually say. A NOT NULL here would reintroduce exactly
    # the fabrication Phase 1 removed.
    #
    # The legacy columns above (light_need, humidity_pct_*, temp_f_*, soil_type)
    # are deliberately left in place: 1,900 rows carry them and the app reads
    # them today. Retiring them is the catalog-shrink pass, plan 3.4.

    # Light as two independent axes — ambient intensity in footcandles, and
    # direct-beam tolerance. Pothos and Peace Lily share an intensity need and
    # differ on beam hours, and that difference is what scorches leaves.
    light_fc_min: Optional[int] = None
    light_fc_good: Optional[int] = None
    direct_sun_hours_max: Optional[float] = None
    outdoor_sun_exposure: Optional[list[str]] = Field(
        default=None, sa_column=Column(JSON, nullable=True))

    # Water: the regime is the fact, the day counts are an estimate that
    # carries its own assumptions in water_estimate_basis.
    water_regime: Optional[WaterRegime] = None
    water_dry_down_target: Optional[str] = None
    water_check_depth_cm: Optional[float] = None
    water_growing_days_est: Optional[int] = None
    water_dormant_days_est: Optional[int] = None
    water_estimate_basis: Optional[str] = None

    humidity_need: Optional[HumidityNeed] = None

    # Temperature as four separate concepts. One flat band silently instructs
    # the user to prevent flowering in anything needing a cool rest.
    day_f_min: Optional[int] = None
    day_f_max: Optional[int] = None
    night_f_min: Optional[int] = None
    night_f_max: Optional[int] = None
    chill_damage_f: Optional[int] = None
    cool_rest_note: Optional[str] = None

    soil_base: Optional[SoilBase] = None
    soil_drainage: Optional[SoilDrainage] = None
    soil_ph_min: Optional[float] = None
    soil_ph_max: Optional[float] = None

    # Interval without a season is how a reminder ends up firing in December.
    fertilize_active_months: Optional[list[int]] = Field(
        default=None, sa_column=Column(JSON, nullable=True))
    fertilize_interval_days: Optional[int] = None
    fertilize_strength: Optional[FertilizeStrength] = None

    # The sentence a person should read. `toxic_to_pets` stays the raw flag.
    toxicity_detail: Optional[str] = None

    # Derived by the recompute, never typed in. `care_provenance` maps each
    # resolved field to "sourced" or "genus_inferred" -- ADR 0002 requires an
    # inherited value to be labelled wherever it is shown. `resolver_version`
    # makes staleness a query when the rules change.
    care_data_status: Optional[CareDataStatus] = None
    care_provenance: Optional[dict] = Field(
        default=None, sa_column=Column(JSON, nullable=True))
    resolver_version: Optional[str] = None

    # Provenance + review trail for catalog expansion
    source: SpeciesSource = SpeciesSource.curated
    source_ref: str = ""           # e.g. Perenual species id, for traceability
    review_status: ReviewStatus = ReviewStatus.approved
    review_note: str = ""          # citation from manual verification (source + URL)

    plants: list["Plant"] = Relationship(back_populates="species")
    care_schedules: list["CareSchedule"] = Relationship(back_populates="species")
    traits: list["SpeciesTrait"] = Relationship(back_populates="species")

    @property
    def humidity_sourced(self) -> bool:
        """Whether this row's humidity numbers came from a real source.

        The Perenual import had no humidity field; every imported row derives
        its percentages from a watering category and carries a
        `humidity_source` trait saying so (present on all imports, absent on
        all curated rows). Numbers derived that way are not facts, and no
        surface should present them as facts — the advisor omits them, the
        detail screen hides the stat, and the Almanac stops sorting on them.

        Touching `self.traits` lazy-loads when the relation isn't already in
        memory — fine for single-species paths; the list endpoint computes
        this in one query instead (see `list_species`)."""
        return all(t.trait != "humidity_source" for t in self.traits)

    @property
    def toxicity_description(self) -> str:
        """A plain-language toxicity sentence, generated from what we know.

        A property rather than a column: it is derived, so it can improve as the
        nuance table does without a migration, and every endpoint that returns a
        Species picks it up automatically. `toxic_to_pets` stays as the raw flag
        for filtering; this is what a person should actually read."""
        from app.services.toxicity import describe_for_species
        return describe_for_species(
            self.scientific_name, self.common_name, self.toxic_to_pets
        )


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


class Authority(SQLModel, table=True):
    """An organisation whose publications count as evidence.

    Distinct from `SpeciesSource`, which says which pipeline produced a row and
    nothing about whether anyone checked it. Tier drives precedence when claims
    conflict; licence exists so a source that turns out to be unusable can be
    withdrawn by query rather than by archaeology (ADR 0001).
    """
    __table_args__ = (UniqueConstraint("name"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    tier: int = Field(default=2)
    licence: str = ""
    homepage_url: str = ""

    claims: list["Claim"] = Relationship(back_populates="authority")


class Claim(SQLModel, table=True):
    """One field's value for one subject, as asserted by one citation.

    `subject` is a name, not a foreign key: genus-level claims have no species
    row to point at, and evidence may be collected before the species exists in
    the catalog. Resolution matches on the name (see resolve.py).

    `quote` is audit evidence and never leaves the server — ADR 0003.
    """
    __table_args__ = (UniqueConstraint("subject", "field", "citation_url"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    subject: str = Field(index=True)
    field: str = Field(index=True)
    # JSON-encoded so a bool stays a bool and 100 does not come back "100".
    value_json: str
    authority_id: int = Field(foreign_key="authority.id")
    citation_title: str = ""
    citation_url: str = ""
    quote: str = ""
    collected_at: datetime = Field(default_factory=datetime.utcnow)

    authority: Optional[Authority] = Relationship(back_populates="claims")


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
    # Owner (auth plan decision 1). Schema-nullable only because SQLite can't
    # add NOT NULL to existing rows; backfilled to dev@local in 0004 and
    # required at the application layer from Phase 5 onward.
    user_id: Optional[str] = Field(default=None, foreign_key="user.id", index=True)
    city: str = ""
    region: str = ""
    country: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    # Climate characteristics — how much weather reaches plants here.
    shelter: Shelter = Shelter.sheltered
    temp_exposure: TempExposure = TempExposure.indoor
    sun_exposure: SunExposure = SunExposure.partial_sun
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="environments")
    plants: list["Plant"] = Relationship(back_populates="environment")


class Plant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Canonical UUID: never changes, even when the plant is transferred to a
    # new owner or installation. Census aggregators use this to deduplicate.
    plant_uuid: str = Field(default_factory=lambda: str(uuid4()), unique=True)
    nickname: str = ""
    species_id: int = Field(foreign_key="species.id")
    # How many physical plants this row stands for.
    #
    #   quantity == 1  -> an individual. plant_uuid identifies one physical
    #                     plant, and stewardship + census dedup mean exactly
    #                     what they have always meant. Every row that existed
    #                     before this column was added is this case.
    #   quantity  > 1  -> a planting: "twelve tomatoes along the south fence".
    #                     A gardener counts rather than names, and care is
    #                     applied to the group, so care logs and stewardship
    #                     records describe all of them at once.
    #
    # The census must therefore SUM this column rather than count rows; see
    # app/routers/census.py.
    quantity: int = Field(default=1)
    # Set when this row was split off another (see POST /plants/{id}/split).
    # Splitting is the one operation that mints a second plant_uuid for plants
    # that were previously counted under one, so recording the origin is what
    # lets a census aggregator recognise the pair and avoid double-counting.
    split_from_uuid: Optional[str] = Field(default=None, index=True)
    environment_id: Optional[int] = Field(default=None, foreign_key="environment.id")
    # Owner. Schema-nullable only because SQLite can't add a NOT NULL column
    # to existing rows; the migration backfills every plant to the dev user
    # and Phase 6 enforces presence at the application layer. Make it
    # NOT NULL for real at the Postgres move.
    user_id: Optional[str] = Field(default=None, foreign_key="user.id", index=True)

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
    user: Optional[User] = Relationship(back_populates="plants")
    # A plant's history is meaningless without the plant; delete it together
    care_logs: list["CareLog"] = Relationship(back_populates="plant", cascade_delete=True)
    stewardship_records: list["StewardshipRecord"] = Relationship(back_populates="plant", cascade_delete=True)


class CareLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plant_id: int = Field(foreign_key="plant.id")
    action: CareType
    # Null = the log predates outcomes; the action was done. Never backfilled —
    # we don't invent records about what someone found in the soil.
    outcome: Optional[CareOutcome] = None
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
