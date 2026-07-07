FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Hosted DB lives on the mounted volume (see fly.toml); local runs keep the
# cwd-relative default from app/db/database.py
ENV DATABASE_URL=sqlite:////data/garden_gnome.db

EXPOSE 8080

# Seed is idempotent — safe on every boot, and it keeps the species catalog
# current with the code that shipped in this image.
CMD ["sh", "-c", "python -m app.data.seed && uvicorn app.main:app --host 0.0.0.0 --port 8080"]
