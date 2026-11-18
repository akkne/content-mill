from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import Session

from app.domain.knowledge import DocumentVersion, KnowledgeNode, MediaUpload
from app.infrastructure.database.models import (
    DocumentVersionModel,
    KnowledgeNodeModel,
    MediaUploadModel,
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
        model.voice_language,
        model.voice_model,
        model.folder_role,
        model.description,
        model.elevenlabs_voice_id,
        model.linked_voice_id,
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
                select(ProjectModel.id)
                .where(ProjectModel.id == project_id, ProjectModel.owner_id == owner_id)
                .with_for_update()
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
        self,
        project_id: UUID,
        parent_id: UUID | None,
        kind: str,
        name: str,
        folder_role: str | None = None,
    ) -> KnowledgeNode:
        model = KnowledgeNodeModel(
            project_id=project_id,
            parent_id=parent_id,
            kind=kind,
            name=name,
            folder_role=folder_role,
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
        self.session.execute(
            update(KnowledgeNodeModel)
            .where(
                KnowledgeNodeModel.project_id == project_id,
                KnowledgeNodeModel.linked_voice_id.in_([root_id, *node_ids]),
            )
            .values(linked_voice_id=None, revision=KnowledgeNodeModel.revision + 1)
        )
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

    def record_upload(self, upload: MediaUpload) -> None:
        self.session.add(MediaUploadModel(**vars(upload)))

    def upload(self, project_id: UUID, upload_id: UUID) -> MediaUpload | None:
        model = self.session.scalar(
            select(MediaUploadModel)
            .where(
                MediaUploadModel.project_id == project_id,
                MediaUploadModel.id == upload_id,
            )
            .with_for_update()
        )
        return (
            MediaUpload(
                **{key: getattr(model, key) for key in MediaUpload.__dataclass_fields__}
            )
            if model
            else None
        )

    def finish_upload(self, upload_id: UUID, node_id: UUID, version: int) -> None:
        self.session.execute(
            update(MediaUploadModel)
            .where(MediaUploadModel.id == upload_id)
            .values(node_id=node_id, completed_version=version)
        )

    def expired_uploads(self, now: datetime) -> list[MediaUpload]:
        rows = self.session.scalars(
            select(MediaUploadModel)
            .where(MediaUploadModel.expires_at < now)
            .order_by(MediaUploadModel.expires_at)
            .limit(100)
            .with_for_update(skip_locked=True)
        ).all()
        uploads = [
            MediaUpload(
                **{key: getattr(row, key) for key in MediaUpload.__dataclass_fields__}
            )
            for row in rows
        ]
        for row in rows:
            self.session.delete(row)
        return uploads

    def _latest_version(self):
        return (
            select(func.max(DocumentVersionModel.version))
            .where(DocumentVersionModel.node_id == KnowledgeNodeModel.id)
            .correlate(KnowledgeNodeModel)
            .scalar_subquery()
        )

    def search(self, project_id: UUID, query: str, limit: int) -> list[KnowledgeNode]:
        models = self.session.scalars(
            select(KnowledgeNodeModel)
            .outerjoin(
                DocumentVersionModel,
                and_(
                    DocumentVersionModel.node_id == KnowledgeNodeModel.id,
                    DocumentVersionModel.version == self._latest_version(),
                ),
            )
            .where(
                KnowledgeNodeModel.project_id == project_id,
                KnowledgeNodeModel.archived_at.is_(None),
                or_(
                    KnowledgeNodeModel.name.icontains(query, autoescape=True),
                    DocumentVersionModel.search_text.icontains(query, autoescape=True),
                ),
            )
            .order_by(KnowledgeNodeModel.name, KnowledgeNodeModel.id)
            .limit(limit)
        ).all()
        return [as_node(model) for model in models]

    def unindexed_versions(
        self, project_id: UUID
    ) -> list[tuple[KnowledgeNode, DocumentVersion]]:
        rows = self.session.execute(
            select(KnowledgeNodeModel, DocumentVersionModel)
            .join(
                DocumentVersionModel,
                and_(
                    DocumentVersionModel.node_id == KnowledgeNodeModel.id,
                    DocumentVersionModel.version == self._latest_version(),
                ),
            )
            .where(
                KnowledgeNodeModel.project_id == project_id,
                KnowledgeNodeModel.archived_at.is_(None),
                DocumentVersionModel.search_text.is_(None),
            )
        ).all()
        return [(as_node(node), as_version(version)) for node, version in rows]

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
    ) -> DocumentVersion | None:
        changed = self.session.scalar(
            update(KnowledgeNodeModel)
            .where(
                KnowledgeNodeModel.id == node_id,
                KnowledgeNodeModel.revision == revision,
                KnowledgeNodeModel.archived_at.is_(None),
                KnowledgeNodeModel.kind.in_(
                    ("document", "image", "audio", "video", "file")
                ),
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
            search_text=search_text,
        )
        self.session.add(model)
        self.session.flush()
        return as_version(model)
