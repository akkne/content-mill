from collections import defaultdict
from contextlib import ExitStack
from uuid import UUID

from app.application.knowledge.ports import DocumentStore, KnowledgeRepository
from app.application.knowledge.seed_documents import create_entry
from app.application.projects.ports import ProjectUnitOfWorkFactory
from app.domain.knowledge import (
    ExampleEntry,
    KnowledgeNode,
    NodeConflict,
    NodeNotFound,
)
from app.domain.project import ProjectNotFound


def ensure_library_folder(
    repo: KnowledgeRepository,
    project: UUID,
    nodes: list[KnowledgeNode],
    name: str,
    role: str,
) -> KnowledgeNode:
    for node in nodes:
        if node.folder_role == role and node.kind == "folder":
            return node
    # Keep existing user folders and archived trees intact.
    names = {node.name.casefold() for node in nodes if node.parent_id is None}
    candidate = name
    suffix = 2
    while candidate.casefold() in names:
        candidate = f"{name} ({suffix})"
        suffix += 1
    return repo.create(project, None, "folder", candidate, role)


class AvatarLibrary:
    def __init__(self, work: ProjectUnitOfWorkFactory, store: DocumentStore):
        self.work = work
        self.store = store

    def workspace(self, owner: UUID) -> UUID:
        with self.work() as work:
            project, fresh = work.repository.avatar_workspace(owner)
            if fresh:
                for label, role in (("Аватары", "avatars"), ("Голоса", "voices")):
                    work.knowledge.create(project, None, "folder", label, role)
            work.commit()
            return project

    def assigned_projects(self, owner: UUID) -> dict[UUID, list[UUID]]:
        with self.work() as work:
            return work.repository.avatar_assignments(owner)

    def assign(self, owner: UUID, avatar: UUID, project: UUID):
        source = self.workspace(owner)
        with self.work() as work, ExitStack() as cleanup:
            repo = work.knowledge
            if (
                source == project
                or not repo.owns_project(source, owner)
                or not repo.owns_project(project, owner)
            ):
                raise ProjectNotFound
            root = repo.get(source, avatar)
            if root is None or root.folder_role != "avatar":
                raise NodeNotFound
            target = repo.list(project)
            existing = next((n for n in target if n.library_avatar_id == avatar), None)
            if existing:
                return existing.id
            parent = ensure_library_folder(repo, project, target, "Аватары", "avatars")
            if any(
                n.parent_id == parent.id and n.name.casefold() == root.name.casefold()
                for n in target
            ):
                raise NodeConflict
            children = defaultdict(list)
            for node in repo.list(source):
                children[node.parent_id].append(node)

            def copy(node, parent_id):
                if node.kind == "folder":
                    saved = repo.create(
                        project, parent_id, node.kind, node.name, node.folder_role
                    )
                    for child in children.get(node.id, []):
                        copy(child, saved.id)
                    return saved
                versions = repo.versions(node.id)
                if not versions:
                    return repo.create(project, parent_id, node.kind, node.name)
                version = versions[0]
                entry = ExampleEntry(
                    str(node.id),
                    None,
                    node.name,
                    node.kind,
                    self.store.get(version.storage_key),
                    version.format,
                )
                return create_entry(
                    project, parent_id, entry, repo, self.store, cleanup
                )

            assigned = copy(root, parent.id)
            linked = None
            if root.linked_voice_id:
                voice = repo.get(source, root.linked_voice_id)
                if voice and voice.library_voice_id:
                    ensure_library_folder(repo, project, target, "Голоса", "voices")
                    linked = work.repository.attach_avatar_voice(
                        project, voice.library_voice_id, owner
                    )
            repo.change(
                project,
                assigned.id,
                assigned.revision,
                linked_voice_id=linked,
                library_avatar_id=avatar,
            )
            work.commit()
            cleanup.pop_all()
            return assigned.id
