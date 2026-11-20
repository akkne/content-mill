from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.application.speech import Reservation
from app.application.voice_catalog import CatalogError
from app.infrastructure.database.models import LibraryVoiceModel as Voice
from app.infrastructure.database.models import SpeechJobModel as Job
from app.infrastructure.database.session import session_factory


class SqlSpeechRepository:
    def reserve(
        self, owner: UUID, voice: UUID, request: UUID, text: str
    ) -> Reservation:
        digest = sha256(text.encode()).hexdigest()
        with session_factory().begin() as db:
            row = db.scalar(
                select(Voice)
                .where(Voice.id == voice, Voice.owner_id == owner)
                .with_for_update()
            )
            if row is None:
                raise CatalogError(404, "Голос не найден.")
            existing = db.get(Job, request)
            if existing:
                if existing.voice_id != voice or existing.text_hash != digest:
                    raise CatalogError(409, "Этот идентификатор уже использован.")
                return Reservation(False, "", None)
            if not row.elevenlabs_voice_id:
                raise CatalogError(422, "В карточке отсутствует ID ElevenLabs.")
            if row.voice_model and row.voice_model != "eleven_multilingual_v2":
                raise CatalogError(
                    422,
                    "Для озвучки укажите модель eleven_multilingual_v2 в карточке голоса.",
                )
            if db.scalar(
                select(Job.id)
                .where(
                    Job.voice_id == voice,
                    Job.status == "submitting",
                    Job.created_at > datetime.now(UTC) - timedelta(minutes=2),
                )
                .limit(1)
            ):
                raise CatalogError(409, "Предыдущий запрос ещё отправляется.")
            db.add(
                Job(id=request, voice_id=voice, text_hash=digest, status="submitting")
            )
            try:
                db.flush()
            except IntegrityError as error:
                raise CatalogError(
                    409, "Этот идентификатор уже использован."
                ) from error
            return Reservation(True, row.elevenlabs_voice_id, row.lumean_template_id)

    def save_template(self, voice: UUID, template: UUID):
        with session_factory().begin() as db:
            db.execute(
                update(Voice)
                .where(Voice.id == voice)
                .values(lumean_template_id=template)
            )

    def finish(self, request: UUID, order: UUID | None, status: str):
        with session_factory().begin() as db:
            db.execute(
                update(Job)
                .where(Job.id == request)
                .values(status=status, order_id=order)
            )

    def lookup(self, owner: UUID, voice: UUID, request: UUID):
        with session_factory()() as db:
            job = db.scalar(
                select(Job)
                .join(Voice)
                .where(Voice.owner_id == owner, Voice.id == voice, Job.id == request)
            )
            if job is None:
                raise CatalogError(404, "Озвучка не найдена.")
            if job.status == "submitting" and datetime.now(
                UTC
            ) - job.created_at > timedelta(minutes=2):
                return "uncertain", None
            return job.status, job.order_id

    def recent(self, owner: UUID, voice: UUID) -> list[UUID]:
        with session_factory()() as db:
            return list(
                db.scalars(
                    select(Job.id)
                    .join(Voice)
                    .where(Voice.id == voice, Voice.owner_id == owner)
                    .order_by(Job.created_at.desc())
                    .limit(20)
                )
            )
