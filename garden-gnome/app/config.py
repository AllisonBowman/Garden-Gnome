"""Application settings, loaded once from the environment / .env.

Core token secrets (JWT_SECRET, FERNET_KEY) are required: the app fails fast
at startup if they're missing, rather than issuing unverifiable tokens.
Provider credentials (Apple/Google) stay optional until the Phase 0 console
setup is done — the oauth verifiers raise a clear error if used unconfigured,
so the rest of the API keeps working without them.

Deployment note: the Fly.io app must have JWT_SECRET and FERNET_KEY set via
`fly secrets set` BEFORE deploying this code, or boot will fail on purpose.
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",  # .env also holds advisor/vision/etc. settings
    )

    # --- Token/crypto core (required) ---
    jwt_secret: str
    jwt_alg: str = "HS256"
    access_token_ttl_min: int = 30
    refresh_token_ttl_days: int = 90
    # Encrypts Apple refresh tokens at rest (cryptography.fernet key)
    fernet_key: str

    # --- Sign in with Apple (required from Phase 4 onward) ---
    apple_bundle_id: Optional[str] = None
    apple_team_id: Optional[str] = None
    apple_key_id: Optional[str] = None
    apple_private_key_path: Optional[str] = None

    # --- Google Sign-In (required from Phase 4 onward) ---
    google_client_id: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
