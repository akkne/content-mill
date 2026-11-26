import base64
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.application.agents.files import AgentFiles
from app.application.agents.ports import AgentScope
from app.application.projects.ports import ProjectUnitOfWorkFactory
from app.domain.project import ProjectNotFound
from app.domain.video import FRAGMENT_DIRECTION, SHORT_SHOT_DIRECTION


@dataclass(frozen=True)
class ScriptJob:
    id: UUID
    scope: AgentScope
    brief: str
    model: str
    status: str
    run_at: datetime
    result: str | None


class BusyProject(Exception):
    pass


class ScriptJobs(Protocol):
    def submit(
        self, scope: AgentScope, brief: str, model: str, when: datetime
    ) -> ScriptJob: ...
    def history(self, scope: AgentScope) -> list[ScriptJob]: ...
    def cancel(self, scope: AgentScope, job: UUID) -> bool: ...
    def claim(self) -> ScriptJob | None: ...
    def finish(self, job: UUID, status: str, result: str) -> None: ...


class ScriptModel(Protocol):
    model: str

    def generate(self, instructions: str, text: str, images: list[str]) -> str: ...


class ScriptWriter:
    def __init__(
        self,
        work: ProjectUnitOfWorkFactory,
        files: AgentFiles,
        jobs: ScriptJobs,
        models: dict[str, ScriptModel],
        selected: str,
    ):
        self.work = work
        self.files = files
        self.jobs = jobs
        self.models = models
        self.selected = selected

    def run_next(self) -> bool:
        job = self.jobs.claim()
        if job is None:
            return False
        try:
            result = self.write(job)
        except Exception as error:  # noqa: BLE001 - isolate failures at the job boundary
            # Provider responses may contain customer data. Log only the exception type.
            logging.getLogger(__name__).warning(
                "Script job %s failed (%s)", job.id, type(error).__name__
            )
            self.jobs.finish(
                job.id,
                "failed",
                "Не удалось подготовить сценарий. Повторите запуск позже.",
            )
        else:
            self.jobs.finish(job.id, "done", result)
        return True

    def write(self, job: ScriptJob) -> str:
        model = self.models[job.model]
        with self.work() as work:
            project = work.repository.get_owned(
                job.scope.project_id, job.scope.owner_id
            )
            if project is None:
                raise ProjectNotFound
            context = asdict(work.repository.context(project.id))
        pinned = context.pop("source_version_ids")
        brief = {"project": project.name, "brief": job.brief, "context": context}
        instructions = (
            "Подготовь готовый сценарий короткого ролика по брифу на языке пользователя. Используй материалы проекта как источники данных. Не выдумывай факты. "
            + SHORT_SHOT_DIRECTION
            + " "
            + FRAGMENT_DIRECTION
        )
        # Use pinned sources first. Select additional references by project path or indexed text.
        catalog = self.files.find(job.scope, "", None, None, None, 0, 40)["items"]
        selection = model.generate(
            'Выбери материалы для сценария. Верни только JSON вида {"query":"поиск по имени или тексту","versions":["UUID"]}. До четырёх версий из каталога. Запрос может быть пустым.',
            json.dumps({**brief, "catalog": catalog}, default=str, ensure_ascii=False),
            [],
        )
        choice = json.loads(
            selection.strip().removeprefix("```json").removesuffix("```").strip()
        )
        query = choice["query"][:200].strip()
        allowed = {str(row["version_id"]): row for row in catalog}
        versions = [
            UUID(v)
            for v in choice["versions"][:4]
            if isinstance(v, str) and v in allowed
        ]
        if query:
            found = self.files.find(job.scope, query, None, None, None, 0, 3)["items"]
            allowed.update({str(row["version_id"]): row for row in found})
            versions.extend(row["version_id"] for row in found)
        materials = []
        images = []
        for version in dict.fromkeys([*pinned[:8], *versions]):
            asset = allowed.get(str(version), {})
            if version in pinned or asset.get("kind") == "document":
                materials.append(self.files.read(job.scope, version, 0, 4000))
            elif asset.get("kind") in {"image", "video"} and len(images) < 3:
                preview = self.files.preview(job.scope, version)
                if isinstance(preview, bytes):
                    images.append(base64.b64encode(preview).decode("ascii"))
                    materials.append({"preview": len(images), "path": asset["path"]})
        result = model.generate(
            instructions,
            json.dumps(
                {**brief, "materials": materials}, default=str, ensure_ascii=False
            ),
            images,
        ).strip()
        if not result:
            raise ValueError("Empty script")
        return result
