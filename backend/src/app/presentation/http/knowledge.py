from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.application.knowledge_service import KnowledgeService
from app.container import knowledge_service
from app.domain.auth import User
from app.domain.knowledge import InvalidNodeOperation, NodeConflict, NodeNotFound
from app.domain.project import ProjectNotFound, RevisionConflict
from app.presentation.http.auth import current_user
from app.presentation.http.projects import expected_revision

router = APIRouter(prefix="/api/v1/projects/{project_id}/nodes")
Service = Annotated[KnowledgeService, Depends(knowledge_service)]
CurrentUser = Annotated[User, Depends(current_user)]


class NodeInput(BaseModel):
    parent_id: UUID | None = None
    name: str = Field(min_length=1, max_length=160)
    kind: Literal["folder", "document"]

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        name = value.strip()
        if not name or name in (".", "..") or "/" in name or "\\" in name:
            raise ValueError("Некорректное имя")
        return name


class RenameInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return NodeInput.clean_name(value)


class MoveInput(BaseModel):
    new_parent_id: UUID | None = None


def translate(error: Exception) -> HTTPException:
    if isinstance(error, (ProjectNotFound, NodeNotFound)):
        return HTTPException(status_code=404, detail="Ресурс не найден")
    if isinstance(error, RevisionConflict):
        return HTTPException(status_code=409, detail="Версия узла изменилась")
    if isinstance(error, NodeConflict):
        return HTTPException(status_code=409, detail="Имя уже занято в этой папке")
    return HTTPException(status_code=422, detail=str(error))


@router.get("")
def list_nodes(
    project_id: UUID, user: CurrentUser, service: Service, parent_id: UUID | None = None
) -> dict:
    try:
        nodes = service.list_nodes(project_id, user.id)
        if parent_id is not None and not any(
            n.id == parent_id and n.kind == "folder" for n in nodes
        ):
            raise NodeNotFound
    except (ProjectNotFound, NodeNotFound) as error:
        raise translate(error) from error
    return {
        "items": [n for n in nodes if n.parent_id == parent_id],
        "next_cursor": None,
    }


@router.get("/tree")
def tree(project_id: UUID, user: CurrentUser, service: Service) -> dict:
    try:
        nodes = service.list_nodes(project_id, user.id)
    except ProjectNotFound as error:
        raise translate(error) from error
    return {"items": nodes}


@router.post("", status_code=201)
def create_node(
    project_id: UUID, payload: NodeInput, user: CurrentUser, service: Service
):
    try:
        return service.create_node(
            project_id, user.id, payload.parent_id, payload.kind, payload.name
        )
    except (ProjectNotFound, InvalidNodeOperation, NodeConflict) as error:
        raise translate(error) from error


@router.get("/{node_id}")
def get_node(project_id: UUID, node_id: UUID, user: CurrentUser, service: Service):
    try:
        return service.get_node(project_id, user.id, node_id)
    except (ProjectNotFound, NodeNotFound) as error:
        raise translate(error) from error


@router.patch("/{node_id}")
def rename_node(
    project_id: UUID,
    node_id: UUID,
    payload: RenameInput,
    user: CurrentUser,
    service: Service,
    if_match: str | None = Header(default=None),
):
    try:
        return service.change_node(
            project_id, user.id, node_id, expected_revision(if_match), name=payload.name
        )
    except (ProjectNotFound, NodeNotFound, NodeConflict, RevisionConflict) as error:
        raise translate(error) from error


@router.post("/{node_id}/move")
def move_node(
    project_id: UUID,
    node_id: UUID,
    payload: MoveInput,
    user: CurrentUser,
    service: Service,
    if_match: str | None = Header(default=None),
):
    try:
        return service.change_node(
            project_id,
            user.id,
            node_id,
            expected_revision(if_match),
            parent_id=payload.new_parent_id,
            move=True,
        )
    except (
        ProjectNotFound,
        NodeNotFound,
        NodeConflict,
        RevisionConflict,
        InvalidNodeOperation,
    ) as error:
        raise translate(error) from error


@router.delete("/{node_id}", status_code=204)
def archive_node(
    project_id: UUID,
    node_id: UUID,
    user: CurrentUser,
    service: Service,
    if_match: str | None = Header(default=None),
) -> None:
    try:
        service.archive_node(project_id, user.id, node_id, expected_revision(if_match))
    except (ProjectNotFound, NodeNotFound, RevisionConflict) as error:
        raise translate(error) from error
