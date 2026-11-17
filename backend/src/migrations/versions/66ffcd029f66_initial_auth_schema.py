"""Initial auth schema from SQLAlchemy models.

Also adopts the tables created by the earlier direct SQL implementation.
"""

import sqlalchemy as sa
from alembic import op

revision = "66ffcd029f66"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())

    if "users" not in existing:
        op.create_table(
            "users",
            sa.Column("id", sa.UUID(), primary_key=True),
            sa.Column("email", sa.String(254), nullable=False, unique=True),
            sa.Column("display_name", sa.Text(), nullable=False),
            sa.Column("password_hash", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
    else:
        op.alter_column("users", "email", type_=sa.String(254), existing_nullable=False)

    if "auth_sessions" not in existing:
        op.create_table(
            "auth_sessions",
            sa.Column("id", sa.UUID(), primary_key=True),
            sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("family_id", sa.UUID(), nullable=False),
            sa.Column("refresh_hash", sa.Text(), nullable=False, unique=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True)),
            sa.Column("rotated_at", sa.DateTime(timezone=True)),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index("auth_sessions_family_idx", "auth_sessions", ["family_id"])

    if "access_tokens" not in existing:
        op.create_table(
            "access_tokens",
            sa.Column("token_hash", sa.Text(), primary_key=True),
            sa.Column(
                "session_id",
                sa.UUID(),
                sa.ForeignKey("auth_sessions.id"),
                nullable=False,
            ),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        )

    if "login_attempts" not in existing:
        op.create_table(
            "login_attempts",
            sa.Column("id", sa.UUID(), primary_key=True),
            sa.Column("attempt_key", sa.Text(), nullable=False),
            sa.Column(
                "attempted_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index(
            "login_attempts_key_idx", "login_attempts", ["attempt_key", "attempted_at"]
        )
    else:
        attempts = sa.table("login_attempts", sa.column("attempt_key"))
        op.execute(attempts.delete())
        op.add_column("login_attempts", sa.Column("id", sa.UUID(), nullable=True))
        op.alter_column("login_attempts", "id", nullable=False, existing_type=sa.UUID())
        op.create_primary_key("login_attempts_pkey", "login_attempts", ["id"])


def downgrade() -> None:
    op.drop_table("access_tokens")
    op.drop_index("auth_sessions_family_idx", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_table("users")
    op.drop_index("login_attempts_key_idx", table_name="login_attempts")
    op.drop_table("login_attempts")
