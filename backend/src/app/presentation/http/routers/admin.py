from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.application.projects.admin import ClientAdministration, SalesMode
from app.container import client_administration
from app.domain.project import RevisionConflict
from app.presentation.http.dependencies import require_admin

router = APIRouter(prefix="/api/v1/admin", dependencies=[Depends(require_admin)])
Service = Annotated[ClientAdministration, Depends(client_administration)]


class ClientSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    revision: int = Field(ge=1)
    sales_mode: SalesMode
    package_name: str = Field(max_length=160)
    delivery_notes: str = Field(max_length=3000)
    video_style: str = Field(max_length=64)
    video_duration: int


@router.get("/clients")
def clients(
    service: Service,
    q: str = Query("", max_length=160),
    mode: SalesMode | None = None,
    offset: int = Query(0, ge=0, le=2147483647),
    limit: int = Query(20, ge=1, le=100),
):
    return service.list(q.strip(), mode, offset, limit)


@router.put("/clients/{project_id}", status_code=204)
def save(project_id: UUID, data: ClientSettings, service: Service):
    try:
        service.save(project_id, data.revision, data.model_dump(exclude={"revision"}))
    except ValueError as error:
        raise HTTPException(422, detail=str(error)) from error
    except RevisionConflict as error:
        raise HTTPException(
            409, detail="Обновите страницу перед сохранением"
        ) from error
