"""Per-IP rate limiting for the auth surface (Phase 9 hardening).

Lives in its own module so routers can import the limiter without a circular
import through app.main. Only decorated routes are limited — the rest of the
API is unaffected.

Limits are configurable via env (useful for load tests); the test suite
disables the limiter globally and re-enables it only inside the dedicated
429 test.
"""
import os

from slowapi import Limiter
from slowapi.util import get_remote_address

# Sign-in endpoints are the brute-force surface: strictest budget.
SIGNIN_LIMIT = os.getenv("RATE_LIMIT_SIGNIN", "10/minute")
# Token maintenance is routine (every ~30 min per device): looser budget.
TOKEN_LIMIT = os.getenv("RATE_LIMIT_TOKEN", "30/minute")

limiter = Limiter(key_func=get_remote_address)
