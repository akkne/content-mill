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


class LibraryVoiceModel(Base):
    __tablename__ = "library_voices"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    elevenlabs_voice_id: Mapped[str | None] = mapped_column(String(160))
    voice_gender: Mapped[str | None] = mapped_column(String(16))
    catalog_languages: Mapped[list[str] | None] = mapped_column(JSONB)
    voice_language: Mapped[str | None] = mapped_column(String(80))
    voice_model: Mapped[str | None] = mapped_column(String(160))
    voice_preview_url: Mapped[str | None] = mapped_column(Text)


class KnowledgeNodeModel(Base):
    __tablename__ = "knowledge_nodes"
    __table_args__ = (
        Index("knowledge_nodes_project_parent_idx", "project_id", "parent_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id")
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("knowledge_nodes.id")
    )
    kind: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(160))
    revision: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    library_voice_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("library_voices.id", name="knowledge_library_voice_fk"), index=True
    )
    folder_role: Mapped[str | None] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text)
    elevenlabs_voice_id: Mapped[str | None] = mapped_column(String(160))
    linked_voice_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("knowledge_nodes.id", name="knowledge_nodes_linked_voice_fk")
    )
    voice_gender: Mapped[str | None] = mapped_column(String(16))
    catalog_languages: Mapped[list[str] | None] = mapped_column(JSONB)
    voice_preview_url: Mapped[str | None] = mapped_column(Text)
    voice_language: Mapped[str | None] = mapped_column(String(80))
    voice_model: Mapped[str | None] = mapped_column(String(160))


class DocumentVersionModel(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        Index("document_versions_node_version_idx", "node_id", "version", unique=True),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    node_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("knowledge_nodes.id")
    )
    version: Mapped[int] = mapped_column()
    format: Mapped[str] = mapped_column(String(16))
    size_bytes: Mapped[int] = mapped_column()
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(Text, unique=True)
    search_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MediaUploadModel(Base):
    __tablename__ = "media_uploads"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    parent_id: Mapped[UUID | None]
    node_id: Mapped[UUID | None]
    revision: Mapped[int | None]
    name: Mapped[str] = mapped_column(String(160))
    mime_type: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int]
    sha256: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_version: Mapped[int | None]
