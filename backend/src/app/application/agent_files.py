import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID

from app.application.agent_ports import AgentScope, PreviewRenderer
from app.application.knowledge_ports import DocumentStore
from app.application.project_ports import ProjectUnitOfWorkFactory
from app.domain.knowledge import DocumentVersion, InvalidNodeOperation, NodeNotFound
from app.domain.project import ProjectNotFound


class AgentFiles:
    def __init__(
        self,
        work: ProjectUnitOfWorkFactory,
        store: DocumentStore,
        renderer: PreviewRenderer,
    ):
        self.work = work
        self.store = store
        self.renderer = renderer

    def issue(self, scope: AgentScope) -> dict:
        token = "cm_mcp_" + secrets.token_urlsafe(32)
        expires = datetime.now(UTC) + timedelta(hours=1)
        with self.work() as work:
            if not work.repository.get_owned(scope.project_id, scope.owner_id):
                raise ProjectNotFound
            work.agent.replace_token(scope, sha256(token.encode()).hexdigest(), expires)
            work.commit()
        return {"token": token, "expires_at": expires}

    def revoke(self, scope: AgentScope) -> None:
        with self.work() as work:
            if not work.repository.get_owned(scope.project_id, scope.owner_id):
                raise ProjectNotFound
            work.agent.revoke(scope)
            work.commit()

    def resolve(self, token: str) -> AgentScope | None:
        if not token.startswith("cm_mcp_") or len(token) != 50:
            return None
        with self.work() as work:
            return work.agent.resolve(
                sha256(token.encode()).hexdigest(), datetime.now(UTC)
            )

    def find(
        self,
        scope: AgentScope,
        query: str,
        kind: str | None,
        folder_id: UUID | None,
        character_id: UUID | None,
        offset: int,
        limit: int,
    ) -> dict:
        with self.work() as work:
            rows = work.agent.find(
                scope.project_id,
                query.strip(),
                kind,
                folder_id,
                character_id,
                offset,
                limit + 1,
            )
        return {
            "items": rows[:limit],
            "next_offset": offset + limit if len(rows) > limit else None,
        }

    def _asset(self, scope: AgentScope, version_id: UUID):
        with self.work() as work:
            result = work.agent.asset(scope.project_id, version_id)
        if result is None:
            raise NodeNotFound("Версия файла не найдена")
        return result

    def _content(self, version: DocumentVersion) -> bytes:
        content = self.store.get(version.storage_key)
        if sha256(content).hexdigest() != version.sha256:
            raise InvalidNodeOperation("Контрольная сумма файла не совпала")
        return content

    def read(
        self, scope: AgentScope, version_id: UUID, offset: int, limit: int
    ) -> dict:
        name, kind, version = self._asset(scope, version_id)
        if kind != "document":
            raise InvalidNodeOperation("Выберите текстовый документ")
        text = self._content(version).decode("utf-8")
        return {
            "name": name,
            "version_id": str(version_id),
            "text": text[offset : offset + limit],
            "next_offset": offset + limit if offset + limit < len(text) else None,
        }

    def preview(self, scope: AgentScope, version_id: UUID) -> dict | bytes:
        name, kind, version = self._asset(scope, version_id)
        if kind not in {"image", "video"}:
            return {
                "name": name,
                "version_id": str(version_id),
                "format": version.format,
                "size_bytes": version.size_bytes,
                "preview_available": False,
            }
        return self.renderer.render(self._content(version), version.format)
