"""Per-client rate limiting for the auth surface (Phase 9 hardening).

Lives in its own module so routers can import the limiter without a circular
import through app.main. Only decorated routes are limited — the rest of the
API is unaffected.

Limits are configurable via env (useful for load tests); the test suite
disables the limiter globally and re-enables it only inside the dedicated
429 test.
"""
import ipaddress
import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

# Sign-in endpoints are the brute-force surface: strictest budget.
SIGNIN_LIMIT = os.getenv("RATE_LIMIT_SIGNIN", "10/minute")
# Token maintenance is routine (every ~30 min per device): looser budget.
TOKEN_LIMIT = os.getenv("RATE_LIMIT_TOKEN", "30/minute")

#: Set by Fly's edge proxy on every request it forwards: the address the
#: request actually came from. Fly overwrites any value a client sends, and
#: the machine's port is reachable only through that proxy.
FLY_CLIENT_IP = "Fly-Client-IP"


def client_key(request: Request) -> str:
    """Whose budget a request spends: the real client, not the hop before it.

    On Fly the TCP peer of every request is Fly's proxy, so keying on the
    socket address (slowapi's get_remote_address) put every user in one
    bucket: ten sign-ins a minute for the whole service, and a 9 am wave of
    token refreshes answered with 429s that sign people out. Fly-Client-IP
    names the caller; off Fly (local runs, tests) the socket peer is the
    caller, so it is the fallback, as it is for a header that is not an
    address.

    An IPv6 caller is keyed by its /64. A phone or home router is handed a
    whole /64 and can pick any address in it, so per-address keys would let
    one device walk around the limit."""
    raw = request.headers.get(FLY_CLIENT_IP, "").strip()
    if raw:
        try:
            address = ipaddress.ip_address(raw)
        except ValueError:
            return get_remote_address(request)
        if address.version == 6 and address.ipv4_mapped:
            return str(address.ipv4_mapped)
        if address.version == 6:
            return str(ipaddress.ip_network(f"{address}/64", strict=False))
        return str(address)
    return get_remote_address(request)


limiter = Limiter(key_func=client_key)
