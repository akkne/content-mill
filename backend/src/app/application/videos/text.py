import base64
import json
from dataclasses import asdict
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.application.agents.files import AgentFiles
from app.application.agents.ports import AgentScope
from app.application.scripts.jobs import ScriptModel
from app.domain.project import ProjectContext
from app.domain.video import VideoSource, VideoTextUnavailable, scene_count

VideoText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=6000)
]


class VideoCopy(BaseModel):
    script: VideoText
    caption: VideoText
    edit_plan: list[VideoText] = Field(min_length=1)


class VideoTextGenerator:
    def __init__(self, model: ScriptModel | None, files: AgentFiles):
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
            materials, images = [], []
            for source in sources:
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
                "settings": settings,
                "scene_count": scene_count(settings["duration"]),
                "context": asdict(context),
                "materials": materials,
            }
            result = self.model.generate(
                "Подготовь сценарий короткого ролика, подпись к публикации и монтажный лист "
                "по сценам с таймкодами, кадрами, склейками и титрами на языке settings.language. "
                "Напиши ровно scene_count непрерывных планов для восьмисекундных исходников. "
                "Уложи историю и реплики в итоговую длительность settings.duration. Для каждого "
                "плана опиши положение предметов, персонажей, одежду и склейку. Для каждой "
                "реплики дай точный текст, говорящего и пометку «в кадре» или «за кадром». "
                "Имена из брифа и обозначения «Персонаж 1» соответствуют записям settings.characters. "
                "Сохраняй точные имена говорящих. Для немого персонажа не пиши реплик. "
                "Связывай фото и одежду с владельцем по ID версии, учитывай выбранные файлы. "
                "Выбранные пользователем материалы — первоочередные творческие источники. "
                "Если задан состав, реплики могут принадлежать только персонажам с голосом. "
                "Верни только JSON "
                "с полями script и caption (строки до 6000 символов) и edit_plan (список строк).",
                json.dumps(data, ensure_ascii=False, default=str),
                images,
            )
            copy = VideoCopy.model_validate_json(
                result.strip().removeprefix("```json").removesuffix("```").strip()
            )
        except Exception as error:
            raise VideoTextUnavailable(
                "Не удалось подготовить текст ролика. Повторите запуск позже."
            ) from error
        return copy.script, copy.caption, copy.edit_plan
