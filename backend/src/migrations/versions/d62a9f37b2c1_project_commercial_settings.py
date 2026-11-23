"""Store project delivery terms and video defaults."""

import sqlalchemy as sa
from alembic import op

revision = "d62a9f37b2c1"
down_revision = "9bae69c67e8f"
branch_labels = None
depends_on = None


def upgrade():
    for column in (
        sa.Column(
            "sales_mode", sa.String(20), nullable=False, server_default="unassigned"
        ),
        sa.Column("package_name", sa.String(160), nullable=False, server_default=""),
        sa.Column("delivery_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("video_duration", sa.Integer(), nullable=False, server_default="30"),
        sa.Column(
            "video_style", sa.String(64), nullable=False, server_default="По сценарию"
        ),
        sa.Column("admin_revision", sa.Integer(), nullable=False, server_default="1"),
    ):
        op.add_column("projects", column)


def downgrade():
    for name in (
        "admin_revision",
        "video_style",
        "video_duration",
        "delivery_notes",
        "package_name",
        "sales_mode",
    ):
        op.drop_column("projects", name)
