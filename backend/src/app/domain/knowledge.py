from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class KnowledgeNode:
    id: UUID
    project_id: UUID
    parent_id: UUID | None
    kind: str
    name: str
    revision: int
    created_at: datetime
    archived_at: datetime | None
    voice_language: str | None = None
    voice_model: str | None = None


@dataclass(frozen=True)
class DocumentVersion:
    id: UUID
    node_id: UUID
    version: int
    format: str
    size_bytes: int
    sha256: str
    storage_key: str
    created_at: datetime


class NodeNotFound(Exception):
    pass


class InvalidNodeOperation(Exception):
    pass


class NodeConflict(Exception):
    pass


class DocumentStorageError(Exception):
    pass


@dataclass(frozen=True)
class MediaUpload:
    id: UUID
    project_id: UUID
    parent_id: UUID | None
    node_id: UUID | None
    revision: int | None
    name: str
    mime_type: str
    size_bytes: int
    sha256: str
    expires_at: datetime
    completed_version: int | None = None

    @property
    def staging_key(self) -> str:
        return f"uploads/{self.project_id}/{self.id}"


@dataclass(frozen=True)
class ExampleEntry:
    id: str
    parent: str | None
    name: str
    kind: str
    content: bytes = b""
    format: str = ""
