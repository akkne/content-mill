from datetime import datetime
from uuid import UUID

from sqlalchemy import Text, and_, cast, delete, literal, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, aliased

from app.application.agent_ports import AgentScope
from app.domain.knowledge import DocumentVersion
from app.infrastructure.database.knowledge_repository import as_version
from app.infrastructure.database.models import (
    DocumentVersionModel as Version,
)
from app.infrastructure.database.models import (
    KnowledgeNodeModel as Node,
)
from app.infrastructure.database.models import (
    ProjectAgentTokenModel as Token,
)
from app.infrastructure.database.models import (
    ProjectModel as Project,
)


class SqlAgentRepository:
    def __init__(self, session: Session):
        self.session = session

    def replace_token(self, scope: AgentScope, digest: str, expires: datetime) -> None:
        values = {
            "owner_id": scope.owner_id,
            "token_hash": digest,
            "expires_at": expires,
        }
        stmt = insert(Token).values(project_id=scope.project_id, **values)
        self.session.execute(
            stmt.on_conflict_do_update(index_elements=[Token.project_id], set_=values)
        )

    def revoke(self, scope: AgentScope) -> None:
        self.session.execute(
            delete(Token).where(
                Token.project_id == scope.project_id, Token.owner_id == scope.owner_id
            )
        )

    def resolve(self, digest: str, now: datetime) -> AgentScope | None:
        row = self.session.execute(
            select(Token.project_id, Token.owner_id)
            .join(Project, Project.id == Token.project_id)
            .where(
                Token.token_hash == digest,
                Token.expires_at > now,
                Project.owner_id == Token.owner_id,
            )
        ).one_or_none()
        return AgentScope(*row) if row else None

    def asset(
        self, project: UUID, version_id: UUID
    ) -> tuple[str, str, DocumentVersion] | None:
        row = self.session.execute(
            select(Node.name, Node.kind, Version)
            .join_from(Version, Node, Node.id == Version.node_id)
            .where(
                Version.id == version_id,
                Node.project_id == project,
                Node.archived_at.is_(None),
            )
        ).one_or_none()
        return (row.name, row.kind, as_version(row[2])) if row else None

    def find(
        self,
        project: UUID,
        query: str,
        kind: str | None,
        folder_id: UUID | None,
        character_id: UUID | None,
        offset: int,
        limit: int,
    ) -> list[dict]:
        live = and_(Node.project_id == project, Node.archived_at.is_(None))
        tree = (
            select(
                Node.id,
                cast(Node.name, Text).label("path"),
                (Node.id == folder_id).label("in_folder"),
                and_(Node.id == character_id, Node.folder_role == "avatar").label(
                    "in_character"
                ),
            )
            .where(live, Node.parent_id.is_(None))
            .cte("tree", recursive=True)
        )
        tree = tree.union_all(
            select(
                Node.id,
                tree.c.path + literal("/") + Node.name,
                or_(tree.c.in_folder, Node.id == folder_id),
                or_(
                    tree.c.in_character,
                    and_(Node.id == character_id, Node.folder_role == "avatar"),
                ),
            )
            .join(tree, Node.parent_id == tree.c.id)
            .where(live)
        )
        latest = aliased(Version)
        latest_id = (
            select(latest.id)
            .where(latest.node_id == Node.id)
            .order_by(latest.version.desc())
            .limit(1)
            .correlate(Node)
            .scalar_subquery()
        )
        stmt = (
            select(
                Node.id.label("node_id"),
                Node.name,
                Node.kind,
                tree.c.path,
                Version.id.label("version_id"),
                Version.version,
                Version.format,
                Version.size_bytes,
            )
            .select_from(Node)
            .join(tree, tree.c.id == Node.id)
            .join(Version, Version.id == latest_id)
        )
        if query:
            stmt = stmt.where(
                or_(
                    tree.c.path.icontains(query, autoescape=True),
                    Version.search_text.icontains(query, autoescape=True),
                )
            )
        if kind:
            stmt = stmt.where(Node.kind == kind)
        if folder_id:
            stmt = stmt.where(tree.c.in_folder)
        if character_id:
            stmt = stmt.where(tree.c.in_character)
        rows = self.session.execute(
            stmt.order_by(tree.c.path, Node.id).offset(offset).limit(limit)
        ).mappings()
        return [dict(row) for row in rows]
