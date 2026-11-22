from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)

    @field_validator("name")
    @classmethod
    def non_empty_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Название не может быть пустым")
        return value


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    owner_id: UUID
    revision: int
    created_at: datetime


class ProductInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)

    @field_validator("name")
    @classmethod
    def non_empty_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Название не может быть пустым")
        return value


class FactInput(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    source_url: str | None = Field(default=None, max_length=2000)

    @field_validator("text")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Факт не может быть пустым")
        return value


class ContextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(default="", max_length=10000)
    audiences: list[str] = Field(default_factory=list, max_length=50)
    products: list[ProductInput] = Field(default_factory=list, max_length=50)
    facts: list[FactInput] = Field(default_factory=list, max_length=100)
    tone_of_voice: str = Field(default="", max_length=5000)
    forbidden_terms: list[str] = Field(default_factory=list, max_length=100)
    source_version_ids: list[UUID] = Field(default_factory=list)


class ContextResponse(ContextInput):
    project_id: UUID
    revision: int
