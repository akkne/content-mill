from contextlib import ExitStack
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID, uuid4

from app.application.knowledge_ports import (
    DocumentStore,
    KnowledgeUnitOfWork,
    KnowledgeUnitOfWorkFactory,
)
from app.application.seed_documents import create_entry
from app.domain.knowledge import (
    AVATAR_DESCRIPTION,
    AVATAR_FOLDERS,
    DocumentVersion,
    ExampleEntry,
    InvalidNodeOperation,
    KnowledgeNode,
    MediaUpload,
    NodeConflict,
    NodeNotFound,
)
from app.domain.media import MAX_MEDIA_BYTES, MEDIA_TYPES, verify_media
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
        self,
        work: KnowledgeUnitOfWork,
        project_id: UUID,
        parent_id: UUID | None,
        kind: str,
    ) -> KnowledgeNode | None:
        if parent_id is None:
            return
        parent = work.repository.get(project_id, parent_id)
        if parent is None or parent.kind != "folder":
            raise InvalidNodeOperation("Родительская папка не найдена")
        allowed = {
            "wardrobe": "folder",
            "photos": "image",
            "outfit": "image",
            "voice": "audio",
        }
        required = allowed.get(parent.folder_role)
        if required and kind != required:
            raise InvalidNodeOperation(
                "Этот тип элемента не подходит для выбранной папки"
            )
        return parent

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
            parent = self._parent(work, project_id, parent_id, kind)
            self._unique(work.repository.list(project_id), parent_id, name)
            if parent and parent.folder_role == "voices" and kind == "folder":
                raise InvalidNodeOperation("Выберите голос из личной библиотеки")
            role = None
            if parent and kind == "folder":
                role = {
                    "avatars": "avatar",
                    "wardrobe": "outfit",
                }.get(parent.folder_role)
            node = work.repository.create(project_id, parent_id, kind, name, role)
            if role == "avatar":
                work.repository.create(
                    project_id, node.id, "document", AVATAR_DESCRIPTION
                )
                for label, child_role in AVATAR_FOLDERS.items():
                    work.repository.create(
                        project_id,
                        node.id,
                        "folder",
                        label,
                        child_role,
                    )
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
                target = self._parent(work, project_id, parent_id, node.kind)
                if node.folder_role == "voice" and (
                    not target or target.folder_role != "voices"
                ):
                    raise InvalidNodeOperation(
                        "Голос должен находиться в папке «Голоса»"
                    )
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
            node = work.repository.get(project_id, node_id)
            if node is None or node.kind == "folder":
                raise NodeNotFound
            return work.repository.versions(node_id)

    def search_nodes(
        self, project_id: UUID, owner_id: UUID, query: str, limit: int = 100
    ) -> list[KnowledgeNode]:
        with self.unit_of_work() as work:
            self._owned(work, project_id, owner_id)
            matches = work.repository.search(project_id, query, limit)
            unindexed = work.repository.unindexed_versions(project_id)
        seen = {node.id for node in matches}
        for node, version in unindexed:
            if len(matches) >= limit:
                break
            if node.id in seen:
                continue
            content = self.store.get(version.storage_key)
            if sha256(content).hexdigest() != version.sha256:
                raise InvalidNodeOperation("Содержимое документа повреждено")
            if query.casefold() in content.decode("utf-8").casefold():
                matches.append(node)
                seen.add(node.id)
        return matches

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
                    content,
                )
                if saved is None:
                    raise RevisionConflict
                work.commit()
            except Exception:
                self.store.delete(key)
                raise
        return replace(node, revision=revision + 1), saved

    def start_upload(
        self,
        project_id: UUID,
        owner_id: UUID,
        parent_id: UUID | None,
        node_id: UUID | None,
        revision: int | None,
        name: str,
        mime_type: str,
        size_bytes: int,
        digest: str,
    ) -> tuple[MediaUpload, str]:
        if mime_type not in MEDIA_TYPES or not 0 < size_bytes <= MAX_MEDIA_BYTES:
            raise InvalidNodeOperation("Неподдерживаемый формат или размер файла")
        with self.unit_of_work() as work:
            self._owned(work, project_id, owner_id)
            if node_id:
                node = work.repository.get(project_id, node_id)
                if node is None or node.kind != MEDIA_TYPES[mime_type]:
                    raise InvalidNodeOperation(
                        "Тип новой версии должен совпадать с типом файла"
                    )
                if revision != node.revision:
                    raise RevisionConflict
            else:
                self._parent(work, project_id, parent_id, MEDIA_TYPES[mime_type])
                self._unique(work.repository.list(project_id), parent_id, name)
            upload = MediaUpload(
                uuid4(),
                project_id,
                parent_id,
                node_id,
                revision,
                name,
                mime_type,
                size_bytes,
                digest,
                datetime.now(UTC) + timedelta(minutes=10),
            )
            url = self.store.upload_url(upload.staging_key, mime_type, size_bytes)
            work.repository.record_upload(upload)
            work.commit()
            return upload, url

    def complete_upload(
        self, project_id: UUID, owner_id: UUID, upload_id: UUID
    ) -> tuple[KnowledgeNode, DocumentVersion]:
        with self.unit_of_work() as work:
            self._owned(work, project_id, owner_id)
            upload = work.repository.upload(project_id, upload_id)
            if not upload or upload.expires_at <= datetime.now(UTC):
                raise InvalidNodeOperation("Срок загрузки истёк")
            if upload.node_id:
                node = work.repository.get(project_id, upload.node_id)
                if node is None:
                    raise NodeNotFound
                versions = work.repository.versions(node.id)
                if upload.completed_version:
                    return node, next(
                        v for v in versions if v.version == upload.completed_version
                    )
                if node.revision != upload.revision:
                    raise RevisionConflict
                number = versions[0].version + 1
            else:
                self._parent(
                    work, project_id, upload.parent_id, MEDIA_TYPES[upload.mime_type]
                )
                self._unique(
                    work.repository.list(project_id), upload.parent_id, upload.name
                )
                node = work.repository.create(
                    project_id,
                    upload.parent_id,
                    MEDIA_TYPES[upload.mime_type],
                    upload.name,
                )
                number = 1
            data = self.store.read_upload(upload.staging_key, upload.size_bytes)
            if (
                len(data) != upload.size_bytes
                or sha256(data).hexdigest() != upload.sha256
            ):
                raise InvalidNodeOperation(
                    "Размер или контрольная сумма файла не совпали"
                )
            verify_media(data, upload.mime_type)
            key = f"projects/{project_id}/nodes/{node.id}/versions/{uuid4()}"
            self.store.put(key, data, upload.mime_type)
            try:
                version = work.repository.add_version(
                    node.id,
                    node.revision,
                    number,
                    upload.mime_type,
                    len(data),
                    upload.sha256,
                    key,
                    "",
                )
                if version is None:
                    raise RevisionConflict
                work.repository.finish_upload(upload.id, node.id, number)
                work.commit()
            except Exception:
                self.store.delete(key)
                raise
            return replace(node, revision=node.revision + 1), version

    def download(
        self, project_id: UUID, owner_id: UUID, node_id: UUID, number: int | None
    ) -> tuple[str, DocumentVersion]:
        versions = self.document_versions(project_id, owner_id, node_id)
        version = next(
            (v for v in versions if number is None or v.version == number), None
        )
        if version is None:
            raise NodeNotFound
        return self.store.download_url(version.storage_key), version

    def clean_uploads(self) -> None:
        with self.unit_of_work() as work:
            for upload in work.repository.expired_uploads(
                datetime.now(UTC) - timedelta(minutes=5)
            ):
                self.store.delete(upload.staging_key)
            work.commit()

    def edit_profile(
        self,
        project_id: UUID,
        owner_id: UUID,
        node_id: UUID,
        revision: int,
        role: str,
        **fields: object,
    ) -> KnowledgeNode:
        with self.unit_of_work() as work:
            self._owned(work, project_id, owner_id)
            node = work.repository.get(project_id, node_id)
            if node is None or node.folder_role != role:
                raise NodeNotFound
            if role == "voice":
                raise InvalidNodeOperation(
                    "Настройки голоса редактируются в личной библиотеке"
                )
            voice_id = fields.get("linked_voice_id")
            if isinstance(voice_id, UUID):
                voice = work.repository.get(project_id, voice_id)
                if voice is None or voice.folder_role != "voice":
                    raise InvalidNodeOperation("Выберите голос этого проекта")
            updated = work.repository.change(project_id, node_id, revision, **fields)
            if updated is None:
                raise RevisionConflict
            work.commit()
            return updated

    def import_examples(
        self, project_id: UUID, owner_id: UUID, entries: list[ExampleEntry]
    ) -> list[KnowledgeNode]:
        with self.unit_of_work() as work, ExitStack() as cleanup:
            self._owned(work, project_id, owner_id)
            self._unique(work.repository.list(project_id), None, entries[0].name)
            nodes = {}
            for entry in entries:
                parent = nodes[entry.parent].id if entry.parent else None
                nodes[entry.id] = create_entry(
                    project_id, parent, entry, work.repository, self.store, cleanup
                )
            work.commit()
            cleanup.pop_all()
            return list(nodes.values())
