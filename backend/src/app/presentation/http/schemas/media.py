from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.domain.media import MAX_MEDIA_BYTES
from app.presentation.http.schemas.knowledge import RenameInput


class UploadInput(RenameInput):
    parent_id: UUID | None = None
    node_id: UUID | None = None
    mime_type: str
    size_bytes: int = Field(gt=0, le=MAX_MEDIA_BYTES)
    sha256: str = Field(pattern="^[a-f0-9]{64}$")


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
