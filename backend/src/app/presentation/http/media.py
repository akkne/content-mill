from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Header, Query
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.domain.knowledge import (
    DocumentStorageError,
    InvalidNodeOperation,
    NodeConflict,
    NodeNotFound,
)
from app.domain.media import MAX_MEDIA_BYTES
from app.domain.project import ProjectNotFound, RevisionConflict
from app.infrastructure.examples.library import example_entries
from app.presentation.http.knowledge import (
    CurrentUser,
    RenameInput,
    Service,
    VersionResponse,
    translate,
)
from app.presentation.http.projects import expected_revision

router = APIRouter(prefix="/api/v1/projects/{project_id}")
media_errors = (
    ProjectNotFound,
    NodeNotFound,
    NodeConflict,
    RevisionConflict,
    InvalidNodeOperation,
    DocumentStorageError,
)


class UploadInput(RenameInput):
    parent_id: UUID | None = None
    node_id: UUID | None = None
    mime_type: str
    size_bytes: int = Field(gt=0, le=MAX_MEDIA_BYTES)
    sha256: str = Field(pattern="^[a-f0-9]{64}$")


@router.post("/files/uploads", status_code=201)
def start(
    project_id: UUID,
    payload: UploadInput,
    user: CurrentUser,
    service: Service,
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
def complete(project_id: UUID, upload_id: UUID, user: CurrentUser, service: Service):
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
    service: Service,
    version: Annotated[int | None, Query(ge=1)] = None,
):
    try:
        url, selected = service.download(project_id, user.id, node_id, version)
        return {"url": url, "version": VersionResponse.model_validate(selected)}
    except media_errors as error:
        raise translate(error) from error


@router.post("/files/examples", status_code=201)
def examples(project_id: UUID, user: CurrentUser, service: Service):
    try:
        return {
            "items": service.import_examples(project_id, user.id, example_entries())
        }
    except media_errors as error:
        raise translate(error) from error


class AvatarProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    linked_voice_id: UUID | None = None


class VoiceProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str = Field(max_length=4000)
    voice_gender: Literal["male", "female"] | None = None
    voice_language: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=80)
    ]
    voice_model: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=160)
    ]
    elevenlabs_voice_id: str | None = Field(default=None, max_length=160)


@router.put("/nodes/{node_id}/profile")
def profile(
    project_id: UUID,
    node_id: UUID,
    payload: VoiceProfile | AvatarProfile,
    user: CurrentUser,
    service: Service,
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
