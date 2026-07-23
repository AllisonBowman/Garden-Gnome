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
    nickname: str
    species_id: int = Field(foreign_key="species.id")
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
