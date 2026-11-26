from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from app.application.agents.ports import AgentScope
from app.application.projects.ports import ProjectUnitOfWorkFactory
from app.application.videos.cast import cast_options, resolve_cast
from app.domain.motion import DEFAULT_STYLE, REELS, STYLES
from app.domain.project import ProjectContext, ProjectNotFound
from app.domain.video import (
    EDITING_DIRECTIONS,
    VIDEO_DURATIONS,
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
    "duration": VIDEO_DURATIONS,
    "editing_style": list(EDITING_DIRECTIONS),
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
        *,
        media_error: str = "",
        lipsync_available: bool = False,
    ):
        self.media_error = media_error
        self.work = work
        self.generator = generator
        self.assembly_error = assembly_error
        self.lipsync_available = lipsync_available

    def check_assembly(self, settings):
        error = self.assembly_error or (
            self.media_error if not settings.get("speaker_source_id") else ""
        )
        if error:
            raise VideoTextUnavailable(error)

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
            current = work.repository.get_owned(project, owner)
            if not current:
                raise ProjectNotFound
            if assemble:
                self.check_assembly(settings)
            context = work.repository.context(project)
            settings = {
                "editing_style": current.video_style,
                "duration": current.video_duration,
                **settings,
            }
            if settings.get("reel_format") and settings["reel_format"] not in REELS:
                raise InvalidVideo("Неизвестный формат монтажа рилса")
            outro = settings.get("outro_template")
            if outro and (outro not in STYLES or not settings.get("reel_format")):
                raise InvalidVideo("Проверьте финальную вставку")
            if (
                settings.get("motion_template")
                and settings["motion_template"] not in STYLES
            ):
                raise InvalidVideo("Неизвестный шаблон монтажа")
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
            settings.update(short_shots=True, generated_overlays=True)
            speaker = settings.get("speaker_source_id")
            if speaker:
                if not settings.get("reel_format") or not any(
                    s.id == speaker and s.format in {"video/mp4", "video/webm"}
                    for s in materials
                ):
                    raise InvalidVideo(
                        "Выберите видеозапись спикера из материалов ролика."
                    )
                if settings.get("characters") or settings.get("heygen_lipsync"):
                    raise InvalidVideo(
                        "Для записи спикера используется исходный голос."
                    )
                settings["speaker_source_id"] = str(speaker)
            photo = settings.get("product_photo_id")
            if photo is not None:
                if not any(
                    s.id == photo
                    and s.format in {"image/jpeg", "image/png", "image/webp"}
                    for s in materials
                ):
                    raise InvalidVideo("Выберите фото товара из материалов ролика.")
                settings["product_photo_id"] = str(photo)
            if settings.get("characters"):
                settings["characters"] = resolve_cast(
                    settings["characters"], work.knowledge.list(project), materials
                )
            if settings.get("heygen_lipsync") and (
                not self.lipsync_available
                or not any(
                    person.get("voice") for person in settings.get("characters", [])
                )
            ):
                raise InvalidVideo(
                    "Для HeyGen подключите озвучку и назначьте голос персонажу."
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
            if speaker:
                script, caption, journal = "", title, []
            else:
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
                video.settings["production"] = {
                    "stage": "reel_source"
                    if settings.get("speaker_source_id")
                    else "storyboard"
                }
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
                "motion_default": DEFAULT_STYLE,
                "options": OPTIONS,
                "defaults": {
                    "duration": current.video_duration,
                    "editing_style": current.video_style,
                },
                "lipsync_available": self.lipsync_available,
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
                        "format": s.format,
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
                if (
                    action == "script"
                    and not video.settings.get("speaker_source_id")
                    and (video.status == "draft" or "production" not in video.settings)
                ):
                    if video.script != value:
                        video.journal = []
                    video.script = value
                elif action == "caption":
                    video.caption = value
                elif action == "assemble" and video.status in ("draft", "failed"):
                    self.check_assembly(video.settings)
                    if (
                        video.needs_order_check()
                        and value != "new_order"
                        and video.settings["production"]["stage"]
                        not in {"overlay_design", "overlay_animate"}
                    ):
                        raise InvalidVideo(
                            "Проверьте заказ у провайдера перед новой отправкой."
                        )
                    video.status = "generating"
                    state = video.settings.setdefault(
                        "production",
                        {
                            "stage": "reel_source"
                            if video.settings.get("speaker_source_id")
                            else "storyboard"
                        },
                    )
                    state.pop("error", None)
                    if state.get("motion_export") and state.get("failure", {}).get(
                        "terminal"
                    ):
                        state["retry_motion_export"] = True
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
