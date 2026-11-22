from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.application.avatars.library import AvatarLibrary
from app.container import avatar_library
from app.domain.knowledge import (
    DocumentStorageError,
    InvalidNodeOperation,
    NodeConflict,
    NodeNotFound,
)
from app.presentation.http.dependencies import CurrentUser
from app.presentation.http.errors import translate

router = APIRouter(prefix="/api/v1/avatars")
Library = Annotated[AvatarLibrary, Depends(avatar_library)]


@router.post("/workspace")
def workspace(user: CurrentUser, library: Library):
    return {
        "project_id": library.workspace(user.id),
        "assignments": library.assigned_projects(user.id),
    }


@router.post("/{avatar}/projects/{project}")
def assign(avatar: UUID, project: UUID, user: CurrentUser, library: Library):
    try:
        return {"node_id": library.assign(user.id, avatar, project)}
    except (
        InvalidNodeOperation,
        NodeConflict,
        NodeNotFound,
        DocumentStorageError,
    ) as error:
        raise translate(error) from error
