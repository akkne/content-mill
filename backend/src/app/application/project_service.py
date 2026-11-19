from dataclasses import replace
from uuid import UUID

from app.application.project_ports import ProjectUnitOfWorkFactory
from app.domain.knowledge import AVATAR_DESCRIPTION, AVATAR_FOLDERS
from app.domain.project import (
    InvalidSourceVersion,
    Project,
    ProjectContext,
    ProjectNotFound,
    RevisionConflict,
)

STARTER_FOLDERS = (
    "Бренд",
    "Бренд/Товары",
    "Бренд/Формат",
    "Бренд/Правила бренда",
    "Аватары",
    "Аватары/Основной аватар",
    *(f"Аватары/Основной аватар/{name}" for name in AVATAR_FOLDERS),
    "Голоса",
    "Референсы",
    "Формулы роликов",
    "Промпты",
    *(
        f"Промпты/{name}"
        for name in (
            "Общие",
            "Бриф и источники",
            "Сценарий и хуки",
            "Раскадровка",
            "Голос",
            "Аватар",
            "Медиаматериалы",
            "Анимации",
            "Монтаж и субтитры",
            "Рендер и проверка",
            "Варианты и публикация",
        )
    ),
    "Ролики",
    "Ролики/CM-000123",
    "Ролики/CM-000123/Документы",
    "Ролики/CM-000123/Материалы",
    *(
        f"Ролики/CM-000123/Материалы/{name}"
        for name in ("Видео", "Аудио", "Изображения")
    ),
)


class ProjectService:
    def __init__(self, unit_of_work: ProjectUnitOfWorkFactory) -> None:
        self.unit_of_work = unit_of_work

    def list_projects(
        self, owner_id: UUID, limit: int = 20, cursor: UUID | None = None
    ) -> list[Project]:
        with self.unit_of_work() as work:
            return work.repository.list_owned(owner_id, limit, cursor)

    def create_project(self, owner_id: UUID, name: str) -> Project:
        with self.unit_of_work() as work:
            project = work.repository.create(owner_id, name.strip())
            folders: dict[str, UUID] = {}
            roles = {
                "Голоса": "voices",
                "Аватары": "avatars",
                "Аватары/Основной аватар": "avatar",
                **{
                    f"Аватары/Основной аватар/{name}": role
                    for name, role in AVATAR_FOLDERS.items()
                },
            }
            for path in STARTER_FOLDERS:
                parent, _, label = path.rpartition("/")
                folder = work.knowledge.create(
                    project.id,
                    folders[parent] if parent else None,
                    "folder",
                    label,
                    roles.get(path),
                )
                folders[path] = folder.id
            work.knowledge.create(
                project.id,
                folders["Аватары/Основной аватар"],
                "document",
                AVATAR_DESCRIPTION,
            )
            work.commit()
            return project

    def get_project(self, project_id: UUID, owner_id: UUID) -> Project:
        with self.unit_of_work() as work:
            project = work.repository.get_owned(project_id, owner_id)
        if project is None:
            raise ProjectNotFound
        return project

    def rename_project(
        self, project_id: UUID, owner_id: UUID, name: str, revision: int
    ) -> Project:
        with self.unit_of_work() as work:
            current = work.repository.get_owned(project_id, owner_id)
            if current is None:
                raise ProjectNotFound
            updated = work.repository.rename(project_id, name.strip(), revision)
            if updated is None:
                raise RevisionConflict
            work.commit()
            return updated

    def get_context(self, project_id: UUID, owner_id: UUID) -> ProjectContext:
        with self.unit_of_work() as work:
            if work.repository.get_owned(project_id, owner_id) is None:
                raise ProjectNotFound
            return work.repository.context(project_id)

    def save_context(
        self,
        project_id: UUID,
        owner_id: UUID,
        context: ProjectContext,
        revision: int,
        fields: set[str] | None = None,
    ) -> ProjectContext:
        with self.unit_of_work() as work:
            if work.repository.get_owned(project_id, owner_id) is None:
                raise ProjectNotFound
            if fields is not None:
                current = work.repository.context(project_id)
                if current.revision != revision:
                    raise RevisionConflict
                context = replace(
                    current, **{key: getattr(context, key) for key in fields}
                )
            if not work.repository.valid_source_versions(
                project_id, context.source_version_ids
            ):
                raise InvalidSourceVersion
            updated = work.repository.save_context(context, revision)
            if updated is None:
                raise RevisionConflict
            work.commit()
            return updated
