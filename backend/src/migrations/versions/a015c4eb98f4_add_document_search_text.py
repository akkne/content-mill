"""Add search text to document versions.

Revision ID: a015c4eb98f4
Revises: 47a320be4fb1
"""

import sqlalchemy as sa
from alembic import op

revision = "a015c4eb98f4"
down_revision = "47a320be4fb1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document_versions", sa.Column("search_text", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("document_versions", "search_text")
