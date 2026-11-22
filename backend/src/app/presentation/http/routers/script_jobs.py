from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.application.agents.ports import AgentScope
from app.application.scripts.jobs import BusyProject, ScriptJob, ScriptWriter
from app.container import script_writer
from app.presentation.http.dependencies import CurrentUser
from app.presentation.http.schemas.script_jobs import ScriptRequest

router = APIRouter(prefix="/api/v1/projects/{project_id}/scripts")
Service = Annotated[ScriptWriter, Depends(script_writer)]


def present(job: ScriptJob) -> dict:
    return {
        "id": job.id,
        "brief": job.brief,
        "model": job.model,
        "run_at": job.run_at,
        "status": job.status,
        "result": job.result,
    }


@router.get("")
def history(project_id: UUID, user: CurrentUser, service: Service) -> dict:
    jobs = service.jobs.history(AgentScope(project_id, user.id))
    return {
        "enabled": service.selected in service.models,
        "items": [present(job) for job in jobs],
    }


@router.post("", status_code=202)
def submit(
    project_id: UUID, payload: ScriptRequest, user: CurrentUser, service: Service
) -> dict:
    if service.selected not in service.models:
        raise HTTPException(503, "Генерация сценариев пока недоступна.")
    when = payload.run_at or datetime.now(UTC)
    if payload.run_at and when <= datetime.now(UTC):
        raise HTTPException(422, "Выберите время в будущем.")
    try:
        job = service.jobs.submit(
            AgentScope(project_id, user.id), payload.brief, service.selected, when
        )
    except BusyProject as error:
        raise HTTPException(409, "В проекте уже есть активное задание.") from error
    return present(job)


@router.delete("/{job_id}", status_code=204)
def cancel(project_id: UUID, job_id: UUID, user: CurrentUser, service: Service) -> None:
    if not service.jobs.cancel(AgentScope(project_id, user.id), job_id):
        raise HTTPException(409, "Задание недоступно для отмены.")
