from typing import Literal
from uuid import UUID

from app.application.projects.ports import ProjectUnitOfWorkFactory
from app.domain.project import RevisionConflict
from app.domain.video import EDITING_DIRECTIONS, VIDEO_DURATIONS

SalesMode = Literal["unassigned", "saas", "implementation"]


class ClientAdministration:
    def __init__(self, work: ProjectUnitOfWorkFactory):
        self.work = work

    def list(self, query: str, mode: SalesMode | None, offset: int, limit: int):
        with self.work() as work:
            result = work.repository.list_clients(query, mode, offset, limit)
            return {
                **result,
                "durations": VIDEO_DURATIONS,
                "styles": list(EDITING_DIRECTIONS),
            }

    def save(self, project_id: UUID, revision: int, settings: dict):
        if (
            settings["video_duration"] not in VIDEO_DURATIONS
            or settings["video_style"] not in EDITING_DIRECTIONS
        ):
            raise ValueError("Недопустимые настройки ролика")
        with self.work() as work:
            if not work.repository.update_client(project_id, revision, settings):
                raise RevisionConflict
            work.commit()
