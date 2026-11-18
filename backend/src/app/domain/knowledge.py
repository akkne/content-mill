from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

AVATAR_DESCRIPTION = "Описание аватара.md"
AVATAR_FOLDERS = {
    "Лицо крупным планом": "photos",
    "В полный рост": "photos",
    "Дополнительные ракурсы": "photos",
    "Одежда": "wardrobe",
}


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
    folder_role: str | None = None
    description: str | None = None
    elevenlabs_voice_id: str | None = None
    linked_voice_id: UUID | None = None


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
