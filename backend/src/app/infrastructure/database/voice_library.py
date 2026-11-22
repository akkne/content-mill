from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.application.voice_catalog import CatalogVoice
from app.application.voice_library import LibraryVoice
from app.domain.knowledge import InvalidNodeOperation, NodeNotFound
from app.domain.project import ProjectNotFound
from app.infrastructure.database.knowledge_repository import as_node
from app.infrastructure.database.models import (
    AvatarWorkspaceModel,
    ProjectModel,
    UserModel,
)
from app.infrastructure.database.models import KnowledgeNodeModel as Node
from app.infrastructure.database.models import LibraryVoiceModel as Voice
from app.infrastructure.database.session import session_factory

VOICE_FIELDS = (
    "name",
    "description",
    "elevenlabs_voice_id",
    "voice_gender",
    "voice_language",
    "catalog_languages",
    "voice_model",
    "voice_preview_url",
)


def view(row: Voice, projects: list[UUID]) -> LibraryVoice:
    return LibraryVoice(
        id=row.id, project_ids=projects, **{k: getattr(row, k) for k in VOICE_FIELDS}
    )


class SqlVoiceLibrary:
    def list_owned(self, owner: UUID):
        with session_factory()() as db:
            rows = db.execute(
                select(Voice, Node.project_id)
                .outerjoin(
                    Node,
                    (Node.library_voice_id == Voice.id)
                    & Node.archived_at.is_(None)
                    & ~Node.project_id.in_(select(AvatarWorkspaceModel.project_id)),
                )
                .where(Voice.owner_id == owner)
                .order_by(Voice.name, Voice.id)
            )
            voices = {}
            for voice, project in rows:
                if voice.id not in voices:
                    voices[voice.id] = view(voice, [])
                if project:
                    voices[voice.id].project_ids.append(project)
            return list(voices.values())

    def create(self, owner: UUID, name: str, voice: CatalogVoice, model: str | None):
        with session_factory().begin() as db:
            db.scalar(
                select(UserModel.id).where(UserModel.id == owner).with_for_update()
            )
            existing = db.scalar(
                select(Voice.id).where(
                    Voice.owner_id == owner,
                    Voice.name == name,
                    Voice.elevenlabs_voice_id == voice.id,
                )
            )
            if existing:
                raise InvalidNodeOperation(
                    "Этот голос уже сохранён под таким названием"
                )
            row = Voice(
                owner_id=owner,
                name=name,
                description=voice.description,
                elevenlabs_voice_id=voice.id,
                voice_gender=voice.gender,
                catalog_languages=voice.languages,
                voice_language=next(iter(voice.languages), None),
                voice_model=model,
                voice_preview_url=voice.preview_url,
            )
            db.add(row)
            db.flush()
            return view(row, [])

    def edit(self, owner: UUID, voice: UUID, fields: dict):
        with session_factory().begin() as db:
            row = db.scalar(
                select(Voice)
                .where(Voice.id == voice, Voice.owner_id == owner)
                .with_for_update()
            )
            if row is None:
                raise NodeNotFound
            if fields["elevenlabs_voice_id"] != row.elevenlabs_voice_id:
                fields.update(catalog_languages=[], voice_preview_url=None)
            changes = {
                key: value
                for key, value in fields.items()
                if getattr(row, key) != value
            }
            if changes:
                for key, value in changes.items():
                    setattr(row, key, value)
                db.execute(
                    update(Node)
                    .where(Node.library_voice_id == voice)
                    .values(**changes, revision=Node.revision + 1)
                )
            projects = list(
                db.scalars(
                    select(Node.project_id).where(
                        Node.library_voice_id == voice, Node.archived_at.is_(None)
                    )
                )
            )
            return view(row, projects)

    def assign(self, owner: UUID, voice: UUID, add: set[UUID], remove: set[UUID]):
        with session_factory().begin() as db:
            row = db.scalar(
                select(Voice)
                .where(Voice.id == voice, Voice.owner_id == owner)
                .with_for_update()
            )
            if row is None:
                raise NodeNotFound
            targets = set(
                db.scalars(
                    select(ProjectModel.id)
                    .where(
                        ProjectModel.owner_id == owner,
                        ProjectModel.id.in_(add | remove),
                    )
                    .order_by(ProjectModel.id)
                    .with_for_update()
                )
            )
            if targets != add | remove:
                raise ProjectNotFound
            added = []
            for project in sorted(targets):
                active = db.scalar(
                    select(Node).where(
                        Node.project_id == project,
                        Node.library_voice_id == voice,
                        Node.archived_at.is_(None),
                    )
                )
                if project in add:
                    added.append(as_node(active or self.attach(db, project, row)))
                elif active is not None:
                    self._detach(db, active)
            return added

    def attach(self, db: Session, project: UUID, voice: Voice):
        folder = db.scalar(
            select(Node.id).where(
                Node.project_id == project,
                Node.folder_role == "voices",
                Node.archived_at.is_(None),
            )
        )
        if folder is None:
            raise InvalidNodeOperation("В выбранном проекте отсутствует папка «Голоса»")
        previous = db.scalar(
            select(Node).where(
                Node.project_id == project,
                Node.library_voice_id == voice.id,
                Node.folder_role == "detached_voice",
            )
        )
        fields = {key: getattr(voice, key) for key in VOICE_FIELDS}
        names = {
            name.casefold()
            for name in db.scalars(
                select(Node.name).where(
                    Node.parent_id == folder, Node.archived_at.is_(None)
                )
            )
        }
        base = previous.name if previous else voice.name
        name = base
        suffix = 2
        while name.casefold() in names:
            ending = f" ({suffix})"
            name = base[: 160 - len(ending)] + ending
            suffix += 1
        if previous:
            db.execute(
                update(Node)
                .where(
                    Node.id.in_(self._descendants(previous.id)),
                    Node.archived_at == previous.archived_at,
                )
                .values(archived_at=None, revision=Node.revision + 1)
            )
            previous.archived_at = None
            previous.folder_role = "voice"
            previous.parent_id = folder
            previous.name = name
            previous.revision += 1
            node = previous
        else:
            fields["name"] = name
            node = Node(
                project_id=project,
                parent_id=folder,
                kind="folder",
                folder_role="voice",
                library_voice_id=voice.id,
                **fields,
            )
            db.add(node)
        db.flush()
        return node

    @staticmethod
    def _descendants(root: UUID):
        children = select(Node.id).where(Node.parent_id == root).cte(recursive=True)
        children = children.union_all(
            select(Node.id).join(children, Node.parent_id == children.c.id)
        )
        return select(children.c.id)

    def _detach(self, db: Session, node: Node):
        instant = datetime.now(UTC)
        db.execute(
            update(Node)
            .where(Node.id.in_(self._descendants(node.id)), Node.archived_at.is_(None))
            .values(archived_at=instant, revision=Node.revision + 1)
        )
        db.execute(
            update(Node)
            .where(Node.project_id == node.project_id, Node.linked_voice_id == node.id)
            .values(linked_voice_id=None, revision=Node.revision + 1)
        )
        node.archived_at = instant
        node.folder_role = "detached_voice"
        node.revision += 1
