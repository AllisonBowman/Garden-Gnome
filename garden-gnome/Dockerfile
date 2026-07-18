FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
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
