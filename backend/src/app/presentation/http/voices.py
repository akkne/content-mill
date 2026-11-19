from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, StringConstraints

from app.application.voice_catalog import (
    CatalogError,
    VoiceCatalog,
    VoicePage,
)
from app.application.voice_library import VoiceLibrary
from app.container import voice_catalog, voice_library
from app.domain.knowledge import InvalidNodeOperation, NodeNotFound
from app.domain.project import ProjectNotFound
from app.presentation.http.knowledge import CurrentUser, RenameInput, translate

router = APIRouter(prefix="/api/v1/voices")
Catalog = Annotated[VoiceCatalog, Depends(voice_catalog)]
Gender = Literal["male", "female"]


Library = Annotated[VoiceLibrary, Depends(voice_library)]


@router.get("")
def library_list(user: CurrentUser, library: Library):
    return library.repository.list(user.id)


@router.get("/catalog")
def search(
    user: CurrentUser,
    catalog: Catalog,
    query: str = Query("", max_length=160),
    exact: bool = False,
    language: str = Query("", max_length=80),
    gender: Gender | None = None,
    cursor: str = Query("", max_length=2048),
) -> VoicePage:
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

    description: str = Field(default="", max_length=4000)
    language: str = Field(default="", max_length=80)
    model: str | None = Field(default=None, max_length=160)


@router.post("", status_code=201)
def save(payload: SaveVoice, user: CurrentUser, library: Library):
    try:
        return library.create(
            user.id,
            payload.name,
            payload.voice_id,
            payload.from_catalog,
            payload.description,
            payload.language,
            payload.gender,
            payload.model,
        )
    except CatalogError as error:
        raise HTTPException(error.status, str(error)) from error
    except InvalidNodeOperation as error:
        raise translate(error) from error


class AssignProjects(BaseModel):
    add: set[UUID] = Field(default_factory=set)
    remove: set[UUID] = Field(default_factory=set)


@router.patch("/{voice_id}/projects")
def assign(
    voice_id: UUID, payload: AssignProjects, user: CurrentUser, library: Library
):
    try:
        return library.assign(user.id, voice_id, payload.add, payload.remove)
    except (ProjectNotFound, NodeNotFound, InvalidNodeOperation) as error:
        raise translate(error) from error


class VoiceDetails(BaseModel):
    description: str = Field(max_length=4000)
    voice_language: str = Field(max_length=80)
    voice_gender: Gender | None
    voice_model: str = Field(max_length=160)
    elevenlabs_voice_id: str | None = Field(max_length=160)


@router.patch("/{voice_id}")
def edit(voice_id: UUID, payload: VoiceDetails, user: CurrentUser, library: Library):
    try:
        return library.repository.edit(user.id, voice_id, payload.model_dump())
    except NodeNotFound as error:
        raise translate(error) from error
