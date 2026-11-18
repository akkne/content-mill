from uuid import UUID

from sqlalchemy import select, tuple_, update
from sqlalchemy.orm import Session

from app.domain.project import (
    Fact,
    InvalidCursor,
    Product,
    Project,
    ProjectContext,
)
from app.infrastructure.database.models import (
    DocumentVersionModel,
    KnowledgeNodeModel,
    ProjectContextModel,
    ProjectModel,
)


def as_project(model: ProjectModel) -> Project:
    return Project(
        model.id, model.owner_id, model.name, model.revision, model.created_at
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

    def list_owned(
        self, owner_id: UUID, limit: int, cursor: UUID | None
    ) -> list[Project]:
        query = select(ProjectModel).where(ProjectModel.owner_id == owner_id)
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
        starter = [
            ("Бренд", None),
            ("Аватары", None),
            ("Референсы", None),
            ("Формулы роликов", None),
            ("Промпты", None),
            ("Ролики", None),
        ]
        folders: dict[str, KnowledgeNodeModel] = {}
        for folder_name, parent_name in starter:
            folder = KnowledgeNodeModel(
                project_id=model.id,
                parent_id=folders[parent_name].id if parent_name else None,
                kind="folder",
                name=folder_name,
            )
            self.session.add(folder)
            self.session.flush()
            folders[folder_name] = folder
        self.session.flush()
        return as_project(model)

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
                KnowledgeNodeModel.project_id == project_id,
            )
        ).all()
        return len(set(found)) == len(set(version_ids))
