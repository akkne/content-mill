from uuid import UUID

from sqlalchemy import func, or_, select, tuple_, update
from sqlalchemy.orm import Session

from app.domain.project import (
    Fact,
    InvalidCursor,
    Product,
    Project,
    ProjectContext,
)
from app.infrastructure.database.models import (
    AvatarWorkspaceModel,
    DocumentVersionModel,
    KnowledgeNodeModel,
    LibraryVoiceModel,
    ProjectContextModel,
    ProjectModel,
    UserModel,
    VideoModel,
)
from app.infrastructure.database.repositories.voice_library import SqlVoiceLibrary


def as_project(model: ProjectModel) -> Project:
    return Project(
        model.id,
        model.owner_id,
        model.name,
        model.revision,
        model.created_at,
        model.video_duration,
        model.video_style,
    )


def as_context(model: ProjectContextModel) -> ProjectContext:
    return ProjectContext(
        project_id=model.project_id,
        revision=model.revision,
        description=model.description,
        audiences=model.audiences,
        products=[Product(**item) for item in model.products],
        facts=[Fact(**item) for item in model.facts],
        tone_of_voice=model.tone_of_voice,
        forbidden_terms=model.forbidden_terms,
        source_version_ids=[UUID(item) for item in model.source_version_ids],
    )


class SqlAlchemyProjectRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_clients(self, query, mode, offset, limit):
        project = ProjectModel
        conditions = [~project.id.in_(select(AvatarWorkspaceModel.project_id))]
        if query:
            conditions.append(
                or_(
                    project.name.icontains(query, autoescape=True),
                    UserModel.email.icontains(query, autoescape=True),
                )
            )
        totals = dict(
            self.session.execute(
                select(project.sales_mode, func.count())
                .join(UserModel, UserModel.id == project.owner_id)
                .where(*conditions)
                .group_by(project.sales_mode)
            ).all()
        )
        if mode:
            conditions.append(project.sales_mode == mode)
        videos = (
            select(func.count(VideoModel.id))
            .where(VideoModel.project_id == project.id)
            .scalar_subquery()
        )
        rows = self.session.execute(
            select(
                project.id,
                project.name,
                UserModel.email,
                project.sales_mode,
                project.package_name,
                project.delivery_notes,
                project.video_duration,
                project.video_style,
                project.admin_revision,
                videos.label("video_count"),
            )
            .join(UserModel, UserModel.id == project.owner_id)
            .where(*conditions)
            .order_by(project.created_at.desc(), project.id.desc())
            .offset(offset)
            .limit(limit)
        ).mappings()
        return {"items": [dict(row) for row in rows], "totals": totals}

    def update_client(self, project_id, revision, settings):
        updated = self.session.scalar(
            update(ProjectModel)
            .where(
                ProjectModel.id == project_id,
                ProjectModel.admin_revision == revision,
                ~ProjectModel.id.in_(select(AvatarWorkspaceModel.project_id)),
            )
            .values(**settings, admin_revision=revision + 1)
            .returning(ProjectModel.id)
        )
        return updated is not None

    def list_owned(
        self, owner_id: UUID, limit: int, cursor: UUID | None
    ) -> list[Project]:
        query = select(ProjectModel).where(
            ProjectModel.owner_id == owner_id,
            ~ProjectModel.id.in_(select(AvatarWorkspaceModel.project_id)),
        )
        if cursor:
            last = self.session.scalar(
                select(ProjectModel).where(
                    ProjectModel.id == cursor, ProjectModel.owner_id == owner_id
                )
            )
            if last is None:
                raise InvalidCursor
            query = query.where(
                tuple_(ProjectModel.created_at, ProjectModel.id)
                < tuple_(last.created_at, last.id)
            )
        models = self.session.scalars(
            query.order_by(
                ProjectModel.created_at.desc(), ProjectModel.id.desc()
            ).limit(limit + 1)
        ).all()
        return [as_project(model) for model in models]

    def create(self, owner_id: UUID, name: str) -> Project:
        model = ProjectModel(owner_id=owner_id, name=name)
        self.session.add(model)
        self.session.flush()
        self.session.add(ProjectContextModel(project_id=model.id))
        return as_project(model)

    def avatar_assignments(self, owner: UUID) -> dict[UUID, list[UUID]]:
        node = KnowledgeNodeModel
        rows = self.session.execute(
            select(node.library_avatar_id, node.project_id)
            .join(ProjectModel, ProjectModel.id == node.project_id)
            .where(
                ProjectModel.owner_id == owner,
                node.library_avatar_id.is_not(None),
                node.archived_at.is_(None),
            )
        )
        result: dict[UUID, list[UUID]] = {}
        for avatar, project in rows:
            result.setdefault(avatar, []).append(project)
        return result

    def attach_avatar_voice(self, project: UUID, voice: UUID, owner: UUID) -> UUID:
        card = self.session.scalar(
            select(LibraryVoiceModel).where(
                LibraryVoiceModel.id == voice, LibraryVoiceModel.owner_id == owner
            )
        )
        if card is None:
            raise ValueError("Missing avatar voice")
        node = self.session.scalar(
            select(KnowledgeNodeModel).where(
                KnowledgeNodeModel.project_id == project,
                KnowledgeNodeModel.library_voice_id == voice,
                KnowledgeNodeModel.archived_at.is_(None),
            )
        )
        return (node or SqlVoiceLibrary().attach(self.session, project, card)).id

    def avatar_workspace(self, owner: UUID) -> tuple[UUID, bool]:
        self.session.scalar(
            select(UserModel.id).where(UserModel.id == owner).with_for_update()
        )
        existing = self.session.get(AvatarWorkspaceModel, owner)
        if existing:
            return existing.project_id, False
        project = self.create(owner, "Личная библиотека аватаров")
        self.session.add(AvatarWorkspaceModel(owner_id=owner, project_id=project.id))
        return project.id, True

    def get_owned(self, project_id: UUID, owner_id: UUID) -> Project | None:
        model = self.session.scalar(
            select(ProjectModel).where(
                ProjectModel.id == project_id, ProjectModel.owner_id == owner_id
            )
        )
        return as_project(model) if model else None

    def rename(self, project_id: UUID, name: str, revision: int) -> Project | None:
        model = self.session.scalar(
            update(ProjectModel)
            .where(ProjectModel.id == project_id, ProjectModel.revision == revision)
            .values(name=name, revision=revision + 1)
            .returning(ProjectModel)
        )
        return as_project(model) if model else None

    def context(self, project_id: UUID) -> ProjectContext:
        model = self.session.get(ProjectContextModel, project_id)
        if model is None:
            raise RuntimeError("Project context is missing")
        return as_context(model)

    def save_context(
        self, context: ProjectContext, revision: int
    ) -> ProjectContext | None:
        model = self.session.scalar(
            update(ProjectContextModel)
            .where(
                ProjectContextModel.project_id == context.project_id,
                ProjectContextModel.revision == revision,
            )
            .values(
                revision=revision + 1,
                description=context.description,
                audiences=context.audiences,
                products=[vars(item) for item in context.products],
                facts=[vars(item) for item in context.facts],
                tone_of_voice=context.tone_of_voice,
                forbidden_terms=context.forbidden_terms,
                source_version_ids=[str(item) for item in context.source_version_ids],
            )
            .returning(ProjectContextModel)
        )
        return as_context(model) if model else None

    def valid_source_versions(self, project_id: UUID, version_ids: list[UUID]) -> bool:
        if not version_ids:
            return True
        found = self.session.scalars(
            select(DocumentVersionModel.id)
            .join(
                KnowledgeNodeModel,
                DocumentVersionModel.node_id == KnowledgeNodeModel.id,
            )
            .where(
                DocumentVersionModel.id.in_(version_ids),
                KnowledgeNodeModel.kind == "document",
                KnowledgeNodeModel.project_id == project_id,
            )
        ).all()
        return len(set(found)) == len(set(version_ids))
