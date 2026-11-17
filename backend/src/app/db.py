import os
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


def database_url() -> str:
    value = os.environ.get("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is required")
    return value


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    with psycopg.connect(database_url(), row_factory=dict_row) as conn:
        yield conn


def migrate() -> None:
    with connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id uuid PRIMARY KEY,
                email text NOT NULL UNIQUE,
                display_name text NOT NULL,
                password_hash text NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now()
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auth_sessions (
                id uuid PRIMARY KEY,
                user_id uuid NOT NULL REFERENCES users(id),
                family_id uuid NOT NULL,
                refresh_hash text NOT NULL UNIQUE,
                expires_at timestamptz NOT NULL,
                revoked_at timestamptz,
                rotated_at timestamptz,
                created_at timestamptz NOT NULL DEFAULT now()
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS auth_sessions_family_idx ON auth_sessions(family_id)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS access_tokens (
                token_hash text PRIMARY KEY,
                session_id uuid NOT NULL REFERENCES auth_sessions(id),
                expires_at timestamptz NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                attempt_key text NOT NULL,
                attempted_at timestamptz NOT NULL DEFAULT now()
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS login_attempts_key_idx ON login_attempts(attempt_key, attempted_at)")
