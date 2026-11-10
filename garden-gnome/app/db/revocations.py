"""Apple grants still to be revoked after the account that held them is gone.

Account deletion must revoke the Sign in with Apple grant (App Store
5.1.1(v), TN3194), and Apple is sometimes unreachable when someone deletes.
The only thing a revoke needs is the encrypted refresh token Apple handed out
at sign-in, and that used to live only on AuthIdentity, which the deletion
removes in the same transaction. So a failed revoke could never be retried.

A row here is that token, copied off the identity before the identity is
deleted: still Fernet-encrypted, with no user id, email or anything else that
says whose it was. It is removed as soon as Apple accepts the revoke
(app/routers/auth.py, revoke_pending_apple_grants), and kept no longer than
30 days or 10 tries in any case, whichever comes first -- a row past that is
dropped at the next boot or retry pass, with a log line and without the
token. The privacy policy says an encrypted Apple sign-in grant may be kept
up to 30 days after deletion, only to retry the revoke.

Defined here rather than in app/models: it is bookkeeping for one route, not
part of the domain, and nothing reads it but that route and its retry.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


class PendingAppleRevocation(SQLModel, table=True):
    __tablename__ = "pending_apple_revocation"

    id: Optional[int] = Field(default=None, primary_key=True)
    #: The Apple refresh token, encrypted with FERNET_KEY exactly as it was
    #: stored on AuthIdentity. Never decrypted except to send it to Apple.
    token_enc: str
    # Naive UTC, like every timestamp in this schema (models._utc_naive).
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_type=DateTime(timezone=False))
    attempts: int = 0
    last_attempt_at: Optional[datetime] = Field(
        default=None, sa_type=DateTime(timezone=False))
