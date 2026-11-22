from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.application.voices.catalog import CatalogError, CatalogVoice, VoiceCatalog
from app.domain.knowledge import InvalidNodeOperation, KnowledgeNode


@dataclass
class LibraryVoice:
    id: UUID
    name: str
    description: str | None
    elevenlabs_voice_id: str | None
    voice_language: str | None
    catalog_languages: list[str] | None
    voice_gender: str | None
    voice_model: str | None
    voice_preview_url: str | None
    project_ids: list[UUID]


class LibraryRepository(Protocol):
    def list_owned(self, owner: UUID) -> list[LibraryVoice]: ...
    def create(
        self, owner: UUID, name: str, voice: CatalogVoice, model: str | None
    ) -> LibraryVoice: ...
    def edit(self, owner: UUID, voice: UUID, fields: dict) -> LibraryVoice: ...
    def assign(
        self, owner: UUID, voice: UUID, add: set[UUID], remove: set[UUID]
    ) -> list[KnowledgeNode]: ...


class VoiceLibrary:
    def __init__(self, repository: LibraryRepository, catalog: VoiceCatalog):
        self.repository = repository
        self.catalog = catalog

    def create(
        self,
        owner: UUID,
        name: str,
        voice_id: str,
        from_catalog: bool,
        description: str,
        language: str,
        gender: str | None,
        model: str | None,
    ):
        voice = CatalogVoice(
            voice_id, name, description, [language] if language else [], gender, None
        )
        if from_catalog:
            page = self.catalog.search(voice_id, True, "", "", "")
            if not page.items:
                raise CatalogError(404, "Голос больше не доступен в каталоге")
            voice = page.items[0]
        return self.repository.create(owner, name, voice, model)

    def assign(self, owner: UUID, voice: UUID, add: set[UUID], remove: set[UUID]):
        if add & remove:
            raise InvalidNodeOperation("Проект одновременно выбран и снят")
        return self.repository.assign(owner, voice, add, remove)
