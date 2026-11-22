from contextlib import ExitStack
from dataclasses import replace
from hashlib import sha256
from uuid import UUID, uuid4

from app.application.knowledge.ports import DocumentStore, KnowledgeRepository
from app.domain.knowledge import ExampleEntry, KnowledgeNode
from app.domain.project import RevisionConflict


def create_entry(
    project_id: UUID,
    parent: UUID | None,
    entry: ExampleEntry,
    repository: KnowledgeRepository,
    store: DocumentStore,
    cleanup: ExitStack,
) -> KnowledgeNode:
    node = repository.create(project_id, parent, entry.kind, entry.name)
    if entry.kind == "folder":
        return node
    key = f"projects/{project_id}/nodes/{node.id}/versions/{uuid4()}"
    mime = {"markdown": "text/markdown", "plain": "text/plain"}.get(
        entry.format, entry.format
    )
    cleanup.callback(store.delete, key)
    store.put(key, entry.content, mime)
    version = repository.add_version(
        node.id,
        node.revision,
        1,
        entry.format,
        len(entry.content),
        sha256(entry.content).hexdigest(),
        key,
        entry.content.decode() if entry.kind == "document" else "",
    )
    if version is None:
        raise RevisionConflict
    return replace(node, revision=node.revision + 1)
