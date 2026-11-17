import getpass
import sys
from uuid import uuid4

from argon2 import PasswordHasher

from app.db import connection, migrate


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m app.bootstrap_user EMAIL DISPLAY_NAME")
    email = sys.argv[1].strip().lower()
    display_name = sys.argv[2].strip()
    if "@" not in email or len(email) > 254 or not display_name:
        raise SystemExit("Provide a valid email and display name")
    password = getpass.getpass("Password (at least 12 characters): ")
    if not 12 <= len(password) <= 1024:
        raise SystemExit("Password must have between 12 and 1024 characters")
    migrate()
    with connection() as conn:
        user = conn.execute(
            "SELECT id FROM users WHERE email = %s", (email,)
        ).fetchone()
        conn.execute(
            "INSERT INTO users (id, email, display_name, password_hash) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (email) DO UPDATE SET "
            "display_name = EXCLUDED.display_name, "
            "password_hash = EXCLUDED.password_hash",
            (uuid4(), email, display_name, PasswordHasher().hash(password)),
        )
        if user:
            conn.execute(
                "UPDATE auth_sessions SET revoked_at = now() "
                "WHERE user_id = %s AND revoked_at IS NULL",
                (user["id"],),
            )
    print(f"Account ready: {email}")


if __name__ == "__main__":
    main()
