# Pinned to a Python patch release and a Debian release, which is what
# `3.12-slim` resolved to when this was written. A floating tag could change
# Python or the system SQLite between a green CI run and the deploy; 0017's
# table rename relies on SQLite 3.26+ rewriting foreign keys (trixie ships
# 3.46). Bump it on purpose, alongside a test run.
FROM python:3.12.15-slim-trixie

WORKDIR /app

COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
# Alembic owns the schema — the migration scripts and config must be in the
# image or run_migrations() (startup + seed) can't find alembic.ini.
COPY alembic ./alembic
COPY alembic.ini .

# Hosted DB lives on the mounted volume (see fly.toml); local runs keep the
# cwd-relative default from app/db/database.py
ENV DATABASE_URL=sqlite:////data/garden_gnome.db

EXPOSE 8080

# Seed is idempotent and now migrates via Alembic (not create_all) before
# inserting, so it's safe on every boot and keeps the species catalog current
# with the code in this image. uvicorn's lifespan re-runs migrations (a no-op
# once at head).
CMD ["sh", "-c", "python -m app.data.seed && uvicorn app.main:app --host 0.0.0.0 --port 8080"]
