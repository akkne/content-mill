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


class NodeNotFound(Exception):
    pass


class InvalidNodeOperation(Exception):
    pass


class NodeConflict(Exception):
    pass
