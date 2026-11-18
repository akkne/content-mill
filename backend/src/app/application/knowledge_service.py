from uuid import UUID

from app.application.knowledge_ports import (
    KnowledgeUnitOfWork,
    KnowledgeUnitOfWorkFactory,
)
from app.domain.knowledge import (
    InvalidNodeOperation,
    KnowledgeNode,
    NodeConflict,
    NodeNotFound,
)
from app.domain.project import ProjectNotFound, RevisionConflict


class KnowledgeService:
    def __init__(self, unit_of_work: KnowledgeUnitOfWorkFactory) -> None:
        self.unit_of_work = unit_of_work

    def _owned(
        self, work: KnowledgeUnitOfWork, project_id: UUID, owner_id: UUID
    ) -> None:
        if not work.repository.owns_project(project_id, owner_id):
            raise ProjectNotFound

    def list_nodes(self, project_id: UUID, owner_id: UUID) -> list[KnowledgeNode]:
        with self.unit_of_work() as work:
            self._owned(work, project_id, owner_id)
            return work.repository.list(project_id)

    def get_node(
        self, project_id: UUID, owner_id: UUID, node_id: UUID
    ) -> KnowledgeNode:
        with self.unit_of_work() as work:
            self._owned(work, project_id, owner_id)
            node = work.repository.get(project_id, node_id)
            if node is None:
                raise NodeNotFound
            return node

    def _parent(
        self, work: KnowledgeUnitOfWork, project_id: UUID, parent_id: UUID | None
    ) -> None:
        if parent_id is None:
            return
        parent = work.repository.get(project_id, parent_id)
        if parent is None or parent.kind != "folder":
            raise InvalidNodeOperation("Родительская папка не найдена")

    def _unique(
        self,
        nodes: list[KnowledgeNode],
        parent_id: UUID | None,
        name: str,
        exclude: UUID | None = None,
    ) -> None:
        if any(
            n.parent_id == parent_id
            and n.name.casefold() == name.casefold()
            and n.id != exclude
            for n in nodes
        ):
            raise NodeConflict

    def create_node(
        self,
        project_id: UUID,
        owner_id: UUID,
        parent_id: UUID | None,
        kind: str,
        name: str,
    ) -> KnowledgeNode:
        with self.unit_of_work() as work:
            self._owned(work, project_id, owner_id)
            self._parent(work, project_id, parent_id)
            self._unique(work.repository.list(project_id), parent_id, name)
            node = work.repository.create(project_id, parent_id, kind, name)
            work.commit()
            return node

    def change_node(
        self,
        project_id: UUID,
        owner_id: UUID,
        node_id: UUID,
        revision: int,
        *,
        name: str | None = None,
        parent_id: UUID | None = None,
        move: bool = False,
    ) -> KnowledgeNode:
        with self.unit_of_work() as work:
            self._owned(work, project_id, owner_id)
            node = work.repository.get(project_id, node_id)
            if node is None:
                raise NodeNotFound
            nodes = work.repository.list(project_id)
            destination = parent_id if move else node.parent_id
            if move:
                self._parent(work, project_id, parent_id)
                parent = parent_id
                by_id = {item.id: item for item in nodes}
                while parent is not None:
                    if parent == node_id:
                        raise InvalidNodeOperation(
                            "Нельзя переместить папку внутрь себя"
                        )
                    parent = by_id[parent].parent_id
            next_name = name if name is not None else node.name
            self._unique(nodes, destination, next_name, node_id)
            values = {"name": next_name} if not move else {"parent_id": parent_id}
            updated = work.repository.change(project_id, node_id, revision, **values)
            if updated is None:
                raise RevisionConflict
            work.commit()
            return updated

    def archive_node(
        self, project_id: UUID, owner_id: UUID, node_id: UUID, revision: int
    ) -> None:
        with self.unit_of_work() as work:
            self._owned(work, project_id, owner_id)
            node = work.repository.get(project_id, node_id)
            if node is None:
                raise NodeNotFound
            nodes = work.repository.list(project_id)
            descendants: list[UUID] = []
            pending = [node_id]
            while pending:
                parent = pending.pop()
                children = [item.id for item in nodes if item.parent_id == parent]
                descendants.extend(children)
                pending.extend(children)
            if not work.repository.archive(project_id, descendants, node_id, revision):
                raise RevisionConflict
            work.commit()
