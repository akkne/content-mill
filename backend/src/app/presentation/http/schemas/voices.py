from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

from app.presentation.http.schemas.knowledge import RenameInput

Gender = Literal["male", "female"]


class SaveVoice(RenameInput):
    voice_id: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)
    ]
    from_catalog: bool = False
    gender: Gender | None = Field(default=None)

    description: str = Field(default="", max_length=4000)
    language: str = Field(default="", max_length=80)
    model: str | None = Field(default=None, max_length=160)


class AssignProjects(BaseModel):
    add: set[UUID] = Field(default_factory=set)
    remove: set[UUID] = Field(default_factory=set)


class VoiceDetails(BaseModel):
    description: str = Field(max_length=4000)
    voice_language: str = Field(max_length=80)
    voice_gender: Gender | None
    voice_model: str = Field(max_length=160)
    elevenlabs_voice_id: str | None = Field(max_length=160)


class SpeechInput(BaseModel):
    text: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
    ]
    request_id: UUID
