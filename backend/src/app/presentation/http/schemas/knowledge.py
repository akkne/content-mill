from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class DocumentInput(BaseModel):
    content: str = Field(max_length=1000000)
    format: Literal["markdown", "plain"]


class VersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    node_id: UUID
    version: int
    format: str
    size_bytes: int
    sha256: str
    created_at: datetime


class ContentResponse(BaseModel):
    node_id: UUID
    revision: int
    version: int
    format: str
    content: str
