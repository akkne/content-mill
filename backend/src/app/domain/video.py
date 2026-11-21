from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

MOCK_SECONDS = 12


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

    def progress(self) -> int:
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
    excerpt: str = ""


class VideoNotFound(Exception):
    pass


class InvalidVideo(ValueError):
    pass


class VideoTextUnavailable(Exception):
    pass
