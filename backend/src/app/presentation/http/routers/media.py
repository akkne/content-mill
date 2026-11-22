from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query

from app.domain.knowledge import (
    DocumentStorageError,
    InvalidNodeOperation,
    NodeConflict,
    NodeNotFound,
)
from app.domain.project import ProjectNotFound, RevisionConflict
from app.infrastructure.examples.library import example_entries
from app.presentation.http.dependencies import (
    CurrentUser,
    KnowledgeServiceDependency,
    expected_revision,
)
from app.presentation.http.errors import translate
from app.presentation.http.schemas.knowledge import VersionResponse
from app.presentation.http.schemas.media import AvatarProfile, UploadInput, VoiceProfile

router = APIRouter(prefix="/api/v1/projects/{project_id}")
media_errors = (
    ProjectNotFound,
    NodeNotFound,
    NodeConflict,
    RevisionConflict,
    InvalidNodeOperation,
    DocumentStorageError,
)


@router.post("/files/uploads", status_code=201)
def start(
    project_id: UUID,
    payload: UploadInput,
    user: CurrentUser,
    service: KnowledgeServiceDependency,
    if_match: str | None = Header(default=None),
):
    try:
        upload, url = service.start_upload(
            project_id,
            user.id,
            payload.parent_id,
            payload.node_id,
            expected_revision(if_match) if payload.node_id else None,
            payload.name,
            payload.mime_type,
            payload.size_bytes,
            payload.sha256,
        )
        return {
            "upload_id": upload.id,
            "upload_url": url,
            "expires_at": upload.expires_at,
        }
    except media_errors as error:
        raise translate(error) from error


@router.post("/files/uploads/{upload_id}/complete")
def complete(
    project_id: UUID,
    upload_id: UUID,
    user: CurrentUser,
    service: KnowledgeServiceDependency,
):
    try:
        node, version = service.complete_upload(project_id, user.id, upload_id)
        return {"node": node, "version": VersionResponse.model_validate(version)}
    except media_errors as error:
        raise translate(error) from error


@router.get("/nodes/{node_id}/download")
def download(
    project_id: UUID,
    node_id: UUID,
    user: CurrentUser,
    service: KnowledgeServiceDependency,
    version: Annotated[int | None, Query(ge=1)] = None,
):
    try:
        url, selected = service.download(project_id, user.id, node_id, version)
        return {"url": url, "version": VersionResponse.model_validate(selected)}
    except media_errors as error:
        raise translate(error) from error


@router.post("/files/examples", status_code=201)
def examples(project_id: UUID, user: CurrentUser, service: KnowledgeServiceDependency):
    try:
        return {
            "items": service.import_examples(project_id, user.id, example_entries())
        }
    except media_errors as error:
        raise translate(error) from error


@router.put("/nodes/{node_id}/profile")
def profile(
    project_id: UUID,
    node_id: UUID,
    payload: VoiceProfile | AvatarProfile,
    user: CurrentUser,
    service: KnowledgeServiceDependency,
    if_match: str | None = Header(default=None),
):
    try:
        role = "voice" if isinstance(payload, VoiceProfile) else "avatar"
        return service.edit_profile(
            project_id,
            user.id,
            node_id,
            expected_revision(if_match),
            role,
            **payload.model_dump(
                exclude={"voice_gender"}
                if role == "voice" and "voice_gender" not in payload.model_fields_set
                else set()
            ),
        )
    except media_errors as error:
        raise translate(error) from error
