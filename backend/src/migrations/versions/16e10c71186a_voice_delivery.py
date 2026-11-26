"""Store delivery preferences on personal voice cards."""

import sqlalchemy as sa
from alembic import op

revision = "16e10c71186a"
down_revision = "209617a2aa6f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "library_voices",
        sa.Column("voice_speed", sa.Float(), nullable=False, server_default="1.1"),
    )
    op.add_column(
        "library_voices",
        sa.Column("voice_style", sa.Float(), nullable=False, server_default="0.4"),
    )


def downgrade() -> None:
    op.drop_column("library_voices", "voice_style")
    op.drop_column("library_voices", "voice_speed")
