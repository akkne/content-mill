from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.application.project_service import ProjectService
from app.container import project_service
from app.domain.auth import User
from app.domain.knowledge import DocumentStorageError
from app.domain.project import (
    Fact,
    InvalidCursor,
    InvalidSourceVersion,
    Product,
    Project,
    ProjectContext,
    ProjectNotFound,
    RevisionConflict,
)
from app.presentation.http.auth import current_user
from app.presentation.http.project_schemas import (
    ContextInput,
    ContextResponse,
    ProjectInput,
    ProjectResponse,
)

router = APIRouter(prefix="/api/v1/projects")
Service = Annotated[ProjectService, Depends(project_service)]
CurrentUser = Annotated[User, Depends(current_user)]


def expected_revision(value: str | None) -> int:
    if value is None:
        raise HTTPException(status_code=428, detail="Требуется заголовок If-Match")
    try:
        revision = int(value.strip('"'))
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Некорректный If-Match") from error
    if revision < 1:
        raise HTTPException(status_code=400, detail="Некорректный If-Match")
    return revision


def project_or_error(
    service: ProjectService, project_id: UUID, owner_id: UUID
) -> Project:
    try:
        return service.get_project(project_id, owner_id)
    except ProjectNotFound as error:
        raise HTTPException(status_code=404, detail="Проект не найден") from error


@router.get("")
def list_projects(
    user: CurrentUser,
    service: Service,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: UUID | None = None,
) -> dict:
    try:
        projects = service.list_projects(user.id, limit, cursor)
    except InvalidCursor as error:
        raise HTTPException(status_code=400, detail="Некорректный курсор") from error
    return {
        "items": [
            ProjectResponse.model_validate(item, from_attributes=True)
            for item in projects[:limit]
        ],
        "next_cursor": str(projects[limit - 1].id) if len(projects) > limit else None,
    }


@router.post("", status_code=201, response_model=ProjectResponse)
def create_project(
    payload: ProjectInput, user: CurrentUser, service: Service
) -> ProjectResponse:
    try:
        project = service.create_project(user.id, payload.name)
    except DocumentStorageError as error:
        raise HTTPException(503, "Хранилище документов недоступно") from error
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID, user: CurrentUser, service: Service
) -> ProjectResponse:
    project = project_or_error(service, project_id, user.id)
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.patch("/{project_id}", response_model=ProjectResponse)
def rename_project(
    project_id: UUID,
    payload: ProjectInput,
    user: CurrentUser,
    service: Service,
    if_match: str | None = Header(default=None),
) -> ProjectResponse:
    try:
        project = service.rename_project(
            project_id, user.id, payload.name, expected_revision(if_match)
        )
    except ProjectNotFound as error:
        raise HTTPException(status_code=404, detail="Проект не найден") from error
    except RevisionConflict as error:
        raise HTTPException(
            status_code=409, detail="Версия проекта изменилась"
        ) from error
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.get("/{project_id}/context", response_model=ContextResponse)
def get_context(
    project_id: UUID, user: CurrentUser, service: Service
) -> ContextResponse:
    try:
        context = service.get_context(project_id, user.id)
    except ProjectNotFound as error:
        raise HTTPException(status_code=404, detail="Проект не найден") from error
    return ContextResponse.model_validate(context, from_attributes=True)


@router.put("/{project_id}/context", response_model=ContextResponse)
def save_context(
    project_id: UUID,
    payload: ContextInput,
    user: CurrentUser,
    service: Service,
    if_match: str | None = Header(default=None),
) -> ContextResponse:
    return persist_context(
        project_id, payload, user, service, expected_revision(if_match)
    )


@router.patch("/{project_id}/context", response_model=ContextResponse)
def patch_context(
    project_id: UUID,
    payload: ContextInput,
    user: CurrentUser,
    service: Service,
    if_match: str | None = Header(default=None),
) -> ContextResponse:
    revision = expected_revision(if_match)
    if not payload.model_fields_set:
        raise HTTPException(status_code=422, detail="Укажите поля контекста")
    return persist_context(
        project_id, payload, user, service, revision, payload.model_fields_set
    )


def persist_context(
    project_id: UUID,
    payload: ContextInput,
    user: User,
    service: ProjectService,
    revision: int,
    fields: set[str] | None = None,
) -> ContextResponse:
    context = ProjectContext(
        project_id=project_id,
        revision=revision,
        description=payload.description,
        audiences=payload.audiences,
        products=[Product(**item.model_dump()) for item in payload.products],
        facts=[Fact(**item.model_dump()) for item in payload.facts],
        tone_of_voice=payload.tone_of_voice,
        forbidden_terms=payload.forbidden_terms,
        source_version_ids=payload.source_version_ids,
    )
    try:
        updated = service.save_context(project_id, user.id, context, revision, fields)
    except ProjectNotFound as error:
        raise HTTPException(status_code=404, detail="Проект не найден") from error
    except RevisionConflict as error:
        raise HTTPException(
            status_code=409, detail="Версия контекста изменилась"
        ) from error
    except InvalidSourceVersion as error:
        raise HTTPException(
            status_code=422, detail="Версия источника не найдена в проекте"
        ) from error
    return ContextResponse.model_validate(updated, from_attributes=True)
