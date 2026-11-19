"""store project voice catalog metadata

Revision ID: b0046640fe3e
Revises: 0c7e785b4ff6
Create Date: 2026-11-19 13:59:34.301262

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b0046640fe3e"
down_revision: str | Sequence[str] | None = "0c7e785b4ff6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "knowledge_nodes",
        sa.Column("voice_gender", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "knowledge_nodes",
        sa.Column(
            "catalog_languages", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    op.add_column(
        "knowledge_nodes", sa.Column("voice_preview_url", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("knowledge_nodes", "voice_preview_url")
    op.drop_column("knowledge_nodes", "catalog_languages")
    op.drop_column("knowledge_nodes", "voice_gender")
