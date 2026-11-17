import getpass
import sys

from app.container import auth_service


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
    auth_service().create_or_reset_user(email, display_name, password)
    print(f"Account ready: {email}")


if __name__ == "__main__":
    main()
