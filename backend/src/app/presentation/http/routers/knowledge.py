from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query

from app.domain.knowledge import (
    DocumentStorageError,
    InvalidNodeOperation,
    NodeConflict,
    NodeNotFound,
)
from app.domain.project import ProjectNotFound, RevisionConflict
from app.presentation.http.dependencies import (
    CurrentUser,
    KnowledgeServiceDependency,
    expected_revision,
)
from app.presentation.http.errors import translate
from app.presentation.http.schemas.knowledge import (
    ContentResponse,
    DocumentInput,
    MoveInput,
    NodeInput,
    RenameInput,
    VersionResponse,
)

router = APIRouter(prefix="/api/v1/projects/{project_id}/nodes")


@router.get("/{node_id}/versions")
def document_versions(
    project_id: UUID,
    node_id: UUID,
    user: CurrentUser,
    service: KnowledgeServiceDependency,
) -> dict:
    try:
        versions = service.document_versions(project_id, user.id, node_id)
    except (ProjectNotFound, NodeNotFound) as error:
        raise translate(error) from error
    return {"items": [VersionResponse.model_validate(item) for item in versions]}


@router.get("/{node_id}/content", response_model=ContentResponse)
def document_content(
    project_id: UUID,
    node_id: UUID,
    user: CurrentUser,
    service: KnowledgeServiceDependency,
    version: Annotated[int | None, Query(ge=1)] = None,
) -> ContentResponse:
    try:
        node, selected, content = service.document_content(
            project_id, user.id, node_id, version
        )
    except (
        ProjectNotFound,
        NodeNotFound,
        DocumentStorageError,
        InvalidNodeOperation,
    ) as error:
        raise translate(error) from error
    return ContentResponse(
        node_id=node.id,
        revision=node.revision,
        version=selected.version if selected else 0,
        format=selected.format
        if selected
        else ("plain" if node.name.lower().endswith(".txt") else "markdown"),
        content=content,
    )


@router.put("/{node_id}/content", response_model=ContentResponse)
def save_document(
    project_id: UUID,
    node_id: UUID,
    payload: DocumentInput,
    user: CurrentUser,
    service: KnowledgeServiceDependency,
    if_match: str | None = Header(default=None),
) -> ContentResponse:
    if len(payload.content.encode("utf-8")) > 1000000:
        raise HTTPException(status_code=413, detail="Документ слишком большой")
    try:
        node, version = service.save_document(
            project_id,
            user.id,
            node_id,
            expected_revision(if_match),
            payload.content,
            payload.format,
        )
    except (
        ProjectNotFound,
        NodeNotFound,
        RevisionConflict,
        DocumentStorageError,
    ) as error:
        raise translate(error) from error
    return ContentResponse(
        node_id=node.id,
        revision=node.revision,
        version=version.version,
        format=version.format,
        content=payload.content,
    )


@router.get("")
def list_nodes(
    project_id: UUID,
    user: CurrentUser,
    service: KnowledgeServiceDependency,
    parent_id: UUID | None = None,
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
def tree(
    project_id: UUID, user: CurrentUser, service: KnowledgeServiceDependency
) -> dict:
    try:
        nodes = service.list_nodes(project_id, user.id)
    except ProjectNotFound as error:
        raise translate(error) from error
    return {"items": nodes}


@router.post("", status_code=201)
def create_node(
    project_id: UUID,
    payload: NodeInput,
    user: CurrentUser,
    service: KnowledgeServiceDependency,
):
    try:
        return service.create_node(
            project_id, user.id, payload.parent_id, payload.kind, payload.name
        )
    except (ProjectNotFound, InvalidNodeOperation, NodeConflict) as error:
        raise translate(error) from error


@router.get("/{node_id}")
def get_node(
    project_id: UUID,
    node_id: UUID,
    user: CurrentUser,
    service: KnowledgeServiceDependency,
):
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
    service: KnowledgeServiceDependency,
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
    service: KnowledgeServiceDependency,
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
    service: KnowledgeServiceDependency,
    if_match: str | None = Header(default=None),
) -> None:
    try:
        service.archive_node(project_id, user.id, node_id, expected_revision(if_match))
    except (ProjectNotFound, NodeNotFound, RevisionConflict) as error:
        raise translate(error) from error
