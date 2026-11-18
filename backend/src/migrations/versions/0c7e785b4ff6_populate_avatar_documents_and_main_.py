"""Populate avatar documents and main voices in existing project libraries."""

from hashlib import sha256
from uuid import uuid4, uuid5

import sqlalchemy as sa
from alembic import op

from app.infrastructure.storage.s3_documents import S3DocumentStore

revision = "0c7e785b4ff6"
down_revision = "9cecd461489c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    db = op.get_bind()
    metadata = sa.MetaData()
    nodes = sa.Table("knowledge_nodes", metadata, autoload_with=db)
    versions = sa.Table("document_versions", metadata, autoload_with=db)
    store = S3DocumentStore()
    parents = (
        db.execute(
            sa.select(nodes).where(
                nodes.c.folder_role.in_(("avatar", "voices")),
                nodes.c.archived_at.is_(None),
            )
        )
        .mappings()
        .all()
    )
    for parent in parents:
        is_avatar = parent["folder_role"] == "avatar"
        name = "Описание аватара.md" if is_avatar else "Основной голос"
        children = db.execute(
            sa.select(nodes.c.name, nodes.c.kind).where(
                nodes.c.parent_id == parent["id"], nodes.c.archived_at.is_(None)
            )
        ).all()
        names = {child.name.casefold(): child.kind for child in children}
        content = parent["description"] if is_avatar else None
        if name.casefold() in names:
            if not is_avatar or (not content and names[name.casefold()] == "document"):
                continue
            # Preserve independently authored files and the old profile text.
            suffix = 2
            while f"Описание аватара ({suffix}).md".casefold() in names:
                suffix += 1
            name = f"Описание аватара ({suffix}).md"
        node_id = uuid4()
        db.execute(
            nodes.insert().values(
                id=node_id,
                project_id=parent["project_id"],
                parent_id=parent["id"],
                kind="document" if is_avatar else "folder",
                name=name,
                revision=1,
                folder_role=None if is_avatar else "voice",
            )
        )
        if content:
            data = content.encode()
            digest = sha256(data).hexdigest()
            version_id = uuid5(parent["id"], digest)
            key = f"projects/{parent['project_id']}/avatar-descriptions/{version_id}"
            store.put(key, data, "text/markdown")
            db.execute(
                versions.insert().values(
                    id=version_id,
                    node_id=node_id,
                    version=1,
                    format="markdown",
                    size_bytes=len(data),
                    sha256=digest,
                    storage_key=key,
                    search_text=content,
                )
            )
            db.execute(
                nodes.update()
                .where(nodes.c.id == parent["id"])
                .values(description=None)
            )


def downgrade() -> None:
    # These documents and voices may already contain user edits.
    pass
