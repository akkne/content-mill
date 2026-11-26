from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.voices.catalog import (
    CatalogError,
    VoiceCatalog,
    VoicePage,
)
from app.application.voices.library import VoiceLibrary
from app.application.voices.speech import SpeechResult, SpeechService
from app.container import speech_service, voice_catalog, voice_library
from app.domain.knowledge import InvalidNodeOperation, NodeNotFound
from app.domain.project import ProjectNotFound
from app.domain.voice import VoiceDelivery
from app.presentation.http.dependencies import CurrentUser
from app.presentation.http.errors import translate
from app.presentation.http.schemas.voices import (
    AssignProjects,
    Gender,
    SaveVoice,
    SpeechInput,
    VoiceDetails,
)

router = APIRouter(prefix="/api/v1/voices")
Catalog = Annotated[VoiceCatalog, Depends(voice_catalog)]


Library = Annotated[VoiceLibrary, Depends(voice_library)]


@router.get("")
def library_list(user: CurrentUser, library: Library):
    return library.repository.list_owned(user.id)


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
            VoiceDelivery(payload.voice_speed, payload.voice_style),
        )
    except CatalogError as error:
        raise HTTPException(error.status, str(error)) from error
    except InvalidNodeOperation as error:
        raise translate(error) from error


@router.patch("/{voice_id}/projects")
def assign(
    voice_id: UUID, payload: AssignProjects, user: CurrentUser, library: Library
):
    try:
        return library.assign(user.id, voice_id, payload.add, payload.remove)
    except (ProjectNotFound, NodeNotFound, InvalidNodeOperation) as error:
        raise translate(error) from error


@router.patch("/{voice_id}")
def edit(voice_id: UUID, payload: VoiceDetails, user: CurrentUser, library: Library):
    try:
        return library.repository.edit(
            user.id, voice_id, payload.model_dump(exclude_unset=True)
        )
    except NodeNotFound as error:
        raise translate(error) from error


Speech = Annotated[SpeechService, Depends(speech_service)]


@router.post("/{voice_id}/speech", status_code=202)
def synthesize(
    voice_id: UUID, payload: SpeechInput, user: CurrentUser, service: Speech
):
    try:
        service.create(user.id, voice_id, payload.request_id, payload.text)
        return {"id": payload.request_id}
    except CatalogError as error:
        raise HTTPException(error.status, str(error)) from error


@router.get("/{voice_id}/speech")
def speech_history(voice_id: UUID, user: CurrentUser, service: Speech) -> list[UUID]:
    return service.repository.recent(user.id, voice_id)


@router.get("/{voice_id}/speech/{request_id}")
def speech_result(
    voice_id: UUID, request_id: UUID, user: CurrentUser, service: Speech
) -> SpeechResult:
    try:
        return service.result(user.id, voice_id, request_id)
    except CatalogError as error:
        raise HTTPException(error.status, str(error)) from error
