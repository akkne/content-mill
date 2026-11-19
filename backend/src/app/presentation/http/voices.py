from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field, StringConstraints

from app.application.voice_catalog import (
    CatalogError,
    CatalogVoice,
    VoiceCatalog,
    VoicePage,
)
from app.container import voice_catalog
from app.domain.knowledge import InvalidNodeOperation, NodeConflict, NodeNotFound
from app.domain.project import ProjectNotFound
from app.presentation.http.knowledge import CurrentUser, RenameInput, Service, translate

router = APIRouter(prefix="/api/v1/projects/{project_id}/nodes/{folder_id}/voices")
Catalog = Annotated[VoiceCatalog, Depends(voice_catalog)]
Gender = Literal["male", "female"]


def check_folder(
    project_id: UUID, folder_id: UUID, user: CurrentUser, service: Service
):
    try:
        folder = service.get_node(project_id, user.id, folder_id)
        if folder.folder_role != "voices":
            raise InvalidNodeOperation("Откройте папку «Голоса»")
    except (ProjectNotFound, NodeNotFound, InvalidNodeOperation) as error:
        raise translate(error) from error


@router.get("")
def search(
    project_id: UUID,
    folder_id: UUID,
    user: CurrentUser,
    service: Service,
    catalog: Catalog,
    query: str = Query("", max_length=160),
    exact: bool = False,
    language: str = Query("", max_length=80),
    gender: Gender | None = None,
    cursor: str = Query("", max_length=2048),
) -> VoicePage:
    check_folder(project_id, folder_id, user, service)
    try:
        return catalog.search(
            query.strip(), exact, language.strip(), gender or "", cursor
        )
    except CatalogError as error:
        raise HTTPException(error.status, str(error)) from error


class SaveVoice(RenameInput):
    voice_id: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)
    ]
    from_catalog: bool = False
    gender: Gender | None = Field(default=None)


@router.post("", status_code=201)
def save(
    project_id: UUID,
    folder_id: UUID,
    payload: SaveVoice,
    user: CurrentUser,
    service: Service,
    catalog: Catalog,
):
    check_folder(project_id, folder_id, user, service)
    try:
        voice = CatalogVoice(
            payload.voice_id, payload.name, "", [], payload.gender, None
        )
        if payload.from_catalog:
            page = catalog.search(payload.voice_id, True, "", "", "")
            if not page.items:
                raise CatalogError(404, "Голос больше не доступен в каталоге")
            voice = page.items[0]
        return service.add_voice(project_id, user.id, folder_id, payload.name, voice)
    except CatalogError as error:
        raise HTTPException(error.status, str(error)) from error
    except (ProjectNotFound, NodeNotFound, InvalidNodeOperation, NodeConflict) as error:
        raise translate(error) from error
