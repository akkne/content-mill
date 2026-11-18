from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    display_name: str
    password_hash: str


@dataclass(frozen=True)
class RefreshSession:
    id: UUID
    user_id: UUID
    family_id: UUID
    expires_at: datetime
    revoked_at: datetime | None
    rotated_at: datetime | None


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    access_expires_at: datetime
    refresh_token: str
    refresh_expires_at: datetime


class EmailAlreadyRegistered(Exception):
    pass


class InvalidCredentials(Exception):
    pass


class InvalidSession(Exception):
    pass


class TooManyAttempts(Exception):
    pass
