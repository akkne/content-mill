"""Issue a short-lived owner invitation from the server console."""

from app.container import auth_service
from app.owner import configured_owner


def main() -> None:
    owner = configured_owner()
    if owner is None:
        raise SystemExit("Configure MILL_ADMIN_USER_ID before issuing a link")
    print(auth_service().issue_owner_setup(owner))


if __name__ == "__main__":
    main()
