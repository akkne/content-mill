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
