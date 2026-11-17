from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(String(254), unique=True)
    display_name: Mapped[str] = mapped_column(Text)
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RefreshSessionModel(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (Index("auth_sessions_family_idx", "family_id"),)

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    family_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    refresh_hash: Mapped[str] = mapped_column(Text, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AccessTokenModel(Base):
    __tablename__ = "access_tokens"

    token_hash: Mapped[str] = mapped_column(Text, primary_key=True)
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("auth_sessions.id")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LoginAttemptModel(Base):
    __tablename__ = "login_attempts"
    __table_args__ = (Index("login_attempts_key_idx", "attempt_key", "attempted_at"),)

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    attempt_key: Mapped[str] = mapped_column(Text)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProjectModel(Base):
    __tablename__ = "projects"
    __table_args__ = (
        Index("projects_owner_created_idx", "owner_id", "created_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id")
    )
    name: Mapped[str] = mapped_column(String(160))
    revision: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProjectContextModel(Base):
    __tablename__ = "project_contexts"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), primary_key=True
    )
    revision: Mapped[int] = mapped_column(default=1)
    description: Mapped[str] = mapped_column(Text, default="")
    audiences: Mapped[list] = mapped_column(JSONB, default=list)
    products: Mapped[list] = mapped_column(JSONB, default=list)
    facts: Mapped[list] = mapped_column(JSONB, default=list)
    tone_of_voice: Mapped[str] = mapped_column(Text, default="")
    forbidden_terms: Mapped[list] = mapped_column(JSONB, default=list)
    source_version_ids: Mapped[list] = mapped_column(JSONB, default=list)
