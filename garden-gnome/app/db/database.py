import os
from uuid import uuid4

from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine

# Overridable so hosted deployments can point at a persistent volume
# (e.g. sqlite:////data/garden_gnome.db on Fly.io)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///garden_gnome.db")

# check_same_thread=False is needed for SQLite + FastAPI
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """Create all tables that don't yet exist. Safe to call repeatedly."""
    SQLModel.metadata.create_all(engine)


def migrate_db() -> None:
    """Add columns introduced after the initial schema to existing databases.

    SQLModel's create_all() handles brand-new tables; this handles new columns
    on tables that were already created before those columns existed. SQLite
    supports ALTER TABLE ADD COLUMN but not inline UNIQUE constraints, so we
    create the uniqueness index separately."""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(plant)"))
        existing_cols = {row[1] for row in result}

        if "plant_uuid" not in existing_cols:
            # Add column (SQLite requires a default for NOT NULL on existing rows)
            conn.execute(text(
                "ALTER TABLE plant ADD COLUMN plant_uuid TEXT NOT NULL DEFAULT ''"
            ))
            # Backfill each existing row with a real UUID before enforcing uniqueness
            rows = conn.execute(text("SELECT id FROM plant")).fetchall()
            for (plant_id,) in rows:
                conn.execute(
                    text("UPDATE plant SET plant_uuid = :uuid WHERE id = :id"),
                    {"uuid": str(uuid4()), "id": plant_id},
                )
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_plant_plant_uuid ON plant (plant_uuid)"
            ))

        if "environment_id" not in existing_cols:
            conn.execute(text(
                "ALTER TABLE plant ADD COLUMN environment_id INTEGER REFERENCES environment(id)"
            ))

        # Species provenance/review columns (catalog expansion). Pre-existing
        # rows are the hand-written catalog: curated + approved by definition.
        species_cols = {
            row[1] for row in conn.execute(text("PRAGMA table_info(species)"))
        }
        for col, ddl in [
            ("source", "ALTER TABLE species ADD COLUMN source TEXT NOT NULL DEFAULT 'curated'"),
            ("source_ref", "ALTER TABLE species ADD COLUMN source_ref TEXT NOT NULL DEFAULT ''"),
            ("review_status", "ALTER TABLE species ADD COLUMN review_status TEXT NOT NULL DEFAULT 'approved'"),
            ("review_note", "ALTER TABLE species ADD COLUMN review_note TEXT NOT NULL DEFAULT ''"),
        ]:
            if col not in species_cols:
                conn.execute(text(ddl))

        conn.commit()


def get_session():
    """FastAPI dependency that yields a DB session."""
    with Session(engine) as session:
        yield session
