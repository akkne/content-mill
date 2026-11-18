from dataclasses import replace
from hashlib import sha256
from uuid import UUID, uuid4

from app.application.knowledge_ports import (
    DocumentStore,
    KnowledgeUnitOfWork,
    KnowledgeUnitOfWorkFactory,
)
from app.domain.knowledge import (
    DocumentVersion,
    InvalidNodeOperation,
    KnowledgeNode,
    NodeConflict,
    NodeNotFound,
)
from app.domain.project import ProjectNotFound, RevisionConflict


class KnowledgeService:
    def __init__(
        self, unit_of_work: KnowledgeUnitOfWorkFactory, store: DocumentStore
    ) -> None:
        self.unit_of_work = unit_of_work
        self.store = store

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

    def _document(
        self, work: KnowledgeUnitOfWork, project_id: UUID, node_id: UUID
    ) -> KnowledgeNode:
        node = work.repository.get(project_id, node_id)
        if node is None or node.kind != "document":
            raise NodeNotFound
        return node

    def document_versions(
        self, project_id: UUID, owner_id: UUID, node_id: UUID
    ) -> list[DocumentVersion]:
        with self.unit_of_work() as work:
            self._owned(work, project_id, owner_id)
            self._document(work, project_id, node_id)
            return work.repository.versions(node_id)

    def document_content(
        self,
        project_id: UUID,
        owner_id: UUID,
        node_id: UUID,
        version: int | None = None,
    ) -> tuple[KnowledgeNode, DocumentVersion | None, str]:
        with self.unit_of_work() as work:
            self._owned(work, project_id, owner_id)
            node = self._document(work, project_id, node_id)
            versions = work.repository.versions(node_id)
        if version is not None and not any(
            item.version == version for item in versions
        ):
            raise NodeNotFound
        selected = (
            next((item for item in versions if item.version == version), None)
            if version is not None
            else (versions[0] if versions else None)
        )
        if selected is None:
            return node, None, ""
        content = self.store.get(selected.storage_key)
        if sha256(content).hexdigest() != selected.sha256:
            raise InvalidNodeOperation("Содержимое документа повреждено")
        return node, selected, content.decode("utf-8")

    def save_document(
        self,
        project_id: UUID,
        owner_id: UUID,
        node_id: UUID,
        revision: int,
        content: str,
        format: str,
    ) -> tuple[KnowledgeNode, DocumentVersion]:
        encoded = content.encode("utf-8")
        with self.unit_of_work() as work:
            self._owned(work, project_id, owner_id)
            node = self._document(work, project_id, node_id)
            versions = work.repository.versions(node_id)
            if node.revision != revision:
                raise RevisionConflict
            version_number = versions[0].version + 1 if versions else 1
            key = f"projects/{project_id}/nodes/{node_id}/versions/{uuid4()}"
            self.store.put(
                key,
                encoded,
                "text/markdown; charset=utf-8"
                if format == "markdown"
                else "text/plain; charset=utf-8",
            )
            try:
                saved = work.repository.add_version(
                    node_id,
                    revision,
                    version_number,
                    format,
                    len(encoded),
                    sha256(encoded).hexdigest(),
                    key,
                )
                if saved is None:
                    raise RevisionConflict
                work.commit()
            except Exception:
                self.store.delete(key)
                raise
        return replace(node, revision=revision + 1), saved
