"""Add knowledge tree nodes.

Revision ID: 9d42a27f7f07
Revises: 40267cb9d8ec
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "9d42a27f7f07"
down_revision = "40267cb9d8ec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["knowledge_nodes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "knowledge_nodes_project_parent_idx",
        "knowledge_nodes",
        ["project_id", "parent_id"],
    )


def downgrade() -> None:
    op.drop_index("knowledge_nodes_project_parent_idx", table_name="knowledge_nodes")
    op.drop_table("knowledge_nodes")
