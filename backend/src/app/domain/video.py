from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

MOCK_SECONDS = 12
VIDEO_DURATIONS = [15, 20, 30, 40, 45, 60]
DEFAULT_EDITING_STYLE = "По сценарию"
EDITING_DIRECTIONS = {
    DEFAULT_EDITING_STYLE: "Следуй указаниям брифа и утверждённого сценария.",
    "Динамичный": "Начни с действия, меняй крупность на движении и оставь финальный акцент.",
    "Детали товара": "Чередуй общий план товара, крупный план детали и показ в использовании. Дай зрителю время рассмотреть деталь.",
    "Спокойный обзор": "Веди зрителя последовательно, удерживай общие планы и сохраняй направление движения между сценами.",
}


def editing_direction(settings: dict) -> str:
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
            and state.get("stage") in {"frame", "submit", "sync"}
            and not state.get("operation")
            and failure.get("stage") == state["stage"]
            and failure.get("reason") in {"network", "timeout", "order_unconfirmed"}
        )

    def progress(self) -> int:
        state = self.settings.get("production")
        if state and self.status in ("generating", "failed"):
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
