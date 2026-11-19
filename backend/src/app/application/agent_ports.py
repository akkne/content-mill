from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.knowledge import DocumentVersion


@dataclass(frozen=True)
class AgentScope:
    project_id: UUID
    owner_id: UUID


class AgentRepository(Protocol):
    def replace_token(
        self, scope: AgentScope, digest: str, expires: datetime
    ) -> None: ...
    def revoke(self, scope: AgentScope) -> None: ...
    def resolve(self, digest: str, now: datetime) -> AgentScope | None: ...
    def find(
        self,
        project: UUID,
        query: str,
        kind: str | None,
        folder_id: UUID | None,
        character_id: UUID | None,
        offset: int,
        limit: int,
    ) -> list[dict]: ...
    def asset(
        self, project: UUID, version_id: UUID
    ) -> tuple[str, str, DocumentVersion] | None: ...


class PreviewRenderer(Protocol):
    def render(self, data: bytes, mime: str) -> bytes: ...
