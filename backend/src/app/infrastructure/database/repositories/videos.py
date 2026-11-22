from copy import deepcopy
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.domain.video import Video, VideoSource
from app.infrastructure.database.models import (
    AvatarWorkspaceModel,
    DocumentVersionModel,
    KnowledgeNodeModel,
    ProjectModel,
    VideoModel,
)


def as_video(row: VideoModel) -> Video:
    return Video(
        row.id,
        row.project_id,
        row.title,
        row.status,
        deepcopy(row.settings),
        row.script,
        row.caption,
        row.journal,
        row.created_at,
        row.ready_at,
    )


class VideoRepository:
    def __init__(self, session: Session):
        self.session = session

    def avatar_library(self, project: UUID) -> UUID | None:
        return self.session.scalar(
            select(AvatarWorkspaceModel.project_id)
            .join(ProjectModel, ProjectModel.owner_id == AvatarWorkspaceModel.owner_id)
            .where(ProjectModel.id == project)
        )

    def voices(self, project: UUID) -> dict[str, str]:
        rows = self.session.execute(
            select(KnowledgeNodeModel.library_voice_id, KnowledgeNodeModel.name)
            .where(
                KnowledgeNodeModel.project_id == project,
                KnowledgeNodeModel.archived_at.is_(None),
                KnowledgeNodeModel.library_voice_id.is_not(None),
                KnowledgeNodeModel.elevenlabs_voice_id.is_not(None),
            )
            .order_by(KnowledgeNodeModel.name)
        )
        return {str(key): name for key, name in rows}

    def finish_due(self, project: UUID) -> None:
        self.session.execute(
            update(VideoModel)
            .where(
                VideoModel.project_id == project,
                VideoModel.status == "generating",
                VideoModel.ready_at <= datetime.now(UTC),
                ~VideoModel.settings.has_key("production"),
            )
            .values(status="ready", ready_at=None)
        )

    def next_production(self, now: datetime) -> Video | None:
        row = self.session.scalar(
            select(VideoModel)
            .where(
                VideoModel.status == "generating",
                VideoModel.settings.has_key("production"),
                VideoModel.ready_at <= now,
            )
            .order_by(VideoModel.ready_at, VideoModel.id)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        return as_video(row) if row else None

    def list_videos(self, project: UUID, status: str, query: str) -> list[Video]:
        stmt = select(VideoModel).where(VideoModel.project_id == project)
        if status != "all":
            stmt = stmt.where(VideoModel.status == status)
        if query:
            stmt = stmt.where(
                func.lower(VideoModel.title).contains(query.lower(), autoescape=True)
            )
        return [
            as_video(row)
            for row in self.session.scalars(
                stmt.order_by(VideoModel.created_at.desc(), VideoModel.id)
            )
        ]

    def get(self, project: UUID, video: UUID, lock: bool) -> Video | None:
        stmt = select(VideoModel).where(
            VideoModel.project_id == project, VideoModel.id == video
        )
        row = self.session.scalar(stmt.with_for_update() if lock else stmt)
        return as_video(row) if row else None

    def save(self, video: Video) -> None:
        self.session.merge(VideoModel(**vars(video)))

    def delete(self, video: Video) -> None:
        self.session.delete(self.session.get(VideoModel, video.id))

    def sources(
        self, project: UUID, ids: list[UUID] | None = None
    ) -> list[VideoSource]:
        node, version = KnowledgeNodeModel, DocumentVersionModel
        columns = [version.id, node.name, version.version, node.id, version.format]
        stmt = (
            select(*columns)
            .join_from(version, node, version.node_id == node.id)
            .where(node.project_id == project, node.archived_at.is_(None))
        )
        if ids is not None:
            stmt = stmt.where(version.id.in_(ids))
        return [
            VideoSource(*row)
            for row in self.session.execute(
                stmt.order_by(node.name, node.id, version.version.desc())
            )
        ]
