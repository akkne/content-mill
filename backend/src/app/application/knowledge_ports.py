from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Protocol, Self
from uuid import UUID

from app.domain.knowledge import DocumentVersion, KnowledgeNode


class KnowledgeRepository(Protocol):
    def owns_project(self, project_id: UUID, owner_id: UUID) -> bool: ...
    def get(self, project_id: UUID, node_id: UUID) -> KnowledgeNode | None: ...
    def list(self, project_id: UUID) -> list[KnowledgeNode]: ...
    def create(
        self, project_id: UUID, parent_id: UUID | None, kind: str, name: str
    ) -> KnowledgeNode: ...
    def change(
        self, project_id: UUID, node_id: UUID, revision: int, **values: object
    ) -> KnowledgeNode | None: ...
    def archive(
        self, project_id: UUID, node_ids: list[UUID], root_id: UUID, revision: int
    ) -> bool: ...
    def versions(self, node_id: UUID) -> list[DocumentVersion]: ...
    def search(
        self, project_id: UUID, query: str, limit: int
    ) -> list[KnowledgeNode]: ...
    def unindexed_versions(
        self, project_id: UUID
    ) -> list[tuple[KnowledgeNode, DocumentVersion]]: ...
    def add_version(
        self,
        node_id: UUID,
        revision: int,
        version: int,
        format: str,
        size_bytes: int,
        sha256: str,
        storage_key: str,
        search_text: str,
    ) -> DocumentVersion | None: ...


class KnowledgeUnitOfWork(Protocol):
    repository: KnowledgeRepository

    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...
    def commit(self) -> None: ...


KnowledgeUnitOfWorkFactory = Callable[[], AbstractContextManager[KnowledgeUnitOfWork]]


class DocumentStore(Protocol):
    def put(self, key: str, content: bytes, content_type: str) -> None: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...
