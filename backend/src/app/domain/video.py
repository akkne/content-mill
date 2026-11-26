from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.domain.motion import REELS, STYLES

MOCK_SECONDS = 12
VIDEO_DURATIONS = [15, 20, 30, 40, 45, 60]
DEFAULT_EDITING_STYLE = "По сценарию"
FACTS_STYLE = "История в цифрах"
STORY_STYLE = "История через детали"
EDITING_DIRECTIONS = {
    DEFAULT_EDITING_STYLE: "Следуй указаниям брифа и утверждённого сценария.",
    FACTS_STYLE: (
        "Открой рассказ конкретным фактом из брифа или вопросом, на который отвечает этот факт. "
        "Если выбран ведущий, дай ему произнести завязку и верни его к выводу. "
        "На ключевом числе смени портрет на зрительное объяснение: долю покажи сектором, "
        "промежуток времени — календарём, изменение — сравнением, только когда для этого есть данные. "
        "Выбери один приём на факт и дай зрителю время его прочесть. "
        "Точные числа, даты и подписи выведи средствами субтитров; оставь генерируемый фон без надписей. "
        "Сохрани единицы измерения. Используй исключительно факты и зависимости из брифа и источников. "
        "При отсутствии чисел опирайся на проверяемый факт. Титры разбей на короткие смысловые фразы; "
        "для акцента укажи в emphasis точное число с единицей или одно ключевое выражение из текста титра."
    ),
    STORY_STYLE: (
        "Начни с решения или события, из-за которого зрителю хочется узнать, что было дальше. "
        "Если в ролике есть ведущий, открой его репликой. При первом упоминании места или предмета "
        "покажи именно этот объект. Дай общий план для ориентира, затем деталь, которая объясняет "
        "поворот истории: жест, предмет, реальное действие. Выбирай детали из материалов клиента. "
        "Сохрани голос рассказчика поверх вставки. Строй склейки на смене мысли, выдержи паузу "
        "на важной детали и верни ведущего для развязки, если он выбран. "
        "Титры дели на короткие фразы по дыханию. В emphasis укажи одно точное слово из титра "
        "на смысловом повороте. Для спокойной фразы оставь поле пустым."
    ),
    "Динамичный": "Начни с действия, меняй крупность на движении и оставь финальный акцент.",
    "Детали товара": "Чередуй общий план товара, крупный план детали и показ в использовании. Дай зрителю время рассмотреть деталь.",
    "Спокойный обзор": "Веди зрителя последовательно, удерживай общие планы и сохраняй направление движения между сценами.",
}


def editing_direction(settings: dict) -> str:
    style = STYLES.get(settings.get("motion_template"))
    if reel := REELS.get(settings.get("reel_format")):
        text = reel["ru"]
        direction = text["beats"] + ". " + text["description"]
        if settings.get("generated_overlays"):
            direction += " Построй цельный рассказ ведущего: сильная первая реплика, объяснение, вывод. Сохрани лицо в верхней половине кадра. Оставь нижнюю половину под отдельные прозрачные иллюстрации и титры. Снимай чистую сцену со спикером без встроенного текста и графики."
            if style:
                direction += " Визуальный референс: " + style["ru"]["description"]
            return direction
        if style:
            direction += (
                " Отдельная анимированная вставка: " + style["ru"]["description"]
            )
        if outro := STYLES.get(settings.get("outro_template")):
            direction += " Финальная вставка: " + outro["ru"]["description"]
        return direction
    if style:
        return style["ru"]["description"] + " " + style["ru"]["use"]
    return EDITING_DIRECTIONS[settings.get("editing_style", DEFAULT_EDITING_STYLE)]


def scene_count(duration: int) -> int:
    return (duration + 7) // 8


@dataclass
class Video:
    id: UUID
    project_id: UUID
    title: str
    status: str
    settings: dict
    script: str
    caption: str
    journal: list[str]
    created_at: datetime
    ready_at: datetime | None = None

    def needs_order_check(self) -> bool:
        state = self.settings.get("production", {})
        failure = state.get("failure", {})
        return (
            self.status == "failed"
            and state.get("stage")
            in {"frame", "submit", "sync", "overlay_design", "overlay_animate"}
            and not state.get("operation")
            and failure.get("stage") == state["stage"]
            and failure.get("reason") in {"network", "timeout", "order_unconfirmed"}
        )

    def progress(self) -> int:
        state = self.settings.get("production")
        if state and self.status in ("generating", "failed"):
            if self.settings.get("generated_overlays"):
                stage = state["stage"]
                if stage in ("render", "reel_export"):
                    return 96
                if stage.startswith("reel_motion_"):
                    return 68 + (
                        26 * state.get("overlay_index", 0)
                        + (13 if stage == "reel_motion_render" else 0)
                    ) // max(1, state.get("overlay_count", 1))
                if stage in (
                    "overlay_design",
                    "collect_overlay_design",
                    "overlay_animate",
                    "collect_overlay_animation",
                ):
                    base = 68 if "design" in stage else 81
                    return base + 13 * state.get("overlay_index", 0) // max(
                        1, state.get("overlay_count", 1)
                    )
                if stage in ("edit", "reel_captions", "reel_plan"):
                    return {"edit": 55, "reel_captions": 60, "reel_plan": 65}[stage]
                if stage == "reel_select":
                    return 35
                return 5 + 50 * state.get("index", 0) // scene_count(
                    self.settings["duration"]
                )
            return min(
                95,
                5
                + 85 * state.get("index", 0) // scene_count(self.settings["duration"]),
            )
        if not self.ready_at or self.status != "generating":
            return 100
        remaining = (self.ready_at - datetime.now(UTC)).total_seconds()
        return max(0, min(99, int(100 * (1 - remaining / MOCK_SECONDS))))


@dataclass(frozen=True)
class VideoSource:
    id: UUID
    name: str
    version: int
    node_id: UUID
    format: str


class VideoNotFound(Exception):
    pass


class InvalidVideo(ValueError):
    pass


class VideoTextUnavailable(Exception):
    pass
