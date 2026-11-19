"""add personal voice library

Revision ID: d42a71aab6f9
Revises: b0046640fe3e
Create Date: 2026-11-19 14:24:01.945691

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d42a71aab6f9"
down_revision: str | Sequence[str] | None = "b0046640fe3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "library_voices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("elevenlabs_voice_id", sa.String(length=160), nullable=True),
        sa.Column("voice_gender", sa.String(length=16), nullable=True),
        sa.Column(
            "catalog_languages", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("voice_language", sa.String(length=80), nullable=True),
        sa.Column("voice_model", sa.String(length=160), nullable=True),
        sa.Column("voice_preview_url", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_library_voices_owner_id"), "library_voices", ["owner_id"], unique=False
    )
    op.add_column(
        "knowledge_nodes", sa.Column("library_voice_id", sa.Uuid(), nullable=True)
    )
    op.create_index(
        op.f("ix_knowledge_nodes_library_voice_id"),
        "knowledge_nodes",
        ["library_voice_id"],
        unique=False,
    )
    op.create_foreign_key(
        "knowledge_library_voice_fk",
        "knowledge_nodes",
        "library_voices",
        ["library_voice_id"],
        ["id"],
    )
    db = op.get_bind()
    metadata = sa.MetaData()
    nodes = sa.Table("knowledge_nodes", metadata, autoload_with=db)
    projects = sa.Table("projects", metadata, autoload_with=db)
    library = sa.Table("library_voices", metadata, autoload_with=db)
    fields = [col.name for col in library.columns if col.name not in ("id", "owner_id")]
    active = sa.and_(nodes.c.folder_role == "voice", nodes.c.archived_at.is_(None))
    db.execute(
        library.insert().from_select(
            ["id", "owner_id", *fields],
            sa.select(
                nodes.c.id, projects.c.owner_id, *(nodes.c[key] for key in fields)
            )
            .select_from(nodes.join(projects, projects.c.id == nodes.c.project_id))
            .where(active),
        )
    )
    db.execute(nodes.update().where(active).values(library_voice_id=nodes.c.id))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "knowledge_library_voice_fk", "knowledge_nodes", type_="foreignkey"
    )
    op.drop_index(
        op.f("ix_knowledge_nodes_library_voice_id"), table_name="knowledge_nodes"
    )
    op.drop_column("knowledge_nodes", "library_voice_id")
    op.drop_index(op.f("ix_library_voices_owner_id"), table_name="library_voices")
    op.drop_table("library_voices")
