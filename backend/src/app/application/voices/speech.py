from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.application.voices.catalog import CatalogError


@dataclass
class SpeechResult:
    status: str
    url: str | None = None


class SpeechProvider(ABC):
    @abstractmethod
    def template(self, voice: str) -> UUID: ...

    @abstractmethod
    def submit(self, template: UUID, voice: str, text: str, request: UUID) -> UUID: ...

    @abstractmethod
    def result(self, order: UUID) -> SpeechResult: ...


@dataclass
class Reservation:
    fresh: bool
    voice: str
    template: UUID | None


class SpeechRepository(Protocol):
    def reserve(
        self, owner: UUID, voice: UUID, request: UUID, text: str
    ) -> Reservation: ...
    def save_template(self, voice: UUID, template: UUID) -> None: ...
    def finish(self, request: UUID, order: UUID | None, status: str) -> None: ...
    def lookup(
        self, owner: UUID, voice: UUID, request: UUID
    ) -> tuple[str, UUID | None]: ...
    def recent(self, owner: UUID, voice: UUID) -> list[UUID]: ...


class SpeechService:
    def __init__(self, repository: SpeechRepository, provider: SpeechProvider):
        self.repository = repository
        self.provider = provider

    def create(self, owner: UUID, voice: UUID, request: UUID, text: str):
        job = self.repository.reserve(owner, voice, request, text)
        if not job.fresh:
            return
        try:
            template = job.template
            if template is None:
                template = self.provider.template(job.voice)
                self.repository.save_template(voice, template)
        except CatalogError:
            self.repository.finish(request, None, "failed")
            raise
        try:
            order = self.provider.submit(template, job.voice, text, request)
        except CatalogError as error:
            self.repository.finish(
                request, None, "uncertain" if error.status == 502 else "failed"
            )
            raise
        self.repository.finish(request, order, "submitted")

    def result(self, owner: UUID, voice: UUID, request: UUID) -> SpeechResult:
        status, order = self.repository.lookup(owner, voice, request)
        return self.provider.result(order) if order else SpeechResult(status)
