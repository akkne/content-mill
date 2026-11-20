from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogVoice:
    id: str
    name: str
    description: str
    languages: list[str]
    gender: str | None
    preview_url: str | None


@dataclass(frozen=True)
class VoicePage:
    items: list[CatalogVoice]
    next_cursor: str | None


class VoiceCatalog(ABC):
    @abstractmethod
    def search(
        self, query: str, exact: bool, language: str, gender: str, cursor: str
    ) -> VoicePage: ...


class CatalogError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
