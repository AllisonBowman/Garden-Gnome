"""Typed failures for provider token verification.

The auth router (Phase 5) maps ProviderTokenError subclasses to 401 and
ProviderConfigError to 503 — this package never touches HTTP itself.
"""


class ProviderTokenError(Exception):
    """The presented provider token is invalid for any reason."""


class UnknownKeyId(ProviderTokenError):
    """Token's kid is not in the provider's JWKS, even after a refetch."""


class NonceMismatch(ProviderTokenError):
    """Apple identity token's nonce doesn't match the client's raw nonce."""


class UnverifiedEmail(ProviderTokenError):
    """Google id_token lacks email_verified=true."""


class JWKSUnavailable(ProviderTokenError):
    """Could not fetch the provider's JWKS (network/provider outage)."""


class ProviderConfigError(Exception):
    """Provider credentials (Phase 0) are missing from settings."""
