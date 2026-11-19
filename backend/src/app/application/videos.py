from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4

from app.application.project_ports import ProjectUnitOfWorkFactory
from app.domain.project import ProjectContext, ProjectNotFound
from app.domain.video import (
    MOCK_SECONDS,
    InvalidVideo,
    Video,
    VideoNotFound,
    VideoSource,
)

OPTIONS = {
    "method": [
        "Проблема → решение",
        "Доказательство",
        "Обучение",
        "Мнение",
        "История",
        "Оффер",
    ],
    "platform": ["Instagram Reels", "YouTube Shorts", "VK Клипы", "Telegram", "TikTok"],
    "duration": [15, 30, 45, 60],
    "voice": ["Спокойный", "Энергичный", "Без озвучки"],
    "language": ["Русский", "English"],
}


class VideoGenerator(Protocol):
    def prepare(
        self,
        title: str,
        settings: dict,
        context: ProjectContext,
        sources: list[VideoSource],
    ) -> tuple[str, str, list[str]]: ...


class VideoService:
    def __init__(self, work: ProjectUnitOfWorkFactory, generator: VideoGenerator):
        self.work = work
        self.generator = generator

    def create(
        self,
        owner: UUID,
        project: UUID,
        title: str,
        settings: dict,
        sources: list[UUID],
        assemble: bool,
    ) -> Video:
        with self.work() as work:
            if not work.repository.get_owned(project, owner):
                raise ProjectNotFound
            context = work.repository.context(project)
            if any(
                settings.get(key) not in choices for key, choices in OPTIONS.items()
            ):
                raise InvalidVideo("Проверьте параметры ролика")
            if settings["product"] and settings["product"] not in {
                p.name for p in context.products
            }:
                raise InvalidVideo("Выберите товар из текущего проекта")
            materials = work.videos.sources(project, sources)
            if {item.id for item in materials} != set(sources):
                raise InvalidVideo("Один из источников недоступен в проекте")
            settings = {
                **settings,
                "sources": [
                    {
                        "id": str(s.id),
                        "name": s.name,
                        "version": s.version,
                        "node_id": str(s.node_id),
                        "format": s.format,
                    }
                    for s in materials
                ],
            }
            script, caption, journal = self.generator.prepare(
                title, settings, context, materials
            )
            video = Video(
                uuid4(),
                project,
                title,
                "generating" if assemble else "draft",
                settings,
                script,
                caption,
                journal,
                datetime.now(UTC),
            )
            if assemble:
                video.ready_at = video.created_at + timedelta(seconds=MOCK_SECONDS)
            work.videos.save(video)
            work.commit()
            return video

    def workspace(self, owner: UUID, project: UUID, status: str, query: str):
        with self.work() as work:
            current = work.repository.get_owned(project, owner)
            if not current:
                raise ProjectNotFound
            work.videos.finish_due(project)
            items = work.videos.list_videos(project, status, query)
            work.commit()
            return {"project": current.name, "items": items}

    def options(self, owner: UUID, project: UUID):
        with self.work() as work:
            current = work.repository.get_owned(project, owner)
            if not current:
                raise ProjectNotFound
            context = work.repository.context(project)
            return {
                "project": current.name,
                "options": OPTIONS,
                "products": [p.name for p in context.products],
                "sources": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "version": s.version,
                        "selected": s.id in context.source_version_ids,
                    }
                    for s in work.videos.sources(project)
                ],
            }

    def detail(
        self,
        owner: UUID,
        project: UUID,
        video_id: UUID,
        action: str = "view",
        value: str = "",
    ) -> Video:
        with self.work() as work:
            if not work.repository.get_owned(project, owner):
                raise ProjectNotFound
            work.videos.finish_due(project)
            video = work.videos.get(project, video_id, lock=action != "view")
            if not video:
                raise VideoNotFound
            if action == "view":
                work.commit()
                return video
            if action == "delete":
                work.videos.delete(video)
            else:
                if action == "script":
                    video.script = value
                elif action == "caption":
                    video.caption = value
                elif action == "assemble" and video.status == "draft":
                    video.status = "generating"
                    video.ready_at = datetime.now(UTC) + timedelta(seconds=MOCK_SECONDS)
                elif action == "duplicate":
                    video.ready_at = None
                    video.id = uuid4()
                    video.title = f"{video.title[:170]} · вариант"
                    video.created_at = datetime.now(UTC)
                    video.status = "draft"
                    video.settings.pop("publication", None)
                elif action in ("publish", "schedule") and video.status in (
                    "ready",
                    "planned",
                ):
                    if action == "schedule":
                        try:
                            when = datetime.fromisoformat(value)
                            if when.utcoffset() is None or when <= datetime.now(UTC):
                                raise ValueError
                        except ValueError as error:
                            raise InvalidVideo(
                                "Выберите дату и время в будущем"
                            ) from error
                    video.settings["publication"] = (
                        value if action == "schedule" else datetime.now(UTC).isoformat()
                    )
                    video.status = "planned" if action == "schedule" else "published"
                else:
                    raise InvalidVideo("Действие недоступно для этого ролика")
                work.videos.save(video)
            work.commit()
            return video
