from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Project:
    id: UUID
    owner_id: UUID
    name: str
    revision: int
    created_at: datetime
    video_duration: int = 30
    video_style: str = "По сценарию"


@dataclass(frozen=True)
class Product:
    name: str
    description: str


@dataclass(frozen=True)
class Fact:
    text: str
    source_url: str | None


@dataclass(frozen=True)
class ProjectContext:
    project_id: UUID
    revision: int
    description: str
    audiences: list[str]
    products: list[Product]
    facts: list[Fact]
    tone_of_voice: str
    forbidden_terms: list[str]
    source_version_ids: list[UUID]


class ProjectNotFound(Exception):
    pass


class RevisionConflict(Exception):
    pass


class InvalidCursor(Exception):
    pass


class InvalidSourceVersion(Exception):
    pass
