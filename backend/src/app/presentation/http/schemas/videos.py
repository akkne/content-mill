from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.video import DEFAULT_EDITING_STYLE


class CastRow(BaseModel):
    character_id: UUID
    voice_id: UUID | None = None


class VideoInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(min_length=1, max_length=180)
    brief: str = Field(default="", max_length=2000)
    product: str = Field(default="", max_length=200)
    platform: str = "Instagram Reels"
    method: str = "Проблема → решение"
    editing_style: str = DEFAULT_EDITING_STYLE
    duration: int = 30
    voice: str = Field(default="Без озвучки", max_length=160)
    language: str = "Русский"
    characters: list[CastRow] = Field(default_factory=list, max_length=32)
    sources: list[UUID] = Field(default_factory=list, max_length=100)
    product_photo_id: UUID | None = None
    heygen_lipsync: bool = False
    assemble: bool = False


class VideoAction(BaseModel):
    action: Literal[
        "assemble", "duplicate", "delete", "script", "caption", "publish", "schedule"
    ]
    value: str = Field(default="", max_length=6000)
