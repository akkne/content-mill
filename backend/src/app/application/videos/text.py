import base64
import json
from dataclasses import asdict
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.application.agents.files import AgentFiles
from app.application.agents.ports import AgentScope
from app.application.scripts.jobs import ScriptModel
from app.application.videos.spoken_script import ScriptScene, format_script
from app.application.videos.style_guide import GuideReader, attach_style_guide
from app.domain.project import ProjectContext
from app.domain.video import (
    SHORT_SHOT_DIRECTION,
    VideoSource,
    VideoTextUnavailable,
    editing_direction,
    scene_count,
)

VideoText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=6000)
]


class VideoCopy(BaseModel):
    script: VideoText
    caption: VideoText
    edit_plan: list[VideoText] = Field(min_length=1)


class CastVideoCopy(BaseModel):
    scenes: list[ScriptScene] = Field(min_length=1, max_length=15)
    caption: VideoText
    edit_plan: list[VideoText] = Field(min_length=1)


class VideoTextGenerator:
    def __init__(
        self,
        model: ScriptModel | None,
        files: AgentFiles,
        style_guide: GuideReader | None = None,
    ):
        self.style_guide = style_guide
        self.model = model
        self.files = files

    def prepare(
        self,
        scope: AgentScope,
        title: str,
        settings: dict,
        context: ProjectContext,
        sources: list[VideoSource],
    ) -> tuple[str, str, list[str]]:
        if self.model is None:
            raise VideoTextUnavailable("Модель для подготовки текста недоступна.")
        try:
            # The legacy narrator setting applies only to videos without a cast.
            # Describe cast voices by name and keep technical IDs out of the copy.
            script_settings = dict(settings)
            cast = settings.get("characters") or []
            if cast:
                script_settings.pop("voice", None)
                script_settings["characters"] = [
                    {
                        "display_name": person["display_name"],
                        "voice": (person.get("voice") or {}).get("name"),
                        "speech_speed": (person.get("voice") or {}).get("speed"),
                        "expressiveness": (person.get("voice") or {}).get("style"),
                        "visual_references": [
                            ref
                            for ref in person.get("files", [])
                            if ref.get("role")
                            in {
                                "face_reference",
                                "angle_reference",
                                "full_body_reference",
                                "outfit_reference",
                            }
                        ],
                    }
                    for person in cast
                ]
            script_settings.pop("sources", None)
            avatar_attachments = {
                ref["version_id"]
                for person in cast
                for ref in person.get("files", [])
                if ref.get("role") == "attachment"
            }
            materials, images = [], []
            for source in sources:
                if str(source.id) in avatar_attachments and source.format.startswith(
                    "audio/"
                ):
                    continue
                item = asdict(source)
                if source.format in {"markdown", "plain"}:
                    item.update(self.files.read(scope, source.id, 0, 20000))
                elif source.format.startswith(("image/", "video/")):
                    preview = self.files.preview(scope, source.id)
                    images.append(base64.b64encode(preview).decode())
                    item["preview"] = len(images)
                materials.append(item)
            data = {
                "title": title,
                "settings": script_settings,
                "editing_direction": editing_direction(settings),
                "scene_count": scene_count(settings),
                "context": asdict(context),
                "materials": materials,
            }
            if settings.get("short_shots"):
                count = data["scene_count"]
                total_ms = settings["duration"] * 1000
                data["suggested_scene_durations_ms"] = [
                    total_ms * (i + 1) // count - total_ms * i // count
                    for i in range(count)
                ]
            attach_style_guide(
                self.style_guide,
                scope.project_id,
                settings.get("motion_template") or settings.get("editing_style", ""),
                data,
                images,
            )
            schema = CastVideoCopy if cast or settings.get("short_shots") else VideoCopy
            data["output_schema"] = schema.model_json_schema()
            result = self.model.generate(
                "Подготовь сценарий короткого ролика, подпись к публикации и монтажный лист "
                "по сценам с таймкодами, кадрами, склейками и титрами на языке settings.language. "
                "Сценарий содержит интервалы сцен, говорящих, режим реплики и дословную речь. "
                "Вынеси указания по картинке в edit_plan. Исключи из текста ID, настройки сервисов и указания о записи голоса. "
                "Голос каждого говорящего уже выбран в settings.characters. Оценивай длительность реплики по speech_speed его карточки и учитывай expressiveness, в том числе при работе со старыми промптами проекта. "
                "Сохраняй мысль, оговорки и мотивацию автора из settings.brief. "
                "Если автор сравнивает варианты, свяжи его выбор с причиной в одной разговорной фразе. "
                "Не превращай личную оценку в статистический факт или гарантию. "
                "При нехватке времени сокращай вводные, сохраняя объяснение. "
                "У каждой вставки в edit_plan укажи точные слова реплики и то, что зритель должен увидеть. "
                "Не выдумывай для вставок посторонние товары, кейсы, суммы или графики роста. "
                "Следуй editing_direction при выборе темпа, крупности и склеек. "
                "Напиши ровно scene_count непрерывных планов для десятисекундных исходников HeyGen. Для каждой сцены задай таймкод начала и конца в готовом ролике. Монтаж берёт с начала исходника ровно эту длительность. "
                "Уложи историю и реплики в итоговую длительность settings.duration. Для каждого "
                "плана опиши положение предметов, персонажей, одежду и склейку. Для каждой "
                "реплики дай точный текст, говорящего и пометку «в кадре» или «за кадром». "
                "Имена из брифа и обозначения «Персонаж 1» соответствуют записям settings.characters. "
                "Сохраняй точные имена говорящих. Если состав не задан, обозначь рассказчика его ролью. Для немого персонажа не пиши реплик. "
                "Связывай фото и одежду с владельцем по ID версии, учитывай выбранные файлы. "
                "Если задан product_photo_id, запланируй показ оригинала на 1–6 секунд во время конкретной реплики о товаре. "
                "Не выдумывай характеристики, цены и обещания, которых нет в брифе и материалах. "
                "Выбранные пользователем материалы — первоочередные творческие источники. "
                "Если задан состав, реплики могут принадлежать только персонажам с голосом. "
                "Верни только JSON "
                "по output_schema. Если заданы scenes, сумма duration_ms равна длительности ролика в мс. Объединяй последовательные фразы одного говорящего в одну реплику, пока не меняется план или говорящий."
                + (" " + SHORT_SHOT_DIRECTION if settings.get("short_shots") else ""),
                json.dumps(data, ensure_ascii=False, default=str),
                images,
            )
            copy = schema.model_validate_json(
                result.strip().removeprefix("```json").removesuffix("```").strip()
            )
            if isinstance(copy, CastVideoCopy):
                if (
                    len(copy.scenes) != data["scene_count"]
                    or (
                        settings.get("short_shots")
                        and any(
                            not 3000 <= scene.duration_ms <= 4000
                            for scene in copy.scenes
                        )
                    )
                    or sum(scene.duration_ms for scene in copy.scenes)
                    != settings["duration"] * 1000
                ):
                    raise ValueError("Script timing differs from the brief")
                speakers = {p["display_name"] for p in cast if p.get("voice")}
                if cast and any(
                    line.speaker not in speakers
                    for scene in copy.scenes
                    for line in scene.lines
                ):
                    raise ValueError("Script assigns speech to an unvoiced character")
                script = format_script(copy.scenes, settings["language"])
                if len(script) > 6000:
                    raise ValueError("Script exceeds the editable length")
            else:
                script = copy.script
        except Exception as error:
            raise VideoTextUnavailable(
                "Не удалось подготовить текст ролика. Повторите запуск позже."
            ) from error
        return script, copy.caption, copy.edit_plan
