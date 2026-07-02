from uuid import uuid4

from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "sqlite:///garden_gnome.db"

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

        conn.commit()


def get_session():
    """FastAPI dependency that yields a DB session."""
    with Session(engine) as session:
        yield session
