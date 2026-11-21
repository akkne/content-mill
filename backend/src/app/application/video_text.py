import json
from dataclasses import asdict
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.application.script_jobs import ScriptModel
from app.domain.project import ProjectContext
from app.domain.video import VideoSource, VideoTextUnavailable

VideoText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=6000)
]


class VideoCopy(BaseModel):
    script: VideoText
    caption: VideoText
    edit_plan: list[VideoText] = Field(min_length=1)


class VideoTextGenerator:
    def __init__(self, model: ScriptModel | None):
        self.model = model

    def prepare(
        self,
        title: str,
        settings: dict,
        context: ProjectContext,
        sources: list[VideoSource],
    ) -> tuple[str, str, list[str]]:
        if self.model is None:
            raise VideoTextUnavailable("Модель для подготовки текста недоступна.")
        data = {
            "title": title,
            "settings": settings,
            "context": asdict(context),
            "materials": [asdict(source) for source in sources],
        }
        try:
            result = self.model.generate(
                "Подготовь сценарий короткого ролика, подпись к публикации и монтажный лист "
                "по сценам с таймкодами, кадрами, склейками и титрами на языке settings.language. "
                "Учитывай длительность и материалы проекта. Верни только JSON "
                "с полями script и caption (строки до 6000 символов) и edit_plan (список строк).",
                json.dumps(data, ensure_ascii=False, default=str),
                [],
            )
            copy = VideoCopy.model_validate_json(
                result.strip().removeprefix("```json").removesuffix("```").strip()
            )
        except Exception as error:
            raise VideoTextUnavailable(
                "Не удалось подготовить текст ролика. Повторите запуск позже."
            ) from error
        return copy.script, copy.caption, copy.edit_plan
