from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domain.knowledge import DocumentVersion, KnowledgeNode
from app.infrastructure.database.models import (
    DocumentVersionModel,
    KnowledgeNodeModel,
    ProjectModel,
)


def as_node(model: KnowledgeNodeModel) -> KnowledgeNode:
    return KnowledgeNode(
        model.id,
        model.project_id,
        model.parent_id,
        model.kind,
        model.name,
        model.revision,
        model.created_at,
        model.archived_at,
    )


def as_version(model: DocumentVersionModel) -> DocumentVersion:
    return DocumentVersion(
        model.id,
        model.node_id,
        model.version,
        model.format,
        model.size_bytes,
        model.sha256,
        model.storage_key,
        model.created_at,
    )


class SqlAlchemyKnowledgeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def owns_project(self, project_id: UUID, owner_id: UUID) -> bool:
        return (
            self.session.scalar(
                select(ProjectModel.id).where(
                    ProjectModel.id == project_id, ProjectModel.owner_id == owner_id
                )
            )
            is not None
        )

    def get(self, project_id: UUID, node_id: UUID) -> KnowledgeNode | None:
        model = self.session.scalar(
            select(KnowledgeNodeModel).where(
                KnowledgeNodeModel.id == node_id,
                KnowledgeNodeModel.project_id == project_id,
                KnowledgeNodeModel.archived_at.is_(None),
            )
        )
        return as_node(model) if model else None

    def list(self, project_id: UUID) -> list[KnowledgeNode]:
        models = self.session.scalars(
            select(KnowledgeNodeModel)
            .where(
                KnowledgeNodeModel.project_id == project_id,
                KnowledgeNodeModel.archived_at.is_(None),
            )
            .order_by(KnowledgeNodeModel.name, KnowledgeNodeModel.id)
        ).all()
        return [as_node(model) for model in models]

    def create(
        self, project_id: UUID, parent_id: UUID | None, kind: str, name: str
    ) -> KnowledgeNode:
        model = KnowledgeNodeModel(
            project_id=project_id, parent_id=parent_id, kind=kind, name=name
        )
        self.session.add(model)
        self.session.flush()
        return as_node(model)

    def change(
        self, project_id: UUID, node_id: UUID, revision: int, **values: object
    ) -> KnowledgeNode | None:
        model = self.session.scalar(
            update(KnowledgeNodeModel)
            .where(
                KnowledgeNodeModel.id == node_id,
                KnowledgeNodeModel.project_id == project_id,
                KnowledgeNodeModel.revision == revision,
                KnowledgeNodeModel.archived_at.is_(None),
            )
            .values(revision=revision + 1, **values)
            .returning(KnowledgeNodeModel)
        )
        return as_node(model) if model else None

    def archive(
        self, project_id: UUID, node_ids: list[UUID], root_id: UUID, revision: int
    ) -> bool:
        changed = self.session.scalar(
            update(KnowledgeNodeModel)
            .where(
                KnowledgeNodeModel.id == root_id,
                KnowledgeNodeModel.project_id == project_id,
                KnowledgeNodeModel.revision == revision,
                KnowledgeNodeModel.archived_at.is_(None),
            )
            .values(revision=revision + 1, archived_at=datetime.now(UTC))
            .returning(KnowledgeNodeModel.id)
        )
        if changed is None:
            return False
        if node_ids:
            self.session.execute(
                update(KnowledgeNodeModel)
                .where(KnowledgeNodeModel.id.in_(node_ids))
                .values(archived_at=datetime.now(UTC))
            )
        return True

    def versions(self, node_id: UUID) -> list[DocumentVersion]:
        models = self.session.scalars(
            select(DocumentVersionModel)
            .where(DocumentVersionModel.node_id == node_id)
            .order_by(DocumentVersionModel.version.desc())
        ).all()
        return [as_version(model) for model in models]

    def add_version(
        self,
        node_id: UUID,
        revision: int,
        version: int,
        format: str,
        size_bytes: int,
        sha256: str,
        storage_key: str,
    ) -> DocumentVersion | None:
        changed = self.session.scalar(
            update(KnowledgeNodeModel)
            .where(
                KnowledgeNodeModel.id == node_id,
                KnowledgeNodeModel.revision == revision,
                KnowledgeNodeModel.archived_at.is_(None),
                KnowledgeNodeModel.kind == "document",
            )
            .values(revision=revision + 1)
            .returning(KnowledgeNodeModel.id)
        )
        if changed is None:
            return None
        model = DocumentVersionModel(
            node_id=node_id,
            version=version,
            format=format,
            size_bytes=size_bytes,
            sha256=sha256,
            storage_key=storage_key,
        )
        self.session.add(model)
        self.session.flush()
        return as_version(model)
