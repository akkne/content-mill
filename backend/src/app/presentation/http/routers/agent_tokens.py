from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.application.agents.files import AgentFiles
from app.application.agents.ports import AgentScope
from app.container import agent_files
from app.presentation.http.dependencies import CurrentUser

router = APIRouter(prefix="/api/v1/projects/{project_id}/mcp-token")
Service = Annotated[AgentFiles, Depends(agent_files)]


@router.post("", status_code=201)
def issue(
    project_id: UUID, user: CurrentUser, service: Service, response: Response
) -> dict:
    response.headers["Cache-Control"] = "no-store"
    return service.issue(AgentScope(project_id, user.id))


@router.delete("", status_code=204)
def revoke(project_id: UUID, user: CurrentUser, service: Service) -> None:
    service.revoke(AgentScope(project_id, user.id))
