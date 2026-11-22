from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from app.application.agent_ports import AgentScope
from app.application.project_ports import ProjectUnitOfWorkFactory
from app.application.video_cast import cast_options, resolve_cast
from app.domain.project import ProjectContext, ProjectNotFound
from app.domain.video import (
    InvalidVideo,
    Video,
    VideoNotFound,
    VideoSource,
    VideoTextUnavailable,
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
    "language": ["Русский", "English"],
}


class VideoGenerator(Protocol):
    def prepare(
        self,
        scope: AgentScope,
        title: str,
        settings: dict,
        context: ProjectContext,
        sources: list[VideoSource],
    ) -> tuple[str, str, list[str]]: ...


class VideoService:
    def __init__(
        self,
        work: ProjectUnitOfWorkFactory,
        generator: VideoGenerator,
        assembly_error: str = "",
    ):
        self.work = work
        self.generator = generator
        self.assembly_error = assembly_error

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
            if assemble and self.assembly_error:
                raise VideoTextUnavailable(self.assembly_error)
            context = work.repository.context(project)
            if any(
                settings.get(key) not in choices for key, choices in OPTIONS.items()
            ):
                raise InvalidVideo("Проверьте параметры ролика")
            if settings["product"] and settings["product"] not in {
                p.name for p in context.products
            }:
                raise InvalidVideo("Выберите товар из текущего проекта")
            voice = settings.get("voice")
            if voice and voice != "Без озвучки":
                voices = work.videos.voices(project)
                if voice not in voices:
                    raise InvalidVideo("Выберите голос, назначенный этому проекту.")
                settings["library_voice_id"] = voice
                settings["voice"] = voices[voice]
            materials = work.videos.sources(project, sources)
            if settings.get("characters"):
                settings["characters"] = resolve_cast(
                    settings["characters"], work.knowledge.list(project), materials
                )
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
                AgentScope(project, owner),
                title,
                settings,
                context,
                materials,
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
                video.settings["production"] = {"stage": "storyboard"}
                video.ready_at = video.created_at
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
            nodes = work.knowledge.list(project)
            by_id = {n.id: n for n in nodes}

            def source_labels(node_id):
                parts = []
                character, consent = None, False
                node = by_id.get(node_id)
                parent_id = node.parent_id if node else None
                while node:
                    parts.append(node.name)
                    if node.folder_role == "avatar":
                        character = node.id
                    if node.folder_role == "consent":
                        consent = True
                    node = by_id.get(node.parent_id)
                return {
                    "path": "/".join(reversed(parts)),
                    "character_id": character if not consent else None,
                    "node_id": node_id,
                    "parent_id": parent_id,
                }

            return {
                "project": current.name,
                "options": OPTIONS,
                "voices": work.videos.voices(project),
                **cast_options(nodes),
                "folders": [
                    {"id": n.id, "parent_id": n.parent_id, "name": n.name}
                    for n in nodes
                    if n.kind == "folder"
                ],
                "products": [p.name for p in context.products],
                "sources": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "version": s.version,
                        **source_labels(s.node_id),
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
            if video.status == "generating" and action != "duplicate":
                raise InvalidVideo("Действие недоступно для этого ролика")
            if action == "delete":
                work.videos.delete(video)
            else:
                if action == "script" and (
                    video.status == "draft" or "production" not in video.settings
                ):
                    if video.script != value:
                        video.journal = []
                    video.script = value
                elif action == "caption":
                    video.caption = value
                elif action == "assemble" and video.status in ("draft", "failed"):
                    if self.assembly_error:
                        raise VideoTextUnavailable(self.assembly_error)
                    video.status = "generating"
                    state = video.settings.setdefault(
                        "production", {"stage": "storyboard"}
                    )
                    state.pop("error", None)
                    state.pop("failure", None)
                    video.ready_at = datetime.now(UTC)
                elif action == "duplicate":
                    video.ready_at = None
                    video.id = uuid4()
                    video.title = f"{video.title[:170]} · вариант"
                    video.created_at = datetime.now(UTC)
                    video.status = "draft"
                    video.settings.pop("production", None)
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
